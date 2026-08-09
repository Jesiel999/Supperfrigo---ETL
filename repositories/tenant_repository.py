import logging
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


def buscar_token_por_nome(nome: str) -> str | None:
    """
    Busca um token pelo campo `nome` em tenant_config.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT token FROM tenant_config WHERE nome = %s AND ativo = 1",
        (nome,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        logger.warning(f"Nenhum token ativo encontrado em tenant_config para nome={nome}")
        return None

    return row["token"]


def listar_tenants_ativos() -> list[dict]:
    return [{"id": 1, "nome": "Tenant Único"}]
