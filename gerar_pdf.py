#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do Relatório Técnico em PDF — Rigorosamente Formatado no Padrão ABNT
(NBR 14724, NBR 6027, NBR 6023 e IBGE Normas de Apresentação Tabular).

Implementa:
1. Capa e Folha de Rosto em páginas separadas com "Salvador - BA / Novembro de 2026"
   posicionado exatamente no rodapé e nota de natureza do trabalho com recuo de 8 cm.
2. Sumário automático (NBR 6027) em página própria com líderes pontilhados (...) e
   numeração exata das páginas calculada em duas passagens (multiBuild).
3. Margens ABNT (Superior: 3 cm, Esquerda: 3 cm, Inferior: 2 cm, Direita: 2 cm),
   fonte Arial 12 pt, espaçamento entrelinhas 1,5 (18 pt), texto justificado e
   recuo de primeira linha de 1,25 cm em todos os parágrafos.
4. Numeração de páginas no canto superior direito (2 cm da borda superior e direita)
   apenas a partir da primeira página textual (Introdução), contando as folhas desde a Folha de Rosto.
5. Tabelas no padrão ABNT/IBGE (sem bordas verticais laterais ou internas; apenas fios
   horizontais no topo, abaixo do cabeçalho e na base), com título superior e Fonte inferior.
6. Códigos e Logs formatados como Quadros (Quadro 1 a Quadro 4) com bordas fechadas,
   título no topo e "Fonte: O autor (2026)." na base.
7. Equações matemáticas centralizadas com numeração sequencial (1), (2), (3) e (4)
   alinhada à margem direita.
8. Referências Bibliográficas conforme NBR 6023 (alinhadas à esquerda, espaçamento
   simples, títulos em negrito e URL com <...> e "Acesso em: 04 nov. 2026.").
