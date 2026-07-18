# Tasks: Spec 006 — Statistical Analysis and Reporting

**Plan:** [plan.md](plan.md)

Each task is sized to one atomic commit. Execute in order.

- [ ] T1: Add spec 006 plan and task breakdown.
      commit: `docs(specs): add plan and tasks for statistical analysis`
- [ ] T2: Add the analysis environment and session loader.
      commit: `feat(analysis): add session loader and pinned environment`
- [ ] T3: Add the statistics module (Brunner-Munzel, saturation rule, Holm-Bonferroni, failure gate) with unit tests.
      commit: `feat(analysis): add hypothesis testing with saturation rule`
- [ ] T4: Add figure generation and the report/table generator.
      commit: `feat(analysis): add figures and report generation`
- [ ] T5: Run the pipeline on the pilot datasets and commit the outputs.
      commit: `bench(analysis): generate pilot analysis report`
- [ ] T6: Append research-log entries, update the spec index and CLAUDE.md commands.
      commit: `docs: record analysis findings and update references`
