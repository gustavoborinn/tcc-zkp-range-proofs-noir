# Spec 003: Native Benchmark Harness

**Branch:** `spec/003-native-benchmark-harness`
**Status:** drafted
**Depends on:** 002

## Overview

Implement the harness that measures proving time under native execution (`bb prove` with direct OS memory access) for the four circuit variants, following the heavy-tailed benchmarking protocol of the methodology: burn-in, fixed sample size, block randomization, and structured persistence of every sample.

## Methodology traceability

- **Section 3.3 (Environment control):** native condition = terminal execution of `bb prove` with direct OS memory access.
- **Section 3.3, Fase 2 (Statistical instrumentation):**
  - K = 15 warm-up (burn-in) proofs per condition, discarded.
  - N = 100 recorded independent proof cycles per experimental condition (variant × environment).
  - No forced garbage collection between cycles (ecological validity).
  - **Block randomization** of condition order (`Field`, `u8`, `u32`, `u64`) across the benchmarking session, so cumulative heap state acts as stochastic noise, not a confounder.
- **Section 3.4, Metric 1 (Proving time):** milliseconds, client-side, prover only.

## Functional requirements

- FR-1: CLI harness (language decided in plan.md) that runs the full native protocol unattended: for each block, a randomized permutation of the four conditions; per condition, burn-in then recorded cycles until N=100 per condition is reached.
- FR-2: Each sample records: condition, block index, cycle index, wall-clock proving time in ms (witness generation and proof generation timed separately if the toolchain allows), timestamp, and exit status.
- FR-3: Environment metadata captured once per session: CPU model, core count, RAM, OS/kernel, `nargo`/`bb` versions, git commit of the circuits.
- FR-4: Output as line-delimited JSON (or equivalent schema defined in plan.md) under `results/native/`, raw logs gitignored, summarized artifacts committed.
- FR-5: Failures are recorded (never silently retried); the harness reports per-condition failure counts.
- FR-6: A dry-run mode (e.g., K=2, N=5) for validating the harness without the full session cost.

## Out of scope

- Browser/WASM execution (spec 004).
- Statistical testing and plotting (spec 006).

## Acceptance criteria

- AC-1: Dry-run produces schema-valid output for all four conditions with correct sample counts and randomized block orders (visible in the logs).
- AC-2: A full session yields exactly 100 recorded samples per condition (plus 15 discarded burn-in each), with the discard boundary explicit in the data.
- AC-3: Randomization is seeded and the seed is persisted, making the session order reproducible.
- AC-4: Output schema is documented and consumed successfully by a smoke-test loader script (the contract spec 006 will build on).

## Open questions

- Harness language (shell + hyperfine-style timing vs. Python/Node orchestrator) — decided in plan.md by precision and JSON ergonomics.
- Whether `bb` exposes witness-generation and proving phases separately in the installed version.
