import json
import re
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from auth.router import get_current_user
from database.mysql_connection import connection_mysql

from api.routers.schemas.termo import (
    EmpresaTermoDados,
    EmpresaTermoOut,
    GerarTermoRequest,
    ModeloOut,
    TermoEmitidoOut,
)
from services import termo_service as svc

router = APIRouter(
    tags=["Termos de responsabilidade"],
    dependencies=[Depends(get_current_user)],
)

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_UPLOAD = 10 * 1024 * 1024
SLUG_RE = re.compile(r"^[a-z0-9_-]{2,50}$")


# ============================================================
# HELPERS
# ============================================================

def _fechar(conn, cursor):
    for obj in (cursor, conn):
        try:
            obj.close()
        except Exception:
            pass


def _usuario(current_user) -> str:
    if isinstance(current_user, dict):
        return str(current_user.get("nome") or current_user.get("username")
                   or current_user.get("email") or current_user.get("id") or "")
    return str(current_user)


def _ids_sql(ids: list[int]) -> str:
    return ", ".join(["%s"] * len(ids))


def _nome_arquivo(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto).strip("_")[:40] or "termo"


async def _ler_upload(arquivo: UploadFile, extensao: str) -> bytes:
    if not (arquivo.filename or "").lower().endswith(extensao):
        raise HTTPException(400, f"Envie um arquivo {extensao}")
    conteudo = await arquivo.read()
    if len(conteudo) > MAX_UPLOAD:
        raise HTTPException(413, "Arquivo maior que 10 MB")
    if not conteudo:
        raise HTTPException(400, "Arquivo vazio")
    return conteudo


def _modelo_or_404(cursor, id_modelo: int) -> dict:
    cursor.execute("SELECT * FROM termo_modelo WHERE id = %s LIMIT 1", (id_modelo,))
    m = cursor.fetchone()
    if not m:
        raise HTTPException(404, "Modelo não encontrado")
    return m


def _modelo_out(m: dict) -> ModeloOut:
    return ModeloOut(id=m["id"], slug=m["slug"], nome=m["nome"], descricao=m["descricao"],
                     versao=m["versao"], ativo=bool(m["ativo"]), atualizado_em=m["atualizado_em"])


# ============================================================
# CAMPOS DISPONÍVEIS (ajuda para quem edita o modelo no Word)
# ============================================================

@router.get("/campos")
def campos_disponiveis():
    return {"campos": svc.CAMPOS_DISPONIVEIS, "exemplo_lista": svc.EXEMPLO_LOOP}


# ============================================================
# MODELOS (documentos)
# ============================================================

@router.get("/modelos", response_model=list[ModeloOut])
def listar_modelos(incluir_inativos: bool = False):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM termo_modelo"
        if not incluir_inativos:
            sql += " WHERE ativo = 1"
        cursor.execute(sql + " ORDER BY nome")
        return [_modelo_out(m) for m in cursor.fetchall()]
    finally:
        _fechar(conn, cursor)


@router.get("/modelos/{id_modelo}/download")
def baixar_modelo(id_modelo: int):
    """Baixa o .docx atual para editar no Word e subir de volta."""
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        m = _modelo_or_404(cursor, id_modelo)
    finally:
        _fechar(conn, cursor)
    caminho = svc.MODELOS_DIR / m["arquivo"]
    if not caminho.exists():
        raise HTTPException(404, "Arquivo do modelo não encontrado no servidor")
    return FileResponse(caminho, media_type=DOCX_MIME, filename=f"{m['slug']}_v{m['versao']}.docx")


