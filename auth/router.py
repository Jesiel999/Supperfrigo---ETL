import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from database.mysql_connection import connection_mysql
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

# ── Suporta AMBOS os algoritmos de hash ──────────────────────────
# pbkdf2_sha256 = sistema antigo (tabela usuarios)
# bcrypt        = sistema novo   (tabela usuarios)
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Models ────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type:   str
    usuarios:      dict


class AlterarSenha(BaseModel):
    senha_atual: str
    nova_senha:  str


# ── Helpers ───────────────────────────────────────────────────────
def verificar_senha(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def criar_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Busca unificada: tenta tabela nova → fallback tabela antiga ───
def _buscar_usuarios_raw(username: str) -> dict | None:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                username,
                nome,
                email,
                hashed_password,
                ativo
            FROM usuarios
            WHERE username = %s
        """, (username,))

        row = cursor.fetchone()

        if row:
            row["origem"] = "nova"

        return row

    finally:
        cursor.close()
        conn.close()

def _buscar_usuarios(usuario_id: str, tenant_id: int) -> dict | None:
    """Busca dados completos multi-tenant (tabelas novas)."""
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                u.id, u.username, u.nome, u.email, u.ativo,
                t.id   AS tenant_id,
                t.nome AS tenant_nome,
                t.slug AS tenant_slug,
                p.id   AS perfil_id,
                p.nome AS role,
                p.cor  AS perfil_cor
            FROM usuarios u
            JOIN usuario_tenant ut ON ut.usuario_id = u.id
            JOIN tenant t          ON t.id  = ut.tenant_id
            JOIN perfil p          ON p.id  = ut.perfil_id
            WHERE u.id = %s AND t.id = %s
              AND u.ativo = 1 AND ut.ativo = 1
        """, (usuario_id, tenant_id))
        rows = cursor.fetchall()

        if not rows:
            return None

        base = rows[0]
        if not base:
            return None

        # Permissões
        cursor.execute("""
            SELECT mo.codigo AS modulo, pe.codigo AS acao
            FROM perfil_permissao pp
            JOIN permissao pe ON pe.id = pp.permissao_id
            JOIN modulo    mo ON mo.id = pe.modulo_id
            WHERE pp.perfil_id = %s
        """, (base["perfil_id"],))
        perms: dict[str, list] = {}
        for r in cursor.fetchall():
            perms.setdefault(r["modulo"], []).append(r["acao"])

        # Empresas autorizadas
        cursor.execute("""
            SELECT codigo_empresa, nome_empresa FROM usuario_empresa
            WHERE usuario_id = %s AND tenant_id = %s
        """, (usuario_id, tenant_id))
        empresas = cursor.fetchall()

        # Todos os tenants
        cursor.execute("""
            SELECT t.id, t.nome, t.slug FROM usuario_tenant ut
            JOIN tenant t ON t.id = ut.tenant_id
            WHERE ut.usuario_id = %s AND ut.ativo = 1 AND t.ativo = 1
        """, (usuario_id,))
        tenants = cursor.fetchall()

        return {
            "id":          base["id"],
            "username":    base["username"],
            "nome":        base["nome"],
            "email":       base["email"],
            "tenant_id":   base["tenant_id"],
            "tenant_nome": base["tenant_nome"],
            "tenant_slug": base["tenant_slug"],
            "perfil_id":   base["perfil_id"],
            "role": base["role"],
            "perfil_cor":  base["perfil_cor"],
            "permissoes":  perms,
            "empresas": [
                {"codigo": e["codigo_empresa"], "nome": e["nome_empresa"]}
                for e in empresas
            ],
            "tenants": [
                {"id": t["id"], "nome": t["nome"], "slug": t["slug"]}
                for t in tenants
            ],
        }
    finally:
        cursor.close()
        conn.close()


def _atualizar_ultimo_acesso(usuario_id: str, tabela: str):
    conn   = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE {tabela} SET ultimo_acesso = NOW() WHERE id = %s",
            (usuario_id,)
        )
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
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        origem   = payload.get("origem", "nova")
        if not username:
            raise exc
    except JWTError:
        raise exc

    user = _buscar_usuarios_raw(username)
    if not user:
        raise exc

    # Para sistema novo, enriquece com permissões multi-tenant
    if origem == "nova":
        tenant_id = payload.get("tenant_id")
        if tenant_id:
            completo = _buscar_usuarios(
                user["id"],
                int(tenant_id)
            )

            if completo:
                completo["_hashed_password"] = user["hashed_password"]
                return completo

    # Fallback: retorna dados básicos (compatibilidade sistema antigo)
    perfil_id = user.get("perfil_id", "")
    user["permissoes"] = _buscar_permissoes_antigas(perfil_id) if perfil_id else []
    user["_hashed_password"] = user.pop("hashed_password", "")
    return user


