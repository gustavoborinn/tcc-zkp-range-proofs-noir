# Tasks: Spec 005 — EVM Gas Instrumentation

**Plan:** [plan.md](plan.md)

Each task is sized to one atomic commit. Execute in order.

- [x] T1: Add spec 005 plan and tasks; record the validity-review requirements in specs 005 and 006.
      commit: `docs(specs): add plan and tasks for evm gas instrumentation`
- [x] T2: Add the pure EIP cost module (EIP-7623 decomposition, EIP-4844 blob projection) with unit tests.
      commit: `feat(benchmarks): add eip cost calculation module`
- [x] T3: Add the gas measurement orchestrator (anvil fork, deploy, double-run receipts, decomposition).
      commit: `feat(benchmarks): add gas measurement orchestrator`
- [x] T4: Run the instrumentation and commit the gas dataset.
      commit: `bench(gas): record gas measurement dataset`
- [x] T5: Append research-log entries and update the spec index.
      commit: `docs: record gas instrumentation findings and update spec status`
