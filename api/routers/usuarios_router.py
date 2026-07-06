from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

# ── Models ────────────────────────────────────────────────
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    role: str  # 'admin', 'gestor', 'analista', 'operador'
    perfil_id: str

class UsuarioCreate(UsuarioBase):
    username: str
    password: str

class UsuarioUpdate(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    role: str
    perfil_id: str
    ativo: bool

class UsuarioResponse(UsuarioBase):
    id: str
    username: str
    ativo: bool
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
def _buscar_usuario_por_id(usuario_id: str, conn) -> dict | None:
    """Busca um usuário específico no banco"""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, username, nome, email, telefone, role, perfil_id, ativo, role,
                   criado_em, ultimo_acesso
            FROM usuarios WHERE id = %s
        """, (usuario_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

def _usuario_to_response(user: dict) -> UsuarioResponse:
    """Converte dados do banco para response"""
    return UsuarioResponse(
        id=user["id"],
        username=user["username"],
        nome=user["nome"],
        email=user["email"],
        telefone=user.get("telefone"),
        role=user.get("role", "operador"),
        perfil_id=user.get("perfil_id", ""),
        ativo=bool(user.get("ativo", 1)),
        criado_em=user.get("criado_em").isoformat() if user.get("criado_em") else None,
        ultimo_acesso=user.get("ultimo_acesso").isoformat() if user.get("ultimo_acesso") else None
    )

# ── ENDPOINTS ─────────────────────────────────────────────

@router.get("", response_model=UsuariosListResponse)
def listar_usuarios(
    busca: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    ativo: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    print("role:", current_user.get("role"))
    """
    Lista todos os usuários do tenant atual.
    Filtra por busca (nome/email), role e status ativo.
    """
    # Verificar permissão de acesso (apenas admin)
    if current_user.get("role") not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para listar usuários"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Montar query com filtros dinâmicos
        query = "SELECT * FROM usuarios WHERE 1=1"
        params = []
        
        if busca:
            query += " AND (nome LIKE %s OR email LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        
        if role:
            query += " AND role = %s"
            params.append(role)
        
        if ativo is not None:
            query += " AND ativo = %s"
            params.append(1 if ativo else 0)
        
        query += " ORDER BY nome ASC"
        
        cursor.execute(query, params)
        usuarios = cursor.fetchall()
        
        return UsuariosListResponse(
            total=len(usuarios),
            usuarios=[_usuario_to_response(u) for u in usuarios]
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obter_usuario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém dados de um usuário específico.
    """
    # Usuário só pode ver a si mesmo, admin vê todos
    if current_user.get("role") != "admin" and current_user["id"] != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    usuario = _buscar_usuario_por_id(usuario_id, conn)
    conn.close()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return _usuario_to_response(usuario)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    data: UsuarioCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um novo usuário.
    Apenas admin pode criar usuários.
    """
    # Verificar permissão
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para criar usuários"
        )
    
    # Validar username único
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (data.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )
        
        # Importar helpers de auth para hash de senha
        from auth.router import pwd_context
        import uuid
        
        usuario_id = str(uuid.uuid4())
        hashed_pwd = pwd_context.hash(data.password)
        
        cursor.execute("""
            INSERT INTO usuarios 
            (id, username, nome, email, telefone, hashed_password, role, perfil_id, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario_id, data.username, data.nome, data.email, 
            data.telefone or "", hashed_pwd, data.role, data.perfil_id, 1
        ))
        
        conn.commit()
        
        # Buscar e retornar o usuário criado
        novo_usuario = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(novo_usuario)
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar usuário: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: str,
    data: UsuarioUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Atualiza dados de um usuário.
    Admin pode editar qualquer usuário. Usuário pode editar a si mesmo.
    """
    # Verificar permissão
    if current_user.get("role") != "admin" and current_user["id"] != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para editar este usuário"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validar existência
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Validar email único (excluindo o próprio)
        cursor.execute(
            "SELECT id FROM usuarios WHERE email = %s AND id != %s",
            (data.email, usuario_id)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )
        
        # Atualizar
        cursor.execute("""
            UPDATE usuarios 
            SET nome = %s, email = %s, telefone = %s, 
                role = %s, perfil_id = %s, ativo = %s
            WHERE id = %s
        """, (
            data.nome, data.email, data.telefone or "",
            data.role, data.perfil_id, 1 if data.ativo else 0,
            usuario_id
        ))
        
        conn.commit()
        
        # Retornar usuário atualizado
        usuario_atualizado = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(usuario_atualizado)
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao atualizar: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.patch("/{usuario_id}/ativo")
def toggle_ativo(
    usuario_id: str,
    data: AtivoRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ativa ou desativa um usuário.
    Admin pode desativar qualquer usuário (exceto outros admins).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Proteger admin
        if usuario.get("role") == "admin" and not data.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível desativar um administrador"
            )
        
        cursor.execute(
            "UPDATE usuarios SET ativo = %s WHERE id = %s",
            (1 if data.ativo else 0, usuario_id)
        )
        conn.commit()
        
        usuario_atualizado = _buscar_usuario_por_id(usuario_id, conn)
        return _usuario_to_response(usuario_atualizado)
        
    finally:
        cursor.close()
        conn.close()


@router.post("/{usuario_id}/reset-senha")
def reset_senha(
    usuario_id: str,
    data: ResetSenhaRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Reseta a senha de um usuário.
    Apenas admin pode fazer isso.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    if len(data.nova_senha) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha deve ter no mínimo 8 caracteres"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        from auth.router import pwd_context
        
        hashed_pwd = pwd_context.hash(data.nova_senha)
        cursor.execute(
            "UPDATE usuarios SET hashed_password = %s WHERE id = %s",
            (hashed_pwd, usuario_id)
        )
        conn.commit()
        
        return {"message": "Senha redefinida com sucesso"}
        
    finally:
        cursor.close()
        conn.close()


@router.delete("/{usuario_id}")
def deletar_usuario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deleta um usuário (soft delete via ativo=false).
    Apenas admin pode deletar.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        usuario = _buscar_usuario_por_id(usuario_id, conn)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Proteger último admin
        if usuario.get("role") == "admin":
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE role = 'admin' AND ativo = 1")
            result = cursor.fetchone()
            if result["count"] <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não é possível deletar o último administrador"
                )
        
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = %s", (usuario_id,))
        conn.commit()
        
        return {"message": "Usuário deletado com sucesso"}
        
    finally:
        cursor.close()
        conn.close()