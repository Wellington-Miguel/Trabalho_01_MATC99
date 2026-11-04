# Trabalho 01 — Criptografia Aplicada: Proteção, Assinaturas Digitais e Certificados

**Disciplina:** MATC99 — Segurança e Auditoria de Sistemas de Informação  
**Instituição:** Universidade Federal da Bahia (UFBA) — Instituto de Computação  
**Cenário Auditado:** XYZW Tecnologia e Soluções Digitais S.A.  

---

## 1. Visão Geral do Projeto

Este repositório contém a implementação experimental, os artefatos criptográficos, os logs forenses e o relatório técnico completo referentes à auditoria de segurança da **XYZW Tecnologia**. O projeto valida controles criptográficos divididos em dois módulos:

1. **Parte I (`parte1_aes_gcm.py`):** Confidencialidade, integridade e autenticidade de conteúdo utilizando a cifra simétrica autenticada **AES-256-GCM (AEAD)** padronizada pelo **NIST SP 800-38D**, com Nonce CSPRNG de 96 bits (12 bytes), Dados Associados (AAD) e Authentication Tag de 128 bits (16 bytes), incluindo provas experimentais de rejeição contra ataques de *bit-flipping* no ciphertext e tentativa de decifragem com chave simétrica espúria (`cryptography.exceptions.InvalidTag`).
2. **Parte II (`parte2_pki_testes.sh`):** Não-repúdio, integridade documental e autenticidade de identidade mediante **Infraestrutura de Chaves Públicas (PKI / X.509 v3)** e assinaturas digitais **RSA-SHA256** utilizando **OpenSSL 3.x**, cobrindo a emissão de uma CA Raiz Corporativa (`XYZW Root CA`, RSA 4096 bits), certificado de entidade final legítima (`parceiro.xyzw.com`, RSA 2048 bits), CA atacante (`Rogue CA`) e avaliação forense dos **Cenários A (ACEITAR)**, **B (REJEITAR — `Verification failure`)** e **C (REJEITAR — `error 20 at 0 depth lookup: unable to get local issuer certificate`)**.

---

## 2. Pré-Requisitos do Ambiente

Para reproduzir integralmente os experimentos em ambiente **Linux (Ubuntu/Debian)** ou **WSL2 (Windows Subsystem for Linux)**:

- **Sistema Operacional:** Linux Kernel 6.x / Ubuntu 24.04 LTS (ou WSL2 equivalente)
- **Python:** `Python >= 3.10` (testado em Python 3.12.3 e Python 3.13.14)
- **Biblioteca Python `cryptography`:** `cryptography >= 41.0.0`
- **OpenSSL CLI:** `OpenSSL >= 3.0.0` (testado em OpenSSL 3.0.13)
- **Utilitários POSIX padrão:** `bash`, `sed`, `awk`, `sha256sum`, `wc`, `chmod`

