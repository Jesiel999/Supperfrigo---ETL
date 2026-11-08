from datetime import datetime

from bronze.extract._base import extrair_paginado_sem_filtro
from config.settings import (
    SANCES_TOKEN,
    URL_SANCES_ESTOQUE_VEICULOS,
    REQUEST_TIMEOUT,
    SLEEP_REQUEST,
)
from core.logger import get_layer_logger
from repositories.sances.estoque_veiculos_repository import salvar_pagina_raw

logger = get_layer_logger("bronze", "estoque_veiculos")

# ==========================================
# CAMPOS (nível raiz do veículo)
# ==========================================
# dias_estoque NÃO é gravado de propósito: muda todo dia e faria o raw
# "mudar" sempre. É calculado na Silver a partir de data_nf_compra.
CAMPOS_SIMPLES = [
    "codigo", "placa", "chassi", "renavam",
    "marca", "modelo", "caracteristica_modelo",
    "cor", "combustivel", "tipo_veiculo_denatran",
    "ano_fabricacao", "ano_modelo", "quilometragem",
    "quantidade_portas", "cambio",
    "cilindrada", "unidade_cilindrada",
    "condicao", "descricao_conectacarros", "acessorios",
    "numero_motor", "potencia_maxima",
    "preco_venda", "preco_promocional",
    "codigo_empresa", "cnpj_empresa", "nome_empresa",
    "ultima_atualizacao_cadastro", "ultima_alteracao", "ultima_alteracao_preco",
    "consignado", "situacao", "disponibilidade",
    "codigo_situacao", "codigo_disponibilidade", "codigo_condicao",
    "data_nf_compra", "numero_nf_compra", "serie_nf_compra",
    "ativo_no_estoque",
    "referencia", "codigo_importado",
]

CAMPOS_DATETIME = [
    "ultima_atualizacao_cadastro",
    "ultima_alteracao",
    "ultima_alteracao_preco",
]

CAMPOS_DATE = ["data_nf_compra"]


# ==========================================
# HELPERS
# ==========================================

def _converter_data(valor, so_data: bool = False) -> str | None:
    """'2026-06-29T10:30:00.000-03:00' -> '2026-06-29 10:30:00' (hora local, sem fuso)."""
    if not valor:
        return None

    texto = str(valor).strip().replace("T", " ")

    if so_data:
        try:
            return datetime.strptime(texto[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

    for fmt, tamanho in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(texto[:tamanho], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return None


def _achatar_item(item: dict) -> dict:
    """Converte datas e achata os blocos aninhados (fipe, localizacao, oferta...)."""
    linha = {campo: item.get(campo) for campo in CAMPOS_SIMPLES}

    for campo in CAMPOS_DATETIME:
        linha[campo] = _converter_data(linha[campo])
    for campo in CAMPOS_DATE:
        linha[campo] = _converter_data(linha[campo], so_data=True)

    fipe      = item.get("fipe") or {}
    local     = item.get("localizacao") or {}
    oferta    = item.get("oferta") or {}
    carac     = item.get("caracteristicas") or {}
    garantia  = item.get("garantia") or {}
    reserva   = item.get("reserva") or {}
    negociacao = item.get("negociacao") or {}

    linha.update({
        "fipe_codigo":     fipe.get("codigo"),
        "fipe_descricao":  fipe.get("descricao"),
        "fipe_valor":      fipe.get("valor"),

        "uf":     local.get("uf"),
        "cidade": local.get("cidade"),

        "publicado_web":      oferta.get("publicado_web"),
        "destaque":           oferta.get("destaque"),
        "repasse":            oferta.get("repasse"),
        "observacoes_oferta": oferta.get("observacoes"),
        "url_video":          oferta.get("url_video"),

        "blindado":            carac.get("blindado"),
        "unico_dono":          carac.get("unico_dono"),
        "licenciado":          carac.get("licenciado"),
        "ipva_pago":           carac.get("ipva_pago"),
        "adaptado_deficiente": carac.get("adaptado_deficiente"),
        "cor_interna":         carac.get("cor_interna"),

        "garantia_inicio": _converter_data(garantia.get("inicio")),
        "garantia_fim":    _converter_data(garantia.get("fim")),

        "reserva_data_hora":       _converter_data(reserva.get("data_hora")),
        "reserva_codigo_cliente":  reserva.get("codigo_cliente"),
        "reserva_codigo_vendedor": reserva.get("codigo_vendedor"),

        "codigo_negociacao_compra": negociacao.get("compra"),
        "codigo_negociacao_venda":  negociacao.get("proposta_venda"),
    })

    # O bloco 'custo' só vem com incluir_custos=true. Se não veio, as colunas
    # ficam FORA do upsert — senão um incremental sem custos zeraria o que o
    # sweep completo gravou.
    if "custo" in item:
        custo = item.get("custo") or {}
        linha["valor_compra"]    = custo.get("valor_compra")
        linha["total_despesas"]  = custo.get("total_despesas")

    return linha


# ==========================================
# INTERFACE PÚBLICA
# ==========================================

def extrair_estoque_veiculos_sances(
    tenant_id: int,
    origem: str,
    token: str | None = None,
    limit: int = 500,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {token or SANCES_TOKEN}"}
    extra_params = filtros or {}

    def _persistir_pagina(itens: list[dict], offset: int, limit_usado: int) -> None:
        linhas = []

        for item in itens:
            if not item.get("codigo"):
                continue

            linha = _achatar_item(item)
            linha["tenant_id"] = tenant_id
            linhas.append(linha)

        logger.info(
            f"[estoque_veiculos] página {offset}: {len(itens)} itens recebidos, "
            f"{len(linhas)} válidos (com 'codigo')"
        )

        if itens and not linhas:
            logger.warning(
                f"[estoque_veiculos] página {offset}: nenhum item com 'codigo'. "
                f"Chaves do primeiro item: {list(itens[0].keys())[:15]}"
            )

        salvar_pagina_raw(tenant_id=tenant_id, itens=linhas)

    return extrair_paginado_sem_filtro(
        url=URL_SANCES_ESTOQUE_VEICULOS,
        headers=headers,
        origem=origem,
        tenant_id=tenant_id,
        on_page=_persistir_pagina,
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        extra_params=extra_params,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,   # 10 req/min -> >= 6s entre páginas
        nome_param_pagina="page",
        nome_param_limite="perPage",
        valor_padrao_pagina=1,
    )