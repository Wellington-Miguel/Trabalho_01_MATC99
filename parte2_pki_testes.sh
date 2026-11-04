#!/usr/bin/env bash
# ==============================================================================
# UFBA - Instituto de Computação
# Disciplina: MATC99 - Segurança e Auditoria de Sistemas de Informação
# Trabalho 01 - Parte II: PKI, Assinaturas Digitais e Cadeia de Certificação
# Empresa Auditada: Miguelito Segurança e Tecnologia Ltda.
# ==============================================================================
# Este script cria a estrutura de diretórios da PKI de testes, gera a Root CA
# da Miguelito Segurança e Tecnologia (RSA 4096 bits), emite o certificado do
# parceiro legítimo, cria uma CA não confiável (Rogue CA) com certificado falso
# e executa os Cenários A, B e C pedidos na especificação do trabalho.
# ==============================================================================

set -euo pipefail

DIR_ATUAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKI_DIR="${DIR_ATUAL}/pki_miguelito"
CA_RAIZ_DIR="${PKI_DIR}/root_ca"
PARCEIRO_DIR="${PKI_DIR}/parceiro_legitimo"
ROGUE_DIR="${PKI_DIR}/rogue_ca"
FALSO_DIR="${PKI_DIR}/parceiro_forjado"
CENARIOS_DIR="${PKI_DIR}/cenarios_auditoria"

ARQ_LOG="${DIR_ATUAL}/parte2_pki_testes.log"
CONTRATO_BASE="${DIR_ATUAL}/contrato_miguelito.txt"

registrar_log() {
    local nivel="$1"
    shift
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S.%3N')"
    echo "[${ts}] [${nivel}] $*" | tee -a "${ARQ_LOG}"
}

# Limpa artefatos de execuções anteriores (incluindo pasta antiga caso exista) para rodar do zero
rm -rf "${PKI_DIR}" "${DIR_ATUAL}/pki_xyzw" "${ARQ_LOG}"
mkdir -p "${CA_RAIZ_DIR}" "${PARCEIRO_DIR}" "${ROGUE_DIR}" "${FALSO_DIR}" "${CENARIOS_DIR}"

registrar_log "INFO" "=== Iniciando Testes de PKI e Assinatura Digital - Miguelito Segurança e Tecnologia ==="
registrar_log "INFO" "Ambiente OpenSSL: $(openssl version)"

if [[ ! -f "${CONTRATO_BASE}" ]]; then
    registrar_log "ERRO" "Arquivo ${CONTRATO_BASE} não encontrado no diretório."
    exit 1
fi
cp "${CONTRATO_BASE}" "${CENARIOS_DIR}/contrato_miguelito.txt"

# 1. Criação da Root CA legítima (Miguelito Root CA) - RSA 4096 bits
registrar_log "INFO" "[Passo 1] Configurando a Root CA interna (Miguelito Root CA - RSA 4096 bits)..."

