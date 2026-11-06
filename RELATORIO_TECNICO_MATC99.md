# UNIVERSIDADE FEDERAL DA BAHIA
## INSTITUTO DE COMPUTAÇÃO
### DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO

---

<div align="center">

### MATC99 — SEGURANÇA E AUDITORIA DE SISTEMAS DE INFORMAÇÃO

# TRABALHO 01 — CRIPTOGRAFIA APLICADA: PROTEÇÃO, ASSINATURAS DIGITAIS E CERTIFICADOS

Estudo de Caso: Auditoria de Contratos Digitais na Miguelito Segurança e Tecnologia Ltda.  
Aluno: Wellington Miguel de Jesus Silva  
Local e Data: Salvador — BA, Novembro de 2026  

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

Neste trabalho, analisamos o cenário da empresa fictícia Miguelito Segurança e Tecnologia Ltda. (CNPJ `14.382.910/0001-55`), sediada em Salvador/BA, que atua na operação de sistemas críticos e contrata serviços de nuvem híbrida, links redundantes MPLS/IPSec e custódia de módulos HSM junto a fornecedores externos. Durante uma revisão de auditoria sobre a tramitação do Contrato Comercial nº 2026/00849-MST, celebrado com a fornecedora Parceiro Infraestrutura e Cloud Computing Ltda. (`parceiro.miguelito.com.br`, CNPJ `67.419.002/0001-83`) no valor global de R\$ 1.450.000,00 (dividido em 12 parcelas mensais de R\$ 120.833,33), surgiram indícios de duas falhas graves no processo de troca e validação dos arquivos digitais: a suspeita de manipulação de cláusulas financeiras durante o trânsito do documento e o recebimento de contratos assinados com certificados digitais não reconhecidos pela governança interna.

Do ponto de vista de segurança da informação e perícia forense, o incidente enfrentado pela Miguelito Segurança e Tecnologia envolve três riscos práticos distintos que precisam ser isolados e tratados:

a) Interceptação e modificação em trânsito (*Man-in-the-Middle* / *Bit-Flipping*): contratos comerciais contêm dados bancários, valores de SLA, multas contratuais e especificações técnicas de arquitetura que não podem vazar para terceiros em trânsito (quebra de confidencialidade). Além disso, caso a empresa utilize um algoritmo de cifragem tradicional sem autenticação integrada, um atacante posicionado na rede pode alterar bytes específicos do texto cifrado para modificar valores no texto decifrado sem precisar conhecer a chave secreta;

b) Adulteração documental pós-assinatura: mesmo quando um contrato é assinado por um representante legítimo, existe o risco de o arquivo sofrer modificações posteriores — seja por ação maliciosa interna, seja por interceptação — alterando, por exemplo, o valor da parcela mensal de R\$ 120.833,33 para R\$ 920.833,33. O mecanismo de auditoria precisa detectar alterações mínimas de um único caractere e rejeitar o documento imediatamente;

c) Falsificação de identidade criptográfica (*Key Spoofing* via *Rogue CA*): um invasor externo pode gerar seu próprio par de chaves assimétricas, configurar uma Autoridade Certificadora própria (*Rogue CA*) e emitir um certificado digital preenchido com os mesmos dados cadastrais do fornecedor verdadeiro (`CN = parceiro.miguelito.com.br`). Se o setor responsável pela conferência verificar apenas se a assinatura digital é matematicamente válida contra a chave pública anexada ao processo — esquecendo de verificar quem assinou aquele certificado —, o contrato fraudulento será aceito como se fosse autêntico.

Para responder a esse cenário, este trabalho implementa e documenta uma bancada experimental dividida em duas frentes complementares. Na Parte I, utilizamos a biblioteca `cryptography` do Python para proteger o contrato com a cifra simétrica autenticada AES-256-GCM, testando a recuperação íntegra do arquivo e o comportamento do algoritmo frente à adulteração de bytes no criptograma e ao uso de chaves incorretas. Na Parte II, utilizamos o OpenSSL em ambiente Linux para construir uma Infraestrutura de Chaves Públicas (PKI) completa, confrontando a Autoridade Certificadora interna da empresa (`Miguelito Root CA`) com uma autoridade atacante (`Rogue CA`) ao longo de três cenários de auditoria (Cenários A, B e C).

---

## 2. Fundamentação Teórica

### 2.1. Criptografia Simétrica vs. Criptografia Assimétrica

A escolha entre algoritmos simétricos e assimétricos em uma arquitetura corporativa decorre diretamente das diferenças de desempenho, gestão de chaves e propriedades jurídicas de cada modelo (STALLINGS, 2023).

Na criptografia simétrica, o emissor e o destinatário compartilham exatamente a mesma chave secreta $K$, que é usada tanto na operação de cifragem quanto na decifragem. Algoritmos simétricos modernos, como o AES (*Advanced Encryption Standard*), operam sobre blocos de bits por meio de rodadas sucessivas de substituição, permutação e combinação linear com chaves derivadas. Por serem operações leves e contarem com instruções dedicadas diretamente nos processadores atuais (*AES-NI*), as cifras simétricas atingem taxas de transferência de múltiplos gigabytes por segundo, sendo a única opção viável na prática para cifrar arquivos extensos, bancos de dados e tráfego de rede em tempo real.

