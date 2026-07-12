from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter(prefix="/api/menu", tags=["Menu"])


class ModuloMenu(BaseModel):
    codigo: str
    nome: str
    rota: Optional[str] = None


class AplicacaoMenu(BaseModel):
    nome: str
    slug: str
    modulos: List[ModuloMenu]


class SistemaMenu(BaseModel):
    nome: str
    slug: str
    aplicacoes: List[AplicacaoMenu]


class MenuResponse(BaseModel):
    sistemas: List[SistemaMenu]


@router.get("", response_model=MenuResponse)
def obter_menu(current_user: dict = Depends(get_current_user)):
    """
    Devolve a árvore sistema → aplicação → módulo que o usuário logado pode ver.
    Regra: admin vê tudo. Usuário comum só vê módulos onde tem a permissão
    'visualizar' no perfil (via perfil_permissao). Aplicações sem nenhum
    módulo visível não aparecem; sistemas sem nenhuma aplicação visível também não.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT sis.nome AS sistema_nome, sis.slug AS sistema_slug,
                   ap.nome AS aplicacao_nome, ap.slug AS aplicacao_slug,
                   mo.codigo AS modulo_codigo, mo.nome AS modulo_nome, mo.rota AS modulo_rota
            FROM aplicacao ap
            JOIN sistemas sis ON sis.id = ap.sistema_id
            JOIN modulo mo    ON mo.aplicacao_id = ap.id
            ORDER BY sis.nome, ap.nome, mo.nome
            """
        )
        linhas = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    is_admin = bool(current_user.get("is_admin"))
    permissoes = current_user.get("permissoes") or {}

    # dict[sistema_slug] -> { "nome": ..., "aplicacoes": dict[aplicacao_slug] -> AplicacaoMenu }
    sistemas_map: dict[str, dict] = {}

    for r in linhas:
        codigo_modulo = r["modulo_codigo"]
        tem_acesso = is_admin or "visualizar" in permissoes.get(codigo_modulo, [])
        if not tem_acesso:
            continue

        sis_slug = r["sistema_slug"]
        ap_slug = r["aplicacao_slug"]

        if sis_slug not in sistemas_map:
            sistemas_map[sis_slug] = {
                "nome": r["sistema_nome"],
                "slug": sis_slug,
                "aplicacoes": {},
            }

        aplicacoes_do_sistema = sistemas_map[sis_slug]["aplicacoes"]
        if ap_slug not in aplicacoes_do_sistema:
            aplicacoes_do_sistema[ap_slug] = AplicacaoMenu(
                nome=r["aplicacao_nome"], slug=ap_slug, modulos=[]
            )

        aplicacoes_do_sistema[ap_slug].modulos.append(
            ModuloMenu(codigo=codigo_modulo, nome=r["modulo_nome"], rota=r["modulo_rota"])
        )

    sistemas: List[SistemaMenu] = []
    for sis_data in sistemas_map.values():
        aplicacoes = [ap for ap in sis_data["aplicacoes"].values() if ap.modulos]
        if aplicacoes:
            sistemas.append(SistemaMenu(nome=sis_data["nome"], slug=sis_data["slug"], aplicacoes=aplicacoes))

    return MenuResponse(sistemas=sistemas)