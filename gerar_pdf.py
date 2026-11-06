import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas com numeração de páginas profissional: 'Página X de Y' e cabeçalho sutil."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Desenha cabeçalho apenas da página 2 em diante
        if self._pageNumber > 1:
            self.drawString(
                2 * cm, 
                28.2 * cm, 
                "MATC99 — Segurança e Auditoria de Sistemas de Informação | UFBA"
            )
            self.setStrokeColor(colors.HexColor("#D0D7DE"))
            self.setLineWidth(0.5)
            self.line(2 * cm, 28.0 * cm, 19 * cm, 28.0 * cm)

        # Rodapé em todas as páginas
        self.setStrokeColor(colors.HexColor("#D0D7DE"))
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.8 * cm, 19 * cm, 1.8 * cm)
        
        self.drawString(
            2 * cm, 
            1.3 * cm, 
            "Relatório Técnico — Criptografia Aplicada e Perícia Forense (Miguelito Seg. e Tec.)"
        )
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19 * cm, 1.3 * cm, page_str)
        self.restoreState()


def build_pdf(filename="RELATORIO_TECNICO_MATC99.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0B2545")
    secondary_color = colors.HexColor("#134074")
    body_color = colors.HexColor("#1D2D44")
    code_bg = colors.HexColor("#F4F6F9")
    code_border = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        alignment=1, # Centralizado
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        alignment=1,
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=body_color,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=body_color,
        alignment=4, # Justificado
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=0
    )

    formula_style = ParagraphStyle(
        'Formula_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        alignment=1,
        textColor=primary_color,
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # Cabeçalho da Capa
    story.append(Paragraph("UNIVERSIDADE FEDERAL DA BAHIA — UFBA", subtitle_style))
    story.append(Paragraph("INSTITUTO DE COMPUTAÇÃO — DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO", meta_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("RELATÓRIO TÉCNICO DE AUDITORIA FORENSE E CRIPTOGRAFIA APLICADA", title_style))
    story.append(Paragraph("Proteção de Contratos Digitais, Cifras AEAD (AES-256-GCM), PKI X.509 e Assinaturas RSA", subtitle_style))
    
    meta_text = (
        "<b>Disciplina:</b> Segurança e Auditoria de Sistemas de Informação (MATC99)<br/>"
        "<b>Empresa Auditada (Cenário Prático):</b> Miguelito Segurança e Tecnologia Ltda.<br/>"
        "<b>Autor:</b> Wellington Miguel de Jesus Silva &nbsp;|&nbsp; <b>Data:</b> Novembro de 2026"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=14))

    # 1. Introdução
    story.append(Paragraph("1. Introdução e Contextualização do Incidente", h1_style))
    story.append(Paragraph(
        "A empresa <b>Miguelito Segurança e Tecnologia Ltda.</b> (CNPJ 14.382.910/0001-55), sediada em Salvador/BA, formaliza contratos eletrônicos "
        "com prestadores de serviços de infraestrutura crítica em nuvem. Durante a rotina de auditoria interna sobre a tramitação do "
        "<b>Contrato Comercial nº 2026/00849-MST</b>, firmado com a fornecedora <i>Parceiro Infraestrutura e Cloud Computing Ltda.</i> "
        "(parceiro.miguelito.com.br) no valor global de R$ 1.450.000,00, foram levantadas vulnerabilidades operacionais na transmissão e custódia do documento.",
        body_style
    ))
    story.append(Paragraph(
        "A auditoria delimitou três vetores de risco que demandavam tratamento criptográfico determinístico:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Adulteração em Trânsito (Bit-Flipping):</b> A possibilidade de interceptação de arquivos cifrados com manipulação de valores em modos de cifra maleáveis.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Fraude Pós-Assinatura:</b> A alteração intencional de cláusulas contratuais (ex.: parcela mensal de R$ 120.833,33 para R$ 920.833,33) após a aposição de assinatura legítima.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Falsificação de Identidade via Rogue CA:</b> A submissão de documentos assinados com chaves privadas associadas a certificados forjados emitidos por autoridades não confiáveis.",
        bullet_style
    ))
    story.append(Paragraph(
        "Para solucionar esses problemas, implementou-se uma arquitetura de proteção em duas frentes: confidencialidade e integridade via cifra simétrica autenticada "
        "<b>AES-256-GCM</b> (Parte I) e não-repúdio e garantia de identidade por meio de <b>PKI X.509</b> e assinaturas <b>RSA-SHA256</b> (Parte II).",
        body_style
    ))

    # 2. Fundamentação Teórica
    story.append(Paragraph("2. Fundamentação Teórica", h1_style))
    story.append(Paragraph("2.1. Criptografia Simétrica vs. Assimétrica", h2_style))
    story.append(Paragraph(
        "A criptografia simétrica emprega a mesma chave secreta para cifrar e decifrar. Apresenta alta taxa de transferência e suporte de hardware (AES-NI), "
        "sendo ideal para grandes volumes de dados. Contudo, não oferece não-repúdio entre as partes que conhecem a chave. Já a criptografia assimétrica baseia-se "
        "em pares de chaves matematicamente vinculadas (privada e pública). Embora seja computacionalmente mais exigente, resolve a distribuição de chaves e provê não-repúdio pericial.",
        body_style
    ))

    story.append(Paragraph("2.2. Funcionamento do Modo AES-256-GCM (AEAD)", h2_style))
    story.append(Paragraph(
        "O AES-GCM (NIST SP 800-38D) é um esquema de cifragem autenticada que combina o modo contador (GCTR) com autenticação polinomial universal (GHASH) em GF(2¹²⁸). "
        "O texto cifrado é gerado por C_i = P_i ⊕ E_K(inc₃₂(J₀)). Para garantir a integridade, deriva-se a subchave de autenticação H = E_K(0¹²⁸). Os dados associados (AAD) "
        "e os blocos de texto cifrado são avaliados segundo o polinômio irredutível P(x) = x¹²⁸ + x⁷ + x² + x + 1. A Authentication Tag resultante de 128 bits é dada por:",
        body_style
    ))
    story.append(Paragraph("T = GHASH_H(AAD, Ciphertext) ⊕ E_K(J₀)", formula_style))
    story.append(Paragraph(
        "Se um único bit de C_i for alterado (C'_i = C_i ⊕ Δ com Δ ≠ 0), a diferença na tag calculada será ΔT = Δ · H^(n - i + 2) mod P(x). Como GF(2¹²⁸) é um corpo finito "
        "isento de divisores de zero, ΔT ≠ 0 para qualquer Δ ≠ 0 e H ≠ 0, impedindo alterações silenciosas e disparando imediatamente a exceção <i>InvalidTag</i>.",
        body_style
    ))

    story.append(Paragraph("2.3. Assinaturas Digitais (RSA-SHA256) e Infraestrutura de Chaves Públicas (RFC 5280)", h2_style))
    story.append(Paragraph(
        "A assinatura digital opera no paradigma Hash-then-Sign (PKCS#1 v1.5 / RFC 8017). Calcula-se o resumo h = SHA-256(M), aplica-se a codificação com preenchimento ASN.1 (EM) "
        "e eleva-se à chave privada: S = EM^d mod N. A verificação calcula EM' = S^e mod N e confere o hash. "
        "A PKI X.509 garante a amarração segura entre a identidade do titular e a chave pública através de uma cadeia de confiança hierárquica assinada pela Root CA corporativa.",
        body_style
    ))

    # 3. Metodologia e Ambiente
    story.append(Paragraph("3. Metodologia e Ambiente Experimental", h1_style))
    story.append(Paragraph(
        "Os testes foram desenvolvidos e executados em subsistema Linux de auditoria, preservando logs com carimbo de tempo em milissegundos e integridade forense SHA-256.",
        body_style
    ))

    table_env_data = [
        [Paragraph("<b>Componente</b>", body_style), Paragraph("<b>Versão / Especificação</b>", body_style), Paragraph("<b>Aplicação nos Experimentos</b>", body_style)],
        [Paragraph("Sistema Operacional", body_style), Paragraph("Ubuntu 24.04 LTS (Kernel 6.6.87.2 WSL2)", body_style), Paragraph("Ambiente controlado de execução POSIX.", body_style)],
        [Paragraph("Interpretador", body_style), Paragraph("Python 3.12.3", body_style), Paragraph("Execução do módulo parte1_aes_gcm.py.", body_style)],
        [Paragraph("Biblioteca Cripto", body_style), Paragraph("cryptography 41.0.7 / 50.0.2", body_style), Paragraph("Cifragem AESGCM e tratamento de InvalidTag.", body_style)],
        [Paragraph("CLI OpenSSL", body_style), Paragraph("OpenSSL 3.0.13 (30 Jan 2024)", body_style), Paragraph("Geração de chaves, certificados X.509 e assinaturas.", body_style)],
        [Paragraph("Contrato Base", body_style), Paragraph("contrato_miguelito.txt (2.841 bytes)", body_style), Paragraph("Documento comercial nº 2026/00849-MST auditado.", body_style)]
    ]
    t_env = Table(table_env_data, colWidths=[3.5 * cm, 5.5 * cm, 8.0 * cm])
    t_env.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_env)
    story.append(Spacer(1, 10))

    # 4. Experimentos Parte I
    story.append(Paragraph("4. Experimentos da Parte I: Proteção e Integridade com AES-256-GCM", h1_style))
    story.append(Paragraph(
        "O script <code>parte1_aes_gcm.py</code> carrega o contrato original (SHA-256: <code>9147c039...</code>), gera chave simétrica de 256 bits, "
        "Nonce de 12 bytes (96 bits) e dados associados (AAD: <code>MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849</code>). "
        "O arquivo cifrado <code>contrato_miguelito.enc</code> foi salvo em disco com 2.869 bytes (12B Nonce + 2.841B Ciphertext + 16B Tag).",
        body_style
    ))
    story.append(Paragraph(
        "A decifragem legítima recuperou os 2.841 bytes sem divergências (original == recuperado: True). Em seguida, foram testados os cenários de falha planejados:",
        body_style
    ))

    log_p1_text = (
        "[INFO] Contrato carregado: contrato_miguelito.txt (2841 bytes)\n"
        "[INFO] SHA-256 original: 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67\n"
        "[INFO] Arquivo cifrado salvo em: contrato_miguelito.enc (2869 bytes totais)\n"
        "[INFO] Comparacao de bytes (original == recuperado): True (2841 bytes)\n"
        "[INFO] --- [Teste de Falha 1: Adulteracao de 1 byte no Ciphertext (Bit-Flipping)] ---\n"
        "[INFO] Byte modificado no offset 1420 (0x058C): 0x4B -> 0x4A\n"
        "[WARN] Excecao capturada com sucesso: cryptography.exceptions.InvalidTag\n"
        "[INFO] Motivo: A alteracao mudou o resultado do GHASH em GF(2^128). Tag recalculada divergiu da original.\n"
        "[INFO] --- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---\n"
        "[WARN] Excecao capturada com sucesso: cryptography.exceptions.InvalidTag\n"
        "[INFO] Motivo: Chave K' espuria altera subchave H' e mascara E_K'(J0), invalidando a tag em tempo constante."
    )
    t_log_p1 = Table([[Preformatted(log_p1_text, code_style)]], colWidths=[17.0 * cm])
    t_log_p1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), code_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, code_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_log_p1)
    story.append(Spacer(1, 10))

    # 5. Experimentos Parte II
    story.append(Paragraph("5. Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação", h1_style))
    story.append(Paragraph(
        "A infraestrutura PKI construída pelo script <code>parte2_pki_testes.sh</code> implantou duas hierarquias: "
        "(1) Cadeia Confiável corporativa composta pela <b>Miguelito Root CA</b> (RSA 4096 bits) e certificado da entidade <b>parceiro.miguelito.com.br</b> (RSA 2048 bits); "
        "(2) Cadeia Não Confiável formada por uma <b>Rogue CA</b> que emitiu certificado falso sob o mesmo CN do parceiro.",
        body_style
    ))

    # Cenário A
    story.append(Paragraph("5.1. Cenário A: Documento Íntegro e Cadeia Confiável (Veredito: ACEITAR)", h2_style))
    story.append(Paragraph(
        "O contrato foi assinado pela chave privada legítima do parceiro e validado em duas etapas com a chave pública e a Trust Store corporativa:",
        body_style
    ))
    cmd_a = (
        "$ openssl dgst -sha256 -verify parceiro_pub.pem -signature cenario_a.sig contrato_miguelito.txt\n"
        "Resultado: Verified OK\n"
        "$ openssl verify -CAfile miguelito_root_ca.crt parceiro.crt\n"
        "Resultado: parceiro.crt: OK"
    )
    t_cmd_a = Table([[Preformatted(cmd_a, code_style)]], colWidths=[17.0 * cm])
    t_cmd_a.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), code_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, code_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cmd_a)
    story.append(Paragraph("<b>Justificativa de Aceitação:</b> Integridade matemática atestada pelo SHA-256 e identidade do signatário ratificada pela Root CA interna.", body_style))

    # Cenário B
    story.append(Paragraph("5.2. Cenário B: Adulteração Pós-Assinatura no Contrato (Veredito: REJEITAR)", h2_style))
    story.append(Paragraph(
        "Simulou-se fraude contratual modificando o valor mensal de R$ 120.833,33 para R$ 920.833,33 (1 byte alterado: '1' para '9'). "
        "O hash original (<code>9147c039...</code>) divergiu do hash adulterado (<code>817d7fae...</code>).",
        body_style
    ))
    cmd_b = (
        "$ openssl dgst -sha256 -verify parceiro_pub.pem -signature cenario_a.sig contrato_adulterado.txt\n"
        "error:02000068:rsa routines:ossl_rsa_verify:bad signature\n"
        "Verification failure (Exit Code: 1)"
    )
    t_cmd_b = Table([[Preformatted(cmd_b, code_style)]], colWidths=[17.0 * cm])
    t_cmd_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), code_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, code_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cmd_b)
    story.append(Paragraph("<b>Justificativa de Rejeição:</b> Quebra estrita do hash SHA-256 pelo efeito avalanche. O bloco PKCS#1 decifrado não corresponde ao digest do texto alterado.", body_style))

    # Cenário C
    story.append(Paragraph("5.3. Cenário C: Certificado Forjado por Rogue CA (Veredito: REJEITAR)", h2_style))
    story.append(Paragraph(
        "O contrato íntegro foi assinado com a chave do certificado emitido pela Rogue CA. A verificação matemática isolada tem êxito, mas a validação de cadeia corporativa falha:",
        body_style
    ))
    cmd_c = (
        "$ openssl dgst -sha256 -verify parceiro_forjado_pub.pem -signature cenario_c_forjado.sig contrato_miguelito.txt\n"
        "Resultado: Verified OK  <-- Integridade matematica aparente\n"
        "$ openssl verify -CAfile miguelito_root_ca.crt parceiro_forjado.crt\n"
        "error 20 at 0 depth lookup: unable to get local issuer certificate\n"
        "verification failed (Exit Code: 2)"
    )
    t_cmd_c = Table([[Preformatted(cmd_c, code_style)]], colWidths=[17.0 * cm])
    t_cmd_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), code_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, code_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cmd_c)
    story.append(Paragraph(
        "<b>Diferenciação Crítica:</b> Demonstra-se que integridade matemática isolada não comprova legitimidade. Sem validação de cadeia X.509 na Trust Store, "
        "ataques de spoofing de certificado não são detectados.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # 6. Matriz de Decisão
    story.append(Paragraph("6. Matriz de Decisão e Recomendações Corporativas", h1_style))
    story.append(Paragraph("6.1. Tabela Comparativa de Auditoria", h2_style))

    table_audit_data = [
        [Paragraph("<b>Cenário / Teste</b>", body_style), Paragraph("<b>Integridade Matemática</b>", body_style), Paragraph("<b>Confiabilidade da Chave / CA</b>", body_style), Paragraph("<b>Resultado OpenSSL / Python</b>", body_style), Paragraph("<b>Decisão</b>", body_style)],
        [Paragraph("Parte I: AEAD Normal", body_style), Paragraph("Válida (Tag GCM confere)", body_style), Paragraph("Válida (Chave simétrica legítima)", body_style), Paragraph("2.841 bytes íntegros", body_style), Paragraph("<font color='#0D9488'><b>ACEITAR</b></font>", body_style)],
        [Paragraph("Parte I: Bit-Flipping", body_style), Paragraph("Inválida (GHASH diverge)", body_style), Paragraph("Válida (Chave legítima)", body_style), Paragraph("InvalidTag levantada", body_style), Paragraph("<font color='#E11D48'><b>REJEITAR</b></font>", body_style)],
        [Paragraph("Parte I: Chave Espúria", body_style), Paragraph("Não verificável (H' != H)", body_style), Paragraph("Inválida (Chave não autorizada)", body_style), Paragraph("InvalidTag levantada", body_style), Paragraph("<font color='#E11D48'><b>REJEITAR</b></font>", body_style)],
        [Paragraph("Parte II: Cenário A", body_style), Paragraph("Válida (Verified OK)", body_style), Paragraph("Válida (Miguelito Root CA: OK)", body_style), Paragraph("Exit Code 0 em ambos", body_style), Paragraph("<font color='#0D9488'><b>ACEITAR</b></font>", body_style)],
        [Paragraph("Parte II: Cenário B", body_style), Paragraph("Inválida (Verification failure)", body_style), Paragraph("Válida (Certificado legítimo)", body_style), Paragraph("Exit Code 1 (bad signature)", body_style), Paragraph("<font color='#E11D48'><b>REJEITAR</b></font>", body_style)],
        [Paragraph("Parte II: Cenário C", body_style), Paragraph("Válida (Verified OK)", body_style), Paragraph("Inválida (Fora da Trust Store)", body_style), Paragraph("Exit Code 2 (error 20)", body_style), Paragraph("<font color='#E11D48'><b>REJEITAR</b></font>", body_style)],
    ]
    t_audit = Table(table_audit_data, colWidths=[3.2 * cm, 3.4 * cm, 3.8 * cm, 4.4 * cm, 2.2 * cm])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_audit)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.2. Recomendações Práticas para a Miguelito Segurança e Tecnologia", h2_style))
    story.append(Paragraph("1. <b>Validação em Duas Etapas Obrigatória:</b> Condicionar a validação de contratos à checagem prévia da cadeia X.509 (-CAfile miguelito_root_ca.crt), recusando certificados emitidos por CAs não homologadas.", bullet_style))
    story.append(Paragraph("2. <b>Custódia da Root CA em HSM e Uso de Sub-CA:</b> Manter a chave privada RSA 4096-bit da Miguelito Root CA isolada (offline/HSM) e emitir certificados finais apenas por Autoridade Intermediária.", bullet_style))
    story.append(Paragraph("3. <b>Mecanismos de Revogação (CRL / OCSP):</b> Implementar listas CRL ou consulta OCSP no pipeline de recepção para barrar chaves privadas comprometidas antes do vencimento.", bullet_style))
    story.append(Paragraph("4. <b>Gestão de Nonces no AES-GCM:</b> Garantir Nonces aleatórios de 12 bytes gerados por CSPRNG sem repetição para uma mesma chave simétrica, evitando a recuperação da subchave H do GHASH.", bullet_style))

    # 7. Conclusão
    story.append(Paragraph("7. Conclusão", h1_style))
    story.append(Paragraph(
        "A auditoria prática comprovou a complementaridade entre cifra simétrica autenticada e infraestrutura de chaves públicas. "
        "O AES-256-GCM assegurou a blindagem de trânsito contra interceptações e neutralizou ataques de bit-flipping via GHASH. "
        "Por sua vez, a PKI corporativa ancorada na Miguelito Root CA eliminou a fragilidade de validações matemáticas cegas (Cenário C), "
        "fornecendo a base necessária para que contratos digitais possuam confidencialidade, integridade, autenticidade e validade jurídica incontestável.",
        body_style
    ))

    # 8. Referências
    story.append(Paragraph("8. Referências Bibliográficas", h1_style))
    story.append(Paragraph("1. DWORKIN, M. J. <i>Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC</i>. NIST SP 800-38D, Nov. 2007.", body_style))
    story.append(Paragraph("2. COOPER, D. et al. <i>Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile</i>. IETF RFC 5280, Maio 2008.", body_style))
    story.append(Paragraph("3. MORIARTY, K. et al. <i>PKCS #1: RSA Cryptography Specifications Version 2.2</i>. IETF RFC 8017, Nov. 2016.", body_style))
    story.append(Paragraph("4. STALLINGS, W. <i>Criptografia e Segurança de Redes: Princípios e Práticas</i>. 8ª ed. São Paulo: Pearson, 2023.", body_style))
    story.append(Paragraph("5. PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA). <i>Cryptography Documentation — AESGCM</i>. https://cryptography.io", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso: {filename}")

if __name__ == "__main__":
    build_pdf()
