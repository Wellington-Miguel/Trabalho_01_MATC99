# Trabalho 01 — Criptografia Aplicada: Proteção, Assinaturas Digitais e Certificados

**Disciplina:** MATC99 — Segurança e Auditoria de Sistemas de Informação  
**Professor:** Joselito Júnior  
**Instituição:** Universidade Federal da Bahia (UFBA) — Instituto de Computação  
**Aluno:** Wellington Miguel de Jesus Silva  
**Empresa Auditada (Cenário):** Miguelito Segurança e Tecnologia Ltda.  

---

## Sobre o Pacote de Experimentos (`.ZIP`)

Este arquivo `.ZIP` reúne todos os entregáveis práticos solicitados nos itens **B**, **C** e **D** da especificação do Trabalho 01 (o **Item A — Relatório Técnico em PDF** é enviado separadamente no campo próprio do formulário):

- **Item B (Scripts e logs utilizados nos experimentos):**
  - `parte1_aes_gcm.py` e `parte1_aes_gcm.log`
  - `parte2_pki_testes.sh` e `parte2_pki_testes.log`
- **Item C (Documentos fictícios, assinaturas, certificados e chaves públicas necessários à verificação):**
  - Contrato original (`contrato_miguelito.txt`), criptograma AES-256-GCM (`contrato_miguelito.enc`), contrato recuperado (`contrato_miguelito_recuperado.txt`) e contrato adulterado (`pki_miguelito/cenarios_auditoria/contrato_adulterado.txt`).
  - Assinaturas digitais (`cenario_a.sig` e `cenario_c_forjado.sig`).
  - Certificados X.509 v3 (`miguelito_root_ca.crt`, `parceiro.crt`, `rogue_root_ca.crt`, `parceiro_forjado.crt`).
  - Chaves públicas em formato PEM (`parceiro_pub.pem`, `parceiro_forjado_pub.pem`) e respectivos pares de chaves/CSRs/arquivos `.cnf`.
- **Item D (Instruções para reprodução dos procedimentos):**
  - Este documento (`README.md`).

---

## Pré-requisitos

Os scripts foram desenvolvidos e testados em ambiente Linux (Ubuntu 24.04 LTS via WSL2). Para reproduzir os experimentos, são necessários:

- **Python 3.10+** com a biblioteca `cryptography` instalada
- **OpenSSL 3.x**
- Utilitários padrão POSIX (`bash`, `sed`, `awk`, `sha256sum`, `wc`)

No Ubuntu/Debian (ou WSL), instale as dependências com:

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-cryptography openssl coreutils
```

Se preferir instalar a biblioteca Python via `pip`:

```bash
pip install cryptography
```

---

## Instruções para Reprodução dos Procedimentos

### 1. Reproduzindo a Parte I (Proteção e Integridade com AES-256-GCM)

Na pasta raiz onde o `.ZIP` foi extraído, execute:

```bash
python3 parte1_aes_gcm.py
```

**O que o script executa:**
1. Carrega o documento comercial fictício `contrato_miguelito.txt` (`2.841 bytes`) e calcula seu hash SHA-256.
2. Criptografa o documento com **AES-256-GCM** (chave de 32 bytes, Nonce de 12 bytes e Tag de 16 bytes), gravando `contrato_miguelito.enc` (`2.869 bytes`).
3. Descriptografa `contrato_miguelito.enc` com a chave correta, salvando `contrato_miguelito_recuperado.txt` e comprovando integridade byte a byte (`original == recuperado: True`).
4. Executa os dois testes de falha exigidos (adulteração de 1 byte no *ciphertext* no offset `1420` e tentativa de decifragem com chave incorreta), capturando a exceção `cryptography.exceptions.InvalidTag` e gravando o log em `parte1_aes_gcm.log`.

---

### 2. Reproduzindo a Parte II (Assinaturas Digitais e Certificados X.509)

Para executar a automação completa da Parte II (que recria as CAs, emite os certificados e roda os Cenários A, B e C), execute:

```bash
chmod +x parte2_pki_testes.sh
./parte2_pki_testes.sh
```

> **Observação (Windows/WSL):** Caso o script tenha sido editado no Windows com quebras de linha `CRLF`, converta-o para `LF` antes da execução:
> ```bash
> sed -i 's/\r$//' parte2_pki_testes.sh && ./parte2_pki_testes.sh
> ```

---

### 3. Verificação Manual Direta dos Artefatos Já Gerados (Cenários A, B e C)

Caso deseje apenas conferir diretamente as assinaturas, certificados e chaves públicas já incluídos na pasta `pki_miguelito/` sem sobrescrevê-los:

#### Cenário A — Documento original, assinado corretamente e com certificado confiável (Decisão: ACEITAR)
```bash
# 1. Verificar assinatura digital com a chave pública do parceiro legítimo (Esperado: Verified OK)
openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_a.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 2. Validar cadeia de certificação contra a Miguelito Root CA (Esperado: parceiro.crt: OK)
openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_legitimo/parceiro.crt
```

#### Cenário B — Documento alterado após a assinatura (Decisão: REJEITAR)
```bash
# Verificar assinatura original contra o contrato com valor adulterado (Esperado: Verification failure)
openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_a.sig \
    pki_miguelito/cenarios_auditoria/contrato_adulterado.txt
