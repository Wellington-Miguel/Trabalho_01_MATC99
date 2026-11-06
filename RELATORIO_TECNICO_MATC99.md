# UNIVERSIDADE FEDERAL DA BAHIA
## INSTITUTO DE COMPUTAÇÃO
### DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO

---

<div align="center">

### **MATC99 — SEGURANÇA E AUDITORIA DE SISTEMAS DE INFORMAÇÃO**

# **TRABALHO 01 — CRIPTOGRAFIA APLICADA: PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS**

**Estudo de Caso:** Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.  
**Aluno:** Wellington Miguel de Jesus Silva  
**Local e Data:** Salvador — BA, Novembro de 2026  

</div>

---

## Sumário

1. [Introdução e Contextualização do Problema](#1-introdução-e-contextualização-do-problema)
2. [Fundamentação Teórica](#2-fundamentação-teórica)
   - [2.1. Criptografia Simétrica vs. Criptografia Assimétrica](#21-criptografia-simétrica-vs-criptografia-assimétrica)
   - [2.2. Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)](#22-funcionamento-do-modo-aes-gcm-e-integridade-autenticada-aead)
   - [2.3. Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA](#23-infraestrutura-de-chaves-públicas-pki-certificados-x509-e-assinaturas-rsa)
3. [Metodologia e Ambiente Experimental](#3-metodologia-e-ambiente-experimental)
4. [Experimentos da Parte I: Proteção e Integridade com AES-256-GCM](#4-experimentos-da-parte-i-proteção-e-integridade-com-aes-256-gcm)
   - [4.1. Procedimentos de Cifragem, Empacotamento e Decifragem](#41-procedimentos-de-cifragem-empacotamento-e-decifragem)
   - [4.2. Logs de Execução e Análise dos Cenários de Falha](#42-logs-de-execução-e-análise-dos-cenários-de-falha)
   - [4.3. Propriedades de Segurança Garantidas](#43-propriedades-de-segurança-garantidas)
5. [Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação](#5-experimentos-da-parte-ii-assinaturas-digitais-e-cadeia-de-certificação)
   - [5.1. Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)](#51-estrutura-da-pki-simulada-ca-corporativa-vs-rogue-ca)
   - [5.2. Análise do Cenário A: Documento Íntegro e Cadeia Válida](#52-análise-do-cenário-a-documento-íntegro-e-cadeia-válida)
   - [5.3. Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura](#53-análise-do-cenário-b-adulteração-de-conteúdo-pós-assinatura)
   - [5.4. Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável](#54-análise-do-cenário-c-certificado-emitido-por-autoridade-não-confiável)
6. [Matriz de Decisão e Recomendações de Governança](#6-matriz-de-decisão-e-recomendações-de-governança)
   - [6.1. Matriz Comparativa de Auditoria](#61-matriz-comparativa-de-auditoria)
   - [6.2. Recomendações Técnicas para a Miguelito Segurança e Tecnologia](#62-recomendações-técnicas-para-a-miguelito-segurança-e-tecnologia)
7. [Conclusão](#7-conclusão)
8. [Referências Bibliográficas](#8-referências-bibliográficas)

---

## 1. Introdução e Contextualização do Problema

A digitalização de processos de contratação entre empresas (B2B) substituiu o papel físico e o reconhecimento de firma em cartório por fluxos eletrônicos baseados em rede. Embora essa transição reduza custos operacionais e acelere o fechamento de negócios, ela transfere toda a responsabilidade jurídica e financeira da transação para os controles criptográficos adotados pelas partes. Quando esses controles são mal projetados ou validados apenas de forma parcial, a empresa fica exposta a fraudes financeiras e à perda de validade jurídica dos seus instrumentos contratuais.

Neste trabalho, analisamos o cenário da empresa fictícia **Miguelito Segurança e Tecnologia Ltda.** (CNPJ `14.382.910/0001-55`), sediada em Salvador/BA, que atua na operação de sistemas críticos e contrata serviços de nuvem híbrida, links redundantes MPLS/IPSec e custódia de módulos HSM junto a fornecedores externos. Durante uma revisão de auditoria sobre a tramitação do **Contrato Comercial nº 2026/00849-MST**, celebrado com a fornecedora **Parceiro Infraestrutura e Cloud Computing Ltda.** (`parceiro.miguelito.com.br`, CNPJ `67.419.002/0001-83`) no valor global de R\$ 1.450.000,00 (dividido em 12 parcelas mensais de R\$ 120.833,33), surgiram indícios de duas falhas graves no processo de troca e validação dos arquivos digitais: a suspeita de manipulação de cláusulas financeiras durante o trânsito do documento e o recebimento de contratos assinados com certificados digitais não reconhecidos pela governança interna.

Do ponto de vista de segurança da informação e perícia forense, o incidente enfrentado pela Miguelito Segurança e Tecnologia envolve três riscos práticos distintos que precisam ser isolados e tratados:

1. **Interceptação e Modificação em Trânsito (*Man-in-the-Middle* / *Bit-Flipping*):** Contratos comerciais contêm dados bancários, valores de SLA, multas contratuais e especificações técnicas de arquitetura que não podem vazar para terceiros em trânsito (quebra de confidencialidade). Além disso, caso a empresa utilize um algoritmo de cifragem tradicional sem autenticação integrada, um atacante posicionado na rede pode alterar bytes específicos do texto cifrado para modificar valores no texto decifrado sem precisar conhecer a chave secreta.
2. **Adulteração Documental Pós-Assinatura:** Mesmo quando um contrato é assinado por um representante legítimo, existe o risco de o arquivo sofrer modificações posteriores — seja por ação maliciosa interna, seja por interceptação — alterando, por exemplo, o valor da parcela mensal de R\$ 120.833,33 para R\$ 920.833,33. O mecanismo de auditoria precisa detectar alterações mínimas de um único caractere e rejeitar o documento imediatamente.
3. **Falsificação de Identidade Criptográfica (*Key Spoofing* via *Rogue CA*):** Um invasor externo pode gerar seu próprio par de chaves assimétricas, configurar uma Autoridade Certificadora própria (*Rogue CA*) e emitir um certificado digital preenchido com os mesmos dados cadastrais do fornecedor verdadeiro (`CN = parceiro.miguelito.com.br`). Se o setor responsável pela conferência verificar apenas se a assinatura digital é matematicamente válida contra a chave pública anexada ao processo — esquecendo de verificar quem assinou aquele certificado —, o contrato fraudulento será aceito como se fosse autêntico.

Para responder a esse cenário, este trabalho implementa e documenta uma bancada experimental dividida em duas frentes complementares. Na **Parte I**, utilizamos a biblioteca `cryptography` do Python para proteger o contrato com a cifra simétrica autenticada **AES-256-GCM**, testando a recuperação íntegra do arquivo e o comportamento do algoritmo frente à adulteração de bytes no criptograma e ao uso de chaves incorretas. Na **Parte II**, utilizamos o **OpenSSL** em ambiente Linux para construir uma Infraestrutura de Chaves Públicas (PKI) completa, confrontando a Autoridade Certificadora interna da empresa (`Miguelito Root CA`) com uma autoridade atacante (`Rogue CA`) ao longo de três cenários de auditoria (Cenários A, B e C).

---

## 2. Fundamentação Teórica

### 2.1. Criptografia Simétrica vs. Criptografia Assimétrica

A escolha entre algoritmos simétricos e assimétricos em uma arquitetura corporativa decorre diretamente das diferenças de desempenho, gestão de chaves e propriedades jurídicas de cada modelo.

Na **criptografia simétrica**, o emissor e o destinatário compartilham exatamente a mesma chave secreta $K$, que é usada tanto na operação de cifragem quanto na decifragem. Algoritmos simétricos modernos, como o AES (*Advanced Encryption Standard*), operam sobre blocos de bits por meio de rodadas sucessivas de substituição, permutação e combinação linear com chaves derivadas. Por serem operações leves e contarem com instruções dedicadas diretamente nos processadores atuais (*AES-NI*), as cifras simétricas atingem taxas de transferência de múltiplos gigabytes por segundo, sendo a única opção viável na prática para cifrar arquivos extensos, bancos de dados e tráfego de rede em tempo real.

Por outro lado, a criptografia simétrica possui duas limitações importantes para ambientes corporativos abertos:
- **Problema da distribuição e escalabilidade de chaves:** Antes de trocar qualquer contrato cifrado, a Miguelito Segurança e Tecnologia e seu fornecedor precisam compartilhar a chave $K$ por um canal seguro prévio. Em uma rede com $n$ empresas parceiras, seriam necessárias $n(n-1)/2$ chaves secretas distintas para manter o isolamento entre cada par de comunicação.
- **Ausência de Não-Repúdio (Irretratabilidade):** Como tanto a contratante quanto a contratada possuem a mesma chave $K$, ambas têm capacidade técnica idêntica para gerar um arquivo cifrado e sua respectiva tag de verificação. Em uma disputa judicial, a Miguelito não conseguiria provar a um juiz ou perito externo que determinado arquivo veio exclusivamente do fornecedor, pois a própria Miguelito poderia tê-lo forjado usando a chave compartilhada.

A **criptografia assimétrica (ou de chave pública)** contorna esses dois limites ao substituir a chave compartilhada por um par de chaves matematicamente vinculadas: uma **chave privada** (mantida em sigilo absoluto pelo seu titular) e uma **chave pública** (que pode ser divulgada abertamente a qualquer parceiro). A segurança desse modelo baseia-se em funções de caminho único com alçapão (*trapdoor one-way functions*), nas quais é fácil calcular a função em um sentido usando a chave pública, mas computacionalmente inviável inverter o cálculo sem conhecer a informação secreta contida na chave privada — como ocorre no problema da fatoração de inteiros compostos por dois primos grandes no algoritmo RSA.

Essa assimetria permite inverter a lógica de operação conforme o objetivo de segurança:
- **Para Confidencialidade (Híbrida):** Qualquer pessoa pode usar a chave pública do destinatário para cifrar uma chave de sessão simétrica, garantindo que somente o detentor da chave privada correspondente consiga abri-la.
- **Para Autenticidade e Não-Repúdio (Assinatura Digital):** O titular usa sua chave privada exclusiva para assinar o resumo criptográfico de um documento, e qualquer auditor pode usar a chave pública correspondente para conferir a assinatura. Como apenas o titular detém a chave privada, ele não pode negar posteriormente a autoria da assinatura (*não-repúdio*), suprindo exatamente a lacuna deixada pela criptografia simétrica.

### 2.2. Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)

Durante muitos anos, sistemas corporativos utilizaram cifras de bloco em modos de operação voltados exclusivamente para confidencialidade, como o **CBC** (*Cipher Block Chaining*) ou o **CTR** (*Counter Mode*). Embora esses modos escondam o conteúdo do texto em claro contra um observador passivo, eles não oferecem proteção nativa contra um atacante ativo que modifique o texto cifrado em trânsito.

No modo Contador (CTR) puro, por exemplo, a cifra de bloco AES não é aplicada diretamente sobre os blocos do documento original. Em vez disso, o algoritmo recebe um valor público inicial único de 96 bits (12 bytes) chamado **Nonce** (*Number used once*) ou Vetor de Inicialização (IV), concatena a ele um contador sequencial de 32 bits (formando o bloco inicial $J_0$) e cifra esse contador com a chave secreta $K$. O fluxo pseudoaleatório resultante (*keystream*) é então combinado com cada bloco do texto em claro $P_i$ através da operação lógica **XOR** (ou-exclusivo bit a bit) para produzir o bloco cifrado $C_i$.

O grande perigo de usar o modo CTR isoladamente reside na sua **maleabilidade linear**: como a decifragem consiste apenas em aplicar novamente a operação XOR entre o bloco cifrado recebido e o mesmo *keystream*, se um invasor interceptar o arquivo no caminho e inverter exatamente um bit em uma posição conhecida do bloco cifrado $C_i$, o processo de decifragem não apresentará nenhum erro e inverterá exatamente o mesmo bit no texto em claro recuperado $P_i$. Em um contrato comercial padronizado onde a posição das cláusulas é previsível, isso permitiria alterar dígitos de valores monetários ou números de conta bancária às cegas (*ataque de bit-flipping*).

Para eliminar essa vulnerabilidade sem precisar configurar um algoritmo de MAC separado (como HMAC-SHA256), o padrão **NIST SP 800-38D** definiu o **AES-GCM** (*Galois/Counter Mode*), classificado como um esquema **AEAD** (*Authenticated Encryption with Associated Data*). O AES-GCM une a velocidade do modo contador com um mecanismo algébrico de autenticação chamado **GHASH**, operando em quatro etapas integradas:

1. **Derivação da Subchave de Autenticação ($H$):** Antes de processar os dados, o algoritmo passa um bloco de 128 bits preenchido com zeros pela cifra AES usando a chave secreta $K$, gerando uma subchave interna $H = E_K(0^{128})$ que jamais é exposta fora do módulo criptográfico.
2. **Inclusão de Dados Associados (AAD):** O modo GCM permite autenticar metadados que precisam viajar em texto claro (como cabeçalhos de roteamento, número do contrato ou identificação das partes) junto com o arquivo cifrado. Esses dados formam o campo *Additional Authenticated Data* (AAD).
3. **Cálculo Polinomial no Corpo de Galois $GF(2^{128})$ via GHASH:** O GHASH trata cada bloco de 128 bits do AAD e cada bloco já cifrado ($C_1, C_2, \dots, C_n$), seguidos de um bloco final com os comprimentos em bits do AAD e do texto cifrado, como coeficientes de um polinômio avaliado na subchave secreta $H$. Toda a aritmética de soma (XOR) e multiplicação é feita dentro do corpo finito $GF(2^{128})$ módulo o polinômio irredutível $P(x) = x^{128} + x^7 + x^2 + x + 1$.
4. **Mascaramento e Geração da Authentication Tag ($T$):** O resultado de 128 bits saído do polinômio GHASH recebe um XOR final com a cifragem do contador inicial $E_K(J_0)$, resultando na **Authentication Tag** de 16 bytes (128 bits) que acompanha o arquivo cifrado:
   $$T = \text{GHASH}_H(\text{AAD}, \text{Ciphertext}) \oplus E_K(J_0)$$

O diferencial de segurança do AES-GCM ocorre no momento da decifragem, que segue estritamente a regra **Encrypt-then-MAC**: antes de devolver qualquer byte decifrado para o usuário, a função `AESGCM.decrypt()` lê o Nonce, o AAD e os blocos cifrados $C_i$ recebidos, recalcula o polinômio GHASH do zero para obter uma tag local $T'$ e a compara em tempo constante com a tag $T$ que veio anexada ao arquivo.

Se um atacante tiver alterado sequer um bit em qualquer bloco $C_i$ (introduzindo uma diferença não nula $\Delta$), a propriedade matemática de corpos finitos garante que essa diferença será multiplicada por uma potência de $H$ dentro do GHASH: $\Delta T = \Delta \cdot H^{n-i+2} \pmod{P(x)}$. Como em um corpo finito não existem divisores de zero (o produto de dois elementos não nulos nunca dá zero), a tag recalculada $T'$ será obrigatoriamente diferente de $T$. Nesse instante, a biblioteca descarta o texto decifrado da memória e interrompe a execução lançando a exceção `InvalidTag`, neutralizando qualquer tentativa de manipulação em trânsito.

### 2.3. Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA

Embora o AES-256-GCM resolva a proteção do arquivo em trânsito e em repouso entre sistemas que já compartilham uma chave, ele não substitui a assinatura jurídica de um contrato entre duas empresas distintas. Para garantir que a fornecedora **Parceiro Infraestrutura e Cloud Computing Ltda.** não possa repudiar o contrato assinado e que qualquer auditor da **Miguelito Segurança e Tecnologia** possa conferir essa assinatura sem precisar conhecer segredos do fornecedor, emprega-se o esquema de assinatura digital **RSA com SHA-256** (padronizado na **RFC 8017 — PKCS#1**).

O processo de assinatura digital segue o paradigma **Hash-then-Sign** (Resumir e depois Assinar):

1. **Resumo Criptográfico (SHA-256):** Em vez de aplicar a operação matemática do RSA diretamente sobre os milhares de bytes do contrato — o que seria lento e exigiria fragmentar o documento em vários blocos independentes sujeitos a ataques de reordenação —, o documento passa primeiro pela função hash criptográfica **SHA-256**. O SHA-256 comprime um arquivo de qualquer tamanho em uma impressão digital fixa de 256 bits (32 bytes). Essa função possui duas propriedades essenciais para auditoria: **efeito avalanche** (mudar uma única vírgula ou dígito no contrato altera cerca de metade dos bits do hash de forma imprevisível) e **resistência à colisão e segunda pré-imagem** (é computacionalmente inviável fabricar um contrato adulterado que produza exatamente o mesmo hash de 32 bytes do contrato original).
2. **Preenchimento (Padding PKCS#1 v1.5 / PSS) e Operação com Chave Privada:** No padrão clássico **RSASSA-PKCS1-v1_5** (utilizado por padrão pelo comando `openssl dgst -sha256 -sign`), o hash de 32 bytes e o identificador oficial (OID) do algoritmo SHA-256 são encapsulados em uma estrutura ASN.1 chamada `DigestInfo` e completados com bytes de preenchimento determinístico até atingir exatamente o tamanho do módulo da chave RSA (256 bytes para uma chave de 2048 bits), formando o bloco codificado $EM$. *(Cabe destacar que a RFC 8017 também especifica o esquema moderno **RSA-PSS**, que introduz um valor aleatório — salt — no preenchimento para tornar a assinatura probabilística e fortalecer a redução matemática de segurança).* Em seguida, o signatário aplica sua chave privada $(d, N)$ através da exponenciação modular $S = EM^d \bmod N$, gerando o arquivo binário de assinatura `.sig`.
3. **Verificação Matemática com a Chave Pública:** Para conferir a assinatura, o auditor recalcula o hash SHA-256 do arquivo de texto recebido e, paralelamente, aplica a chave pública do signatário $(e, N)$ sobre a assinatura ($EM' = S^e \bmod N$). Se o hash extraído de dentro da assinatura coincidir bit a bit com o hash calculado sobre o documento, o OpenSSL retorna `Verified OK`; caso contrário, retorna `Verification failure`.

Contudo, existe uma armadilha conceitual crítica que separa uma simples verificação matemática de uma auditoria de segurança real: **a operação matemática do RSA valida apenas que a assinatura foi feita pelo dono da chave privada correspondente àquela chave pública, mas uma chave pública, sozinha, é apenas um número anônimo**. Qualquer pessoa pode gerar um par de chaves RSA no próprio computador e afirmar que aquela chave pública pertence ao diretor financeiro de outra empresa.

É exatamente para amarrar uma identidade do mundo real a uma chave pública que existe a **Infraestrutura de Chaves Públicas (PKI)** e o padrão de certificados digitais **X.509 v3 (RFC 5280)**. Em uma PKI corporativa:
- A organização institui uma **Autoridade Certificadora Raiz (Root CA)** — neste projeto, a `Miguelito Root CA` — cuja chave privada de alta segurança (RSA 4096 bits) funciona como âncora de confiança (*Trust Anchor*). O certificado autoassinado dessa Root CA é instalado previamente no repositório de autoridades confiáveis (**Trust Store**) dos servidores da empresa.
- Quando uma empresa parceira é homologada, ela gera seu par de chaves e envia uma requisição (CSR) para a CA da contratante. Após validar a documentação jurídica da parceira, a `Miguelito Root CA` emite e assina digitalmente um **Certificado X.509** (`parceiro.crt`) contendo o nome distinto do titular (`Subject: CN = parceiro.miguelito.com.br`), o período de validade, a chave pública do parceiro e as extensões X.509 v3 que limitam o que aquela chave pode fazer (como `basicConstraints: CA:FALSE`, que impede o parceiro de sair emitindo certificados para terceiros, e `keyUsage: digitalSignature, nonRepudiation`).

Portanto, a validação pericial de um documento assinado exige obrigatoriamente **duas verificações conjuntas**: (i) a verificação matemática da assinatura do documento contra a chave pública do certificado e (ii) a validação da cadeia de certificação (`openssl verify`) desde o certificado apresentado até uma Root CA presente na *Trust Store* corporativa, além da checagem de não-revogação via listas **CRL** (*Certificate Revocation List*) ou protocolo **OCSP**. Se qualquer uma das duas etapas falhar, o contrato deve ser imediatamente rejeitado.

---

## 3. Metodologia e Ambiente Experimental

Para validar experimentalmente os conceitos discutidos na fundamentação teórica, construímos dois scripts automatizados em ambiente Linux (executados via WSL2), mantendo o registro de todos os comandos, tamanhos de arquivos, números de série e resumos SHA-256 em arquivos de log dedicados. A Tabela 1 resume as ferramentas e versões utilizadas na bancada de testes.

| Componente / Ferramenta | Versão / Especificação | Finalidade nos Experimentos |
| :--- | :--- | :--- |
| **Sistema Operacional** | Ubuntu 24.04 LTS (Kernel Linux `6.6.87.2-microsoft-standard-WSL2 x86_64`) | Ambiente POSIX isolado para execução dos scripts e coleta de logs. |
| **Interpretador Python** | `Python 3.12.3` (WSL) / `Python 3.13.14` (Host) | Execução do script modular `parte1_aes_gcm.py`. |
| **Biblioteca `cryptography`** | `v41.0.7` / `v50.0.2` (`hazmat.primitives.ciphers.aead.AESGCM`) | Implementação do AES-256-GCM e captura da exceção `InvalidTag`. |
| **Suíte OpenSSL CLI** | `OpenSSL 3.0.13 (30 Jan 2024)` | Geração de chaves RSA 4096/2048 bits, emissão X.509 v3, `dgst` e `verify`. |
| **Contrato Comercial Base** | `contrato_miguelito.txt` (`2.841 bytes`, codificação UTF-8) | Contrato nº 2026/00849-MST firmado pela Miguelito Segurança e Tecnologia. |

---

## 4. Experimentos da Parte I: Proteção e Integridade com AES-256-GCM

### 4.1. Procedimentos de Cifragem, Empacotamento e Decifragem

O script `parte1_aes_gcm.py` foi estruturado de forma modular utilizando uma classe de dados (`CriptogramaGCM`) para manipular separadamente os componentes gerados pela cifra autenticada. O fluxo experimental seguiu três etapas iniciais para estabelecer a linha de base legítima:

1. **Carregamento e cálculo de hash do documento original:** O arquivo `contrato_miguelito.txt` foi lido em modo binário, contabilizando exatos **2.841 bytes**. Antes de qualquer operação criptográfica, registrou-se o resumo SHA-256 do arquivo em claro (`9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67`) para servir de gabarito na conferência pós-decifragem.
2. **Geração de parâmetros e cifragem AES-256-GCM:** Utilizamos o gerador criptograficamente seguro do sistema operacional (`os.urandom` / `AESGCM.generate_key`) para produzir uma chave simétrica de **256 bits (32 bytes)** e um Nonce exclusivo de **96 bits (12 bytes)**. Como Dados Associados (AAD), definimos a string de contexto `MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849`. Na biblioteca `cryptography`, o método `AESGCM.encrypt()` retorna o texto cifrado concatenado com os 16 bytes da *Authentication Tag*. Para persistir o criptograma completo no arquivo `contrato_miguelito.enc`, empacotamos os campos na ordem:
   $$\text{Nonce (12 bytes)} \parallel \text{Ciphertext (2.841 bytes)} \parallel \text{Authentication Tag (16 bytes)} = \text{2.869 bytes totais}$$
3. **Decifragem legítima e conferência byte a byte:** Na sequência, o script leu os 2.869 bytes gravados em `contrato_miguelito.enc`, desempacotou o Nonce dos primeiros 12 bytes e submeteu o restante (`Ciphertext + Tag`) junto com a chave correta e o AAD ao método `AESGCM.decrypt()`. A validação do polinômio GHASH ocorreu sem erros, gerando o arquivo `contrato_miguelito_recuperado.txt` com 2.841 bytes e hash SHA-256 idêntico ao original (`original == recuperado: True`).

### 4.2. Logs de Execução e Análise dos Cenários de Falha

Após comprovar o funcionamento do fluxo legítimo, o script executou automaticamente dois testes de falha exigidos pela auditoria, capturando as exceções lançadas pela biblioteca. O trecho abaixo reproduz as evidências gravadas no arquivo `parte1_aes_gcm.log`:

```text
[2026-11-04 15:36:36.889] [INFO] === Auditoria Criptográfica - Miguelito Segurança e Tecnologia (Parte I: AES-256-GCM) ===
[2026-11-04 15:36:36.890] [INFO] [Passo 1] Carregando o contrato original...
[2026-11-04 15:36:36.894] [INFO] Contrato carregado: contrato_miguelito.txt (2841 bytes)
[2026-11-04 15:36:36.895] [INFO] SHA-256 original: 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:36.895] [INFO] [Passo 2] Cifrando o documento com AES-256-GCM...
[2026-11-04 15:36:36.901] [INFO] Arquivo cifrado salvo em: contrato_miguelito.enc (2869 bytes totais)
[2026-11-04 15:36:36.901] [INFO]   Chave AES-256 (32B) : 185c3c58dc5153a9b84ddaf0b85ec9933e52f67c44f8d150f42151a460aa8a28
[2026-11-04 15:36:36.902] [INFO]   Nonce / IV (12B)    : 1d5d2cb6580417d1f29dbf07
[2026-11-04 15:36:36.902] [INFO]   AAD                 : MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849
[2026-11-04 15:36:36.903] [INFO]   Ciphertext          : 2841 bytes
[2026-11-04 15:36:36.903] [INFO]   Auth Tag (16B)      : f987ee9b9f25a4ea8cbcac904a675b94
[2026-11-04 15:36:36.903] [INFO]   SHA-256 (.enc)      : 411df1f9eb37861b0697853141b4c19045aad70a554567a4164354135ab85d8c
[2026-11-04 15:36:36.904] [INFO] [Passo 3] Lendo o arquivo .enc e validando a recuperação do documento...
[2026-11-04 15:36:36.909] [INFO] Comparação de bytes (original == recuperado): True (2841 bytes)
[2026-11-04 15:36:36.909] [INFO] SHA-256 recuperado: 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:36.910] [INFO] --- [Teste de Falha 1: Adulteração de 1 byte no Ciphertext (Bit-Flipping)] ---
[2026-11-04 15:36:36.910] [INFO] Byte modificado no offset 1420 (0x058C): 0x4B -> 0x4A
[2026-11-04 15:36:36.910] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag
[2026-11-04 15:36:36.911] [INFO] Motivo: A alteração no bloco cifrado mudou o resultado do polinômio GHASH em GF(2^128). Como a tag recalculada divergiu da tag original, a decifragem foi abortada.
[2026-11-04 15:36:36.911] [INFO] --- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---
[2026-11-04 15:36:36.911] [INFO] Chave correta : 185c3c58dc5153a9b84ddaf0b85ec9933e52f67c44f8d150f42151a460aa8a28
[2026-11-04 15:36:36.912] [INFO] Chave errada  : 8908f8e494c7d2089963f9ca67836a1d43bfc0a0ea511d3343b5c0a40d8df58e
[2026-11-04 15:36:36.912] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag
[2026-11-04 15:36:36.913] [INFO] Motivo: Com uma chave K' diferente, tanto a subchave do GHASH H' = E_K'(0^128) quanto o bloco cifrado do contador inicial E_K'(J0) mudam completamente, invalidando a tag.
```

A análise técnica dos dois eventos demonstra a eficácia do controle AEAD:
- **No Teste de Falha 1 (Bit-Flipping no Offset 1420):** Modificamos intencionalmente apenas o bit menos significativo do byte localizado na metade do texto cifrado (posição `0x058C`, alterando seu valor hexadecimal de `0x4B` para `0x4A` via operação `XOR 0x01`). Mesmo utilizando a chave legítima (`185c3c58...`) e o Nonce correto, a rotina `AESGCM.decrypt()` recusou o pacote e disparou `cryptography.exceptions.InvalidTag`. Isso confirma na prática que o polinômio GHASH em $GF(2^{128})$ detectou a perturbação no coeficiente correspondente ao 89º bloco de 128 bits, gerando uma tag local diferente de `f987ee9b9f25a4ea8cbcac904a675b94` e impedindo que o byte adulterado chegasse ao texto em claro.
- **No Teste de Falha 2 (Chave Simétrica Incorreta):** Mantivemos o arquivo `contrato_miguelito.enc` intacto, mas tentamos decifrá-lo passando uma segunda chave de 256 bits (`8908f8e4...`). Como essa chave espúria gera uma subchave de hash $H'$ e uma máscara de contador $E_{K'}(J_0)$ completamente diferentes das usadas na cifragem, a conferência da tag de 128 bits falhou imediatamente, lançando a mesma exceção `cryptography.exceptions.InvalidTag`.

### 4.3. Propriedades de Segurança Garantidas

Com a implementação do AES-256-GCM validada na Parte I, o fluxo de arquivos da Miguelito Segurança e Tecnologia passa a contar com três garantias simultâneas: **confidencialidade** (nenhum observador sem a chave de 256 bits consegue ler as cláusulas do contrato), **integridade do criptograma e de seus metadados** (qualquer alteração de 1 bit no Nonce, no AAD, no texto cifrado ou na Tag provoca rejeição imediata via `InvalidTag`) e **autenticidade simétrica de origem** (a validação da Tag comprova que o arquivo foi cifrado por quem detém a chave secreta compartilhada).

---

## 5. Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação

### 5.1. Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)

Para avaliar os riscos de adulteração pós-assinatura e de uso de certificados falsos, o script `parte2_pki_testes.sh` automatizou a criação de uma estrutura de diretórios (`pki_miguelito/`) contendo duas cadeias de certificação X.509 v3 independentes:

1. **Cadeia Corporativa Legítima (Trust Store da Miguelito):**
   - **Autoridade Raiz (`Miguelito Root CA`):** Gerada com chave privada RSA de **4096 bits** (`miguelito_root_ca.key`) e certificado autoassinado válido por 10 anos (`miguelito_root_ca.crt`, Serial `362E0342B4975053DE63770150A88BC71BAE2D96`). Recebeu as extensões críticas de autoridade certificadora (`basicConstraints = critical, CA:true, pathlen:0` e `keyUsage = critical, digitalSignature, cRLSign, keyCertSign`).
   - **Certificado do Fornecedor Legítimo (`parceiro.crt`):** Par de chaves RSA de **2048 bits** gerado para `CN = parceiro.miguelito.com.br` (`O = Parceiro Infraestrutura e Cloud Computing Ltda`). A requisição (CSR) foi assinada pela `Miguelito Root CA` (Serial `21CFB1F05A7A7751254A5581A3A6F65759E6BCC2`), recebendo extensões restritas de entidade final (`basicConstraints = critical, CA:FALSE` e `keyUsage = critical, digitalSignature, nonRepudiation, keyEncipherment`).
2. **Cadeia Externa Não Confiável (Infraestrutura Atacante):**
   - **Autoridade Atacante (`Rogue Root CA`):** Par de chaves RSA de 4096 bits e certificado autoassinado (`rogue_root_ca.crt`, `O = Rogue Unverified Authority`) que **não** faz parte da *Trust Store* da Miguelito Segurança e Tecnologia.
   - **Certificado Forjado (`parceiro_forjado.crt`):** O atacante gerou seu próprio par de chaves RSA de 2048 bits (`parceiro_forjado.key`) e preencheu uma requisição CSR copiando exatamente o mesmo `Subject` do fornecedor verdadeiro (`CN = parceiro.miguelito.com.br`). Contudo, quem assinou esse certificado foi a `Rogue Root CA` (Serial `35D9F02AD06A2A5EFB2A238DE860B45B0F657127`).

### 5.2. Análise do Cenário A: Documento Íntegro e Cadeia Válida

No **Cenário A**, simulamos o fluxo normal e legítimo de assinatura e auditoria do contrato comercial. Primeiro, o documento original foi assinado com a chave privada legítima do parceiro; em seguida, o auditor validou a assinatura matemática usando a chave pública extraída do certificado e conferiu a cadeia do certificado contra a `Miguelito Root CA`:

```bash
# 1. Assinatura digital RSA-SHA256 do contrato original pelo parceiro legítimo
openssl dgst -sha256 -sign pki_miguelito/parceiro_legitimo/parceiro.key \
    -out pki_miguelito/cenarios_auditoria/cenario_a.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 2. Verificação matemática da assinatura via chave pública do parceiro
openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_a.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 3. Validação da cadeia de certificação X.509 contra a Trust Store (Miguelito Root CA)
openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_legitimo/parceiro.crt
```

**Evidências coletadas no log (`parte2_pki_testes.log`):**
```text
[2026-11-04 15:36:40.668] [INFO] >>> CENÁRIO A: Documento íntegro assinado pelo parceiro legítimo
[2026-11-04 15:36:40.697] [INFO] Assinatura gerada: cenario_a.sig (256 bytes)
[2026-11-04 15:36:40.721] [INFO] Verificação da assinatura (openssl dgst -verify): Verified OK
[2026-11-04 15:36:40.743] [INFO] Validação da cadeia contra Miguelito Root CA (openssl verify): /mnt/c/Users/WellingtonMJS/Documents/Trabalho_01_MATC99/pki_miguelito/parceiro_legitimo/parceiro.crt: OK
[2026-11-04 15:36:40.750] [INFO] Resultado Cenário A -> DECISÃO: ACEITAR
```

**Justificativa de Auditoria (DECISÃO: ACEITAR):** O arquivo de assinatura `cenario_a.sig` (256 bytes, correspondente ao módulo RSA de 2048 bits) retornou `Verified OK`, provando que nenhum byte de `contrato_miguelito.txt` foi modificado após a assinatura. Paralelamente, o comando `openssl verify` retornou `parceiro.crt: OK`, confirmando que o certificado do fornecedor possui assinatura válida da `Miguelito Root CA` e respeita todas as restrições X.509 v3. Com integridade documental e autenticidade de identidade comprovadas, o contrato é aceito com garantia de não-repúdio.

### 5.3. Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura

No **Cenário B**, testamos o que acontece quando um contrato legitimamente assinado no Cenário A sofre uma adulteração financeira antes de ser arquivado ou auditado. Utilizando o utilitário `sed`, modificamos apenas um dígito na Cláusula Segunda do contrato, alterando o valor da parcela mensal de `R$ 120.833,33` para `R$ 920.833,33` (troca do caractere `'1'` pelo `'9'`), e submetemos o arquivo fraudado à verificação com a assinatura original:

```bash
# 1. Adulteração de 1 byte no valor da parcela mensal (R$ 120.833,33 -> R$ 920.833,33)
sed 's/R\$ 120\.833,33/R\$ 920.833,33/g' pki_miguelito/cenarios_auditoria/contrato_miguelito.txt \
    > pki_miguelito/cenarios_auditoria/contrato_adulterado.txt

# 2. Conferência da assinatura original (cenario_a.sig) contra o contrato adulterado
openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_a.sig \
    pki_miguelito/cenarios_auditoria/contrato_adulterado.txt
```

**Evidências coletadas no log (`parte2_pki_testes.log`):**
```text
[2026-11-04 15:36:40.764] [INFO] >>> CENÁRIO B: Documento adulterado após a assinatura (alteração no valor da parcela)
[2026-11-04 15:36:40.824] [INFO] SHA-256 original   : 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:40.832] [INFO] SHA-256 adulterado : 817d7fae7346f151320d2469a8546c52edefa478219948e1efbb75edf9f0a8d2
[2026-11-04 15:36:40.856] [WARN] Código de saída do OpenSSL: 1
  40C71E4E407F0000:error:02000068:rsa routines:ossl_rsa_verify:bad signature:../crypto/rsa/rsa_sign.c:430:
  40C71E4E407F0000:error:1C880004:Provider routines:rsa_verify:RSA lib:../providers/implementations/signature/rsa_sig.c:774:
  Verification failure
[2026-11-04 15:36:40.868] [WARN] Resultado Cenário B -> DECISÃO: REJEITAR (O hash do documento modificado não confere com a assinatura).
```

**Justificativa de Auditoria (DECISÃO: REJEITAR):** Embora o certificado do parceiro continue sendo legítimo, a alteração de um único caractere no texto provocou o efeito avalanche na função SHA-256, mudando o resumo do documento de `9147c039...` para `817d7fae...`. Quando a rotina interna `ossl_rsa_verify` decifrou o bloco PKCS#1 v1.5 contido em `cenario_a.sig` usando a chave pública do parceiro, ela encontrou o hash original (`9147c039...`). Como os dois resumos são diferentes e o atacante não possui a chave privada do parceiro para recalcular uma nova assinatura válida sobre o texto fraudado, o OpenSSL encerrou com código de erro `1` (`bad signature` / `Verification failure`). O contrato deve ser imediatamente rejeitado por violação de integridade pós-assinatura.

### 5.4. Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável

No **Cenário C**, simulamos um ataque de falsidade ideológica (*spoofing* de identidade): o atacante toma o contrato original sem alterar uma única palavra, mas o assina usando a chave privada do certificado falso (`parceiro_forjado.key`) emitido pela `Rogue CA` em nome de `parceiro.miguelito.com.br`. Em seguida, executamos as duas etapas da auditoria:

```bash
# 1. Assinatura do contrato original usando a chave privada falsa (vinculada à Rogue CA)
openssl dgst -sha256 -sign pki_miguelito/parceiro_forjado/parceiro_forjado.key \
    -out pki_miguelito/cenarios_auditoria/cenario_c_forjado.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 2. Etapa 1 da Auditoria: Verificação matemática contra a chave pública do certificado falso
openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem \
    -signature pki_miguelito/cenarios_auditoria/cenario_c_forjado.sig \
    pki_miguelito/cenarios_auditoria/contrato_miguelito.txt

# 3. Etapa 2 da Auditoria: Validação do certificado falso contra a Trust Store da Miguelito
openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_forjado/parceiro_forjado.crt
```

**Evidências coletadas no log (`parte2_pki_testes.log`):**
```text
[2026-11-04 15:36:40.884] [INFO] >>> CENÁRIO C: Documento original assinado com a chave do certificado forjado (Rogue CA)
[2026-11-04 15:36:40.927] [INFO] 1) Verificação matemática com a chave pública do certificado falso: Verified OK
[2026-11-04 15:36:40.949] [WARN] 2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code 2):
  C = BR, ST = Sao Paulo, L = Sao Paulo, O = Parceiro Infraestrutura e Cloud Computing Ltda, OU = Contratos Digitais B2B, CN = parceiro.miguelito.com.br
  error 20 at 0 depth lookup: unable to get local issuer certificate
  error /mnt/c/Users/WellingtonMJS/Documents/Trabalho_01_MATC99/pki_miguelito/parceiro_forjado/parceiro_forjado.crt: verification failed
[2026-11-04 15:36:40.962] [WARN] Resultado Cenário C -> DECISÃO: REJEITAR (Assinatura matematicamente válida para aquela chave, mas o certificado não foi emitido pela Miguelito Root CA).
```

**Diferenciação entre Integridade e Autenticidade da Origem (DECISÃO: REJEITAR):** O Cenário C evidencia por que a auditoria de assinaturas digitais nunca pode se resumir ao comando `openssl dgst -verify`. Na primeira etapa, o OpenSSL retornou **`Verified OK`** porque o par de chaves do atacante é matematicamente consistente: a chave pública presente em `parceiro_forjado.crt` de fato decifra a assinatura feita por `parceiro_forjado.key` e o documento não foi modificado desde que o atacante o assinou. Todavia, quando passamos para a segunda etapa (`openssl verify`), o verificador inspeciona o certificado no nível 0 da cadeia (`at 0 depth lookup`), lê o campo emissor (`Issuer: CN = Rogue Root CA`) e tenta localizar o certificado dessa autoridade dentro da *Trust Store* oficial da empresa (`miguelito_root_ca.crt`). Como a `Rogue Root CA` não é reconhecida pela Miguelito Segurança e Tecnologia, a construção da cadeia de confiança falha com o erro **`error 20 at 0 depth lookup: unable to get local issuer certificate`** (código de saída `2`). Portanto, apesar de haver integridade matemática isolada, não há autenticidade da identidade do emissor, exigindo a rejeição imediata do documento.

---

## 6. Matriz de Decisão e Recomendações de Governança

### 6.1. Matriz Comparativa de Auditoria

A Tabela 2 consolida os resultados experimentais obtidos nas Partes I e II, relacionando a integridade matemática do conteúdo, a confiabilidade da chave ou identidade apresentada e o veredito final de auditoria.

| Cenário Auditado | Controle Testado | Integridade Matemática do Arquivo | Confiabilidade da Chave / Identidade | Evidência Técnica (Python / OpenSSL) | Veredito Final |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Parte I — Base Legítima** | Decifragem AES-256-GCM com arquivo e chave íntegros | **Válida** (Tag GCM e SHA-256 conferem) | **Válida** (Posse da chave simétrica legítima) | Sem exceções; 2.841 bytes recuperados | **ACEITAR** |
| **Parte I — Falha 1 (Bit-Flipping)** | Adulteração de 1 byte no ciphertext (Offset `1420`) | **Inválida** (Polinômio GHASH diverge) | **Válida** (Chave simétrica correta utilizada) | `cryptography.exceptions.InvalidTag` | **REJEITAR** |
| **Parte I — Falha 2 (Chave Espúria)** | Tentativa de decifragem com chave de 256 bits incorreta | **Não verificável** (Subchave $H' \neq H$) | **Inválida** (Chave desconhecida/não autorizada) | `cryptography.exceptions.InvalidTag` | **REJEITAR** |
| **Parte II — Cenário A** | Contrato original + Assinatura e Certificado legítimos | **Válida** (`Verified OK`) | **Válida** (`parceiro.crt: OK` na Trust Store) | Exit Code `0` em `dgst` e `verify` | **ACEITAR** |
| **Parte II — Cenário B** | Contrato com parcela adulterada (`R$ 120k` $\to$ `R$ 920k`) | **Inválida** (`Verification failure`) | **Válida** (Certificado legítimo do parceiro) | `ossl_rsa_verify:bad signature` (Exit `1`) | **REJEITAR** |
| **Parte II — Cenário C** | Contrato assinado por certificado emitido pela `Rogue CA` | **Válida** (`Verified OK` contra a chave falsa) | **Inválida** (Emissor fora da Trust Store) | `error 20: unable to get local issuer certificate` (Exit `2`) | **REJEITAR** |

### 6.2. Recomendações Técnicas para a Miguelito Segurança e Tecnologia

Com base nas vulnerabilidades demonstradas nos testes, recomendamos quatro diretrizes práticas para a governança criptográfica da Miguelito Segurança e Tecnologia:

1. **Bloqueio de Validação Parcial e Fixação da Trust Store (*Trust Anchor Pinning*):** O sistema de recepção de contratos da empresa deve ser configurado para executar obrigatoriamente a validação da cadeia X.509 (`openssl verify`) apontando exclusivamente para o arquivo `miguelito_root_ca.crt` antes de processar qualquer assinatura digital. Deve-se restringir as permissões de administrador nos servidores para impedir que certificados raiz externos sejam adicionados acidentalmente ao repositório do sistema operacional.
2. **Isolamento da Root CA em HSM e Adoção de Autoridade Intermediária:** Na prática corporativa, a chave privada de 4096 bits da `Miguelito Root CA` não deve ficar armazenada em disco comum nem assinar diretamente certificados de fornecedores. Recomenda-se mantê-la *offline* (dentro de um módulo HSM homologado FIPS 140-3) e utilizá-la apenas para assinar uma **CA Intermediária Emissora** (*Issuing CA*). Assim, o dia a dia de emissão fica restrito à intermediária e, em caso de incidente, basta revogar a intermediária sem perder a âncora raiz.
3. **Implantação de Controle de Revogação (CRL / OCSP) e Checagem de `keyUsage`:** Um certificado dentro do prazo de validade e assinado pela CA correta ainda pode ser perigoso se a chave privada do parceiro tiver sido roubada na semana anterior. Por isso, a Miguelito deve publicar uma **Lista de Certificados Revogados (CRL)** periódica ou operar um serviço **OCSP**, exigindo a flag `-crl_check` na validação. Além disso, o validador deve exigir que o certificado apresentado possua `basicConstraints: CA:FALSE` e os bits `digitalSignature` e `nonRepudiation` habilitados na extensão `keyUsage`.
4. **Gerenciamento Seguro de Nonces e Chaves no AES-256-GCM:** Como o AES-GCM baseia sua confidencialidade no modo contador e sua integridade no polinômio GHASH com subchave fixa $H = E_K(0^{128})$, a reutilização de um mesmo Nonce de 12 bytes com a mesma chave $K$ em dois arquivos diferentes é catastrófica: permite que um atacante elimine o *keystream* aplicando XOR entre os dois textos cifrados e descubra a subchave $H$ resolvendo a equação polinomial resultante em $GF(2^{128})$ (*ataque de reutilização de Nonce*). Recomenda-se gerar Nonces sempre via CSPRNG e rotacionar as chaves simétricas de transporte a cada sessão (por exemplo, combinando troca de chaves efêmera ECDHE ou encapsulamento RSA-OAEP).

---

## 7. Conclusão

O trabalho experimental desenvolvido para o cenário da **Miguelito Segurança e Tecnologia Ltda.** permitiu verificar na prática como diferentes primitivas criptográficas atuam de maneira complementar para proteger documentos comerciais críticos contra fraudes em trânsito e falsificação de autoria.

Nos testes da **Parte I**, comprovamos que a escolha de um modo de cifragem autenticado (AEAD) como o **AES-256-GCM** é indispensável quando se deseja proteger arquivos contra manipulação ativa. Enquanto um modo de cifragem tradicional permitiria que a alteração de 1 byte no meio do arquivo cifrado corrompesse silenciosamente o texto decifrado, a camada algébrica **GHASH** em $GF(2^{128})$ detectou tanto o ataque de *bit-flipping* no offset `1420` quanto a tentativa de leitura com chave espúria, interrompendo a decifragem através da exceção `InvalidTag` antes que qualquer dado corrompido fosse entregue à aplicação.

Nos experimentos da **Parte II**, a construção da PKI com o OpenSSL deixou clara a fronteira entre **integridade de conteúdo** e **confiabilidade de identidade**. O Cenário B demonstrou como o efeito avalanche do **SHA-256** aliado à assinatura RSA impede que cláusulas financeiras sejam alteradas após a assinatura (`Verification failure`). Já o Cenário C ilustrou o ponto mais sensível de uma auditoria de sistemas: uma assinatura digital pode ser matematicamente perfeita (`Verified OK`) e, ainda assim, pertencer a um certificado forjado por uma autoridade ilegítima (`error 20 at 0 depth lookup: unable to get local issuer certificate`). Conclui-se, portanto, que a segurança efetiva do fluxo de contratos da empresa depende da aplicação conjunta da cifragem autenticada AES-256-GCM no transporte e da verificação rigorosa da cadeia de certificação X.509 ancorada na `Miguelito Root CA`.

---

## 8. Referências Bibliográficas

1. **DWORKIN, Morris J.** *Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC*. **NIST Special Publication (SP) 800-38D**, National Institute of Standards and Technology, Gaithersburg, MD, Nov. 2007.
2. **COOPER, D.; SANTESSON, S.; FARRELL, S.; BOEYEN, S.; HOUSLEY, R.; POLK, W.** *Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile*. **IETF RFC 5280**, Maio 2008. Disponível em: `https://datatracker.ietf.org/doc/html/rfc5280`.
3. **MORIARTY, K.; KALISKI, B.; JONSSON, J.; RUSCH, A.** *PKCS #1: RSA Cryptography Specifications Version 2.2*. **IETF RFC 8017**, Nov. 2016. Disponível em: `https://datatracker.ietf.org/doc/html/rfc8017`.
4. **NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST).** *Secure Hash Standard (SHS)*. **FIPS PUB 180-4**, U.S. Department of Commerce, Ago. 2015.
5. **STALLINGS, William.** *Criptografia e Segurança de Redes: Princípios e Práticas*. 8ª ed. São Paulo: Pearson Education, 2023.
6. **PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA).** *Cryptography Documentation — Authenticated Encryption with Associated Data (AESGCM)*. Disponível em: `https://cryptography.io/en/latest/hazmat/primitives/aead/`.
