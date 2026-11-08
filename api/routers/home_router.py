from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel

router = APIRouter()

# ═════════════════════════════════════════════════════════════
#  AVISOS
# ═════════════════════════════════════════════════════════════
@router.get("/avisos")
def get_home_avisos(current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, titulo, tag,
                   DATE(COALESCE(publicar_de, criado_em)) AS data
            FROM avisos_home
            WHERE tenant_id = %s
              AND ativo = 1
              AND (publicar_de  IS NULL OR publicar_de  <= NOW())
              AND (publicar_ate IS NULL OR publicar_ate >= NOW())
            ORDER BY (tag = 'Importante') DESC, COALESCE(publicar_de, criado_em) DESC
            LIMIT 5
            """,
            [current_user["tenant_id"]],
        )
        rows = cursor.fetchall()
        for r in rows:
            r["data"] = r["data"].isoformat() if r["data"] else None
        return {"total": len(rows), "data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ═════════════════════════════════════════════════════════════
#  AVISOS — administração (criar / editar / excluir)
# ═════════════════════════════════════════════════════════════
class AvisoIn(BaseModel):
    titulo: str
    tag: Optional[Literal["Importante", "Novidade", "Manutenção"]] = None
    publicar_de: Optional[date] = None
    publicar_ate: Optional[date] = None
    ativo: bool = True


@router.get("/admin/avisos")
def listar_avisos_admin(current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, titulo, tag, publicar_de, publicar_ate, ativo, criado_por, criado_em
               FROM avisos_home WHERE tenant_id = %s ORDER BY criado_em DESC""",
            [current_user["tenant_id"]],
        )
        rows = cursor.fetchall()
        for r in rows:
            r["ativo"] = bool(r["ativo"])
            for k, v in r.items():
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        return {"total": len(rows), "data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/admin/avisos")
def criar_aviso(aviso: AvisoIn, current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        autor = current_user.get("id")
        cursor.execute(
            """INSERT INTO avisos_home (tenant_id, titulo, tag, publicar_de, publicar_ate, ativo, criado_por)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [current_user["tenant_id"], aviso.titulo.strip(), aviso.tag, aviso.publicar_de, aviso.publicar_ate,
             int(aviso.ativo), autor],
        )
        conn.commit()
        return {"id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.put("/admin/avisos/{aviso_id}")
def atualizar_aviso(aviso_id: int, aviso: AvisoIn, current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE avisos_home
               SET titulo = %s, tag = %s, publicar_de = %s, publicar_ate = %s, ativo = %s
               WHERE id = %s AND tenant_id = %s""",
            [aviso.titulo.strip(), aviso.tag, aviso.publicar_de, aviso.publicar_ate, int(aviso.ativo),
             aviso_id, current_user["tenant_id"]],
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Aviso não encontrado")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.delete("/admin/avisos/{aviso_id}")
def excluir_aviso(aviso_id: int, current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM avisos_home WHERE id = %s AND tenant_id = %s",
                       [aviso_id, current_user["tenant_id"]])
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Aviso não encontrado")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ═════════════════════════════════════════════════════════════
#  STATUS DAS INTEGRAÇÕES  (a partir de pipeline_offset / pipeline_execucao, as mesmas
# ═════════════════════════════════════════════════════════════
_GRUPOS_INTEGRACAO = [
    ("financeiro", "ERP · Financeiro"),
    ("estoque",    "ERP · Estoque"),
    ("chamado",    "Chamados"),
    ("crm",        "CRM"),
    ("telemetria", "Telemetria"),
]
_LIMITE_OK_MIN = 60          # pipelines rodam a cada ~30 min: até 60 min = em dia
_LIMITE_ATRASADO_MIN = 24 * 60   # acima disso (ou nunca rodou) = sem atualização


def _status_por_idade(ultima: Optional[datetime], agora: datetime) -> str:
    if ultima is None:
        return "erro"
    minutos = (agora - ultima).total_seconds() / 60
    if minutos <= _LIMITE_OK_MIN:
        return "ok"
    return "atrasado" if minutos <= _LIMITE_ATRASADO_MIN else "erro"


@router.get("/integracoes")
def get_home_integracoes(current_user: dict = Depends(get_current_user)):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT po.origem, MAX(pe.fim_execucao) AS ultima
            FROM pipeline_offset po
            LEFT JOIN pipeline_execucao pe
                   ON pe.pipeline_offset_id = po.id AND pe.fim_execucao IS NOT NULL
            WHERE po.tenant_id = %s
            GROUP BY po.origem
            """,
            [current_user["tenant_id"]],
        )
        rows = cursor.fetchall()

        # agrupa pipelines do mesmo sistema; vale o mais ANTIGO (um pipeline parado já é alerta)
        grupos: dict = {}
        for r in rows:
            origem = (r["origem"] or "").lower()
            nome = next((rot for pref, rot in _GRUPOS_INTEGRACAO if origem.startswith(pref)), r["origem"] or "—")
            ultima = r["ultima"]
            if nome not in grupos:
                grupos[nome] = ultima
            elif ultima is None or (grupos[nome] is not None and ultima < grupos[nome]):
                grupos[nome] = ultima

        agora = datetime.now()   # ⚠️ mesmo fuso em que o banco grava fim_execucao
        data = [
            {
                "nome": nome,
                "status": _status_por_idade(ultima, agora),
                "atualizadoEm": ultima.isoformat() if ultima else None,
            }
            for nome, ultima in sorted(grupos.items())
        ]
        return {"total": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()