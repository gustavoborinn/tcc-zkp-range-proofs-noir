# Tasks: Spec 002 — Proof Pipeline and Solidity Verifier

**Plan:** [plan.md](plan.md)

Each task is sized to one atomic commit. Execute in order.

- [ ] T1: Add spec 002 plan and task breakdown.
      commit: `docs(specs): add plan and tasks for proof pipeline and verifier`
- [ ] T2: Extend the metrics script to collect backend gate counts (closes the spec 001 pending marker) and refresh the committed metrics file.
      commit: `feat(scripts): collect backend gate counts`
- [ ] T3: Add the proving pipeline script generating and locally verifying proofs for all variants, with proof-size metrics.
      commit: `feat(scripts): add proving and verification pipeline`
- [ ] T4: Scaffold the Foundry project with the generated Solidity verifiers and EIP-170 size tuning (`optimizer_runs = 1`).
      commit: `feat(contracts): add generated ultrahonk verifiers`
- [ ] T5: Add Foundry tests accepting a valid proof fixture and rejecting a mutated one.
      commit: `test(contracts): verify proof acceptance and rejection`
- [ ] T6: Add the Sepolia-fork deployment script with valid and corrupted verification transactions.
      commit: `feat(scripts): add sepolia fork deployment and verification`
- [ ] T7: Update CLAUDE.md command reference to the verified bb syntax, append research-log entries, and update the spec index.
      commit: `docs: record proof pipeline findings and update references`