```

#### Cenário C — Assinatura matematicamente válida, mas certificado emitido por CA não confiável (Decisão: REJEITAR)
```bash
# 1. Verificar assinatura com a chave pública do certificado forjado (Esperado: Verified OK)
openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_c_forjado.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 2. Validar cadeia do certificado forjado contra a Miguelito Root CA
# (Esperado: error 20 at 0 depth lookup: unable to get local issuer certificate)
openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_forjado/parceiro_forjado.crt
```

---

## Estrutura de Arquivos Contidos no `.ZIP`

```text
Trabalho_01_MATC99.zip
├── README.md                                   # Instruções para reprodução dos procedimentos (Item D)
├── contrato_miguelito.txt                      # Documento comercial fictício original (Item C)
├── contrato_miguelito.enc                      # Contrato criptografado com AES-256-GCM (Item C)
├── contrato_miguelito_recuperado.txt           # Contrato recuperado após descriptografia (Item C)
├── parte1_aes_gcm.py                           # Script Python dos experimentos da Parte I (Item B)
├── parte1_aes_gcm.log                          # Evidências e logs de execução da Parte I (Item B)
├── parte2_pki_testes.sh                        # Script Bash/OpenSSL dos experimentos da Parte II (Item B)
├── parte2_pki_testes.log                       # Evidências e logs de execução da Parte II (Item B)
└── pki_miguelito/                              # Certificados, chaves públicas e assinaturas (Item C)
    ├── root_ca/
    │   ├── root_ca.cnf                         # Configuração OpenSSL da Miguelito Root CA
    │   ├── miguelito_root_ca.key               # Chave privada RSA 4096 bits da CA confiável
    │   ├── miguelito_root_ca.crt               # Certificado autoassinado da Miguelito Root CA
    │   └── miguelito_root_ca.srl               # Controle de número de série da CA
    ├── parceiro_legitimo/
    │   ├── parceiro.cnf                        # Configuração X.509 v3 do parceiro legítimo
    │   ├── parceiro.key                        # Chave privada RSA 2048 bits do parceiro legítimo
    │   ├── parceiro.csr                        # Requisição de assinatura (CSR) do parceiro
    │   ├── parceiro.crt                        # Certificado legítimo assinado pela Miguelito Root CA
    │   └── parceiro_pub.pem                    # Chave pública do parceiro legítimo
    ├── rogue_ca/
    │   ├── rogue_ca.cnf                        # Configuração da CA não confiável (Rogue CA)
    │   ├── rogue_root_ca.key                   # Chave privada RSA 4096 bits da Rogue CA
    │   ├── rogue_root_ca.crt                   # Certificado autoassinado da Rogue CA
    │   └── rogue_root_ca.srl                   # Controle de número de série da Rogue CA
    ├── parceiro_forjado/
    │   ├── parceiro_forjado.key                # Chave privada RSA 2048 bits falsa
    │   ├── parceiro_forjado.csr                # CSR falso em nome do parceiro
    │   ├── parceiro_forjado.crt                # Certificado falso emitido pela Rogue CA
    │   └── parceiro_forjado_pub.pem            # Chave pública extraída do certificado falso
    └── cenarios_auditoria/
        ├── contrato_miguelito.txt              # Documento original assinado nos Cenários A e C
        ├── contrato_adulterado.txt             # Documento alterado após a assinatura (Cenário B)
        ├── cenario_a.sig                       # Assinatura digital legítima (Cenário A)
        └── cenario_c_forjado.sig               # Assinatura digital com certificado falso (Cenário C)
```
