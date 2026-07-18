# Plan: Spec 004 — WASM Benchmark Harness

**Spec:** [spec.md](spec.md)
**Status:** approved

## Technical approach

Feasibility was probed before planning, on the exact paired stack:

- **`@aztec/bb.js@5.0.0-nightly.20260324` exists on npm** — the same version string as the native `bb`, so the pairing required by methodology section 3.1 is exact, not approximate.
- The installed API exposes `UltraHonkBackend.generateProof(witness, { verifierTarget: 'evm' })` — the same `evm` target semantics as the native CLI, so the latency decision from spec 003 carries over unchanged.
- `Barretenberg.new({ backend: BackendType.WasmWorker, threads })` forces the threaded WASM backend (bb.js would otherwise silently prefer the native binary when available, which would invalidate the environment axis).
- Probe results (Node, WasmWorker, 8 threads): u64 proof ≈ 232 ms vs ≈ 90 ms native — a ~2.5x slowdown preview of Axis A. Proof is byte-identical in size (7,232 B) and **cross-verifies against the native vk with `bb verify -t evm`**, so WASM-generated proofs are accepted by the deployed Solidity verifier.
- Chrome 150 installed (satisfies the >= 133 requirement).

The harness mirrors the native protocol exactly (same K/N defaults, seeded block permutations, witness prepared outside the timed region, failures recorded and never retried) so Axis A compares environments, not protocols. Sessions reuse the JSONL schema; `benchmarks/native/validate_session.py` validates WASM sessions unchanged.

## Design

```
benchmarks/wasm/package.json          # pins @aztec/bb.js 5.0.0-nightly.20260324 (save-exact)
benchmarks/wasm/server.py             # static server with COOP/COEP headers + POST endpoint
                                      # that writes the session JSONL to results/wasm/
benchmarks/wasm/index.html            # harness page (ES module importing the bb.js browser build)
benchmarks/wasm/harness.js            # protocol runner: seeded PRNG (mulberry32) + Fisher-Yates
                                      # permutations, performance.now() timing, failure capture
benchmarks/wasm/drive_session.mjs      # optional driver (Node): builds with Vite, launches real headful Chrome via
                                      # Playwright, opens the page, waits for session completion
results/wasm/session-<UTC>.jsonl      # committed session datasets (same schema as native)
```

Key mechanics:

- **Cross-origin isolation:** `server.py` sends `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` on every response; the page refuses to run unless `crossOriginIsolated === true` and records `navigator.hardwareConcurrency` as the thread count.
- **Witness parity:** the page fetches the ACIR artifact and the native-generated witness (`target/<pkg>.gz`) per condition; witness solving stays outside the timed region, as in spec 003. One `UltraHonkBackend` per condition is created during preparation; burn-in blocks then force V8 tier-up (Liftoff → TurboFan) exactly as the methodology prescribes.
- **Timing:** `performance.now()` around each `generateProof(witness, { verifierTarget: 'evm' })` call.
- **Failure protocol:** every rejection/exception is recorded (`ok: false`, error string) and the session continues; the 15% failure-rate rule (methodology Fase 2.3) is enforced at validation/analysis time, not by aborting collection.
- **Session config** (seed, K, N, label) passed via URL query; the completed session is POSTed to the server, which writes `results/wasm/session-<UTC>.jsonl` — same header/cycle records as native plus `browser`, `cross_origin_isolated`, `hardware_concurrency`, `bbjs_version`.
- **Automation:** `drive_session.mjs` launches installed real Chrome (Playwright, `channel="chrome"`, headful — headless would alter the V8 profile the methodology cares about), navigates with the session parameters, and exits when the page signals completion. Manual runs (open the URL in Chrome) remain fully supported; the driver only removes the clicking.

## Stack and versions

`@aztec/bb.js` 5.0.0-nightly.20260324 (exact), Chrome 150.0.7871.128, Node 24.14.1 (server tooling only), Python 3.12.3, Playwright (dev dependency, pinned on install).

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| bb.js silently falling back to a non-worker backend | wrong environment measured | `BackendType.WasmWorker` forced; page asserts `crossOriginIsolated` and records the backend type |
| Headful Chrome unavailable in an automated context | driver fails | manual mode is first-class; driver failure never blocks collection |
| WASM memory pressure on larger sessions | failures mid-session | failures are recorded data (methodology); validator reports the failure rate against the 15% rule |
| bb.js browser bundle needing extra assets (wasm binaries) | page load failure | served from `node_modules` via the same origin; probe confirmed the bundle self-locates its wasm |

## Verification plan

1. Server up → page reports `crossOriginIsolated === true`, threads > 1.
2. Dry-run session (K=2, N=5) in real Chrome produces a schema-valid JSONL accepted by `validate_session.py`.
3. Full pilot session (K=15, N=100) committed; failure rates reported by the validator.
4. One WASM-produced proof cross-verified with native `bb verify -t evm` (already demonstrated in the probe; re-checked from a browser-produced proof).
