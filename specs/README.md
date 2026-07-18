# Spec Workflow

This project uses a spec-driven development flow inspired by spec-kit, adapted to the thesis methodology (`docs/methodology.md`). Every unit of work is a numbered spec that moves through three documents before and during implementation.

## Lifecycle

```
spec.md (WHAT/WHY) ──approved──> plan.md (HOW) ──approved──> tasks.md ──> implementation ──> PR
```

1. **Specify.** Write `specs/NNN-name/spec.md` from `templates/spec-template.md`. It defines scope, requirements, and measurable acceptance criteria, and cites the methodology sections it implements. The spec is reviewed and approved by the project owner before any planning.
2. **Plan.** On the spec's branch, write `plan.md` from `templates/plan-template.md`: technical approach, exact tool versions, file-level design, risks, and how the result will be verified. Approved before implementation starts.
3. **Break down.** Write `tasks.md`: numbered tasks, each small enough to be one commit, with a suggested commit message.
4. **Implement.** Execute tasks in order, committing atomically. Update `tasks.md` checkboxes as work lands.
5. **Ship.** Open a PR to `main` using the PR template. The PR references the spec and demonstrates the acceptance criteria are met.

## Rules

- One spec = one branch (`spec/NNN-short-name`) = one pull request.
- Specs are drafted up front but detailed plans are written just-in-time, on the spec's own branch, so they reflect the real state of the toolchain.
- Acceptance criteria must be objectively checkable (a command that passes, a file that exists with a defined schema, a metric that is produced).
- A spec whose deliverable feeds the experiment (circuits, harnesses, instrumentation) must state its methodology traceability explicitly. If spec work reveals a conflict with `docs/methodology.md`, work stops and the conflict is raised — the methodology is only changed deliberately, never silently.

## Definition of done

A spec is done when:

- [ ] All acceptance criteria in `spec.md` pass and are demonstrated in the PR description.
- [ ] `nargo fmt --check` and `nargo test` pass at the workspace root (CI enforces this).
- [ ] All commits follow the conventions in `CLAUDE.md` (Conventional Commits, English, no attribution trailers).
- [ ] The PR is merged into `main`.

## Spec index

| # | Spec | Status | Depends on |
|---|------|--------|------------|
| 000 | project-foundation (this structure) | done | — |
| 001 | [range-proof-circuits](001-range-proof-circuits/spec.md) | in review | — |
| 002 | [proof-pipeline-and-verifier](002-proof-pipeline-and-verifier/spec.md) | drafted | 001 |
| 003 | [native-benchmark-harness](003-native-benchmark-harness/spec.md) | drafted | 002 |
| 004 | [wasm-benchmark-harness](004-wasm-benchmark-harness/spec.md) | drafted | 002 |
| 005 | [evm-gas-instrumentation](005-evm-gas-instrumentation/spec.md) | drafted | 002 |
| 006 | [statistical-analysis](006-statistical-analysis/spec.md) | drafted | 003, 004, 005 |
