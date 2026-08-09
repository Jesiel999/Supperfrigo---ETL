import logging
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


# ── Bronze: RAW ──────────────────────────────────────────────

def upsert_pessoa_sances_raw(registros: list[dict]) -> dict:
    """Insere/atualiza pessoas extraídas do Sances. PK natural: codigo_cliente."""
    if not registros:
        return {"processados": 0}

    conn = connection_mysql()
    cursor = conn.cursor()

    sql = """
        INSERT INTO pessoa_sances_raw
            (codigo_cliente, tipo, cpf_cnpj, nome_cliente, sexo)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            tipo = VALUES(tipo),
            cpf_cnpj = VALUES(cpf_cnpj),
            nome_cliente = VALUES(nome_cliente),
            sexo = VALUES(sexo)
    """

    linhas = [
        (r.get("codigo_cliente"), r.get("tipo"), r.get("cpf_cnpj"), r.get("nome_cliente"), r.get("sexo"))
        for r in registros
    ]

    cursor.executemany(sql, linhas)
    conn.commit()
    afetados = cursor.rowcount
    cursor.close()
    conn.close()

    logger.info(f"[pessoa_sances_raw] {len(registros)} registros processados.")
    return {"processados": len(registros), "afetados": afetados}


def upsert_pessoa_sults_raw(registros: list[dict]) -> dict:
    """Insere/atualiza pessoas extraídas do Sults. PK natural: id."""
    if not registros:
        return {"processados": 0}

    conn = connection_mysql()
    cursor = conn.cursor()

    sql = """
        INSERT INTO pessoa_sults_raw
            (id, nome, ativo, sexo, cpf, celular, telefone, email,
             dtCadastro, dtUltimaAlteracao, dtInativacao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nome = VALUES(nome),
            ativo = VALUES(ativo),
            sexo = VALUES(sexo),
            cpf = VALUES(cpf),
            celular = VALUES(celular),
            telefone = VALUES(telefone),
            email = VALUES(email),
            dtCadastro = VALUES(dtCadastro),
            dtUltimaAlteracao = VALUES(dtUltimaAlteracao),
            dtInativacao = VALUES(dtInativacao)
    """

    linhas = [
        (
            r.get("id"), r.get("nome"), r.get("ativo"), r.get("sexo"), r.get("cpf"),
            r.get("celular"), r.get("telefone"), r.get("email"),
            r.get("dtCadastro"), r.get("dtUltimaAlteracao"), r.get("dtInativacao"),
        )
        for r in registros
    ]

    cursor.executemany(sql, linhas)
    conn.commit()
    afetados = cursor.rowcount
    cursor.close()
    conn.close()

    logger.info(f"[pessoa_sults_raw] {len(registros)} registros processados.")
    return {"processados": len(registros), "afetados": afetados}


def upsert_endereco_sances_raw(pessoa_id: int, endereco: dict | None) -> None:
    """Grava o endereço aninhado no registro de pessoa. 1 endereço por pessoa."""
    if not pessoa_id or not endereco:
        return

    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO endereco_sances_raw
            (pessoa_id, rua, numero, complemento, bairro, cidade, uf, cep)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            rua = VALUES(rua), numero = VALUES(numero), complemento = VALUES(complemento),
            bairro = VALUES(bairro), cidade = VALUES(cidade), uf = VALUES(uf), cep = VALUES(cep)
        """,
        (
            pessoa_id, endereco.get("rua"), endereco.get("numero"), endereco.get("complemento"),
            endereco.get("bairro"), endereco.get("cidade"), endereco.get("uf"), endereco.get("cep"),
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def upsert_telefone_sances_raw(pessoa_id: int, telefone: dict | None) -> None:
    """Grava o telefone aninhado no registro de pessoa. 1 linha por pessoa (celular/comercial/residencial em colunas)."""
    if not pessoa_id or not telefone:
        return

    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO telefone_sances_raw (pessoa_id, celular, comercial, residencial)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            celular = VALUES(celular), comercial = VALUES(comercial), residencial = VALUES(residencial)
        """,
        (pessoa_id, telefone.get("celular"), telefone.get("comercial"), telefone.get("residencial")),
    )
    conn.commit()
    cursor.close()
    conn.close()


