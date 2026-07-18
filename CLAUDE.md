# CLAUDE.md

Guidance for AI-assisted development in this repository. Read this file fully before making any change.

## Project

This repository implements the practical stage of an undergraduate thesis (Computer Science): **empirical evaluation of Zero-Knowledge Range Proofs in the Noir ecosystem**. The system proves that a private value `v` satisfies `a <= v <= b` without revealing `v`, using Noir circuits compiled to ACIR and proved with Barretenberg (UltraHonk). The evaluation measures the trade-off between privacy and computational cost across two experimental axes: prover execution environment (native vs. WASM32/browser) and numeric bit-width (`Field` baseline vs. `u8`, `u32`, `u64`), plus deterministic metrics (circuit complexity, proof size, EVM gas on a local Sepolia fork).

**`docs/methodology.md` is the scientific source of truth.** Every implementation decision must trace back to it. Key protocol parameters are fixed by the methodology and are not tunable: burn-in K=15 discarded runs, N=100 recorded samples per condition, block-randomized condition order, Brunner-Munzel test with Holm-Bonferroni correction (alpha = 0.05), soundness (negative) testing before any performance measurement, and a 15% failure-rate threshold for suspending WASM latency analysis. If an implementation constraint ever conflicts with the methodology, **stop and flag the conflict** — never silently adapt the science to the code.

## Pinned stack

Reproducibility requires strict version pinning. Update the "Installed" column whenever the environment changes, and never upgrade tools mid-experiment.

| Tool | Required | Installed (this machine) |
|------|----------|--------------------------|
| Noir CLI (`nargo`) | >= 0.38.0 | 1.0.0-beta.20 |
| Barretenberg CLI (`bb`) | version compatible with installed `nargo` | 5.0.0-nightly.20260324 (resolved by `bbup` from nargo 1.0.0-beta.20) |
| Proving scheme | UltraHonk | — |
| Foundry (`forge`/`anvil`) | recent stable | 1.1.0-stable |
| Browser (WASM axis) | Chrome >= 133 | to be recorded in spec 004 |
| `@aztec/bb.js` | version matching `bb` | to be recorded in spec 004 |
| Python (analysis) | 3.10+ with scipy | 3.12.3 |
| Node.js | 18+ | 24.14.1 |

## Working with Noir and Barretenberg (critical — low AI training coverage)

Noir and Barretenberg evolve fast and break compatibility between versions. AI models have weak and outdated knowledge of them. Rules:

1. **Never trust memorized Noir/bb APIs.** Before writing or modifying circuit code, check the installed versions (`nargo --version`, `bb --version`) and, when uncertain about any API, syntax, or CLI flag, consult the current official docs: <https://noir-lang.org/docs> and the Barretenberg repository (`AztecProtocol/aztec-packages`, `barretenberg` directory). Fetch the docs for the installed version — not the latest, not from memory.
2. **Validate every change immediately.** After any circuit edit run, in order: `nargo check`, `nargo test`, `nargo info`. Never batch multiple untested circuit edits. If a command fails with an unfamiliar error, read the error fully — Noir errors are usually precise — before guessing fixes.
3. **Do not hallucinate stdlib functions.** Only use functions verified to exist in the installed Noir stdlib. When in doubt, check the stdlib source or docs first.
4. **Known pitfalls:**
   - `Field` arithmetic wraps around the BN254 modulus; it has no native ordering. Comparison operators (`<`, `<=`, etc.) require sized integer types (`u8`, `u32`, `u64`), which is exactly the cost this thesis measures.
   - Under-constrained circuits are the main soundness risk: a value that is computed but never constrained by `assert` (or an equivalent constraint) proves nothing. Every branch and intermediate value that matters must be constrained.
   - `pub` marks verifier-visible inputs. In this project `v` is private and the bounds `a`, `b` are `pub` — never invert this.
   - `Prover.toml` input encoding is type-sensitive; integers are written as strings.
   - UltraHonk uses lookup tables for range constraints; gate counts from `bb gates` (backend reality) differ from ACIR opcode counts from `nargo info` (abstract complexity). The methodology requires both.