# ── /auth/login — compatível com sistema antigo e novo ────────────
@router.post("/login", response_model=Token)   # alias para o novo sistema
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Aceita POST em /auth/login (sistema antigo) e /auth/token (sistema novo).
    Detecta automaticamente em qual tabela o usuário está.
    """
    user = _buscar_usuarios_raw(form_data.username)

    origem = user.get("origem", "nova")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

        print("=" * 80)
        print("USUARIO:", form_data.username)
        print("HASH:", user.get("hashed_password"))
        print("SENHA:", form_data.password)
        print("=" * 80)

    if not user.get("hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário sem senha cadastrada",
        )

    try:
        senha_valida = verificar_senha(
            form_data.password,
            user["hashed_password"]
        )
    except Exception as e:
        print("ERRO HASH:", e)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hash de senha inválido",
        )

    if not senha_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if int(user.get("ativo", 1)) != 1:
        raise HTTPException(
            status_code=400,
            detail="Usuário inativo"
        )

    # ── Sistema NOVO: multi-tenant ─────────────────────────────
    if origem == "nova":
        conn   = connection_mysql()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT tenant_id FROM usuario_tenant WHERE usuario_id = %s AND ativo = 1",
                (user["id"],)
            )
            tenants = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        if not tenants:
            raise HTTPException(status_code=403, detail="Usuário sem tenant ativo")

        # tenant_id pode vir no client_id do form OAuth2
        tenant_id = None
        if hasattr(form_data, "client_id") and form_data.client_id:
            try:
                tenant_id = int(form_data.client_id)
            except (ValueError, TypeError):
                pass
        tenant_id = tenant_id or tenants[0]["tenant_id"]

        usuarios_completo = _buscar_usuarios(user["id"], tenant_id)
        if not usuarios_completo:
            raise HTTPException(status_code=403, detail="Acesso negado a este tenant")

        _atualizar_ultimo_acesso(user["id"], "usuarios")

        token = criar_token({
            "sub":       user["username"],
            "tenant_id": tenant_id,
            "origem":    "nova",
        })
        return {"access_token": token, "token_type": "bearer", "usuarios": usuarios_completo}

    # ── Sistema ANTIGO: compatibilidade ────────────────────────
    perfil_id  = user.get("perfil_id", "")
    permissoes = _buscar_permissoes_antigas(perfil_id) if perfil_id else []

    _atualizar_ultimo_acesso(user["id"], "usuarios")

    token = criar_token({
        "sub":       user["username"],
        "role":      user.get("role", "operador"),
        "perfil_id": perfil_id,
        "origem":    "antiga",
    })

    return {
        "access_token": token,
        "token_type":   "bearer",
        "usuarios": {
            "id":         user["id"],
            "username":   user["username"],
            "nome":       user["nome"],
            "email":      user["email"],
            "role":       user.get("role", "operador"),
            "perfil_id":  perfil_id,
            "permissoes": permissoes,
            # Campos novos com fallback para não quebrar o Angular
            "tenant_id":   None,
            "tenant_nome": None,
            "empresas":    [],
            "tenants":     [],
        },
    }


# ── /auth/me ──────────────────────────────────────────────────────
@router.get("/me")
def me(current=Depends(get_current_user)):
    return {k: v for k, v in current.items() if k not in ("hashed_password")}


# ── /auth/alterar-senha ───────────────────────────────────────────
@router.put("/alterar-senha")
def alterar_senha(body: AlterarSenha, current=Depends(get_current_user)):
    if not verificar_senha(
        body.senha_atual,
        current.get("_hashed_password", "")
    ):
        raise HTTPException(
            status_code=400,
            detail="Senha atual incorreta"
        )

    nova_hash = pwd_context.hash(body.nova_senha)
    conn   = connection_mysql()
    cursor = conn.cursor()
    try:
        # Atualiza na tabela correta conforme origem
        tabela = "usuarios" if current.get("tenant_id") else "usuarios"
        campo  = "hashed_password"
        cursor.execute(
            f"UPDATE {tabela} SET {campo} = %s WHERE id = %s",
            (nova_hash, current["id"])
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"status": "Senha alterada com sucesso"}
    

# ── /auth/trocar-tenant ───────────────────────────────────────────
@router.post("/trocar-tenant")
def trocar_tenant(tenant_id: int, usuarios: dict = Depends(get_current_user)):
    if not any(t["id"] == tenant_id for t in usuarios.get("tenants", [])):
        raise HTTPException(status_code=403, detail="Sem acesso a este tenant")

    usuarios_novo = _buscar_usuarios(usuarios["id"], tenant_id)
    if not usuarios_novo:
        raise HTTPException(status_code=403, detail="Acesso negado")

    token = criar_token({
        "sub":       usuarios["username"],
        "tenant_id": tenant_id,
        "origem":    "nova",
    })
    return {"access_token": token, "token_type": "bearer", "usuarios": usuarios_novo}
