# Evidências dos capítulos 3 e 4

Revisão de 24/10/2026. Escopo: rascunhos de implementação e método, não auditoria integral da tese. Caminhos relativos à raiz do repositório. Hashes das fontes locais em `validation/chapter-evidence.json`.

| Afirmação / trecho | Evidência e localizador | Estado e limite |
|---|---|---|
| Oito relações e entradas (3.1) | `circuits/range_proof_*/src/main.nr`, função main; `docs/circuit-relations.md`, Relations | Conferido contra código; Field diagnóstico não é intervalo |
| Exclusão de retorno modular (3.1) | Cinco assert_max_bit_size nos circuitos asserted; argumento com M e p no documento de relações | Argumento matemático da relação, não prova formal da cadeia de ferramentas |
| Compromisso, domínio, ordem (3.1) | `range_proof_committed_u64/src/main.nr`, commit e main | Mesmo v vinculado; não autentica emissor |
| Entradas canônicas / versões (3.2) | Manifesto spec008, canonical_inputs; manifesto congelado spec016, versions | Fixtures fixas não são amostra de aplicação |
| Escopos e verificação (3.2 e 4.1) | `benchmarks/expanded/collect.py`, native; harness.js, circuitProve; common.py, verify_and_store | Regiões diferentes; não isolar causalmente motor |
| 71, 46 e 15 testes/casos (3.3) | `results/spec008/final-correctness/manifest.json`, noir-checks.txt e foundry-tests.json; `docs/circuit-relations.md`, Verification | Contagens de funções e casos distintas; não alegar prova de segurança |
| Hardware / memória (4.1) | `results/final-readiness-20261024/native-smoke/session.jsonl`, cabeçalho machine.cpuinfo/meminfo | MemTotal informado pelo kernel, não memória usada ou capacidade nominal instalada |
| Ambiente e workers (4.1) | `specs/016-final-analysis/frozen-manifest.json`, machine/browser/versions | Trabalhadores observados não são utilização simultânea; pool nativo desconhecido |
| Calendário e 36.800 tentativas (4.2) | `specs/016-final-analysis/schedule.json`, days/K/N; `scripts/collect-today.py` | Atualizado em 26/10: 1/20 pares; day.json e counts-review.json de 2026-10-26 |
| Falhas, prazo e proveniência (4.2) | Runner, final_protocol.py e `docs/final-statistical-method.md`, Collection | O limite de 20 minutos impede novos inícios, não substitui deadline da tentativa |
| Gas (4.3) | `docs/final-gas-collection-plan.md` | Rodada concluída em attempt05; ver complemento abaixo |
| Contrastes e estimador (4.4) | `analysis/final_daily.py`, daily_contrasts/infer; protocolo congelado | Mesma direção dos numeradores; parâmetros distintos do projeto inicial |
| Teste de quantil e empates (4.4) | Documentação SciPy 1.18.0 quantile_test, Parameters/Notes/Returns; consulta 24/10/2026 | Fonte primária verificada; não certifica IID dos dados reais |
| Brunner–Munzel (4.4) | Documentação SciPy brunnermunzel, descrição inicial; consulta 24/10/2026 | Sustenta escopo de duas amostras independentes, não conclusão do estudo |
| Planejamento e intervalos (4.4) | `results/final-readiness-20261024/replication-planning.json`; `analysis/test_final_daily.py` | Cálculo próprio sob alternativas hipotéticas; sem potência estimada do piloto |
| Revisão do método e limitações (4.4–4.5) | Diário, entradas specs009/013/016; `docs/final-statistical-method.md` | Preservar correções posteriores; não reaproveitar conclusões históricas contestadas |

Referências documentais externas estão em `references.tex`, com links verificáveis. O estilo numérico provisório de citação e a formatação bibliográfica ainda precisam ser reconciliados com o manual; não se declara adequação final. Fontes primárias teóricas adicionais serão integradas durante a fundamentação, sem substituir a documentação da implementação efetivamente usada.

## Fundamentação ampliada em 25/10/2026

Arquitetura UltraHonk e três comparadores adicionais: fontes, localizadores e limites registrados em `sources/verification.md`, complemento de 25/10. Nenhum fator externo de desempenho foi importado como resultado ou previsão local.

## Introdução — 25/10/2026

- Objetivo geral/específicos: proposta original, seção Introdução/Objetivos; redação consolidada sem alterar a proposta.
- P1/P2/P3: plano de produção §3, método final e relações implementadas. Viabilidade operacionalizada por custos; não criado limiar de aceitação de aplicação.
- Compromisso e oito variantes: seção de implementação e docs/circuit-relations.md; não atribuída autenticidade externa.
- Motivação conceitual: fontes zkproofref, zkbenchmark e eip170 já verificadas; nenhum número novo.
- Requisitos de introdução: manual UNIFAL 2025 §3.2.2.1, pp.42–43; estrutura em seções §3.2.2; precedência institucional Resolução 041/2020 art.8.

## Tabelas estruturais — 25/10/2026

Tabelas 1–2: coverage.csv da auditoria de 24/10; valores ACIR/gates/prova conferidos com manifesto spec008. Gerador em scripts/build_structural_tables.py; hashes em validation/structural-tables-provenance.json. Runtime compilado não equivale a nova implantação.

## Correção funcional — 26/10/2026

Seção 5.1: contagens rechecadas nos três arquivos originais spec008; hashes e totais em validation/functional-evidence.json. Os 46 casos correspondem à geração de testemunha, não a 46 provas rejeitadas pelo verificador. Nenhum teste novo executado nesta revisão.

## Gas integrado — 26/10/2026

Tabela 3 e seções 4.3/5.2–5.3: results/final-gas-20261026-attempt05 exclusivamente. scripts/build_gas_table.py reconta 80 receipts, decomposições e oito resumos. Hashes em validation/gas-table-provenance.json. Tentativas anteriores descritas como incidentes, sem integrar tabela. Primeiro par: day.json e counts-review.json de 26/10, 240 aquecimentos e 1.600 medidas. Sem inferência final de latência.

## Discussão parcial — 26/10/2026

Seção 6: tabelas 1–3 sustentam métricas por camada e igualdade observada de execução líquida. Compromisso e limitações conforme relações implementadas; comparações com zkbenchmark/basebenchmark/eidreport dentro do alcance já verificado. P1/P2 pendentes. Hashes em validation/discussion-evidence.json; revisão em discussion-review.md. Datas de revisão documental não substituem data de publicação.

## Implantação — 26/10/2026

Tabela 4: 16 receipts de attempt05, vínculos por fonte/endereço, cruzamento com broadcast e hashes originais. Gerador scripts/build_deployment_table.py; evidências deployment-evidence.json e deployment-crosscheck.json. Soma por par não é custo amortizado nem inclui infraestrutura prévia; uma observação por contrato. Seções 4.3/5.2/6.1 atualizadas.

## Revisão integrada — 26/10/2026

P1/P2/P3 e limites mapeados em validation/integrated-review.md. Dezenove referências ordenadas e sem chaves faltantes; suporte de backend Node restringido ao que foi consultado. Hashes de fontes e arquivos congelados em integrated-review-evidence.json. Quatro marcadores de seção e elementos pré-textuais permanecem pendentes.

## Apêndice de rastreabilidade — 27/10/2026

Apêndice A localiza artefatos e scripts já usados nas seções anteriores. Caminhos existentes conferidos; comportamento dos três geradores editoriais inspecionado. Não representa publicação dos dados, nova execução ou validação independente. Manual 2025 §3.2.3.3 p.47; validação visual e builds em validation/reproducibility-appendix-*.
