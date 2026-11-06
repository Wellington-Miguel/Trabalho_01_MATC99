#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do Relatório Técnico em PDF — Padrão ABNT Condensado (Limite de 7 páginas).

Correções aplicadas:
1. Correção matemática das Equações (1), (2), (3) e (4) no Tópico 2:
   - Registro da fonte TrueType 'Segoe UI Symbol' (seguisym.ttf) para renderizar
     nativamente o operador XOR (⊕) sem quadrados pretos (.notdef / \\x00).
   - Preservação explícita dos expoentes e subscritos em todas as equações:
     Eq. (1): C_i = P_i ⊕ E_K(inc_32^i(J_0))
     Eq. (2): T = GHASH_H(AAD, Ciphertext) ⊕ E_K(J_0)
     Eq. (3): ΔT = Δ · H^(n-i+2) (mod P(x))
     Eq. (4): S = EM^d (mod N)  e  EM' = S^e (mod N)
   - Numeração sequencial (1) a (4) alinhada à margem direita.
2. Otimização estrutural de espaço para cumprir rigorosamente o limite máximo de 7 páginas:
   - Aglutinação dos elementos pré-textuais (Cabeçalho institucional, Autor, Título,
     Nota de natureza com recuo de 8 cm, Sumário compacto com líderes pontilhados e
     Local/Data no rodapé) na Página 1.
   - Redução da fonte dos Quadros 1 a 4 (listings de logs e comandos OpenSSL) para 6,2 pt
     (scriptsize/tiny) com padding enxuto (2,5 pt) e quebra segura em 104 colunas.
   - Tabelas 1 e 2 ocupando exatamente a largura útil (16,0 cm = textwidth) com fonte
     compacta (8,2 pt = small) e bordas abertas padrão IBGE/ABNT.
   - Fluxo contínuo entre as seções 1 a 8 (sem quebras de página forçadas) e referências
     bibliográficas NBR 6023 em espaçamento simples.
