# Validation of Private Attributes in Smart Contracts via Zero-Knowledge Proofs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Noir](https://img.shields.io/badge/Language-Noir-black)](https://noir-lang.org/)

## 1. Overview

This repository contains the implementation and benchmarking of **Zero-Knowledge Range Proofs** using the **Noir** DSL, developed as an undergraduate thesis (Computer Science). The system proves that a hidden value `v` satisfies `a <= v <= b` — e.g., financial solvency or age verification — without revealing `v` to the network or the verifier.

The evaluation quantifies the trade-off between privacy and computational cost across two experimental axes:

- **Execution environment:** native proving (`bb` CLI) vs. browser proving (WASM32 via `bb.js`).
- **Bit-width:** a `Field` baseline vs. `u8`, `u32`, and `u64` range-constrained variants.

Metrics include proving time (stochastic, tested with Brunner-Munzel + Holm-Bonferroni), circuit complexity (ACIR opcodes and backend gates), proof size, and post-Pectra EVM gas (execution, calldata under EIP-7623, and fractional blob projection under EIP-4844) measured on a local Sepolia fork.

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Thesis documents — `docs/methodology.md` is the scientific source of truth |
| `specs/` | Spec-driven workflow: numbered specs (spec → plan → tasks) and templates |
| `circuits/` | Noir workspace packages, one per circuit variant |
| `contracts/` | Foundry project with the generated Solidity verifier |
| `benchmarks/` | Native and WASM benchmark harnesses |
| `analysis/` | Statistical analysis and figure generation (Python) |
| `scripts/` | Environment checks and pipeline scripts |
| `results/` | Collected metrics (raw logs gitignored; summaries committed) |

## 3. Tech stack

| Tool | Version policy |
|------|----------------|
| [Noir](https://noir-lang.org/) (`nargo`) | pinned, see `CLAUDE.md` |
| Barretenberg (`bb`) — UltraHonk | paired with `nargo` |
| Solidity + [Foundry](https://getfoundry.sh/) | verifier build, Sepolia fork via `anvil` |
| `@aztec/bb.js` (WASM32) | paired with `bb`, Chrome >= 133 |
| Python 3 | statistics and plots |

Run `scripts/check-env.sh` to audit the local toolchain.

## 4. Development workflow

Work is organized as numbered specs under `specs/` (see `specs/README.md`): each spec is specified, planned, broken into tasks, implemented on its own `spec/NNN-*` branch, and merged via pull request. Conventions for commits, branches, and PRs are documented in `CLAUDE.md`.

## 5. Methodology summary

The benchmark protocol (defined in `docs/methodology.md`) uses K=15 burn-in runs and N=100 recorded proof cycles per condition with block-randomized condition ordering; proving-time hypotheses are tested non-parametrically (Brunner-Munzel, alpha = 0.05, Holm-Bonferroni correction for multiple comparisons), while deterministic metrics (gates, proof size, gas) are compared exactly. Circuit soundness is audited with negative tests before any performance measurement.
