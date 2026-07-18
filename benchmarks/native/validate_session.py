#!/usr/bin/env python3
"""Validates a benchmark session file against the protocol contract.

This is the schema contract that spec 006 (statistical analysis) builds on:
a session that passes here is guaranteed to have a metadata header, the
declared number of burn-in and measurement blocks, and block-randomized
condition ordering. Exits non-zero on any violation.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED_HEADER_KEYS = {
    "environment", "verifier_target", "protocol", "conditions",
    "tools", "machine", "git_commit", "started_at",
}
REQUIRED_CYCLE_KEYS = {"phase", "block", "position", "variant", "proving_ms", "exit_code", "ok"}


def fail(msg):
    sys.exit(f"invalid session: {msg}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    args = parser.parse_args()

    lines = args.session.read_text().splitlines()
    if not lines:
        fail("empty file")

    header = json.loads(lines[0])
    if header.get("type") != "session":
        fail("first record is not a session header")
    missing = REQUIRED_HEADER_KEYS - header.keys()
    if missing:
        fail(f"header missing keys: {sorted(missing)}")
    if header["protocol"].get("seed") is None:
        fail("randomization seed not persisted")

    conditions = header["conditions"]
    burn_in = header["protocol"]["burn_in_blocks"]
    samples = header["protocol"]["sample_blocks"]

    cycles = [json.loads(line) for line in lines[1:]]
    for i, cycle in enumerate(cycles):
        if cycle.get("type") != "cycle":
            fail(f"record {i + 1} is not a cycle")
        missing = REQUIRED_CYCLE_KEYS - cycle.keys()
        if missing:
            fail(f"cycle {i + 1} missing keys: {sorted(missing)}")

    expected = (burn_in + samples) * len(conditions)
    if len(cycles) != expected:
        fail(f"expected {expected} cycles, found {len(cycles)}")

    blocks = {}
    for cycle in cycles:
        blocks.setdefault(cycle["block"], []).append(cycle)
    for block_id, block in sorted(blocks.items()):
        variants = [c["variant"] for c in sorted(block, key=lambda c: c["position"])]
        if sorted(variants) != sorted(conditions):
            fail(f"block {block_id} is not a permutation of the conditions: {variants}")
        expected_phase = "burnin" if block_id < burn_in else "measure"
        phases = {c["phase"] for c in block}
        if phases != {expected_phase}:
            fail(f"block {block_id} has phase {phases}, expected {expected_phase}")

    measured = Counter(c["variant"] for c in cycles if c["phase"] == "measure")
    for condition in conditions:
        if measured[condition] != samples:
            fail(f"{condition}: {measured[condition]} measured cycles, expected {samples}")

    orders = {tuple(c["variant"] for c in sorted(b, key=lambda c: c["position"])) for b in blocks.values()}
    if len(blocks) >= 8 and len(orders) == 1:
        fail("all blocks share one condition order; randomization absent")

    ok_rate = {
        condition: sum(1 for c in cycles if c["phase"] == "measure" and c["variant"] == condition and c["ok"]) / samples
        for condition in conditions
    }
    print(f"valid session: {len(blocks)} blocks, {samples} samples/condition, seed {header['protocol']['seed']}")
    for condition, rate in ok_rate.items():
        marker = "" if rate == 1.0 else f"  <-- failure rate {(1 - rate):.1%}"
        print(f"  {condition}: {rate:.1%} ok{marker}")


if __name__ == "__main__":
    main()
