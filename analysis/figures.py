"""Figure generation (methodology section 3.4, metric 1: exploratory visual
analysis via violin plots and empirical cumulative distribution functions).

Deterministic output: fixed sizes, dpi, and styles; no timestamps.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SHORT = {"range_proof_field": "Field", "range_proof_u8": "u8",
         "range_proof_u32": "u32", "range_proof_u64": "u64"}
ORDER = ["range_proof_field", "range_proof_u8", "range_proof_u32", "range_proof_u64"]
DPI = 150


def violin_by_environment(native, wasm, outdir: Path):
    """Side-by-side violins per condition for both environments."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for ax, samples, title in ((axes[0], native, "Native"), (axes[1], wasm, "WASM32 (Chrome)")):
        data = [samples[c] for c in ORDER]
        parts = ax.violinplot(data, showmedians=True)
        for body in parts["bodies"]:
            body.set_alpha(0.6)
        ax.set_xticks(range(1, len(ORDER) + 1), [SHORT[c] for c in ORDER])
        ax.set_title(title)
        ax.set_ylabel("proving time (ms)")
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = outdir / "violin-proving-time.png"
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def ecdf_axis_a(native, wasm, outdir: Path):
    """ECDF per condition, native vs WASM overlaid (Axis A view)."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=False)
    for ax, condition in zip(axes.flat, ORDER):
        for samples, label, style in ((native, "native", "-"), (wasm, "wasm", "--")):
            xs = sorted(samples[condition])
            ys = [(i + 1) / len(xs) for i in range(len(xs))]
            ax.step(xs, ys, style, where="post", label=label)
        ax.set_title(SHORT[condition])
        ax.set_xlabel("proving time (ms)")
        ax.set_ylabel("ECDF")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    path = outdir / "ecdf-axis-a.png"
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def ecdf_axis_b(samples, environment: str, outdir: Path):
    """ECDF of all conditions in one environment (Axis B view)."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for condition in ORDER:
        xs = sorted(samples[condition])
        ys = [(i + 1) / len(xs) for i in range(len(xs))]
        ax.step(xs, ys, where="post", label=SHORT[condition])
    ax.set_xlabel("proving time (ms)")
    ax.set_ylabel("ECDF")
    ax.set_title(f"Axis B — {environment}")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = outdir / f"ecdf-axis-b-{environment}.png"
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path
