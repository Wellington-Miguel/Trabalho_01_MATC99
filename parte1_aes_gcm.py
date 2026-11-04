#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
UNIVERSIDADE FEDERAL DA BAHIA (UFBA) - INSTITUTO DE COMPUTAÇÃO
Disciplina: MATC99 - Segurança e Auditoria de Sistemas de Informação
Trabalho 01: Criptografia Aplicada: Proteção, Assinaturas Digitais e Certificados
Módulo: Parte I - Proteção e Integridade com AES-256-GCM (AEAD)
Arquivo: parte1_aes_gcm.py
================================================================================
Descrição Técnica:
    Implementa e valida experimentalmente controles criptográficos baseados na
    cifra simétrica autenticada AES-256-GCM (NIST SP 800-38D), demonstrando:
      1. Carregamento e inspeção forense (SHA-256) do contrato comercial original.
      2. Cifragem autenticada com chave de 256 bits, Nonce CSPRNG de 96 bits (12B)
         e Authentication Tag de 128 bits (16B) gerada pela função GHASH em GF(2^128).
      3. Decifragem legítima e verificação byte a byte de integridade.
      4. Detecção de adulteração de 1 byte no ciphertext (ataque de bit-flipping)
         com captura da exceção cryptography.exceptions.InvalidTag.
      5. Detecção de tentativa de decifragem com chave simétrica incorreta (espúria)
         com captura da exceção cryptography.exceptions.InvalidTag.
================================================================================
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Constantes Criptográficas (NIST SP 800-38D)
KEY_SIZE_BITS: int = 256
KEY_SIZE_BYTES: int = KEY_SIZE_BITS // 8       # 32 bytes (256 bits)
NONCE_SIZE_BYTES: int = 12                     # 12 bytes (96 bits recomendados pelo NIST)
TAG_SIZE_BYTES: int = 16                       # 16 bytes (128 bits de Authentication Tag)
AAD_DEFAULT: bytes = b"MATC99-UFBA|XYZW-TECNOLOGIA|CONTRATO-2026-00849|AES-256-GCM"

# Caminhos de arquivos
BASE_DIR: Path = Path(__file__).resolve().parent
INPUT_FILE: Path = BASE_DIR / "contrato_xyzw.txt"
ENCRYPTED_FILE: Path = BASE_DIR / "contrato_xyzw.enc"
RECOVERED_FILE: Path = BASE_DIR / "contrato_xyzw_recuperado.txt"
LOG_FILE: Path = BASE_DIR / "parte1_aes_gcm.log"


@dataclass(frozen=True)
class PacoteCriptograficoGCM:
    """
    Estrutura de dados para representar o criptograma AEAD AES-256-GCM.
    Na biblioteca `cryptography`, o método `AESGCM.encrypt()` retorna a
    concatenação `ciphertext || tag` (onde os últimos 16 bytes são a Tag).
    No arquivo `.enc`, persistimos: `nonce (12B) || ciphertext (N bytes) || tag (16B)`.
    """
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    aad: bytes

    @property
    def payload_combinado(self) -> bytes:
        """Retorna ciphertext || tag conforme esperado por AESGCM.decrypt()."""
        return self.ciphertext + self.tag

    def serializar(self) -> bytes:
        """Serializa o pacote para gravação em disco: Nonce (12B) || Ciphertext || Tag (16B)."""
        return self.nonce + self.ciphertext + self.tag

    @classmethod
    def desserializar(cls, dados_brutos: bytes, aad: bytes = AAD_DEFAULT) -> "PacoteCriptograficoGCM":
        """Reconstrói a estrutura a partir dos bytes lidos do arquivo `.enc`."""
        tamanho_minimo = NONCE_SIZE_BYTES + TAG_SIZE_BYTES
        if len(dados_brutos) < tamanho_minimo:
            raise ValueError(
                f"Arquivo criptografado truncado ou inválido: {len(dados_brutos)} bytes "
                f"(mínimo esperado: {tamanho_minimo} bytes)."
            )
        nonce = dados_brutos[:NONCE_SIZE_BYTES]
        ciphertext = dados_brutos[NONCE_SIZE_BYTES:-TAG_SIZE_BYTES]
        tag = dados_brutos[-TAG_SIZE_BYTES:]
        return cls(nonce=nonce, ciphertext=ciphertext, tag=tag, aad=aad)


