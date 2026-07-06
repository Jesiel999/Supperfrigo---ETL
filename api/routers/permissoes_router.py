from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, List

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter(prefix="/api/permissoes", tags=["Permissoes"])

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
RECURSOS_PADRAO = [
    {"recurso": "dashboard_inadimplencia", "label": "Dashboard Inadimplência", "categoria": "Financeiro"},
    {"recurso": "dashboard_dre", "label": "DRE", "categoria": "Financeiro"},
    {"recurso": "dashboard_pmp", "label": "PMP", "categoria": "Financeiro"},
    {"recurso": "dashboard_aging", "label": "Aging Report", "categoria": "Financeiro"},
    {"recurso": "cobrancas", "label": "Cobranças", "categoria": "Financeiro"},
    {"recurso": "contas_receber", "label": "Contas a Receber", "categoria": "Financeiro"},
    {"recurso": "contas_pagar", "label": "Contas a Pagar", "categoria": "Financeiro"},
    {"recurso": "fluxo_caixa", "label": "Fluxo de Caixa", "categoria": "Financeiro"},
    {"recurso": "relatorios", "label": "Relatórios", "categoria": "Financeiro"},
    {"recurso": "geral", "label": "Geral", "categoria": "Operações"},
    {"recurso": "admin_usuarios", "label": "Gestão de Usuários", "categoria": "Admin"},
    {"recurso": "admin_permissoes", "label": "Perfis & Permissões", "categoria": "Admin"},
]

CATEGORIAS_PADRAO = ["Financeiro", "Operações", "Admin"]