cat > "${CA_RAIZ_DIR}/root_ca.cnf" << 'EOF'
[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
x509_extensions     = v3_ca

[ dn ]
C                   = BR
ST                  = Bahia
L                   = Salvador
O                   = Miguelito Seguranca e Tecnologia Ltda
OU                  = Seguranca da Informacao e PKI Interna
CN                  = Miguelito Root CA

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true, pathlen:0
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign
EOF

openssl genrsa -out "${CA_RAIZ_DIR}/miguelito_root_ca.key" 4096 2>> "${ARQ_LOG}"
chmod 600 "${CA_RAIZ_DIR}/miguelito_root_ca.key"

openssl req -x509 -new -nodes \
    -key "${CA_RAIZ_DIR}/miguelito_root_ca.key" \
    -sha256 -days 3650 \
    -config "${CA_RAIZ_DIR}/root_ca.cnf" \
    -extensions v3_ca \
    -out "${CA_RAIZ_DIR}/miguelito_root_ca.crt" 2>> "${ARQ_LOG}"

registrar_log "INFO" "Certificado da Miguelito Root CA emitido:"
openssl x509 -in "${CA_RAIZ_DIR}/miguelito_root_ca.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/  /' | tee -a "${ARQ_LOG}"

# 2. Emissão do certificado do parceiro legítimo assinado pela Miguelito Root CA
registrar_log "INFO" "[Passo 2] Emitindo par de chaves e certificado para o parceiro legítimo (parceiro.miguelito.com.br)..."

cat > "${PARCEIRO_DIR}/parceiro.cnf" << 'EOF'
[ req ]
default_bits        = 2048
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
req_extensions      = v3_req

[ dn ]
C                   = BR
ST                  = Sao Paulo
L                   = Sao Paulo
O                   = Parceiro Infraestrutura e Cloud Computing Ltda
OU                  = Contratos Digitais B2B
CN                  = parceiro.miguelito.com.br

[ v3_req ]
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, nonRepudiation, keyEncipherment
subjectAltName         = @alt_names

[ v3_folha ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, nonRepudiation, keyEncipherment
extendedKeyUsage       = clientAuth, emailProtection, codeSigning
subjectAltName         = @alt_names

[ alt_names ]
DNS.1 = parceiro.miguelito.com.br
DNS.2 = parceiro.xyzw.com
EOF

openssl genrsa -out "${PARCEIRO_DIR}/parceiro.key" 2048 2>> "${ARQ_LOG}"
chmod 600 "${PARCEIRO_DIR}/parceiro.key"

openssl req -new \
    -key "${PARCEIRO_DIR}/parceiro.key" \
    -config "${PARCEIRO_DIR}/parceiro.cnf" \
    -out "${PARCEIRO_DIR}/parceiro.csr" 2>> "${ARQ_LOG}"

openssl x509 -req \
    -in "${PARCEIRO_DIR}/parceiro.csr" \
    -CA "${CA_RAIZ_DIR}/miguelito_root_ca.crt" \
    -CAkey "${CA_RAIZ_DIR}/miguelito_root_ca.key" \
    -CAcreateserial \
    -out "${PARCEIRO_DIR}/parceiro.crt" \
    -days 365 -sha256 \
    -extfile "${PARCEIRO_DIR}/parceiro.cnf" \
    -extensions v3_folha 2>> "${ARQ_LOG}"

# Extrai a chave pública do certificado do parceiro para usar no openssl dgst -verify
openssl x509 -in "${PARCEIRO_DIR}/parceiro.crt" -pubkey -noout > "${PARCEIRO_DIR}/parceiro_pub.pem"

registrar_log "INFO" "Certificado do parceiro legítimo assinado pela Miguelito Root CA:"
openssl x509 -in "${PARCEIRO_DIR}/parceiro.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/  /' | tee -a "${ARQ_LOG}"

# 3. Criação da Rogue CA (atacante) e emissão de certificado forjado
registrar_log "INFO" "[Passo 3] Criando a Rogue CA (não confiável) e emitindo certificado falso do parceiro..."

cat > "${ROGUE_DIR}/rogue_ca.cnf" << 'EOF'
[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
x509_extensions     = v3_ca

[ dn ]
C                   = XX
ST                  = External
L                   = Unknown
O                   = Rogue Unverified Authority
OU                  = Untrusted PKI
CN                  = Rogue Root CA

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true, pathlen:0
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign
EOF

openssl genrsa -out "${ROGUE_DIR}/rogue_root_ca.key" 4096 2>> "${ARQ_LOG}"
chmod 600 "${ROGUE_DIR}/rogue_root_ca.key"

openssl req -x509 -new -nodes \
    -key "${ROGUE_DIR}/rogue_root_ca.key" \
    -sha256 -days 3650 \
    -config "${ROGUE_DIR}/rogue_ca.cnf" \
    -extensions v3_ca \
    -out "${ROGUE_DIR}/rogue_root_ca.crt" 2>> "${ARQ_LOG}"

# O atacante gera sua própria chave e usa os mesmos dados de Subject (CN=parceiro.miguelito.com.br),
# mas quem assina o certificado é a Rogue CA.
openssl genrsa -out "${FALSO_DIR}/parceiro_forjado.key" 2048 2>> "${ARQ_LOG}"
chmod 600 "${FALSO_DIR}/parceiro_forjado.key"

openssl req -new \
    -key "${FALSO_DIR}/parceiro_forjado.key" \
    -config "${PARCEIRO_DIR}/parceiro.cnf" \
    -out "${FALSO_DIR}/parceiro_forjado.csr" 2>> "${ARQ_LOG}"

openssl x509 -req \
    -in "${FALSO_DIR}/parceiro_forjado.csr" \
    -CA "${ROGUE_DIR}/rogue_root_ca.crt" \
    -CAkey "${ROGUE_DIR}/rogue_root_ca.key" \
    -CAcreateserial \
    -out "${FALSO_DIR}/parceiro_forjado.crt" \
    -days 365 -sha256 \
    -extfile "${PARCEIRO_DIR}/parceiro.cnf" \
    -extensions v3_folha 2>> "${ARQ_LOG}"

openssl x509 -in "${FALSO_DIR}/parceiro_forjado.crt" -pubkey -noout > "${FALSO_DIR}/parceiro_forjado_pub.pem"

registrar_log "INFO" "Certificado forjado emitido pela Rogue CA:"
openssl x509 -in "${FALSO_DIR}/parceiro_forjado.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/  /' | tee -a "${ARQ_LOG}"

# 4. Execução dos 3 Cenários de Auditoria
registrar_log "INFO" "------------------------------------------------------------------------------"
registrar_log "INFO" "[Passo 4] Executando os Cenários de Auditoria A, B e C"
registrar_log "INFO" "------------------------------------------------------------------------------"

# --- CENÁRIO A ---
registrar_log "INFO" ">>> CENÁRIO A: Documento íntegro assinado pelo parceiro legítimo"

openssl dgst -sha256 -sign "${PARCEIRO_DIR}/parceiro.key" \
    -out "${CENARIOS_DIR}/cenario_a.sig" \
    "${CENARIOS_DIR}/contrato_miguelito.txt"

registrar_log "INFO" "Assinatura gerada: cenario_a.sig ($(wc -c < "${CENARIOS_DIR}/cenario_a.sig") bytes)"

SAIDA_DGST_A="$(openssl dgst -sha256 -verify "${PARCEIRO_DIR}/parceiro_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_a.sig" \
    "${CENARIOS_DIR}/contrato_miguelito.txt" 2>&1)"
registrar_log "INFO" "Verificação da assinatura (openssl dgst -verify): ${SAIDA_DGST_A}"

SAIDA_CHAIN_A="$(openssl verify -CAfile "${CA_RAIZ_DIR}/miguelito_root_ca.crt" "${PARCEIRO_DIR}/parceiro.crt" 2>&1)"
registrar_log "INFO" "Validação da cadeia contra Miguelito Root CA (openssl verify): ${SAIDA_CHAIN_A}"
registrar_log "INFO" "Resultado Cenário A -> DECISÃO: ACEITAR"

# --- CENÁRIO B ---
registrar_log "INFO" "------------------------------------------------------------------------------"
registrar_log "INFO" ">>> CENÁRIO B: Documento adulterado após a assinatura (alteração no valor da parcela)"

# Altera o primeiro dígito da parcela mensal de R$ 120.833,33 para R$ 920.833,33
sed 's/R\$ 120\.833,33/R\$ 920.833,33/g' "${CENARIOS_DIR}/contrato_miguelito.txt" > "${CENARIOS_DIR}/contrato_adulterado.txt"

HASH_ORIG="$(sha256sum "${CENARIOS_DIR}/contrato_miguelito.txt" | awk '{print $1}')"
HASH_MOD="$(sha256sum "${CENARIOS_DIR}/contrato_adulterado.txt" | awk '{print $1}')"
registrar_log "INFO" "SHA-256 original   : ${HASH_ORIG}"
registrar_log "INFO" "SHA-256 adulterado : ${HASH_MOD}"

set +e
SAIDA_DGST_B="$(openssl dgst -sha256 -verify "${PARCEIRO_DIR}/parceiro_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_a.sig" \
    "${CENARIOS_DIR}/contrato_adulterado.txt" 2>&1)"
CODIGO_B=$?
set -e

registrar_log "WARN" "Código de saída do OpenSSL: ${CODIGO_B}"
echo "${SAIDA_DGST_B}" | sed 's/^/  /' | tee -a "${ARQ_LOG}"
registrar_log "WARN" "Resultado Cenário B -> DECISÃO: REJEITAR (O hash do documento modificado não confere com a assinatura)."

# --- CENÁRIO C ---
registrar_log "INFO" "------------------------------------------------------------------------------"
registrar_log "INFO" ">>> CENÁRIO C: Documento original assinado com a chave do certificado forjado (Rogue CA)"

openssl dgst -sha256 -sign "${FALSO_DIR}/parceiro_forjado.key" \
    -out "${CENARIOS_DIR}/cenario_c_forjado.sig" \
    "${CENARIOS_DIR}/contrato_miguelito.txt"

SAIDA_DGST_C="$(openssl dgst -sha256 -verify "${FALSO_DIR}/parceiro_forjado_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_c_forjado.sig" \
    "${CENARIOS_DIR}/contrato_miguelito.txt" 2>&1)"
registrar_log "INFO" "1) Verificação matemática com a chave pública do certificado falso: ${SAIDA_DGST_C}"

set +e
SAIDA_CHAIN_C="$(openssl verify -CAfile "${CA_RAIZ_DIR}/miguelito_root_ca.crt" "${FALSO_DIR}/parceiro_forjado.crt" 2>&1)"
CODIGO_C=$?
set -e

registrar_log "WARN" "2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code ${CODIGO_C}):"
echo "${SAIDA_CHAIN_C}" | sed 's/^/  /' | tee -a "${ARQ_LOG}"
registrar_log "WARN" "Resultado Cenário C -> DECISÃO: REJEITAR (Assinatura matematicamente válida para aquela chave, mas o certificado não foi emitido pela Miguelito Root CA)."

registrar_log "INFO" "------------------------------------------------------------------------------"
registrar_log "INFO" "Resumo Final:"
registrar_log "INFO" "  Cenário A: Assinatura OK | Cadeia OK (Miguelito Root CA) -> ACEITAR"
registrar_log "INFO" "  Cenário B: Verification failure (Exit ${CODIGO_B})                -> REJEITAR"
registrar_log "INFO" "  Cenário C: Assinatura OK | Falha na cadeia (Exit ${CODIGO_C})     -> REJEITAR"