Por outro lado, a criptografia simétrica possui duas limitações importantes para ambientes corporativos abertos:

a) Problema da distribuição e escalabilidade de chaves: antes de trocar qualquer contrato cifrado, a Miguelito Segurança e Tecnologia e seu fornecedor precisam compartilhar a chave $K$ por um canal seguro prévio. Em uma rede com $n$ empresas parceiras, seriam necessárias $n(n-1)/2$ chaves secretas distintas para manter o isolamento entre cada par de comunicação;

b) Ausência de não-repúdio (irretratabilidade): como tanto a contratante quanto a contratada possuem a mesma chave $K$, ambas têm capacidade técnica idêntica para gerar um arquivo cifrado e sua respectiva tag de verificação. Em uma disputa judicial, a Miguelito não conseguiria provar a um juiz ou perito externo que determinado arquivo veio exclusivamente do fornecedor, pois a própria Miguelito poderia tê-lo forjado usando a chave compartilhada.

A criptografia assimétrica (ou de chave pública) contorna esses dois limites ao substituir a chave compartilhada por um par de chaves matematicamente vinculadas: uma chave privada (mantida em sigilo absoluto pelo seu titular) e uma chave pública (que pode ser divulgada abertamente a qualquer parceiro). A segurança desse modelo baseia-se em funções de caminho único com alçapão (*trapdoor one-way functions*), nas quais é fácil calcular a função em um sentido usando a chave pública, mas computacionalmente inviável inverter o cálculo sem conhecer a informação secreta contida na chave privada — como ocorre no problema da fatoração de inteiros compostos por dois primos grandes no algoritmo RSA (MORIARTY et al., 2016).

Essa assimetria permite inverter a lógica de operação conforme o objetivo de segurança: para confidencialidade híbrida, qualquer parte usa a chave pública do destinatário para cifrar uma chave de sessão simétrica; já para autenticidade e não-repúdio (assinatura digital), o titular usa sua chave privada exclusiva para assinar o resumo criptográfico de um documento, e qualquer auditor pode usar a chave pública correspondente para conferir a assinatura. Como apenas o titular detém a chave privada, ele não pode negar posteriormente a autoria da assinatura, suprindo a lacuna deixada pela criptografia simétrica.

### 2.2. Funcionamento do Modo AES-GCM e Integridade Autenticada (AEAD)

Durante muitos anos, sistemas corporativos utilizaram cifras de bloco em modos de operação voltados exclusivamente para confidencialidade, como o CBC (*Cipher Block Chaining*) ou o CTR (*Counter Mode*). Embora esses modos escondam o conteúdo do texto em claro contra um observador passivo, eles não oferecem proteção nativa contra um atacante ativo que modifique o texto cifrado em trânsito.

No modo Contador (CTR), a cifra de bloco AES não é aplicada diretamente sobre os blocos do documento original. Em vez disso, o algoritmo recebe um valor público inicial único de 96 bits (12 bytes) chamado *Nonce* (*Number used once*), concatena a ele um contador sequencial de 32 bits (formando o bloco inicial $J_0$) e cifra esse contador com a chave secreta $K$. O fluxo pseudoaleatório resultante (*keystream*) é combinado com cada bloco do texto em claro $P_i$ através da operação lógica XOR ($\oplus$) para produzir o bloco cifrado $C_i$, conforme a Equação (1):

$$C_i = P_i \oplus E_K(\text{inc}_{32}(J_0)) \qquad (1)$$

O perigo de usar o modo CTR isoladamente reside na sua maleabilidade linear: como a decifragem consiste apenas em aplicar novamente a operação XOR entre o bloco cifrado recebido e o mesmo *keystream*, se um invasor interceptar o arquivo no caminho e inverter exatamente um bit em uma posição conhecida do bloco cifrado $C_i$, o processo de decifragem não apresentará nenhum erro e inverterá exatamente o mesmo bit no texto em claro recuperado $P_i$. Em um contrato comercial padronizado onde a posição das cláusulas é previsível, isso permitiria alterar dígitos de valores monetários às cegas (*ataque de bit-flipping*).

Para eliminar essa vulnerabilidade sem precisar configurar um algoritmo de MAC separado, a recomendação NIST SP 800-38D (DWORKIN, 2007) definiu o AES-GCM (*Galois/Counter Mode*), classificado como um esquema AEAD (*Authenticated Encryption with Associated Data*). O AES-GCM une a velocidade do modo contador com um mecanismo algébrico de autenticação chamado GHASH. Primeiro, deriva-se a subchave de autenticação $H = E_K(0^{128})$ cifrando um bloco de 128 bits zero com a chave secreta $K$. Em seguida, o GHASH trata cada bloco de 128 bits dos Dados Associados (AAD) e cada bloco cifrado ($C_1, \dots, C_n$) como coeficientes de um polinômio avaliado na subchave $H$ dentro do corpo finito $GF(2^{128})$, módulo o polinômio irredutível $P(x) = x^{128} + x^7 + x^2 + x + 1$. O resultado do GHASH recebe uma máscara XOR com a cifragem do contador inicial $E_K(J_0)$, originando a *Authentication Tag* $T$ de 128 bits (16 bytes), expressa na Equação (2):

