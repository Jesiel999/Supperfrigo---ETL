from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user
from datetime import date, timedelta 
 

router = APIRouter()


# ── Helper: aplica a regra básica de acesso por empresa ─────────────
def _empresas_permitidas(current_user: dict) -> Optional[list]:
    """
    None  = usuário sem restrição no JWT (vê todas as empresas do empresa_bi)
    list  = lista de códigos (str) que o usuário PODE ver — qualquer coisa
            fora disso deve ser bloqueada, mesmo que o cliente peça.
    """
    empresas = current_user.get("empresas") or []
    if not empresas:
        return None
    return [str(e["codigo"]) for e in empresas]


def _aplicar_filtro_empresa(filtros: list, params: list, id_empresa: Optional[str], permitidas: Optional[list]):
    """
    Regra central: se o usuário tem restrição, SEMPRE filtra pelo que ele
    pode ver — ignora ou valida o id_empresa vindo da query string.
    Nunca confia no client para decidir o que ele pode ver.
    """
    if permitidas is not None:
        if id_empresa:
            if id_empresa not in permitidas:
                raise HTTPException(status_code=403, detail="Sem acesso a esta empresa")
            filtros.append("id_empresa = %s")
            params.append(id_empresa)
        else:
            placeholders = ",".join(["%s"] * len(permitidas))
            filtros.append(f"id_empresa IN ({placeholders})")
            params.extend(permitidas)
    elif id_empresa:
        filtros.append("id_empresa = %s")
        params.append(id_empresa)


