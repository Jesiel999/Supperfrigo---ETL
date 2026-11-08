from datetime import date, datetime

from core.logger import get_layer_logger

logger = get_layer_logger("silver", "estoque_veiculos_transform")

FAIXAS_ESTOQUE = [
    (30, "0-30 dias"),
    (60, "31-60 dias"),
    (90, "61-90 dias"),
    (180, "91-180 dias"),
]


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


def _num(valor) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _faixa_estoque(dias: int | None) -> str | None:
    if dias is None:
        return None
    for limite, rotulo in FAIXAS_ESTOQUE:
        if dias <= limite:
            return rotulo
    return "180+ dias"


def transformar_estoque_veiculos(registros_raw: list[dict], tenant_id: int) -> list[dict]:

    resultado: list[dict] = []
    hoje = date.today()

    for raw in registros_raw:
        try:
            codigo = raw.get("codigo")

            ativo_raw = raw.get("ativo_no_estoque")
            ativo = bool(ativo_raw) if ativo_raw is not None else True
            reservado = raw.get("reserva_data_hora") is not None

            if not ativo:
                status_estoque = "FORA DO ESTOQUE"
            elif reservado:
                status_estoque = "RESERVADO"
            else:
                status_estoque = "EM ESTOQUE"

            data_nf_compra = _to_date(raw.get("data_nf_compra"))

            dias_estoque = None
            if ativo and data_nf_compra:
                dias_estoque = max((hoje - data_nf_compra).days, 0)

            # preços
            preco_venda       = _num(raw.get("preco_venda"))
            preco_promocional = _num(raw.get("preco_promocional"))
            preco_efetivo = (
                preco_promocional
                if preco_promocional and preco_promocional > 0
                else preco_venda
            )

            fipe_valor = _num(raw.get("fipe_valor"))
            diferenca_fipe = None
            percentual_sobre_fipe = None
            if preco_efetivo is not None and fipe_valor:
                diferenca_fipe = round(preco_efetivo - fipe_valor, 2)
                percentual_sobre_fipe = round(diferenca_fipe / fipe_valor * 100, 2)

            # custo / margem (só preenchidos se a extração rodou com incluir_custos)
            valor_compra   = _num(raw.get("valor_compra"))
            total_despesas = _num(raw.get("total_despesas"))
            custo_total = margem_bruta = margem_percentual = None
            if valor_compra is not None:
                custo_total = round(valor_compra + (total_despesas or 0), 2)
                if preco_efetivo is not None:
                    margem_bruta = round(preco_efetivo - custo_total, 2)
                    if preco_efetivo > 0:
                        margem_percentual = round(margem_bruta / preco_efetivo * 100, 2)

            bi = {
                "tenant_id":                tenant_id,
                "codigo_raw":               codigo,
                "id_empresa":               raw.get("codigo_empresa"),
                "nome_empresa":             raw.get("nome_empresa"),

                "placa":                    raw.get("placa"),
                "chassi":                   raw.get("chassi"),
                "marca":                    raw.get("marca"),
                "modelo":                   raw.get("modelo"),
                "versao":                   raw.get("caracteristica_modelo"),
                "cor":                      raw.get("cor"),
                "combustivel":              raw.get("combustivel"),
                "cambio":                   raw.get("cambio"),
                "condicao":                 raw.get("condicao"),
                "ano_fabricacao":           raw.get("ano_fabricacao"),
                "ano_modelo":               raw.get("ano_modelo"),
                "quilometragem":            raw.get("quilometragem"),
                "uf":                       raw.get("uf"),
                "cidade":                   raw.get("cidade"),

                "codigo_situacao":          raw.get("codigo_situacao"),
                "situacao":                 raw.get("situacao"),
                "codigo_disponibilidade":   raw.get("codigo_disponibilidade"),
                "disponibilidade":          raw.get("disponibilidade"),
                "ativo_no_estoque":         1 if ativo else 0,
                "reservado":                1 if reservado else 0,
                "consignado":               raw.get("consignado"),
                "publicado_web":            raw.get("publicado_web"),
                "status_estoque":           status_estoque,

                "preco_venda":              preco_venda,
                "preco_promocional":        preco_promocional,
                "preco_efetivo":            preco_efetivo,
                "fipe_valor":               fipe_valor,
                "diferenca_fipe":           diferenca_fipe,
                "percentual_sobre_fipe":    percentual_sobre_fipe,

                "valor_compra":             valor_compra,
                "total_despesas":           total_despesas,
                "custo_total":              custo_total,
                "margem_bruta":             margem_bruta,
                "margem_percentual":        margem_percentual,

                "data_nf_compra":           data_nf_compra,
                "dias_estoque":             dias_estoque,
                "faixa_estoque":            _faixa_estoque(dias_estoque),
                "data_ultima_alteracao_preco": _to_date(raw.get("ultima_alteracao_preco")),
                "atualizado_em":            raw.get("ultima_alteracao"),
            }

            resultado.append(bi)

        except Exception as e:
            logger.error(f"Erro ao transformar veículo {raw.get('codigo')} tenant={tenant_id}: {e}")

    return resultado