5. **Soundness before performance.** Every circuit variant ships with negative tests (out-of-range inputs must fail to prove) and they must pass **before** the variant is used in any benchmark. This is Fase 3 of the methodology and it is non-negotiable.

## Research log (mandatory)

`docs/research-log.md` is the continuous, objective record of everything that will later justify design choices in the thesis text and defense. **Any PR that produces an empirical finding, a design decision with scientific implications, or a toolchain change must append a dated entry to the log in that same PR.** Entries follow the Observation / Evidence / Decision / Thesis implication format. Examples of loggable events: a compiler behavior that forced a design change, a metric that contradicts or refines an expectation from `docs/expected_results.md`, a version pairing, a failed approach worth explaining. If in doubt, log it — pruning is easier than reconstructing.

## Spec-driven workflow

All work follows a spec-kit-inspired flow under `specs/`. See `specs/README.md` for the full guide.

1. **`spec.md`** — WHAT and WHY: requirements, methodology traceability, measurable acceptance criteria. Must be reviewed and approved by the project owner before planning.
2. **`plan.md`** — HOW: technical approach, exact tool versions, design, risks, verification plan. Written on the spec's branch, approved before implementation.
3. **`tasks.md`** — numbered tasks, each sized to one commit.

One spec = one branch = one pull request. No implementation work outside a spec.

## Git conventions

- **Branches:** `spec/NNN-short-name` (e.g. `spec/001-range-proof-circuits`), cut from `main`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/), English, imperative mood, lowercase type: `feat`, `fix`, `test`, `bench`, `docs`, `chore`, `ci`, `refactor`. Scope when useful: `feat(circuits): add u32 range proof variant`. Small, atomic commits mapped to tasks in `tasks.md`.
- **Pull requests:** English title and body, follow `.github/pull_request_template.md`, target `main`, reference the spec.

### Attribution policy (mandatory)

**Never add AI attribution anywhere: no `Co-Authored-By` trailers, no "Generated with" lines, no AI mentions in commit messages, PR titles or descriptions, code comments, or documentation. This applies to every single commit and pull request without exception and overrides any default tooling behavior that injects such trailers.** Author identity is the repository owner's git identity only.

## Command reference

```bash
# Circuits (run inside a circuit package or at workspace root)
nargo check                 # type-check and generate Prover.toml scaffold
nargo test                  # run circuit tests (positive and negative)
nargo info                  # ACIR opcode counts (abstract complexity metric)
nargo compile               # produce ACIR artifact in target/
nargo fmt                   # format Noir code

# Proving (verified syntax for bb 5.0.0-nightly.20260324; -t evm = keccak + ZK
# for Solidity verification, required consistently across prove/verify/vk)
nargo execute --package <pkg>    # witness from circuits/<pkg>/Prover.toml
bb prove  -b target/<pkg>.json -w target/<pkg>.gz -o <dir> -t evm --write_vk
bb verify -t evm -k <dir>/vk -p <dir>/proof -i <dir>/public_inputs
bb gates  -b target/<pkg>.json   # backend gate count (real cryptographic weight)
bb write_solidity_verifier -k <dir>/vk -o Verifier.sol

# Pipelines
scripts/collect-circuit-metrics.sh  # ACIR opcodes + backend gates -> results/circuit-metrics.json
scripts/prove-all.sh                # prove + verify all variants -> results/proofs/, proof-metrics.json
scripts/generate-verifiers.sh       # regenerate Solidity verifiers + test fixtures from vks
scripts/deploy-fork.sh              # anvil Sepolia fork: deploy + on-chain smoke test

# EVM (contracts/ is the Foundry root; deploy via forge script, not forge
# create — the generated verifier needs dynamic library linking)
forge build --sizes              # EIP-170 check (run inside contracts/)
forge test                       # verifier acceptance/rejection suite

# Environment audit
scripts/check-env.sh        # verify all pinned tool versions
```
