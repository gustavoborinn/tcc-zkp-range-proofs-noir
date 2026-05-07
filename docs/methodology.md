# 3. Metodologia de Pesquisa

A presente pesquisa propõe o desenvolvimento, a implementação e a avaliação empírica de desempenho de um circuito criptográfico do tipo *Range Proof* construído no ecossistema Noir. O objetivo central é avaliar empiricamente o custo computacional e a degradação de desempenho deste circuito, quantificando o impacto arquitetural do ambiente de execução (Nativo vs. WASM32) e o peso criptográfico da imposição de diferentes larguras de bits ($u8$, $u32$, $u64$) sobre o tempo de geração da prova, tamanho do artefato e custo de verificação na EVM. O delineamento metodológico está estruturado para garantir a validade científica da avaliação perante as limitações práticas de infraestrutura Web3 (EVM pós-Pectra e arquitetura WASM32).

## 3.1 Classificação da Pesquisa e Fixação Tecnológica (Stack Pinning)

Para garantir a reprodutibilidade e evitar a quebra de compatibilidade em um ecossistema em rápida evolução, o ambiente de desenvolvimento é estritamente fixado:
* **Compilador de Circuito:** Noir CLI (`nargo` versão $\ge 0.38.0$).
* **Backend Criptográfico e Gerador de Verificador:** Barretenberg CLI (`bb` versão correspondente ao `nargo`), operando sob o esquema **UltraHonk**.
* **Alvo de Deploy e Instrumentação:** Rede de testes Sepolia (Ethereum). Para fins de instrumentação rigorosa de *Gas* (detalhada na Seção 3.4), as transações de verificação serão simuladas em um *fork* local espelhando o estado exato do bloco mais recente da Sepolia (via `anvil`), garantindo equivalência com a rede pública, porém isolando a coleta métrica contra restrições de *rate limit* e ruídos de *mempool*.

A pesquisa caracteriza-se como **Aplicada com Avaliação de Desempenho**, orientada por métricas quantitativas e testes de dominância estocástica robustos a ambientes ruidosos.

## 3.2 Formulação das Hipóteses Estatísticas

A testagem estatística será restrita às variáveis empíricas que apresentam flutuação estocástica (Tempo de Geração da Prova). Variáveis de natureza determinística (Contagem de Gates, Tamanho da Prova e *Execution Gas*) não serão submetidas a testes de hipóteses, sendo analisadas via comparação analítica exata. 

Devido à natureza multimodal da latência no ambiente WASM32, a avaliação das hipóteses empíricas será amparada por testes não paramétricos de igualdade estocástica (Teste de Brunner-Munzel).

**Eixo A: Impacto Arquitetural do Ambiente de Execução**
Avalia a variável estocástica (Tempo de Prova) frente ao ambiente de execução.
* **Hipótese Nula ($H_0$):** Não há diferença estocástica no tempo de geração da prova entre a execução nativa e a execução via WebAssembly. A probabilidade de uma prova gerada nativamente ($X$) ser mais rápida do que uma gerada em WASM ($Y$) é igual a 0,5 ($P(X < Y) + 0.5 \cdot P(X = Y) = 0.5$).
* **Hipótese Alternativa ($H_1$):** Existe dominância estocástica da execução nativa sobre o ambiente WASM. O ambiente web apresenta latência estatisticamente superior ($P(X < Y) + 0.5 \cdot P(X = Y) \neq 0.5$), ocasionada pelos gargalos do motor V8 (rotinas de *Garbage Collection* e restrições de concorrência de *threads*).

**Eixo B: Custo Empírico da Restrição de Intervalo (Bit-width)**
Avalia o impacto empírico do processamento criptográfico exigido por diferentes larguras de bits.
* **Hipótese Nula ($H_0$):** A imposição de limites de intervalo estritos ($u8$, $u32$, $u64$) não gera diferença estatisticamente significativa no tempo de geração da prova em comparação a um circuito de linha de base utilizando o tipo irrestrito (`Field`).
* **Hipótese Alternativa ($H_1$):** A restrição da largura de bits incrementa significativamente a latência de geração da prova em relação à linha de base, refletindo o *overhead* computacional no momento de prover as *Lookup Tables* do esquema UltraHonk.

