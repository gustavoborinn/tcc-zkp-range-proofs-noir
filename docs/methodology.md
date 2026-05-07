# 3. Metodologia de Pesquisa

A presente pesquisa propõe o desenvolvimento, a implementação e a avaliação empírica de desempenho de um circuito criptográfico do tipo *Range Proof* construído no ecossistema Noir. O delineamento metodológico está estruturado para garantir a validade científica da avaliação de desempenho perante as limitações práticas de infraestrutura Web3 (EVM pós-Pectra e arquitetura WASM32).

## 3.1 Classificação da Pesquisa e Fixação Tecnológica (Stack Pinning)

Para garantir a reprodutibilidade e evitar a quebra de compatibilidade em um ecossistema em rápida evolução, o ambiente de desenvolvimento é estritamente fixado:
*   **Compilador de Circuito:** Noir CLI (`nargo` versão $\ge 0.38.0$).
*   **Backend Criptográfico e Gerador de Verificador:** Barretenberg CLI (`bb` versão correspondente ao `nargo`), operando sob o esquema **UltraHonk**.
*   **Alvo de Deploy:** Rede de testes Sepolia (Ethereum).

A pesquisa caracteriza-se como **Aplicada com Avaliação de Desempenho**, orientada por métricas quantitativas e testes de dominância estocástica robustos a ambientes ruidosos.

## 3.2 Delineamento Experimental e Variáveis de Controle

O escopo isola lógicas de negócios complexas. O experimento foca na instrumentação das seguintes variáveis independentes:

*   **Controle de Largura de Bits (Bit-width) e Linha de Base:** O tamanho do *input* $v$ no intervalo $a \le v \le b$ será testado variando as restrições de inteiros ($u8$, $u32$, $u64$). Para mitigar o custo fixo das tabelas de busca (*Lookup Tables*) inerentes ao UltraHonk, um circuito idêntico utilizando o tipo matemático irrestrito `Field` será usado como "linha de base", isolando o custo puramente imposto pela restrição de intervalo.
*   **Controle de Degradação de Ambiente (WASM32 vs Nativo):** A latência do lado do cliente (Prover) será testada sob duas condições:
    1.  **Execução Nativa:** Terminal (`bb prove`), com acesso direto à memória do SO.
    2.  **Execução em WebAssembly (WASM):** Ambiente navegador (Chrome $\ge 133$) utilizando o artefato `bb-threads.wasm`. O experimento reconhece o limite estrutural do compilador *wasm32* (teto de 4 GiB e limite de $2^{19}$ *gates*) e fará o provisionamento obrigatório de cabeçalhos COOP/COEP (*Cross-Origin Isolation*) para habilitar o *SharedArrayBuffer* e o paralelismo.

**Fase 1: Construção e Deploy sob EIP-170**
Compilação do código Noir para representação intermediária (ACIR), seguida pela geração do *Smart Contract* verificador Solidity via `bb write_solidity_verifier`. Para transpor o limite estrito de tamanho de contrato da EVM (EIP-170, max 24.5 KB) — frequentemente excedido por verificadores UltraHonk genéricos (~33 KB) —, o artefato será submetido a *tuning* agressivo no compilador Solidity (`optimizer_runs = 1`). Caso a complexidade do circuito invalide o otimizador, a topologia de *Split-Verifier* (bibliotecas acopladas) será adotada para garantir o deploy na Sepolia.

**Fase 2: Instrumentação Estatística (Heavy-Tailed Benchmarking)**
Execução de $N \ge 100$ ciclos de provas por ambiente. Reconhecendo que a execução WASM sofre de flutuações extremas causadas por pausas de *Garbage Collection* do motor V8 e estrangulamento de *threads*, a análise de latência descartará métodos baseados em normalidade.

**Fase 3: Auditoria de Correção Lógica (Qualitativa)**
Validação de *soundness* lógica (*Under-constrained Testing*). Execução de testes negativos submetendo *inputs* fora do intervalo permitido, assegurando (Pass/Fail) a ausência de vulnerabilidades estruturais antes da coleta de desempenho.

## 3.3 Variáveis e Métricas de Avaliação Quantitativa

A viabilidade do sistema será determinada pelas métricas a seguir:

1.  **Tempo de Geração da Prova (Proving Time):** Mensurado em milissegundos. A análise de degradação ambiente dispensará o Teste t e o Teste de Mann-Whitney clássico (frágeis a variâncias multimodais). A avaliação será conduzida via Análise Visual Exploratória (Gráficos de Violino e Funções de Distribuição Cumulativa Empírica - ECDF) suportada pelo **Teste de Brunner-Munzel** ou testes de permutação, garantindo validade mesmo com assimetria extrema entre os ambientes.
2.  **Custo Computacional e de Dados (Gas Cost EVM Pectra):** Fracionado estruturalmente para a rede Sepolia:
    *   *Execution Gas:* Custo puro das operações da EVM via verificador Solidity.
    *   *Blob Gas (EIP-4844):* Custo de submissão do *payload* via transações Tipo 3 (*Blob-carrying*), padrão-ouro atual de viabilidade de dados.
    *   *Calldata Gas (EIP-7623):* Medido como limite superior (pior cenário), assumindo o custo de *bytes* majorado pela recente atualização Pectra.
3.  **Tamanho da Prova (Proof Size):** Medido em bytes, visando observar o crescimento logarítmico subjacente das provas UltraHonk à medida que a largura de bits e o tamanho da tabela de *lookups* aumentam.
4.  **Complexidade do Circuito (Constraint Count):** Instrumentação dupla: *ACIR Opcodes* (`nargo info`) para complexidade abstrata e *Backend Gates* (`bb gates`) para o peso criptográfico real gerado para o provador Barretenberg.