def configurar_logger() -> logging.Logger:
    """Configura logger com timestamps precisos em ISO-8601 para console e arquivo."""
    logger = logging.getLogger("Auditoria_AES_GCM")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formato = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formato)

    file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formato)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def calcular_sha256(dados: bytes) -> str:
    """Calcula o resumo criptográfico SHA-256 em representação hexadecimal."""
    return hashlib.sha256(dados).hexdigest()


def carregar_documento(caminho: Path, logger: logging.Logger) -> bytes:
    """Carrega o documento contratual em bytes e registra suas métricas forenses."""
    if not caminho.exists():
        raise FileNotFoundError(f"Documento contratual não encontrado em: {caminho}")

    conteudo = caminho.read_bytes()
    resumo_hash = calcular_sha256(conteudo)
    logger.info("Documento carregado com sucesso: '%s'", caminho.name)
    logger.info("  -> Tamanho original (Plaintext): %d bytes", len(conteudo))
    logger.info("  -> SHA-256 (Plaintext)         : %s", resumo_hash)
    return conteudo


def cifrar_documento_aes_gcm(
    plaintext: bytes,
    chave: bytes,
    aad: bytes,
    caminho_saida: Path,
    logger: logging.Logger,
) -> PacoteCriptograficoGCM:
    """
    Executa a cifragem autenticada AES-256-GCM gerando Nonce CSPRNG de 12 bytes
    e Authentication Tag de 16 bytes, persistindo o resultado em `contrato_xyzw.enc`.
    """
    if len(chave) != KEY_SIZE_BYTES:
        raise ValueError(f"A chave deve conter exatamente {KEY_SIZE_BYTES} bytes (256 bits).")

    # Geração de Nonce (Initialization Vector) criptograficamente seguro de 96 bits (12 bytes)
    nonce: bytes = os.urandom(NONCE_SIZE_BYTES)
    aesgcm = AESGCM(chave)

    # AESGCM.encrypt retorna: Ciphertext (mesmo tamanho do plaintext) + Tag (16 bytes)
    ct_e_tag: bytes = aesgcm.encrypt(nonce=nonce, data=plaintext, associated_data=aad)
    ciphertext: bytes = ct_e_tag[:-TAG_SIZE_BYTES]
    tag: bytes = ct_e_tag[-TAG_SIZE_BYTES:]

    pacote = PacoteCriptograficoGCM(nonce=nonce, ciphertext=ciphertext, tag=tag, aad=aad)
    bytes_serializados = pacote.serializar()
    caminho_saida.write_bytes(bytes_serializados)

    logger.info("Cifragem AES-256-GCM concluída e gravada em '%s'.", caminho_saida.name)
    logger.info("  -> Algoritmo / Modo            : AES-256-GCM (NIST SP 800-38D)")
    logger.info("  -> Chave Simétrica (256 bits)  : %s", chave.hex())
    logger.info("  -> Nonce / IV (96 bits / 12B)  : %s", nonce.hex())
    logger.info("  -> Dados Associados (AAD)      : %s", aad.decode("utf-8"))
    logger.info("  -> Tamanho do Ciphertext       : %d bytes", len(ciphertext))
    logger.info("  -> Authentication Tag (128b/16B): %s", tag.hex())
    logger.info("  -> Tamanho Total (.enc)        : %d bytes (12B Nonce + %dB CT + 16B Tag)",
                len(bytes_serializados), len(ciphertext))
    logger.info("  -> SHA-256 do Arquivo (.enc)   : %s", calcular_sha256(bytes_serializados))

    return pacote


def decifrar_documento_aes_gcm(
    pacote: PacoteCriptograficoGCM,
    chave: bytes,
    logger: logging.Logger,
    caminho_recuperado: Optional[Path] = None,
) -> bytes:
    """
    Executa a decifragem e validação da Tag de Autenticação (GHASH) via AES-256-GCM.
    Caso qualquer bit do Nonce, AAD, Ciphertext, Tag ou Chave divirja, a biblioteca
    lança imediatamente `cryptography.exceptions.InvalidTag` sem liberar plaintext.
    """
    aesgcm = AESGCM(chave)
    plaintext_recuperado = aesgcm.decrypt(
        nonce=pacote.nonce,
        data=pacote.payload_combinado,
        associated_data=pacote.aad,
    )
    if caminho_recuperado is not None:
        caminho_recuperado.write_bytes(plaintext_recuperado)
    return plaintext_recuperado


