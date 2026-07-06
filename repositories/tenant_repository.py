from database.mysql_connection import connection_mysql
import logging

logger = logging.getLogger(__name__)


def listar_tenants_ativos() -> list[dict]:
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nome, slug FROM tenant WHERE ativo = 1")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def buscar_config_tenant(tenant_id: int) -> dict | None:
    """
    Busca configurações do tenant incluindo token da API Sances.
    Requer tabela tenant_config (criada abaixo se não existir).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        # Cria tabela de config se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_config (
                tenant_id     INT          NOT NULL PRIMARY KEY,
                nome    VARCHAR(80)     NOT NULL,
                token  VARCHAR(500),
                ativo         TINYINT(1)   NOT NULL DEFAULT 1,
                FOREIGN KEY (tenant_id) REFERENCES tenant(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()

        cursor.execute(
            "SELECT * FROM tenant_config WHERE tenant_id = %s",
            (tenant_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
