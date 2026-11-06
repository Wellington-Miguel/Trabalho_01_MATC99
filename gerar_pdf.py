#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do Relatório Técnico em PDF (Padrão Universitário UFBA - MATC99)
Produz o arquivo RELATORIO_TECNICO_MATC99.pdf (6 páginas) com fontes TrueType
nativas do sistema (Arial / Consolas), sem imagens de fórmulas coladas e com
diagramação limpa de trabalho acadêmico.
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
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Remove pasta antiga de imagens de fórmulas caso exista
DIR_BASE = Path(__file__).resolve().parent
shutil.rmtree(DIR_BASE / "formulas_img", ignore_errors=True)

# Registro de fontes TrueType com suporte completo a acentuação e símbolos matemáticos Unicode
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


class CanvasRelatorioAcademico(canvas.Canvas):
    """Numeração de páginas 'Página X de Y' e cabeçalho discreto a partir da página 2."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_paginas = len(self._saved_page_states)
        print(f"Total real de paginas no PDF: {total_paginas}")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._desenhar_cabecalho_rodape(total_paginas)
            super().showPage()
        super().save()

    def _desenhar_cabecalho_rodape(self, total_paginas: int):
        self.saveState()
        self.setFont(FONT_BODY, 8.5)
        self.setFillColor(colors.HexColor("#444444"))

        # Cabeçalho e rodapé apenas a partir da página 2 (capa limpa na página 1)
        if self._pageNumber > 1:
            self.drawString(
                2.0 * cm,
                28.1 * cm,
                "UFBA — MATC99: Segurança e Auditoria de Sistemas de Informação",
            )
            self.drawRightString(
                19.0 * cm,
                28.1 * cm,
                "Trabalho 01 — Criptografia Aplicada",
            )
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(2.0 * cm, 27.9 * cm, 19.0 * cm, 27.9 * cm)

            self.line(2.0 * cm, 1.7 * cm, 19.0 * cm, 1.7 * cm)
            self.drawString(
                2.0 * cm,
                1.25 * cm,
                "Estudo de Caso: Miguelito Segurança e Tecnologia Ltda.",
            )
            self.drawRightString(
                19.0 * cm,
                1.25 * cm,
                f"Página {self._pageNumber} de {total_paginas}",
            )
        self.restoreState()


def caixa_codigo(texto: str, estilo_codigo: ParagraphStyle, largura_cm: float = 17.0) -> Table:
    """Cria um bloco de código/log com fundo cinza claro e borda discreta."""
    tabela = Table([[Preformatted(texto.strip(), estilo_codigo)]], colWidths=[largura_cm * cm])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F8FA")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return tabela


def gerar_pdf(caminho_saida: str = "RELATORIO_TECNICO_MATC99.pdf"):
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.1 * cm,
        bottomMargin=1.9 * cm,
        title="Trabalho 01 - Criptografia Aplicada (MATC99 - UFBA)",
        author="Wellington Miguel de Jesus Silva",
    )

    styles = getSampleStyleSheet()
    cor_titulo = colors.HexColor("#111827")
    cor_subtitulo = colors.HexColor("#1F2937")
    cor_texto = colors.HexColor("#111111")

    # Estilos da Capa
    capa_inst = ParagraphStyle(
        "CapaInst",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=17,
        alignment=TA_CENTER,
        textColor=cor_titulo,
    )
    capa_disc = ParagraphStyle(
        "CapaDisc",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=cor_subtitulo,
    )
    capa_titulo = ParagraphStyle(
        "CapaTitulo",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        textColor=cor_titulo,
        spaceAfter=10,
    )
    capa_sub = ParagraphStyle(
        "CapaSub",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=11.5,
        leading=16,
        alignment=TA_CENTER,
        textColor=cor_subtitulo,
    )
    capa_meta = ParagraphStyle(
        "CapaMeta",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=10.5,
        leading=16,
        alignment=TA_LEFT,
        textColor=cor_texto,
    )

    # Estilos do Documento
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=15,
        textColor=cor_titulo,
        spaceBefore=9.5,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13.5,
        textColor=cor_subtitulo,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Corpo",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.1,
        leading=12.6,
        alignment=TA_JUSTIFY,
        textColor=cor_texto,
        spaceAfter=4.0,
    )
    bullet_style = ParagraphStyle(
        "ItemLista",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=3.0,
    )
    eq_style = ParagraphStyle(
        "Equacao",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=cor_titulo,
        spaceBefore=4,
        spaceAfter=6,
    )
    code_style = ParagraphStyle(
        "Codigo",
        parent=styles["Normal"],
        fontName=FONT_MONO,
        fontSize=7.4,
        leading=10.0,
        textColor=colors.HexColor("#111827"),
    )
    tab_header = ParagraphStyle(
        "TabHeader",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8.8,
        leading=11.5,
        textColor=cor_titulo,
    )
    tab_cell = ParagraphStyle(
        "TabCell",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=8.5,
        leading=11.5,
        textColor=cor_texto,
    )
    tab_cell_center = ParagraphStyle(
        "TabCellCenter",
        parent=tab_cell,
        alignment=TA_CENTER,
    )
    sumario_item = ParagraphStyle(
        "SumarioItem",
        parent=styles["Normal"],
        fontName=FONT_BODY,
        fontSize=9.2,
        leading=13.0,
        textColor=cor_texto,
    )

    story = []

    # ==========================================================================
    # PÁGINA 1: CAPA ACADÊMICA E SUMÁRIO
    # ==========================================================================
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("UNIVERSIDADE FEDERAL DA BAHIA", capa_inst))
    story.append(Paragraph("INSTITUTO DE COMPUTAÇÃO", capa_inst))
    story.append(Paragraph("DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO", capa_disc))
    story.append(Spacer(1, 0.7 * cm))

    story.append(
        Paragraph(
            "TRABALHO 01 — CRIPTOGRAFIA APLICADA:<br/>PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS",
            capa_titulo,
        )
    )
    story.append(
        Paragraph(
            "Estudo de Caso: Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.",
            capa_sub,
        )
    )
    story.append(Spacer(1, 0.7 * cm))

    # Bloco de metadados alinhado à direita (padrão universitário brasileiro)
    bloco_meta = Table(
        [
            [
                "",
                Paragraph(
                    "Relatório Técnico apresentado à disciplina <b>MATC99 — Segurança e Auditoria "
                    "de Sistemas de Informação</b> do Instituto de Computação da Universidade Federal "
                    "da Bahia (UFBA), como requisito parcial de avaliação prática.<br/><br/>"
                    "<b>Aluno:</b> Wellington Miguel de Jesus Silva<br/>"
                    "<b>Empresa Auditada (Cenário):</b> Miguelito Segurança e Tecnologia Ltda.",
                    capa_meta,
                ),
            ]
        ],
        colWidths=[5.5 * cm, 11.5 * cm],
    )
    bloco_meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (1, 0), (1, 0), 10),
                ("LINEBEFORE", (1, 0), (1, 0), 1.0, colors.HexColor("#9CA3AF")),
            ]
        )
    )
    story.append(bloco_meta)
    story.append(Spacer(1, 0.6 * cm))

    # Sumário Executivo na metade inferior da página 1
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#D1D5DB"), spaceAfter=4))
    story.append(Paragraph("SUMÁRIO", h1_style))
    itens_sumario = [
        "<b>1. Introdução e Contextualização do Problema</b>",
        "<b>2. Fundamentação Teórica</b>",
        "&nbsp;&nbsp;&nbsp;&nbsp;2.1. Criptografia Simétrica vs. Criptografia Assimétrica",
        "&nbsp;&nbsp;&nbsp;&nbsp;2.2. Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)",
        "&nbsp;&nbsp;&nbsp;&nbsp;2.3. Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA",
        "<b>3. Metodologia e Ambiente Experimental</b>",
        "<b>4. Experimentos da Parte I: Proteção e Integridade com AES-256-GCM</b>",
        "<b>5. Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação</b>",
        "<b>6. Matriz de Decisão e Recomendações de Governança</b>",
        "<b>7. Conclusão</b>",
        "<b>8. Referências Bibliográficas</b>",
    ]
    for item in itens_sumario:
        story.append(Paragraph(item, sumario_item))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Salvador — BA | Novembro de 2026", capa_disc))
    story.append(PageBreak())

    # ==========================================================================
    # SEÇÃO 1: INTRODUÇÃO E CONTEXTUALIZAÇÃO DO PROBLEMA
    # ==========================================================================
    story.append(Paragraph("1. Introdução e Contextualização do Problema", h1_style))
    story.append(
        Paragraph(
            "A digitalização de processos de contratação entre empresas (B2B) substituiu o papel físico "
            "e o reconhecimento de firma em cartório por fluxos eletrônicos baseados em rede. Embora essa "
            "transição reduza custos operacionais e acelere o fechamento de negócios, ela transfere toda a "
            "responsabilidade jurídica e financeira da transação para os controles criptográficos adotados "
            "pelas partes. Quando esses controles são mal projetados ou validados apenas de forma parcial, "
            "a organização fica exposta a fraudes financeiras e à perda de validade jurídica dos seus contratos.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Neste trabalho, analisamos o cenário da empresa fictícia <b>Miguelito Segurança e Tecnologia Ltda.</b> "
            "(CNPJ 14.382.910/0001-55), sediada em Salvador/BA, que atua na operação de sistemas críticos e contrata "
            "serviços de nuvem híbrida, links redundantes MPLS/IPSec e custódia de módulos HSM junto a fornecedores "
            "externos. Durante uma revisão de auditoria sobre a tramitação do <b>Contrato Comercial nº 2026/00849-MST</b>, "
            "celebrado com a fornecedora <i>Parceiro Infraestrutura e Cloud Computing Ltda.</i> "
            "(<code>parceiro.miguelito.com.br</code>, CNPJ 67.419.002/0001-83) no valor global de R$ 1.450.000,00 "
            "(dividido em 12 parcelas mensais de R$ 120.833,33), surgiram indícios de duas falhas graves no processo "
            "de troca e validação dos arquivos digitais: a suspeita de manipulação de cláusulas financeiras durante o "
            "trânsito do documento e o recebimento de contratos assinados com certificados digitais não reconhecidos "
            "pela governança interna.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Do ponto de vista de segurança da informação e perícia forense, o incidente enfrentado pela Miguelito "
            "Segurança e Tecnologia envolve três riscos práticos distintos que precisam ser isolados e tratados:",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>1. Interceptação e Modificação em Trânsito (<i>Man-in-the-Middle / Bit-Flipping</i>):</b> Contratos "
            "comerciais contêm dados bancários, valores de SLA, multas contratuais e especificações técnicas que não "
            "podem vazar para terceiros em trânsito (quebra de confidencialidade). Além disso, caso a empresa utilize "
            "um algoritmo de cifragem tradicional sem autenticação integrada, um atacante posicionado na rede pode "
            "alterar bytes específicos do texto cifrado para modificar valores no texto decifrado sem precisar conhecer a chave secreta.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>2. Adulteração Documental Pós-Assinatura:</b> Mesmo quando um contrato é assinado por um representante "
            "legítimo, existe o risco de o arquivo sofrer modificações posteriores — seja por ação maliciosa interna, "
            "seja por interceptação — alterando, por exemplo, o valor da parcela mensal de R$ 120.833,33 para "
            "R$ 920.833,33. O mecanismo de auditoria precisa detectar alterações mínimas de um único caractere e "
            "rejeitar o documento imediatamente.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>3. Falsificação de Identidade Criptográfica (<i>Key Spoofing via Rogue CA</i>):</b> Um invasor externo "
            "pode gerar seu próprio par de chaves assimétricas, configurar uma Autoridade Certificadora própria "
            "(<i>Rogue CA</i>) e emitir um certificado digital preenchido com os mesmos dados cadastrais do fornecedor "
            "verdadeiro (<code>CN = parceiro.miguelito.com.br</code>). Se o setor responsável pela conferência verificar "
            "apenas se a assinatura digital é matematicamente válida contra a chave pública anexada ao processo — "
            "esquecendo de verificar quem emitiu aquele certificado —, o contrato fraudulento será aceito como autêntico.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "Para responder a esse cenário, este trabalho implementa e documenta uma bancada experimental dividida em "
            "duas frentes complementares: na <b>Parte I</b>, utilizamos a biblioteca <code>cryptography</code> do Python "
            "para proteger o contrato com a cifra simétrica autenticada <b>AES-256-GCM</b>; na <b>Parte II</b>, utilizamos "
            "o <b>OpenSSL</b> em ambiente Linux para construir uma Infraestrutura de Chaves Públicas (PKI) completa, "
            "confrontando a Autoridade Certificadora interna da empresa (<code>Miguelito Root CA</code>) com uma "
            "autoridade atacante (<code>Rogue CA</code>) ao longo de três cenários de auditoria (Cenários A, B e C).",
            body_style,
        )
    )

    # ==========================================================================
    # SEÇÃO 2: FUNDAMENTAÇÃO TEÓRICA
    # ==========================================================================
    story.append(Paragraph("2. Fundamentação Teórica", h1_style))

    story.append(Paragraph("2.1. Criptografia Simétrica vs. Criptografia Assimétrica", h2_style))
    story.append(
        Paragraph(
            "A escolha entre algoritmos simétricos e assimétricos em uma arquitetura corporativa decorre diretamente "
            "das diferenças de desempenho, gestão de chaves e propriedades jurídicas de cada modelo. Na <b>criptografia "
            "simétrica</b>, o emissor e o destinatário compartilham exatamente a mesma chave secreta <i>K</i>, usada "
            "tanto para cifrar quanto para decifrar os dados. Algoritmos simétricos modernos, como o AES "
            "(<i>Advanced Encryption Standard</i>), operam sobre blocos de bits por meio de rodadas sucessivas de "
            "substituição, permutação e combinação linear com subchaves derivadas. Por serem operações leves e contarem "
            "com instruções dedicadas diretamente no hardware dos processadores atuais (<i>AES-NI</i>), as cifras "
            "simétricas atingem altíssimo desempenho, sendo a escolha ideal para cifrar arquivos extensos e tráfego de rede.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Por outro lado, a criptografia simétrica possui duas limitações estruturais para ambientes de negócios abertos: "
            "(i) o <b>problema da distribuição de chaves</b>, pois exige um canal seguro prévio para combinar a chave <i>K</i> "
            "entre cada par de empresas (em uma rede com <i>n</i> participantes, seriam necessárias <i>n(n-1)/2</i> chaves "
            "distintas); e (ii) a <b>ausência de não-repúdio (irretratabilidade)</b>. Como tanto a contratante quanto a "
            "contratada possuem a mesma chave secreta <i>K</i>, ambas têm capacidade técnica idêntica para gerar um arquivo "
            "cifrado e sua tag de verificação. Em uma disputa judicial, a Miguelito não conseguiria provar a um perito externo "
            "que determinado arquivo veio exclusivamente do fornecedor, pois a própria Miguelito poderia tê-lo produzido.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "A <b>criptografia assimétrica (ou de chave pública)</b> resolve esses dois limites ao substituir a chave "
            "compartilhada por um par de chaves matematicamente vinculadas: uma <b>chave privada</b> (mantida sob custódia "
            "exclusiva do titular) e uma <b>chave pública</b> (divulgada abertamente). Sua segurança baseia-se em problemas "
            "matemáticos difíceis de inverter sem o segredo privado, como a fatoração do produto de dois números primos "
            "grandes no algoritmo RSA. Embora seja computacionalmente mais pesada que a simétrica, a criptografia de chave "
            "pública viabiliza as <b>assinaturas digitais</b>: o titular assina o resumo do documento com sua chave privada "
            "e qualquer auditor verifica a assinatura com a chave pública. Como apenas o titular possui a chave privada, "
            "ele não pode negar a autoria posteriormente, garantindo o não-repúdio jurídico.",
            body_style,
        )
    )

    story.append(Paragraph("2.2. Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)", h2_style))
    story.append(
        Paragraph(
            "Durante muitos anos, sistemas corporativos utilizaram cifras de bloco em modos de operação voltados apenas "
            "para confidencialidade, como o CBC (<i>Cipher Block Chaining</i>) ou o CTR (<i>Counter Mode</i>). Embora esses "
            "modos escondam o conteúdo contra observadores passivos, eles não protegem a integridade contra atacantes ativos. "
            "No modo Contador (CTR) puro, por exemplo, o algoritmo recebe um valor único de 96 bits (12 bytes) chamado "
            "<b>Nonce</b> (IV), concatena um contador sequencial de 32 bits (bloco inicial <i>J<sub>0</sub></i>) e cifra esse "
            "contador com a chave <i>K</i> para gerar um fluxo pseudoaleatório (<i>keystream</i>), que é combinado via operação "
            "lógica <b>XOR</b> com cada bloco de texto em claro <i>P<sub>i</sub></i> para gerar o bloco cifrado <i>C<sub>i</sub></i>.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "O risco de usar o modo CTR sozinho está na sua <b>maleabilidade linear</b>: como decifrar consiste apenas em "
            "aplicar novamente o XOR entre o texto cifrado e o mesmo <i>keystream</i>, se um invasor interceptar o arquivo "
            "e inverter 1 bit em uma posição conhecida do bloco cifrado <i>C<sub>i</sub></i>, a decifragem ocorrerá sem erro "
            "algum e inverterá exatamente o mesmo bit no texto recuperado <i>P<sub>i</sub></i> (ataque de <i>bit-flipping</i>). "
            "Para resolver isso de forma nativa, o padrão <b>NIST SP 800-38D</b> especificou o <b>AES-GCM</b> "
            "(<i>Galois/Counter Mode</i>), um esquema <b>AEAD</b> (<i>Authenticated Encryption with Associated Data</i>) "
            "que acopla o modo contador à função de autenticação algébrica <b>GHASH</b>:",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>1. Subchave de Autenticação e Dados Associados (AAD):</b> Cifra-se um bloco nulo de 128 bits com a chave "
            "<i>K</i> para derivar a subchave interna <i>H = E<sub>K</sub>(0<sup>128</sup>)</i>. Além do texto cifrado, o GCM "
            "permite autenticar metadados em texto claro (como identificação do contrato), chamados de AAD.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>2. Polinômio GHASH em GF(2<sup>128</sup>) e Authentication Tag:</b> Os blocos de 128 bits do AAD e os blocos "
            "já cifrados (<i>C<sub>1</sub>, ..., C<sub>n</sub></i>) entram como coeficientes de um polinômio avaliado no ponto "
            "secreto <i>H</i> dentro do corpo finito de Galois GF(2<sup>128</sup>), definido pelo polinômio irredutível "
            "<i>P(x) = x<sup>128</sup> + x<sup>7</sup> + x<sup>2</sup> + x + 1</i>. O resultado do GHASH sofre um XOR com o "
            "contador inicial cifrado <i>E<sub>K</sub>(J<sub>0</sub>)</i>, formando a <b>Authentication Tag (T)</b> de 16 bytes (128 bits):",
            bullet_style,
        )
    )
    story.append(Paragraph("T = GHASH<sub>H</sub>(AAD, Ciphertext) ⊕ E<sub>K</sub>(J<sub>0</sub>)", eq_style))
    story.append(
        Paragraph(
            "Na decifragem (arquitetura <i>Encrypt-then-MAC</i>), o destinatário recalcula a tag local <i>T'</i> a partir do "
            "Nonce, AAD e Ciphertext recebidos antes de liberar qualquer dado. Se um atacante alterar um byte do bloco "
            "<i>C<sub>i</sub></i> por uma diferença não nula Δ, a diferença entre a tag recalculada e a original em "
            "GF(2<sup>128</sup>) será <i>ΔT = Δ · H<sup>n-i+2</sup> (mod P(x))</i>. Como um corpo finito não possui divisores "
            "de zero, o produto de dois elementos não nulos nunca é zero (<i>T' ≠ T</i>). O algoritmo detecta a divergência "
            "com certeza matemática e aborta a operação lançando a exceção <code>InvalidTag</code>.",
            body_style,
        )
    )

    story.append(
        Paragraph("2.3. Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA", h2_style)
    )
    story.append(
        Paragraph(
            "Para garantir autenticidade de origem e não-repúdio jurídico entre empresas distintas, utiliza-se a assinatura "
            "digital <b>RSA com SHA-256 (RFC 8017 — PKCS#1)</b> no esquema <i>Hash-then-Sign</i>. Primeiro, o documento passa "
            "pela função hash <b>SHA-256</b>, que gera um resumo único de 32 bytes (256 bits) dotado de forte <b>efeito "
            "avalanche</b> (qualquer alteração mínima no texto muda cerca de 50% dos bits do hash) e resistência a colisões. "
            "No padrão <b>PKCS#1 v1.5</b> (ou de forma probabilística com salt no padrão <b>RSA-PSS</b>), esse resumo e o "
            "identificador do algoritmo SHA-256 são estruturados em um bloco ASN.1 preenchido até o tamanho da chave "
            "(256 bytes para RSA 2048 bits), chamado de <i>EM</i>. O signatário aplica sua chave privada <i>(d, N)</i> por "
            "exponenciação modular (<i>S = EM<sup>d</sup> mod N</i>) para gerar a assinatura; quem verifica aplica a chave "
            "pública <i>(e, N)</i> sobre a assinatura (<i>EM' = S<sup>e</sup> mod N</i>) e compara o hash extraído com o hash do arquivo.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Entretanto, a verificação matemática isolada prova apenas que o documento foi assinado pelo par daquela chave "
            "pública, mas não informa a quem essa chave pertence no mundo real. É a <b>Infraestrutura de Chaves Públicas "
            "(PKI / X.509 v3 — RFC 5280)</b> que resolve esse problema: uma <b>Autoridade Certificadora Raiz (Root CA)</b> "
            "confiável — no nosso estudo, a <code>Miguelito Root CA</code>, instalada na <i>Trust Store</i> da empresa — "
            "verifica a identidade do fornecedor e assina digitalmente o seu certificado X.509 (<code>parceiro.crt</code>), "
            "amarrando o nome do titular (<code>Subject: CN = parceiro.miguelito.com.br</code>) à sua chave pública e fixando "
            "restrições de uso (<code>basicConstraints: CA:FALSE</code> e <code>keyUsage: digitalSignature, nonRepudiation</code>). "
            "Assim, uma auditoria completa exige sempre duas etapas: validar matematicamente a assinatura do documento e "
            "validar a cadeia do certificado até a Root CA corporativa, consultando ainda sua não-revogação (via CRL ou OCSP).",
            body_style,
        )
    )

    # ==========================================================================
    # SEÇÃO 3: METODOLOGIA E AMBIENTE EXPERIMENTAL
    # ==========================================================================
    story.append(Paragraph("3. Metodologia e Ambiente Experimental", h1_style))
    story.append(
        Paragraph(
            "Os experimentos foram conduzidos em ambiente Linux (Ubuntu 24.04 LTS sob WSL2), utilizando scripts "
            "idempotentes em Python e GNU Bash para assegurar total reprodutibilidade e registro forense dos resultados. "
            "A Tabela 1 apresenta a especificação das ferramentas empregadas.",
            body_style,
        )
    )

    dados_amb = [
        [
            Paragraph("Componente / Ferramenta", tab_header),
            Paragraph("Versão / Especificação", tab_header),
            Paragraph("Finalidade nos Experimentos", tab_header),
        ],
        [
            Paragraph("Sistema Operacional", tab_cell),
            Paragraph("Ubuntu 24.04 LTS (Kernel 6.6.87.2 WSL2)", tab_cell),
            Paragraph("Ambiente POSIX isolado para execução dos scripts e coleta de logs.", tab_cell),
        ],
        [
            Paragraph("Interpretador Python", tab_cell),
            Paragraph("Python 3.12.3 / 3.13.14", tab_cell),
            Paragraph("Execução do módulo parte1_aes_gcm.py com logging e type hints.", tab_cell),
        ],
        [
            Paragraph("Biblioteca Criptográfica", tab_cell),
            Paragraph("cryptography 41.0.7 / 50.0.2 (AESGCM)", tab_cell),
            Paragraph("Cifragem autenticada AES-256-GCM e captura de InvalidTag.", tab_cell),
        ],
        [
            Paragraph("Suíte OpenSSL CLI", tab_cell),
            Paragraph("OpenSSL 3.0.13 (30 Jan 2024)", tab_cell),
            Paragraph("Geração de chaves RSA 4096/2048-bit, emissão X.509 v3, dgst e verify.", tab_cell),
        ],
        [
            Paragraph("Contrato Comercial Base", tab_cell),
            Paragraph("contrato_miguelito.txt (2.841 bytes)", tab_cell),
            Paragraph("Contrato nº 2026/00849-MST (R$ 1.450.000,00 / 12x R$ 120.833,33).", tab_cell),
        ],
    ]
    tabela_amb = Table(dados_amb, colWidths=[3.8 * cm, 5.4 * cm, 7.8 * cm])
    tabela_amb.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(tabela_amb)
    story.append(Spacer(1, 6))

    # ==========================================================================
    # SEÇÃO 4: EXPERIMENTOS DA PARTE I (AES-256-GCM)
    # ==========================================================================
    story.append(Paragraph("4. Experimentos da Parte I: Proteção e Integridade com AES-256-GCM", h1_style))
    story.append(Paragraph("4.1. Procedimentos de Cifragem, Empacotamento e Decifragem", h2_style))
    story.append(
        Paragraph(
            "O script <code>parte1_aes_gcm.py</code> inicia carregando o arquivo <code>contrato_miguelito.txt</code> "
            "(2.841 bytes) e registrando seu hash SHA-256 original (<code>9147c03987856361...ffe0cfe67</code>). Em seguida, "
            "gera uma chave simétrica aleatória de 256 bits (32 bytes) via <code>AESGCM.generate_key(256)</code>, um Nonce "
            "de 96 bits (12 bytes) via <code>os.urandom(12)</code> e define os Dados Associados (AAD) como "
            "<code>MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849</code>. O arquivo resultante "
            "<code>contrato_miguelito.enc</code> é gravado em disco com exatos <b>2.869 bytes</b>, estruturados na forma: "
            "<b>Nonce (12B) || Ciphertext (2.841B) || Authentication Tag (16B)</b>. Na sequência, o script lê o arquivo "
            "do disco, valida a Tag de 128 bits e recupera <code>contrato_miguelito_recuperado.txt</code>, confirmando "
            "igualdade estrita byte a byte (<code>original == recuperado: True</code>) e mesmo resumo SHA-256.",
            body_style,
        )
    )

    story.append(Paragraph("4.2. Logs de Execução e Análise dos Cenários de Falha", h2_style))
    story.append(
        Paragraph(
            "Após validar a decifragem legítima, o script executou os dois cenários de falha exigidos. O quadro abaixo "
            "reproduz o log real capturado em <code>parte1_aes_gcm.log</code>:",
            body_style,
        )
    )

    log_p1 = """[2026-11-04 15:36:36.889] [INFO] === Auditoria Criptográfica - Miguelito Segurança e Tecnologia (Parte I: AES-256-GCM) ===
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
    story.append(caixa_codigo(log_p1, code_style))
    story.append(Spacer(1, 5))

    story.append(
        Paragraph(
            "No <b>Teste de Falha 1 (Bit-Flipping)</b>, invertemos apenas 1 bit no byte central do texto cifrado "
            "(offset 1420 / <code>0x058C</code>, mudando <code>0x4B</code> para <code>0x4A</code> via <code>XOR 0x01</code>). "
            "Mesmo com a chave correta, o polinômio GHASH em GF(2<sup>128</sup>) produziu uma tag divergente de "
            "<code>f987ee9b...</code>, lançando <code>cryptography.exceptions.InvalidTag</code> e bloqueando a saída. "
            "No <b>Teste de Falha 2 (Chave Espúria)</b>, a tentativa de decifrar o arquivo íntegro com a chave incorreta "
            "<code>8908f8e4...</code> alterou completamente a subchave <i>H'</i> e a máscara do contador inicial, "
            "resultando novamente no bloqueio imediato via <code>InvalidTag</code>. Ficam assim comprovadas as propriedades "
            "de <b>confidencialidade</b>, <b>integridade do criptograma</b> e <b>autenticidade simétrica</b>.",
            body_style,
        )
    )

    # ==========================================================================
    # SEÇÃO 5: EXPERIMENTOS DA PARTE II (PKI E ASSINATURAS DIGITAIS)
    # ==========================================================================
    story.append(Paragraph("5. Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação", h1_style))
    story.append(Paragraph("5.1. Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)", h2_style))
    story.append(
        Paragraph(
            "O script <code>parte2_pki_testes.sh</code> estruturou o diretório <code>pki_miguelito/</code> com duas "
            "hierarquias X.509 v3 distintas: (1) a <b>Cadeia Corporativa Legítima</b>, encabeçada pela autoridade raiz "
            "interna <code>Miguelito Root CA</code> (RSA 4096 bits, autoassinado, Serial <code>362E0342...2D96</code>, "
            "<code>CA:true</code>), que assinou o certificado legítimo do fornecedor <code>parceiro.crt</code> "
            "(<code>CN = parceiro.miguelito.com.br</code>, RSA 2048 bits, Serial <code>21CFB1F0...BCC2</code>, "
            "<code>CA:FALSE</code>); e (2) a <b>Cadeia Atacante (Rogue CA)</b>, composta por uma autoridade externa não "
            "confiável (<code>Rogue Root CA</code>, RSA 4096 bits) que emitiu o certificado falso "
            "<code>parceiro_forjado.crt</code> copiando o mesmo <code>CN = parceiro.miguelito.com.br</code> do fornecedor.",
            body_style,
        )
    )

    story.append(Paragraph("5.2. Análise do Cenário A: Documento Íntegro e Cadeia Válida", h2_style))
    story.append(
        Paragraph(
            "No Cenário A, o contrato original foi assinado com a chave privada legítima do fornecedor e submetido à "
            "verificação matemática da assinatura e à validação da cadeia contra a <code>Miguelito Root CA</code>:",
            body_style,
        )
    )
    bloco_a = """# Comandos executados no Cenário A:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_legitimo/parceiro.key -out cenario_a.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem -signature cenario_a.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt pki_miguelito/parceiro_legitimo/parceiro.crt

# Saída capturada em parte2_pki_testes.log:
[2026-11-04 15:36:40.697] [INFO] Assinatura gerada: cenario_a.sig (256 bytes)
[2026-11-04 15:36:40.721] [INFO] Verificação da assinatura (openssl dgst -verify): Verified OK
[2026-11-04 15:36:40.743] [INFO] Validação da cadeia contra Miguelito Root CA: pki_miguelito/parceiro_legitimo/parceiro.crt: OK
[2026-11-04 15:36:40.750] [INFO] Resultado Cenário A -> DECISÃO: ACEITAR"""
    story.append(caixa_codigo(bloco_a, code_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Análise e Justificativa (DECISÃO: ACEITAR):</b> O retorno <code>Verified OK</code> comprova que o hash "
            "SHA-256 recuperado da assinatura <code>cenario_a.sig</code> (256 bytes) coincide exatamente com o hash de "
            "<code>contrato_miguelito.txt</code>. Simultaneamente, <code>parceiro.crt: OK</code> confirma que o certificado "
            "do signatário foi emitido pela <code>Miguelito Root CA</code>. Estão atendidos os critérios de integridade, "
            "autenticidade de identidade e não-repúdio.",
            body_style,
        )
    )

    story.append(Paragraph("5.3. Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura", h2_style))
    story.append(
        Paragraph(
            "No Cenário B, simulou-se uma fraude financeira alterando 1 byte no contrato após a assinatura (mudança da "
            "parcela mensal de <code>R$ 120.833,33</code> para <code>R$ 920.833,33</code> via <code>sed</code>), "
            "verificando-o em seguida contra a assinatura legítima colhida no Cenário A:",
            body_style,
        )
    )
    bloco_b = """# Comandos executados no Cenário B:
$ sed 's/R\\$ 120\\.833,33/R\\$ 920.833,33/g' contrato_miguelito.txt > contrato_adulterado.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem -signature cenario_a.sig contrato_adulterado.txt

# Saída capturada em parte2_pki_testes.log:
[2026-11-04 15:36:40.824] [INFO] SHA-256 original   : 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:40.832] [INFO] SHA-256 adulterado : 817d7fae7346f151320d2469a8546c52edefa478219948e1efbb75edf9f0a8d2
[2026-11-04 15:36:40.856] [WARN] Código de saída do OpenSSL: 1
  40C71E4E407F0000:error:02000068:rsa routines:ossl_rsa_verify:bad signature:../crypto/rsa/rsa_sign.c:430:
  Verification failure
[2026-11-04 15:36:40.868] [WARN] Resultado Cenário B -> DECISÃO: REJEITAR"""
    story.append(caixa_codigo(bloco_b, code_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Análise e Justificativa (DECISÃO: REJEITAR):</b> A troca do dígito '1' por '9' acionou o efeito avalanche "
            "do SHA-256, alterando completamente o resumo de 256 bits (de <code>9147c039...</code> para "
            "<code>817d7fae...</code>). Ao abrir o bloco PKCS#1 v1.5 da assinatura com a chave pública legítima, a rotina "
            "<code>ossl_rsa_verify</code> constatou a divergência entre o hash assinado e o hash do arquivo modificado, "
            "retornando <code>bad signature / Verification failure</code> (Exit Code 1).",
            body_style,
        )
    )

    story.append(Paragraph("5.4. Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável", h2_style))
    story.append(
        Paragraph(
            "No Cenário C, o contrato original íntegro foi assinado com a chave privada falsa "
            "(<code>parceiro_forjado.key</code>) vinculada ao certificado emitido pela <code>Rogue CA</code>:",
            body_style,
        )
    )
    bloco_c = """# Comandos executados no Cenário C:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_forjado/parceiro_forjado.key -out cenario_c_forjado.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem -signature cenario_c_forjado.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt pki_miguelito/parceiro_forjado/parceiro_forjado.crt

# Saída capturada em parte2_pki_testes.log:
[2026-11-04 15:36:40.927] [INFO] 1) Verificação matemática com a chave pública do certificado falso: Verified OK
[2026-11-04 15:36:40.949] [WARN] 2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code 2):
  C = BR, ST = Sao Paulo, L = Sao Paulo, O = Parceiro Infraestrutura e Cloud Computing Ltda, OU = Contratos Digitais B2B, CN = parceiro.miguelito.com.br
  error 20 at 0 depth lookup: unable to get local issuer certificate
  error pki_miguelito/parceiro_forjado/parceiro_forjado.crt: verification failed
[2026-11-04 15:36:40.962] [WARN] Resultado Cenário C -> DECISÃO: REJEITAR"""
    story.append(caixa_codigo(bloco_c, code_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Diferenciação entre Integridade e Autenticidade (DECISÃO: REJEITAR):</b> Embora a verificação matemática "
            "isolada retorne <code>Verified OK</code> (pois o documento está íntegro em relação ao par de chaves gerado "
            "pelo próprio atacante), a validação de cadeia falha imediatamente no nível 0 (<code>at 0 depth lookup</code>) "
            "com o erro <code>error 20: unable to get local issuer certificate</code>. Isso ocorre porque o emissor do "
            "certificado (<code>Rogue Root CA</code>) não consta na <i>Trust Store</i> da Miguelito Segurança e Tecnologia, "
            "caracterizando tentativa de falsificação ideológica (<i>spoofing</i> de certificado).",
            body_style,
        )
    )

    # ==========================================================================
    # SEÇÃO 6: MATRIZ DE DECISÃO E RECOMENDAÇÕES DE GOVERNANÇA
    # ==========================================================================
    story.append(Paragraph("6. Matriz de Decisão e Recomendações de Governança", h1_style))
    story.append(Paragraph("6.1. Matriz Comparativa de Auditoria", h2_style))

    dados_matriz = [
        [
            Paragraph("Cenário Auditado", tab_header),
            Paragraph("Integridade Matemática", tab_header),
            Paragraph("Confiabilidade da Identidade / Chave", tab_header),
            Paragraph("Evidência Técnica Capturada", tab_header),
            Paragraph("Veredito", tab_header),
        ],
        [
            Paragraph("Parte I — Fluxo Normal", tab_cell),
            Paragraph("Válida (Tag GCM e SHA-256 OK)", tab_cell),
            Paragraph("Válida (Chave simétrica correta)", tab_cell),
            Paragraph("2.841 bytes recuperados sem erro", tab_cell),
            Paragraph("<b>ACEITAR</b>", tab_cell_center),
        ],
        [
            Paragraph("Parte I — Bit-Flipping", tab_cell),
            Paragraph("Inválida (GHASH diverge)", tab_cell),
            Paragraph("Válida (Chave simétrica correta)", tab_cell),
            Paragraph("cryptography.exceptions.InvalidTag", tab_cell),
            Paragraph("<b>REJEITAR</b>", tab_cell_center),
        ],
        [
            Paragraph("Parte I — Chave Espúria", tab_cell),
            Paragraph("Não verificável (H' ≠ H)", tab_cell),
            Paragraph("Inválida (Chave não autorizada)", tab_cell),
            Paragraph("cryptography.exceptions.InvalidTag", tab_cell),
            Paragraph("<b>REJEITAR</b>", tab_cell_center),
        ],
        [
            Paragraph("Parte II — Cenário A", tab_cell),
            Paragraph("Válida (Verified OK)", tab_cell),
            Paragraph("Válida (Miguelito Root CA: OK)", tab_cell),
            Paragraph("Exit Code 0 em dgst e verify", tab_cell),
            Paragraph("<b>ACEITAR</b>", tab_cell_center),
        ],
        [
            Paragraph("Parte II — Cenário B", tab_cell),
            Paragraph("Inválida (Verification failure)", tab_cell),
            Paragraph("Válida (Certificado legítimo)", tab_cell),
            Paragraph("ossl_rsa_verify:bad signature (Exit 1)", tab_cell),
            Paragraph("<b>REJEITAR</b>", tab_cell_center),
        ],
        [
            Paragraph("Parte II — Cenário C", tab_cell),
            Paragraph("Válida (Verified OK isolado)", tab_cell),
            Paragraph("Inválida (Fora da Trust Store)", tab_cell),
            Paragraph("error 20: unable to get local issuer (Exit 2)", tab_cell),
            Paragraph("<b>REJEITAR</b>", tab_cell_center),
        ],
    ]
    tabela_matriz = Table(dados_matriz, colWidths=[3.3 * cm, 3.5 * cm, 3.8 * cm, 4.3 * cm, 2.1 * cm])
    tabela_matriz.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(tabela_matriz)
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.2. Recomendações Técnicas para a Miguelito Segurança e Tecnologia", h2_style))
    story.append(
        Paragraph(
            "• <b>1. Validação Obrigatória em Duas Etapas e Fixação de Trust Store:</b> O pipeline de recebimento de "
            "contratos deve executar primeiro <code>openssl verify -CAfile miguelito_root_ca.crt</code> antes de conferir "
            "a assinatura RSA, bloqueando qualquer certificado emitido por CAs externas não homologadas.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>2. Guarda da Root CA Offline em HSM e Uso de CA Intermediária:</b> Manter a chave privada RSA 4096 bits "
            "da <code>Miguelito Root CA</code> isolada em hardware (HSM FIPS 140-3) e criar uma Autoridade Certificadora "
            "Intermediária para assinar os certificados operacionais dos parceiros comerciais.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>3. Verificação de Revogação (CRL / OCSP) e Extensões X.509 v3:</b> Publicar Listas de Certificados "
            "Revogados (CRL) e ativar consulta OCSP (<code>-crl_check</code>) para recusar chaves privadas comprometidas "
            "antes do vencimento, além de exigir <code>CA:FALSE</code> e <code>keyUsage: digitalSignature, nonRepudiation</code>.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>4. Proibição de Reuso de Nonce e Rotação de Chaves no AES-GCM:</b> Garantir que cada operação no "
            "AES-256-GCM utilize um Nonce de 12 bytes único gerado por CSPRNG e rotacionar periodicamente as chaves "
            "simétricas, prevenindo a exposição do <i>keystream</i> e da subchave <i>H</i> do GHASH.",
            bullet_style,
        )
    )

    # ==========================================================================
    # SEÇÃO 7: CONCLUSÃO E SEÇÃO 8: REFERÊNCIAS BIBLIOGRÁFICAS
    # ==========================================================================
    story.append(Paragraph("7. Conclusão", h1_style))
    story.append(
        Paragraph(
            "O trabalho experimental realizado para o cenário da <b>Miguelito Segurança e Tecnologia Ltda.</b> demonstrou "
            "na prática como a cifragem simétrica autenticada e a infraestrutura de chaves públicas atuam de forma "
            "complementar na proteção de contratos digitais. Na Parte I, comprovou-se que o modo <b>AES-256-GCM</b> "
            "elimina a maleabilidade do modo contador puro por meio do polinômio <b>GHASH</b> em GF(2<sup>128</sup>), "
            "bloqueando instantaneamente tanto a adulteração de 1 bit no texto cifrado quanto o uso de chaves espúrias "
            "através da exceção <code>InvalidTag</code>.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Na Parte II, os testes com o OpenSSL evidenciaram a distinção fundamental entre integridade matemática de "
            "dados e autenticidade da identidade do signatário. Enquanto o Cenário B mostrou que qualquer fraude pós-assinatura "
            "em valores contratuais é barrada pelo efeito avalanche do <b>SHA-256</b> (<code>Verification failure</code>), "
            "o Cenário C provou que uma assinatura matematicamente válida (<code>Verified OK</code>) deve ser rejeitada "
            "quando seu certificado não possui vínculo de confiança com a <code>Miguelito Root CA</code> "
            "(<code>error 20: unable to get local issuer certificate</code>). A adoção conjunta desses dois controles "
            "restabelece integralmente a confidencialidade, a integridade, a autenticidade e o não-repúdio nas operações da empresa.",
            body_style,
        )
    )

    story.append(Paragraph("8. Referências Bibliográficas", h1_style))
    refs = [
        "1. <b>DWORKIN, Morris J.</b> <i>Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC</i>. NIST Special Publication (SP) 800-38D, National Institute of Standards and Technology, Gaithersburg, MD, Nov. 2007.",
        "2. <b>COOPER, D.; SANTESSON, S.; FARRELL, S.; BOEYEN, S.; HOUSLEY, R.; POLK, W.</b> <i>Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile</i>. IETF RFC 5280, Maio 2008.",
        "3. <b>MORIARTY, K.; KALISKI, B.; JONSSON, J.; RUSCH, A.</b> <i>PKCS #1: RSA Cryptography Specifications Version 2.2</i>. IETF RFC 8017, Nov. 2016.",
        "4. <b>NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST).</b> <i>Secure Hash Standard (SHS)</i>. FIPS PUB 180-4, U.S. Department of Commerce, Ago. 2015.",
        "5. <b>STALLINGS, William.</b> <i>Criptografia e Segurança de Redes: Princípios e Práticas</i>. 8ª ed. São Paulo: Pearson Education, 2023.",
        "6. <b>PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA).</b> <i>Cryptography Documentation — Authenticated Encryption with Associated Data (AESGCM)</i>. Disponível em: https://cryptography.io/en/latest/hazmat/primitives/aead/.",
    ]
    for r in refs:
        story.append(Paragraph(r, bullet_style))

    doc.build(story, canvasmaker=CanvasRelatorioAcademico)
    print(f"PDF gerado com sucesso em: {caminho_saida}")


if __name__ == "__main__":
    gerar_pdf()
