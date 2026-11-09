"""
Serviço de geração de termos de responsabilidade.

Fluxo:  modelo .docx (com campos {{ }})  ->  docxtpl preenche  ->  PDF
Conversão para PDF: LibreOffice (soffice) e, se não houver, Word via docx2pdf.
"""
import os
import shutil
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from docxtpl import DocxTemplate
from fastapi import HTTPException

BASE_DIR = Path(os.getenv("TERMOS_STORAGE_DIR", "storage/termos"))
MODELOS_DIR = BASE_DIR / "modelos"
EMITIDOS_DIR = BASE_DIR / "emitidos"
for _d in (MODELOS_DIR, EMITIDOS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Todos os acessórios que um modelo pode usar: {{ acessorios.<chave> }}
ACESSORIOS_CONHECIDOS = [
    "carregador", "mouse", "teclado", "monitor", "suporte", "mouse_pad",
    "cabo_usb", "capa", "pelicula", "caneta", "cabo_energia", "cabo_video",
]

# Documentação dos campos disponíveis para quem edita o modelo no Word
CAMPOS_DISPONIVEIS = {
    "empresa": ["nome", "razao_social", "nome_fantasia", "cnpj", "ie", "endereco",
                "bairro", "cidade", "uf", "cep", "telefone"],
    "colaborador": ["nome", "cpf"],
    "equipamentos (lista)": ["tipo", "nome", "marca", "modelo", "serie", "cor", "condicao",
                             "componentes", "processador", "memoria_ram", "armazenamento",
                             "tamanho", "so", "ip", "mac", "data_fabricacao", "observacao"],
    "chips (lista)": ["numero", "iccid"],
    "resumo": ["modelos", "series", "chips"],
    "acessorios": ACESSORIOS_CONHECIDOS,
    "data": ["dia", "mes", "ano", "cidade", "uf"],
}
EXEMPLO_LOOP = "{%p for eq in equipamentos %} ... {{ eq.marca }} ... {%p endfor %}"


# ----------------------------------------------------------------- contexto
def _txt(v) -> str:
    return "" if v is None else str(v).strip()


def _sim_nao(valor: bool) -> str:
    return "( X ) SIM   (   ) NÃO" if valor else "(   ) SIM   ( X ) NÃO"


def _componentes(row: dict) -> str:
    partes = []
    if row.get("processador"):
        partes.append(_txt(row["processador"]))
    if row.get("memoria_ram"):
        partes.append(f"{_txt(row['memoria_ram'])} de Memória RAM")
    if row.get("armazenamento"):
        partes.append(f"{_txt(row['armazenamento'])} de armazenamento")
    if row.get("tamanho"):
        partes.append(f"tela de {_txt(row['tamanho'])}")
    if row.get("so"):
        partes.append(_txt(row["so"]))
    return ", ".join(partes)


def montar_contexto(*, empresa: dict, colaborador: dict, equipamentos: list[dict],
                    chips: list[dict], acessorios: Optional[dict] = None,
                    data_emissao: Optional[date] = None) -> dict:
    data_emissao = data_emissao or date.today()

    itens = []
    for row in equipamentos:
        itens.append({
            "tipo": _txt(row.get("nome_tipo")) or "Equipamento",
            "nome": _txt(row.get("nome")),
            "marca": _txt(row.get("nome_marca")),
            "modelo": _txt(row.get("nome_modelo")),
            "serie": _txt(row.get("serie")),
            "cor": _txt(row.get("cor")),
            "condicao": _txt(row.get("condicao")),
            "componentes": _componentes(row),
            "processador": _txt(row.get("processador")),
            "memoria_ram": _txt(row.get("memoria_ram")),
            "armazenamento": _txt(row.get("armazenamento")),
            "tamanho": _txt(row.get("tamanho")),
            "so": _txt(row.get("so")),
            "ip": _txt(row.get("ip")),
            "mac": _txt(row.get("mac")),
            "data_fabricacao": (row["data_fabricacao"].strftime("%d/%m/%Y")
                                if row.get("data_fabricacao") else ""),
            "observacao": _txt(row.get("observacao")),
        })

    lista_chips = [{"numero": _txt(c.get("numero")), "iccid": _txt(c.get("iccid"))} for c in chips]

    # acessórios: monitor é marcado automaticamente se algum equipamento tem id_monitor
    marcados = {k: False for k in ACESSORIOS_CONHECIDOS}
    if any(r.get("id_monitor") for r in equipamentos):
        marcados["monitor"] = True
    marcados.update({k: bool(v) for k, v in (acessorios or {}).items()})

    def junta(valores):
        return " / ".join(v for v in valores if v)

    empresa_ctx = {k: _txt(v) for k, v in empresa.items()}
    return {
        "empresa": empresa_ctx,
        "colaborador": {"nome": _txt(colaborador.get("nome")),
                        "cpf": _txt(colaborador.get("cpf_cnpj"))},
        "equipamentos": itens,
        "chips": lista_chips,
        "resumo": {
            "modelos": junta(f"{i['marca']} {i['modelo']}".strip() for i in itens),
            "series": junta(i["serie"] for i in itens),
            "chips": junta(c["numero"] for c in lista_chips),
        },
        "acessorios": {k: _sim_nao(v) for k, v in marcados.items()},
        "data": {
            "dia": f"{data_emissao.day:02d}",
            "mes": MESES[data_emissao.month - 1],
            "ano": str(data_emissao.year),
            "cidade": empresa_ctx.get("cidade", ""),
            "uf": empresa_ctx.get("uf", ""),
        },
    }


# ----------------------------------------------------------------- render
def renderizar_docx(modelo_path: Path, contexto: dict, destino: Path) -> Path:
    try:
        tpl = DocxTemplate(str(modelo_path))
        tpl.render(contexto)
        tpl.save(str(destino))
    except Exception as e:  # erro de sintaxe do Jinja no modelo editado
        raise HTTPException(422, f"Modelo inválido: {e}")
    return destino


def _achar_soffice() -> Optional[str]:
    cand = os.getenv("SOFFICE_PATH")
    if cand and Path(cand).exists():
        return cand
    for nome in ("soffice", "libreoffice"):
        achou = shutil.which(nome)
        if achou:
            return achou
    for caminho in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if Path(caminho).exists():
            return caminho
    return None


def docx_para_pdf(docx_path: Path) -> Path:
    pdf_path = docx_path.with_suffix(".pdf")

    soffice = _achar_soffice()
    if soffice:
        with tempfile.TemporaryDirectory() as profile:   # perfil isolado evita travar com Office aberto
            cmd = [soffice, f"-env:UserInstallation={Path(profile).as_uri()}",
                   "--headless", "--convert-to", "pdf",
                   "--outdir", str(docx_path.parent), str(docx_path)]
            r = subprocess.run(cmd, capture_output=True, timeout=120)
        if r.returncode == 0 and pdf_path.exists():
            return pdf_path

    try:  # alternativa no Windows: Microsoft Word instalado
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            return pdf_path
    except Exception:
        pass

    raise HTTPException(
        503,
        "Não foi possível converter para PDF. Instale o LibreOffice "
        "(ou defina SOFFICE_PATH) ou tenha o Microsoft Word + docx2pdf.",
    )


def gerar(modelo_path: Path, contexto: dict, nome_base: str, formato: str = "pdf") -> Path:
    """Gera o arquivo final em EMITIDOS_DIR e devolve o caminho."""
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_final = EMITIDOS_DIR / f"{nome_base}_{carimbo}.docx"
    renderizar_docx(modelo_path, contexto, docx_final)
    if formato == "docx":
        return docx_final
    pdf = docx_para_pdf(docx_final)
    return pdf


def _paragrafos_desbalanceados(docx_path: Path) -> list[str]:
    """Procura parágrafos do modelo com '{{' sem '}}' (ou '{%' sem '%}').
    O Jinja não reclama disso e o docxtpl simplesmente apaga o trecho, então checamos antes."""
    import re
    import zipfile
    ruins = []
    with zipfile.ZipFile(docx_path) as z:
        for nome in z.namelist():
            if nome.startswith("word/") and nome.endswith(".xml"):
                xml = z.read(nome).decode("utf8", "ignore")
                for par in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
                    texto = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", par))
                    if texto.count("{{") != texto.count("}}") or texto.count("{%") != texto.count("%}"):
                        ruins.append(texto.strip()[:80])
    return ruins


def validar_modelo(path: Path):
    """Renderiza com dados fictícios: pega erro de sintaxe antes de salvar o modelo."""
    exemplo = montar_contexto(
        empresa={k: "teste" for k in CAMPOS_DISPONIVEIS["empresa"]},
        colaborador={"nome": "Fulano de Tal", "cpf_cnpj": "000.000.000-00"},
        equipamentos=[{"nome_tipo": "Notebook", "nome_marca": "X", "nome_modelo": "Y", "serie": "123"}],
        chips=[{"numero": "62 90000-0000", "iccid": "123"}],
    )
    with tempfile.TemporaryDirectory() as tmp:
        ruins = _paragrafos_desbalanceados(path)
        if ruins:
            raise HTTPException(422, f"Campo mal formado no modelo (chaves sem fechar): {ruins[0]!r}")
        renderizar_docx(path, exemplo, Path(tmp) / "teste.docx")
