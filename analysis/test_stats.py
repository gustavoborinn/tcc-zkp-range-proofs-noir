"""Unit tests for the statistics module (spec 006 AC-2, AC-3, AC-5)."""

import unittest
from math import comb

from scipy.stats import brunnermunzel

from stats import (
    TestResult,
    compare,
    completely_separated,
    failure_gate,
    holm_bonferroni,
    relative_effect,
)


class TestRelativeEffect(unittest.TestCase):
    def test_all_smaller(self):
        self.assertEqual(relative_effect([1, 2], [3, 4]), 1.0)

    def test_all_larger(self):
        self.assertEqual(relative_effect([5, 6], [1, 2]), 0.0)

    def test_ties_count_half(self):
        # pairs: (1,1)=tie, (1,2)=win, (1,1)=tie, (1,2)=win -> (2 + 0.5*2)/4
        self.assertEqual(relative_effect([1, 1], [1, 2]), 0.75)


class TestCompare(unittest.TestCase):
    def test_matches_scipy_on_overlapping_samples(self):
        # Reference sample pair from the scipy brunnermunzel documentation.
        x = [1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 4, 1, 1]
        y = [3, 3, 4, 3, 1, 2, 3, 1, 1, 5, 4]
        expected_stat, expected_p = brunnermunzel(x, y)
        result = compare(x, y, "docs-example")
        self.assertFalse(result.saturated)
        self.assertAlmostEqual(result.statistic, float(expected_stat))
        self.assertAlmostEqual(result.p_value, float(expected_p))

    def test_saturation_rule_on_separation(self):
        x = [1.0, 2.0, 3.0]
        y = [10.0, 11.0, 12.0]
        self.assertTrue(completely_separated(x, y))
        result = compare(x, y, "separated")
        self.assertTrue(result.saturated)
        self.assertIsNone(result.statistic)
        self.assertEqual(result.relative_effect, 1.0)
        self.assertEqual(result.p_value, 2 / comb(6, 3))  # exact permutation bound = 0.1

    def test_saturation_direction_reversed(self):
        result = compare([10.0, 11.0], [1.0, 2.0], "reversed")
        self.assertTrue(result.saturated)
        self.assertEqual(result.relative_effect, 0.0)


def _fake(p, name="c"):
    return TestResult(name, 10, 10, 0.9, 1.0, p, False)


class TestHolmBonferroni(unittest.TestCase):
    def test_all_rejected(self):
        decisions = holm_bonferroni([_fake(0.001, "a"), _fake(0.002, "b"), _fake(0.003, "c")])
        self.assertTrue(all(d["reject_h0"] for d in decisions))
        # thresholds: 0.05/3, 0.05/2, 0.05/1 in ascending p order
        self.assertAlmostEqual(min(d["holm_threshold"] for d in decisions), 0.05 / 3)

    def test_step_down_stops_at_first_retention(self):
        # p = 0.001 rejected at 0.05/3; p = 0.04 > 0.05/2 retained;
        # p = 0.010 would pass 0.05/1 but must be retained by the step-down rule.
        decisions = holm_bonferroni([_fake(0.04, "a"), _fake(0.001, "b"), _fake(0.045, "c")])
        by_name = {d["comparison"]: d for d in decisions}
        self.assertTrue(by_name["b"]["reject_h0"])
        self.assertFalse(by_name["a"]["reject_h0"])
        self.assertFalse(by_name["c"]["reject_h0"])

    def test_none_rejected(self):
        decisions = holm_bonferroni([_fake(0.5, "a"), _fake(0.9, "b")])
        self.assertFalse(any(d["reject_h0"] for d in decisions))

    def test_preserves_input_order(self):
        decisions = holm_bonferroni([_fake(0.9, "z"), _fake(0.001, "a")])
        self.assertEqual([d["comparison"] for d in decisions], ["z", "a"])


class TestFailureGate(unittest.TestCase):
    def test_synthetic_condition_above_threshold_excluded(self):
        # 80/100 ok -> 20% failure -> latency analysis suspended (AC-5)
        gate = failure_gate(80, 100)
        self.assertFalse(gate["latency_analysis"])
        self.assertAlmostEqual(gate["failure_rate"], 0.20)

    def test_boundary_15_percent_included(self):
        gate = failure_gate(85, 100)
        self.assertTrue(gate["latency_analysis"])

    def test_zero_failures(self):
        gate = failure_gate(100, 100)
        self.assertTrue(gate["latency_analysis"])
        self.assertEqual(gate["failure_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