$$T = \text{GHASH}_H(\text{AAD}, \text{Ciphertext}) \oplus E_K(J_0) \qquad (2)$$

O diferencial de segurança do AES-GCM ocorre no momento da decifragem, que segue a regra *Encrypt-then-MAC*: antes de devolver qualquer byte decifrado para o usuário, a função `AESGCM.decrypt()` lê o Nonce, o AAD e os blocos cifrados $C_i$ recebidos, recalcula o polinômio GHASH do zero para obter uma tag local $T'$ e a compara em tempo constante com a tag $T$ anexada ao arquivo. Se um atacante tiver alterado sequer um bit em qualquer bloco $C_i$ (introduzindo uma máscara de erro não nula $\Delta \neq 0$, de forma que $C'_i = C_i \oplus \Delta$), a diferença algébrica $\Delta T = T' \oplus T$ na tag recalculada será dada pela Equação (3):

$$\Delta T = \Delta \cdot H^{n-i+2} \pmod{P(x)} \qquad (3)$$

Como $GF(2^{128})$ é um corpo finito isento de divisores de zero, o produto de dois elementos não nulos ($\Delta \neq 0$ e $H \neq 0$) jamais resulta em zero ($\Delta T \neq 0$). Assim, a tag recalculada $T'$ diverge obrigatoriamente de $T$, fazendo a biblioteca descartar o texto decifrado da memória e interromper a execução com a exceção `InvalidTag`.

### 2.3. Infraestrutura de Chaves Públicas (PKI), Certificados X.509 e Assinaturas RSA

Embora o AES-256-GCM proteja o arquivo em trânsito e em repouso entre sistemas que já compartilham uma chave, ele não substitui a assinatura jurídica de um contrato entre empresas distintas. Para garantir que a fornecedora não possa repudiar o contrato assinado, emprega-se a assinatura digital RSA com SHA-256 segundo o paradigma *Hash-then-Sign* (MORIARTY et al., 2016). Primeiro, o documento passa pela função hash SHA-256 (NIST, 2015), que comprime o arquivo em um resumo fixo de 256 bits (32 bytes) dotado de efeito avalanche e resistência a colisões. No esquema RSASSA-PKCS1-v1_5 (ou de modo probabilístico no RSA-PSS), o hash de 32 bytes e o identificador (OID) do algoritmo SHA-256 são encapsulados em uma estrutura ASN.1 (`DigestInfo`) com preenchimento até o tamanho do módulo RSA (256 bytes para chaves de 2048 bits), formando o bloco codificado $EM$. A geração da assinatura $S$ com a chave privada $(d, N)$ e a sua verificação com a chave pública $(e, N)$ seguem a Equação (4):

$$S = EM^d \bmod N \quad \text{e} \quad EM' = S^e \bmod N \qquad (4)$$

Todavia, a operação matemática da Equação (4) valida apenas que a assinatura foi produzida pelo detentor da chave privada correspondente àquela chave pública, mas não prova a quem pertence essa chave pública. Para vincular formalmente uma identidade jurídica a uma chave pública, utiliza-se a Infraestrutura de Chaves Públicas (PKI) e os certificados X.509 v3 padronizados pela RFC 5280 (COOPER et al., 2008). A organização institui uma Autoridade Certificadora Raiz (*Root CA*) — neste estudo, a `Miguelito Root CA` — cujo certificado autoassinado é instalado na *Trust Store* corporativa. A Root CA assina digitalmente o certificado do fornecedor (`parceiro.crt`), amarrando seu nome (`Subject: CN = parceiro.miguelito.com.br`) à sua chave pública e fixando extensões críticas (`basicConstraints: CA:FALSE` e `keyUsage: digitalSignature, nonRepudiation`). Dessa forma, a auditoria de um contrato assinado exige sempre duas checagens conjuntas: a verificação matemática da assinatura e a validação da cadeia X.509 até a Root CA corporativa (incluindo checagem de revogação via CRL ou OCSP).

---

## 3. Metodologia e Ambiente Experimental

Para validar experimentalmente os conceitos discutidos na fundamentação teórica, construímos dois scripts automatizados em ambiente Linux (executados via WSL2), mantendo o registro de todos os comandos, tamanhos de arquivos, números de série e resumos SHA-256 em arquivos de log dedicados. A Tabela 1 apresenta a especificação técnica do ambiente experimental utilizado.

**Tabela 1 – Especificação técnica do ambiente experimental e ferramentas de auditoria**

