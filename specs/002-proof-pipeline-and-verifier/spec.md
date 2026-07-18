# Spec 002: Proof Pipeline and Solidity Verifier

**Branch:** `spec/002-proof-pipeline-and-verifier`
**Status:** done
**Depends on:** 001

## Overview

Build the end-to-end proving pipeline for each circuit variant using the Barretenberg CLI under UltraHonk: witness generation, proof generation, local verification, proof-size measurement, and generation of the Solidity verifier contract. Deliver a Foundry project that compiles the verifier under EIP-170 constraints and deploys it to a local Sepolia fork.

## Methodology traceability

- **Section 3.1 (Stack pinning):** Barretenberg CLI (`bb`) version matching installed `nargo`, UltraHonk scheme. Deployment target: Sepolia state via local `anvil` fork of the most recent block.
- **Section 3.3, Fase 1 (Build and deploy under EIP-170):** compile Noir to ACIR, generate the Solidity verifier via `bb write_solidity_verifier`. Generic UltraHonk verifiers (~33 KB) exceed the EVM contract-size limit (EIP-170, max 24.5 KB): apply aggressive Solidity optimizer tuning (`optimizer_runs = 1`); if the optimizer cannot bring the artifact under the limit, adopt the split-verifier topology (linked libraries) to guarantee deployability.
- **Section 3.4, Metric 3 (Proof size):** proof size in bytes per variant (fixed per bit-width under UltraHonk), recorded as a deterministic metric.
- **Section 3.4, Metric 4:** with `bb` now installed, complete the backend gate counts left pending by spec 001.

## Functional requirements

- FR-1: Install and pin `bb` (record exact version in `CLAUDE.md` stack table); document the pairing with the installed `nargo` version.
- FR-2: A reproducible script proves and locally verifies each of the four variants (witness → proof → verify), storing artifacts under `results/` with proof size in bytes.
- FR-3: Solidity verifier generated per variant (or shared, per `bb` behavior — documented in plan.md) inside a Foundry project under `contracts/`.
- FR-4: Foundry profile with `optimizer_runs = 1`; compiled bytecode size measured and compared against the EIP-170 limit; split-verifier fallback implemented only if required, with the decision recorded.
- FR-5: Deployment script targeting an `anvil` fork of the latest Sepolia block; an on-chain verification transaction of a valid proof succeeds, and an invalid/mutated proof reverts.

## Out of scope

- Repeated timing measurements (specs 003/004).
- Gas accounting beyond a smoke check (spec 005).

## Acceptance criteria

- AC-1: `bb --version` recorded; pipeline script runs clean for all four variants and emits proof sizes in bytes to a committed metrics file.
- AC-2: `forge build` succeeds; deployed verifier bytecode size ≤ 24,576 bytes, or the split-verifier topology is in place and deployable.
- AC-3: On the anvil Sepolia fork: valid proof verification transaction succeeds; corrupted proof is rejected.
- AC-4: Backend gate counts (`bb gates`) recorded for all four variants.

## Open questions

- Which `bb` version pairs with `nargo 1.0.0-beta.20` and the exact current CLI syntax (flags changed repeatedly across versions — verify against installed `bb --help`, not memory).
- Whether one verifier serves all variants or one per variant (depends on verification-key handling in the installed toolchain).
