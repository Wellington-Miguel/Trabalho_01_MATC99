# Trabalho 01 — Criptografia Aplicada: Proteção, Assinaturas Digitais e Certificados

**Disciplina:** MATC99 — Segurança e Auditoria de Sistemas de Informação  
**Instituição:** Universidade Federal da Bahia (UFBA) — Instituto de Computação  
**Empresa Auditada (Cenário):** Miguelito Segurança e Tecnologia Ltda.  

---

## Sobre o Trabalho

Este repositório reúne os códigos, certificados, logs de execução e o relatório técnico do Trabalho 01 da disciplina MATC99. O objetivo foi simular uma auditoria prática sobre os fluxos de troca de contratos digitais da empresa **Miguelito Segurança e Tecnologia**, validando controles criptográficos em duas partes:

1. **Parte I (`parte1_aes_gcm.py`):** Cifragem e validação de integridade do contrato comercial (`contrato_xyzw.txt`) usando **AES-256-GCM** (com Nonce de 12 bytes e Authentication Tag de 16 bytes), além dos testes de falha para adulteração de 1 byte no texto cifrado (*bit-flipping*) e tentativa de leitura com chave incorreta (`InvalidTag`).
2. **Parte II (`parte2_pki_testes.sh`):** Estruturação de uma PKI local com OpenSSL contendo a autoridade raiz interna da empresa (`Miguelito Root CA`, RSA 4096 bits), emissão do certificado legítimo do parceiro comercial (`parceiro.miguelito.com.br`), criação de uma CA paralela não autorizada (`Rogue CA`) e bateria de testes para os Cenários A, B e C.

---

## Pré-requisitos

Os scripts foram desenvolvidos e testados em ambiente Linux (Ubuntu 24.04 via WSL2). Para rodar os testes, você vai precisar de:

- **Python 3.10+** com o pacote `cryptography` instalado
- **OpenSSL 3.x**
- Utilitários padrão do ambiente Linux (`bash`, `sed`, `awk`, `sha256sum`, `wc`)

No Ubuntu/Debian (ou WSL), basta instalar os pacotes com:

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-cryptography openssl coreutils
```

Se preferir instalar a biblioteca Python via `pip`:

```bash
pip install cryptography
```

---

## Como Executar os Testes

### 1. Rodando a Parte I (AES-256-GCM)

Na pasta raiz do projeto, execute:

```bash
python3 parte1_aes_gcm.py
```

O script vai ler o `contrato_miguelito.txt`, gerar o arquivo cifrado `contrato_miguelito.enc` (contendo `Nonce + Ciphertext + Tag`), recuperar o documento em `contrato_miguelito_recuperado.txt` conferindo o hash SHA-256, simular os dois casos de falha (`InvalidTag`) e salvar toda a saída em `parte1_aes_gcm.log`.

### 2. Rodando a Parte II (PKI e Assinaturas com OpenSSL)

Dê permissão de execução ao script Bash e rode:

```bash
chmod +x parte2_pki_testes.sh
./parte2_pki_testes.sh
```

> **Observação (Windows/WSL):** Se o script tiver sido salvo com fim de linha padrão Windows (`CRLF`), converta para `LF` antes de rodar:
> ```bash
> sed -i 's/\r$//' parte2_pki_testes.sh && ./parte2_pki_testes.sh
> ```

O script recria do zero a pasta `pki_miguelito/` com todas as chaves, certificados e assinaturas, exibindo no terminal (e salvando em `parte2_pki_testes.log`) os resultados dos Cenários A, B e C.

---

## Estrutura de Diretórios do Projeto

A organização dos arquivos para entrega no pacote `.ZIP` segue a estrutura abaixo:

```text
Trabalho_01_MATC99/
├── README.md                                   # Instruções de execução e organização dos arquivos
├── RELATORIO_TECNICO_MATC99.md                 # Relatório técnico completo (Seções 1 a 8 + texto do Forms)
├── contrato_miguelito.txt                      # Contrato comercial base da Miguelito Segurança e Tecnologia
├── contrato_miguelito.enc                      # Arquivo cifrado pelo AES-256-GCM (12B Nonce + CT + 16B Tag)
├── contrato_miguelito_recuperado.txt           # Contrato recuperado após decifragem legítima
├── parte1_aes_gcm.py                           # Script Python da Parte I (AES-256-GCM e testes de falha)
├── parte1_aes_gcm.log                          # Log de execução da Parte I com timestamps
├── parte2_pki_testes.sh                        # Script Bash da Parte II (PKI OpenSSL e Cenários A, B e C)
├── parte2_pki_testes.log                       # Log de execução da Parte II
└── pki_miguelito/                              # Diretório gerado pelo script da Parte II
    ├── root_ca/
    │   ├── root_ca.cnf                         # Configuração OpenSSL da Miguelito Root CA
    │   ├── miguelito_root_ca.key               # Chave privada RSA 4096 bits da CA interna
    │   ├── miguelito_root_ca.crt               # Certificado autoassinado da Miguelito Root CA
    │   └── miguelito_root_ca.srl               # Controle de serial da CA
    ├── parceiro_legitimo/
    │   ├── parceiro.cnf                        # Configuração X.509 v3 do parceiro comercial
    │   ├── parceiro.key                        # Chave privada RSA 2048 bits do parceiro legítimo
    │   ├── parceiro.csr                        # CSR do parceiro legítimo
    │   ├── parceiro.crt                        # Certificado assinado pela Miguelito Root CA
    │   └── parceiro_pub.pem                    # Chave pública extraída do certificado legítimo
    ├── rogue_ca/
    │   ├── rogue_ca.cnf                        # Configuração da CA não confiável (Rogue CA)
    │   ├── rogue_root_ca.key                   # Chave privada RSA 4096 bits da Rogue CA
    │   ├── rogue_root_ca.crt                   # Certificado autoassinado da Rogue CA
    │   └── rogue_root_ca.srl                   # Controle de serial da Rogue CA
    ├── parceiro_forjado/
    │   ├── parceiro_forjado.key                # Chave privada RSA 2048 bits usada pelo atacante
    │   ├── parceiro_forjado.csr                # CSR falso com o mesmo CN do parceiro
    │   ├── parceiro_forjado.crt                # Certificado forjado assinado pela Rogue CA
    │   └── parceiro_forjado_pub.pem            # Chave pública extraída do certificado forjado
    └── cenarios_auditoria/
        ├── contrato_miguelito.txt              # Cópia do contrato original usada nos testes A e C
        ├── contrato_adulterado.txt             # Contrato com valor da parcela adulterado (Cenário B)
        ├── cenario_a.sig                       # Assinatura RSA-SHA256 legítima (256 bytes)
        └── cenario_c_forjado.sig               # Assinatura RSA-SHA256 gerada com a chave falsa
```

---

## Gerando o Arquivo `.ZIP` para Entrega

Para compactar todos os arquivos necessários em um único `.zip`:

```bash
zip -r Trabalho_01_MATC99.zip \
    README.md \
    RELATORIO_TECNICO_MATC99.md \
    contrato_miguelito.txt \
    contrato_miguelito.enc \
    contrato_miguelito_recuperado.txt \
    parte1_aes_gcm.py \
    parte1_aes_gcm.log \
    parte2_pki_testes.sh \
    parte2_pki_testes.log \
    pki_miguelito/
```