| Componente / Ferramenta | Versão / Especificação | Finalidade nos Experimentos |
| :--- | :--- | :--- |
| Sistema Operacional | Ubuntu 24.04 LTS (Kernel Linux 6.6.87.2-WSL2 x86_64) | Ambiente POSIX isolado para execução dos scripts e coleta de logs. |
| Interpretador Python | Python 3.12.3 (WSL) / Python 3.13.14 (Host) | Execução do script modular `parte1_aes_gcm.py`. |
| Biblioteca `cryptography` | v41.0.7 / v50.0.2 (PyCA `AESGCM`) | Implementação do AES-256-GCM e captura da exceção `InvalidTag`. |
| Suíte OpenSSL CLI | OpenSSL 3.0.13 (30 Jan 2024) | Geração de chaves RSA 4096/2048 bits, emissão X.509 v3, `dgst` e `verify`. |
| Contrato Comercial Base | `contrato_miguelito.txt` (2.841 bytes, UTF-8) | Contrato nº 2026/00849-MST firmado pela Miguelito Segurança e Tecnologia. |

Fonte: O autor (2026).

---

## 4. Experimentos da Parte I: Proteção e Integridade com AES-256-GCM

### 4.1. Procedimentos de Cifragem, Empacotamento e Decifragem

O script `parte1_aes_gcm.py` foi estruturado de forma modular utilizando uma classe de dados (`CriptogramaGCM`) para manipular separadamente os componentes gerados pela cifra autenticada. O fluxo experimental seguiu três etapas iniciais para estabelecer a linha de base legítima:

a) Carregamento e hash do contrato original: o arquivo `contrato_miguelito.txt` foi lido em modo binário, contabilizando exatos 2.841 bytes. Registrou-se o resumo SHA-256 do documento em claro (`9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67`) para conferência pós-decifragem;

b) Geração de parâmetros e cifragem AES-256-GCM: utilizando o gerador seguro do sistema operacional (`os.urandom`), foram gerados uma chave simétrica de 256 bits (32 bytes) e um Nonce exclusivo de 96 bits (12 bytes). Como Dados Associados (AAD), definiu-se o contexto `MATC99-UFBA|MIGUELITO-SEGURANCA-E-TECNOLOGIA|CONTRATO-2026-00849`. O arquivo binário `contrato_miguelito.enc` foi gravado empacotando sequencialmente o Nonce (12 bytes), o texto cifrado (2.841 bytes) e a *Authentication Tag* (16 bytes), totalizando 2.869 bytes;

c) Decifragem legítima e conferência byte a byte: o script leu os 2.869 bytes de `contrato_miguelito.enc`, desempacotou o Nonce e submeteu o criptograma e a Tag ao método `AESGCM.decrypt()`. A validação do polinômio GHASH ocorreu sem erros, gerando o arquivo `contrato_miguelito_recuperado.txt` com 2.841 bytes e hash SHA-256 idêntico ao original (`original == recuperado: True`).

### 4.2. Logs de Execução e Análise dos Cenários de Falha

Após comprovar o funcionamento do fluxo legítimo, o script executou automaticamente dois testes de falha exigidos pela auditoria, capturando as exceções lançadas pela biblioteca. O Quadro 1 reproduz o log de execução gravado pelo script `parte1_aes_gcm.py`.

**Quadro 1 – Log de execução da Parte I: cifragem legítima e testes de falha no AES-256-GCM**

```text
[2026-11-04 15:36:36.889] [INFO] === Auditoria Criptográfica - Miguelito Segurança e Tecnologia (Parte I: AES-256-GCM) ===
[2026-11-04 15:36:36.894] [INFO] Contrato carregado: contrato_miguelito.txt (2841 bytes)
[2026-11-04 15:36:36.895] [INFO] SHA-256 original: 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:36.901] [INFO] Arquivo cifrado salvo em: contrato_miguelito.enc (2869 bytes totais)
[2026-11-04 15:36:36.901] [INFO]   Chave AES-256 (32B) : 185c3c58dc5153a9b84ddaf0b85ec9933e52f67c44f8d150f42151a460aa8a28
[2026-11-04 15:36:36.902] [INFO]   Nonce / IV (12B)    : 1d5d2cb6580417d1f29dbf07
[2026-11-04 15:36:36.903] [INFO]   Auth Tag (16B)      : f987ee9b9f25a4ea8cbcac904a675b94
[2026-11-04 15:36:36.909] [INFO] Comparação de bytes (original == recuperado): True (2841 bytes)
[2026-11-04 15:36:36.910] [INFO] --- [Teste de Falha 1: Adulteração de 1 byte no Ciphertext (Bit-Flipping)] ---
[2026-11-04 15:36:36.910] [INFO] Byte modificado no offset 1420 (0x058C): 0x4B -> 0x4A
[2026-11-04 15:36:36.910] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag
[2026-11-04 15:36:36.911] [INFO] --- [Teste de Falha 2: Tentativa de Decifragem com Chave Incorreta] ---
[2026-11-04 15:36:36.912] [INFO] Chave errada  : 8908f8e494c7d2089963f9ca67836a1d43bfc0a0ea511d3343b5c0a40d8df58e
[2026-11-04 15:36:36.912] [WARNING] Exceção capturada com sucesso: cryptography.exceptions.InvalidTag
```