"""

import shutil
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

# Registro das fontes TrueType (Arial e Consolas)
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

# Largura útil ABNT: A4 (21,0 cm) - 3,0 cm (esq) - 2,0 cm (dir) = 16,0 cm
LARGURA_UTIL = 16.0 * cm


class AbntDocTemplate(BaseDocTemplate):
    """
    Template ABNT (NBR 14724 / NBR 6027):
    - Captura os títulos (H1 e H2) para alimentar automaticamente o Sumário (TableOfContents)
      com a numeração de página real (contando a partir da Folha de Rosto, onde a Capa não é contada).
    """

    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            # Pela NBR 14724, a Capa (página física 1) não é contada na numeração de folhas;
            # a contagem inicia na Folha de Rosto (página física 2 = folha 1), portanto num_abnt = page - 1
            num_pagina_abnt = max(1, self.page - 1)
            if style_name == "ABNT_H1":
                texto_limpo = flowable.getPlainText()
                self.notify("TOCEntry", (0, texto_limpo, num_pagina_abnt))
            elif style_name == "ABNT_H2":
                texto_limpo = flowable.getPlainText()
                self.notify("TOCEntry", (1, texto_limpo, num_pagina_abnt))


def on_page_pre_textual(canvas, doc):
    """
    Elementos pré-textuais (Capa, Folha de Rosto e Sumário):
    - Não exibem número de página (NBR 14724).
    - Na Capa (pág. física 1) e na Folha de Rosto (pág. física 2), posicionam
      fixamente "SALVADOR - BA" e "Novembro de 2026" no rodapé da página.
    """
    canvas.saveState()
    if doc.page in (1, 2):
        canvas.setFont(FONT_BOLD, 12)
        # Centro horizontal da área útil ABNT: margem esquerda (3 cm) + metade de 16 cm (8 cm) = 11 cm
        x_centro = 3.0 * cm + (LARGURA_UTIL / 2.0)
        canvas.drawCentredString(x_centro, 2.7 * cm, "SALVADOR - BA")
        canvas.setFont(FONT_BODY, 12)
        canvas.drawCentredString(x_centro, 2.1 * cm, "Novembro de 2026")
    canvas.restoreState()


def on_page_textual(canvas, doc):
    """
    Elementos textuais e pós-textuais (a partir da Introdução):
    - Numeração em algarismos arábicos no canto superior direito, a 2 cm da borda
      superior e a 2 cm da borda direita (NBR 14724).
    - Número da folha = doc.page - 1 (pois a Capa não entra na contagem).
    """
    canvas.saveState()
    canvas.setFont(FONT_BODY, 10)
    num_folha = doc.page - 1
    canvas.drawRightString(21.0 * cm - 2.0 * cm, 29.7 * cm - 2.0 * cm, str(num_folha))
    canvas.restoreState()


def bloco_equacao_abnt(formula_html: str, numero_eq: str, st_eq: ParagraphStyle, st_num: ParagraphStyle) -> Table:
    """
    Cria uma equação destacada padrão ABNT: fórmula centralizada e numeração (1), (2)...
    alinhada à margem direita.
    """
    t = Table(
        [[Paragraph(formula_html, st_eq), Paragraph(f"({numero_eq})", st_num)]],
        colWidths=[14.2 * cm, 1.8 * cm],
    )
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
) -> KeepTogether:
    """
    Cria um Quadro / Listing padrão ABNT:
    - Título na parte superior: "Quadro X – Título"
    - Quadro com bordas fechadas laterais, superior e inferior
    - Fonte obrigatória na parte inferior: "Fonte: O autor (2026)."
    """
    p_titulo = Paragraph(f"<b>Quadro {numero}</b> – {titulo}", st_legenda)
    t_quadro = Table([[Preformatted(conteudo_codigo.strip(), st_codigo)]], colWidths=[LARGURA_UTIL])
    t_quadro.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    p_fonte = Paragraph("Fonte: O autor (2026).", st_fonte)
    return KeepTogether([p_titulo, t_quadro, p_fonte, Spacer(1, 6)])


def criar_tabela_abnt(
    numero: int,
    titulo: str,
    dados_linhas: list,
    larguras_colunas: list,
    st_legenda: ParagraphStyle,
    st_fonte: ParagraphStyle,
    centralizar_ultima: bool = False,
) -> KeepTogether:
    """
    Cria uma Tabela no padrão ABNT / IBGE:
    - Título na parte superior: "Tabela X – Título"
    - ABERTA nas laterais (sem bordas verticais externas ou internas)
    - Fios horizontais apenas no topo da tabela, abaixo do cabeçalho e na base
    - Fonte obrigatória na parte inferior: "Fonte: O autor (2026)."
    """
    p_titulo = Paragraph(f"<b>Tabela {numero}</b> – {titulo}", st_legenda)
    t = Table(dados_linhas, colWidths=larguras_colunas)
    comandos_estilo = [
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if centralizar_ultima:
        comandos_estilo.append(("ALIGN", (-1, 0), (-1, -1), "CENTER"))
    t.setStyle(TableStyle(comandos_estilo))
    p_fonte = Paragraph("Fonte: O autor (2026).", st_fonte)
    return KeepTogether([p_titulo, t, p_fonte, Spacer(1, 6)])


def gerar_pdf(caminho_saida: str = "RELATORIO_TECNICO_MATC99.pdf"):
    # Margens ABNT NBR 14724: Esquerda 3 cm, Superior 3 cm, Direita 2 cm, Inferior 2 cm
    doc = AbntDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=3.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=3.0 * cm,
        bottomMargin=2.0 * cm,
        title="Trabalho 01 - Criptografia Aplicada (MATC99 - UFBA)",
        author="Wellington Miguel de Jesus Silva",
    )

    frame_abnt = Frame(
        3.0 * cm,
        2.0 * cm,
        LARGURA_UTIL,
        29.7 * cm - 5.0 * cm,  # 24,7 cm de altura útil
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
    # ESTILOS TIPOGRAFIA GERAL ABNT (Fonte 12 pt, Entrelinhas 1,5 = 18 pt, Recuo 1,25 cm)
    # ==========================================================================
    st_capa_inst = ParagraphStyle(
        "CapaInst",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
    )
    st_capa_autor = ParagraphStyle(
        "CapaAutor",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
    )
    st_capa_titulo = ParagraphStyle(
        "CapaTitulo",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=21,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    st_capa_subtitulo = ParagraphStyle(
        "CapaSubtitulo",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
    )
    # Nota de natureza na Folha de Rosto: recuo de 8 cm da margem esquerda, espaçamento simples (NBR 14724)
    st_natureza = ParagraphStyle(
        "NaturezaTrabalho",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10,
        leading=13,
        alignment=TA_JUSTIFY,
        leftIndent=8.0 * cm,
    )
    st_titulo_central = ParagraphStyle(
        "TituloCentralPreTextual",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    # Títulos de Seção Primária e Secundária (NBR 6024)
    st_h1 = ParagraphStyle(
        "ABNT_H1",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True,
    )
    st_h2 = ParagraphStyle(
        "ABNT_H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    # Corpo do texto: Fonte 12, espaçamento 1,5 (18 pt), justificado, recuo de 1,25 cm na 1ª linha
    st_corpo = ParagraphStyle(
        "ABNT_Corpo",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        firstLineIndent=1.25 * cm,
        spaceAfter=6,
    )

    # Alíneas / Listas com recuo padronizado
    st_alinea = ParagraphStyle(
        "ABNT_Alinea",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        leftIndent=1.25 * cm,
        firstLineIndent=0,
        spaceAfter=6,
    )

    # Equações centralizadas e numeração à direita
    st_eq = ParagraphStyle(
        "ABNT_Equacao",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=11.5,
        leading=16,
        alignment=TA_CENTER,
    )
    st_eq_num = ParagraphStyle(
        "ABNT_EquacaoNum",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=11.5,
        leading=16,
        alignment=TA_RIGHT,
    )

    # Legendas (Topo) e Fontes (Base) de Tabelas e Quadros (tamanho 10, espaçamento simples - NBR 14724)
    st_legenda = ParagraphStyle(
        "ABNT_Legenda",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    st_fonte = ParagraphStyle(
        "ABNT_Fonte",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        spaceBefore=3,
        spaceAfter=8,
    )

    # Células de Tabela e Código de Quadros (tamanho menor conforme NBR 14724 Seção 5.1)
    st_tab_cab = ParagraphStyle(
        "ABNT_TabCab",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        alignment=TA_LEFT,
    )
    st_tab_cel = ParagraphStyle(
        "ABNT_TabCel",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.2,
        leading=12,
        alignment=TA_LEFT,
    )
    st_tab_cel_centro = ParagraphStyle(
        "ABNT_TabCelCentro",
        parent=st_tab_cel,
        alignment=TA_CENTER,
    )
    st_codigo = ParagraphStyle(
        "ABNT_Codigo",
        parent=styles["Normal"],
        fontName=FONT_MONO,
        fontSize=7.4,
        leading=10.2,
        textColor=colors.black,
    )

    # Referências Bibliográficas (NBR 6023: alinhadas à esquerda, espaçamento simples, separadas por 1 espaço simples)
    st_ref = ParagraphStyle(
        "ABNT_Referencia",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=12,
        leading=14.4,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceAfter=12,
    )

    # Estilos do Sumário (NBR 6027) com preenchimento pontilhado automático
    st_toc_l0 = ParagraphStyle(
        "TOC_Level0",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=20,
        leftIndent=0,
        spaceAfter=2,
    )
    st_toc_l1 = ParagraphStyle(
        "TOC_Level1",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=12,
        leading=18,
        leftIndent=0.8 * cm,
        spaceAfter=2,
    )

    story = []

    # ==========================================================================
    # PÁGINA 1: CAPA (NBR 14724)
    # ==========================================================================
    story.append(
        Paragraph(
            "UNIVERSIDADE FEDERAL DA BAHIA<br/>"
            "INSTITUTO DE COMPUTAÇÃO<br/>"
            "DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO",
            st_capa_inst,
        )
    )
    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph("WELLINGTON MIGUEL DE JESUS SILVA", st_capa_autor))
    story.append(Spacer(1, 4.5 * cm))
    story.append(
        Paragraph(
            "TRABALHO 01 – CRIPTOGRAFIA APLICADA:<br/>"
            "PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS",
            st_capa_titulo,
        )
    )
    story.append(
        Paragraph(
            "Estudo de Caso: Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.",
            st_capa_subtitulo,
        )
    )
    # O local e data ("SALVADOR - BA / Novembro de 2026") são desenhados no rodapé por on_page_pre_textual
    story.append(PageBreak())

    # ==========================================================================
    # PÁGINA 2: FOLHA DE ROSTO (NBR 14724)
    # ==========================================================================
    story.append(Paragraph("WELLINGTON MIGUEL DE JESUS SILVA", st_capa_autor))
    story.append(Spacer(1, 5.0 * cm))
    story.append(
        Paragraph(
            "TRABALHO 01 – CRIPTOGRAFIA APLICADA:<br/>"
            "PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS",
            st_capa_titulo,
        )
    )
    story.append(
        Paragraph(
            "Estudo de Caso: Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.",
            st_capa_subtitulo,
        )
    )
    story.append(Spacer(1, 3.5 * cm))
    story.append(
        Paragraph(
            "Relatório Técnico apresentado à disciplina MATC99 – Segurança e Auditoria "
            "de Sistemas de Informação, do Instituto de Computação da Universidade Federal "
            "da Bahia (UFBA), como requisito parcial para avaliação prática.<br/><br/>"
            "Cenário Auditado: Miguelito Segurança e Tecnologia Ltda.",
            st_natureza,
        )
    )
    # O local e data ("SALVADOR - BA / Novembro de 2026") são desenhados no rodapé por on_page_pre_textual
    story.append(PageBreak())

    # ==========================================================================
    # PÁGINA 3: SUMÁRIO (NBR 6027 - COM PONTILHADOS E PÁGINAS AUTOMÁTICAS)
    # ==========================================================================
    story.append(Paragraph("SUMÁRIO", st_titulo_central))
    toc = TableOfContents()
    toc.levelStyles = [st_toc_l0, st_toc_l1]
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(NextPageTemplate("Textual"))
    story.append(PageBreak())

    # ==========================================================================
    # SEÇÃO 1: INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA
    # ==========================================================================
    story.append(Paragraph("1 INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA", st_h1))
    story.append(
        Paragraph(
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
        Paragraph(
            "Neste trabalho, analisa-se o cenário da empresa fictícia <b>Miguelito Segurança e Tecnologia Ltda.</b> "
            "(CNPJ 14.382.910/0001-55), sediada em Salvador/BA, que atua na operação de sistemas críticos e contrata "
            "serviços de nuvem híbrida, links redundantes MPLS/IPSec e custódia de módulos HSM junto a fornecedores "
            "externos. Durante uma revisão de auditoria sobre a tramitação do <b>Contrato Comercial nº 2026/00849-MST</b>, "
            "celebrado com a fornecedora <i>Parceiro Infraestrutura e Cloud Computing Ltda.</i> "
            "(<code>parceiro.miguelito.com.br</code>, CNPJ 67.419.002/0001-83) no valor global de R$ 1.450.000,00 "
            "(dividido em 12 parcelas mensais de R$ 120.833,33), surgiram indícios de duas falhas graves no processo "
            "de troca e validação dos arquivos digitais: a suspeita de manipulação de cláusulas financeiras durante o "
            "trânsito do documento e o recebimento de contratos assinados com certificados digitais não reconhecidos "
            "pela governança interna.",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "Do ponto de vista de segurança da informação e perícia forense, o incidente enfrentado pela Miguelito "
            "Segurança e Tecnologia envolve três riscos práticos distintos que precisam ser isolados e tratados:",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "a) <b>interceptação e modificação em trânsito (<i>Man-in-the-Middle / Bit-Flipping</i>):</b> contratos "
            "comerciais contêm dados bancários, valores de SLA, multas contratuais e especificações técnicas que não "
            "podem vazar para terceiros em trânsito (quebra de confidencialidade). Além disso, caso a empresa utilize "
            "um algoritmo de cifragem tradicional sem autenticação integrada, um atacante posicionado na rede pode "
            "alterar bytes específicos do texto cifrado para modificar valores no texto decifrado sem precisar conhecer a chave secreta;",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "b) <b>adulteração documental pós-assinatura:</b> mesmo quando um contrato é assinado por um representante "
            "legítimo, existe o risco de o arquivo sofrer modificações posteriores — seja por ação maliciosa interna, "
            "seja por interceptação — alterando, por exemplo, o valor da parcela mensal de R$ 120.833,33 para "
            "R$ 920.833,33. O mecanismo de auditoria precisa detectar alterações mínimas de um único caractere e "
            "rejeitar o documento imediatamente;",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "c) <b>falsificação de identidade criptográfica (<i>Key Spoofing via Rogue CA</i>):</b> um invasor externo "
            "pode gerar seu próprio par de chaves assimétricas, configurar uma Autoridade Certificadora própria "
            "(<i>Rogue CA</i>) e emitir um certificado digital preenchido com os mesmos dados cadastrais do fornecedor "
            "verdadeiro (<code>CN = parceiro.miguelito.com.br</code>). Se o setor responsável pela conferência verificar "
            "apenas se a assinatura digital é matematicamente válida contra a chave pública anexada ao processo — "
            "esquecendo de verificar quem emitiu aquele certificado —, o contrato fraudulento será aceito como autêntico.",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "Para responder a esse cenário, este trabalho implementa e documenta uma bancada experimental dividida em "
            "duas frentes complementares. Na <b>Parte I</b>, utiliza-se a biblioteca <code>cryptography</code> do Python "
            "para proteger o contrato com a cifra simétrica autenticada <b>AES-256-GCM</b>, testando a recuperação íntegra "
            "do arquivo e o comportamento do algoritmo frente à adulteração de bytes no criptograma e ao uso de chaves "
            "incorretas. Na <b>Parte II</b>, utiliza-se o <b>OpenSSL</b> em ambiente Linux para construir uma Infraestrutura "
            "de Chaves Públicas (PKI) completa, confrontando a Autoridade Certificadora interna da empresa "
            "(<code>Miguelito Root CA</code>) com uma autoridade atacante (<code>Rogue CA</code>) ao longo de três "
            "cenários de auditoria (Cenários A, B e C).",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 2: FUNDAMENTAÇÃO TEÓRICA
    # ==========================================================================
    story.append(Paragraph("2 FUNDAMENTAÇÃO TEÓRICA", st_h1))

    story.append(Paragraph("2.1 Criptografia Simétrica vs. Criptografia Assimétrica", st_h2))
    story.append(
        Paragraph(
            "A escolha entre algoritmos simétricos e assimétricos em uma arquitetura corporativa decorre diretamente "
            "das diferenças de desempenho, gestão de chaves e propriedades jurídicas de cada modelo. Na <b>criptografia "
            "simétrica</b>, o emissor e o destinatário compartilham exatamente a mesma chave secreta <i>K</i>, que é usada "
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
        Paragraph(
            "Por outro lado, a criptografia simétrica possui duas limitações importantes para ambientes corporativos "
            "abertos: o <b>problema da distribuição e escalabilidade de chaves</b>, visto que em uma rede com <i>n</i> "
            "empresas parceiras seriam necessárias <i>n(n-1)/2</i> chaves secretas distintas trocadas por um canal seguro "
            "prévio; e a <b>ausência de não-repúdio (irretratabilidade)</b>. Como tanto a contratante quanto a contratada "
            "possuem a mesma chave <i>K</i>, ambas têm capacidade técnica idêntica para gerar um arquivo cifrado e sua "
            "respectiva tag de verificação. Em uma disputa judicial, a Miguelito Segurança e Tecnologia não conseguiria "
            "provar a um juiz ou perito externo que determinado arquivo veio exclusivamente do fornecedor, pois a própria "
            "contratante poderia tê-lo gerado usando a chave compartilhada.",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "A <b>criptografia assimétrica (ou de chave pública)</b> contorna esses dois limites ao substituir a chave "
            "compartilhada por um par de chaves matematicamente vinculadas: uma <b>chave privada</b> (mantida em sigilo "
            "absoluto pelo seu titular) e uma <b>chave pública</b> (que pode ser divulgada abertamente a qualquer parceiro). "
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

    story.append(Paragraph("2.2 Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)", st_h2))
    story.append(
        Paragraph(
            "Durante muitos anos, sistemas corporativos utilizaram cifras de bloco em modos de operação voltados "
            "exclusivamente para confidencialidade, como o CBC (<i>Cipher Block Chaining</i>) ou o CTR (<i>Counter Mode</i>). "
            "Embora esses modos escondam o conteúdo do texto em claro contra um observador passivo, eles não oferecem "
            "proteção nativa contra um atacante ativo que modifique o texto cifrado em trânsito. No modo Contador (CTR) "
            "puro, o algoritmo recebe um valor público inicial único de 96 bits (12 bytes) chamado <b>Nonce</b> (IV), "
            "concatena a ele um contador sequencial de 32 bits (formando o bloco inicial <i>J<sub>0</sub></i>) e cifra "
            "esse contador com a chave secreta <i>K</i>. O fluxo pseudoaleatório resultante (<i>keystream</i>) é combinado "
            "com cada bloco do texto em claro <i>P<sub>i</sub></i> através da operação lógica XOR (⊕) para produzir o "
            "bloco cifrado <i>C<sub>i</sub></i>, conforme expresso na Equação (1):",
            st_corpo,
        )
    )
    story.append(
        bloco_equacao_abnt(
            "C<sub>i</sub> = P<sub>i</sub> ⊕ E<sub>K</sub>(inc<sub>32</sub><sup>i</sup>(J<sub>0</sub>)), &nbsp;&nbsp; i = 1, 2, ..., n",
            "1",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        Paragraph(
            "O perigo de usar o modo CTR isoladamente reside na sua <b>maleabilidade linear</b>: como a decifragem "
            "consiste apenas em aplicar novamente a operação XOR entre o bloco cifrado recebido e o mesmo <i>keystream</i>, "
            "se um invasor interceptar o arquivo no caminho e inverter 1 bit em uma posição conhecida do bloco cifrado "
            "<i>C<sub>i</sub></i>, o processo de decifragem não apresentará nenhum erro e inverterá exatamente o mesmo bit "
            "no texto em claro recuperado <i>P<sub>i</sub></i>. Em um contrato comercial padronizado onde a posição das "
            "cláusulas é previsível, isso permitiria alterar dígitos de valores monetários às cegas (ataque de <i>bit-flipping</i>).",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "Para eliminar essa vulnerabilidade, a norma <b>NIST SP 800-38D</b> (DWORKIN, 2007) definiu o <b>AES-GCM</b> "
            "(<i>Galois/Counter Mode</i>), um esquema <b>AEAD</b> (<i>Authenticated Encryption with Associated Data</i>) "
            "que une o modo contador ao mecanismo algébrico de autenticação <b>GHASH</b>. Antes de processar os dados, "
            "o algoritmo passa um bloco nulo de 128 bits pela cifra AES com a chave <i>K</i>, derivando a subchave secreta "
            "de autenticação <i>H = E<sub>K</sub>(0<sup>128</sup>)</i>. Em seguida, os blocos de 128 bits dos Dados "
            "Associados não cifrados (AAD) e os blocos já cifrados (<i>C<sub>1</sub>, ..., C<sub>n</sub></i>), seguidos "
            "de um bloco final com os tamanhos em bits de AAD e do texto cifrado, são tratados como coeficientes de um "
            "polinômio avaliado em <i>H</i> dentro do corpo finito de Galois GF(2<sup>128</sup>) módulo o polinômio "
            "irredutível <i>P(x) = x<sup>128</sup> + x<sup>7</sup> + x<sup>2</sup> + x + 1</i>. O resultado de 128 bits "
            "do GHASH recebe um XOR final com a cifragem do contador inicial <i>E<sub>K</sub>(J<sub>0</sub>)</i>, gerando "
            "a <b>Authentication Tag (T)</b> de 16 bytes (128 bits), descrita na Equação (2):",
            st_corpo,
        )
    )
    story.append(
        bloco_equacao_abnt(
            "T = GHASH<sub>H</sub>(AAD, Ciphertext) ⊕ E<sub>K</sub>(J<sub>0</sub>)",
            "2",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        Paragraph(
            "O diferencial de segurança do AES-GCM ocorre na decifragem, que segue estritamente a regra "
            "<b>Encrypt-then-MAC</b>: antes de liberar qualquer byte decifrado para a aplicação, a rotina recalcula a tag "
            "local <i>T'</i> sobre os blocos recebidos e a compara em tempo constante com a tag <i>T</i> anexada ao arquivo. "
            "Se um atacante alterar qualquer bloco cifrado <i>C<sub>i</sub></i> por uma máscara de erro não nula Δ "
            "(ou seja, <i>C'<sub>i</sub> = C<sub>i</sub> ⊕ Δ</i>), a diferença algébrica entre a tag recalculada e a "
            "original em GF(2<sup>128</sup>) é dada pela Equação (3):",
            st_corpo,
        )
    )
    story.append(
        bloco_equacao_abnt(
            "ΔT = T' ⊕ T = Δ · H<sup>n - i + 2</sup> &nbsp; (mod P(x))",
            "3",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        Paragraph(
            "Como GF(2<sup>128</sup>) é um corpo finito e não admite divisores de zero, o produto de dois elementos não "
            "nulos (<i>Δ ≠ 0</i> e <i>H ≠ 0</i>) jamais resulta em zero. Portanto, <i>T' ≠ T</i> obrigatoriamente, fazendo "
            "com que a biblioteca descarte o buffer de saída e lance imediatamente a exceção <code>InvalidTag</code>.",
            st_corpo,
        )
    )

    story.append(
        Paragraph("2.3 Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA", st_h2)
    )
    story.append(
        Paragraph(
            "Embora o AES-256-GCM proteja o arquivo em trânsito e em repouso entre sistemas que já compartilham uma chave, "
            "ele não substitui a assinatura jurídica de um contrato entre empresas distintas. Para garantir que a fornecedora "
            "não possa repudiar o contrato assinado, emprega-se a assinatura digital <b>RSA com SHA-256</b> segundo o "
            "paradigma <b>Hash-then-Sign</b> (MORIARTY et al., 2016). Primeiro, o documento passa pela função hash "
            "<b>SHA-256</b> (NIST, 2015), que comprime o arquivo em um resumo fixo de 256 bits (32 bytes) dotado de "
            "efeito avalanche e resistência a colisões. No esquema <b>RSASSA-PKCS1-v1_5</b> (ou de modo probabilístico "
            "no <b>RSA-PSS</b>), o hash de 32 bytes e o identificador (OID) do algoritmo SHA-256 são encapsulados em uma "
            "estrutura ASN.1 (<code>DigestInfo</code>) com preenchimento até o tamanho do módulo RSA (256 bytes para chaves "
            "de 2048 bits), formando o bloco codificado <i>EM</i>. A geração da assinatura <i>S</i> com a chave privada "
            "<i>(d, N)</i> e a sua verificação com a chave pública <i>(e, N)</i> seguem a Equação (4):",
            st_corpo,
        )
    )
    story.append(
        bloco_equacao_abnt(
            "S = EM<sup>d</sup> (mod N) &nbsp;&nbsp;&nbsp; e &nbsp;&nbsp;&nbsp; EM' = S<sup>e</sup> (mod N)",
            "4",
            st_eq,
            st_eq_num,
        )
    )
    story.append(
        Paragraph(
            "Todavia, a operação matemática da Equação (4) valida apenas que a assinatura foi produzida pelo detentor da "
            "chave privada correspondente àquela chave pública, mas não prova a quem pertence essa chave pública. Para "
            "vincular formalmente uma identidade jurídica a uma chave pública, utiliza-se a <b>Infraestrutura de Chaves "
            "Públicas (PKI)</b> e os certificados <b>X.509 v3</b> padronizados pela <b>RFC 5280</b> (COOPER et al., 2008). "
            "A organização institui uma <b>Autoridade Certificadora Raiz (Root CA)</b> — neste estudo, a "
            "<code>Miguelito Root CA</code> — cujo certificado autoassinado é instalado na <b>Trust Store</b> corporativa. "
            "A Root CA assina digitalmente o certificado do fornecedor (<code>parceiro.crt</code>), amarrando seu nome "
            "(<code>Subject: CN = parceiro.miguelito.com.br</code>) à sua chave pública e fixando extensões críticas "
            "(<code>basicConstraints: CA:FALSE</code> e <code>keyUsage: digitalSignature, nonRepudiation</code>). Dessa "
            "forma, a auditoria de um contrato assinado exige sempre duas checagens conjuntas: a verificação matemática "
            "da assinatura e a validação da cadeia X.509 até a Root CA corporativa (incluindo checagem de revogação via CRL ou OCSP).",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 3: METODOLOGIA E AMBIENTE EXPERIMENTAL
    # ==========================================================================
    story.append(Paragraph("3 METODOLOGIA E AMBIENTE EXPERIMENTAL", st_h1))
    story.append(
        Paragraph(
            "Para validar experimentalmente os controles criptográficos exigidos pela Miguelito Segurança e Tecnologia, "
            "foram construídos dois scripts automatizados em ambiente Linux (Ubuntu 24.04 LTS sob WSL2), registrando "
            "todos os eventos, resumos SHA-256 e códigos de retorno em arquivos de log. A Tabela 1 detalha a especificação "
            "do ambiente experimental.",
            st_corpo,
        )
    )

    linhas_tab1 = [
        [
            Paragraph("Componente / Ferramenta", st_tab_cab),
            Paragraph("Versão / Especificação", st_tab_cab),
            Paragraph("Finalidade nos Experimentos", st_tab_cab),
        ],
        [
            Paragraph("Sistema Operacional", st_tab_cel),
            Paragraph("Ubuntu 24.04 LTS (Kernel 6.6.87.2 WSL2)", st_tab_cel),
            Paragraph("Ambiente POSIX isolado para execução dos scripts e coleta de logs.", st_tab_cel),
        ],
        [
            Paragraph("Interpretador Python", st_tab_cel),
            Paragraph("Python 3.12.3 / 3.13.14", st_tab_cel),
            Paragraph("Execução do módulo parte1_aes_gcm.py com logging e type hints.", st_tab_cel),
        ],
        [
            Paragraph("Biblioteca Criptográfica", st_tab_cel),
            Paragraph("cryptography 41.0.7 / 50.0.2 (AESGCM)", st_tab_cel),
            Paragraph("Cifragem autenticada AES-256-GCM e captura de InvalidTag.", st_tab_cel),
        ],
        [
            Paragraph("Suíte OpenSSL CLI", st_tab_cel),
            Paragraph("OpenSSL 3.0.13 (30 Jan 2024)", st_tab_cel),
            Paragraph("Geração de chaves RSA 4096/2048-bit, emissão X.509 v3, dgst e verify.", st_tab_cel),
        ],
        [
            Paragraph("Contrato Comercial Base", st_tab_cel),
            Paragraph("contrato_miguelito.txt (2.841 bytes)", st_tab_cel),
            Paragraph("Contrato nº 2026/00849-MST (R$ 1.450.000,00 / 12x R$ 120.833,33).", st_tab_cel),
        ],
    ]
    story.append(
        criar_tabela_abnt(
            1,
            "Especificação das ferramentas e ambiente experimental da auditoria",
            linhas_tab1,
            [3.8 * cm, 5.2 * cm, 7.0 * cm],
            st_legenda,
            st_fonte,
        )
    )

    # ==========================================================================
    # SEÇÃO 4: EXPERIMENTOS DA PARTE I (AES-256-GCM)
    # ==========================================================================
    story.append(Paragraph("4 EXPERIMENTOS DA PARTE I: PROTEÇÃO E INTEGRIDADE COM AES-256-GCM", st_h1))
    story.append(Paragraph("4.1 Procedimentos de Cifragem, Empacotamento e Decifragem", st_h2))
    story.append(
        Paragraph(
            "O script <code>parte1_aes_gcm.py</code> encapsula os artefatos criptográficos na classe "
            "<code>CriptogramaGCM</code> e executa inicialmente o fluxo legítimo em três etapas. Na primeira etapa, "
            "o contrato comercial <code>contrato_miguelito.txt</code> é lido em modo binário, totalizando exatos "
            "<b>2.841 bytes</b> e apresentando o resumo SHA-256 de referência "
            "<code>9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67</code>.",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "Na segunda etapa, gera-se uma chave simétrica de 256 bits (32 bytes) via <code>AESGCM.generate_key(256)</code>, "
            "um Nonce aleatório de 96 bits (12 bytes) via <code>os.urandom(12)</code> e define-se o campo de Dados "
            "Associados (AAD) como <code>MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849</code>. O "
            "criptograma completo é persistido no arquivo <code>contrato_miguelito.enc</code> com <b>2.869 bytes</b> "
            "(12 bytes de Nonce + 2.841 bytes de Ciphertext + 16 bytes de Authentication Tag). Na terceira etapa, o "
            "script lê o arquivo <code>.enc</code> do disco, valida a Tag de 128 bits no método <code>AESGCM.decrypt()</code> "
            "e grava o texto recuperado em <code>contrato_miguelito_recuperado.txt</code>, comprovando igualdade estrita "
            "de bytes (<code>original == recuperado: True</code>) e preservação integral do hash SHA-256.",
            st_corpo,
        )
    )

    story.append(Paragraph("4.2 Logs de Execução e Análise dos Cenários de Falha", st_h2))
    story.append(
        Paragraph(
            "Concluída a validação legítima, o script submeteu o criptograma aos dois cenários de falha exigidos pela "
            "especificação: adulteração intencional de 1 byte no texto cifrado (<i>bit-flipping</i>) e tentativa de "
            "decifragem com chave simétrica incorreta. O Quadro 1 apresenta o log de execução capturado.",
            st_corpo,
        )
    )

    log_quadro1 = """[2026-11-04 15:36:36.889] [INFO] === Auditoria Criptográfica - Miguelito Segurança e Tecnologia (Parte I: AES-256-GCM) ===
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
[2026-11-04 15:36:36.911] [INFO] Motivo: A alteração no bloco cifrado mudou o resultado do polinômio GHASH em GF(2^128).
[2026-11-04 15:36:36.911] [INFO] --- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---
[2026-11-04 15:36:36.911] [INFO] Chave correta : 185c3c58dc5153a9b84ddaf0b85ec9933e52f67c44f8d150f42151a460aa8a28
[2026-11-04 15:36:36.912] [INFO] Chave errada  : 8908f8e494c7d2089963f9ca67836a1d43bfc0a0ea511d3343b5c0a40d8df58e
[2026-11-04 15:36:36.912] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag"""
    story.append(
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
        Paragraph(
            "Conforme registrado no Quadro 1, no <b>Teste de Falha 1</b> foi invertido 1 bit no byte localizado no "
            "offset 1420 (<code>0x058C</code>, alterando <code>0x4B</code> para <code>0x4A</code> via <code>XOR 0x01</code>). "
            "Durante a tentativa de decifragem com a chave correta, a avaliação do polinômio GHASH em GF(2<sup>128</sup>) "
            "resultou em uma tag divergente de <code>f987ee9b...</code>, disparando imediatamente a exceção "
            "<code>cryptography.exceptions.InvalidTag</code> sem liberar o texto em claro. De forma análoga, no "
            "<b>Teste de Falha 2</b>, a utilização da chave incorreta <code>8908f8e4...</code> produziu uma subchave "
            "de hash <i>H'</i> e uma máscara de contador distintas das originais, bloqueando a operação com "
            "<code>InvalidTag</code>. Comprovam-se, assim, as propriedades de confidencialidade, integridade e "
            "autenticidade simétrica do criptograma.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 5: EXPERIMENTOS DA PARTE II (PKI E ASSINATURAS DIGITAIS)
    # ==========================================================================
    story.append(Paragraph("5 EXPERIMENTOS DA PARTE II: ASSINATURAS DIGITAIS E CADEIA DE CERTIFICAÇÃO", st_h1))
    story.append(Paragraph("5.1 Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)", st_h2))
    story.append(
        Paragraph(
            "O script <code>parte2_pki_testes.sh</code> provisionou no diretório <code>pki_miguelito/</code> duas "
            "hierarquias de certificação X.509 v3 independentes. Na <b>Cadeia Corporativa Legítima</b>, foi gerada a "
            "autoridade raiz interna <code>Miguelito Root CA</code> com chave RSA de 4096 bits e certificado autoassinado "
            "(<code>miguelito_root_ca.crt</code>, Serial <code>362E0342...2D96</code>, <code>basicConstraints: CA:true</code>), "
            "a qual emitiu e assinou o certificado legítimo do fornecedor <code>parceiro.crt</code> "
            "(<code>CN = parceiro.miguelito.com.br</code>, RSA 2048 bits, Serial <code>21CFB1F0...BCC2</code>, "
            "<code>CA:FALSE</code>). Paralelamente, na <b>Cadeia Atacante</b>, configurou-se uma autoridade externa não "
            "confiável (<code>Rogue Root CA</code>, RSA 4096 bits) que emitiu um certificado forjado "
            "(<code>parceiro_forjado.crt</code>, Serial <code>35D9F02A...7127</code>) preenchido com o mesmo "
            "<code>CN = parceiro.miguelito.com.br</code> do fornecedor legítimo.",
            st_corpo,
        )
    )

    story.append(Paragraph("5.2 Análise do Cenário A: Documento Íntegro e Cadeia Válida", st_h2))
    story.append(
        Paragraph(
            "No Cenário A, o documento original foi assinado com a chave privada legítima do fornecedor e auditado em "
            "duas etapas: verificação matemática da assinatura contra a chave pública do certificado e validação da "
            "cadeia X.509 contra a <code>Miguelito Root CA</code>, conforme detalhado no Quadro 2.",
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
    story.append(
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
        Paragraph(
            "O resultado <code>Verified OK</code> comprova a integridade matemática do contrato após a assinatura, "
            "enquanto <code>parceiro.crt: OK</code> atesta que o certificado do signatário pertence à cadeia de confiança "
            "da <code>Miguelito Root CA</code>, justificando a decisão de <b>ACEITAR</b> o documento.",
            st_corpo,
        )
    )

    story.append(Paragraph("5.3 Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura", st_h2))
    story.append(
        Paragraph(
            "No Cenário B, simulou-se a adulteração de 1 caractere no valor da parcela mensal do contrato após a "
            "assinatura (de <code>R$ 120.833,33</code> para <code>R$ 920.833,33</code>), submetendo o documento modificado "
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
[2026-11-04 15:36:40.856] [WARN] Código de saída do OpenSSL: 1
  40C71E4E407F0000:error:02000068:rsa routines:ossl_rsa_verify:bad signature:../crypto/rsa/rsa_sign.c:430:
  Verification failure
[2026-11-04 15:36:40.868] [WARN] Resultado Cenário B -> DECISÃO: REJEITAR"""
    story.append(
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
        Paragraph(
            "Conforme demonstrado no Quadro 3, a alteração de um único dígito provocou o efeito avalanche na função "
            "SHA-256, mudando o resumo de <code>9147c039...</code> para <code>817d7fae...</code>. Como o hash extraído "
            "do bloco PKCS#1 v1.5 da assinatura não confere com o novo hash calculado, a rotina <code>ossl_rsa_verify</code> "
            "falhou com <code>bad signature / Verification failure</code> (Exit Code 1), determinando a decisão de "
            "<b>REJEITAR</b> o contrato.",
            st_corpo,
        )
    )

    story.append(Paragraph("5.4 Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável", st_h2))
    story.append(
        Paragraph(
            "No Cenário C, o documento original íntegro foi assinado com a chave privada do certificado falso "
            "(<code>parceiro_forjado.key</code>) emitido pela <code>Rogue CA</code>. O Quadro 4 apresenta o contraste "
            "entre a verificação matemática isolada e a validação da cadeia de certificação.",
            st_corpo,
        )
    )

    log_quadro4 = """# Comandos executados no Cenário C:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_forjado/parceiro_forjado.key -out cenario_c_forjado.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem -signature cenario_c_forjado.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt pki_miguelito/parceiro_forjado/parceiro_forjado.crt

# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.927] [INFO] 1) Verificação matemática com a chave pública do certificado falso: Verified OK
[2026-11-04 15:36:40.949] [WARN] 2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code 2):
  C = BR, ST = Sao Paulo, L = Sao Paulo, O = Parceiro Infraestrutura e Cloud Computing Ltda, OU = Contratos Digitais B2B, CN = parceiro.miguelito.com.br
  error 20 at 0 depth lookup: unable to get local issuer certificate
  error pki_miguelito/parceiro_forjado/parceiro_forjado.crt: verification failed
[2026-11-04 15:36:40.962] [WARN] Resultado Cenário C -> DECISÃO: REJEITAR"""
    story.append(
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
        Paragraph(
            "A análise do Quadro 4 evidencia a diferença crítica entre integridade matemática e autenticidade da origem: "
            "a primeira verificação retorna <code>Verified OK</code> porque a assinatura foi conferida contra a própria "
            "chave pública falsa que a gerou. Todavia, na segunda etapa (<code>openssl verify</code>), a validação falha "
            "no nível 0 da cadeia (<code>error 20 at 0 depth lookup: unable to get local issuer certificate</code>, "
            "Exit Code 2), pois a <code>Rogue Root CA</code> não pertence à <i>Trust Store</i> da Miguelito Segurança e "
            "Tecnologia, impondo a decisão pericial de <b>REJEITAR</b> o documento.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 6: MATRIZ DE DECISÃO E RECOMENDAÇÕES DE GOVERNANÇA
    # ==========================================================================
    story.append(Paragraph("6 MATRIZ DE DECISÃO E RECOMENDAÇÕES DE GOVERNANÇA", st_h1))
    story.append(Paragraph("6.1 Matriz Comparativa de Auditoria", st_h2))
    story.append(
        Paragraph(
            "A Tabela 2 sintetiza os resultados obtidos nos experimentos das Partes I e II, relacionando a integridade "
            "matemática do arquivo, a confiabilidade da identidade/chave e o veredito final de auditoria.",
            st_corpo,
        )
    )

    linhas_tab2 = [
        [
            Paragraph("Cenário Auditado", st_tab_cab),
            Paragraph("Integridade Matemática", st_tab_cab),
            Paragraph("Confiabilidade da Chave / CA", st_tab_cab),
            Paragraph("Evidência Técnica Capturada", st_tab_cab),
            Paragraph("Veredito", st_tab_cab),
        ],
        [
            Paragraph("Parte I – Fluxo Normal", st_tab_cel),
            Paragraph("Válida (Tag GCM e SHA-256 OK)", st_tab_cel),
            Paragraph("Válida (Chave simétrica correta)", st_tab_cel),
            Paragraph("2.841 bytes recuperados sem erro", st_tab_cel),
            Paragraph("<b>ACEITAR</b>", st_tab_cel_centro),
        ],
        [
            Paragraph("Parte I – Bit-Flipping", st_tab_cel),
            Paragraph("Inválida (GHASH diverge)", st_tab_cel),
            Paragraph("Válida (Chave simétrica correta)", st_tab_cel),
            Paragraph("cryptography.exceptions.InvalidTag", st_tab_cel),
            Paragraph("<b>REJEITAR</b>", st_tab_cel_centro),
        ],
        [
            Paragraph("Parte I – Chave Espúria", st_tab_cel),
            Paragraph("Não verificável (H' ≠ H)", st_tab_cel),
            Paragraph("Inválida (Chave não autorizada)", st_tab_cel),
            Paragraph("cryptography.exceptions.InvalidTag", st_tab_cel),
            Paragraph("<b>REJEITAR</b>", st_tab_cel_centro),
        ],
        [
            Paragraph("Parte II – Cenário A", st_tab_cel),
            Paragraph("Válida (Verified OK)", st_tab_cel),
            Paragraph("Válida (Miguelito Root CA: OK)", st_tab_cel),
            Paragraph("Exit Code 0 em dgst e verify", st_tab_cel),
            Paragraph("<b>ACEITAR</b>", st_tab_cel_centro),
        ],
        [
            Paragraph("Parte II – Cenário B", st_tab_cel),
            Paragraph("Inválida (Verification failure)", st_tab_cel),
            Paragraph("Válida (Certificado legítimo)", st_tab_cel),
            Paragraph("ossl_rsa_verify:bad signature (Exit 1)", st_tab_cel),
            Paragraph("<b>REJEITAR</b>", st_tab_cel_centro),
        ],
        [
            Paragraph("Parte II – Cenário C", st_tab_cel),
            Paragraph("Válida (Verified OK isolado)", st_tab_cel),
            Paragraph("Inválida (Fora da Trust Store)", st_tab_cel),
            Paragraph("error 20: unable to get issuer (Exit 2)", st_tab_cel),
            Paragraph("<b>REJEITAR</b>", st_tab_cel_centro),
        ],
    ]
    story.append(
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

    story.append(Paragraph("6.2 Recomendações Técnicas para a Miguelito Segurança e Tecnologia", st_h2))
    story.append(
        Paragraph(
            "Com base nos achados periciais, recomendam-se quatro medidas técnicas para a governança criptográfica da "
            "Miguelito Segurança e Tecnologia Ltda.:",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "a) <b>validação obrigatória em duas etapas e fixação da Trust Store:</b> o fluxo automatizado de recebimento "
            "de contratos deve executar obrigatoriamente a validação da cadeia X.509 (<code>openssl verify -CAfile "
            "miguelito_root_ca.crt</code>) antes de conferir a assinatura RSA, bloqueando certificados emitidos por CAs "
            "externas não homologadas;",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "b) <b>isolamento da Root CA em HSM e adoção de CA Intermediária:</b> manter a chave privada RSA de 4096 bits "
            "da <code>Miguelito Root CA</code> isolada <i>offline</i> em módulo HSM (FIPS 140-3) e instituir uma "
            "Autoridade Certificadora Intermediária para emitir os certificados operacionais dos parceiros B2B;",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "c) <b>verificação de revogação (CRL / OCSP) e restrição de uso de chave:</b> publicar Listas de Certificados "
            "Revogados (CRL) e exigir consulta OCSP (<code>-crl_check</code>) para barrar chaves privadas comprometidas "
            "antes da expiração, além de validar a presença de <code>CA:FALSE</code> e <code>keyUsage: digitalSignature, "
            "nonRepudiation</code>;",
            st_alinea,
        )
    )
    story.append(
        Paragraph(
            "d) <b>gerenciamento seguro de Nonces e rotação de chaves no AES-256-GCM:</b> garantir que cada operação de "
            "cifragem utilize um Nonce de 12 bytes exclusivo gerado via CSPRNG e rotacionar periodicamente as chaves "
            "simétricas, prevenindo ataques de reutilização de Nonce que exporiam o <i>keystream</i> e a subchave <i>H</i> do GHASH.",
            st_alinea,
        )
    )

    # ==========================================================================
    # SEÇÃO 7: CONCLUSÃO
    # ==========================================================================
    story.append(Paragraph("7 CONCLUSÃO", st_h1))
    story.append(
        Paragraph(
            "O trabalho experimental desenvolvido para o cenário da <b>Miguelito Segurança e Tecnologia Ltda.</b> "
            "permitiu demonstrar na prática como a cifragem simétrica autenticada e a infraestrutura de chaves públicas "
            "atuam de forma complementar na proteção de contratos digitais. Nos testes da Parte I, comprovou-se que o "
            "modo <b>AES-256-GCM</b> elimina a maleabilidade linear do modo contador puro por meio do polinômio "
            "<b>GHASH</b> em GF(2<sup>128</sup>), bloqueando instantaneamente tanto a adulteração de 1 bit no texto "
            "cifrado quanto a tentativa de leitura com chave espúria através da exceção <code>InvalidTag</code>.",
            st_corpo,
        )
    )
    story.append(
        Paragraph(
            "Nos experimentos da Parte II, a implementação da PKI com o OpenSSL evidenciou a fronteira entre integridade "
            "de conteúdo e autenticidade da identidade do signatário. Enquanto o Cenário B comprovou que qualquer alteração "
            "pós-assinatura em cláusulas financeiras invalida o resumo <b>SHA-256</b> (<code>Verification failure</code>), "
            "o Cenário C demonstrou que uma assinatura matematicamente válida (<code>Verified OK</code>) deve ser "
            "rejeitada quando o certificado que transporta a chave pública não possui vínculo de confiança com a "
            "<code>Miguelito Root CA</code> (<code>error 20 at 0 depth lookup: unable to get local issuer certificate</code>). "
            "Conclui-se que a combinação do transporte cifrado em AES-256-GCM com a validação estrita da cadeia X.509 "
            "assegura integralmente a confidencialidade, a integridade, a autenticidade e o não-repúdio exigidos pela auditoria.",
            st_corpo,
        )
    )

    # ==========================================================================
    # SEÇÃO 8: REFERÊNCIAS BIBLIOGRÁFICAS (NBR 6023)
    # ==========================================================================
    story.append(Paragraph("8 REFERÊNCIAS BIBLIOGRÁFICAS", st_h1))
    referencias_nbr6023 = [
        "COOPER, D.; SANTESSON, S.; FARRELL, S.; BOEYEN, S.; HOUSLEY, R.; POLK, W. <b>Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile</b>. [S. l.]: Internet Engineering Task Force (IETF), RFC 5280, maio 2008. Disponível em: &lt;https://datatracker.ietf.org/doc/html/rfc5280&gt;. Acesso em: 04 nov. 2026.",
        "DWORKIN, Morris J. <b>Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC</b>. Gaithersburg, MD: National Institute of Standards and Technology (NIST), Special Publication 800-38D, nov. 2007.",
        "MORIARTY, K.; KALISKI, B.; JONSSON, J.; RUSCH, A. <b>PKCS #1: RSA Cryptography Specifications Version 2.2</b>. [S. l.]: Internet Engineering Task Force (IETF), RFC 8017, nov. 2016. Disponível em: &lt;https://datatracker.ietf.org/doc/html/rfc8017&gt;. Acesso em: 04 nov. 2026.",
        "NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). <b>FIPS PUB 180-4: Secure Hash Standard (SHS)</b>. Gaithersburg, MD: U.S. Department of Commerce, ago. 2015.",
        "PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA). <b>Cryptography Documentation: Authenticated Encryption with Associated Data (AESGCM)</b>. [S. l.]: PyCA, 2026. Disponível em: &lt;https://cryptography.io/en/latest/hazmat/primitives/aead/&gt;. Acesso em: 04 nov. 2026.",
        "STALLINGS, William. <b>Criptografia e segurança de redes: princípios e práticas</b>. 8. ed. São Paulo: Pearson Education, 2023.",
    ]
    for ref in referencias_nbr6023:
        story.append(Paragraph(ref, st_ref))

    # Duas passagens (multiBuild) para resolver automaticamente os números de página no Sumário
    doc.multiBuild(story)
    print(f"PDF ABNT gerado com sucesso em: {caminho_saida}")


if __name__ == "__main__":
    gerar_pdf()