## 3.3 Delineamento Experimental e Variáveis de Controle

O escopo isola lógicas de negócios complexas. O experimento foca na instrumentação das seguintes variáveis independentes:

* **Controle de Largura de Bits (Bit-width) e Linha de Base:** O tamanho do *input* $v$ no intervalo $a \le v \le b$ será testado variando as restrições de inteiros ($u8$, $u32$, $u64$). Para mitigar o custo fixo das tabelas de busca (*Lookup Tables*) inerentes ao UltraHonk, um circuito idêntico utilizando o tipo matemático irrestrito `Field` será usado como "linha de base", isolando o custo puramente imposto pela restrição de intervalo.
* **Controle de Degradação de Ambiente (WASM32 vs Nativo):** A latência do lado do cliente (Prover) será testada sob duas condições:
    1.  **Execução Nativa:** Terminal (`bb prove`), com acesso direto à memória do SO.
    2.  **Execução em WebAssembly (WASM):** Ambiente navegador (Chrome $\ge 133$) utilizando o artefato `bb-threads.wasm`. O experimento reconhece o limite estrutural do compilador *wasm32* (teto de 4 GiB e limite de $2^{19}$ *gates*) e fará o provisionamento obrigatório de cabeçalhos COOP/COEP (*Cross-Origin Isolation*) para habilitar o *SharedArrayBuffer* e o paralelismo.

**Fase 1: Construção e Deploy sob EIP-170**
Compilação do código Noir para representação intermediária (ACIR), seguida pela geração do *Smart Contract* verificador Solidity via `bb write_solidity_verifier`. Para transpor o limite estrito de tamanho de contrato da EVM (EIP-170, max 24.5 KB) — frequentemente excedido por verificadores UltraHonk genéricos (~33 KB) —, o artefato será submetido a *tuning* agressivo no compilador Solidity (`optimizer_runs = 1`). Caso a complexidade do circuito invalide o otimizador, a topologia de *Split-Verifier* (bibliotecas acopladas) será adotada para garantir o deploy na Sepolia.

**Fase 2: Instrumentação Estatística e Isolamento de Ambiente (Heavy-Tailed Benchmarking)**
A coleta empírica da latência (*Proving Time*) operará sob um protocolo estrito de controle de estado para isolar o custo criptográfico e mitigar artefatos metodológicos inerentes à compilação dinâmica (JIT) e ao gerenciamento de memória. O delineamento obedece à seguinte estrutura:
1. **Protocolo de Aquecimento (Burn-in e Mitigação de Cold-Start):** Antes do registro de métricas, cada ambiente executará $K = 15$ provas iniciais de aquecimento, que serão sumariamente descartadas. No ambiente WASM32, este passo é obrigatório para forçar o processo de *tier-up* do motor V8, garantindo que o código WebAssembly transite do compilador de *baseline* (Liftoff) para o compilador otimizado (TurboFan). Isso isola a latência pura de execução criptográfica do *overhead* de compilação.
2. **Tamanho Amostral, Execução Contínua e Randomização em Blocos:** Após o *burn-in*, serão executados e registrados $N = 100$ ciclos independentes de prova por condição experimental (combinação de ambiente e largura de bits). A rotina não forçará a limpeza de memória (*Garbage Collection*) via *flags* do navegador entre os ciclos de teste, preservando a validade ecológica do experimento. Para garantir que o estado cumulativo do *heap* atue puramente como ruído estocástico e não como variável confundidora, **a ordem de execução das condições experimentais (`Field`, $u8$, $u32$, $u64$) será rigorosamente randomizada em blocos** ao longo das sessões de benchmarking.
3. **Parametrização, Controle de Erro e Tratamento de Falhas Sistêmicas:** O teste empírico adotará um nível de significância basal de $\alpha = 0,05$ (bicaudal). A amostragem de $N = 100$ assegura poder estatístico para a aproximação assintótica do Teste de Brunner-Munzel. Para o Eixo B, que exige múltiplas comparações simultâneas contra a linha de base (`Field`), a inflação do Erro Tipo I (*Family-Wise Error Rate*) será controlada mediante a aplicação do **método de Holm-Bonferroni**. Excepcionalmente, caso gargalos estruturais do ambiente WASM32 (como *Out of Memory* no V8) resultem em falha de geração em mais de 15% da amostra ($n < 85$) em uma dada condição, a análise de latência para esse vetor será suspensa, e o resultado será categorizado quantitativamente pela sua **Taxa de Falha (Failure Rate)**, reportando a inviabilidade arquitetural da execução.