"""

import shutil
import textwrap
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

DIR_BASE = Path(__file__).resolve().parent
shutil.rmtree(DIR_BASE / "formulas_img", ignore_errors=True)

# Registro das fontes TrueType do Windows (Arial, Consolas e Segoe UI Symbol para operadores matemáticos)
FONT_DIR = Path("C:/Windows/Fonts")
if (FONT_DIR / "arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-BoldItalic",
    )
    FONT_BODY = "Arial"
    FONT_BOLD = "Arial-Bold"
    FONT_ITALIC = "Arial-Italic"
else:
    FONT_BODY = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_ITALIC = "Helvetica-Oblique"

if (FONT_DIR / "consola.ttf").exists():
    pdfmetrics.registerFont(TTFont("Consolas", str(FONT_DIR / "consola.ttf")))
    pdfmetrics.registerFont(TTFont("Consolas-Bold", str(FONT_DIR / "consolab.ttf")))
    FONT_MONO = "Consolas"
else:
    FONT_MONO = "Courier"

if (FONT_DIR / "seguisym.ttf").exists():
    pdfmetrics.registerFont(TTFont("SegoeUISymbol", str(FONT_DIR / "seguisym.ttf")))
    FONT_SYMBOL = "SegoeUISymbol"
else:
    FONT_SYMBOL = FONT_BODY

# Largura útil ABNT: A4 (21,0 cm) - 3,0 cm (esq) - 2,0 cm (dir) = 16,0 cm (\textwidth)
LARGURA_UTIL = 16.0 * cm


def preparar_simbolos_matematicos(texto_html: str) -> str:
    """
    Substitui o operador XOR (⊕) por tag de fonte explícita (SegoeUISymbol),
    visto que a fonte Arial padrão não possui o glifo U+2295 (o que gerava quadrados).
    """
    if FONT_SYMBOL != FONT_BODY and "⊕" in texto_html:
        return texto_html.replace("⊕", f'<font name="{FONT_SYMBOL}">⊕</font>')
    return texto_html


def p_abnt(texto_html: str, estilo: ParagraphStyle) -> Paragraph:
    """Wrapper de Paragraph que garante renderização limpa de símbolos matemáticos."""
    return Paragraph(preparar_simbolos_matematicos(texto_html), estilo)


class AbntDocTemplate(BaseDocTemplate):
    """
    Template ABNT (NBR 14724 / NBR 6027):
    - Alimenta automaticamente o Sumário (TableOfContents) com a numeração de página real.
    """

    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            if style_name == "ABNT_H1":
                texto_limpo = flowable.getPlainText()
                self.notify("TOCEntry", (0, texto_limpo, self.page))
            elif style_name == "ABNT_H2":
                texto_limpo = flowable.getPlainText()
                self.notify("TOCEntry", (1, texto_limpo, self.page))


def on_page_pre_textual(canvas, doc):
    """
    Página 1 (Elementos Pré-Textuais condensados: Capa/Folha de Rosto + Sumário):
    - Não exibe número de página no topo (NBR 14724).
    - Posiciona fixamente "SALVADOR - BA" e "Novembro de 2026" no rodapé da página.
    """
    canvas.saveState()
    canvas.setFont(FONT_BOLD, 10.5)
    x_centro = 3.0 * cm + (LARGURA_UTIL / 2.0)
    canvas.drawCentredString(x_centro, 2.2 * cm, "SALVADOR - BA")
    canvas.setFont(FONT_BODY, 10.5)
    canvas.drawCentredString(x_centro, 1.7 * cm, "Novembro de 2026")
    canvas.restoreState()


def on_page_textual(canvas, doc):
    """
    Elementos textuais e pós-textuais (a partir da Introdução):
    - Numeração em algarismos arábicos no canto superior direito, a 2 cm da borda
      superior e a 2 cm da borda direita (NBR 14724).
    """
    canvas.saveState()
    canvas.setFont(FONT_BODY, 10)
    canvas.drawRightString(21.0 * cm - 2.0 * cm, 29.7 * cm - 1.8 * cm, str(doc.page))
    canvas.restoreState()


def quebrar_linhas_quadro(texto: str, largura_max: int = 100) -> str:
    """
    Garante que nenhuma linha dentro de um Quadro ultrapasse a largura do retângulo (16,0 cm).
    Em fonte Consolas 6,5 pt, 100 caracteres ocupam ~13,8 cm (dentro dos 16,0 cm).
    """
    linhas_formatadas = []
    for linha in texto.strip().splitlines():
        if len(linha) <= largura_max:
            linhas_formatadas.append(linha)
        else:
            recuo = "    " if not linha.startswith("  ") else "      "
            partes = textwrap.wrap(
                linha,
                width=largura_max,
                subsequent_indent=recuo,
                break_long_words=True,
                break_on_hyphens=False,
            )
            linhas_formatadas.extend(partes)
    return "\n".join(linhas_formatadas)


def bloco_equacao_abnt(
    formula_html: str, numero_eq: str, st_eq: ParagraphStyle, st_num: ParagraphStyle
) -> Table:
    """
    Simula o ambiente \\begin{equation} ... \\end{equation}:
    fórmula centralizada e numeração (1), (2), (3), (4) alinhada à margem direita.
    """
    t = Table(
        [[p_abnt(formula_html, st_eq), p_abnt(f"({numero_eq})", st_num)]],
        colWidths=[14.5 * cm, 1.5 * cm],
    )
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def criar_quadro_abnt(
    numero: int,
    titulo: str,
    conteudo_codigo: str,
    st_legenda: ParagraphStyle,
    st_codigo: ParagraphStyle,
    st_fonte: ParagraphStyle,
) -> list:
    """
    Cria um Quadro / Listing compacto (fonte scriptsize = 6.2 pt e padding mínimo).
    """
    texto_ajustado = quebrar_linhas_quadro(conteudo_codigo, largura_max=104)
    p_titulo = p_abnt(f"<b>Quadro {numero}</b> – {titulo}", st_legenda)
    t_quadro = Table([[Preformatted(texto_ajustado, st_codigo)]], colWidths=[LARGURA_UTIL])
    t_quadro.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    p_fonte = p_abnt("Fonte: O autor (2026).", st_fonte)
    return [KeepTogether([p_titulo, t_quadro, p_fonte])]


def criar_tabela_abnt(
    numero: int,
    titulo: str,
    dados_linhas: list,
    larguras_colunas: list,
    st_legenda: ParagraphStyle,
    st_fonte: ParagraphStyle,
    centralizar_ultima: bool = False,
) -> list:
    """
    Cria uma Tabela no padrão ABNT / IBGE (sem bordas laterais verticais,
    ocupando exatamente textwidth = 16,0 cm com fonte small).
    """
    p_titulo = p_abnt(f"<b>Tabela {numero}</b> – {titulo}", st_legenda)
    t = Table(dados_linhas, colWidths=larguras_colunas)
    comandos_estilo = [
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if centralizar_ultima:
        comandos_estilo.append(("ALIGN", (-1, 0), (-1, -1), "CENTER"))
    t.setStyle(TableStyle(comandos_estilo))
    p_fonte = p_abnt("Fonte: O autor (2026).", st_fonte)
    return [KeepTogether([p_titulo, t, p_fonte])]


def gerar_pdf(caminho_saida: str = "RELATORIO_TECNICO_MATC99.pdf"):
    doc = AbntDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=3.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=1.5 * cm,
        title="Trabalho 01 - Criptografia Aplicada (MATC99 - UFBA)",
        author="Wellington Miguel de Jesus Silva",
    )

    frame_abnt = Frame(
        3.0 * cm,
        1.5 * cm,
        LARGURA_UTIL,
        29.7 * cm - 3.5 * cm,
        id="frame_abnt",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )

    doc.addPageTemplates(
        [
            PageTemplate(id="PreTextual", frames=[frame_abnt], onPage=on_page_pre_textual),
            PageTemplate(id="Textual", frames=[frame_abnt], onPage=on_page_textual),
        ]
    )

    styles = getSampleStyleSheet()

    # ==========================================================================
    # ESTILOS TIPOGRAFIA ABNT OTIMIZADOS PARA <= 7 PÁGINAS
    # ==========================================================================
    st_capa_inst = ParagraphStyle(
        "CapaInst",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
    )
    st_capa_autor = ParagraphStyle(
        "CapaAutor",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
    )
    st_capa_titulo = ParagraphStyle(
        "CapaTitulo",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12.5,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    st_capa_subtitulo = ParagraphStyle(
        "CapaSubtitulo",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
    )
    st_natureza = ParagraphStyle(
        "NaturezaTrabalho",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.5,
        leading=12,
        alignment=TA_JUSTIFY,
        leftIndent=8.0 * cm,
    )
    st_titulo_sumario = ParagraphStyle(
        "TituloSumario",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=6,
    )

    st_h1 = ParagraphStyle(
        "ABNT_H1",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13.0,
        alignment=TA_LEFT,
        spaceBefore=5.5,
        spaceAfter=2.0,
        keepWithNext=True,
    )
    st_h2 = ParagraphStyle(
        "ABNT_H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.0,
        leading=12.2,
        alignment=TA_LEFT,
        spaceBefore=4.0,
        spaceAfter=1.5,
        keepWithNext=True,
    )

    st_corpo = ParagraphStyle(
        "ABNT_Corpo",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.4,
        leading=11.8,
        alignment=TA_JUSTIFY,
        firstLineIndent=1.25 * cm,
        spaceAfter=1.8,
    )

    st_alinea = ParagraphStyle(
        "ABNT_Alinea",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.4,
        leading=11.6,
        alignment=TA_JUSTIFY,
        leftIndent=1.25 * cm,
        firstLineIndent=0,
        spaceAfter=1.5,
    )

    # Estilo das equações matemáticas usando fonte normal + tags <i>, <sub> e <sup>
    st_eq = ParagraphStyle(
        "ABNT_Equacao",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10.0,
        leading=12.5,
        alignment=TA_CENTER,
    )
    st_eq_num = ParagraphStyle(
        "ABNT_EquacaoNum",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10.0,
        leading=12.5,
        alignment=TA_RIGHT,
    )

    st_legenda = ParagraphStyle(
        "ABNT_Legenda",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=8.8,
        leading=10.5,
        alignment=TA_LEFT,
        spaceBefore=3.5,
        spaceAfter=1.5,
        keepWithNext=True,
    )
    st_fonte = ParagraphStyle(
        "ABNT_Fonte",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=8.0,
        leading=9.5,
        alignment=TA_LEFT,
        spaceBefore=1.0,
        spaceAfter=2.5,
    )

    # Tabelas com fonte \small (8.2 pt)
    st_tab_cab = ParagraphStyle(
        "ABNT_TabCab",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8.2,
        leading=9.8,
        alignment=TA_LEFT,
    )
    st_tab_cel = ParagraphStyle(
        "ABNT_TabCel",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=8.0,
        leading=9.6,
        alignment=TA_LEFT,
    )
    st_tab_cel_centro = ParagraphStyle(
        "ABNT_TabCelCentro",
        parent=st_tab_cel,
        alignment=TA_CENTER,
    )

    # Quadros e Logs em \scriptsize / \tiny (6.2 pt) para mínima altura vertical e sem estourar largura
    st_codigo = ParagraphStyle(
        "ABNT_Codigo",
        parent=styles["Normal"],
        fontName=FONT_MONO,
        fontSize=6.2,
        leading=7.4,
        textColor=colors.black,
    )

    # Referências bibliográficas com espaçamento simples entre linhas (NBR 6023)
    st_ref = ParagraphStyle(
        "ABNT_Referencia",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=8.8,
        leading=10.2,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceAfter=2.5,
    )

    # Sumário compacto com líderes pontilhados
    st_toc_l0 = ParagraphStyle(
        "TOC_Level0",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        leftIndent=0,
        spaceAfter=1,
    )
    st_toc_l1 = ParagraphStyle(
        "TOC_Level1",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.2,
        leading=11.8,
        leftIndent=0.6 * cm,
        spaceAfter=0.5,
    )

    story = []

    # ==========================================================================
    # PÁGINA 1: ELEMENTOS PRÉ-TEXTUAIS CONDENSADOS (CAPA / ROSTO + SUMÁRIO)
    # ==========================================================================
    story.append(
        p_abnt(
            "UNIVERSIDADE FEDERAL DA BAHIA<br/>"
            "INSTITUTO DE COMPUTAÇÃO<br/>"
            "DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO",
            st_capa_inst,
        )
    )
    story.append(Spacer(1, 0.45 * cm))
    story.append(p_abnt("WELLINGTON MIGUEL DE JESUS SILVA", st_capa_autor))
    story.append(Spacer(1, 0.55 * cm))
    story.append(
        p_abnt(
            "TRABALHO 01 – CRIPTOGRAFIA APLICADA:<br/>"
            "PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS",
            st_capa_titulo,
        )
    )
    story.append(
        p_abnt(
            "Estudo de Caso: Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.",
            st_capa_subtitulo,
        )
    )
    story.append(Spacer(1, 0.45 * cm))
    story.append(
        p_abnt(
            "Relatório Técnico apresentado à disciplina MATC99 – Segurança e Auditoria "
            "de Sistemas de Informação, do Instituto de Computação da Universidade Federal "
            "da Bahia (UFBA), como requisito parcial para avaliação prática. "
            "Cenário Auditado: Miguelito Segurança e Tecnologia Ltda.",
            st_natureza,
        )
    )
    story.append(Spacer(1, 0.45 * cm))
    story.append(p_abnt("SUMÁRIO", st_titulo_sumario))
    toc = TableOfContents()
    toc.levelStyles = [st_toc_l0, st_toc_l1]
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(NextPageTemplate("Textual"))
    story.append(PageBreak())

    # ==========================================================================
    # SEÇÃO 1: INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA
    # ==========================================================================
    story.append(p_abnt("1 INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA", st_h1))
    story.append(
        p_abnt(
            "A digitalização de processos de contratação entre empresas (B2B) substituiu o papel físico "
            "e o reconhecimento de firma em cartório por fluxos eletrônicos baseados em rede. Embora essa "
            "transição reduza custos operacionais e acelere o fechamento de negócios, ela transfere toda a "
            "responsabilidade jurídica e financeira da transação para os controles criptográficos adotados "
            "pelas partes. Quando esses controles são mal projetados ou validados apenas de forma parcial, "
            "a organização fica exposta a fraudes financeiras e à perda de validade jurídica dos seus instrumentos contratuais.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Neste trabalho, analisa-se o cenário da empresa fictícia Miguelito Segurança e Tecnologia Ltda. "
            "(CNPJ 14.382.910/0001-55), sediada em Salvador/BA, que atua na operação de sistemas críticos e contrata "
            "serviços de nuvem híbrida, links redundantes MPLS/IPSec e custódia de módulos HSM junto a fornecedores "
            "externos. Durante uma revisão de auditoria sobre a tramitação do Contrato Comercial nº 2026/00849-MST, "
            "celebrado com a fornecedora Parceiro Infraestrutura e Cloud Computing Ltda. "
            "(parceiro.miguelito.com.br, CNPJ 67.419.002/0001-83) no valor global de R$ 1.450.000,00 "
            "(dividido em 12 parcelas mensais de R$ 120.833,33), surgiram indícios de duas falhas graves no processo "
            "de troca e validação dos arquivos digitais: a suspeita de manipulação de cláusulas financeiras durante o "
            "trânsito do documento e o recebimento de contratos assinados com certificados digitais não reconhecidos "
            "pela governança interna.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Do ponto de vista de segurança da informação e perícia forense, o incidente enfrentado pela Miguelito "
            "Segurança e Tecnologia envolve três riscos práticos distintos que precisam ser isolados e tratados:",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "a) interceptação e modificação em trânsito (<i>Man-in-the-Middle / Bit-Flipping</i>): contratos "
            "comerciais contêm dados bancários, valores de SLA, multas contratuais e especificações técnicas que não "
            "podem vazar para terceiros em trânsito (quebra de confidencialidade). Além disso, caso a empresa utilize "
            "um algoritmo de cifragem tradicional sem autenticação integrada, um atacante posicionado na rede pode "
            "alterar bytes específicos do texto cifrado para modificar valores no texto decifrado sem precisar conhecer a chave secreta;",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "b) adulteração documental pós-assinatura: mesmo quando um contrato é assinado por um representante "
            "legítimo, existe o risco de o arquivo sofrer modificações posteriores — seja por ação maliciosa interna, "
            "seja por interceptação — alterando, por exemplo, o valor da parcela mensal de R$ 120.833,33 para "
            "R$ 920.833,33. O mecanismo de auditoria precisa detectar alterações mínimas de um único caractere e "
            "rejeitar o documento imediatamente;",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "c) falsificação de identidade criptográfica (<i>Key Spoofing via Rogue CA</i>): um invasor externo "
            "pode gerar seu próprio par de chaves assimétricas, configurar uma Autoridade Certificadora própria "
            "(<i>Rogue CA</i>) e emitir um certificado digital preenchido com os mesmos dados cadastrais do fornecedor "
            "verdadeiro (CN = parceiro.miguelito.com.br). Se o setor responsável pela conferência verificar "
            "apenas se a assinatura digital é matematicamente válida contra a chave pública anexada ao processo — "
            "esquecendo de verificar quem emitiu aquele certificado —, o contrato fraudulento será aceito como autêntico.",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "Para responder a esse cenário, este trabalho implementa e documenta uma bancada experimental dividida em "
            "duas frentes complementares. Na Parte I, utiliza-se a biblioteca <i>cryptography</i> do Python "
            "para proteger o contrato com a cifra simétrica autenticada AES-256-GCM, testando a recuperação íntegra "
            "do arquivo e o comportamento do algoritmo frente à adulteração de bytes no criptograma e ao uso de chaves "
            "incorretas. Na Parte II, utiliza-se o OpenSSL em ambiente Linux para construir uma Infraestrutura "
            "de Chaves Públicas (PKI) completa, confrontando a Autoridade Certificadora interna da empresa "
            "(Miguelito Root CA) com uma autoridade atacante (Rogue CA) ao longo de três "
            "cenários de auditoria (Cenários A, B e C).",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 2: FUNDAMENTAÇÃO TEÓRICA
    # ==========================================================================
    story.append(p_abnt("2 FUNDAMENTAÇÃO TEÓRICA", st_h1))

    story.append(p_abnt("2.1 Criptografia Simétrica vs. Criptografia Assimétrica", st_h2))
    story.append(
        p_abnt(
            "A escolha entre algoritmos simétricos e assimétricos em uma arquitetura corporativa decorre diretamente "
            "das diferenças de desempenho, gestão de chaves e propriedades jurídicas de cada modelo. Na criptografia "
            "simétrica, o emissor e o destinatário compartilham exatamente a mesma chave secreta <i>K</i>, que é usada "
            "tanto na operação de cifragem quanto na decifragem (STALLINGS, 2023). Algoritmos simétricos modernos, como o "
            "AES (<i>Advanced Encryption Standard</i>), operam sobre blocos de bits por meio de rodadas sucessivas de "
            "substituição, permutação e combinação linear com chaves derivadas. Por serem operações leves e contarem com "
            "instruções dedicadas diretamente nos processadores atuais (<i>AES-NI</i>), as cifras simétricas atingem taxas "
            "de transferência de múltiplos gigabytes por segundo, sendo a única opção viável na prática para cifrar "
            "arquivos extensos, bancos de dados e tráfego de rede em tempo real.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Por outro lado, a criptografia simétrica possui duas limitações importantes para ambientes corporativos "
            "abertos: o problema da distribuição e escalabilidade de chaves, visto que em uma rede com <i>n</i> "
            "empresas parceiras seriam necessárias <i>n(n-1)/2</i> chaves secretas distintas trocadas por um canal seguro "
            "prévio; e a ausência de não-repúdio (irretratabilidade). Como tanto a contratante quanto a contratada "
            "possuem a mesma chave <i>K</i>, ambas têm capacidade técnica idêntica para gerar um arquivo cifrado e sua "
            "respectiva tag de verificação. Em uma disputa judicial, a Miguelito Segurança e Tecnologia não conseguiria "
            "provar a um juiz ou perito externo que determinado arquivo veio exclusivamente do fornecedor, pois a própria "
            "contratante poderia tê-lo gerado usando a chave compartilhada.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "A criptografia assimétrica (ou de chave pública) contorna esses dois limites ao substituir a chave "
            "compartilhada por um par de chaves matematicamente vinculadas: uma chave privada (mantida em sigilo "
            "absoluto pelo seu titular) e uma chave pública (que pode ser divulgada abertamente a qualquer parceiro). "
            "A segurança desse modelo baseia-se em funções de caminho único com alçapão (<i>trapdoor one-way functions</i>), "
            "nas quais é fácil calcular a função em um sentido usando a chave pública, mas computacionalmente inviável "
            "inverter o cálculo sem conhecer a informação secreta contida na chave privada — como ocorre no problema da "
            "fatoração do produto de dois primos grandes no algoritmo RSA (MORIARTY et al., 2016). Quando o titular usa "
            "sua chave privada exclusiva para assinar o resumo criptográfico de um documento, qualquer auditor pode usar "
            "a chave pública correspondente para conferir a assinatura. Como apenas o titular detém a chave privada, ele "
            "não pode negar posteriormente a autoria da assinatura, garantindo o não-repúdio jurídico.",
            st_corpo,
        )
    )

    story.append(p_abnt("2.2 Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)", st_h2))
    story.append(
        p_abnt(
            "Durante muitos anos, sistemas corporativos utilizaram cifras de bloco em modos de operação voltados "
            "exclusivamente para confidencialidade, como o CBC (<i>Cipher Block Chaining</i>) ou o CTR (<i>Counter Mode</i>). "
            "Embora esses modos escondam o conteúdo do texto em claro contra um observador passivo, eles não oferecem "
            "proteção nativa contra um atacante ativo que modifique o texto cifrado em trânsito. No modo Contador (CTR) "
            "puro, o algoritmo recebe um valor público inicial único de 96 bits (12 bytes) chamado <i>Nonce</i> (IV), "
            "concatena a ele um contador sequencial de 32 bits (formando o bloco inicial <i>J<sub>0</sub></i>) e cifra "
            "esse contador com a chave secreta <i>K</i>. O fluxo pseudoaleatório resultante (<i>keystream</i>) é combinado "
            "com cada bloco do texto em claro <i>P<sub>i</sub></i> através da operação lógica XOR (⊕) para produzir o "
            "bloco cifrado <i>C<sub>i</sub></i>, conforme expresso na Equação (1):",
            st_corpo,
        )
    )
    # Equação 1: C_i = P_i \oplus E_K(inc_{32}^i(J_0))
    story.append(
        bloco_equacao_abnt(
            "<i>C</i><sub><i>i</i></sub> = <i>P</i><sub><i>i</i></sub> ⊕ <i>E</i><sub><i>K</i></sub>(inc<sub>32</sub><sup><i>i</i></sup>(<i>J</i><sub>0</sub>))",
            "1",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        p_abnt(
            "O perigo de usar o modo CTR isoladamente reside na sua maleabilidade linear: como a decifragem "
            "consiste apenas em aplicar novamente a operação XOR entre o bloco cifrado recebido e o mesmo <i>keystream</i>, "
            "se um invasor interceptar o arquivo no caminho e inverter 1 bit em uma posição conhecida do bloco cifrado "
            "<i>C<sub>i</sub></i>, o processo de decifragem não apresentará nenhum erro e inverterá exatamente o mesmo bit "
            "no texto em claro recuperado <i>P<sub>i</sub></i>. Em um contrato comercial padronizado onde a posição das "
            "cláusulas é previsível, isso permitiria alterar dígitos de valores monetários às cegas (ataque de <i>bit-flipping</i>).",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Para eliminar essa vulnerabilidade, a norma NIST SP 800-38D (DWORKIN, 2007) definiu o AES-GCM "
            "(<i>Galois/Counter Mode</i>), um esquema AEAD (<i>Authenticated Encryption with Associated Data</i>) "
            "que une o modo contador ao mecanismo algébrico de autenticação GHASH. Antes de processar os dados, "
            "o algoritmo passa um bloco nulo de 128 bits pela cifra AES com a chave <i>K</i>, derivando a subchave secreta "
            "de autenticação <i>H = E<sub>K</sub>(0<sup>128</sup>)</i>. Em seguida, os blocos de 128 bits dos Dados "
            "Associados não cifrados (AAD) e os blocos já cifrados (<i>C<sub>1</sub>, ..., C<sub>n</sub></i>), seguidos "
            "de um bloco final com os tamanhos em bits de AAD e do texto cifrado, são tratados como coeficientes de um "
            "polinômio avaliado em <i>H</i> dentro do corpo finito de Galois GF(2<sup>128</sup>) módulo o polinômio "
            "irredutível <i>P(x) = x<sup>128</sup> + x<sup>7</sup> + x<sup>2</sup> + x + 1</i>. O resultado de 128 bits "
            "do GHASH recebe um XOR final (⊕) com a cifragem do contador inicial <i>E<sub>K</sub>(J<sub>0</sub>)</i>, gerando "
            "a <i>Authentication Tag</i> (<i>T</i>) de 16 bytes (128 bits), descrita na Equação (2):",
            st_corpo,
        )
    )
    # Equação 2: T = GHASH_H(AAD, Ciphertext) \oplus E_K(J_0)
    story.append(
        bloco_equacao_abnt(
            "<i>T</i> = GHASH<sub><i>H</i></sub>(AAD, Ciphertext) ⊕ <i>E</i><sub><i>K</i></sub>(<i>J</i><sub>0</sub>)",
            "2",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        p_abnt(
            "O diferencial de segurança do AES-GCM ocorre na decifragem, que segue estritamente a regra "
            "<i>Encrypt-then-MAC</i>: antes de liberar qualquer byte decifrado para a aplicação, a rotina recalcula a tag "
            "local <i>T'</i> sobre os blocos recebidos e a compara em tempo constante com a tag <i>T</i> anexada ao arquivo. "
            "Se um atacante alterar qualquer bloco cifrado <i>C<sub>i</sub></i> por uma máscara de erro não nula Δ "
            "(ou seja, <i>C'<sub>i</sub> = C<sub>i</sub> ⊕ Δ</i>), a diferença algébrica entre a tag recalculada e a "
            "original em GF(2<sup>128</sup>) é dada pela Equação (3):",
            st_corpo,
        )
    )
    # Equação 3: \Delta T = \Delta \cdot H^{n-i+2} \pmod{P(x)}
    story.append(
        bloco_equacao_abnt(
            "Δ<i>T</i> = Δ · <i>H</i><sup><i>n</i>−<i>i</i>+2</sup> (mod <i>P</i>(<i>x</i>))",
            "3",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        p_abnt(
            "Como GF(2<sup>128</sup>) é um corpo finito e não admite divisores de zero, o produto de dois elementos não "
            "nulos (<i>Δ ≠ 0</i> e <i>H ≠ 0</i>) jamais resulta em zero. Portanto, <i>T' ≠ T</i> obrigatoriamente, fazendo "
            "com que a biblioteca descarte o buffer de saída e lance imediatamente a exceção <i>InvalidTag</i>.",
            st_corpo,
        )
    )

    story.append(
        p_abnt("2.3 Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA", st_h2)
    )
    story.append(
        p_abnt(
            "Embora o AES-256-GCM proteja o arquivo em trânsito e em repouso entre sistemas que já compartilham uma chave, "
            "ele não substitui a assinatura jurídica de um contrato entre empresas distintas. Para garantir que a fornecedora "
            "não possa repudiar o contrato assinado, emprega-se a assinatura digital RSA com SHA-256 segundo o "
            "paradigma <i>Hash-then-Sign</i> (MORIARTY et al., 2016). Primeiro, o documento passa pela função hash "
            "SHA-256 (NIST, 2015), que comprime o arquivo em um resumo fixo de 256 bits (32 bytes) dotado de "
            "efeito avalanche e resistência a colisões. No esquema RSASSA-PKCS1-v1_5 (ou de modo probabilístico "
            "no RSA-PSS), o hash de 32 bytes e o identificador (OID) do algoritmo SHA-256 são encapsulados em uma "
            "estrutura ASN.1 (<i>DigestInfo</i>) com preenchimento até o tamanho do módulo RSA (256 bytes para chaves "
            "de 2048 bits), formando o bloco codificado <i>EM</i>. A geração da assinatura <i>S</i> com a chave privada "
            "<i>(d, N)</i> e a sua verificação com a chave pública <i>(e, N)</i> seguem a Equação (4):",
            st_corpo,
        )
    )
    # Equação 4: S = EM^d \pmod N e EM' = S^e \pmod N
    story.append(
        bloco_equacao_abnt(
            "<i>S</i> = <i>EM</i><sup><i>d</i></sup> (mod <i>N</i>) &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; <i>EM'</i> = <i>S</i><sup><i>e</i></sup> (mod <i>N</i>)",
            "4",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        p_abnt(
            "Todavia, a operação matemática da Equação (4) valida apenas que a assinatura foi produzida pelo detentor da "
            "chave privada correspondente àquela chave pública, mas não prova a quem pertence essa chave pública. Para "
            "vincular formalmente uma identidade jurídica a uma chave pública, utiliza-se a Infraestrutura de Chaves "
            "Públicas (PKI) e os certificados X.509 v3 padronizados pela RFC 5280 (COOPER et al., 2008). "
            "A organização institui uma Autoridade Certificadora Raiz (Root CA) — neste estudo, a "
            "Miguelito Root CA — cujo certificado autoassinado é instalado na <i>Trust Store</i> corporativa. "
            "A Root CA assina digitalmente o certificado do fornecedor (parceiro.crt), amarrando seu nome "
            "(Subject: CN = parceiro.miguelito.com.br) à sua chave pública e fixando extensões críticas "
            "(basicConstraints: CA:FALSE e keyUsage: digitalSignature, nonRepudiation). Dessa "
            "forma, a auditoria de um contrato assinado exige sempre duas checagens conjuntas: a verificação matemática "
            "da assinatura e a validação da cadeia X.509 até a Root CA corporativa (incluindo checagem de revogação via CRL ou OCSP).",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 3: METODOLOGIA E AMBIENTE EXPERIMENTAL
    # ==========================================================================
    story.append(p_abnt("3 METODOLOGIA E AMBIENTE EXPERIMENTAL", st_h1))
    story.append(
        p_abnt(
            "Para validar experimentalmente os controles criptográficos exigidos pela Miguelito Segurança e Tecnologia, "
            "foram construídos dois scripts automatizados em ambiente Linux (Ubuntu 24.04 LTS sob WSL2), registrando "
            "todos os eventos, resumos SHA-256 e códigos de retorno em arquivos de log. A Tabela 1 detalha a especificação "
            "do ambiente experimental.",
            st_corpo,
        )
    )

    linhas_tab1 = [
        [
            p_abnt("Componente / Ferramenta", st_tab_cab),
            p_abnt("Versão / Especificação", st_tab_cab),
            p_abnt("Finalidade nos Experimentos", st_tab_cab),
        ],
        [
            p_abnt("Sistema Operacional", st_tab_cel),
            p_abnt("Ubuntu 24.04 LTS (Kernel 6.6.87.2 WSL2)", st_tab_cel),
            p_abnt("Ambiente POSIX isolado para execução dos scripts e coleta de logs.", st_tab_cel),
        ],
        [
            p_abnt("Interpretador Python", st_tab_cel),
            p_abnt("Python 3.12.3 / 3.13.14", st_tab_cel),
            p_abnt("Execução do módulo parte1_aes_gcm.py com logging e type hints.", st_tab_cel),
        ],
        [
            p_abnt("Biblioteca Criptográfica", st_tab_cel),
            p_abnt("cryptography 41.0.7 / 50.0.2 (AESGCM)", st_tab_cel),
            p_abnt("Cifragem autenticada AES-256-GCM e captura de InvalidTag.", st_tab_cel),
        ],
        [
            p_abnt("Suíte OpenSSL CLI", st_tab_cel),
            p_abnt("OpenSSL 3.0.13 (30 Jan 2024)", st_tab_cel),
            p_abnt("Geração de chaves RSA 4096/2048-bit, emissão X.509 v3, dgst e verify.", st_tab_cel),
        ],
        [
            p_abnt("Contrato Comercial Base", st_tab_cel),
            p_abnt("contrato_miguelito.txt (2.841 bytes)", st_tab_cel),
            p_abnt("Contrato nº 2026/00849-MST (R$ 1.450.000,00 / 12x R$ 120.833,33).", st_tab_cel),
        ],
    ]
    story.extend(
        criar_tabela_abnt(
            1,
            "Especificação das ferramentas e ambiente experimental da auditoria",
            linhas_tab1,
            [3.8 * cm, 5.0 * cm, 7.2 * cm],
            st_legenda,
            st_fonte,
        )
    )

    # ==========================================================================
    # SEÇÃO 4: EXPERIMENTOS DA PARTE I (AES-256-GCM)
    # ==========================================================================
    story.append(p_abnt("4 EXPERIMENTOS DA PARTE I: PROTEÇÃO E INTEGRIDADE COM AES-256-GCM", st_h1))
    story.append(p_abnt("4.1 Procedimentos de Cifragem, Empacotamento e Decifragem", st_h2))
    story.append(
        p_abnt(
            "O script parte1_aes_gcm.py encapsula os artefatos criptográficos na classe "
            "CriptogramaGCM e executa inicialmente o fluxo legítimo em três etapas. Na primeira etapa, "
            "o contrato comercial contrato_miguelito.txt é lido em modo binário, totalizando exatos "
            "2.841 bytes e apresentando o resumo SHA-256 de referência "
            "9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Na segunda etapa, gera-se uma chave simétrica de 256 bits (32 bytes) via AESGCM.generate_key(256), "
            "um Nonce aleatório de 96 bits (12 bytes) via os.urandom(12) e define-se o campo de Dados "
            "Associados (AAD) como MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849. O "
            "criptograma completo é persistido no arquivo contrato_miguelito.enc com 2.869 bytes "
            "(12 bytes de Nonce + 2.841 bytes de Ciphertext + 16 bytes de Authentication Tag). Na terceira etapa, o "
            "script lê o arquivo .enc do disco, valida a Tag de 128 bits no método AESGCM.decrypt() "
            "e grava o texto recuperado em contrato_miguelito_recuperado.txt, comprovando igualdade estrita "
            "de bytes (original == recuperado: True) e preservação integral do hash SHA-256.",
            st_corpo,
        )
    )

    story.append(p_abnt("4.2 Logs de Execução e Análise dos Cenários de Falha", st_h2))
    story.append(
        p_abnt(
            "Concluída a validação legítima, o script submeteu o criptograma aos dois cenários de falha exigidos pela "
            "especificação: adulteração intencional de 1 byte no texto cifrado (<i>bit-flipping</i>) e tentativa de "
            "decifragem com chave simétrica incorreta. O Quadro 1 apresenta o log de execução capturado.",
            st_corpo,
        )
    )

    log_quadro1 = """[2026-11-04 15:36:36.889] [INFO] === Auditoria Criptográfica - Miguelito Segurança e Tecnologia ===
