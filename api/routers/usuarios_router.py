from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from database.mysql_connection import connection_mysql
from auth.router import get_current_user, pwd_context

router = APIRouter(prefix="/api", tags=["Usuarios"])

class UsuarioEmpresasRequest(BaseModel):
    codigos: List[int]  # [] = sem restrição, vê todas


class UsuarioEmpresasResponse(BaseModel):
    codigos: List[int]
    sem_restricao: bool
    
# ── Models ────────────────────────────────────────────────
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    perfil_id: int


class UsuarioCreate(UsuarioBase):
    username: str
    password: str


class UsuarioUpdate(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    perfil_id: int
    ativo: bool


class UsuarioResponse(UsuarioBase):
    id: int
    username: str
    ativo: bool
    perfil_nome: Optional[str] = None
    perfil_cor: Optional[str] = None
    is_admin: bool = False
    criado_em: Optional[str] = None
    ultimo_acesso: Optional[str] = None


class UsuariosListResponse(BaseModel):
    total: int
    usuarios: list[UsuarioResponse]


class ResetSenhaRequest(BaseModel):
    nova_senha: str


class AtivoRequest(BaseModel):
    ativo: bool


# ── Helpers ───────────────────────────────────────────────
def _exigir_admin(current_user: dict):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")


def _buscar_usuario_por_id(usuario_id: int, conn) -> dict | None:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.id, u.username, u.nome, u.email, u.telefone, u.perfil_id,
                   u.ativo, u.criado_em, u.ultimo_acesso,
                   p.nome AS perfil_nome, p.cor AS perfil_cor, p.is_admin,
                   p.tenant_id AS perfil_tenant_id
            FROM usuarios u
            LEFT JOIN perfil p ON p.id = u.perfil_id
            WHERE u.id = %s
            """,
            (usuario_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def _usuario_to_response(user: dict) -> UsuarioResponse:
    return UsuarioResponse(
        id=user["id"],
        username=user["username"],
        nome=user["nome"],
        email=user["email"],
        telefone=user.get("telefone"),
        perfil_id=user.get("perfil_id"),
        perfil_nome=user.get("perfil_nome"),
        perfil_cor=user.get("perfil_cor"),
        is_admin=bool(user.get("is_admin", 0)),
        ativo=bool(user.get("ativo", 1)),
        criado_em=user.get("criado_em").isoformat() if user.get("criado_em") else None,
        ultimo_acesso=user.get("ultimo_acesso").isoformat() if user.get("ultimo_acesso") else None,
    )


def _sincronizar_tenant_do_usuario(cursor, usuario_id: int, perfil_id: int, ativo: bool = True):
    """
    Garante que o usuário esteja vinculado (usuario_tenant) ao tenant
    dono do perfil selecionado. É isso que resolve o 'usuário criado
    sem tenant' — o tenant é sempre derivado do perfil escolhido.
    """
    cursor.execute("SELECT tenant_id FROM perfil WHERE id = %s", (perfil_id,))
    perfil = cursor.fetchone()
    if not perfil:
        raise HTTPException(status_code=400, detail="Perfil inválido")

    tenant_id = perfil["tenant_id"]

    cursor.execute(
        """
        INSERT INTO usuario_tenant (usuario_id, tenant_id, perfil_id, ativo)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE perfil_id = VALUES(perfil_id), ativo = VALUES(ativo)
        """,
        (usuario_id, tenant_id, perfil_id, 1 if ativo else 0),
    )
    return tenant_id


# ── ENDPOINTS ─────────────────────────────────────────────

@router.get("", response_model=UsuariosListResponse)
def listar_usuarios(
    busca: Optional[str] = Query(None),
    perfil_id: Optional[int] = Query(None),
    ativo: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT u.id, u.username, u.nome, u.email, u.telefone, u.perfil_id,
                   u.ativo, u.criado_em, u.ultimo_acesso,
                   p.nome AS perfil_nome, p.cor AS perfil_cor, p.is_admin
            FROM usuarios u
            LEFT JOIN perfil p ON p.id = u.perfil_id
            WHERE 1=1
        """
        params = []

        if busca:
            query += " AND (u.nome LIKE %s OR u.email LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])

        if perfil_id is not None:
            query += " AND u.perfil_id = %s"
            params.append(perfil_id)

        if ativo is not None:
            query += " AND u.ativo = %s"
            params.append(1 if ativo else 0)

        query += " ORDER BY u.nome ASC"

        cursor.execute(query, params)
        usuarios = cursor.fetchall()

        return UsuariosListResponse(
            total=len(usuarios),
            usuarios=[_usuario_to_response(u) for u in usuarios],
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obter_usuario(usuario_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin") and current_user["id"] != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")

    conn = connection_mysql()
    usuario = _buscar_usuario_por_id(usuario_id, conn)
    conn.close()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    return _usuario_to_response(usuario)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(data: UsuarioCreate, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username já existe")

        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        cursor.execute("SELECT id FROM perfil WHERE id = %s", (data.perfil_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Perfil inválido")

        if len(data.password) < 8:
            raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 8 caracteres")

        hashed_pwd = pwd_context.hash(data.password)

        cursor.execute(
            """
            INSERT INTO usuarios
                (username, nome, email, telefone, hashed_password, perfil_id, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            (data.username, data.nome, data.email, data.telefone or "", hashed_pwd, data.perfil_id),
        )
        usuario_id = cursor.lastrowid

        # >>> É este passo que faltava: sem ele o usuário fica sem tenant <<<
        _sincronizar_tenant_do_usuario(cursor, usuario_id, data.perfil_id, ativo=True)

        conn.commit()

        novo_usuario = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(novo_usuario)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(usuario_id: int, data: UsuarioUpdate, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin") and current_user["id"] != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar este usuário")

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # usuário comum não pode trocar o próprio perfil/status
        if not current_user.get("is_admin"):
            data.perfil_id = usuario["perfil_id"]
            data.ativo = bool(usuario["ativo"])

        cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (data.email, usuario_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        cursor.execute("SELECT id FROM perfil WHERE id = %s", (data.perfil_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Perfil inválido")

        # protege o último admin
        if usuario.get("is_admin") and not data.ativo:
            cursor.execute(
                """
                SELECT COUNT(*) AS total FROM usuarios u
                JOIN perfil p ON p.id = u.perfil_id
                WHERE p.is_admin = 1 AND u.ativo = 1
                """
            )
            if cursor.fetchone()["total"] <= 1:
                raise HTTPException(status_code=400, detail="Não é possível desativar o último administrador")

        cursor.execute(
            """
            UPDATE usuarios
            SET nome = %s, email = %s, telefone = %s, perfil_id = %s, ativo = %s
            WHERE id = %s
            """,
            (data.nome, data.email, data.telefone or "", data.perfil_id, 1 if data.ativo else 0, usuario_id),
        )

        # mantém usuario_tenant sincronizado com o perfil/tenant atual
        _sincronizar_tenant_do_usuario(cursor, usuario_id, data.perfil_id, ativo=data.ativo)

        conn.commit()

        usuario_atualizado = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(usuario_atualizado)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.patch("/{usuario_id}/ativo", response_model=UsuarioResponse)
def toggle_ativo(usuario_id: int, data: AtivoRequest, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        if usuario.get("is_admin") and not data.ativo:
            raise HTTPException(status_code=400, detail="Não é possível desativar um administrador")

        cursor.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (1 if data.ativo else 0, usuario_id))
        cursor.execute(
            "UPDATE usuario_tenant SET ativo = %s WHERE usuario_id = %s",
            (1 if data.ativo else 0, usuario_id),
        )
        conn.commit()

        usuario_atualizado = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(usuario_atualizado)

    except HTTPException:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@router.post("/{usuario_id}/reset-senha")
def reset_senha(usuario_id: int, data: ResetSenhaRequest, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    if len(data.nova_senha) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 8 caracteres")

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        hashed_pwd = pwd_context.hash(data.nova_senha)
        cursor.execute("UPDATE usuarios SET hashed_password = %s WHERE id = %s", (hashed_pwd, usuario_id))
        conn.commit()

        return {"message": "Senha redefinida com sucesso"}
    finally:
        cursor.close()
        conn.close()


@router.delete("/{usuario_id}")
def deletar_usuario(usuario_id: int, current_user: dict = Depends(get_current_user)):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        if usuario.get("is_admin"):
            cursor.execute(
                """
                SELECT COUNT(*) AS total FROM usuarios u
                JOIN perfil p ON p.id = u.perfil_id
                WHERE p.is_admin = 1 AND u.ativo = 1
                """
            )
            if cursor.fetchone()["total"] <= 1:
                raise HTTPException(status_code=400, detail="Não é possível deletar o último administrador")

        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = %s", (usuario_id,))
        cursor.execute("UPDATE usuario_tenant SET ativo = 0 WHERE usuario_id = %s", (usuario_id,))
        conn.commit()

        return {"message": "Usuário deletado com sucesso"}
    except HTTPException:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

@router.get("/{usuario_id}/empresas", response_model=UsuarioEmpresasResponse)
def listar_empresas_usuario(usuario_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin") and current_user["id"] != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        cursor.execute(
            "SELECT codigo_empresa FROM usuario_empresa WHERE usuario_id = %s AND tenant_id = %s",
            (usuario_id, current_user["tenant_id"]),
        )
        codigos = [r["codigo_empresa"] for r in cursor.fetchall()]
        return UsuarioEmpresasResponse(codigos=codigos, sem_restricao=len(codigos) == 0)
    finally:
        cursor.close()
        conn.close()


@router.put("/{usuario_id}/empresas", response_model=UsuarioEmpresasResponse)
def atualizar_empresas_usuario(
    usuario_id: int, data: UsuarioEmpresasRequest, current_user: dict = Depends(get_current_user)
):
    _exigir_admin(current_user)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        tenant_id = current_user["tenant_id"]
        codigos = list(set(data.codigos))

        if codigos:
            placeholders = ",".join(["%s"] * len(codigos))
            cursor.execute(
                f"SELECT codigo_empresa FROM empresa_bi WHERE codigo_empresa IN ({placeholders})",
                tuple(codigos),
            )
            validos = {r["codigo_empresa"] for r in cursor.fetchall()}
            invalidos = set(codigos) - validos
            if invalidos:
                raise HTTPException(status_code=400, detail=f"Códigos inválidos: {sorted(invalidos)}")

        cursor.execute(
            "DELETE FROM usuario_empresa WHERE usuario_id = %s AND tenant_id = %s",
            (usuario_id, tenant_id),
        )
        if codigos:
            cursor.executemany(
                "INSERT INTO usuario_empresa (usuario_id, tenant_id, codigo_empresa) VALUES (%s, %s, %s)",
                [(usuario_id, tenant_id, c) for c in codigos],
            )

        conn.commit()
        return UsuarioEmpresasResponse(codigos=codigos, sem_restricao=len(codigos) == 0)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar empresas: {str(e)}")
    finally:
        cursor.close()
        conn.close()