Fonte: O autor (2026).

A análise técnica dos dois eventos registrados no Quadro 1 demonstra a eficácia do controle AEAD: no Teste de Falha 1 (*Bit-Flipping* no offset 1420), modificamos apenas o bit menos significativo do byte localizado na metade do texto cifrado (posição `0x058C`, alterando seu valor de `0x4B` para `0x4A` via `XOR 0x01`). Mesmo utilizando a chave legítima e o Nonce correto, a rotina `AESGCM.decrypt()` recusou o pacote e disparou `cryptography.exceptions.InvalidTag`, confirmando que o polinômio GHASH em $GF(2^{128})$ detectou a perturbação no 89º bloco de 128 bits, conforme previsto pela Equação (3). No Teste de Falha 2 (Chave Simétrica Incorreta), mantivemos o arquivo `contrato_miguelito.enc` intacto, mas tentamos decifrá-lo com uma chave espúria (`8908f8e4...`). Como essa chave gera uma subchave $H'$ e uma máscara de contador $E_{K'}(J_0)$ distintas das originais, a verificação da tag de 128 bits falhou imediatamente, lançando novamente `cryptography.exceptions.InvalidTag`.

### 4.3. Propriedades de Segurança Garantidas

Com a implementação do AES-256-GCM validada na Parte I, o fluxo de arquivos da Miguelito Segurança e Tecnologia passa a contar com três garantias simultâneas: confidencialidade (nenhum observador sem a chave de 256 bits consegue ler as cláusulas do contrato), integridade do criptograma e de seus metadados (qualquer alteração de 1 bit no Nonce, no AAD, no texto cifrado ou na Tag provoca rejeição imediata via `InvalidTag`) e autenticidade simétrica de origem (a validação da Tag comprova que o arquivo foi cifrado por quem detém a chave secreta compartilhada).

---

## 5. Experimentos da Parte II: Assinaturas Digitais e Cadeia de Certificação

### 5.1. Estrutura da PKI Simulada (CA Corporativa vs. Rogue CA)

Para avaliar os riscos de adulteração pós-assinatura e de uso de certificados falsos, o script `parte2_pki_testes.sh` automatizou a criação do diretório `pki_miguelito/` contendo duas cadeias de certificação X.509 v3 independentes:

a) Cadeia Corporativa Legítima (*Trust Store* da Miguelito): composta pela Autoridade Raiz `Miguelito Root CA` (chave RSA de 4096 bits, certificado autoassinado `miguelito_root_ca.crt`, Serial `362E0342B4975053DE63770150A88BC71BAE2D96`, com `basicConstraints = critical, CA:true, pathlen:0`) e pelo certificado de entidade final do fornecedor legítimo (`parceiro.crt`, chave RSA de 2048 bits, `CN = parceiro.miguelito.com.br`, Serial `21CFB1F05A7A7751254A5581A3A6F65759E6BCC2`, assinado pela `Miguelito Root CA` com `CA:FALSE` e `keyUsage = critical, digitalSignature, nonRepudiation`);

b) Cadeia Externa Não Confiável (Infraestrutura Atacante): composta pela `Rogue Root CA` (chave RSA de 4096 bits e certificado autoassinado `rogue_root_ca.crt`, ausente da *Trust Store* da Miguelito) e pelo certificado forjado (`parceiro_forjado.crt`, Serial `35D9F02AD06A2A5EFB2A238DE860B45B0F657127`), que copia exatamente o mesmo `Subject` do fornecedor verdadeiro (`CN = parceiro.miguelito.com.br`), mas é assinado pela `Rogue Root CA`.

### 5.2. Análise do Cenário A: Documento Íntegro e Cadeia Válida

No Cenário A, simulamos o fluxo normal e legítimo de assinatura e auditoria do contrato comercial. Primeiro, o documento original foi assinado com a chave privada legítima do parceiro; em seguida, o auditor validou a assinatura matemática usando a chave pública extraída do certificado e conferiu a cadeia do certificado contra a `Miguelito Root CA`, conforme apresentado no Quadro 2.

**Quadro 2 – Comandos OpenSSL e log de verificação do Cenário A (Fluxo Legítimo)**

```text
# Comandos executados no Cenário A:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_legitimo/parceiro.key \
    -out cenario_a.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature cenario_a.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_legitimo/parceiro.crt

# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.697] [INFO] Assinatura gerada: cenario_a.sig (256 bytes)
[2026-11-04 15:36:40.721] [INFO] Verificação da assinatura (openssl dgst -verify): Verified OK
[2026-11-04 15:36:40.743] [INFO] Validação da cadeia contra Miguelito Root CA: parceiro.crt: OK
[2026-11-04 15:36:40.750] [INFO] Resultado Cenário A -> DECISÃO: ACEITAR
```

