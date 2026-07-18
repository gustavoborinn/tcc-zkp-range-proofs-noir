# Spec 005: EVM Gas Instrumentation

**Branch:** `spec/005-evm-gas-instrumentation`
**Status:** drafted
**Depends on:** 002

## Overview

Instrument the deterministic on-chain cost metrics of proof verification for each circuit variant in a sterile environment: execution gas from transaction receipts on a local Sepolia fork, calldata cost under post-Pectra rules (EIP-7623), and a fractional blob-gas projection (EIP-4844) modeling rollup/batching scenarios.

## Methodology traceability

- **Section 3.4, Metric 2 (Gas cost, EVM Pectra):** measured on a **local fork of Sepolia** (via `anvil`) at the most recent block, isolating collection from mempool noise, propagation latency, and RPC rate limits. These metrics are deterministic — the verifier contract is stateless, operating only on calldata and arithmetic, neutralizing EIP-2929 warm/cold variance — so they are compared exactly, with **no hypothesis testing** (Section 3.2).
  - **Execution gas:** `gasUsed` from the simulated transaction receipt of the verification call.
  - **Calldata gas (EIP-7623):** cost of submitting the proof as standard calldata under updated Pectra pricing, as a control metric.
  - **Blob gas (EIP-4844):** Type-3 envelope cost computed **fractionally** against the 128 KB blob limit, under the premise of operation coupled to a sequencer/batching infrastructure — a comparative projection, not the standalone user cost.

## Functional requirements

- FR-1: Script that forks Sepolia at the latest block with `anvil`, deploys the verifier(s) from spec 002, and submits one verification transaction per variant with a valid proof.
- FR-2: Extraction of `gasUsed` per variant from receipts; run repeated twice to confirm determinism (identical values expected; any variance is a red flag to investigate, not average away).
- FR-3: Calldata gas computation for each proof artifact under EIP-7623 rules (implemented from the EIP text, with the formula documented and unit-tested against hand-computed examples).
- FR-4: Fractional blob-gas projection per proof: proof bytes / 128 KB blob capacity × blob cost, with the pricing assumptions documented.
- FR-5: All results written to a committed machine-readable file under `results/gas/` keyed by variant and fork block number.

## Out of scope

- Proving-time measurement (specs 003/004).
- Statistical testing (none applies — deterministic metrics; spec 006 only tabulates these).

## Acceptance criteria

- AC-1: One command reproduces the full gas dataset for all four variants against a pinned fork block.
- AC-2: Two consecutive runs at the same fork block produce byte-identical gas results.
- AC-3: EIP-7623 calldata computation validated by unit tests against manually computed vectors.
- AC-4: Output file documents fork block number, chain id, and toolchain versions.

## Open questions

- Sepolia RPC endpoint choice for forking (public vs. keyed) — only affects setup, not results.
- Exact EIP-7623 floor-pricing interaction with the verifier calldata shape (resolved in plan.md from the EIP text).
