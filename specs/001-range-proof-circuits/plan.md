# Plan: Spec 001 — Range Proof Circuits

**Spec:** [spec.md](spec.md)
**Status:** approved

## Technical approach

Four sibling Noir packages under `circuits/`, one per variant, registered as workspace members in the root `Nargo.toml`. The three integer variants (`u8`, `u32`, `u64`) are textually identical except for the numeric type of `v`, `a`, `b`, keeping the comparison valid: they constrain `a <= v <= b` with two comparison assertions carrying distinct failure messages (required for precise negative testing with `#[test(should_fail_with)]`).

The `Field` baseline cannot use comparison operators (no ordering over the BN254 field). Empirical probing on the installed toolchain (nargo 1.0.0-beta.20) showed that algebraically trivial identities — e.g. `(v - a) + (b - v) == b - a` — are eliminated by the compiler and produce **0 ACIR opcodes**, which would invalidate the baseline. The chosen formulation is:

```noir
assert((v - a) * (b - v) != 0);
```

This binds the private witness `v` to both public bounds through multiplicative arithmetic and one inverse check (5 ACIR opcodes, verified), involving **no bit decomposition or lookup-oriented range machinery**. Its predicate (`v` differs from both bounds) is intentionally not a range check — the baseline's role in the methodology (Section 3.3) is to expose the fixed circuit/lookup overhead of UltraHonk so the integer variants' deltas isolate the pure cost of range restriction. This rationale must be stated in the thesis text.

### Probe findings that shape the analysis

Measured with `nargo info --json` on nargo 1.0.0-beta.20:

| Circuit | ACIR opcodes |
|---------|--------------|
| `Field` baseline (`(v-a)*(b-v) != 0`) | 5 |
| `u8` / `u32` / `u64` (two comparisons) | 11 each — **identical across widths** |

ACIR abstracts bit-width: opcode counts do not differentiate `u8`/`u32`/`u64`. The width-dependent cost is expected to surface only in backend gate counts (`bb gates`, spec 002) and proving time (specs 003/004). This is consistent with `docs/expected_results.md` ("backend optimizations may decompose integers into smaller limbs or reuse lookup structures") and must be reported as a finding, not a defect.

## Stack and versions

- `nargo` 1.0.0-beta.20 (verified; syntax for `assert(cond, "msg")`, `#[test]`, `#[test(should_fail_with = "msg")]` and `nargo info --json` all probed on this exact version).
- `bb`: not installed; backend gate collection explicitly degrades to "pending" (spec 002 completes it), per AC-3.

## Design

```
Nargo.toml                          # workspace members: the four packages
circuits/
  range_proof_field/{Nargo.toml, src/main.nr}
  range_proof_u8/{Nargo.toml, src/main.nr}
  range_proof_u32/{Nargo.toml, src/main.nr}
  range_proof_u64/{Nargo.toml, src/main.nr}
scripts/collect-circuit-metrics.sh  # nargo info --json per package -> results/circuit-metrics.json
results/circuit-metrics.json        # committed deterministic metrics (ACIR now, backend gates in spec 002)
```

- Integer variants: `fn main(v: u64, a: pub u64, b: pub u64)` with `assert(v >= a, "value below lower bound")` and `assert(v <= b, "value above upper bound")` (types swapped per variant).
- Tests per integer variant: in-range interior, exactly-at-lower-bound, exactly-at-upper-bound (positive); below-range and above-range via `should_fail_with` matching the exact assertion messages. Test interval fixed at `[10, 100]` across all variants (fits `u8`, keeping inputs constant across widths as required by the spec).
- Baseline tests: passes for `v` strictly inside; fails (`should_fail_with`) for `v == a` and `v == b`, documenting the predicate difference.
- Metrics script: iterates workspace packages, extracts `programs[].functions[main].opcodes` from `nargo info --json` via `jq`, emits one JSON record per variant with fields `{variant, acir_opcodes, backend_gates: null, nargo_version, collected_at}`; `backend_gates` stays `null` with a `"pending: bb not installed"` note until spec 002.

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Compiler eliminates baseline constraints in a future nargo version | Baseline silently becomes 0-opcode, invalidating comparisons | Metrics script fails loudly if any variant reports 0 ACIR opcodes |
| ACIR parity across widths misread as "no cost difference" | Wrong thesis conclusion | Plan documents that differentiation is expected at backend/proving layers; results file records both metrics side by side |
| `should_fail_with` message drift | Negative tests pass vacuously on wrong failure | Messages are unique per bound and asserted exactly |

## Verification plan

1. `nargo test` at workspace root: all packages, positive and negative tests pass.
2. `nargo fmt --check` clean.
3. `scripts/collect-circuit-metrics.sh` produces `results/circuit-metrics.json` with 4 records, nonzero ACIR counts, and explicit pending marker for backend gates.
4. Diff review: integer variants differ only in the numeric type tokens (AC-4).
