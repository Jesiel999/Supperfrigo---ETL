from config.settings import SULTS_TOKEN, URL_CHAMADOS, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_paginado_sem_filtro
from repositories.sults.chamados_repository import upsert_chamados_raw
from repositories.sults.chamados_apoio_repository import upsert_chamados_apoio_raw
from repositories.sults.chamados_etiqueta_repository import upsert_chamados_etiqueta_raw

logger = get_layer_logger("bronze", "chamados")

ORIGEM = "chamados_sults"

def extrair_chamados(
    tenant_id: int,
    token: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
) -> dict:

    headers = {
        "Authorization": f"{token or 'SULTS_TOKEN'}"
    }

    extra_params = filtros.copy() if filtros else {}

    def _persistir_pagina(
        itens: list[dict],
        offset: int,
        limit_usado: int,
    ) -> None:

        chamados_raw = []
        apoios_raw = []
        etiquetas_raw = []

        for chamado in itens:

            codigo = chamado.get("id")

            if not codigo:
                continue

            solicitante = chamado.get("solicitante") or {}
            responsavel = chamado.get("responsavel") or {}
            unidade = chamado.get("unidade") or {}
            departamento = chamado.get("departamento") or {}
            departamento_envio = chamado.get("departamentoEnvio") or {}
            assunto = chamado.get("assunto") or {}

            # ==================================================
            # CHAMADO
            # ==================================================

            chamados_raw.append({
                "tenant_id": tenant_id,
                "codigo": codigo,

                "titulo": chamado.get("titulo"),

                "solicitante_id": solicitante.get("id"),
                "solicitante_nome": solicitante.get("nome"),

                "responsavel_id": responsavel.get("id"),
                "responsavel_nome": responsavel.get("nome"),

                "unidade_id": unidade.get("id"),
                "unidade_nome": unidade.get("nome"),

                "departamento_id": departamento.get("id"),
                "departamento_nome": departamento.get("nome"),

                "departamento_envio_id": departamento_envio.get("id"),
                "departamento_envio_nome": departamento_envio.get("nome"),

                "assunto_id": assunto.get("id"),
                "assunto_nome": assunto.get("nome"),

                "tipo": chamado.get("tipo"),
                "situacao": chamado.get("situacao"),

                "data_aberto": chamado.get("aberto"),
                "data_resolvido": chamado.get("resolvido"),
                "data_concluido": chamado.get("concluido"),

                "data_resolver_planejado":
                    chamado.get("resolverPlanejado"),

                "data_resolver_estipulado":
                    chamado.get("resolverEstipulado"),

                "data_primeira_interacao":
                    chamado.get("primeiraInteracao"),

                "data_ultima_alteracao":
                    chamado.get("ultimaAlteracao"),

                "avaliacao_nota":
                    chamado.get("avaliacaoNota"),

                "avaliacao_observacao":
                    chamado.get("avaliacaoObservacao"),

                "quantidade_interacao_publico":
                    chamado.get("countInteracaoPublico"),

                "quantidade_interacao_interno":
                    chamado.get("countInteracaoInterno"),
            })

            # ==================================================
            # APOIOS
            # ==================================================

            apoios = chamado.get("apoio") or []

            for apoio in apoios:

                pessoa = (
                    apoio.get("pessapoiooa")
                    or apoio.get("pessoa")
                    or {}
                )

                departamento_apoio = (
                    apoio.get("departamento")
                    or {}
                )

                apoios_raw.append({
                    "tenant_id": tenant_id,
                    "chamado_codigo": codigo,

                    "pessoa_id": pessoa.get("id"),
                    "pessoa_nome": pessoa.get("nome"),

                    "departamento_id":
                        departamento_apoio.get("id"),

                    "departamento_nome":
                        departamento_apoio.get("nome"),

                    "pessoa_unidade":
                        apoio.get("pessoaUnidade", False),
                })

            # ==================================================
            # ETIQUETAS
            # ==================================================

            etiquetas = chamado.get("etiqueta") or []

            for etiqueta in etiquetas:

                etiquetas_raw.append({
                    "tenant_id": tenant_id,
                    "chamado_codigo": codigo,

                    "etiqueta_id": etiqueta.get("id"),
                    "etiqueta_nome": etiqueta.get("nome"),
                    "etiqueta_cor": etiqueta.get("cor"),
                })

        # ======================================================
        # PERSISTE A PÁGINA IMEDIATAMENTE
        # ======================================================

        if chamados_raw:
            upsert_chamados_raw(chamados_raw)

        if apoios_raw:
            upsert_chamados_apoio_raw(apoios_raw)

        if etiquetas_raw:
            upsert_chamados_etiqueta_raw(etiquetas_raw)

        logger.info(
            f"[BRONZE-CHAMADOS] "
            f"tenant={tenant_id} | "
            f"offset={offset} | "
            f"chamados={len(chamados_raw)} | "
            f"apoios={len(apoios_raw)} | "
            f"etiquetas={len(etiquetas_raw)}"
        )

    return extrair_paginado_sem_filtro(
        url=URL_CHAMADOS,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        on_page=_persistir_pagina,
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        extra_params=extra_params,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
    )