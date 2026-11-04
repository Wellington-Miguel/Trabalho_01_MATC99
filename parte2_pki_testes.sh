#!/usr/bin/env bash
# ==============================================================================
# UNIVERSIDADE FEDERAL DA BAHIA (UFBA) - INSTITUTO DE COMPUTAÇÃO
# Disciplina: MATC99 - Segurança e Auditoria de Sistemas de Informação
# Trabalho 01: Criptografia Aplicada: Proteção, Assinaturas Digitais e Certificados
# Módulo: Parte II - PKI, Assinaturas Digitais e Cadeia de Certificação (OpenSSL)
# Arquivo: parte2_pki_testes.sh
# ==============================================================================
# Descrição Técnica:
#   Script de automação idempotente que estrutura uma Infraestrutura de Chaves
#   Públicas (PKI / X.509 v3) completa, emite certificados legítimos e forjados,
#   e executa os 3 cenários de perícia forense e auditoria exigidos pela XYZW:
#     1. Root CA Legítima ("XYZW Root CA") - RSA 4096 bits, X.509 v3 Autoassinado.
#     2. Entidade Parceira Legítima ("parceiro.xyzw.com") - RSA 2048 bits,
#        assinado pela XYZW Root CA com extensões v3 (digitalSignature,
#        nonRepudiation, keyEncipherment e SAN DNS:parceiro.xyzw.com).
#     3. Root CA Atacante ("Rogue CA") - RSA 4096 bits, X.509 v3 Autoassinado,
#        e emissão de certificado forjado para "parceiro.xyzw.com".
#     4. Execução e coleta de evidências dos Cenários A (ACEITAR), B (REJEITAR
#        por violação de integridade) e C (REJEITAR por certificado não confiável).
# ==============================================================================

set -euo pipefail

# Diretórios de trabalho e artefatos
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKI_DIR="${SCRIPT_DIR}/pki_xyzw"
ROOT_CA_DIR="${PKI_DIR}/root_ca"
PARCEIRO_DIR="${PKI_DIR}/parceiro_legitimo"
ROGUE_CA_DIR="${PKI_DIR}/rogue_ca"
ATACANTE_DIR="${PKI_DIR}/parceiro_forjado"
CENARIOS_DIR="${PKI_DIR}/cenarios_auditoria"
LOG_FILE="${SCRIPT_DIR}/parte2_pki_testes.log"
CONTRATO_ORIG="${SCRIPT_DIR}/contrato_xyzw.txt"

# Função auxiliar de logging com timestamp ISO-8601
log() {
    local nivel="$1"
    shift
    local msg="$*"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S.%3N')"
    echo "[${ts}] [${nivel}] ${msg}" | tee -a "${LOG_FILE}"
}

separador() {
    echo "================================================================================" | tee -a "${LOG_FILE}"
}

subseparador() {
    echo "--------------------------------------------------------------------------------" | tee -a "${LOG_FILE}"
}

# Inicialização idempotente: limpa execuções anteriores para garantir reprodutibilidade
rm -rf "${PKI_DIR}" "${LOG_FILE}"
mkdir -p "${ROOT_CA_DIR}" "${PARCEIRO_DIR}" "${ROGUE_CA_DIR}" "${ATACANTE_DIR}" "${CENARIOS_DIR}"

separador
log "INFO" "INICIANDO AUDITORIA PKI E ASSINATURAS DIGITAIS - PARTE II (OpenSSL)"
log "INFO" "Versão do OpenSSL: $(openssl version)"
separador

# Verificação de existência do contrato base
if [[ ! -f "${CONTRATO_ORIG}" ]]; then
    log "ERROR" "Arquivo base '${CONTRATO_ORIG}' não encontrado! Execute a criação do contrato antes."
    exit 1
fi
cp "${CONTRATO_ORIG}" "${CENARIOS_DIR}/contrato_xyzw.txt"

# ==============================================================================
# PASSO 1: CONFIGURAÇÃO DA ROOT CA LEGÍTIMA (XYZW Root CA) - RSA 4096-BIT
# ==============================================================================
log "INFO" "[PASSO 1] Gerando Autoridade Certificadora Raiz Legítima (XYZW Root CA - RSA 4096 bits)"

