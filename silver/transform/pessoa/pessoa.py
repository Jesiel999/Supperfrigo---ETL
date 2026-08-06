import logging
from bronze.extract.utils import normalizar_cpf_cnpj

logger = logging.getLogger(__name__)


def transformar_pessoa(raw: dict, tenant_id: int) -> list[dict]:
    """
    Une os registros de pessoa_sances_raw e pessoa_sults_raw em uma única
    lista de pessoas para pessoa_bi.

    Critério de match: CPF/CNPJ normalizado (somente dígitos). Quando não
    há CPF em nenhum dos dois lados, o registro entra como pessoa isolada
    (não é possível casar com segurança sem chave).

    colaborador: marcado como 1 quando a pessoa existe no Sults (sistema
    de colaboradores), 0 caso exista apenas no Sances. Ajuste essa regra
    se a definição de "colaborador" for outra.
    """
    sances = raw.get("sances", [])
    sults = raw.get("sults", [])

    por_cpf: dict[str, dict] = {}

    for p in sances:
        cpf = normalizar_cpf_cnpj(p.get("cpf_cnpj"))
        chave = cpf or f"sances:{p['codigo_cliente']}"
        registro = por_cpf.setdefault(chave, {"colaborador": 0})
        registro["cpf_cnpj"] = cpf or None
        registro["id_sances"] = p.get("codigo_cliente")
        registro["nome"] = p.get("nome_cliente")
        registro["sexo"] = (p.get("sexo") or "")[:1] or None

    for p in sults:
        cpf = normalizar_cpf_cnpj(p.get("cpf"))
        chave = cpf or f"sults:{p['id']}"
        registro = por_cpf.setdefault(chave, {})
        registro["cpf_cnpj"] = registro.get("cpf_cnpj") or cpf or None
        registro["id_sults"] = p.get("id")
        registro["colaborador"] = 1
        registro["nome"] = registro.get("nome") or p.get("nome")
        registro["sexo"] = registro.get("sexo") or (p.get("sexo") or "")[:1] or None

    resultado = list(por_cpf.values())
    logger.info(
        f"[SILVER pessoa] tenant={tenant_id} | sances={len(sances)} "
        f"sults={len(sults)} unificados={len(resultado)}"
    )
    return resultado
