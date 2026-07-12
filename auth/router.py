from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

from database.mysql_connection import connection_mysql
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

logger = logging.getLogger(__name__)
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Models ────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


class AlterarSenha(BaseModel):
    senha_atual: str
    nova_senha: str


# ── Helpers de senha/token ─────────────────────────────────────────
def verificar_senha(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def criar_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Busca básica por username (login) ──────────────────────────────
def _buscar_usuario_raw(username: str) -> dict | None:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, username, nome, email, telefone,
                   hashed_password, perfil_id, ativo
            FROM usuarios
            WHERE username = %s
            """,
            (username,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ── Dados do perfil (fonte única de permissões, direto do usuário) ─
def _buscar_perfil(perfil_id: int) -> dict | None:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, tenant_id, nome, descricao, cor, is_admin, ativo
            FROM perfil
            WHERE id = %s
            """,
            (perfil_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def _buscar_permissoes_perfil(perfil_id: int) -> dict:
    """Permissões reais do perfil, vindas de perfil_permissao/permissao/modulo."""
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
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
        perms: dict[str, list] = {}
        for r in cursor.fetchall():
            perms.setdefault(r["modulo"], []).append(r["acao"])
        return perms
    finally:
        cursor.close()
        conn.close()


# ── Monta o objeto de usuário completo (usado em login e /me) ─────
def _montar_usuario_completo(user: dict, tenant_id: int | None = None) -> dict:
    perfil = _buscar_perfil(user["perfil_id"]) if user.get("perfil_id") else None
    permissoes = _buscar_permissoes_perfil(user["perfil_id"]) if user.get("perfil_id") else {}

    # tenant efetivo: o solicitado, senão o do próprio perfil
    tenant_id = tenant_id or (perfil["tenant_id"] if perfil else None)

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_info = None
        if tenant_id:
            cursor.execute("SELECT id, nome, slug FROM tenant WHERE id = %s", (tenant_id,))
            tenant_info = cursor.fetchone()

        cursor.execute(
            """
            SELECT eb.codigo_empresa AS codigo, eb.nome_empresa AS nome
            FROM usuario_empresa ue
            JOIN empresa_bi eb ON eb.codigo_empresa = ue.codigo_empresa
            WHERE ue.usuario_id = %s AND ue.tenant_id = %s
            ORDER BY eb.nome_empresa
            """,
            (user["id"], tenant_id),
        )
        empresas = cursor.fetchall()
        # ---- Loger de retorno de empresas
        # logger.info("Empresas retornadas: %s", empresas)
        cursor.execute(
            """
            SELECT t.id, t.nome, t.slug
            FROM usuario_tenant ut
            JOIN tenant t ON t.id = ut.tenant_id
            WHERE ut.usuario_id = %s AND ut.ativo = 1 AND t.ativo = 1
            """,
            (user["id"],),
        )
        tenants = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    
    return {
        "id": user["id"],
        "username": user["username"],
        "nome": user["nome"],
        "email": user["email"],
        "telefone": user.get("telefone"),
        "ativo": bool(user.get("ativo", 1)),

        "perfil_id": user.get("perfil_id"),
        "perfil_nome": perfil["nome"] if perfil else None,
        "perfil_cor": perfil["cor"] if perfil else None,
        "is_admin": bool(perfil["is_admin"]) if perfil else False,
        "permissoes": permissoes,

        "tenant_id": tenant_info["id"] if tenant_info else None,
        "tenant_nome": tenant_info["nome"] if tenant_info else None,
        "tenant_slug": tenant_info["slug"] if tenant_info else None,
        "empresas": [
            {"codigo": e["codigo"], "nome": e["nome"]} for e in empresas
        ],
        "tenants": [{"id": t["id"], "nome": t["nome"], "slug": t["slug"]} for t in tenants],
    }


def _atualizar_ultimo_acesso(usuario_id: int):
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET ultimo_acesso = NOW() WHERE id = %s", (usuario_id,))
        conn.commit()
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()


# ── get_current_user — usado em todos os endpoints protegidos ──────
async def get_current_user(token: str = Depends(oauth2)) -> dict:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise exc
    except JWTError:
        raise exc

    user = _buscar_usuario_raw(username)
    if not user or not user.get("ativo", 1):
        raise exc

    completo = _montar_usuario_completo(user, tenant_id=payload.get("tenant_id"))
    completo["_hashed_password"] = user["hashed_password"]
    return completo


# ── /auth/login ─────────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _buscar_usuario_raw(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    if not user.get("hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário sem senha cadastrada",
        )

    if not verificar_senha(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if int(user.get("ativo", 1)) != 1:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    if not user.get("perfil_id"):
        raise HTTPException(
            status_code=403,
            detail="Usuário sem perfil vinculado. Contate o administrador.",
        )

    # tenant_id pode vir explicitamente no client_id do form OAuth2
    tenant_id = None
    if getattr(form_data, "client_id", None):
        try:
            tenant_id = int(form_data.client_id)
        except (ValueError, TypeError):
            pass

    usuario_completo = _montar_usuario_completo(user, tenant_id=tenant_id)

    if not usuario_completo.get("tenant_id"):
        raise HTTPException(
            status_code=403,
            detail="Usuário sem tenant vinculado. Contate o administrador.",
        )

    _atualizar_ultimo_acesso(user["id"])

    token = criar_token({
        "sub": user["username"],
        "tenant_id": usuario_completo["tenant_id"],
    })

    return {"access_token": token, "token_type": "bearer", "usuario": usuario_completo}


# ── /auth/me ──────────────────────────────────────────────────────
@router.get("/me")
def me(current=Depends(get_current_user)):
    return {k: v for k, v in current.items() if k != "_hashed_password"}


# ── /auth/alterar-senha (o próprio usuário troca a própria senha) ──
@router.put("/alterar-senha")
def alterar_senha(body: AlterarSenha, current=Depends(get_current_user)):
    if not verificar_senha(body.senha_atual, current.get("_hashed_password", "")):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    nova_hash = pwd_context.hash(body.nova_senha)
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE usuarios SET hashed_password = %s WHERE id = %s",
            (nova_hash, current["id"]),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"status": "Senha alterada com sucesso"}


# ── /auth/trocar-tenant ─────────────────────────────────────────────
class TrocarTenantRequest(BaseModel):
    tenant_id: int


@router.post("/trocar-tenant")
def trocar_tenant(data: TrocarTenantRequest, usuario: dict = Depends(get_current_user)):
    tenant_id = data.tenant_id
    if not any(t["id"] == tenant_id for t in usuario.get("tenants", [])):
        raise HTTPException(status_code=403, detail="Sem acesso a este tenant")

    user_raw = _buscar_usuario_raw(usuario["username"])
    usuario_novo = _montar_usuario_completo(user_raw, tenant_id=tenant_id)

    token = criar_token({"sub": usuario["username"], "tenant_id": tenant_id})
    return {"access_token": token, "token_type": "bearer", "usuario": usuario_novo}