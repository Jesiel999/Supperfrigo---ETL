from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, List

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter(prefix="/api", tags=["Permissoes"])


# ── Models ────────────────────────────────────────────────
class PermissaoItem(BaseModel):
    recurso: str
    label: str
    categoria: str
    visualizar: bool = False
    criar: bool = False
    editar: bool = False
    excluir: bool = False


class PerfilBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    cor: str = "#64748b"


class PerfilCreate(PerfilBase):
    permissoes: Dict[str, Dict[str, bool]]


class PerfilUpdate(PerfilBase):
    permissoes: Dict[str, Dict[str, bool]]


class PerfilResponse(PerfilBase):
    id: int
    total_usuarios: int
    permissoes: List[PermissaoItem]
    ativo: bool = True
    is_admin: bool = False


class PermissoesListResponse(BaseModel):
    total: int
    perfis: List[PerfilResponse]


class RecursoResponse(BaseModel):
    recurso: str
    label: str
    categoria: str


class RecursosResponse(BaseModel):
    recursos: List[RecursoResponse]


class CategoriasResponse(BaseModel):
    categorias: List[str]


# ── Helpers ───────────────────────────────────────────────
def _exigir_admin(current_user: dict):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")


def _listar_modulos(cursor) -> List[dict]:
    cursor.execute(
        """
        SELECT mo.codigo AS recurso, mo.nome AS label, ap.nome AS categoria, mo.id AS modulo_id
        FROM modulo mo
        JOIN aplicacao ap ON ap.id = mo.aplicacao_id
        ORDER BY ap.nome, mo.nome
        """
    )
    return cursor.fetchall()


def _buscar_perfil_por_id(perfil_id: int, cursor) -> dict | None:
    cursor.execute(
        "SELECT id, tenant_id, nome, descricao, cor, ativo, is_admin FROM perfil WHERE id = %s",
        (perfil_id,),
    )
    return cursor.fetchone()


def _buscar_permissoes_perfil(perfil_id: int, cursor) -> List[PermissaoItem]:
    """Lê as permissões reais do perfil, cruzando com todos os módulos existentes."""
    modulos = _listar_modulos(cursor)

    cursor.execute(
        """
        SELECT mo.codigo AS modulo, pe.codigo AS acao
        FROM perfil_permissao pp
        JOIN permissao pe ON pe.id = pp.permissao_id
        JOIN modulo mo    ON mo.id = pe.modulo_id
        WHERE pp.perfil_id = %s
        """,
        (perfil_id,),
    )
    concedidas: dict[str, set] = {}
    for r in cursor.fetchall():
        concedidas.setdefault(r["modulo"], set()).add(r["acao"])

    itens = []
    for m in modulos:
        acoes = concedidas.get(m["recurso"], set())
        itens.append(
            PermissaoItem(
                recurso=m["recurso"],
                label=m["label"],
                categoria=m["categoria"],
                visualizar="visualizar" in acoes,
                criar="criar" in acoes,
                editar="editar" in acoes,
                excluir="excluir" in acoes,
            )
        )
    return itens


def _contar_usuarios_perfil(perfil_id: int, cursor) -> int:
    cursor.execute(
        "SELECT COUNT(*) AS total FROM usuarios WHERE perfil_id = %s AND ativo = 1",
        (perfil_id,),
    )
    r = cursor.fetchone()
    return r["total"] if r else 0


def _perfil_to_response(perfil: dict, cursor) -> PerfilResponse:
    permissoes = _buscar_permissoes_perfil(perfil["id"], cursor)
    total_usuarios = _contar_usuarios_perfil(perfil["id"], cursor)

    return PerfilResponse(
        id=perfil["id"],
        nome=perfil["nome"],
        descricao=perfil.get("descricao") or "",
        cor=perfil.get("cor") or "#64748b",
        total_usuarios=total_usuarios,
        permissoes=permissoes,
        ativo=bool(perfil.get("ativo", 1)),
        is_admin=bool(perfil.get("is_admin", 0)),
    )


def _salvar_permissoes(perfil_id: int, permissoes: Dict[str, Dict[str, bool]], cursor):
    cursor.execute(
        """
        SELECT pe.id, mo.codigo AS modulo, pe.codigo AS acao
        FROM permissao pe
        JOIN modulo mo ON mo.id = pe.modulo_id
        """
    )
    permissao_id_por_chave = {(r["modulo"], r["acao"]): r["id"] for r in cursor.fetchall()}

    cursor.execute("DELETE FROM perfil_permissao WHERE perfil_id = %s", (perfil_id,))

    linhas = []
    for recurso, acoes in permissoes.items():
        for acao, marcado in acoes.items():
            if not marcado:
                continue
            permissao_id = permissao_id_por_chave.get((recurso, acao))
            if permissao_id:
                linhas.append((perfil_id, permissao_id))

    if linhas:
        cursor.executemany(
            "INSERT INTO perfil_permissao (perfil_id, permissao_id) VALUES (%s, %s)",
            linhas,
        )