### Instalação de Dependências (Ubuntu / Debian / WSL)

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-cryptography openssl coreutils
```

Caso utilize ambiente virtual Python (`venv`) ou instalação via `pip`:

```bash
pip install cryptography
```

---

## 3. Instruções Exatas para Reprodução Experimental

### Passo 1: Executar a Parte I (Proteção e Integridade com AES-256-GCM)

No terminal Linux/WSL, dentro do diretório raiz do projeto:

```bash
python3 parte1_aes_gcm.py
```

**Saídas geradas pela Parte I:**
- `contrato_xyzw.enc`: Criptograma binário estruturado como `Nonce (12 bytes) || Ciphertext (3621 bytes) || Tag (16 bytes)`, totalizando `3649 bytes`.
- `contrato_xyzw_recuperado.txt`: Documento decifrado e verificado byte a byte contra `contrato_xyzw.txt`.
- `parte1_aes_gcm.log`: Log forense detalhado com timestamps em milissegundos, hashes SHA-256 e captura das exceções `cryptography.exceptions.InvalidTag`.

### Passo 2: Executar a Parte II (PKI, Assinaturas Digitais e Cadeia X.509)

Conceda permissão de execução ao script Bash e execute-o:

```bash
chmod +x parte2_pki_testes.sh
./parte2_pki_testes.sh
```

> **Nota para usuários Windows/WSL:** Caso o arquivo `parte2_pki_testes.sh` tenha sido editado no Windows com quebras de linha CRLF, normalize para LF antes de executar:
> ```bash
> sed -i 's/\r$//' parte2_pki_testes.sh && ./parte2_pki_testes.sh
> ```

**Saídas geradas pela Parte II:**
- Diretório `pki_xyzw/` contendo toda a hierarquia de chaves, CSRs, certificados X.509 v3 e assinaturas dos Cenários A, B e C.
- `parte2_pki_testes.log`: Log de auditoria consolidado com as saídas exatas do OpenSSL (`Verified OK`, `Verification failure`, `error 20 at 0 depth lookup: unable to get local issuer certificate`).

---

## 4. Árvore de Diretórios do Projeto (Estrutura para Empacotamento `.ZIP`)

Abaixo encontra-se a estrutura completa do pacote de entrega (`Trabalho_01_MATC99.zip`):

```text
Trabalho_01_MATC99/
├── README.md                                   # Instruções de uso, dependências e arquitetura do projeto
├── RELATORIO_TECNICO_MATC99.md                 # Relatório Técnico Completo (Seções 1 a 8 + Resposta Google Forms)
├── contrato_xyzw.txt                           # Documento contratual comercial original (Plaintext - 3621 bytes)
├── contrato_xyzw.enc                           # Criptograma AEAD gerado (12B Nonce + 3621B Ciphertext + 16B Tag)
├── contrato_xyzw_recuperado.txt                # Contrato recuperado após decifragem e validação da Tag GCM
├── parte1_aes_gcm.py                           # Script Python modular (AES-256-GCM, Bit-Flipping e Chave Espúria)
├── parte1_aes_gcm.log                          # Evidências e logs de execução da Parte I com timestamps
├── parte2_pki_testes.sh                        # Script Bash idempotente de automação da PKI e Cenários A, B e C
├── parte2_pki_testes.log                       # Evidências e logs de execução da Parte II (OpenSSL 3.x)
└── pki_xyzw/                                   # Artefatos gerados pela Infraestrutura de Chaves Públicas
    ├── root_ca/
    │   ├── openssl_root_ca.cnf                 # Configuração X.509 v3 da XYZW Root CA (CA:true, pathlen:0)
    │   ├── xyzw_root_ca.key                    # Chave privada RSA 4096 bits da Root CA legítima
    │   ├── xyzw_root_ca.crt                    # Certificado autoassinado da XYZW Root CA (Trust Anchor)
    │   └── xyzw_root_ca.srl                    # Controle de número de série da XYZW Root CA
    ├── parceiro_legitimo/
    │   ├── openssl_parceiro.cnf                # Configuração X.509 v3 de entidade final (SAN DNS:parceiro.xyzw.com)
    │   ├── parceiro.key                        # Chave privada RSA 2048 bits do parceiro legítimo
    │   ├── parceiro.csr                        # Requisição de Assinatura de Certificado (CSR) legítima
    │   ├── parceiro.crt                        # Certificado legítimo assinado pela XYZW Root CA
    │   └── parceiro_pub.pem                    # Chave pública extraída do certificado legítimo
    ├── rogue_ca/
    │   ├── openssl_rogue_ca.cnf                # Configuração X.509 v3 da Autoridade Certificadora Atacante
    │   ├── rogue_root_ca.key                   # Chave privada RSA 4096 bits da Rogue CA
    │   ├── rogue_root_ca.crt                   # Certificado autoassinado da Rogue CA (Não confiável)
    │   └── rogue_root_ca.srl                   # Controle de número de série da Rogue CA
    ├── parceiro_forjado/
    │   ├── parceiro_forjado.key                # Chave privada RSA 2048 bits do atacante
    │   ├── parceiro_forjado.csr                # CSR forjado com CN=parceiro.xyzw.com
    │   ├── parceiro_forjado.crt                # Certificado forjado assinado pela Rogue CA
    │   └── parceiro_forjado_pub.pem            # Chave pública extraída do certificado forjado
    └── cenarios_auditoria/
        ├── contrato_xyzw.txt                   # Cópia íntegra do contrato utilizada nos Cenários A e C
        ├── contrato_xyzw_adulterado.txt        # Contrato fraudado no Cenário B (parcela alterada em 1 byte)
        ├── cenario_a_contrato.sig              # Assinatura RSA-SHA256 legítima (256 bytes)
        └── cenario_c_contrato_forjado.sig      # Assinatura RSA-SHA256 gerada com a chave forjada (256 bytes)
```

---

## 5. Comando para Empacotamento em `.ZIP`

Para gerar o arquivo `.zip` de submissão contendo todos os códigos-fonte, certificados, assinaturas, logs e relatório técnico:

```bash
zip -r Trabalho_01_MATC99.zip \
    README.md \
    RELATORIO_TECNICO_MATC99.md \
    contrato_xyzw.txt \
    contrato_xyzw.enc \
    contrato_xyzw_recuperado.txt \
    parte1_aes_gcm.py \
    parte1_aes_gcm.log \
    parte2_pki_testes.sh \
    parte2_pki_testes.log \
    pki_xyzw/
```

