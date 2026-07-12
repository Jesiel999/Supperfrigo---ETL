from fastapi import APIRouter, Depends
from database.mysql_connection import connection_mysql
from auth.router import get_current_user
from pydantic import BaseModel

router = APIRouter()

class Empresa(BaseModel):
    codigo_empresa: int
    nome_empresa: str

class EmpresasResponse(BaseModel):
    total: int
    empresas: list[Empresa]

@router.get("/", response_model=EmpresasResponse)
def listar_empresas(current_user: dict = Depends(get_current_user)):
    """Todas as empresas do empresa_bi, sem filtro nenhum.
    Usado pela tela de admin para escolher o que conceder a cada usuário.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT codigo_empresa, nome_empresa FROM empresa_bi ORDER BY codigo_empresa ASC"
        )
        empresas = cursor.fetchall()
        return EmpresasResponse(total=len(empresas), empresas=empresas)
    finally:
        cursor.close()
        conn.close()