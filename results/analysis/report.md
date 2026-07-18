# Statistical Analysis Report

## Input inventory

- `results/native/session-20260718T171730Z.jsonl` — environment **native**, label `official`, seed 753410584, git `674e60f7`
- `results/wasm/session-20260718T171941Z.jsonl` — environment **wasm**, label `official`, seed 3449093065, git `674e60f7`
- `results/circuit-metrics.json`
- `results/proof-metrics.json`
- `results/gas/gas-metrics.json`

Significance level: alpha = 0.05 (two-tailed). Saturated pairs (complete separation) report the exact permutation bound p = 2/C(n+m, n) instead of the asymptotic Brunner-Munzel statistic (spec 006 FR-3b).

## Failure-rate gates

| env | condition | ok | failure rate | latency analysis |
|---|---|---|---|---|
| native | Field | 100/100 | 0.0% | included |
| native | u8 | 100/100 | 0.0% | included |
| native | u32 | 100/100 | 0.0% | included |
| native | u64 | 100/100 | 0.0% | included |
| wasm | Field | 100/100 | 0.0% | included |
| wasm | u8 | 100/100 | 0.0% | included |
| wasm | u32 | 100/100 | 0.0% | included |
| wasm | u64 | 100/100 | 0.0% | included |

## Axis A — execution environment (native vs. WASM32)

| condition | native median [IQR] (ms) | wasm median [IQR] (ms) | slowdown | p_hat P(nat<wasm) | p-value |
|---|---|---|---|---|---|
| Field | 38.6 [36.9, 41.2] | 104.5 [103.0, 106.8] | 2.71x | 1.00 | <= 2.21e-59 (sat.) |
| u8 | 41.0 [39.4, 43.6] | 117.9 [115.1, 120.8] | 2.88x | 1.00 | <= 2.21e-59 (sat.) |
| u32 | 98.5 [96.0, 102.1] | 237.5 [233.0, 242.4] | 2.41x | 1.00 | <= 2.21e-59 (sat.) |
| u64 | 97.3 [94.6, 100.9] | 234.3 [229.8, 238.7] | 2.41x | 1.00 | <= 2.21e-59 (sat.) |

## Axis B — bit-width vs. Field baseline (Holm-Bonferroni)

### native

| comparison | p_hat P(var<Field) | p-value | Holm threshold | decision |
|---|---|---|---|---|
| u8-vs-Field | 0.28 | 1.06e-08 | 0.0500 | reject H0 |
| u32-vs-Field | 0.00 | <= 2.21e-59 (sat.) | 0.0167 | reject H0 |
| u64-vs-Field | 0.00 | <= 2.21e-59 (sat.) | 0.0250 | reject H0 |

### wasm

| comparison | p_hat P(var<Field) | p-value | Holm threshold | decision |
|---|---|---|---|---|
| u8-vs-Field | 0.02 | 2.60e-72 | 0.0167 | reject H0 |
| u32-vs-Field | 0.00 | <= 2.21e-59 (sat.) | 0.0250 | reject H0 |
| u64-vs-Field | 0.00 | <= 2.21e-59 (sat.) | 0.0500 | reject H0 |

Supplementary (no family correction): u32 vs u64, native: p_hat = 0.42, p = 5.33e-02.

## Deterministic metrics (exact comparison — no hypothesis testing)

| variant | ACIR opcodes | backend gates | proof (B) | exec gas | calldata std | calldata floor | blob gas |
|---|---|---|---|---|---|---|---|
| Field | 5 | 40 | 4928 | 1838390 | 76464 | 191160 | 4992 |
| u8 | 11 | 93 | 5312 | 1899684 | 82668 | 206670 | 5376 |
| u32 | 11 | 2791 | 7232 | 2206708 | 113208 | 283020 | 7296 |
| u64 | 11 | 2838 | 7232 | 2206708 | 113172 | 282930 | 7296 |

Gas measured on Sepolia fork block 11300032 (chain 11155111), compilation profile optimizer_runs = 1 (EIP-170 fit).

## Figures

![violin-proving-time](figures/violin-proving-time.png)
![ecdf-axis-a](figures/ecdf-axis-a.png)
![ecdf-axis-b-native](figures/ecdf-axis-b-native.png)
![ecdf-axis-b-wasm](figures/ecdf-axis-b-wasm.png)