[2026-11-04 15:36:36.894] [INFO] Contrato carregado: contrato_miguelito.txt (2841 bytes)
[2026-11-04 15:36:36.895] [INFO] SHA-256 original: 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:36.901] [INFO] Arquivo cifrado salvo em: contrato_miguelito.enc (2869 bytes totais)
[2026-11-04 15:36:36.901] [INFO]   Chave AES-256 (32B) : 185c3c58dc5153a9b84ddaf0b85ec9933e52f67c44f8d150f42151a460aa8a28
[2026-11-04 15:36:36.902] [INFO]   Nonce / IV (12B)    : 1d5d2cb6580417d1f29dbf07
[2026-11-04 15:36:36.902] [INFO]   AAD                 : MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849
[2026-11-04 15:36:36.903] [INFO]   Auth Tag (16B)      : f987ee9b9f25a4ea8cbcac904a675b94
[2026-11-04 15:36:36.909] [INFO] Comparação de bytes (original == recuperado): True (2841 bytes)
[2026-11-04 15:36:36.910] [INFO] --- [Teste de Falha 1: Adulteração de 1 byte no Ciphertext (Bit-Flipping)] ---
[2026-11-04 15:36:36.910] [INFO] Byte modificado no offset 1420 (0x058C): 0x4B -> 0x4A
[2026-11-04 15:36:36.910] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag
[2026-11-04 15:36:36.911] [INFO] --- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---
[2026-11-04 15:36:36.912] [INFO] Chave errada  : 8908f8e494c7d2089963f9ca67836a1d43bfc0a0ea511d3343b5c0a40d8df58e
[2026-11-04 15:36:36.912] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag"""
    story.extend(
        criar_quadro_abnt(
            1,
            "Log de execução da Parte I (AES-256-GCM e captura de InvalidTag)",
            log_quadro1,
            st_legenda,
            st_codigo,
            st_fonte,
        )
    )

    story.append(
        p_abnt(
            "Conforme registrado no Quadro 1, no Teste de Falha 1 foi invertido 1 bit no byte localizado no "
            "offset 1420 (0x058C, alterando 0x4B para 0x4A via operação XOR 0x01). "
            "Durante a tentativa de decifragem com a chave correta, a avaliação do polinômio GHASH em GF(2<sup>128</sup>) "
            "resultou em uma tag divergente de f987ee9b..., disparando imediatamente a exceção "
            "<i>cryptography.exceptions.InvalidTag</i> sem liberar o texto em claro. De forma análoga, no "
            "Teste de Falha 2, a utilização da chave incorreta 8908f8e4... produziu uma subchave "
            "de hash <i>H'</i> e uma máscara de contador distintas das originais, bloqueando a operação com "
            "<i>InvalidTag</i>. Comprovam-se, assim, as propriedades de confidencialidade, integridade e "
            "autenticidade simétrica do criptograma.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 5: EXPERIMENTOS DA PARTE II (PKI E ASSINATURAS DIGITAIS)
    # ==========================================================================
    story.append(p_abnt("5 EXPERIMENTOS DA PARTE II: ASSINATURAS DIGITAIS E CADEIA DE CERTIFICAÇÃO", st_h1))
    story.append(p_abnt("5.1 Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)", st_h2))
    story.append(
        p_abnt(
            "O script parte2_pki_testes.sh provisionou no diretório pki_miguelito/ duas "
            "hierarquias de certificação X.509 v3 independentes. Na Cadeia Corporativa Legítima, foi gerada a "
            "autoridade raiz interna Miguelito Root CA com chave RSA de 4096 bits e certificado autoassinado "
            "(miguelito_root_ca.crt, Serial 362E0342...2D96, basicConstraints: CA:true), "
            "a qual emitiu e assinou o certificado legítimo do fornecedor parceiro.crt "
            "(CN = parceiro.miguelito.com.br, RSA 2048 bits, Serial 21CFB1F0...BCC2, "
            "CA:FALSE). Paralelamente, na Cadeia Atacante, configurou-se uma autoridade externa não "
            "confiável (Rogue Root CA, RSA 4096 bits) que emitiu um certificado forjado "
            "(parceiro_forjado.crt, Serial 35D9F02A...7127) preenchido com o mesmo "
            "CN = parceiro.miguelito.com.br do fornecedor legítimo.",
            st_corpo,
        )
    )

    story.append(p_abnt("5.2 Análise do Cenário A: Documento Íntegro e Cadeia Válida", st_h2))
    story.append(
        p_abnt(
            "No Cenário A, o documento original foi assinado com a chave privada legítima do fornecedor e auditado em "
            "duas etapas: verificação matemática da assinatura contra a chave pública do certificado e validação da "
            "cadeia X.509 contra a Miguelito Root CA, conforme detalhado no Quadro 2.",
            st_corpo,
        )
    )

    log_quadro2 = """# Comandos executados no Cenário A:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_legitimo/parceiro.key -out cenario_a.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem -signature cenario_a.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt pki_miguelito/parceiro_legitimo/parceiro.crt
# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.697] [INFO] Assinatura gerada: cenario_a.sig (256 bytes)
[2026-11-04 15:36:40.721] [INFO] Verificação da assinatura (openssl dgst -verify): Verified OK
[2026-11-04 15:36:40.743] [INFO] Validação da cadeia contra Miguelito Root CA: pki_miguelito/parceiro_legitimo/parceiro.crt: OK
[2026-11-04 15:36:40.750] [INFO] Resultado Cenário A -> DECISÃO: ACEITAR"""
    story.extend(
        criar_quadro_abnt(
            2,
            "Comandos e log de verificação do Cenário A (Assinatura e Cadeia Legítimas)",
            log_quadro2,
            st_legenda,
            st_codigo,
            st_fonte,
        )
    )
    story.append(
        p_abnt(
            "O resultado <i>Verified OK</i> comprova a integridade matemática do contrato após a assinatura, "
            "enquanto o retorno <i>parceiro.crt: OK</i> atesta que o certificado do signatário pertence à cadeia de confiança "
            "da Miguelito Root CA, justificando a decisão de aceitar o documento.",
            st_corpo,
        )
    )

    story.append(p_abnt("5.3 Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura", st_h2))
    story.append(
        p_abnt(
            "No Cenário B, simulou-se a adulteração de 1 caractere no valor da parcela mensal do contrato após a "
            "assinatura (de R$ 120.833,33 para R$ 920.833,33), submetendo o documento modificado "
            "à verificação contra a assinatura original colhida no Cenário A. O Quadro 3 exibe os resultados obtidos.",
            st_corpo,
        )
    )

    log_quadro3 = """# Comandos executados no Cenário B:
