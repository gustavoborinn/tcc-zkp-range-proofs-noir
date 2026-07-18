# Tasks: Spec 003 — Native Benchmark Harness

**Plan:** [plan.md](plan.md)

Each task is sized to one atomic commit. Execute in order.

- [ ] T1: Add spec 003 plan and task breakdown.
      commit: `docs(specs): add plan and tasks for native benchmark harness`
- [ ] T2: Add the benchmark runner implementing burn-in, block randomization, and JSONL session output.
      commit: `feat(benchmarks): add native proving benchmark harness`
- [ ] T3: Add the session validator enforcing the protocol and schema contract.
      commit: `feat(benchmarks): add benchmark session validator`
- [ ] T4: Run and commit a full-protocol pilot session on the development machine.
      commit: `bench(native): record pilot benchmark session`
- [ ] T5: Append research-log entries (verifier-target decision, timing caveats, pilot observations) and update the spec index.
      commit: `docs: record native benchmark decisions and update spec status`