@router.post("/modelos", response_model=ModeloOut, status_code=201)
async def criar_modelo(
    slug: str = Form(...),
    nome: str = Form(...),
    descricao: Optional[str] = Form(None),
    arquivo: UploadFile = File(...),
):
    if not SLUG_RE.match(slug):
        raise HTTPException(400, "slug deve ter 2-50 caracteres: letras minúsculas, números, _ ou -")
    conteudo = await _ler_upload(arquivo, ".docx")

    destino = svc.MODELOS_DIR / f"{slug}_v1.docx"
    destino.write_bytes(conteudo)
    try:
        svc.validar_modelo(destino)
    except HTTPException:
        destino.unlink(missing_ok=True)
        raise

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM termo_modelo WHERE slug = %s", (slug,))
        if cursor.fetchone():
            destino.unlink(missing_ok=True)
            raise HTTPException(409, "Já existe um modelo com esse slug")
        cursor.execute(
            "INSERT INTO termo_modelo (slug, nome, descricao, arquivo, versao) VALUES (%s,%s,%s,%s,1)",
            (slug, nome, descricao, destino.name),
        )
        conn.commit()
        return _modelo_out(_modelo_or_404(cursor, cursor.lastrowid))
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        destino.unlink(missing_ok=True)
        raise HTTPException(500, f"Erro ao criar modelo: {e}")
    finally:
        _fechar(conn, cursor)


@router.put("/modelos/{id_modelo}/arquivo", response_model=ModeloOut)
async def substituir_arquivo_modelo(id_modelo: int, arquivo: UploadFile = File(...)):
    """Sobe uma nova versão do modelo. As versões anteriores ficam guardadas no servidor."""
    conteudo = await _ler_upload(arquivo, ".docx")

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        m = _modelo_or_404(cursor, id_modelo)
        nova_versao = m["versao"] + 1
        destino = svc.MODELOS_DIR / f"{m['slug']}_v{nova_versao}.docx"
        destino.write_bytes(conteudo)
        try:
            svc.validar_modelo(destino)
        except HTTPException:
            destino.unlink(missing_ok=True)
            raise
        cursor.execute("UPDATE termo_modelo SET arquivo = %s, versao = %s WHERE id = %s",
                       (destino.name, nova_versao, id_modelo))
        conn.commit()
        return _modelo_out(_modelo_or_404(cursor, id_modelo))
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Erro ao atualizar modelo: {e}")
    finally:
        _fechar(conn, cursor)


@router.delete("/modelos/{id_modelo}", status_code=204)
def desativar_modelo(id_modelo: int):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        _modelo_or_404(cursor, id_modelo)
        cursor.execute("UPDATE termo_modelo SET ativo = 0 WHERE id = %s", (id_modelo,))
        conn.commit()
        return None
    finally:
        _fechar(conn, cursor)


# ============================================================
# DADOS DA EMPRESA PARA O TERMO
# ============================================================

_SQL_EMPRESA = """
    SELECT emp.codigo_empresa, emp.nome_empresa,
           d.razao_social, d.nome_fantasia, d.cnpj, d.ie, d.endereco,
           d.bairro, d.cidade, d.uf, d.cep, d.telefone
    FROM empresa_bi emp
    LEFT JOIN empresa_bi d ON d.codigo_empresa = emp.codigo_empresa
    WHERE emp.codigo_empresa = %s
    LIMIT 1
"""


@router.get("/empresas/{codigo_empresa}", response_model=EmpresaTermoOut)
def obter_dados_empresa(codigo_empresa: int):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(_SQL_EMPRESA, (codigo_empresa,))
        e = cursor.fetchone()
        if not e:
            raise HTTPException(404, "Empresa não encontrada")
        return e
    finally:
        _fechar(conn, cursor)


@router.put("/empresas/{codigo_empresa}", response_model=EmpresaTermoOut)
def salvar_dados_empresa(codigo_empresa: int, payload: EmpresaTermoDados):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM empresa_bi WHERE codigo_empresa = %s", (codigo_empresa,))
        if not cursor.fetchone():
            raise HTTPException(404, "Empresa não encontrada")

        dados = payload.model_dump()
        colunas = list(dados.keys())
        cursor.execute(
            f"""
            INSERT INTO empresa_bi (codigo_empresa, {", ".join(colunas)})
            VALUES (%s, {", ".join(["%s"] * len(colunas))})
            ON DUPLICATE KEY UPDATE {", ".join(f"{c} = VALUES({c})" for c in colunas)}
            """,
            (codigo_empresa, *dados.values()),
        )
        conn.commit()
        cursor.execute(_SQL_EMPRESA, (codigo_empresa,))
        return cursor.fetchone()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Erro ao salvar dados da empresa: {e}")
    finally:
        _fechar(conn, cursor)