$ sed 's/R\\$ 120\\.833,33/R\\$ 920.833,33/g' contrato_miguelito.txt > contrato_adulterado.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem -signature cenario_a.sig contrato_adulterado.txt
# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.824] [INFO] SHA-256 original   : 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:40.832] [INFO] SHA-256 adulterado : 817d7fae7346f151320d2469a8546c52edefa478219948e1efbb75edf9f0a8d2
[2026-11-04 15:36:40.856] [WARN] Código de saída do OpenSSL: 1 | ossl_rsa_verify:bad signature -> Verification failure
[2026-11-04 15:36:40.868] [WARN] Resultado Cenário B -> DECISÃO: REJEITAR"""
    story.extend(
        criar_quadro_abnt(
            3,
            "Comandos e log de verificação do Cenário B (Adulteração Pós-Assinatura)",
            log_quadro3,
            st_legenda,
            st_codigo,
            st_fonte,
        )
    )
    story.append(
        p_abnt(
            "Conforme demonstrado no Quadro 3, a alteração de um único dígito provocou o efeito avalanche na função "
            "SHA-256, mudando o resumo de 9147c039... para 817d7fae.... Como o hash extraído "
            "do bloco PKCS#1 v1.5 da assinatura não confere com o novo hash calculado, a rotina ossl_rsa_verify "
            "falhou com <i>bad signature / Verification failure</i> (Exit Code 1), determinando a decisão de "
            "rejeitar o contrato.",
            st_corpo,
        )
    )

    story.append(p_abnt("5.4 Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável", st_h2))
    story.append(
        p_abnt(
            "No Cenário C, o documento original íntegro foi assinado com a chave privada do certificado falso "
            "(parceiro_forjado.key) emitido pela Rogue CA. O Quadro 4 apresenta o contraste "
            "entre a verificação matemática isolada e a validação da cadeia de certificação.",
            st_corpo,
        )
    )

    log_quadro4 = """# Comandos executados no Cenário C:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_forjado/parceiro_forjado.key -out cenario_c_forjado.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem -signature cenario_c_forjado.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt pki_miguelito/parceiro_forjado/parceiro_forjado.crt
# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.927] [INFO] 1) Verificação matemática com a chave pública falsa: Verified OK
[2026-11-04 15:36:40.949] [WARN] 2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code 2):
  CN = parceiro.miguelito.com.br -> error 20 at 0 depth lookup: unable to get local issuer certificate
  error pki_miguelito/parceiro_forjado/parceiro_forjado.crt: verification failed
[2026-11-04 15:36:40.962] [WARN] Resultado Cenário C -> DECISÃO: REJEITAR"""
    story.extend(
        criar_quadro_abnt(
            4,
            "Comandos e log de verificação do Cenário C (Certificado Forjado por Rogue CA)",
            log_quadro4,
            st_legenda,
            st_codigo,
            st_fonte,
        )
    )
    story.append(
        p_abnt(
            "A análise do Quadro 4 evidencia a diferença crítica entre integridade matemática e autenticidade da origem: "
            "a primeira verificação retorna <i>Verified OK</i> porque a assinatura foi conferida contra a própria "
            "chave pública falsa que a gerou. Todavia, na segunda etapa (openssl verify), a validação falha "
            "no nível 0 da cadeia (<i>error 20 at 0 depth lookup: unable to get local issuer certificate</i>, "
            "Exit Code 2), pois a Rogue Root CA não pertence à <i>Trust Store</i> da Miguelito Segurança e "
            "Tecnologia, impondo a decisão pericial de rejeitar o documento.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 6: MATRIZ DE DECISÃO E RECOMENDAÇÕES DE GOVERNANÇA
    # ==========================================================================
    story.append(p_abnt("6 MATRIZ DE DECISÃO E RECOMENDAÇÕES DE GOVERNANÇA", st_h1))
    story.append(p_abnt("6.1 Matriz Comparativa de Auditoria", st_h2))
    story.append(
        p_abnt(
            "A Tabela 2 sintetiza os resultados obtidos nos experimentos das Partes I e II, relacionando a integridade "
            "matemática do arquivo, a confiabilidade da identidade/chave e o veredito final de auditoria.",
            st_corpo,
        )
    )

    linhas_tab2 = [
        [
            p_abnt("Cenário Auditado", st_tab_cab),
            p_abnt("Integridade Matemática", st_tab_cab),
            p_abnt("Confiabilidade da Chave / CA", st_tab_cab),
            p_abnt("Evidência Técnica Capturada", st_tab_cab),
            p_abnt("Veredito", st_tab_cab),
        ],
        [
            p_abnt("Parte I – Fluxo Normal", st_tab_cel),
            p_abnt("Válida (Tag GCM e SHA-256 OK)", st_tab_cel),
            p_abnt("Válida (Chave simétrica correta)", st_tab_cel),
            p_abnt("2.841 bytes recuperados sem erro", st_tab_cel),
            p_abnt("ACEITAR", st_tab_cel_centro),
        ],
        [
            p_abnt("Parte I – Bit-Flipping", st_tab_cel),
            p_abnt("Inválida (GHASH diverge)", st_tab_cel),
            p_abnt("Válida (Chave simétrica correta)", st_tab_cel),
            p_abnt("cryptography.exceptions.InvalidTag", st_tab_cel),
            p_abnt("REJEITAR", st_tab_cel_centro),
        ],
        [
            p_abnt("Parte I – Chave Espúria", st_tab_cel),
            p_abnt("Não verificável (H' ≠ H)", st_tab_cel),
            p_abnt("Inválida (Chave não autorizada)", st_tab_cel),
            p_abnt("cryptography.exceptions.InvalidTag", st_tab_cel),
            p_abnt("REJEITAR", st_tab_cel_centro),
        ],
        [
            p_abnt("Parte II – Cenário A", st_tab_cel),
            p_abnt("Válida (Verified OK)", st_tab_cel),
            p_abnt("Válida (Miguelito Root CA: OK)", st_tab_cel),
            p_abnt("Exit Code 0 em dgst e verify", st_tab_cel),
            p_abnt("ACEITAR", st_tab_cel_centro),
        ],
        [
            p_abnt("Parte II – Cenário B", st_tab_cel),
            p_abnt("Inválida (Verification failure)", st_tab_cel),
            p_abnt("Válida (Certificado legítimo)", st_tab_cel),
            p_abnt("ossl_rsa_verify:bad signature (Exit 1)", st_tab_cel),
            p_abnt("REJEITAR", st_tab_cel_centro),
        ],
        [
            p_abnt("Parte II – Cenário C", st_tab_cel),
            p_abnt("Válida (Verified OK isolado)", st_tab_cel),
            p_abnt("Inválida (Fora da Trust Store)", st_tab_cel),
            p_abnt("error 20: unable to get issuer (Exit 2)", st_tab_cel),
            p_abnt("REJEITAR", st_tab_cel_centro),
        ],
    ]
    story.extend(
        criar_tabela_abnt(
            2,
            "Matriz comparativa de decisão dos cenários auditados nas Partes I e II",
            linhas_tab2,
            [3.2 * cm, 3.3 * cm, 3.6 * cm, 3.9 * cm, 2.0 * cm],
            st_legenda,
            st_fonte,
            centralizar_ultima=True,
        )
    )

    story.append(p_abnt("6.2 Recomendações Técnicas para a Miguelito Segurança e Tecnologia", st_h2))
    story.append(
        p_abnt(
            "Com base nos achados periciais, recomendam-se quatro medidas técnicas para a governança criptográfica da "
            "Miguelito Segurança e Tecnologia Ltda.:",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "a) validação obrigatória em duas etapas e fixação da <i>Trust Store</i>: o fluxo automatizado de recebimento "
            "de contratos deve executar obrigatoriamente a validação da cadeia X.509 (openssl verify -CAfile "
            "miguelito_root_ca.crt) antes de conferir a assinatura RSA, bloqueando certificados emitidos por CAs "
            "externas não homologadas;",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "b) isolamento da Root CA em HSM e adoção de CA Intermediária: manter a chave privada RSA de 4096 bits "
            "da Miguelito Root CA isolada <i>offline</i> em módulo HSM (FIPS 140-3) e instituir uma "
            "Autoridade Certificadora Intermediária para emitir os certificados operacionais dos parceiros B2B;",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "c) verificação de revogação (CRL / OCSP) e restrição de uso de chave: publicar Listas de Certificados "
            "Revogados (CRL) e exigir consulta OCSP (-crl_check) para barrar chaves privadas comprometidas "
            "antes da expiração, além de validar a presença de CA:FALSE e keyUsage: digitalSignature, "
            "nonRepudiation;",
            st_alinea,
        )
    )
    story.append(
        p_abnt(
            "d) gerenciamento seguro de Nonces e rotação de chaves no AES-256-GCM: garantir que cada operação de "
            "cifragem utilize um Nonce de 12 bytes exclusivo gerado via CSPRNG e rotacionar periodicamente as chaves "
            "simétricas, prevenindo ataques de reutilização de Nonce que exporiam o <i>keystream</i> e a subchave <i>H</i> do GHASH.",
            st_alinea,
        )
    )

    # ==========================================================================
    # SEÇÃO 7: CONCLUSÃO
    # ==========================================================================
    story.append(p_abnt("7 CONCLUSÃO", st_h1))
    story.append(
        p_abnt(
            "O trabalho experimental desenvolvido para o cenário da Miguelito Segurança e Tecnologia Ltda. "
            "permitiu demonstrar na prática como a cifragem simétrica autenticada e a infraestrutura de chaves públicas "
            "atuam de forma complementar na proteção de contratos digitais. Nos testes da Parte I, comprovou-se que o "
            "modo AES-256-GCM elimina a maleabilidade linear do modo contador puro por meio do polinômio "
            "GHASH em GF(2<sup>128</sup>), bloqueando instantaneamente tanto a adulteração de 1 bit no texto "
            "cifrado quanto a tentativa de leitura com chave espúria através da exceção <i>InvalidTag</i>.",
            st_corpo,
        )
    )
    story.append(
        p_abnt(
            "Nos experimentos da Parte II, a implementação da PKI com o OpenSSL evidenciou a fronteira entre integridade "
            "de conteúdo e autenticidade da identidade do signatário. Enquanto o Cenário B comprovou que qualquer alteração "
            "pós-assinatura em cláusulas financeiras invalida o resumo SHA-256 (<i>Verification failure</i>), "
            "o Cenário C demonstrou que uma assinatura matematicamente válida (<i>Verified OK</i>) deve ser "
            "rejeitada quando o certificado que transporta a chave pública não possui vínculo de confiança com a "
            "Miguelito Root CA (<i>error 20 at 0 depth lookup: unable to get local issuer certificate</i>). "
            "Conclui-se que a combinação do transporte cifrado em AES-256-GCM com a validação estrita da cadeia X.509 "
            "assegura integralmente a confidencialidade, a integridade, a autenticidade e o não-repúdio exigidos pela auditoria.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 8: REFERÊNCIAS BIBLIOGRÁFICAS (NBR 6023 - ESPAÇAMENTO SIMPLES)
    # ==========================================================================
    story.append(p_abnt("8 REFERÊNCIAS BIBLIOGRÁFICAS", st_h1))
    referencias_nbr6023 = [
        "COOPER, D.; SANTESSON, S.; FARRELL, S.; BOEYEN, S.; HOUSLEY, R.; POLK, W. <b>Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile</b>. [S. l.]: Internet Engineering Task Force (IETF), RFC 5280, maio 2008. Disponível em: &lt;https://datatracker.ietf.org/doc/html/rfc5280&gt;. Acesso em: 04 nov. 2026.",
        "DWORKIN, Morris J. <b>Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC</b>. Gaithersburg, MD: National Institute of Standards and Technology (NIST), Special Publication 800-38D, nov. 2007.",
        "MORIARTY, K.; KALISKI, B.; JONSSON, J.; RUSCH, A. <b>PKCS #1: RSA Cryptography Specifications Version 2.2</b>. [S. l.]: Internet Engineering Task Force (IETF), RFC 8017, nov. 2016. Disponível em: &lt;https://datatracker.ietf.org/doc/html/rfc8017&gt;. Acesso em: 04 nov. 2026.",
        "NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). <b>FIPS PUB 180-4: Secure Hash Standard (SHS)</b>. Gaithersburg, MD: U.S. Department of Commerce, ago. 2015.",
        "PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA). <b>Cryptography Documentation: Authenticated Encryption with Associated Data (AESGCM)</b>. [S. l.]: PyCA, 2026. Disponível em: &lt;https://cryptography.io/en/latest/hazmat/primitives/aead/&gt;. Acesso em: 04 nov. 2026.",
        "STALLINGS, William. <b>Criptografia e segurança de redes: princípios e práticas</b>. 8. ed. São Paulo: Pearson Education, 2023.",
    ]
    for ref in referencias_nbr6023:
        story.append(p_abnt(ref, st_ref))

    doc.multiBuild(story)
    print(f"PDF ABNT gerado com sucesso em: {caminho_saida}")


if __name__ == "__main__":
    gerar_pdf()