Fonte: O autor (2026).

No Cenário A (Decisão: ACEITAR), o arquivo de assinatura `cenario_a.sig` (256 bytes) retornou `Verified OK`, provando que nenhum byte de `contrato_miguelito.txt` foi modificado após a assinatura. Paralelamente, o comando `openssl verify` retornou `parceiro.crt: OK`, confirmando que o certificado do fornecedor possui assinatura válida da `Miguelito Root CA` e respeita todas as restrições X.509 v3. Com integridade documental e autenticidade de identidade comprovadas, o contrato é aceito com garantia de não-repúdio.

### 5.3. Análise do Cenário B: Adulteração de Conteúdo Pós-Assinatura

No Cenário B, testamos o que acontece quando um contrato legitimamente assinado no Cenário A sofre uma adulteração financeira antes de ser auditado. Utilizando o utilitário `sed`, modificamos apenas um dígito na Cláusula Segunda do contrato, alterando o valor da parcela mensal de `R$ 120.833,33` para `R$ 920.833,33` (troca do caractere `'1'` pelo `'9'`), e submetemos o arquivo fraudado à verificação com a assinatura original, conforme detalhado no Quadro 3.

**Quadro 3 – Comandos e log de verificação do Cenário B (Adulteração Pós-Assinatura)**

```text
# Comandos executados no Cenário B:
$ sed 's/R\$ 120\.833,33/R\$ 920.833,33/g' contrato_miguelito.txt > contrato_adulterado.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_legitimo/parceiro_pub.pem \
    -signature cenario_a.sig contrato_adulterado.txt

# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.824] [INFO] SHA-256 original   : 9147c03987856361e26a46f794f9588fe0850329cc2eaa28d5f0fd6ffe0cfe67
[2026-11-04 15:36:40.832] [INFO] SHA-256 adulterado : 817d7fae7346f151320d2469a8546c52edefa478219948e1efbb75edf9f0a8d2
[2026-11-04 15:36:40.856] [WARN] Código de saída do OpenSSL: 1
  40C71E4E407F0000:error:02000068:rsa routines:ossl_rsa_verify:bad signature:../crypto/rsa/rsa_sign.c:430:
  Verification failure
[2026-11-04 15:36:40.868] [WARN] Resultado Cenário B -> DECISÃO: REJEITAR
```

Fonte: O autor (2026).

No Cenário B (Decisão: REJEITAR), embora o certificado do parceiro continue sendo legítimo, a alteração de um único caractere no texto provocou o efeito avalanche na função SHA-256, mudando o resumo do documento de `9147c039...` para `817d7fae...`. Quando a rotina interna `ossl_rsa_verify` decifrou o bloco PKCS#1 v1.5 contido em `cenario_a.sig` usando a chave pública do parceiro, ela encontrou o hash original (`9147c039...`). Como os dois resumos divergem e o atacante não possui a chave privada do parceiro para recalcular uma nova assinatura válida sobre o texto fraudado, o OpenSSL encerrou com código de erro `1` (`bad signature` / `Verification failure`). O contrato deve ser imediatamente rejeitado por violação de integridade pós-assinatura.

### 5.4. Análise do Cenário C: Certificado Emitido por Autoridade Não Confiável

No Cenário C, simulamos um ataque de falsidade ideológica (*spoofing* de identidade): o atacante toma o contrato original sem alterar uma única palavra, mas o assina usando a chave privada do certificado falso (`parceiro_forjado.key`) emitido pela `Rogue CA` em nome de `parceiro.miguelito.com.br`. O Quadro 4 apresenta os comandos e logs obtidos nas duas etapas da auditoria.

**Quadro 4 – Comandos e log de verificação do Cenário C (Certificado Forjado por Rogue CA)**

```text
# Comandos executados no Cenário C:
$ openssl dgst -sha256 -sign pki_miguelito/parceiro_forjado/parceiro_forjado.key \
    -out cenario_c_forjado.sig contrato_miguelito.txt
$ openssl dgst -sha256 -verify pki_miguelito/parceiro_forjado/parceiro_forjado_pub.pem \
    -signature cenario_c_forjado.sig contrato_miguelito.txt
$ openssl verify -CAfile pki_miguelito/root_ca/miguelito_root_ca.crt \
    pki_miguelito/parceiro_forjado/parceiro_forjado.crt

# Evidências coletadas em parte2_pki_testes.log:
[2026-11-04 15:36:40.927] [INFO] 1) Verificação matemática com a chave pública do certificado falso: Verified OK
[2026-11-04 15:36:40.949] [WARN] 2) Validação da cadeia contra a Trust Store da Miguelito (Exit Code 2):
  C = BR, ST = Sao Paulo, L = Sao Paulo, O = Parceiro Infraestrutura e Cloud Computing Ltda, CN = parceiro.miguelito.com.br
  error 20 at 0 depth lookup: unable to get local issuer certificate
  error pki_miguelito/parceiro_forjado/parceiro_forjado.crt: verification failed
[2026-11-04 15:36:40.962] [WARN] Resultado Cenário C -> DECISÃO: REJEITAR
```