def upsert_email_sances_raw(pessoa_id: int, email: dict | None) -> None:
    """
    Grava os e-mails aninhados no registro de pessoa. O bloco "email" vem
    como {"principal": "...", "financeiro": "..."} — uma linha por tipo
    (chave do dict), pulando valores vazios.
    """
    if not pessoa_id or not email:
        return

    linhas = [(pessoa_id, endereco_email, tipo) for tipo, endereco_email in email.items() if endereco_email]
    if not linhas:
        return

    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO email_sances_raw (pessoa_id, email, tipo)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE email = VALUES(email)
        """,
        linhas,
    )
    conn.commit()
    cursor.close()
    conn.close()


def upsert_pessoa_sances_completo(registros: list[dict]) -> dict:
    """
    Recebe os registros crus da API Sances — já incluindo os blocos
    aninhados de endereco/email/telefone — e distribui os dados entre
    as 4 tabelas raw: pessoa_sances_raw, endereco_sances_raw,
    email_sances_raw, telefone_sances_raw.

    É esta função que o Step de Bronze deve chamar (não
    upsert_pessoa_sances_raw sozinha), pois é ela quem sabe separar o
    payload único do endpoint nas tabelas certas.
    """
    if not registros:
        return {"processados": 0}

    pessoas = [
        {
            "codigo_cliente": r.get("codigo_cliente"),
            "tipo": r.get("tipo"),
            "cpf_cnpj": r.get("cpf_cnpj"),
            "nome_cliente": r.get("nome_cliente"),
            "sexo": r.get("sexo"),
        }
        for r in registros
    ]
    resultado_pessoa = upsert_pessoa_sances_raw(pessoas)

    for r in registros:
        pessoa_id = r.get("codigo_cliente")
        upsert_endereco_sances_raw(pessoa_id, r.get("endereco"))
        upsert_email_sances_raw(pessoa_id, r.get("email"))
        upsert_telefone_sances_raw(pessoa_id, r.get("telefone"))

    logger.info(
        f"[pessoa_sances_completo] {len(registros)} pessoas processadas "
        f"(endereco/email/telefone distribuídos nas respectivas tabelas)."
    )
    return resultado_pessoa


def _primeiro_ou_lista(valores) -> str | None:
    """
    celular/telefone/email vêm como array na API do Sults, mas
    pessoa_sults_raw só tem uma coluna VARCHAR para cada (não é lista
    como email_sances_raw). Junta com "; " para não perder dado, mas
    se sua realidade tem pessoas com vários números/e-mails com
    frequência, vale considerar criar tabelas filhas como as da Sances.
    """
    if not valores:
        return None
    if isinstance(valores, str):
        return valores or None
    return "; ".join(v for v in valores if v) or None


def upsert_endereco_sults_raw(pessoa_id: int, endereco: dict | None) -> None:
    """Grava o endereço aninhado no registro de pessoa do Sults. 1 endereço por pessoa (delete+insert)."""
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM endereco_sults_raw WHERE pessoa_id = %s", (pessoa_id,))

    if endereco:
        cursor.execute(
            """
            INSERT INTO endereco_sults_raw
                (pessoa_id, uf, cidade, complemento, numero, bairro, cep, rua)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pessoa_id, endereco.get("uf"), endereco.get("cidade"), endereco.get("complemento"),
                endereco.get("numero"), endereco.get("bairro"), endereco.get("cep"), endereco.get("rua"),
            ),
        )

    conn.commit()
    cursor.close()
    conn.close()


