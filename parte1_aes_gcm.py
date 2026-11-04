#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UFBA - Instituto de Computação
Disciplina: MATC99 - Segurança e Auditoria de Sistemas de Informação
Trabalho 01 - Parte I: Proteção e Integridade com AES-256-GCM

Script para testar a cifragem autenticada (AEAD) do contrato comercial da
Miguelito Segurança e Tecnologia e validar o comportamento do algoritmo
diante de adulteração de bytes no texto cifrado e uso de chave incorreta.
"""

import hashlib
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Parâmetros recomendados pelo NIST SP 800-38D para AES-GCM
TAM_CHAVE_BITS = 256
TAM_CHAVE_BYTES = TAM_CHAVE_BITS // 8  # 32 bytes
TAM_NONCE_BYTES = 12                   # 96 bits
TAM_TAG_BYTES = 16                     # 128 bits

# Dados associados (AAD): autenticados no GHASH, mas não cifrados
AAD_PADRAO = b"MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849"

DIR_BASE = Path(__file__).resolve().parent
ARQ_CONTRATO = DIR_BASE / "contrato_miguelito.txt"
ARQ_CIFRADO = DIR_BASE / "contrato_miguelito.enc"
ARQ_RECUPERADO = DIR_BASE / "contrato_miguelito_recuperado.txt"
ARQ_LOG = DIR_BASE / "parte1_aes_gcm.log"


@dataclass
class CriptogramaGCM:
    """
    Representa os componentes gerados pelo AES-GCM.
    O método encrypt() da biblioteca cryptography devolve (ciphertext + tag)
    concatenados. Aqui separamos os campos para facilitar a inspeção e
    salvar no arquivo .enc no formato: Nonce (12B) + Ciphertext + Tag (16B).
    """
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    aad: bytes

    @property
    def dados_com_tag(self) -> bytes:
        return self.ciphertext + self.tag

    def empacotar(self) -> bytes:
        return self.nonce + self.ciphertext + self.tag

    @classmethod
    def desempacotar(cls, bruto: bytes, aad: bytes = AAD_PADRAO) -> "CriptogramaGCM":
        min_bytes = TAM_NONCE_BYTES + TAM_TAG_BYTES
        if len(bruto) < min_bytes:
            raise ValueError(f"Arquivo .enc menor que o tamanho mínimo esperado ({min_bytes} bytes).")

        nonce = bruto[:TAM_NONCE_BYTES]
        ciphertext = bruto[TAM_NONCE_BYTES:-TAM_TAG_BYTES]
        tag = bruto[-TAM_TAG_BYTES:]
        return cls(nonce=nonce, ciphertext=ciphertext, tag=tag, aad=aad)


def iniciar_logger() -> logging.Logger:
    logger = logging.getLogger("parte1_gcm")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    h_console = logging.StreamHandler(sys.stdout)
    h_console.setFormatter(fmt)

    h_arquivo = logging.FileHandler(ARQ_LOG, mode="w", encoding="utf-8")
    h_arquivo.setFormatter(fmt)

    logger.addHandler(h_console)
    logger.addHandler(h_arquivo)
    return logger


def sha256_hex(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def ler_contrato(caminho: Path, log: logging.Logger) -> bytes:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    dados = caminho.read_bytes()
    log.info("Contrato carregado: %s (%d bytes)", caminho.name, len(dados))
    log.info("SHA-256 original: %s", sha256_hex(dados))
    return dados


def cifrar_contrato(
    plaintext: bytes,
    chave: bytes,
    aad: bytes,
    destino: Path,
    log: logging.Logger,
) -> CriptogramaGCM:
    """Cifra o texto em claro usando AES-256-GCM e grava o resultado em disco."""
    nonce = os.urandom(TAM_NONCE_BYTES)
    aesgcm = AESGCM(chave)

    # Na cryptography, os últimos 16 bytes do retorno correspondem à tag GHASH
    saida_aead = aesgcm.encrypt(nonce=nonce, data=plaintext, associated_data=aad)
    ciphertext = saida_aead[:-TAM_TAG_BYTES]
    tag = saida_aead[-TAM_TAG_BYTES:]

    pacote = CriptogramaGCM(nonce=nonce, ciphertext=ciphertext, tag=tag, aad=aad)
    bytes_finais = pacote.empacotar()
    destino.write_bytes(bytes_finais)

    log.info("Arquivo cifrado salvo em: %s (%d bytes totais)", destino.name, len(bytes_finais))
    log.info("  Chave AES-256 (32B) : %s", chave.hex())
    log.info("  Nonce / IV (12B)    : %s", nonce.hex())
    log.info("  AAD                 : %s", aad.decode("utf-8"))
    log.info("  Ciphertext          : %d bytes", len(ciphertext))
    log.info("  Auth Tag (16B)      : %s", tag.hex())
    log.info("  SHA-256 (.enc)      : %s", sha256_hex(bytes_finais))
    return pacote


def decifrar_contrato(
    pacote: CriptogramaGCM,
    chave: bytes,
    saida_opcional: Optional[Path] = None,
) -> bytes:
    """
    Decifra o pacote e verifica a Authentication Tag.
    Se a tag calculada não bater com a recebida, AESGCM.decrypt levanta InvalidTag.
    """
    aesgcm = AESGCM(chave)
    texto_recuperado = aesgcm.decrypt(
        nonce=pacote.nonce,
        data=pacote.dados_com_tag,
        associated_data=pacote.aad,
    )
    if saida_opcional:
        saida_opcional.write_bytes(texto_recuperado)
    return texto_recuperado


def teste_adulteracao_ciphertext(
    pacote_valido: CriptogramaGCM,
    chave: bytes,
    log: logging.Logger,
) -> Tuple[bool, str]:
    """
    Simula um ataque de bit-flipping invertendo 1 bit no meio do ciphertext.
    Como o modo CTR puro é maleável, quem barra essa alteração no GCM é o GHASH.
    """
    log.info("--- [Teste de Falha 1: Adulteração de 1 byte no Ciphertext (Bit-Flipping)] ---")

    ct_alterado = bytearray(pacote_valido.ciphertext)
    pos = len(ct_alterado) // 2
    valor_antes = ct_alterado[pos]
    valor_depois = valor_antes ^ 0x01  # inverte o bit menos significativo
    ct_alterado[pos] = valor_depois

    pacote_corrompido = CriptogramaGCM(
        nonce=pacote_valido.nonce,
        ciphertext=bytes(ct_alterado),
        tag=pacote_valido.tag,
        aad=pacote_valido.aad,
    )

    log.info("Byte modificado no offset %d (0x%04X): 0x%02X -> 0x%02X", pos, pos, valor_antes, valor_depois)

    try:
        decifrar_contrato(pacote_corrompido, chave)
        log.error("ERRO: O ciphertext adulterado foi decifrado sem levantar exceção!")
        return False, "Nenhuma exceção lançada"
    except InvalidTag as erro:
        nome_excecao = f"{erro.__class__.__module__}.{erro.__class__.__name__}"
        log.warning("Exceção capturada com sucesso: %s", nome_excecao)
        log.info(
            "Motivo: A alteração no bloco cifrado mudou o resultado do polinômio GHASH em GF(2^128). "
            "Como a tag recalculada divergiu da tag original, a decifragem foi abortada."
        )
        return True, nome_excecao


def teste_chave_incorreta(
    pacote_valido: CriptogramaGCM,
    chave_correta: bytes,
    log: logging.Logger,
) -> Tuple[bool, str]:
    """Tenta decifrar o arquivo .enc utilizando outra chave de 256 bits."""
    log.info("--- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---")

    chave_errada = AESGCM.generate_key(bit_length=TAM_CHAVE_BITS)
    while chave_errada == chave_correta:
        chave_errada = AESGCM.generate_key(bit_length=TAM_CHAVE_BITS)

    log.info("Chave correta : %s", chave_correta.hex())
    log.info("Chave errada  : %s", chave_errada.hex())

    try:
        decifrar_contrato(pacote_valido, chave_errada)
        log.error("ERRO: A chave incorreta decifrou o pacote sem erro!")
        return False, "Nenhuma exceção lançada"
    except InvalidTag as erro:
        nome_excecao = f"{erro.__class__.__module__}.{erro.__class__.__name__}"
        log.warning("Exceção capturada com sucesso: %s", nome_excecao)
        log.info(
            "Motivo: Com uma chave K' diferente, tanto a subchave do GHASH H' = E_K'(0^128) "
            "quanto o bloco cifrado do contador inicial E_K'(J0) mudam completamente, invalidando a tag."
        )
        return True, nome_excecao


def registrar_resumo_ghash(log: logging.Logger) -> None:
    log.info("--- [Nota Técnica: Por que o GHASH detecta alterações no Ciphertext] ---")
    log.info(
        "No AES-GCM, os blocos do AAD e do texto cifrado C_1..C_n funcionam como coeficientes de um "
        "polinômio avaliado na subchave secreta H = E_K(0^128) dentro do corpo finito GF(2^128), "
        "definido pelo polinômio irredutível P(x) = x^128 + x^7 + x^2 + x + 1."
    )
    log.info(
        "Se um byte do bloco C_i sofre uma alteração Delta != 0 (C'_i = C_i XOR Delta), a diferença "
        "entre a tag recalculada T' e a tag original T será Delta_T = Delta * H^(n - i + 2) mod P(x). "
        "Como em um corpo finito não há divisores de zero, para Delta != 0 e H != 0 o produto nunca "
        "é zero, garantindo T' != T e disparando InvalidTag antes de entregar qualquer dado."
    )


def main() -> int:
    log = iniciar_logger()
    log.info("=== Auditoria Criptográfica - Miguelito Segurança e Tecnologia (Parte I: AES-256-GCM) ===")

    # 1. Leitura do contrato comercial
    log.info("[Passo 1] Carregando o contrato original...")
    texto_original = ler_contrato(ARQ_CONTRATO, log)

    # 2. Cifragem com AES-256-GCM
    log.info("[Passo 2] Cifrando o documento com AES-256-GCM...")
    chave_simetrica = AESGCM.generate_key(bit_length=TAM_CHAVE_BITS)
    cifrar_contrato(
        plaintext=texto_original,
        chave=chave_simetrica,
        aad=AAD_PADRAO,
        destino=ARQ_CIFRADO,
        log=log,
    )

    # 3. Leitura do arquivo .enc e decifragem legítima
    log.info("[Passo 3] Lendo o arquivo .enc e validando a recuperação do documento...")
    dados_disco = ARQ_CIFRADO.read_bytes()
    pacote_lido = CriptogramaGCM.desempacotar(dados_disco, aad=AAD_PADRAO)
    texto_recuperado = decifrar_contrato(pacote_lido, chave_simetrica, saida_opcional=ARQ_RECUPERADO)

    mesmo_conteudo = (texto_original == texto_recuperado)
    log.info("Comparação de bytes (original == recuperado): %s (%d bytes)", mesmo_conteudo, len(texto_recuperado))
    log.info("SHA-256 recuperado: %s", sha256_hex(texto_recuperado))

    if not mesmo_conteudo:
        log.error("Falha na conferência de integridade do arquivo recuperado!")
        return 1

    # 4. Testes dos cenários de falha
    ok_bitflip, exc_1 = teste_adulteracao_ciphertext(pacote_lido, chave_simetrica, log)
    ok_chave, exc_2 = teste_chave_incorreta(pacote_lido, chave_simetrica, log)

    # 5. Explicação matemática do GHASH no log
    registrar_resumo_ghash(log)

    log.info("=== Resumo dos Testes (Parte I) ===")
    log.info("1. Decifragem legítima e conferência de bytes : OK")
    log.info("2. Bloqueio de ciphertext adulterado (1 byte) : %s (%s)", "OK" if ok_bitflip else "FALHA", exc_1)
    log.info("3. Bloqueio de chave simétrica incorreta      : %s (%s)", "OK" if ok_chave else "FALHA", exc_2)
    return 0 if (ok_bitflip and ok_chave) else 1


if __name__ == "__main__":
    sys.exit(main())