Fonte: O autor (2026).

No Cenário C (Decisão: REJEITAR), fica evidente a diferença entre integridade matemática e autenticidade da origem. Na primeira etapa, o comando `openssl dgst -verify` retornou `Verified OK` porque o par de chaves do atacante é matematicamente consistente: a chave pública presente em `parceiro_forjado.crt` de fato decifra a assinatura feita por `parceiro_forjado.key` e o documento não foi modificado desde que o atacante o assinou. Todavia, quando passamos para a segunda etapa (`openssl verify`), o verificador inspeciona o certificado no nível 0 da cadeia (`at 0 depth lookup`), lê o campo emissor (`Issuer: CN = Rogue Root CA`) e tenta localizar o certificado dessa autoridade dentro da *Trust Store* oficial da empresa (`miguelito_root_ca.crt`). Como a `Rogue Root CA` não é reconhecida pela Miguelito Segurança e Tecnologia, a construção da cadeia de confiança falha com o erro `error 20 at 0 depth lookup: unable to get local issuer certificate` (código de saída `2`). Portanto, apesar de haver integridade matemática isolada, não há autenticidade da identidade do emissor, exigindo a rejeição imediata do documento.

---

## 6. Matriz de Decisão e Recomendações de Governança

### 6.1. Matriz Comparativa de Auditoria

A Tabela 2 consolida os resultados experimentais obtidos nas Partes I e II, relacionando a integridade matemática do conteúdo, a confiabilidade da chave ou identidade apresentada e o veredito final de auditoria.

**Tabela 2 – Matriz comparativa de decisão pericial e resultados experimentais (Partes I e II)**

| Cenário Auditado | Controle Testado | Integridade Matemática | Confiabilidade da Identidade | Evidência Técnica (Python / OpenSSL) | Veredito Final |
| :--- | :--- | :---: | :---: | :--- | :---: |
| Parte I — Base Legítima | Decifragem AES-256-GCM com arquivo e chave íntegros | Válida (Tag GCM e SHA-256 conferem) | Válida (Posse da chave simétrica legítima) | Sem exceções; 2.841 bytes recuperados | ACEITAR |
| Parte I — Falha 1 (Bit-Flipping) | Adulteração de 1 byte no ciphertext (Offset 1420) | Inválida (Polinômio GHASH diverge) | Válida (Chave simétrica correta utilizada) | `cryptography.exceptions.InvalidTag` | REJEITAR |
| Parte I — Falha 2 (Chave Espúria) | Tentativa de decifragem com chave de 256 bits incorreta | Não verificável (Subchave $H' \neq H$) | Inválida (Chave desconhecida) | `cryptography.exceptions.InvalidTag` | REJEITAR |
| Parte II — Cenário A | Contrato original + Assinatura e Certificado legítimos | Válida (`Verified OK`) | Válida (`parceiro.crt: OK` na Trust Store) | Exit Code `0` em `dgst` e `verify` | ACEITAR |
| Parte II — Cenário B | Contrato com parcela adulterada (R\$ 120k para R\$ 920k) | Inválida (`Verification failure`) | Válida (Certificado legítimo do parceiro) | `ossl_rsa_verify:bad signature` (Exit `1`) | REJEITAR |
| Parte II — Cenário C | Contrato assinado por certificado emitido pela Rogue CA | Válida (`Verified OK` na chave falsa) | Inválida (Emissor fora da Trust Store) | `error 20: unable to get local issuer certificate` | REJEITAR |

Fonte: O autor (2026).

### 6.2. Recomendações Técnicas para a Miguelito Segurança e Tecnologia

Com base nas vulnerabilidades demonstradas nos testes, recomendamos quatro diretrizes práticas para a governança criptográfica da Miguelito Segurança e Tecnologia:

a) Bloqueio de validação parcial e fixação da *Trust Store* (*Trust Anchor Pinning*): o sistema de recepção de contratos da empresa deve executar obrigatoriamente a validação da cadeia X.509 (`openssl verify`) apontando exclusivamente para o arquivo `miguelito_root_ca.crt` antes de processar qualquer assinatura digital. Deve-se restringir as permissões de administrador nos servidores para impedir que certificados raiz externos sejam adicionados acidentalmente ao repositório do sistema operacional;

b) Isolamento da Root CA em HSM e adoção de Autoridade Intermediária: na prática corporativa, a chave privada de 4096 bits da `Miguelito Root CA` não deve ficar armazenada em disco comum nem assinar diretamente certificados de fornecedores. Recomenda-se mantê-la *offline* (dentro de um módulo HSM homologado FIPS 140-3) e utilizá-la apenas para assinar uma CA Intermediária Emissora (*Issuing CA*). Assim, o dia a dia de emissão fica restrito à intermediária e, em caso de incidente, basta revogar a intermediária sem perder a âncora raiz;

