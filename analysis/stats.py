"""Hypothesis testing for the thesis (methodology section 3.2 + spec 006 FR-3b).

Pure functions. Stochastic metric only (proving time); deterministic metrics
are compared exactly elsewhere. Rules implemented:

- Brunner-Munzel (two-tailed) for overlapping samples, via scipy.
- Saturation rule for completely separated samples, where the BM variance is
  zero and the asymptotic statistic undefined: report the exact relative
  effect (0 or 1) with the exact permutation bound p = 2 / C(n+m, n) — the
  probability, under exchangeability, of complete separation in either
  direction.
- Relative effect p_hat = P(X < Y) + 0.5 * P(X = Y), computed exactly.
- Holm-Bonferroni step-down for the Axis B family (alpha = 0.05).
- Failure-rate gate (methodology Fase 2.3): conditions with more than 15%
  failed cycles are excluded from latency testing.
"""

from dataclasses import dataclass
from math import comb

from scipy.stats import brunnermunzel

ALPHA = 0.05
FAILURE_RATE_THRESHOLD = 0.15


def relative_effect(x, y) -> float:
    """Exact p_hat = P(X < Y) + 0.5 P(X = Y) over all pairs."""
    wins = sum(1 for a in x for b in y if a < b)
    ties = sum(1 for a in x for b in y if a == b)
    return (wins + 0.5 * ties) / (len(x) * len(y))


def completely_separated(x, y) -> bool:
    return max(x) < min(y) or max(y) < min(x)


@dataclass
class TestResult:
    comparison: str
    n_x: int
    n_y: int
    relative_effect: float
    statistic: float | None
    p_value: float
    saturated: bool

    def summary(self) -> str:
        if self.saturated:
            return (f"saturated (complete separation): relative effect = {self.relative_effect:.2f}, "
                    f"exact permutation bound p <= {self.p_value:.3e}")
        return f"BM statistic = {self.statistic:.3f}, p = {self.p_value:.3e}, p_hat = {self.relative_effect:.3f}"


def compare(x, y, comparison: str) -> TestResult:
    """Two-tailed comparison of two samples of proving times."""
    effect = relative_effect(x, y)
    if completely_separated(x, y):
        bound = 2 / comb(len(x) + len(y), len(x))
        return TestResult(comparison, len(x), len(y), effect, None, bound, True)
    statistic, p_value = brunnermunzel(x, y)
    return TestResult(comparison, len(x), len(y), effect, float(statistic), float(p_value), False)


def holm_bonferroni(results: list[TestResult], alpha: float = ALPHA) -> list[dict]:
    """Step-down Holm-Bonferroni over a family of comparisons.

    Returns one record per comparison with the adjusted threshold and the
    reject/retain decision, in the original input order.
    """
    m = len(results)
    order = sorted(range(m), key=lambda i: results[i].p_value)
    decisions = [None] * m
    rejecting = True
    for rank, idx in enumerate(order):
        threshold = alpha / (m - rank)
        reject = rejecting and results[idx].p_value <= threshold
        if not reject:
            rejecting = False  # step-down: once retained, all later retained
        decisions[idx] = {
            "comparison": results[idx].comparison,
            "p_value": results[idx].p_value,
            "holm_threshold": threshold,
            "reject_h0": reject,
            "saturated": results[idx].saturated,
            "relative_effect": results[idx].relative_effect,
            "statistic": results[idx].statistic,
        }
    return decisions


def failure_gate(ok_samples: int, planned: int) -> dict:
    """Methodology Fase 2.3: strictly more than 15% failures (n < 85 for
    N=100) suspends latency analysis. Integer arithmetic avoids float
    artifacts at the boundary."""
    failures = planned - ok_samples
    return {
        "ok_samples": ok_samples,
        "planned": planned,
        "failure_rate": failures / planned,
        "latency_analysis": failures * 100 <= int(FAILURE_RATE_THRESHOLD * 100) * planned,
    }
