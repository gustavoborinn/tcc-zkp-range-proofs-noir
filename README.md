# Validation of Private Attributes in Smart Contracts via Zero-Knowledge Proofs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Noir](https://img.shields.io/badge/Language-Noir-black)](https://noir-lang.org/)

## 1. Overview

This repository contains the implementation and benchmarking of **Zero-Knowledge Range Proofs** using the **Noir** DSL, developed as an undergraduate thesis (Computer Science). The system proves that a hidden value `v` satisfies `a <= v <= b` — e.g., financial solvency or age verification — without revealing `v` to the network or the verifier.

The evaluation quantifies the trade-off between privacy and computational cost across two experimental axes:

- **Execution environment:** native proving (`bb` CLI) vs. browser proving (WASM32 via `bb.js` in Chrome, cross-origin isolated).
- **Bit-width:** a `Field` baseline vs. `u8`, `u32`, and `u64` range-constrained variants.

Metrics include proving time (stochastic, tested with Brunner-Munzel + Holm-Bonferroni), circuit complexity (ACIR opcodes and backend gates), proof size, and post-Pectra EVM gas — execution gas decomposed under EIP-7623 and a fractional blob projection under EIP-4844 — measured on a local Sepolia fork.

## 2. Pipeline

The full experimental pipeline is implemented as six specs (see `specs/README.md` for status):

1. **Circuits** — four Noir workspace packages (`Field` baseline, `u8`, `u32`, `u64`) with positive and negative soundness tests.
2. **Proof pipeline & verifier** — UltraHonk proofs targeting the EVM (`-t evm`), Solidity verifiers generated per variant and deployed under the EIP-170 size limit (`optimizer_runs = 1`), smoke-tested on an anvil fork of Sepolia.
3. **Native benchmark** — K=15 burn-in + N=100 recorded proof cycles per condition, block-randomized, persisted as validated JSONL sessions.
4. **WASM benchmark** — the identical protocol in real Chrome (COOP/COEP server, `SharedArrayBuffer` threads, Playwright driver); browser proofs cross-verify against the native verification key.
5. **Gas instrumentation** — deterministic receipts on a Sepolia fork, double-run identity check, EIP-7623 decomposition, EIP-4844 blob projection.
6. **Statistical analysis** — Brunner-Munzel with an exact-permutation saturation rule for completely separated samples, Holm-Bonferroni on the bit-width family, violin/ECDF figures, and LaTeX tables.

Empirical findings and design decisions are logged continuously in [`docs/research-log.md`](docs/research-log.md).

## 3. Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Thesis documents — `docs/methodology.md` is the scientific source of truth; `docs/research-log.md` is the running record of findings |
| `specs/` | Spec-driven workflow: numbered specs (spec → plan → tasks) and templates |
| `circuits/` | Noir workspace packages, one per circuit variant |
| `contracts/` | Foundry project with the generated UltraHonk Solidity verifiers and tests |
| `benchmarks/native/` | Native proving-time harness and the session protocol validator |
| `benchmarks/wasm/` | Browser harness (Vite build, COOP/COEP server, Playwright driver) |
| `benchmarks/gas/` | EVM gas instrumentation (EIP-7623/EIP-4844 cost module + fork orchestrator) |
| `analysis/` | Statistical pipeline: hypothesis tests, figures, report and LaTeX tables |
| `scripts/` | Environment audit and proof/verifier/deployment pipelines |
| `results/` | Committed datasets and analysis outputs (raw scratch is gitignored) |

## 4. Tech stack

Versions are strictly pinned for reproducibility — the authoritative table lives in `CLAUDE.md`.

| Tool | Version |
|------|---------|
| [Noir](https://noir-lang.org/) (`nargo`) | 1.0.0-beta.20 |
| Barretenberg (`bb`) — UltraHonk | 5.0.0-nightly.20260324 (resolved by `bbup` pairing) |
| `@aztec/bb.js` (WASM32) | 5.0.0-nightly.20260324 (exact pairing) |
| Solidity + [Foundry](https://getfoundry.sh/) | solc 0.8.28, Foundry 1.1.0-stable |
| Browser (WASM axis) | Chrome 150 (>= 133 required) |
| Python (analysis) | 3.12 + scipy/numpy/matplotlib pinned in `analysis/requirements.txt` |

Run `scripts/check-env.sh` to audit the local toolchain.

## 5. Reproducing the experiment

```bash
scripts/check-env.sh                      # audit toolchain versions
nargo test                                # circuit soundness (positive + negative tests)
scripts/collect-circuit-metrics.sh        # ACIR opcodes + backend gates
scripts/prove-all.sh                      # proofs + local verification + sizes
scripts/generate-verifiers.sh             # Solidity verifiers + test fixtures
(cd contracts && forge test)              # on-chain acceptance/rejection suite
scripts/deploy-fork.sh                    # deploy + smoke test on a Sepolia fork

python3 benchmarks/native/run_benchmark.py            # native latency session
(cd benchmarks/wasm && npm install && node drive_session.mjs)  # WASM session in Chrome
python3 benchmarks/gas/measure_gas.py                 # deterministic gas dataset

python3 -m venv analysis/.venv && analysis/.venv/bin/pip install -r analysis/requirements.txt
(cd analysis && .venv/bin/python run_analysis.py)     # report, figures, LaTeX tables
```

Latency sessions are validated against the benchmark protocol by `benchmarks/native/validate_session.py`; the analysis refuses any session the validator rejects.

## 6. Development workflow

Work is organized as numbered specs under `specs/` (see `specs/README.md`): each spec is specified, planned, broken into tasks, implemented on its own `spec/NNN-*` branch, and merged via pull request. Conventions for commits, branches, and PRs are documented in `CLAUDE.md`.

## 7. Methodology summary

The benchmark protocol (defined in `docs/methodology.md`) uses K=15 burn-in runs and N=100 recorded proof cycles per condition with block-randomized condition ordering; proving-time hypotheses are tested non-parametrically (Brunner-Munzel, alpha = 0.05, Holm-Bonferroni correction for multiple comparisons), while deterministic metrics (gates, proof size, gas) are compared exactly. Circuit soundness is audited with negative tests before any performance measurement.