def upsert_empresa_sults_raw(pessoa_id: int, empresa: list | None) -> None:
    """
    Grava os vínculos empregatícios da pessoa. Uma pessoa pode ter mais de
    um vínculo (várias unidades) — substitui tudo a cada execução
    (delete+insert), já que não há chave natural estável por vínculo.
    """
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empresa_sults_raw WHERE pessoa_id = %s", (pessoa_id,))

    if empresa:
        linhas = [
            (
                pessoa_id,
                (e.get("qualificacao") or {}).get("nome"),
                (e.get("qualificacao") or {}).get("id"),
                e.get("id"),
                e.get("nomeFantasia"),
                (e.get("cargo") or {}).get("nome"),
                (e.get("cargo") or {}).get("id"),
            )
            for e in empresa
        ]
        cursor.executemany(
            """
            INSERT INTO empresa_sults_raw
                (pessoa_id, qualificacao_nome, qualificacao_id, nomeFantasia_id,
                 nomeFantasia, nomeFantasia_cargo_nome, nomeFantasia_cargo_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            linhas,
        )

    conn.commit()
    cursor.close()
    conn.close()


def upsert_campo_adicional_sults_raw(pessoa_id: int, campos: list | None) -> None:
    """Grava os campos adicionais da pessoa. Substitui tudo a cada execução (delete+insert)."""
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campoAdicional_sults_raw WHERE pessoa_id = %s", (pessoa_id,))

    if campos:
        linhas = [
            (pessoa_id, c.get("valor"), c.get("id"), c.get("label"))
            for c in campos
        ]
        cursor.executemany(
            """
            INSERT INTO campoAdicional_sults_raw (pessoa_id, valor, id_campoAdicional, label)
            VALUES (%s, %s, %s, %s)
            """,
            linhas,
        )

    conn.commit()
    cursor.close()
    conn.close()


def upsert_pessoa_sults_completo(registros: list[dict]) -> dict:
    """
    Recebe os registros crus da API Sults — já incluindo os blocos
    aninhados de endereco/empresa/campoAdicional — e distribui os dados
    entre pessoa_sults_raw, endereco_sults_raw, empresa_sults_raw e
    campoAdicional_sults_raw.
    """
    if not registros:
        return {"processados": 0}

    pessoas = [
        {
            "id": r.get("id"),
            "nome": r.get("nome"),
            "ativo": r.get("ativo"),
            "sexo": r.get("sexo"),
            "cpf": r.get("cpf"),
            "celular": _primeiro_ou_lista(r.get("celular")),
            "telefone": _primeiro_ou_lista(r.get("telefone")),
            "email": _primeiro_ou_lista(r.get("email")),
            "dtCadastro": r.get("dtCadastro"),
            "dtUltimaAlteracao": r.get("dtUltimaAlteracao"),
            "dtInativacao": r.get("dtInativacao"),
        }
        for r in registros
    ]
    resultado_pessoa = upsert_pessoa_sults_raw(pessoas)

    for r in registros:
        pessoa_id = r.get("id")
        upsert_endereco_sults_raw(pessoa_id, r.get("endereco"))
        upsert_empresa_sults_raw(pessoa_id, r.get("empresa"))
        upsert_campo_adicional_sults_raw(pessoa_id, r.get("campoAdicional"))

    logger.info(
        f"[pessoa_sults_completo] {len(registros)} pessoas processadas "
        f"(endereco/empresa/campoAdicional distribuídos nas respectivas tabelas)."
    )
    return resultado_pessoa


def buscar_raw_para_transform() -> dict:
    """
    Busca os dados raw dos dois sistemas para a transformação Silver.
    A união (match por CPF/CNPJ) acontece na camada Silver, não aqui.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pessoa_sances_raw")
    sances = cursor.fetchall()

    cursor.execute("SELECT * FROM pessoa_sults_raw")
    sults = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"sances": sances, "sults": sults}


# ── Silver: BI ───────────────────────────────────────────────

def upsert_pessoa_bi(registros: list[dict]) -> dict:
    """
    Insere/atualiza pessoas unificadas em pessoa_bi.

    ATENÇÃO: usa cpf_cnpj como chave de upsert (UNIQUE KEY), mas o desenho
    atual de pessoa_bi não tem essa coluna — ver observação no README.
    Sem uma chave estável, cada execução do Silver duplicaria os registros.
    """
    if not registros:
        return {"processados": 0}

    conn = connection_mysql()
    cursor = conn.cursor()

    sql = """
        INSERT INTO pessoa_bi
            (cpf_cnpj, id_sances, id_sults, id_multisys, id_nectar, id_econnect,
             nome, sexo, colaborador, criado_em, atualizado_em)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            id_sances = COALESCE(VALUES(id_sances), id_sances),
            id_sults = COALESCE(VALUES(id_sults), id_sults),
            nome = VALUES(nome),
            sexo = VALUES(sexo),
            colaborador = VALUES(colaborador),
            atualizado_em = NOW()
    """

    linhas = [
        (
            r.get("cpf_cnpj"), r.get("id_sances"), r.get("id_sults"),
            r.get("id_multisys"), r.get("id_nectar"), r.get("id_econnect"),
            r.get("nome"), r.get("sexo"), r.get("colaborador", 0),
        )
        for r in registros
    ]

    cursor.executemany(sql, linhas)
    conn.commit()
    afetados = cursor.rowcount
    cursor.close()
    conn.close()

    logger.info(f"[pessoa_bi] {len(registros)} registros processados.")
    return {"processados": len(registros), "afetados": afetados}
