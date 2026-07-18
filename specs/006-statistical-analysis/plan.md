# Plan: Spec 006 — Statistical Analysis and Reporting

**Spec:** [spec.md](spec.md)
**Status:** approved

## Technical approach

A Python package under `analysis/` turns committed session datasets into the thesis results. All methodological parameters are fixed upstream (methodology 3.2–3.4; FR-3b from the validity review): Brunner-Munzel for the stochastic metric, alpha = 0.05 two-tailed, Holm-Bonferroni on Axis B, exact analytical comparison (no tests) for deterministic metrics, median/IQR summaries, violin + ECDF figures.

Dependencies (scipy, numpy, matplotlib) are pinned in `analysis/requirements.txt` and installed into a local venv — the system Python is externally managed (verified during the validity review). The pipeline is a single entry point: sessions in, report + figures + LaTeX tables out, every number traceable to its input file.

### Statistical rules implemented

- **Brunner-Munzel (overlapping samples):** scipy's `brunnermunzel`, validated in unit tests against reference values. Relative effect `p̂ = P(X<Y) + 0.5·P(X=Y)` computed exactly by pairwise comparison (100×100 pairs — trivial).
- **Saturation rule (FR-3b, complete separation):** when samples do not overlap, the BM variance is zero and the asymptotic statistic undefined (observed in the pilots for every native-vs-WASM pair). The pipeline reports the exact relative effect (0 or 1) and the exact permutation bound `p = 2 / C(n+m, n)` (probability of complete separation in either direction under exchangeability) and marks the pair `saturated` in every table.
- **Holm-Bonferroni (Axis B):** three comparisons per environment (u8/u32/u64 vs. field baseline), ordered p-values, sequential rejection at alpha/(m−k+1); implemented directly and unit-tested (ordering, early-stop, all-reject and none-reject cases).
- **Failure-rate rule (methodology Fase 2.3):** conditions with < 85 ok samples out of 100 are excluded from latency testing and reported by failure rate; exercised in unit tests with a synthetic dataset (AC-5).

## Design

```
analysis/requirements.txt      # pinned scipy/numpy/matplotlib
analysis/loader.py             # session discovery + validation (delegates to
                               # benchmarks/native/validate_session.py) + parsing
analysis/stats.py              # BM wrapper, saturation rule, relative effect, Holm-Bonferroni,
                               # failure-rate gate — pure functions
analysis/test_stats.py         # unit tests (scipy reference values, Holm cases, saturation,
                               # synthetic failure dataset)
analysis/figures.py            # violin + ECDF per axis (matplotlib, deterministic)
analysis/run_analysis.py       # entry point: reads results/{native,wasm,gas}/ + circuit/proof
                               # metrics -> results/analysis/{report.md, figures/, tables/}
results/analysis/              # committed outputs (report, PNG figures, .tex tables)
```

Report structure (`report.md`): input inventory (files + seeds + git commits), Axis A table (per variant: medians, IQRs, relative effect, statistic/p or saturation bound), Axis B tables per environment with Holm-adjusted decisions, deterministic tables (ACIR/backend gates, proof sizes, decomposed gas, blob projection) rendered from the committed JSON, and figure references. LaTeX tables mirror the report tables for direct thesis inclusion.

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| scipy BM implementation nuances (dof, ties) | wrong p-values | unit tests against published/scipy reference values; ties absent in ms-resolution data anyway |
| Pilot-only data being read as final results | overclaiming | report header carries session labels (`pilot`) and machine metadata; official sessions rerun on a quiet machine replace the inputs without code changes |
| Matplotlib nondeterminism (fonts/layout) | churn in committed figures | fixed figsize/dpi/style, no timestamps in figures |

## Verification plan

1. `python -m unittest` in `analysis/` passes (BM reference, Holm, saturation, failure-rate synthetic).
2. `run_analysis.py` on the committed pilots produces the report, 4 figures, and LaTeX tables; saturated pairs are marked; u8-vs-field yields the p≈5.1e-11 seen in the review probe; u32-vs-u64 is not significant.
3. Deterministic tables reproduce the exact JSON values (spot-checked).
4. Deleting `results/analysis/` and rerunning regenerates byte-identical tables and report (figures identical at pixel level barring font cache).