@router.get("/inadimplencia")
def get_inadimplencia(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    status:     Optional[str] = Query(None, description="VENCIDO | EM ABERTO"),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de inadimplência da view vw_bi_inadimplencia,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        if status:
            filtros.append("status_financeiro = %s")
            params.append(status)

        if dias_atraso_min is not None:
            filtros.append("dias_atraso >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_inadimplencia {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.get("/pmp")
def get_pmp(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de prazo médio de pagamento da view vw_bi_pmp,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_movimentacao >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_movimentacao <= %s")
            params.append(data_fim)

        if dias_atraso_min is not None:
            filtros.append("dias_pagamento >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_pmp {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.get("/pmr")
def get_pmr(  
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de prazo médio de recebimento da view vw_bi_pmr,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_movimentacao >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_movimentacao <= %s")
            params.append(data_fim)

        if dias_atraso_min is not None:
            filtros.append("dias_recebimento >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_pmr {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@router.get("/receber")
def get_receber(
    id_empresa: Optional[str] = Query(None),
    id_pessoa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):

    """
    Retorna registros do Receber evidenciando a taxa de recebimento
    """

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try: 
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_receber {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@router.get("/pagar")
def get_pagar(
    id_empresa: Optional[str] = Query(None),
    id_pessoa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros do Pagar evidenciando a taxa de pagamento
    """

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try: 
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_pagar {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


# Helper compartilhado: nome da pessoa (pessoa_bi) para os ids presentes nas linhas devolvidas.
# O filtro de Pessoa BI agora é feito NO FRONT (padrão do ReceberService), então cada linha
# precisa trazer id_pessoa e nome_pessoa.

def _nomes_pessoas(cursor, ids, lote: int = 1000) -> dict:
    ids = sorted({str(i) for i in ids if i not in (None, "")})
    nomes: dict = {}
    for k in range(0, len(ids), lote):
        parte = ids[k:k + lote]
        cursor.execute(
            f"""SELECT id_sances, MAX(nome) AS nome
                FROM pessoa_bi
                WHERE id_sances IN ({','.join(['%s'] * len(parte))})
                GROUP BY id_sances""",
            parte,
        )
        for p in cursor.fetchall():
            nomes[str(p["id_sances"])] = p["nome"]
    return nomes
 
 
@router.get("/pessoas")
def get_pessoas_filtro(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Pessoas (clientes/fornecedores) com títulos no período — alimenta o filtro de DRE e FCP."""
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
 
    try:
        filtros = [
            "f.tenant_id = %s",
            "f.tipo_titulo IN ('RECEBER','PAGAR')",
            "UPPER(f.descricao_situacao) <> 'CANCELADO'",
            "f.id_pessoa IS NOT NULL",
            "f.id_pessoa <> ''",
        ]
        params = [current_user["tenant_id"]]
 
        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)
 
        if data_inicio:
            ini = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("f.data_competencia >= %s")
            params.append(ini.isoformat())
        if data_fim:
            fim = date.fromisoformat(data_fim)
            prox_mes = (fim.replace(day=1) + timedelta(days=32)).replace(day=1)
            filtros.append("f.data_competencia < %s")
            params.append(prox_mes.isoformat())
 
        sql = f"""
            SELECT t.id_pessoa AS id,
                   (SELECT MAX(p.nome) FROM pessoa_bi p WHERE p.id_sances = t.id_pessoa) AS nome
            FROM (
                SELECT DISTINCT f.id_pessoa
                FROM financeiro_bi f
                WHERE {' AND '.join(filtros)}
            ) t
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()
 
        data = [{"id": str(r["id"]), "nome": r["nome"] or f"Pessoa {r['id']}"} for r in rows]
        data.sort(key=lambda r: r["nome"].lower())
        return {"total": len(data), "data": data}
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ── GET /dre : `incluir_abertos` + dimensão Empresa e Pessoa BI (cada linha traz id_pessoa e nome_pessoa;
#    o filtro de pessoa é aplicado no front, como no ReceberService) ──
@router.get("/dre")
def get_dre(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    incluir_abertos: bool = Query(True),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = ["tenant_id = %s"]
        params = [current_user["tenant_id"]]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if data_inicio:
            inicio = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("mes_competencia >= %s")
            params.append(inicio.isoformat())

        if data_fim:
            filtros.append("mes_competencia <= %s")
            params.append(data_fim)

        # False = só títulos baixados (realizado). True = baixados + em aberto.
        if not incluir_abertos:
            filtros.append("em_aberto = 0")

        where = f"WHERE {' AND '.join(filtros)}"

        # conta × pessoa (o front soma por conta e aplica o filtro de pessoa localmente)
        sql = f"""
            SELECT
                pc.classificacao,
                pc.descricao,
                pc.eh_analitica,
                v.id_empresa,
                v.id_pessoa,
                SUM(v.valor_dre) AS total,
                MAX(v.ultima_atualizacao) AS ultima_atualizacao
            FROM plano_contas_bi pc
            JOIN (
                SELECT
                    numero_conta_resultado,
                    id_empresa,
                    id_pessoa,
                    SUM(valor_dre) AS valor_dre,
                    MAX(ultima_atualizacao) AS ultima_atualizacao
                FROM vw_bi_dre
                {where}
                GROUP BY numero_conta_resultado, id_empresa, id_pessoa
            ) v
                ON v.numero_conta_resultado = pc.classificacao
                OR v.numero_conta_resultado LIKE CONCAT(pc.classificacao, '.%%')
            WHERE pc.grupo = 'Resultado'
            GROUP BY pc.classificacao, pc.descricao, pc.eh_analitica, v.id_empresa, v.id_pessoa
            HAVING pc.eh_analitica = 0 OR total <> 0
            ORDER BY pc.classificacao
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        nomes = _nomes_pessoas(cursor, {r["id_pessoa"] for r in rows})

        for row in rows:
            row["total"] = float(row["total"])
            row["eh_analitica"] = bool(row["eh_analitica"])
            row["nome_pessoa"] = nomes.get(str(row["id_pessoa"]))
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────────
# GET /fcp  — agora devolve conta × empresa × mês (periodo "YYYY-MM")
# ─────────────────────────────────────────────────────────────
@router.get("/fcp")
def get_fcp(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = ["tenant_id = %s"]
        params = [current_user["tenant_id"]]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if data_inicio:
            filtros.append("mes_competencia >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("mes_competencia <= %s")
            params.append(data_fim)

        where = f"WHERE {' AND '.join(filtros)}"

        sql = f"""
            SELECT
                pc.classificacao,
                pc.descricao,
                pc.eh_analitica,
                v.id_empresa,
                v.id_pessoa,
                v.periodo,
                SUM(v.valor_dre) AS total,
                MAX(v.ultima_atualizacao) AS ultima_atualizacao
            FROM plano_contas_bi pc
            JOIN (
                SELECT id_empresa,
                       id_pessoa,
                       numero_conta_resultado,
                       LEFT(mes_competencia, 7) AS periodo,
                       SUM(valor_dre)           AS valor_dre,
                       MAX(ultima_atualizacao)  AS ultima_atualizacao
                FROM vw_bi_fcp
                {where}
                GROUP BY id_empresa, id_pessoa, numero_conta_resultado, LEFT(mes_competencia, 7)
            ) v
              ON v.numero_conta_resultado = pc.classificacao
              OR v.numero_conta_resultado LIKE CONCAT(pc.classificacao, '.%%')
            WHERE pc.grupo = 'Resultado'
            GROUP BY pc.classificacao, pc.descricao, pc.eh_analitica, v.id_empresa, v.id_pessoa, v.periodo
            ORDER BY pc.classificacao, v.periodo
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        nomes = _nomes_pessoas(cursor, {r["id_pessoa"] for r in rows})

        for row in rows:
            row["total"] = float(row["total"] or 0)
            row["eh_analitica"] = bool(row["eh_analitica"])
            row["nome_pessoa"] = nomes.get(str(row["id_pessoa"]))
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
 
from datetime import date, timedelta   # (acrescente timedelta ao import existente)

# Contas de resultado consideradas "a pagar": custos (3.2) e despesas (3.3).
_FCP_CLASSES_PAGAR = ("3.2", "3.3")

# Nome da empresa em empresa_bi (primeiro que existir e estiver preenchido).
_FCP_COLS_NOME_EMPRESA = ["nome_fantasia", "razao_social", "nome_empresa", "nome", "fantasia", "descricao"]


def _fcp_in(n: int) -> str:
    return ",".join(["%s"] * n)


@router.get("/fcp/pagar")
def get_fcp_pagar(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    base_data: str = Query("competencia", pattern="^(competencia|vencimento)$"),
    current_user: dict = Depends(get_current_user),
):
    """Títulos a PAGAR EM ABERTO de custos e despesas, com fornecedor, nota, parcela e valores.

    base_data: 'competencia' (padrão, mesma base do resto do FCP) ou 'vencimento'.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = [
            "f.tenant_id = %s",
            "f.tipo_titulo = 'PAGAR'",
            "UPPER(f.descricao_situacao) NOT IN ('CANCELADO', 'BAIXADO', 'BAIXADO PARCIAL', 'UNIDO', 'RENEGOCIADO')",
        ]
        params = [current_user["tenant_id"]]

        # custos/despesas: conta exata ou qualquer filha (3.2 / 3.2.x...)
        conds = " OR ".join(
            ["(f.numero_conta_resultado = %s OR f.numero_conta_resultado LIKE %s)"] * len(_FCP_CLASSES_PAGAR)
        )
        filtros.append(f"({conds})")
        for c in _FCP_CLASSES_PAGAR:
            params += [c, f"{c}.%"]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        col_data = "f.data_competencia" if base_data == "competencia" else "f.data_vencimento"
        if data_inicio:
            ini = date.fromisoformat(data_inicio)
            filtros.append(f"{col_data} >= %s")
            params.append(ini.isoformat())

        if data_fim:
            fim = date.fromisoformat(data_fim)
            filtros.append(f"{col_data} <= %s")
            params.append(fim.isoformat())

        # valor_pago: mesma fonte da view (recebimentos_bi por codigo_raw).
        # valor_nota: soma de TODAS as parcelas da mesma nota (empresa + fornecedor + nº documento).
        sql = f"""
            SELECT
                f.codigo_raw                      AS codigo,
                f.id_empresa,
                f.id_pessoa,
                f.numero_documento,
                f.ordem                           AS parcela,
                f.origem,
                f.descricao_situacao,
                f.status_financeiro,
                f.descricao_forma_pagamento,
                f.descricao_categoria_financeira,
                f.descricao_centro_custo,
                f.numero_conta_resultado,
                f.descricao_conta_resultado,
                f.data_emissao,
                f.data_competencia,
                f.data_vencimento,
                f.data_baixa,
                f.dias_atraso,
                f.valor_nominal                   AS valor_titulo,
                f.valor_total                     AS valor_total_bruto,
                COALESCE((
                    SELECT SUM(r.valor_pago)
                    FROM recebimentos_bi r
                    WHERE r.codigo_raw = f.codigo_raw
                ), 0)                             AS valor_pago,
                CASE
                    WHEN f.numero_documento IS NULL OR f.numero_documento = '' THEN f.valor_nominal
                    ELSE (
                        SELECT SUM(x.valor_nominal)
                        FROM financeiro_bi x
                        WHERE x.tenant_id        = f.tenant_id
                          AND x.id_empresa       = f.id_empresa
                          AND x.id_pessoa        = f.id_pessoa
                          AND x.numero_documento = f.numero_documento
                          AND x.tipo_titulo      = 'PAGAR'
                          AND UPPER(x.descricao_situacao) NOT IN ('CANCELADO', 'BAIXADO', 'BAIXADO PARCIAL', 'UNIDO', 'RENEGOCIADO')
                    )
                END                               AS valor_nota
            FROM financeiro_bi f
            WHERE {' AND '.join(filtros)}
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # ── nomes (só dos IDs presentes) ──
        ids_empresa = sorted({str(r["id_empresa"]) for r in rows if r.get("id_empresa") not in (None, "")})
        ids_pessoa = sorted({str(r["id_pessoa"]) for r in rows if r.get("id_pessoa") not in (None, "")})

        nomes_empresa: dict = {}
        if ids_empresa:
            cursor.execute(
                f"SELECT * FROM empresa_bi WHERE codigo_empresa IN ({_fcp_in(len(ids_empresa))})",
                ids_empresa,
            )
            for e in cursor.fetchall():
                nome = next((e[c] for c in _FCP_COLS_NOME_EMPRESA if e.get(c)), None)
                nomes_empresa.setdefault(str(e["codigo_empresa"]), nome)

        nomes_pessoa: dict = {}
        if ids_pessoa:
            cursor.execute(
                f"""SELECT id_sances, MAX(nome) AS nome
                    FROM pessoa_bi
                    WHERE id_sances IN ({_fcp_in(len(ids_pessoa))})
                    GROUP BY id_sances""",
                ids_pessoa,
            )
            for p in cursor.fetchall():
                nomes_pessoa[str(p["id_sances"])] = p["nome"]

        for row in rows:
            nominal = float(row.get("valor_titulo") or 0)
            pago = float(row.get("valor_pago") or 0)
            situacao = (row.get("descricao_situacao") or "").upper()

            row["valor_titulo"] = nominal
            row["valor_pago"] = pago
            row["valor_nota"] = float(row.get("valor_nota") or nominal)
            # saldo EM ABERTO (mesma regra da vw_bi_fcp): baixa parcial = nominal - pago; demais = valor_total
            bruto = float(row.pop("valor_total_bruto") or nominal)
            row["valor_em_aberto"] = max(nominal - pago, 0.0) if situacao == "BAIXADO PARCIAL" else bruto

            row["nome_empresa"] = nomes_empresa.get(str(row.get("id_empresa")))
            row["nome_fornecedor"] = nomes_pessoa.get(str(row.get("id_pessoa")))

            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        rows = [r for r in rows if r["valor_em_aberto"] > 0]

        # por fornecedor → nota → parcela → vencimento
        rows.sort(key=lambda r: (
            (r.get("nome_fornecedor") or "~").lower(),
            str(r.get("numero_documento") or ""),
            str(r.get("parcela") or ""),
            str(r.get("data_vencimento") or ""),
        ))

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

        
from datetime import date, timedelta   # (acrescente timedelta ao import existente)

# Colunas que já vêm certas da financeiro_bi (numero_documento, origem, data_vencimento,
# data_baixa, status_financeiro) não precisam de mapeamento.
_CANDIDATOS = {
    "descricao": ["descricao", "descricao_titulo", "historico", "observacao"],
}

# Nome da empresa em empresa_bi (usa o primeiro que existir e estiver preenchido).
# ⚠️ Se continuar null, acrescente aqui o nome real da coluna.
_COLS_NOME_EMPRESA = ["nome_fantasia", "razao_social", "nome_empresa", "nome", "fantasia", "descricao"]


def _in(n: int) -> str:
    return ",".join(["%s"] * n)


@router.get("/dre/titulos")
def get_fcp_titulos(
    classificacao: str = Query(...),
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = [
            "f.tenant_id = %s",
            "f.tipo_titulo IN ('RECEBER','PAGAR')",
            "UPPER(f.descricao_situacao) NOT IN ('CANCELADO', 'UNIDO', 'RENEGOCIADO')",
            "f.numero_conta_resultado = %s",
        ]
        params = [current_user["tenant_id"], classificacao]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if data_inicio:
            ini = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("f.data_competencia >= %s")
            params.append(ini.isoformat())
        if data_fim:
            fim = date.fromisoformat(data_fim)
            prox_mes = (fim.replace(day=1) + timedelta(days=32)).replace(day=1)
            filtros.append("f.data_competencia <= %s")
            params.append(prox_mes.isoformat())

        sql = f"""
            SELECT
                f.*,
                COALESCE((
                    SELECT r.valor_pago
                    FROM recebimentos_bi r
                    WHERE CAST(r.codigo_raw AS CHAR) = CAST(f.codigo_raw AS CHAR)
                    ORDER BY r.id DESC
                    LIMIT 1
                ), 0) AS valor_pago_calc
            FROM financeiro_bi f
            WHERE {' AND '.join(filtros)}
            ORDER BY f.data_competencia, f.codigo_raw
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # ── Nomes: busca só os IDs presentes nos títulos (evita varrer as tabelas inteiras)
        ids_empresa = sorted({str(r["id_empresa"]) for r in rows if r.get("id_empresa") not in (None, "")})
        ids_pessoa = sorted({str(r["id_pessoa"]) for r in rows if r.get("id_pessoa") not in (None, "")})

        nomes_empresa: dict = {}
        if ids_empresa:
            cursor.execute(
                f"SELECT * FROM empresa_bi WHERE codigo_empresa IN ({_in(len(ids_empresa))})",
                ids_empresa,
            )
            for e in cursor.fetchall():
                nome = next((e[c] for c in _COLS_NOME_EMPRESA if e.get(c)), None)
                nomes_empresa.setdefault(str(e["codigo_empresa"]), nome)

        nomes_pessoa: dict = {}
        if ids_pessoa:
            cursor.execute(
                f"""SELECT id_sances, MAX(nome) AS nome
                    FROM pessoa_bi
                    WHERE id_sances IN ({_in(len(ids_pessoa))})
                    GROUP BY id_sances""",
                ids_pessoa,
            )
            for p in cursor.fetchall():
                nomes_pessoa[str(p["id_sances"])] = p["nome"]

        for row in rows:
            # valor COM SINAL, mesma regra da view (bate com o valor da conta)
            bruto = float(row.get("valor_total") or 0)
            nominal = float(row.get("valor_nominal") or bruto)
            pago = float(row.pop("valor_pago_calc") or 0)
            tipo = row.get("tipo_titulo")
            sinal = 1 if tipo == "RECEBER" else -1 if tipo == "PAGAR" else 0
            parcial = (row.get("descricao_situacao") or "").upper() == "BAIXADO PARCIAL"
            # saldo EM ABERTO (mesma regra da vw_bi_fcp), com sinal: bate com o valor da conta no FCP
            saldo = max(nominal - pago, 0.0) if parcial else bruto
            row["valor_total"] = sinal * saldo
            row["valor_pago"] = pago

            row["codigo"] = row.get("codigo_raw")
            row["nome_empresa"] = nomes_empresa.get(str(row.get("id_empresa")))
            row["nome_pessoa"] = nomes_pessoa.get(str(row.get("id_pessoa")))

            for alvo, nomes in _CANDIDATOS.items():
                if row.get(alvo) is None:
                    row[alvo] = next((row[n] for n in nomes if row.get(n) is not None), None)
            if not row.get("descricao"):
                row["descricao"] = row.get("descricao_conta_resultado")
            if not row.get("origem"):
                row["origem"] = tipo

            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        rows = [r for r in rows if r["valor_total"] != 0]
        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/fcp/titulos")
def get_fcp_titulos(
    classificacao: str = Query(...),
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = [
            "f.tenant_id = %s",
            "f.tipo_titulo IN ('RECEBER','PAGAR')",
            "UPPER(f.descricao_situacao) NOT IN ('CANCELADO', 'UNIDO', 'RENEGOCIADO', 'BAIXADO', 'BAIXADO PARCIAL')",
            "f.numero_conta_resultado = %s",
        ]
        params = [current_user["tenant_id"], classificacao]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if data_inicio:
            filtros.append("f.data_competencia >= %s")
            params.append(data_inicio)
        if data_fim:
            filtros.append("f.data_competencia <= %s")
            params.append(data_fim)

        sql = f"""
            SELECT
                f.*,
                COALESCE((
                    SELECT r.valor_pago
                    FROM recebimentos_bi r
                    WHERE CAST(r.codigo_raw AS CHAR) = CAST(f.codigo_raw AS CHAR)
                    ORDER BY r.id DESC
                    LIMIT 1
                ), 0) AS valor_pago_calc
            FROM financeiro_bi f
            WHERE {' AND '.join(filtros)}
            ORDER BY f.data_competencia, f.codigo_raw
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # ── Nomes: busca só os IDs presentes nos títulos (evita varrer as tabelas inteiras)
        ids_empresa = sorted({str(r["id_empresa"]) for r in rows if r.get("id_empresa") not in (None, "")})
        ids_pessoa = sorted({str(r["id_pessoa"]) for r in rows if r.get("id_pessoa") not in (None, "")})

        nomes_empresa: dict = {}
        if ids_empresa:
            cursor.execute(
                f"SELECT * FROM empresa_bi WHERE codigo_empresa IN ({_in(len(ids_empresa))})",
                ids_empresa,
            )
            for e in cursor.fetchall():
                nome = next((e[c] for c in _COLS_NOME_EMPRESA if e.get(c)), None)
                nomes_empresa.setdefault(str(e["codigo_empresa"]), nome)

        nomes_pessoa: dict = {}
        if ids_pessoa:
            cursor.execute(
                f"""SELECT id_sances, MAX(nome) AS nome
                    FROM pessoa_bi
                    WHERE id_sances IN ({_in(len(ids_pessoa))})
                    GROUP BY id_sances""",
                ids_pessoa,
            )
            for p in cursor.fetchall():
                nomes_pessoa[str(p["id_sances"])] = p["nome"]

        for row in rows:
            # valor COM SINAL, mesma regra da view (bate com o valor da conta)
            bruto = float(row.get("valor_total") or 0)
            nominal = float(row.get("valor_nominal") or bruto)
            pago = float(row.pop("valor_pago_calc") or 0)
            tipo = row.get("tipo_titulo")
            sinal = 1 if tipo == "RECEBER" else -1 if tipo == "PAGAR" else 0
            parcial = (row.get("descricao_situacao") or "").upper() == "BAIXADO PARCIAL"
            # saldo EM ABERTO (mesma regra da vw_bi_fcp), com sinal: bate com o valor da conta no FCP
            saldo = max(nominal - pago, 0.0) if parcial else bruto
            row["valor_total"] = sinal * saldo
            row["valor_pago"] = pago

            row["codigo"] = row.get("codigo_raw")
            row["nome_empresa"] = nomes_empresa.get(str(row.get("id_empresa")))
            row["nome_pessoa"] = nomes_pessoa.get(str(row.get("id_pessoa")))

            for alvo, nomes in _CANDIDATOS.items():
                if row.get(alvo) is None:
                    row[alvo] = next((row[n] for n in nomes if row.get(n) is not None), None)
            if not row.get("descricao"):
                row["descricao"] = row.get("descricao_conta_resultado")
            if not row.get("origem"):
                row["origem"] = tipo

            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        rows = [r for r in rows if r["valor_total"] != 0]
        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


_DRE_CLASSE_DESPESAS = "3.3"
 
 
@router.get("/despesas-mensal")
def get_dre_despesas_mensal(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    incluir_abertos: bool = Query(True),
    current_user: dict = Depends(get_current_user),
):
    """Contas analíticas de despesa × empresa × mês (alimenta os gráficos de linha da DRE)."""
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
 
    try:
        filtros = [
            "tenant_id = %s",
            "(numero_conta_resultado = %s OR numero_conta_resultado LIKE %s)",
        ]
        params = [current_user["tenant_id"], _DRE_CLASSE_DESPESAS, f"{_DRE_CLASSE_DESPESAS}.%"]
 
        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)
 
        if data_inicio:
            inicio = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("mes_competencia >= %s")
            params.append(inicio.isoformat())
        if data_fim:
            filtros.append("mes_competencia <= %s")
            params.append(data_fim)
        if not incluir_abertos:
            filtros.append("em_aberto = 0")
 
        sql = f"""
            SELECT
                pc.classificacao,
                pc.descricao,
                v.id_empresa,
                v.id_pessoa,
                v.periodo,
                v.total
            FROM plano_contas_bi pc
            JOIN (
                SELECT id_empresa,
                       id_pessoa,
                       numero_conta_resultado,
                       LEFT(mes_competencia, 7) AS periodo,
                       SUM(valor_dre)           AS total
                FROM vw_bi_dre
                WHERE {' AND '.join(filtros)}
                GROUP BY id_empresa, id_pessoa, numero_conta_resultado, LEFT(mes_competencia, 7)
            ) v ON v.numero_conta_resultado = pc.classificacao
            WHERE pc.grupo = 'Resultado' AND pc.eh_analitica = 1
            ORDER BY pc.classificacao, v.periodo
        """
 
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        nomes = _nomes_pessoas(cursor, {r["id_pessoa"] for r in rows})
        for row in rows:
            row["total"] = float(row["total"] or 0)
            row["nome_pessoa"] = nomes.get(str(row["id_pessoa"]))
 
        return {"total": len(rows), "data": rows}
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────────────────────────
# GET /fluxo-caixa — REALIZADO (títulos baixados, por mês da baixa) — conta × empresa × mês × pessoa (periodo "YYYY-MM").
# Cada linha traz id_pessoa e nome_pessoa: o filtro de Pessoa BI é aplicado no front
# (mesmo padrão do ReceberService).
# ─────────────────────────────────────────────────────────────
@router.get("/fluxo-caixa")
def get_fluxo_caixa(
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = ["tenant_id = %s"]
        params = [current_user["tenant_id"]]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if data_inicio:
            inicio = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("mes_baixa >= %s")
            params.append(inicio.isoformat())

        if data_fim:
            filtros.append("mes_baixa <= %s")
            params.append(data_fim)

        where = f"WHERE {' AND '.join(filtros)}"

        sql = f"""
            SELECT
                pc.classificacao,
                pc.descricao,
                pc.eh_analitica,
                v.id_empresa,
                v.id_pessoa,
                v.periodo,
                SUM(v.valor_dre) AS total,
                MAX(v.ultima_atualizacao) AS ultima_atualizacao
            FROM plano_contas_bi pc
            JOIN (
                SELECT id_empresa,
                       id_pessoa,
                       numero_conta_resultado,
                       LEFT(mes_baixa, 7) AS periodo,
                       SUM(valor_caixa)         AS valor_dre,
                       MAX(ultima_atualizacao)  AS ultima_atualizacao
                FROM vw_bi_fluxo_caixa
                {where}
                GROUP BY id_empresa, id_pessoa, numero_conta_resultado, LEFT(mes_baixa, 7)
            ) v
              ON v.numero_conta_resultado = pc.classificacao
              OR v.numero_conta_resultado LIKE CONCAT(pc.classificacao, '.%%')
            WHERE pc.grupo = 'Resultado'
            GROUP BY pc.classificacao, pc.descricao, pc.eh_analitica, v.id_empresa, v.id_pessoa, v.periodo
            ORDER BY pc.classificacao, v.periodo
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        nomes = _nomes_pessoas(cursor, {r["id_pessoa"] for r in rows})

        for row in rows:
            row["total"] = float(row["total"] or 0)
            row["eh_analitica"] = bool(row["eh_analitica"])
            row["nome_pessoa"] = nomes.get(str(row["id_pessoa"]))
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────────
# GET /fluxo-caixa/titulos — títulos BAIXADOS que compõem uma conta (drawer).
# valor_total já vem COM SINAL e = valor efetivamente pago (bate com o valor da conta na tela).
# ─────────────────────────────────────────────────────────────
@router.get("/fluxo-caixa/titulos")
def get_fluxo_caixa_titulos(
    classificacao: str = Query(...),
    id_empresa: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = [
            "f.tenant_id = %s",
            "f.tipo_titulo IN ('RECEBER','PAGAR')",
            "UPPER(f.descricao_situacao) IN ('BAIXADO','BAIXADO PARCIAL')",
            "f.data_baixa IS NOT NULL",
            "f.numero_conta_resultado = %s",
        ]
        params = [current_user["tenant_id"], classificacao]

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        # mesma janela mensal da view (mes_baixa)
        if data_inicio:
            ini = date.fromisoformat(data_inicio).replace(day=1)
            filtros.append("f.data_baixa >= %s")
            params.append(ini.isoformat())
        if data_fim:
            fim = date.fromisoformat(data_fim)
            prox_mes = (fim.replace(day=1) + timedelta(days=32)).replace(day=1)
            filtros.append("f.data_baixa < %s")
            params.append(prox_mes.isoformat())

        sql = f"""
            SELECT
                f.*,
                COALESCE(NULLIF((
                    SELECT SUM(r.valor_pago) FROM recebimentos_bi r WHERE r.codigo_raw = f.codigo_raw
                ), 0), f.valor_total) AS valor_pago_calc
            FROM financeiro_bi f
            WHERE {' AND '.join(filtros)}
            ORDER BY f.data_baixa, f.codigo_raw
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # nomes (empresa e pessoa) só dos ids presentes
        ids_empresa = sorted({str(r["id_empresa"]) for r in rows if r.get("id_empresa") not in (None, "")})
        nomes_empresa: dict = {}
        if ids_empresa:
            cursor.execute(
                f"SELECT * FROM empresa_bi WHERE codigo_empresa IN ({','.join(['%s'] * len(ids_empresa))})",
                ids_empresa,
            )
            for e in cursor.fetchall():
                nome = next((e[c] for c in ["nome_fantasia", "razao_social", "nome_empresa", "nome", "fantasia", "descricao"] if e.get(c)), None)
                nomes_empresa.setdefault(str(e["codigo_empresa"]), nome)
        nomes_pessoa = _nomes_pessoas(cursor, {r.get("id_pessoa") for r in rows})

        for row in rows:
            pago = float(row.pop("valor_pago_calc") or 0)
            tipo = row.get("tipo_titulo")
            sinal = 1 if tipo == "RECEBER" else -1 if tipo == "PAGAR" else 0
            row["valor_total"] = sinal * pago
            row["valor_pago"] = pago
            row["codigo"] = row.get("codigo_raw")
            row["nome_empresa"] = nomes_empresa.get(str(row.get("id_empresa")))
            row["nome_pessoa"] = nomes_pessoa.get(str(row.get("id_pessoa")))
            if not row.get("descricao"):
                row["descricao"] = row.get("descricao_conta_resultado")
            if not row.get("origem"):
                row["origem"] = tipo
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

#!/usr/bin/env python3
"""
Troca cores fixas (tema escuro) por variáveis de tema dentro do bloco `styles: [`...`]` de componentes Angular.

Uso:   python theme-codemod.py src/app/**/*.ts          (altera os arquivos; cria .bak)
       python theme-codemod.py --dry-run arquivo.ts     (só mostra quantas trocas faria)
Regras (valor fixo → variável):
  #141922 → var(--modal-bg)      #1a202c → var(--modal-card)     #9ca3af → var(--muted)   #cbd5e1 → var(--text)
  rgba(255,255,255,.04|.05) → var(--tint-1)   .06 → var(--tint-2)   .08|.09|.1 → var(--tint-3)
  rgba(0,0,0,.55|.65) → var(--backdrop)       rgba(0,0,0,.45) → var(--shadow-color)
  #f43f5e → var(--accent) (ou var(--neg) em .neg / .state-erro)   #e11d48 → var(--accent-hover)
  #38bdf8 → var(--info)   #34d399 → var(--pos)   color-scheme:dark → color-scheme:var(--color-scheme)
  color:white → var(--text-strong), exceto em regras com fundo sólido de destaque (botões vermelhos).
Revise o resultado: tudo que não estiver na lista continua como estava.
"""
import re, sys, shutil

SIMPLES = [
    (r'color-scheme:\s*dark', 'color-scheme:var(--color-scheme)'),
    (r'#141922\b', 'var(--modal-bg)'),
    (r'#1a202c\b', 'var(--modal-card)'),
    (r'#9ca3af\b', 'var(--muted)'),
    (r'#cbd5e1\b', 'var(--text)'),
    (r'rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0?\.0[45]\s*\)', 'var(--tint-1)'),
    (r'rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0?\.06\s*\)', 'var(--tint-2)'),
    (r'rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0?\.(?:08|09|1|10)\s*\)', 'var(--tint-3)'),
    (r'rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.(?:55|65)\s*\)', 'var(--backdrop)'),
    (r'rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.45\s*\)', 'var(--shadow-color)'),
    (r'#e11d48\b', 'var(--accent-hover)'),
    (r'#38bdf8\b', 'var(--info)'),
    (r'#34d399\b', 'var(--pos)'),
]

REGRA = re.compile(r'([^{}]+)\{([^{}]*)\}')


def tema_regra(m: re.Match, contagem: dict) -> str:
    seletor, corpo = m.group(1), m.group(2)
    novo = corpo
    solido = re.search(r'background:\s*#f43f5e', corpo, re.I) is not None   # botão vermelho: texto branco fica
    if not solido:
        novo = re.sub(r'(?<![\w-])color:\s*white\b', 'color:var(--text-strong)', novo)
    alvo = 'var(--neg)' if re.search(r'\.neg\b|state-erro', seletor) else 'var(--accent)'
    novo = re.sub(r'#f43f5e\b', alvo, novo, flags=re.I)
    if novo != corpo:
        contagem['n'] += 1
    return f'{seletor}{{{novo}}}'


def processar(texto: str):
    a = texto.find('styles: [`')
    if a < 0:
        return texto, 0
    b = texto.find('`],', a)
    css = texto[a:b]
    total = 0
    for padrao, subst in SIMPLES:
        css, n = re.subn(padrao, subst, css, flags=re.I)
        total += n
    cont = {'n': 0}
    css = REGRA.sub(lambda m: tema_regra(m, cont), css)
    total += cont['n']
    return texto[:a] + css + texto[b:], total


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    dry = '--dry-run' in sys.argv
    for p in args:
        s = open(p, encoding='utf-8').read()
        novo, n = processar(s)
        print(f'{p}: {n} trocas' + (' (dry-run)' if dry else ''))
        if n and not dry:
            shutil.copyfile(p, p + '.bak')
            open(p, 'w', encoding='utf-8').write(novo)


if __name__ == '__main__':
    main()