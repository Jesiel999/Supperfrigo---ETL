"""
Gera os modelos .docx com campos {{ }} a partir dos termos originais.
Uso: python build_templates.py
Saída: ./modelos/termo_*.docx
"""
import copy
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

SRC_NOTE = "/mnt/user-data/uploads/TERMO_DE_RESPONSABILIDADE_NOTEBOOK_-_EDERALDO_NOVO.docx"
SRC_CEL = "/mnt/user-data/uploads/06_01_24_TERMO_DE_RESPONSABILIDADE_DE_ENTREGA_CELULAR_-_EDERALDO.docx"
OUT = "modelos"


# ---------------------------------------------------------------- helpers
def _base_rpr(p):
    for r in p._p.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is not None:
            return copy.deepcopy(rpr)
    return None


def _sem_negrito(rpr):
    if rpr is not None:
        for tag in ("w:b", "w:bCs", "w:u"):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)
    return rpr


def set_text(p, text, bold_all=None, rpr_override=None):
    """Substitui o texto do parágrafo mantendo a formatação do 1º run.
    Aceita **negrito** inline."""
    rpr = _sem_negrito(copy.deepcopy(rpr_override) if rpr_override is not None else _base_rpr(p))
    for child in list(p._p):
        if child.tag != qn("w:pPr"):
            p._p.remove(child)
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        if rpr is not None:
            run._r.insert(0, copy.deepcopy(rpr))
        if i % 2 == 1 or bold_all:
            run.bold = True


def clone_after(ref_p, text):
    new = copy.deepcopy(ref_p._p)
    ref_p._p.addnext(new)
    para = Paragraph(new, ref_p._parent)
    set_text(para, text)
    return para


def delete(p):
    p._p.getparent().remove(p._p)


def replace_in_paragraph(p, old, new):
    """Troca texto mesmo que ele esteja quebrado em vários runs."""
    runs = [r for r in p._p.iter(qn("w:r")) if r.find(qn("w:t")) is not None]
    texts = [r.find(qn("w:t")).text or "" for r in runs]
    joined = "".join(texts)
    idx = joined.find(old)
    if idx < 0:
        return False
    end = idx + len(old)
    pos = 0
    first = True
    for r, t in zip(runs, texts):
        s, e = pos, pos + len(t)
        pos = e
        if e <= idx or s >= end:
            continue
        a, b = max(idx, s) - s, min(end, e) - s
        t_new = t[:a] + (new if first else "") + t[b:]
        first = False
        node = r.find(qn("w:t"))
        node.text = t_new
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


def all_paragraphs(doc):
    for p in doc.element.body.iter(qn("w:p")):
        yield Paragraph(p, doc)


# ---------------------------------------------------------------- cabeçalho
def parametrizar_cabecalho(doc):
    h = doc.sections[0].header.paragraphs
    set_text(h[0], "{{ empresa.nome_fantasia }}")
    set_text(h[2], "Cnpj: {{ empresa.cnpj }}   I.E.: {{ empresa.ie }}")
    set_text(h[3], "{{ empresa.endereco }}")
    set_text(h[4], "{{ empresa.bairro }}   {{ empresa.cidade }}—{{ empresa.uf }}")
    set_text(h[5], "Cep: {{ empresa.cep }}  {{ empresa.telefone }}")


# ---------------------------------------------------------------- conteúdo por tipo
REGRAS_COMUNS_FIM = [
    "Em caso de dano, inutilização ou extravio do equipamento é necessário comunicar imediatamente o seu gestor.",
    "No caso de férias, licença maternidade ou qualquer outro afastamento das funções, o usuário deverá entregar o {item} e todos os seus acessórios ao seu gestor nas mesmas condições de uso e conservação verificadas por ocasião de seu recebimento até o período de retorno para a empresa.",
]
REGRA_SIGILO = [
    "O não cumprimento das devidas regras acarretará no recolhimento do {item}, no qual deverá constar todas as informações contidas no dispositivo até o momento da devolução, não podendo excluir e/ou transferir qualquer arquivo ou pasta que contenha informações da empresa e tampouco repassar informações a terceiros.",
    "Em casos de transferência intencional de informações de direito da empresa, o usuário estará sujeito a multa de R$50.000,00, podendo ser contato telefônico, fotos, arquivos, documentos, planilhas, conversas de Whatsapp e outros.",
    "É de responsabilidade do COLABORADOR manter as informações sigilosas e/ou confidenciais em áreas seguras (de acesso exclusivo do colaborador mediante login e senha), desta forma, restringindo o acesso indevido por parte de outros usuários não autorizados.",
]

