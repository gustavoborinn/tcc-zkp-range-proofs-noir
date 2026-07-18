# Spec 006: Statistical Analysis and Reporting

**Branch:** `spec/006-statistical-analysis`
**Status:** in review
**Depends on:** 003, 004, 005

## Overview

Implement the analysis pipeline that turns the collected samples into the thesis results: non-parametric hypothesis tests for the stochastic metric (proving time) across both experimental axes, exact comparative tables for the deterministic metrics, and publication-quality figures.

## Methodology traceability

- **Section 3.2 (Hypotheses):**
  - **Axis A (environment):** Brunner-Munzel test of stochastic equality between native and WASM proving times per variant; H1 = stochastic dominance of native execution (two-tailed, relative effect P(X<Y) + 0.5·P(X=Y) ≠ 0.5).
  - **Axis B (bit-width):** Brunner-Munzel tests of each integer variant (`u8`, `u32`, `u64`) against the `Field` baseline within each environment; family-wise error controlled with **Holm-Bonferroni**.
  - Significance level alpha = 0.05, two-tailed; N=100 supports the asymptotic approximation of Brunner-Munzel.
  - Deterministic metrics (gates, proof size, gas) receive **exact analytical comparison, no hypothesis tests**.
- **Section 3.3, Fase 2.3:** conditions flagged `failure-rate-only` (WASM failure > 15%) are excluded from latency testing and reported via their Failure Rate.
- **Section 3.4, Metric 1:** exploratory visual analysis via violin plots and empirical cumulative distribution functions (ECDF); summaries by median and IQR (no mean-only summaries).

## Functional requirements

- FR-1: Python package under `analysis/` (pinned dependencies, e.g. scipy for `brunnermunzel`, numpy, pandas, matplotlib) with a reproducible entry point: raw results in, full report out.
- FR-2: Loader validating the schema contract from specs 003/004 (shared loader), refusing malformed or incomplete sessions.
- FR-3: Axis A and Axis B test implementations producing: test statistic, p-value, relative effect estimate, and Holm-Bonferroni adjusted decisions for Axis B.
- FR-3b (validity-review requirement): an explicit saturation rule for completely separated samples, where the Brunner-Munzel variance estimate is zero and the statistic is undefined (already observed in the pilot data for every native-vs-WASM pair): report the relative effect (exactly 0 or 1) with an exact permutation-based p-value bound instead of the asymptotic statistic, and mark the pair as saturated in the output tables.
- FR-4: Figures: violin plots and ECDFs per condition and environment; deterministic-metric tables (ACIR opcodes, backend gates, proof size, execution/calldata/blob gas) formatted for direct inclusion in the thesis (LaTeX-friendly output).
- FR-5: A single generated report (Markdown) linking every number to its input data file and analysis version, for auditability.

## Out of scope

- Any data collection.
- Thesis prose (the report feeds the text; it is not the text).

## Acceptance criteria

- AC-1: Running the pipeline on the dry-run datasets from specs 003/004 completes and emits a schema-valid report (numbers meaningless but plumbing proven).
- AC-2: Brunner-Munzel implementation validated against a published worked example or scipy reference values.
- AC-3: Holm-Bonferroni ordering and rejection logic covered by unit tests.
- AC-4: All figures regenerate deterministically from committed summary data (fixed seeds where sampling is involved).
- AC-5: Failure-rate reporting path exercised by a synthetic dataset with a >15% failure condition.

## Open questions

- Exact figure styling for the thesis template (resolved when the thesis document format is fixed).
- Whether to also report bootstrap confidence intervals for the relative effect (supplementary, if methodology owner approves).