def _buscar_perfil_por_id(perfil_id: str, conn) -> dict | None:
    """Busca um perfil no banco"""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nome, descricao, cor, ativo FROM perfil WHERE id = %s
        """, (perfil_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

def _buscar_permissoes_perfil(perfil_id: str, conn) -> List[PermissaoItem]:
    """Busca as permissões de um perfil"""
    cursor = conn.cursor(dictionary=True)
    try:
        # Para simplicidade, retorna permissões mockadas
        # Em produção, isso viria do banco (tabelas perfil_permissao, permissao, etc)
        permissoes = []
        
        for recurso in RECURSOS_PADRAO:
            # Mock: admin tem tudo, demais têm restrições
            if perfil_id == "perfil_admin":
                perm = PermissaoItem(
                    **recurso,
                    visualizar=True, criar=True, editar=True, excluir=True
                )
            elif perfil_id == "perfil_gestor":
                perm = PermissaoItem(
                    **recurso,
                    visualizar=not recurso["recurso"].startswith("admin_"),
                    criar=recurso["recurso"] in ["cobrancas", "contas_receber", "contas_pagar"],
                    editar=recurso["recurso"] in ["cobrancas", "contas_receber", "contas_pagar"],
                    excluir=False
                )
            elif perfil_id == "perfil_analista":
                perm = PermissaoItem(
                    **recurso,
                    visualizar=recurso["recurso"].startswith("dashboard_") or recurso["recurso"] == "relatorios",
                    criar=False, editar=False, excluir=False
                )
            elif perfil_id == "perfil_operador":
                perm = PermissaoItem(
                    **recurso,
                    visualizar=recurso["recurso"] in ["veiculos", "fretes", "dashboard_inadimplencia"],
                    criar=recurso["recurso"] in ["geral"],
                    editar=recurso["recurso"] in ["geral"],
                    excluir=False
                )
            else:
                perm = PermissaoItem(**recurso)
            
            permissoes.append(perm)
        
        return permissoes
    finally:
        cursor.close()

def _contar_usuarios_perfil(perfil_id: str, conn) -> int:
    """Conta quantos usuários usam um perfil"""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT COUNT(*) as count FROM usuarios WHERE perfil_id = %s AND ativo = 1",
            (perfil_id,)
        )
        result = cursor.fetchone()
        return result["count"] if result else 0
    finally:
        cursor.close()

def _perfil_to_response(perfil: dict, conn) -> PerfilResponse:
    """Converte dados do banco para response"""
    permissoes = _buscar_permissoes_perfil(perfil["id"], conn)
    total_usuarios = _contar_usuarios_perfil(perfil["id"], conn)
    
    return PerfilResponse(
        id=perfil["id"],
        nome=perfil["nome"],
        descricao=perfil.get("descricao", ""),
        cor=perfil.get("cor", "#64748b"),
        total_usuarios=total_usuarios,
        permissoes=permissoes,
        ativo=bool(perfil.get("ativo", 1))
    )

# ── ENDPOINTS ─────────────────────────────────────────────

@router.get("/recursos", response_model=RecursosResponse)
def listar_recursos(current_user: dict = Depends(get_current_user)):
    """
    Lista todos os recursos/módulos disponíveis no sistema.
    """
    recursos = [
        RecursoResponse(**r) for r in RECURSOS_PADRAO
    ]
    return RecursosResponse(recursos=recursos)


@router.get("/categorias", response_model=CategoriasResponse)
def listar_categorias(current_user: dict = Depends(get_current_user)):
    """
    Lista todas as categorias de recursos.
    """
    return CategoriasResponse(categorias=CATEGORIAS_PADRAO)


@router.get("/perfis", response_model=PermissoesListResponse)
def listar_perfis(current_user: dict = Depends(get_current_user)):
    """
    Lista todos os perfis do tenant atual.
    """
    # Verificar permissão
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, nome, descricao, cor, ativo FROM perfil ORDER BY nome ASC
        """)
        perfis_db = cursor.fetchall()
        
        perfis_response = [_perfil_to_response(p, conn) for p in perfis_db]
        
        return PermissoesListResponse(
            total=len(perfis_response),
            perfis=perfis_response
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/perfis/{perfil_id}", response_model=PerfilResponse)
def obter_perfil(
    perfil_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém dados de um perfil específico.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    perfil = _buscar_perfil_por_id(perfil_id, conn)
    
    if not perfil:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    response = _perfil_to_response(perfil, conn)
    conn.close()
    
    return response


@router.post("/perfis", response_model=PerfilResponse, status_code=status.HTTP_201_CREATED)
def criar_perfil(
    data: PerfilCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um novo perfil.
    Apenas admin pode criar perfis.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validar nome único
        cursor.execute("SELECT id FROM perfil WHERE nome = %s", (data.nome,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um perfil com este nome"
            )
        
        import uuid
        perfil_id = f"perfil_{uuid.uuid4().hex[:8]}"
        
        # Inserir perfil
        cursor.execute("""
            INSERT INTO perfil (id, nome, descricao, cor, ativo)
            VALUES (%s, %s, %s, %s, 1)
        """, (perfil_id, data.nome, data.descricao or "", data.cor))
        
        # Inserir permissões (simplificado - em produção usar tabela perfil_permissao)
        # Para este exemplo, vamos armazenar um JSON ou simplesmente manter as permissões
        # no response baseado nos dados recebidos
        
        conn.commit()
        
        # Buscar e retornar
        perfil = _buscar_perfil_por_id(perfil_id, conn)
        return _perfil_to_response(perfil, conn)
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar perfil: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/perfis/{perfil_id}", response_model=PerfilResponse)
def atualizar_perfil(
    perfil_id: str,
    data: PerfilUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Atualiza um perfil existente e suas permissões.
    Apenas admin pode atualizar perfis.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    # Proteger perfil admin
    if perfil_id == "perfil_admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perfil admin não pode ser editado"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        perfil = _buscar_perfil_por_id(perfil_id, conn)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        # Validar nome único (excluindo ele mesmo)
        cursor.execute(
            "SELECT id FROM perfil WHERE nome = %s AND id != %s",
            (data.nome, perfil_id)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro perfil com este nome"
            )
        
        # Atualizar perfil
        cursor.execute("""
            UPDATE perfil SET nome = %s, descricao = %s, cor = %s WHERE id = %s
        """, (data.nome, data.descricao or "", data.cor, perfil_id))
        
        # Atualizar permissões (simplificado)
        # Em produção, limpar perfil_permissao e inserir novamente
        
        conn.commit()
        
        # Retornar atualizado
        perfil_atualizado = _buscar_perfil_por_id(perfil_id, conn)
        return _perfil_to_response(perfil_atualizado, conn)
        
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


@router.delete("/perfis/{perfil_id}")
def deletar_perfil(
    perfil_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deleta um perfil.
    Apenas admin pode deletar perfis.
    Não pode deletar perfil se houver usuários atribuídos.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    # Proteger perfis built-in
    if perfil_id.startswith("perfil_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível deletar perfis padrão do sistema"
        )
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        perfil = _buscar_perfil_por_id(perfil_id, conn)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        # Validar se há usuários usando este perfil
        total_usuarios = _contar_usuarios_perfil(perfil_id, conn)
        if total_usuarios > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é possível deletar um perfil com {total_usuarios} usuário(s) atribuído(s)"
            )
        
        # Deletar
        cursor.execute("DELETE FROM perfil WHERE id = %s", (perfil_id,))
        conn.commit()
        
        return {"message": "Perfil deletado com sucesso"}
        
    finally:
        cursor.close()
        conn.close()