# ── ENDPOINTS ─────────────────────────────────────────────

@router.get("/recursos", response_model=RecursosResponse)
def listar_recursos(current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        modulos = _listar_modulos(cursor)
        return RecursosResponse(
            recursos=[RecursoResponse(recurso=m["recurso"], label=m["label"], categoria=m["categoria"]) for m in modulos]
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/categorias", response_model=CategoriasResponse)
def listar_categorias(current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT DISTINCT nome FROM aplicacao ORDER BY nome")
        categorias = [r["nome"] for r in cursor.fetchall()]
        return CategoriasResponse(categorias=categorias)
    finally:
        cursor.close()
        conn.close()


@router.get("/perfis", response_model=PermissoesListResponse)
def listar_perfis(current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        # perfis do mesmo tenant do usuário logado
        cursor.execute(
            "SELECT id, tenant_id, nome, descricao, cor, ativo, is_admin FROM perfil WHERE tenant_id = %s ORDER BY nome ASC",
            (current_user["tenant_id"],),
        )
        perfis_db = cursor.fetchall()
        perfis_response = [_perfil_to_response(p, cursor) for p in perfis_db]

        return PermissoesListResponse(total=len(perfis_response), perfis=perfis_response)
    finally:
        cursor.close()
        conn.close()


@router.get("/perfis/{perfil_id}", response_model=PerfilResponse)
def obter_perfil(perfil_id: int, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        perfil = _buscar_perfil_por_id(perfil_id, cursor)
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")
        return _perfil_to_response(perfil, cursor)
    finally:
        cursor.close()
        conn.close()


@router.post("/perfis", response_model=PerfilResponse, status_code=status.HTTP_201_CREATED)
def criar_perfil(data: PerfilCreate, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id FROM perfil WHERE nome = %s AND tenant_id = %s",
            (data.nome, current_user["tenant_id"]),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Já existe um perfil com este nome")

        cursor.execute(
            "INSERT INTO perfil (tenant_id, nome, descricao, cor, ativo) VALUES (%s, %s, %s, %s, 1)",
            (current_user["tenant_id"], data.nome, data.descricao or "", data.cor),
        )
        perfil_id = cursor.lastrowid

        _salvar_permissoes(perfil_id, data.permissoes, cursor)
        conn.commit()

        perfil = _buscar_perfil_por_id(perfil_id, cursor)
        return _perfil_to_response(perfil, cursor)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar perfil: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.put("/perfis/{perfil_id}", response_model=PerfilResponse)
def atualizar_perfil(perfil_id: int, data: PerfilUpdate, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        perfil = _buscar_perfil_por_id(perfil_id, cursor)
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        if perfil.get("is_admin"):
            raise HTTPException(status_code=400, detail="Perfil administrador não pode ser editado")

        cursor.execute(
            "SELECT id FROM perfil WHERE nome = %s AND id != %s AND tenant_id = %s",
            (data.nome, perfil_id, perfil["tenant_id"]),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Já existe outro perfil com este nome")

        cursor.execute(
            "UPDATE perfil SET nome = %s, descricao = %s, cor = %s WHERE id = %s",
            (data.nome, data.descricao or "", data.cor, perfil_id),
        )

        _salvar_permissoes(perfil_id, data.permissoes, cursor)
        conn.commit()

        perfil_atualizado = _buscar_perfil_por_id(perfil_id, cursor)
        return _perfil_to_response(perfil_atualizado, cursor)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.delete("/perfis/{perfil_id}")
def deletar_perfil(perfil_id: int, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        perfil = _buscar_perfil_por_id(perfil_id, cursor)
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        if perfil.get("is_admin"):
            raise HTTPException(status_code=400, detail="Não é possível deletar o perfil administrador")

        total_usuarios = _contar_usuarios_perfil(perfil_id, cursor)
        if total_usuarios > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível deletar um perfil com {total_usuarios} usuário(s) atribuído(s)",
            )

        cursor.execute("DELETE FROM perfil WHERE id = %s", (perfil_id,))
        conn.commit()

        return {"message": "Perfil deletado com sucesso"}
    except HTTPException:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()