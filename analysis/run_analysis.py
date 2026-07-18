#!/usr/bin/env python3
"""Analysis pipeline entry point (spec 006).

Reads the committed datasets (latency sessions, circuit/proof/gas metrics),
applies the methodology's statistical rules, and writes the auditable report,
figures, and LaTeX tables to results/analysis/. Every number in the report is
traceable to an input file listed in the inventory section.
"""

import statistics
from pathlib import Path

import figures
from loader import CONDITIONS, REPO_ROOT, latest_session, load_json
from stats import ALPHA, compare, failure_gate, holm_bonferroni

SHORT = {"range_proof_field": "Field", "range_proof_u8": "u8",
         "range_proof_u32": "u32", "range_proof_u64": "u64"}
OUT = REPO_ROOT / "results" / "analysis"


def med_iqr(xs):
    xs = sorted(xs)
    n = len(xs)
    return statistics.median(xs), xs[n // 4], xs[(3 * n) // 4]


def fmt_p(result):
    return f"<= {result['p_value']:.2e} (sat.)" if result["saturated"] else f"{result['p_value']:.2e}"


def latex_table(headers, rows, caption, label):
    cols = "l" * len(headers)
    lines = ["\\begin{table}[htbp]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             f"\\begin{{tabular}}{{{cols}}}", "\\toprule",
             " & ".join(headers) + " \\\\", "\\midrule"]
    lines += [" & ".join(str(c) for c in row) + " \\\\" for row in rows]
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    (OUT / "tables").mkdir(exist_ok=True)

    native = latest_session(REPO_ROOT / "results" / "native")
    wasm = latest_session(REPO_ROOT / "results" / "wasm")
    circuit = load_json(REPO_ROOT / "results" / "circuit-metrics.json")
    proofs = load_json(REPO_ROOT / "results" / "proof-metrics.json")
    gas = load_json(REPO_ROOT / "results" / "gas" / "gas-metrics.json")

    report = ["# Statistical Analysis Report", ""]
    report += ["## Input inventory", ""]
    for session in (native, wasm):
        report.append(
            f"- `{session.path.relative_to(REPO_ROOT)}` — environment **{session.environment}**, "
            f"label `{session.header.get('label', '')}`, seed {session.header['protocol']['seed']}, "
            f"git `{(session.header.get('git_commit') or 'n/a')[:8]}`"
        )
    for name in ("circuit-metrics.json", "proof-metrics.json", "gas/gas-metrics.json"):
        report.append(f"- `results/{name}`")
    report += ["", f"Significance level: alpha = {ALPHA} (two-tailed). "
               "Saturated pairs (complete separation) report the exact permutation bound "
               "p = 2/C(n+m, n) instead of the asymptotic Brunner-Munzel statistic (spec 006 FR-3b).", ""]

    # Failure gates (methodology Fase 2.3)
    report += ["## Failure-rate gates", ""]
    gates = {}
    rows = []
    for session in (native, wasm):
        for condition in CONDITIONS:
            gate = failure_gate(len(session.samples[condition]), session.n_planned)
            gates[(session.environment, condition)] = gate
            rows.append((session.environment, SHORT[condition],
                         f"{gate['ok_samples']}/{gate['planned']}",
                         f"{gate['failure_rate']:.1%}",
                         "included" if gate["latency_analysis"] else "**failure-rate only**"))
    report += ["| env | condition | ok | failure rate | latency analysis |",
               "|---|---|---|---|---|"]
    report += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    report.append("")

    def usable(env_session, condition):
        return gates[(env_session.environment, condition)]["latency_analysis"]

    # Axis A: native vs wasm per condition
    report += ["## Axis A — execution environment (native vs. WASM32)", ""]
    axis_a_rows = []
    for condition in CONDITIONS:
        if not (usable(native, condition) and usable(wasm, condition)):
            axis_a_rows.append((SHORT[condition], "excluded by failure gate", "", "", "", ""))
            continue
        x, y = native.samples[condition], wasm.samples[condition]
        result = compare(x, y, f"native-vs-wasm/{condition}").__dict__
        m_n, q1_n, q3_n = med_iqr(x)
        m_w, q1_w, q3_w = med_iqr(y)
        axis_a_rows.append((SHORT[condition],
                            f"{m_n:.1f} [{q1_n:.1f}, {q3_n:.1f}]",
                            f"{m_w:.1f} [{q1_w:.1f}, {q3_w:.1f}]",
                            f"{m_w / m_n:.2f}x",
                            f"{result['relative_effect']:.2f}",
                            fmt_p(result)))
    headers_a = ["condition", "native median [IQR] (ms)", "wasm median [IQR] (ms)",
                 "slowdown", "p_hat P(nat<wasm)", "p-value"]
    report += ["| " + " | ".join(headers_a) + " |", "|" + "---|" * len(headers_a)]
    report += ["| " + " | ".join(str(c) for c in row) + " |" for row in axis_a_rows]
    report.append("")
    (OUT / "tables" / "axis-a.tex").write_text(
        latex_table(headers_a, axis_a_rows, "Axis A: proving time by execution environment", "tab:axis-a"))

    # Axis B: variants vs Field baseline, per environment, Holm-Bonferroni
    report += ["## Axis B — bit-width vs. Field baseline (Holm-Bonferroni)", ""]
    for session in (native, wasm):
        env = session.environment
        family = [compare(session.samples[c], session.samples["range_proof_field"], f"{SHORT[c]}-vs-Field")
                  for c in CONDITIONS[1:] if usable(session, c) and usable(session, "range_proof_field")]
        decisions = holm_bonferroni(family)
        headers_b = ["comparison", "p_hat P(var<Field)", "p-value", "Holm threshold", "decision"]
        rows_b = [(d["comparison"], f"{d['relative_effect']:.2f}", fmt_p(d),
                   f"{d['holm_threshold']:.4f}",
                   "reject H0" if d["reject_h0"] else "retain H0") for d in decisions]
        report += [f"### {env}", "", "| " + " | ".join(headers_b) + " |", "|" + "---|" * len(headers_b)]
        report += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows_b]
        report.append("")
        (OUT / "tables" / f"axis-b-{env}.tex").write_text(
            latex_table(headers_b, rows_b, f"Axis B ({env}): bit-width cost vs. Field baseline", f"tab:axis-b-{env}"))

    # Supplementary: u32 vs u64 (adjacent wide types)
    supp = compare(native.samples["range_proof_u32"], native.samples["range_proof_u64"], "u32-vs-u64 (native)").__dict__
    report += ["Supplementary (no family correction): u32 vs u64, native: "
               f"p_hat = {supp['relative_effect']:.2f}, p = {fmt_p(supp)}.", ""]

    # Deterministic metrics (exact comparison, no tests)
    report += ["## Deterministic metrics (exact comparison — no hypothesis testing)", ""]
    gas_by = {v["variant"]: v for v in gas["variants"]}
    proof_by = {p["variant"]: p for p in proofs["proofs"]}
    circ_by = {c["variant"]: c for c in circuit["circuits"]}
    headers_d = ["variant", "ACIR opcodes", "backend gates", "proof (B)", "exec gas",
                 "calldata std", "calldata floor", "blob gas"]
    rows_d = [(SHORT[c], circ_by[c]["acir_opcodes"], circ_by[c]["backend_gates"],
               proof_by[c]["proof_bytes"], gas_by[c]["pure_execution_gas"],
               gas_by[c]["calldata_standard_cost"], gas_by[c]["calldata_floor_cost"],
               gas_by[c]["blob"]["fractional_blob_gas"]) for c in CONDITIONS]
    report += ["| " + " | ".join(headers_d) + " |", "|" + "---|" * len(headers_d)]
    report += ["| " + " | ".join(str(x) for x in row) + " |" for row in rows_d]
    report += ["", f"Gas measured on Sepolia fork block {gas['fork_block']} "
               f"(chain {gas['chain_id']}), compilation profile optimizer_runs = "
               f"{gas['compilation_profile']['optimizer_runs']} (EIP-170 fit).", ""]
    (OUT / "tables" / "deterministic.tex").write_text(
        latex_table(headers_d, rows_d, "Deterministic metrics per circuit variant", "tab:deterministic"))

    # Figures
    report += ["## Figures", ""]
    for path in (figures.violin_by_environment(native.samples, wasm.samples, OUT / "figures"),
                 figures.ecdf_axis_a(native.samples, wasm.samples, OUT / "figures"),
                 figures.ecdf_axis_b(native.samples, "native", OUT / "figures"),
                 figures.ecdf_axis_b(wasm.samples, "wasm", OUT / "figures")):
        report.append(f"![{path.stem}](figures/{path.name})")
    report.append("")

    (OUT / "report.md").write_text("\n".join(report))
    print(f"wrote {OUT / 'report.md'}, {len(list((OUT / 'tables').glob('*.tex')))} tables, "
          f"{len(list((OUT / 'figures').glob('*.png')))} figures")


if __name__ == "__main__":
    main()
