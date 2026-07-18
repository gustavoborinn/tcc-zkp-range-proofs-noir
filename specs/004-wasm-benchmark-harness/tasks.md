# Tasks: Spec 004 — WASM Benchmark Harness

**Plan:** [plan.md](plan.md)

Each task is sized to one atomic commit. Execute in order.

- [ ] T1: Add spec 004 plan and task breakdown.
      commit: `docs(specs): add plan and tasks for wasm benchmark harness`
- [ ] T2: Add the npm project pinning bb.js and the cross-origin-isolated server with the session write endpoint.
      commit: `feat(benchmarks): add cross-origin isolated wasm server`
- [ ] T3: Add the browser harness page implementing the block-randomized proving protocol.
      commit: `feat(benchmarks): add wasm proving benchmark page`
- [ ] T4: Add the Playwright driver for unattended sessions in real Chrome.
      commit: `feat(benchmarks): add automated wasm session driver`
- [ ] T5: Run and commit a full-protocol pilot session; cross-verify one browser proof natively.
      commit: `bench(wasm): record pilot benchmark session`
- [ ] T6: Record findings and versions (research log, CLAUDE.md stack table, spec index).
      commit: `docs: record wasm benchmark findings and update references`
