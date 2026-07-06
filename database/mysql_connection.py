import mysql.connector
from mysql.connector import Error
from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
import logging

logger = logging.getLogger(__name__)


def connection_mysql():
    """Retorna uma conexão MySQL com autocommit desativado."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_0900_ai_ci",
            autocommit=False,
            connection_timeout=30
        )
        logger.info("Conexão MySQL estabelecida com sucesso.")
        return conn

    except Error as e:
        logger.error(f"Erro ao conectar no MySQL: {e}")
        raise
