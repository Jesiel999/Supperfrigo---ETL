from datetime import date, datetime
from core.logger import get_layer_logger

logger = get_layer_logger("silver", "financeiro_transform")


def _to_date(valor) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def transformar_financeiro(registros_raw: list[dict], tenant_id: int) -> list[dict]:
    """
    Transforma registros do financeiro_raw para financeiro_bi.
    tenant_id é obrigatório — garante isolamento multi-tenant.
    """
    resultado: list[dict] = []
    hoje = date.today()

    for raw in registros_raw:
        try:
            data_vencimento   = _to_date(raw.get("data_vencimento"))
            data_baixa        = _to_date(raw.get("data_baixa"))
            data_cancelamento = _to_date(raw.get("data_cancelamento"))
            data_emissao      = _to_date(raw.get("data_emissao"))
            data_competencia  = _to_date(raw.get("data_competencia"))
            
            descricao_situacao = str(raw.get("descricao_situacao") or "").strip().upper()

            # não subir CANCELADO e UNIDO
            if descricao_situacao in {"CANCELADO", "UNIDO", "RENEGOCIADO "}:
                continue
            # dias_atraso calculado na view, mas salvamos na silver também
            
            # status_financeiro
            if data_baixa:
                status_financeiro = "PAGO"
            elif data_vencimento and data_vencimento < hoje:
                status_financeiro = "VENCIDO"
            else:
                status_financeiro = "EM ABERTO"

            # dias_atraso
            dias_atraso: int | None = None

            if (
                data_baixa is None
                and data_vencimento
                and data_vencimento < date.today()
            ):
                dias_atraso = (date.today() - data_vencimento).days


            # dias_pagamento
            dias_pagamento: int | None = None

            if (
                raw.get("tipo_titulo") == "PAGAR"
                and data_vencimento
                and data_baixa
            ):
                dias_pagamento = (data_baixa - data_vencimento).days


            # dias_recebimento
            dias_recebimento: int | None = None

            if (
                raw.get("tipo_titulo") == "RECEBER"
                and data_emissao
                and data_baixa
            ):
                dias_recebimento = (data_baixa - data_emissao).days

            bi = {
                # ── Chave obrigatória ────────────────────────
                "tenant_id":                   tenant_id,
                "codigo_raw":                  raw.get("codigo"),

                # ── Empresa ──────────────────────────────────
                "id_empresa":                  raw.get("codigo_empresa"),

                # ── Pessoa ───────────────────────────────────
                "id_pessoa":                   raw.get("codigo_pessoa"),

                # ── Documento ────────────────────────────────
                "tipo_titulo":                 raw.get("tipo_titulo"),
                "numero_documento":            raw.get("numero_documento"),
                "ordem":                       raw.get("ordem"),
                "origem":                      raw.get("origem"),

                # ── Situação ─────────────────────────────────
                "codigo_situacao":             raw.get("codigo_situacao"),
                "descricao_situacao":          raw.get("descricao_situacao"),
                "status_financeiro":           status_financeiro,

                # ── Cobrança / Pagamento ─────────────────────
                "descricao_forma_cobranca":    raw.get("descricao_forma_cobranca"),
                "descricao_forma_pagamento":   raw.get("descricao_forma_pagamento"),

                # ── Categorização ────────────────────────────
                "codigo_categoria_financeira":    raw.get("codigo_categoria_financeira"),
                "descricao_categoria_financeira": raw.get("descricao_categoria_financeira"),
                "codigo_centro_custo":            raw.get("codigo_centro_custo"),
                "descricao_centro_custo":         raw.get("descricao_centro_custo"),
                "codigo_conta_resultado":         raw.get("codigo_conta_resultado"),
                "descricao_conta_resultado":      raw.get("descricao_conta_resultado"),

                # ── Datas ────────────────────────────────────
                "data_emissao":                data_emissao,
                "data_competencia":            data_competencia,
                "data_vencimento":             data_vencimento,
                "data_baixa":                  data_baixa,
                "data_cancelamento":           data_cancelamento,

                # ── Valores ──────────────────────────────────
                "valor_nominal":               raw.get("valor_nominal"),
                "valor_multa":                 raw.get("valor_multa"),
                "acrescimo":                   raw.get("acrescimo"),
                "valor_total":                 raw.get("valor_total"),

                # ── Calculado ────────────────────────────────
                "dias_atraso":                 dias_atraso,
                "dias_pagamento":              dias_pagamento,
                "dias_recebimento":            dias_recebimento,
            }

            resultado.append(bi)

        except Exception as e:
            logger.error(f"Erro ao transformar registro {raw.get('codigo')} tenant={tenant_id}: {e}")

    logger.info(f"Silver tenant={tenant_id}: {len(resultado)} registros transformados.")
    return resultado