c) Implantação de controle de revogação (CRL / OCSP) e checagem de `keyUsage`: um certificado dentro do prazo de validade e assinado pela CA correta ainda pode ser perigoso se a chave privada do parceiro tiver sido comprometida. Por isso, a Miguelito deve publicar uma Lista de Certificados Revogados (CRL) periódica ou operar um serviço OCSP, exigindo a flag `-crl_check` na validação, além de verificar se o certificado apresentado possui `basicConstraints: CA:FALSE` e os bits `digitalSignature` e `nonRepudiation` habilitados na extensão `keyUsage`;

d) Gerenciamento seguro de Nonces e chaves no AES-256-GCM: como o AES-GCM baseia sua confidencialidade no modo contador e sua integridade no polinômio GHASH com subchave fixa $H = E_K(0^{128})$, a reutilização de um mesmo Nonce de 12 bytes com a mesma chave $K$ em dois arquivos diferentes permite que um atacante elimine o *keystream* aplicando XOR entre os dois textos cifrados e recupere a subchave $H$ resolvendo a equação polinomial resultante em $GF(2^{128})$. Recomenda-se gerar Nonces sempre via CSPRNG e rotacionar as chaves simétricas de transporte a cada sessão (por exemplo, combinando troca de chaves efêmera ECDHE ou encapsulamento RSA-OAEP).

---

## 7. Conclusão

O trabalho experimental desenvolvido para o cenário da Miguelito Segurança e Tecnologia Ltda. permitiu verificar na prática como diferentes primitivas criptográficas atuam de maneira complementar para proteger documentos comerciais críticos contra fraudes em trânsito e falsificação de autoria.

Nos testes da Parte I, comprovamos que a escolha de um modo de cifragem autenticado (AEAD) como o AES-256-GCM é indispensável quando se deseja proteger arquivos contra manipulação ativa. Enquanto um modo de cifragem tradicional permitiria que a alteração de 1 byte no meio do arquivo cifrado corrompesse silenciosamente o texto decifrado, a camada algébrica GHASH em $GF(2^{128})$ detectou tanto o ataque de *bit-flipping* no offset 1420 quanto a tentativa de leitura com chave espúria, interrompendo a decifragem através da exceção `InvalidTag` antes que qualquer dado corrompido fosse entregue à aplicação.

Nos experimentos da Parte II, a construção da PKI com o OpenSSL deixou clara a fronteira entre integridade de conteúdo e confiabilidade de identidade. O Cenário B demonstrou como o efeito avalanche do SHA-256 aliado à assinatura RSA impede que cláusulas financeiras sejam alteradas após a assinatura (`Verification failure`). Já o Cenário C ilustrou o ponto mais sensível de uma auditoria de sistemas: uma assinatura digital pode ser matematicamente perfeita (`Verified OK`) e, ainda assim, pertencer a um certificado forjado por uma autoridade ilegítima (`error 20 at 0 depth lookup: unable to get local issuer certificate`). Conclui-se, portanto, que a segurança efetiva do fluxo de contratos da empresa depende da aplicação conjunta da cifragem autenticada AES-256-GCM no transporte e da verificação rigorosa da cadeia de certificação X.509 ancorada na `Miguelito Root CA`.

---

## 8. Referências Bibliográficas

COOPER, D.; SANTESSON, S.; FARRELL, S.; BOEYEN, S.; HOUSLEY, R.; POLK, W. **Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile**. [S. l.]: Internet Engineering Task Force (IETF), RFC 5280, maio 2008. Disponível em: \<https://datatracker.ietf.org/doc/html/rfc5280\>. Acesso em: 04 nov. 2026.

DWORKIN, Morris J. **Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC**. Gaithersburg, MD: National Institute of Standards and Technology (NIST), Special Publication 800-38D, nov. 2007.

MORIARTY, K.; KALISKI, B.; JONSSON, J.; RUSCH, A. **PKCS #1: RSA Cryptography Specifications Version 2.2**. [S. l.]: Internet Engineering Task Force (IETF), RFC 8017, nov. 2016. Disponível em: \<https://datatracker.ietf.org/doc/html/rfc8017\>. Acesso em: 04 nov. 2026.

NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). **FIPS PUB 180-4: Secure Hash Standard (SHS)**. Gaithersburg, MD: U.S. Department of Commerce, ago. 2015.

PYTHON CRYPTOGRAPHIC AUTHORITY (PyCA). **Cryptography Documentation: Authenticated Encryption with Associated Data (AESGCM)**. [S. l.]: PyCA, 2026. Disponível em: \<https://cryptography.io/en/latest/hazmat/primitives/aead/\>. Acesso em: 04 nov. 2026.

STALLINGS, William. **Criptografia e segurança de redes: princípios e práticas**. 8. ed. São Paulo: Pearson Education, 2023.