def simular_adulteracao_ciphertext(
    pacote_legitimo: PacoteCriptograficoGCM,
    chave_legitima: bytes,
    logger: logging.Logger,
) -> Tuple[bool, str]:
    """
    Cenário de Falha 4.1: Adulteração intencional de 1 byte no ciphertext (Bit-Flipping).
    Inverte os bits de um byte específico no meio do ciphertext (XOR 0x01) simulando
    um ataque de modificação em trânsito (Man-in-the-Middle) sobre valores contratuais.
    """
    logger.info("-" * 80)
    logger.info("[CENÁRIO DE FALHA 1] Teste de Adulteração de 1 Byte no Ciphertext (Bit-Flipping)")
    logger.info("-" * 80)

    ct_mutavel = bytearray(pacote_legitimo.ciphertext)
    posicao_alvo: int = len(ct_mutavel) // 2
    byte_original: int = ct_mutavel[posicao_alvo]
    byte_adulterado: int = byte_original ^ 0x01  # Inversão de 1 bit (LSB) no byte alvo
    ct_mutavel[posicao_alvo] = byte_adulterado

    pacote_adulterado = PacoteCriptograficoGCM(
        nonce=pacote_legitimo.nonce,
        ciphertext=bytes(ct_mutavel),
        tag=pacote_legitimo.tag,
        aad=pacote_legitimo.aad,
    )

    logger.info("  -> Posição alterada no Ciphertext : Offset %d (0x%04X)", posicao_alvo, posicao_alvo)
    logger.info("  -> Valor do byte original         : 0x%02X (bin: %s)", byte_original, format(byte_original, "08b"))
    logger.info("  -> Valor após XOR 0x01 (Bit-Flip) : 0x%02X (bin: %s)", byte_adulterado, format(byte_adulterado, "08b"))
    logger.info("  -> Tentando decifrar pacote adulterado com a chave legítima...")

    try:
        decifrar_documento_aes_gcm(pacote_adulterado, chave_legitima, logger)
        logger.error("  -> [FALHA CRÍTICA DE SEGURANÇA] O pacote adulterado foi aceito indevidamente!")
        return False, "Falha: adulteração não detectada"
    except InvalidTag as exc:
        tb_linhas = traceback.format_exc().strip().splitlines()
        ultima_linha_tb = tb_linhas[-1] if tb_linhas else repr(exc)
        logger.warning(
            "  -> [EXCEÇÃO CAPTURADA] Tipo: %s.%s | Mensagem: %s",
            InvalidTag.__module__,
            InvalidTag.__name__,
            ultima_linha_tb,
        )
        logger.info(
            "  -> [BLOQUEIO EFETIVO] Decifragem abortada antes da liberação do texto em claro! "
            "O polinômio GHASH em GF(2^128) produziu uma Tag divergente da Tag anexada."
        )
        return True, ultima_linha_tb


def simular_chave_incorreta(
    pacote_legitimo: PacoteCriptograficoGCM,
    chave_legitima: bytes,
    logger: logging.Logger,
) -> Tuple[bool, str]:
    """
    Cenário de Falha 4.2: Tentativa de decifragem com uma chave simétrica incorreta.
    Gera uma chave espúria de 256 bits e tenta decifrar o pacote legítimo.
    """
    logger.info("-" * 80)
    logger.info("[CENÁRIO DE FALHA 2] Tentativa de Decifragem com Chave Simétrica Incorreta")
    logger.info("-" * 80)

    chave_incorreta: bytes = os.urandom(KEY_SIZE_BYTES)
    while chave_incorreta == chave_legitima:
        chave_incorreta = os.urandom(KEY_SIZE_BYTES)

    logger.info("  -> Chave Legítima (256 bits)      : %s", chave_legitima.hex())
    logger.info("  -> Chave Espúria  (256 bits)      : %s", chave_incorreta.hex())
    logger.info("  -> Tentando decifrar o arquivo 'contrato_xyzw.enc' com a chave espúria...")

    try:
        decifrar_documento_aes_gcm(pacote_legitimo, chave_incorreta, logger)
        logger.error("  -> [FALHA CRÍTICA DE SEGURANÇA] Decifragem com chave incorreta não lançou erro!")
        return False, "Falha: chave espúria aceita"
    except InvalidTag as exc:
        tb_linhas = traceback.format_exc().strip().splitlines()
        ultima_linha_tb = tb_linhas[-1] if tb_linhas else repr(exc)
        logger.warning(
            "  -> [EXCEÇÃO CAPTURADA] Tipo: %s.%s | Mensagem: %s",
            InvalidTag.__module__,
            InvalidTag.__name__,
            ultima_linha_tb,
        )
        logger.info(
            "  -> [BLOQUEIO EFETIVO] A subchave de hash H' = E(K', 0^128) e a máscara E(K', J_0) "
            "derivadas da chave espúria K' são completamente distintas das originais, "
            "invalidando a verificação da Tag em tempo constante."
        )
        return True, ultima_linha_tb