TIPOS = {
    "notebook": dict(
        titulo="TERMO DE RESPONSABILIDADE PELA GUARDA E USO DE APARELHO NOTEBOOK",
        item="notebook", Item="Notebook",
        acessorios=[("CARREGADOR", "carregador"), ("MOUSE", "mouse"), ("TECLADO", "teclado"),
                    ("MONITOR", "monitor"), ("SUPORTE DE NOTEBOOK", "suporte"), ("MOUSE PAD", "mouse_pad")],
        regras=[
            "O {item} é de propriedade da empresa e sua utilização é exclusiva para fins comerciais não podendo ser utilizado em uso particular e tampouco baixar arquivos e instalar aplicativos que possa prejudicar o funcionamento do dispositivo.",
            "**A troca de senhas pode ser feita única e exclusivamente mediante autorização e acompanhamento do departamento de TI da empresa.**",
            "Não é permitido o uso do {item} fora da empresa, salvo autorização prévia junto ao seu gestor.",
        ] + REGRA_SIGILO + REGRAS_COMUNS_FIM,
    ),
    "tablet": dict(
        titulo="TERMO DE RESPONSABILIDADE PELA GUARDA E USO DE APARELHO TABLET",
        item="tablet", Item="Tablet",
        acessorios=[("CARREGADOR", "carregador"), ("CABO USB", "cabo_usb"), ("CAPA", "capa"),
                    ("PELÍCULA", "pelicula"), ("CANETA", "caneta")],
        regras=[
            "O {item} é de propriedade da empresa e sua utilização é exclusiva para fins comerciais não podendo ser utilizado em uso particular e tampouco baixar arquivos e instalar aplicativos que possa prejudicar o funcionamento do dispositivo.",
            "**A troca de senhas e a remoção do bloqueio de tela podem ser feitas única e exclusivamente mediante autorização e acompanhamento do departamento de TI da empresa.**",
            "O uso do {item} fora das dependências da empresa é permitido apenas para atividades profissionais, mediante autorização prévia junto ao seu gestor.",
        ] + REGRA_SIGILO + REGRAS_COMUNS_FIM,
    ),
    "monitor": dict(
        titulo="TERMO DE RESPONSABILIDADE PELA GUARDA E USO DE MONITOR",
        item="monitor", Item="Monitor",
        acessorios=[("CABO DE ENERGIA", "cabo_energia"), ("CABO DE VÍDEO (HDMI/VGA/DP)", "cabo_video"),
                    ("SUPORTE / BASE", "suporte")],
        regras=[
            "O {item} é de propriedade da empresa e sua utilização é exclusiva para fins comerciais, não podendo ser utilizado em uso particular.",
            "Não é permitido abrir, desmontar, reparar ou alterar o {item}, bem como remover etiquetas de patrimônio ou número de série.",
            "Não é permitido conectar ao {item} equipamentos pessoais ou que não tenham sido autorizados pelo departamento de TI da empresa.",
            "O usuário deve zelar pela conservação do {item}, evitando impactos, pressão sobre a tela, objetos pontiagudos e produtos de limpeza inadequados.",
            "A remoção do {item} do local de instalação só poderá ser feita mediante autorização e acompanhamento do departamento de TI da empresa.",
        ] + REGRAS_COMUNS_FIM,
    ),
    "generico": dict(
        titulo="TERMO DE RESPONSABILIDADE PELA GUARDA E USO DE EQUIPAMENTOS",
        item="equipamento", Item="Equipamento",
        acessorios=[],
        regras=[
            "Os equipamentos acima são de propriedade da empresa e sua utilização é exclusiva para fins comerciais, não podendo ser utilizados em uso particular.",
            "Não é permitido abrir, desmontar, reparar ou alterar os equipamentos sem autorização do departamento de TI da empresa.",
        ] + REGRAS_COMUNS_FIM,
    ),
}


