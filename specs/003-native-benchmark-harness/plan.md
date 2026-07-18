# Plan: Spec 003 — Native Benchmark Harness

**Spec:** [spec.md](spec.md)
**Status:** approved

## Technical approach

A Python harness (stdlib only — `subprocess`, `time.monotonic_ns`, seeded `random.Random`, `json`) orchestrates the full protocol from `docs/methodology.md` Fase 2: per session, a preparation stage compiles the workspace and generates one witness per condition; then 15 burn-in blocks (discarded) and 100 measurement blocks are executed, where **each block is a seeded random permutation of the four conditions** with one timed `bb prove` per condition. This yields exactly K=15 discarded + N=100 recorded samples per condition, with block randomization neutralizing cumulative-state drift, as the methodology requires.

Timing probes on this machine (bb 5.0.0-nightly.20260324, precomputed vk): field ≈ 30 ms, u64 ≈ 90 ms per proof — a full session costs under a minute, so full-protocol pilot runs are cheap.

### Methodological decisions resolved in this plan

1. **Verifier target fixed at `-t evm` (keccak + ZK) for all latency measurements**, native and WASM alike. Rationale: the thesis scenario is client-side proving for on-chain verification; the proof being timed must be the proof that the deployed Solidity verifier accepts. The native default (poseidon2) would measure an artifact the EVM pipeline never uses. Recorded in the research log; closes the open decision flagged by spec 002.
2. **Witness generated once per condition per session, outside the timed region.** The methodology's metric is proof-generation time; witness solving is deterministic input preparation. Proof cycles remain independent because UltraHonk proving is randomized per run. Witness-generation time is still recorded once in session metadata.
3. **Precomputed verification key passed via `-k`.** Without it, bb recomputes the VK inside `bb prove` (it warns explicitly), which would conflate one-time key computation with proving latency.
4. **Wall-clock of the `bb prove` subprocess** via monotonic clock, including process startup. Startup is a constant additive component shared by all conditions and inherent to native CLI proving; documented as a caveat rather than subtracted, preserving ecological validity.

## Stack and versions

`nargo` 1.0.0-beta.20, `bb` 5.0.0-nightly.20260324, Python 3.12.3 (stdlib only — no dependencies to pin).

## Design

```
benchmarks/native/run_benchmark.py       # the harness (CLI: --seed, --burn-in, --samples, --output-dir)
benchmarks/native/validate_session.py    # schema/protocol validator; the loader contract for spec 006
results/native/session-<UTC>.jsonl       # committed session datasets
results/native/raw/                      # gitignored scratch (witnesses, per-run proof outputs)
```

Session file format (JSON Lines):

- First record `{"type": "session", ...}`: seed, K, N, conditions, verifier_target, tool versions, git commit, CPU model, core count, total RAM, kernel, timestamp, witness-generation times.
- Then one record per cycle `{"type": "cycle", phase: "burnin"|"measure", block, position, variant, proving_ms, exit_code, ok}`. Failures are recorded with `ok: false` and never retried (methodology: failures are data).

`validate_session.py` enforces: header present, exactly N `measure` cycles per condition with `ok: true` accounting, every block a permutation of the four conditions, seed present. Non-zero exit on any violation — spec 006 builds its loader on this contract.

Defaults K=15, N=100 (methodology values); `--burn-in 2 --samples 5` is the dry-run. The seed defaults to a fresh random value and is always persisted in the header, making any session order-reproducible.

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Background load on the machine during a session | noisy samples | sessions are cheap (<1 min) and repeatable; env metadata recorded; official sessions run on a quiet machine — pilot data is labeled as pilot |
| Process-startup time dominating the fastest condition (field ≈ 30 ms) | compressed effect sizes on Axis B | documented caveat; Brunner-Munzel is rank-based and robust to additive constants; per-condition contrast remains valid |
| bb output format drift | parsing breaks | harness only consumes exit codes and its own timing; no bb stdout parsing |

## Verification plan

1. Dry-run (`--burn-in 2 --samples 5`) produces a schema-valid session file; `validate_session.py` passes on it and fails on a truncated copy.
2. Full-protocol pilot session (K=15, N=100) runs clean, yields 100 measured samples per condition, and is committed as the first dataset.
3. Block permutations visibly differ across blocks (spot-check) and are reproducible given the recorded seed.