def exibir_explicacao_matematica_ghash(logger: logging.Logger) -> None:
    """Registra no log a fundamentação matemática do GHASH sobre o Corpo de Galois GF(2^128)."""
    logger.info("=" * 80)
    logger.info("FUNDAMENTAÇÃO MATEMÁTICA: COMO O GHASH IMPEDE ATAQUES DE ALTERAÇÃO DE CONTEÚDO")
    logger.info("=" * 80)
    explicacao = (
        "1. Corpo Finito GF(2^128): O GHASH opera sobre o corpo de Galois GF(2^128) definido pelo "
        "polinômio irredutível P(x) = x^128 + x^7 + x^2 + x + 1. A adição em GF(2^128) equivale à "
        "operação lógica XOR bit a bit (⊕), e a multiplicação (•) é a multiplicação polinomial módulo P(x).\n"
        "2. Subchave de Hash (H): Antes de autenticar os blocos, o receptor/emissor deriva a subchave "
        "secreta de autenticação H = E_K(0^128) aplicando a cifra de bloco AES-256 sobre um bloco de 128 bits zeros.\n"
        "3. Polinômio de Autenticação GHASH(H, A, C): Os Dados Associados (A, de m blocos de 128 bits) e o "
        "Ciphertext (C, de n blocos de 128 bits: C_1, C_2, ..., C_n), seguidos de um bloco final L = [len(A)_64 || len(C)_64], "
        "formam os coeficientes de um polinômio avaliado em H (Esquema de Horner):\n"
        "     X_i = (X_{i-1} ⊕ B_i) • H  (mod P(x))\n"
        "     GHASH(H, A, C) = A_1•H^{m+n+1} ⊕ ... ⊕ C_i•H^{n-i+2} ⊕ ... ⊕ C_n•H^2 ⊕ L•H\n"
        "4. Geração da Authentication Tag (T): A saída do GHASH é mascarada cifrando o contador inicial J_0 = (Nonce_96 || 0^31 || 1):\n"
        "     T = GHASH(H, A, C) ⊕ E_K(J_0)\n"
        "5. Prova de Detecção de Bit-Flipping (Cenário 1): No modo CTR subjacente ao GCM, o texto cifrado é "
        "C_i = P_i ⊕ E_K(inc_32(J_0, i)). Se um adversário altera um único bit ou byte no bloco C_i para "
        "C'_i = C_i ⊕ Δ (com Δ ≠ 0), a propriedade linear do CTR faria o plaintext decifrado tornar-se P'_i = P_i ⊕ Δ. "
        "Contudo, no AES-GCM, a verificação da Tag ocorre ANTES da liberação do texto decifrado (princípio Encrypt-then-MAC). "
        "O verificador recalcula T' usando C'_i, obtendo uma diferença algébrica na Tag:\n"
        "     ΔT = T' ⊕ T = Δ • H^{n-i+2}  em GF(2^128)\n"
        "Como GF(2^128) é um corpo finito (domínio de integridade sem divisores de zero), para qualquer adulteração "
        "Δ ≠ 0 e H ≠ 0, o produto Δ • H^{n-i+2} é algebricamente diferente de zero (a menos que o atacante conheça H "
        "e forje múltiplos coeficientes simultaneamente para encontrar uma raiz do polinômio, cuja probabilidade sem "
        "conhecer H é limitada a (m+n+1)/2^128 ≈ 2^{-120}). Logo, T' ≠ T com probabilidade 1 - 2^{-128}, disparando `InvalidTag`.\n"
        "6. Prova de Detecção de Chave Incorreta (Cenário 2): Com uma chave incorreta K' ≠ K, tanto a subchave "
        "H' = E_{K'}(0^128) quanto o bloco de máscara E_{K'}(J_0) comportam-se como saídas pseudoaleatórias independentes (PRP). "
        "A probabilidade de colisão T' == T é de exatamente 2^{-128} (≈ 2,93 × 10^{-39}), garantindo rejeição imediata via `InvalidTag`."
    )
    for linha in explicacao.splitlines():
        logger.info("  %s", linha)


