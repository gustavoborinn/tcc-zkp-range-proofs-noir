# Spec 004: WASM Benchmark Harness

**Branch:** `spec/004-wasm-benchmark-harness`
**Status:** in review
**Depends on:** 002

## Overview

Implement the browser-based proving harness that measures proving time under WASM32 (Chrome, `bb.js` with the threaded WASM artifact), mirroring the native protocol from spec 003 so the two environments are directly comparable, and instrumenting the failure modes specific to the WASM32 architecture.

## Methodology traceability

- **Section 3.3 (Environment control, WASM):** Chrome >= 133 executing `bb-threads.wasm`; the experiment acknowledges the structural wasm32 limits (4 GiB memory ceiling, 2^19 gate limit) and **must** serve the page with COOP/COEP headers (cross-origin isolation) to enable `SharedArrayBuffer` and thread parallelism.
- **Section 3.3, Fase 2:** identical protocol to native — K=15 burn-in (here also mandatory to force V8 tier-up from Liftoff to TurboFan), N=100 recorded cycles per condition, no forced GC between cycles, block-randomized condition order.
- **Section 3.3, Fase 2.3 (Systemic failure handling):** if generation fails in more than 15% of the sample (n < 85) for a condition (e.g., V8 Out of Memory), latency analysis for that vector is suspended and the result is reported quantitatively as a **Failure Rate**, documenting architectural infeasibility.
- **Section 3.4, Metric 1:** proving time in ms, client-side.

## Functional requirements

- FR-1: Local static server that serves the harness page with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`; the page asserts `crossOriginIsolated === true` before any measurement.
- FR-2: Browser harness using `@aztec/bb.js` (version paired with the native `bb`) that loads each variant's ACIR artifact, generates the witness and proof, and times each cycle in ms.
- FR-3: Protocol parity with spec 003: same K, N, block randomization (shared seed format), same output schema, plus WASM-specific fields (browser version, thread count, `crossOriginIsolated` flag, failure reason).
- FR-4: Failure tracking per condition; when failures exceed 15% of planned samples, the harness marks the condition as `failure-rate-only` in the output instead of aborting the session.
- FR-5: Results exported from the browser to `results/wasm/` (download or local endpoint), raw logs gitignored, summaries committed.
- FR-6: Dry-run mode as in spec 003.

## Out of scope

- Native execution (spec 003).
- Statistical analysis (spec 006).

## Acceptance criteria

- AC-1: Harness refuses to run without cross-origin isolation; with the provided server it reports `crossOriginIsolated === true` and a thread count > 1.
- AC-2: Dry-run in Chrome >= 133 produces schema-valid output for all four conditions; Chrome version recorded in `CLAUDE.md` stack table.
- AC-3: Full session yields 100 samples per condition or an explicit failure-rate record per the 15% rule.
- AC-4: Output loads with the same loader contract as native results (verified by the smoke-test loader).

## Open questions

- Whether current `bb.js` proves UltraHonk for these circuit sizes within wasm32 limits — a minimal feasibility probe is the first plan.md task.
- Automation level (manual session vs. Playwright-driven runs) given that headless mode may alter V8 behavior; the methodology's ecological validity goal informs this choice.