cat > "${ROOT_CA_DIR}/openssl_root_ca.cnf" << 'EOF'
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
O                   = XYZW Tecnologia e Solucoes Digitais S.A.
OU                  = Diretoria de Seguranca da Informacao e PKI Corporativa
CN                  = XYZW Root CA

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true, pathlen:0
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign
EOF

openssl genrsa -out "${ROOT_CA_DIR}/xyzw_root_ca.key" 4096 2>> "${LOG_FILE}"
chmod 600 "${ROOT_CA_DIR}/xyzw_root_ca.key"

openssl req -x509 -new -nodes \
    -key "${ROOT_CA_DIR}/xyzw_root_ca.key" \
    -sha256 -days 3650 \
    -config "${ROOT_CA_DIR}/openssl_root_ca.cnf" \
    -extensions v3_ca \
    -out "${ROOT_CA_DIR}/xyzw_root_ca.crt" 2>> "${LOG_FILE}"

log "INFO" "  -> Chave Privada Root CA : ${ROOT_CA_DIR}/xyzw_root_ca.key (RSA 4096 bits)"
log "INFO" "  -> Certificado Root CA   : ${ROOT_CA_DIR}/xyzw_root_ca.crt"
openssl x509 -in "${ROOT_CA_DIR}/xyzw_root_ca.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/     /' | tee -a "${LOG_FILE}"

# ==============================================================================
# PASSO 2: EMISSÃO DO CERTIFICADO LEGÍTIMO (parceiro.xyzw.com) ASSINADO PELA XYZW ROOT CA
# ==============================================================================
subseparador
log "INFO" "[PASSO 2] Emitindo Par de Chaves e Certificado X.509 de 'parceiro.xyzw.com' (Assinado pela XYZW Root CA)"

cat > "${PARCEIRO_DIR}/openssl_parceiro.cnf" << 'EOF'
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
OU                  = Operacoes B2B e Contratos Digitais
CN                  = parceiro.xyzw.com

[ v3_req ]
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, nonRepudiation, keyEncipherment
extendedKeyUsage       = clientAuth, emailProtection, codeSigning
subjectAltName         = @alt_names