**Fase 3: Auditoria de Correção Lógica (Qualitativa)**
Validação de *soundness* lógica (*Under-constrained Testing*). Execução de testes negativos submetendo *inputs* fora do intervalo permitido, assegurando (Pass/Fail) a ausência de vulnerabilidades estruturais antes da coleta de desempenho.

## 3.4 Variáveis e Métricas de Avaliação Quantitativa

A viabilidade do sistema será determinada por dois grupos de métricas: empíricas (sujeitas à variância) e determinísticas (estáticas por compilação).

**Métricas Empíricas (Avaliação Estocástica):**
1.  **Tempo de Geração da Prova (Proving Time):** Mensurado em milissegundos do lado do cliente (Prover). A análise de degradação ambiente dispensará testes baseados em normalidade (Teste t). A avaliação será conduzida via Análise Visual Exploratória (Gráficos de Violino e Funções de Distribuição Cumulativa Empírica - ECDF) suportada pelo **Teste de Brunner-Munzel**, garantindo validade matemática perante a assimetria extrema introduzida pelo motor V8 no WASM.

**Métricas Determinísticas (Avaliação Comparativa Exata):**
2.  **Custo Computacional e de Dados (Gas Cost EVM Pectra):** Fracionado estruturalmente e avaliado em ambiente estéril. Para mitigar ruídos de *mempool*, latência de propagação e restrições de *rate limit* de nós RPC públicos, a instrumentação das transações de verificação ocorrerá em um **Fork Local da rede Sepolia** (via `anvil` ou similar), operando no bloco mais recente disponível. Os dados serão extraídos dos *transaction receipts* simulados:
    * *Execution Gas:* Custo puro das operações de validação matemática na EVM executadas pelo verificador Solidity. O determinismo absoluto desta métrica é garantido pela natureza estruturalmente *stateless* (sem estado) do contrato gerado pelo `bb`, que opera exclusivamente sobre *calldata* e operações aritméticas, neutralizando a variância de custo entre acessos quentes e frios a *slots* de memória imposta pela atualização EIP-2929. O valor será extraído do campo `gasUsed` do recibo da transação.
    * *Calldata Gas (EIP-7623):* Custo operacional assumindo a submissão via *calldata* padrão, servindo como métrica de controle, e majorado pelas regras atualizadas da EVM Pectra.
    * *Blob Gas (EIP-4844):* Custo de envelopamento da prova via transação Tipo 3 (*Blob-carrying*). Reconhecendo o limite de 128 KB por *blob*, esta métrica será calculada de forma **fracionária**, avaliando a viabilidade econômica do circuito sob a premissa de que este operaria acoplado a um *Sequencer* ou infraestrutura de *Batching/Rollup*, e não como transação isolada de usuário final.
3.  **Tamanho da Prova (Proof Size):** Medido em bytes (fixo para um mesmo *bit-width* no UltraHonk), visando observar o crescimento logarítmico subjacente à medida que a largura de bits e o tamanho da tabela de *lookups* aumentam.
4.  **Complexidade do Circuito (Constraint Count):** Instrumentação dupla determinística: *ACIR Opcodes* (`nargo info`) para complexidade abstrata e contagem exata de *Backend Gates* (`bb gates`) para o peso criptográfico real gerado para o Barretenberg.