def executar_pipeline_parte1() -> int:
    """Função principal que orquestra todos os passos experimentais da Parte I."""
    logger = configurar_logger()
    logger.info("=" * 80)
    logger.info("INICIANDO AUDITORIA CRIPTOGRÁFICA - PARTE I: AES-256-GCM (AEAD)")
    logger.info("=" * 80)

    # Passo 1: Carregar documento comercial realista (contrato_xyzw.txt)
    logger.info("[PASSO 1] Carregamento e Inspeção Forense do Contrato Original")
    plaintext_original = carregar_documento(INPUT_FILE, logger)

    # Passo 2: Criptografar com AES-256-GCM (Chave 32B, Nonce 12B, Tag 16B)
    logger.info("-" * 80)
    logger.info("[PASSO 2] Cifragem Autenticada AES-256-GCM")
    chave_corporativa: bytes = AESGCM.generate_key(bit_length=KEY_SIZE_BITS)
    cifrar_documento_aes_gcm(
        plaintext=plaintext_original,
        chave=chave_corporativa,
        aad=AAD_DEFAULT,
        caminho_saida=ENCRYPTED_FILE,
        logger=logger,
    )

    # Passo 3: Descriptografia legítima a partir do arquivo salvo e conferência byte a byte
    logger.info("-" * 80)
    logger.info("[PASSO 3] Descriptografia Legítima e Conferência de Integridade Byte a Byte")
    dados_enc_disco = ENCRYPTED_FILE.read_bytes()
    pacote_lido = PacoteCriptograficoGCM.desserializar(dados_enc_disco, aad=AAD_DEFAULT)
    plaintext_recuperado = decifrar_documento_aes_gcm(
        pacote=pacote_lido,
        chave=chave_corporativa,
        logger=logger,
        caminho_recuperado=RECOVERED_FILE,
    )

    hash_original = calcular_sha256(plaintext_original)
    hash_recuperado = calcular_sha256(plaintext_recuperado)
    igualdade_bytes = plaintext_original == plaintext_recuperado

    logger.info("  -> Authentication Tag verificada : VÁLIDA (128 bits íntegros)")
    logger.info("  -> Comparação direta (bytes ==)  : %s (%d == %d bytes)",
                igualdade_bytes, len(plaintext_original), len(plaintext_recuperado))
    logger.info("  -> SHA-256 Original              : %s", hash_original)
    logger.info("  -> SHA-256 Recuperado            : %s", hash_recuperado)
    if not igualdade_bytes or hash_original != hash_recuperado:
        logger.error("Divergência detectada na recuperação do documento legítimo!")
        return 1
    logger.info("  -> [SUCESSO] Integridade e confidencialidade comprovadas sem perda de bits.")

    # Passo 4: Cenários de falha com tratamento de exceções (InvalidTag)
    ok_cenario_1, msg_1 = simular_adulteracao_ciphertext(pacote_lido, chave_corporativa, logger)
    ok_cenario_2, msg_2 = simular_chave_incorreta(pacote_lido, chave_corporativa, logger)

    # Passo 5: Explicação matemática detalhada do GHASH e síntese da auditoria
    exibir_explicacao_matematica_ghash(logger)

    logger.info("=" * 80)
    logger.info("RESUMO EXECUTIVO DOS TESTES DA PARTE I (AES-256-GCM)")
    logger.info("=" * 80)
    logger.info("  [1] Cifragem e Decifragem Legítima (Integridade Byte-a-Byte) : APROVADO")
    logger.info("  [2] Detecção de Bit-Flipping (1 byte alterado no Ciphertext) : %s (%s)",
                "APROVADO" if ok_cenario_1 else "FALHOU", msg_1)
    logger.info("  [3] Detecção de Chave Simétrica Incorreta (Chave Espúria)    : %s (%s)",
                "APROVADO" if ok_cenario_2 else "FALHOU", msg_2)
    logger.info("  [*] Log completo persistido em: %s", LOG_FILE.name)
    logger.info("=" * 80)

    return 0 if (ok_cenario_1 and ok_cenario_2) else 1


if __name__ == "__main__":
    sys.exit(executar_pipeline_parte1())