# ============================================================
# GERAR TERMO
# ============================================================

@router.post("/gerar")
def gerar_termo(payload: GerarTermoRequest, current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        # ---- modelo ------------------------------------------------------
        modelo = _modelo_or_404(cursor, payload.id_modelo)
        if not modelo["ativo"]:
            raise HTTPException(400, "Modelo inativo")
        modelo_path = svc.MODELOS_DIR / modelo["arquivo"]
        if not modelo_path.exists():
            raise HTTPException(404, "Arquivo do modelo não encontrado no servidor")

        # ---- empresa -----------------------------------------------------
        cursor.execute(_SQL_EMPRESA, (payload.id_empresa,))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(404, "Empresa não encontrada")
        if not emp["cnpj"]:
            raise HTTPException(
                422, "Dados da empresa incompletos para o termo (CNPJ). "
                     "Preencha em PUT /api/termos/empresas/{codigo}")
        empresa = {
            "nome": emp["nome_empresa"],
            "razao_social": emp["razao_social"] or emp["nome_empresa"],
            "nome_fantasia": emp["nome_fantasia"] or emp["nome_empresa"],
            **{k: emp[k] for k in ("cnpj", "ie", "endereco", "bairro", "cidade", "uf", "cep", "telefone")},
        }

        # ---- colaborador -------------------------------------------------
        cursor.execute("SELECT id, nome, cpf_cnpj FROM pessoa_bi WHERE id = %s LIMIT 1",
                       (payload.id_colaborador,))
        colaborador = cursor.fetchone()
        if not colaborador:
            raise HTTPException(404, "Colaborador não encontrado")

        # ---- equipamentos (mantém a ordem escolhida) ---------------------
        equipamentos = []
        if payload.equipamentos:
            ids = [i.id for i in payload.equipamentos]
            cursor.execute(
                f"""
                SELECT e.*, tipo.nome AS nome_tipo, marca.nome AS nome_marca, modelo.nome AS nome_modelo
                FROM parque_tecnologico e
                LEFT JOIN tipo_equipamento tipo ON tipo.id = e.id_tipo
                LEFT JOIN marca ON marca.id = e.id_marca
                LEFT JOIN modelo ON modelo.id = e.id_modelo
                WHERE e.id IN ({_ids_sql(ids)})
                """,
                tuple(ids),
            )
            por_id = {r["id"]: r for r in cursor.fetchall()}
            faltando = [i for i in ids if i not in por_id]
            if faltando:
                raise HTTPException(404, f"Equipamento(s) não encontrado(s): {faltando}")
            for item in payload.equipamentos:
                row = dict(por_id[item.id])
                row["cor"], row["condicao"] = item.cor, item.condicao
                equipamentos.append(row)

        # ---- chips -------------------------------------------------------
        chips = []
        if payload.ids_chips:
            cursor.execute(
                f"SELECT id, numero, iccid FROM chips WHERE id IN ({_ids_sql(payload.ids_chips)})",
                tuple(payload.ids_chips),
            )
            por_id = {r["id"]: r for r in cursor.fetchall()}
            faltando = [i for i in payload.ids_chips if i not in por_id]
            if faltando:
                raise HTTPException(404, f"Chip(s) não encontrado(s): {faltando}")
            chips = [por_id[i] for i in payload.ids_chips]

        # ---- gera --------------------------------------------------------
        contexto = svc.montar_contexto(
            empresa=empresa, colaborador=colaborador, equipamentos=equipamentos, chips=chips,
            acessorios=payload.acessorios, data_emissao=payload.data_emissao,
        )
        base = f"termo_{modelo['slug']}_{_nome_arquivo(colaborador['nome'])}"
        arquivo = svc.gerar(modelo_path, contexto, base, payload.formato)

        # ---- histórico ---------------------------------------------------
        cursor.execute(
            """
            INSERT INTO termo_emitido
              (id_modelo, versao_modelo, id_empresa, id_colaborador,
               ids_equipamentos, ids_chips, arquivo, gerado_por)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (modelo["id"], modelo["versao"], payload.id_empresa, payload.id_colaborador,
             json.dumps([i.id for i in payload.equipamentos]), json.dumps(payload.ids_chips),
             arquivo.name, _usuario(current_user)),
        )
        conn.commit()

        mime = "application/pdf" if arquivo.suffix == ".pdf" else DOCX_MIME
        return FileResponse(arquivo, media_type=mime, filename=arquivo.name)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Erro ao gerar termo: {e}")
    finally:
        _fechar(conn, cursor)


# ============================================================
# TERMOS EMITIDOS + COPIA ASSINADA
# ============================================================

@router.get("/emitidos", response_model=list[TermoEmitidoOut])
def listar_emitidos(
    colaborador: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        where, params = "", []
        if colaborador is not None:
            where = "WHERE t.id_colaborador = %s"
            params.append(colaborador)
        cursor.execute(
            f"""
            SELECT t.*, m.nome AS nome_modelo, p.nome AS nome_colaborador
            FROM termo_emitido t
            LEFT JOIN termo_modelo m ON m.id = t.id_modelo
            LEFT JOIN pessoa_bi p ON p.id = t.id_colaborador
            {where}
            ORDER BY t.gerado_em DESC
            LIMIT %s OFFSET %s
            """,
            (*params, limit, skip),
        )
        saida = []
        for r in cursor.fetchall():
            saida.append(TermoEmitidoOut(
                id=r["id"], id_modelo=r["id_modelo"], nome_modelo=r["nome_modelo"],
                versao_modelo=r["versao_modelo"], id_empresa=r["id_empresa"],
                id_colaborador=r["id_colaborador"], nome_colaborador=r["nome_colaborador"],
                ids_equipamentos=json.loads(r["ids_equipamentos"] or "[]"),
                ids_chips=json.loads(r["ids_chips"] or "[]"),
                gerado_por=r["gerado_por"], gerado_em=r["gerado_em"],
                tem_assinado=bool(r["arquivo_assinado"]),
            ))
        return saida
    finally:
        _fechar(conn, cursor)


def _emitido_or_404(cursor, id_emitido: int) -> dict:
    cursor.execute("SELECT * FROM termo_emitido WHERE id = %s LIMIT 1", (id_emitido,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Termo não encontrado")
    return r


@router.get("/emitidos/{id_emitido}/download")
def baixar_emitido(id_emitido: int):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        r = _emitido_or_404(cursor, id_emitido)
    finally:
        _fechar(conn, cursor)
    caminho = svc.EMITIDOS_DIR / r["arquivo"]
    if not caminho.exists():
        raise HTTPException(404, "Arquivo não encontrado no servidor")
    return FileResponse(caminho, filename=caminho.name)


@router.post("/emitidos/{id_emitido}/assinado", status_code=204)
async def subir_assinado(id_emitido: int, arquivo: UploadFile = File(...)):
    """Anexa o PDF assinado (digitalizado) ao termo emitido."""
    nome = (arquivo.filename or "").lower()
    ext = ".pdf" if nome.endswith(".pdf") else None
    if ext is None:
        raise HTTPException(400, "Envie o termo assinado em PDF")
    conteudo = await _ler_upload(arquivo, ".pdf")

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        r = _emitido_or_404(cursor, id_emitido)
        destino = svc.EMITIDOS_DIR / f"assinado_{id_emitido}.pdf"
        destino.write_bytes(conteudo)
        cursor.execute("UPDATE termo_emitido SET arquivo_assinado = %s WHERE id = %s",
                       (destino.name, id_emitido))
        conn.commit()
        return None
    except HTTPException:
        conn.rollback()
        raise
    finally:
        _fechar(conn, cursor)


@router.get("/emitidos/{id_emitido}/assinado")
def baixar_assinado(id_emitido: int):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        r = _emitido_or_404(cursor, id_emitido)
    finally:
        _fechar(conn, cursor)
    if not r["arquivo_assinado"]:
        raise HTTPException(404, "Ainda não há cópia assinada")
    return FileResponse(svc.EMITIDOS_DIR / r["arquivo_assinado"], media_type="application/pdf",
                        filename=f"termo_{id_emitido}_assinado.pdf")