[ v3_leaf ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, nonRepudiation, keyEncipherment
extendedKeyUsage       = clientAuth, emailProtection, codeSigning
subjectAltName         = @alt_names

[ alt_names ]
DNS.1 = parceiro.xyzw.com
EOF

# Geração da chave privada RSA 2048-bit e CSR (Certificate Signing Request)
openssl genrsa -out "${PARCEIRO_DIR}/parceiro.key" 2048 2>> "${LOG_FILE}"
chmod 600 "${PARCEIRO_DIR}/parceiro.key"

openssl req -new \
    -key "${PARCEIRO_DIR}/parceiro.key" \
    -config "${PARCEIRO_DIR}/openssl_parceiro.cnf" \
    -out "${PARCEIRO_DIR}/parceiro.csr" 2>> "${LOG_FILE}"

# Assinatura do certificado pela XYZW Root CA
openssl x509 -req \
    -in "${PARCEIRO_DIR}/parceiro.csr" \
    -CA "${ROOT_CA_DIR}/xyzw_root_ca.crt" \
    -CAkey "${ROOT_CA_DIR}/xyzw_root_ca.key" \
    -CAcreateserial \
    -out "${PARCEIRO_DIR}/parceiro.crt" \
    -days 365 -sha256 \
    -extfile "${PARCEIRO_DIR}/openssl_parceiro.cnf" \
    -extensions v3_leaf 2>> "${LOG_FILE}"

# Extração explícita da chave pública do certificado legítimo
openssl x509 -in "${PARCEIRO_DIR}/parceiro.crt" -pubkey -noout > "${PARCEIRO_DIR}/parceiro_pub.pem"

log "INFO" "  -> Chave Privada Parceiro Legítimo : ${PARCEIRO_DIR}/parceiro.key (RSA 2048 bits)"
log "INFO" "  -> Certificado Parceiro Legítimo   : ${PARCEIRO_DIR}/parceiro.crt"
log "INFO" "  -> Chave Pública Extraída          : ${PARCEIRO_DIR}/parceiro_pub.pem"
openssl x509 -in "${PARCEIRO_DIR}/parceiro.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/     /' | tee -a "${LOG_FILE}"

# ==============================================================================
# PASSO 3: CONFIGURAÇÃO DA ROGUE CA E CERTIFICADO FORJADO PARA parceiro.xyzw.com
# ==============================================================================
subseparador
log "INFO" "[PASSO 3] Configurando Autoridade Certificadora Atacante (Rogue CA) e Certificado Forjado"

cat > "${ROGUE_CA_DIR}/openssl_rogue_ca.cnf" << 'EOF'
[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
encrypt_key         = no
distinguished_name  = dn
x509_extensions     = v3_ca

[ dn ]
C                   = XX
ST                  = Offshore
L                   = Darknet
O                   = Rogue Shadow Trust Authority Ltd
OU                  = Unverified Root Certification Authority
CN                  = Rogue Root CA

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true, pathlen:0
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign
EOF

openssl genrsa -out "${ROGUE_CA_DIR}/rogue_root_ca.key" 4096 2>> "${LOG_FILE}"
chmod 600 "${ROGUE_CA_DIR}/rogue_root_ca.key"

openssl req -x509 -new -nodes \
    -key "${ROGUE_CA_DIR}/rogue_root_ca.key" \
    -sha256 -days 3650 \
    -config "${ROGUE_CA_DIR}/openssl_rogue_ca.cnf" \
    -extensions v3_ca \
    -out "${ROGUE_CA_DIR}/rogue_root_ca.crt" 2>> "${LOG_FILE}"

# Emissão de certificado falso se passando por "parceiro.xyzw.com", porém assinado pela Rogue CA
openssl genrsa -out "${ATACANTE_DIR}/parceiro_forjado.key" 2048 2>> "${LOG_FILE}"
chmod 600 "${ATACANTE_DIR}/parceiro_forjado.key"

openssl req -new \
    -key "${ATACANTE_DIR}/parceiro_forjado.key" \
    -config "${PARCEIRO_DIR}/openssl_parceiro.cnf" \
    -out "${ATACANTE_DIR}/parceiro_forjado.csr" 2>> "${LOG_FILE}"

openssl x509 -req \
    -in "${ATACANTE_DIR}/parceiro_forjado.csr" \
    -CA "${ROGUE_CA_DIR}/rogue_root_ca.crt" \
    -CAkey "${ROGUE_CA_DIR}/rogue_root_ca.key" \
    -CAcreateserial \
    -out "${ATACANTE_DIR}/parceiro_forjado.crt" \
    -days 365 -sha256 \
    -extfile "${PARCEIRO_DIR}/openssl_parceiro.cnf" \
    -extensions v3_leaf 2>> "${LOG_FILE}"

openssl x509 -in "${ATACANTE_DIR}/parceiro_forjado.crt" -pubkey -noout > "${ATACANTE_DIR}/parceiro_forjado_pub.pem"

log "INFO" "  -> Certificado Rogue CA            : ${ROGUE_CA_DIR}/rogue_root_ca.crt"
log "INFO" "  -> Certificado Forjado (Atacante)  : ${ATACANTE_DIR}/parceiro_forjado.crt (CN=parceiro.xyzw.com)"
openssl x509 -in "${ATACANTE_DIR}/parceiro_forjado.crt" -noout -subject -issuer -serial -fingerprint -sha256 | sed 's/^/     /' | tee -a "${LOG_FILE}"

# ==============================================================================
# PASSO 4: EXECUÇÃO DOS 3 CENÁRIOS DE AUDITORIA E PERÍCIA FORENSE
# ==============================================================================
separador
log "INFO" "[PASSO 4] EXECUÇÃO DOS CENÁRIOS DE AUDITORIA (A, B e C)"
separador

# ------------------------------------------------------------------------------
# CENÁRIO A: Assinatura Legítima + Documento Íntegro + Cadeia Válida (ACEITAR)
# ------------------------------------------------------------------------------
log "INFO" ">>> [CENÁRIO A] Contrato Original Assinado pela Chave Privada Legítima de 'parceiro.xyzw.com'"

# 1. Assinar o documento original com SHA-256 + RSA usando a chave privada do parceiro legítimo
openssl dgst -sha256 -sign "${PARCEIRO_DIR}/parceiro.key" \
    -out "${CENARIOS_DIR}/cenario_a_contrato.sig" \
    "${CENARIOS_DIR}/contrato_xyzw.txt"

log "INFO" "  [A.1] Assinatura digital gerada: cenario_a_contrato.sig ($(wc -c < "${CENARIOS_DIR}/cenario_a_contrato.sig") bytes)"
log "INFO" "  [A.2] SHA-256 da assinatura    : $(sha256sum "${CENARIOS_DIR}/cenario_a_contrato.sig" | awk '{print $1}')"

# 2. Verificar a assinatura digital via chave pública legítima
log "INFO" "  [A.3] Executando verificação matemática da assinatura (openssl dgst -sha256 -verify):"
OUT_VERIFY_A="$(openssl dgst -sha256 -verify "${PARCEIRO_DIR}/parceiro_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_a_contrato.sig" \
    "${CENARIOS_DIR}/contrato_xyzw.txt" 2>&1)"
echo "        Resultado OpenSSL dgst: ${OUT_VERIFY_A}" | tee -a "${LOG_FILE}"

# 3. Validar a cadeia de certificação contra a Trust Store corporativa (XYZW Root CA)
log "INFO" "  [A.4] Executando validação da cadeia X.509 contra a XYZW Root CA (openssl verify):"
OUT_CHAIN_A="$(openssl verify -CAfile "${ROOT_CA_DIR}/xyzw_root_ca.crt" "${PARCEIRO_DIR}/parceiro.crt" 2>&1)"
echo "        Resultado OpenSSL verify: ${OUT_CHAIN_A}" | tee -a "${LOG_FILE}"

log "INFO" "  [VEREDITO CENÁRIO A] -> DECISÃO: ACEITAR (Integridade matemática comprovada e cadeia de confiança X.509 válida)."
subseparador

# ------------------------------------------------------------------------------
# CENÁRIO B: Documento Adulterado Pós-Assinatura + Chave Legítima (REJEITAR)
# ------------------------------------------------------------------------------
log "INFO" ">>> [CENÁRIO B] Adulteração Pós-Assinatura no Contrato (Fraude de Valor Monetário)"

# Cria cópia do contrato e altera o valor mensal de R$ 120.833,33 para R$ 920.833,33 (alteração de 1 caractere: '1' -> '9')
sed 's/R\$ 120\.833,33/R\$ 920.833,33/g' "${CENARIOS_DIR}/contrato_xyzw.txt" > "${CENARIOS_DIR}/contrato_xyzw_adulterado.txt"

HASH_ORIG="$(sha256sum "${CENARIOS_DIR}/contrato_xyzw.txt" | awk '{print $1}')"
HASH_ADULT="$(sha256sum "${CENARIOS_DIR}/contrato_xyzw_adulterado.txt" | awk '{print $1}')"

log "INFO" "  [B.1] Adulteração realizada: parcela alterada de 'R\$ 120.833,33' para 'R\$ 920.833,33' (1 byte modificado)"
log "INFO" "  [B.2] SHA-256 Documento Original   : ${HASH_ORIG}"
log "INFO" "  [B.3] SHA-256 Documento Adulterado : ${HASH_ADULT}"
log "INFO" "  [B.4] Executando verificação da assinatura original contra o documento adulterado:"

set +e
OUT_VERIFY_B="$(openssl dgst -sha256 -verify "${PARCEIRO_DIR}/parceiro_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_a_contrato.sig" \
    "${CENARIOS_DIR}/contrato_xyzw_adulterado.txt" 2>&1)"
RC_VERIFY_B=$?
set -e

echo "        Código de Retorno (Exit Code): ${RC_VERIFY_B}" | tee -a "${LOG_FILE}"
echo "        Resultado OpenSSL dgst       : ${OUT_VERIFY_B}" | tee -a "${LOG_FILE}"
log "WARN" "  [VEREDITO CENÁRIO B] -> DECISÃO: REJEITAR (Falha de verificação criptográfica: o efeito avalanche do SHA-256 produziu um digest divergente do bloco PKCS#1 decifrado pela chave pública)."
subseparador

# ------------------------------------------------------------------------------
# CENÁRIO C: Documento Original Assinado pelo Certificado Forjado / Rogue CA (REJEITAR)
# ------------------------------------------------------------------------------
log "INFO" ">>> [CENÁRIO C] Contrato Assinado com Chave Privada Forjada (Emitida pela Rogue CA para 'parceiro.xyzw.com')"

# 1. Atacante assina o documento original com sua chave privada forjada
openssl dgst -sha256 -sign "${ATACANTE_DIR}/parceiro_forjado.key" \
    -out "${CENARIOS_DIR}/cenario_c_contrato_forjado.sig" \
    "${CENARIOS_DIR}/contrato_xyzw.txt"

log "INFO" "  [C.1] Assinatura do atacante gerada: cenario_c_contrato_forjado.sig ($(wc -c < "${CENARIOS_DIR}/cenario_c_contrato_forjado.sig") bytes)"

# 2. Validação matemática isolada contra a chave pública contida no certificado forjado
log "INFO" "  [C.2] Passo 1 da Auditoria: Verificação matemática contra a chave pública do certificado apresentado pelo atacante:"
OUT_VERIFY_C="$(openssl dgst -sha256 -verify "${ATACANTE_DIR}/parceiro_forjado_pub.pem" \
    -signature "${CENARIOS_DIR}/cenario_c_contrato_forjado.sig" \
    "${CENARIOS_DIR}/contrato_xyzw.txt" 2>&1)"
echo "        Resultado OpenSSL dgst: ${OUT_VERIFY_C}" | tee -a "${LOG_FILE}"

# 3. Validação da cadeia de certificação contra a Trust Store corporativa (XYZW Root CA)
log "INFO" "  [C.3] Passo 2 da Auditoria: Validação do certificado apresentado (parceiro_forjado.crt) contra a Trust Store corporativa (XYZW Root CA):"
set +e
OUT_CHAIN_C="$(openssl verify -CAfile "${ROOT_CA_DIR}/xyzw_root_ca.crt" "${ATACANTE_DIR}/parceiro_forjado.crt" 2>&1)"
RC_CHAIN_C=$?
set -e

echo "        Código de Retorno (Exit Code): ${RC_CHAIN_C}" | tee -a "${LOG_FILE}"
echo "${OUT_CHAIN_C}" | sed 's/^/        /' | tee -a "${LOG_FILE}"
log "WARN" "  [VEREDITO CENÁRIO C] -> DECISÃO: REJEITAR (Embora a assinatura seja matematicamente íntegra em relação à chave pública apresentada ['Verified OK'], o certificado não possui vínculo criptográfico com a 'XYZW Root CA' ['error 20: unable to get local issuer certificate'], caracterizando tentativa de spoofing de identidade / certificado ilegítimo)."

separador
log "INFO" "RESUMO CONSOLIDADO DA AUDITORIA PKI (PARTE II)"
separador
log "INFO" "  * Cenário A (Assinatura Legítima + Cadeia XYZW Root CA) : Verified OK | Chain OK                      -> DECISÃO: ACEITAR"
log "INFO" "  * Cenário B (Documento Adulterado Pós-Assinatura)       : Verification Failure (Exit ${RC_VERIFY_B})               -> DECISÃO: REJEITAR"
log "INFO" "  * Cenário C (Assinatura com Certificado da Rogue CA)    : Verified OK | Chain Error 20 (Exit ${RC_CHAIN_C})      -> DECISÃO: REJEITAR"
log "INFO" "  * Log completo salvo em: ${LOG_FILE}"
separador