def build_termo_notebook_like(slug, cfg):
    doc = Document(SRC_NOTE)
    P = doc.paragraphs
    parametrizar_cabecalho(doc)

    set_text(P[1], cfg["titulo"], bold_all=True)
    for r in P[1].runs:
        r.underline = True
    set_text(P[3], "Recebi da empresa {{ empresa.razao_social }} inscrita no CNPJ Nº {{ empresa.cnpj }},")

    # --- lista de itens (loop) -------------------------------------------
    item_line = ("{{ loop.index }} – {{ eq.tipo }}"
                 "{% if eq.marca %} - Marca: {{ eq.marca }}{% endif %}"
                 "{% if eq.cor %} - Cor: {{ eq.cor }}{% endif %}"
                 "{% if eq.condicao %} - Condição: {{ eq.condicao }}{% endif %}"
                 "{% if eq.modelo %} - Modelo: {{ eq.modelo }}{% endif %}"
                 "{% if eq.serie %} - Série: {{ eq.serie }}{% endif %}"
                 "{% if eq.nome %} - Identificação: {{ eq.nome }}{% endif %}")
    comp_line = "{% if eq.componentes %}Componentes: {{ eq.componentes }}{% endif %}"

    p_for = clone_after(P[4], "{%p for eq in equipamentos %}")          # antes do item
    P[4]._p.addnext(p_for._p)                                           # logo após o parágrafo vazio
    set_text(P[5], item_line)
    set_text(P[6], comp_line)
    p_end = clone_after(P[6], "{%p endfor %}")

    # --- acessórios --------------------------------------------------------
    corpo_rpr = _sem_negrito(_base_rpr(P[15]))
    acess = cfg["acessorios"]
    if acess:
        last = P[8]
        # reaproveita o parágrafo 8 como 1º acessório
        for i, (rotulo, chave) in enumerate(acess):
            tgt = P[8] if i == 0 else clone_after(last, "")
            set_text(tgt, f"**{rotulo}:**  {{{{ acessorios.{chave} }}}}", rpr_override=corpo_rpr)
            last = tgt
    else:
        delete(P[8])
    for idx in (9, 10, 11, 12, 13):
        delete(P[idx])

    # --- regras ----------------------------------------------------------------
    set_text(P[15], f"O {cfg['item']} deverá ser utilizado **ÚNICA e EXCLUSIVAMENTE** a serviço da empresa "
                    f"tendo em vista a atividade a ser exercida pelo **USUÁRIO,** não podendo de maneira alguma "
                    f"utilizar-se para meios ilícitos.")
    regras = [r.format(item=cfg["item"]) for r in cfg["regras"]]
    modelo_bullet_a, modelo_bullet_b = P[16], P[22]    # Normal-com-lista / List Paragraph
    anchor = P[23]
    # Insere novas regras após a última existente, depois remove as antigas
    novas = []
    ref_par = anchor
    for r in regras:
        ref_par = clone_after(ref_par, r)
        novas.append(ref_par)
    for idx in range(16, 24):
        delete(P[idx])

    # --- declaração / data / assinaturas ---------------------------------------
    set_text(P[25], "Declaro ser de minha responsabilidade o manuseio e conservação "
                    f"do{'s' if slug == 'generico' else ''} mesmo{'s' if slug == 'generico' else ''}, estando ciente da correta utilização e das devidas "
                    "regras a serem seguidas e do ressarcimento em caso de danificação por má utilização, "
                    "negligência e/ou extravio bem como sua devolução caso venha me desligar da empresa.")
    set_text(P[27], "{{ data.cidade }}-{{ data.uf }}, {{ data.dia }} de {{ data.mes }} de {{ data.ano }}.")

    # assinatura do colaborador (remove o content control ligado às propriedades do doc)
    p30 = P[30]
    for sdt in list(p30._p.iter(qn("w:sdt"))):
        sdt.getparent().remove(sdt)
    set_text(p30, "{{ colaborador.nome }}")
    p30.add_run().add_break()
    run = p30.add_run("CPF: {{ colaborador.cpf }}")
    rpr = _base_rpr(P[29])
    if rpr is not None:
        run._r.insert(0, copy.deepcopy(rpr))
    set_text(P[33], "{{ empresa.razao_social }}")
    set_text(P[34], "CNPJ {{ empresa.cnpj }}")

    doc.save(f"{OUT}/termo_{slug}.docx")


def build_celular():
    doc = Document(SRC_CEL)
    trocas = [
        ("Grupo Giiro", "{{ empresa.nome }}"),
        ("GALAXY A7", "{{ resumo.modelos }}"),
        ("RX8M40958SY", "{{ resumo.series }}"),
        ("62 8307-6263", "{{ resumo.chips }}"),
        ("Luana Carolina Pereira Netto", "{{ colaborador.nome }}"),
        ("951.370.171-91", "{{ colaborador.cpf }}"),
    ]
    for p in all_paragraphs(doc):
        for old, new in trocas:
            replace_in_paragraph(p, old, new)
    doc.save(f"{OUT}/termo_celular.docx")


if __name__ == "__main__":
    for slug, cfg in TIPOS.items():
        build_termo_notebook_like(slug, cfg)
    build_celular()
    print("ok")
