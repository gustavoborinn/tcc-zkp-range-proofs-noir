# Spec 001: Range Proof Circuits

**Branch:** `spec/001-range-proof-circuits`
**Status:** in review
**Depends on:** none

## Overview

Implement the four Noir circuit variants that constitute the experimental subjects of the thesis: a `Field` baseline and three integer-constrained variants (`u8`, `u32`, `u64`), each proving the predicate `a <= v <= b` with `v` private and the bounds `a`, `b` public. This spec also delivers the soundness test suite (positive and negative) required before any performance measurement, and the collection of deterministic complexity metrics per variant.

## Methodology traceability

- **Section 3.3 (Bit-width control and baseline):** the input `v` in `a <= v <= b` is tested under `u8`, `u32`, `u64` integer constraints; an identical circuit using unrestricted `Field` serves as the baseline that isolates the pure cost of the range restriction against the fixed lookup-table cost of UltraHonk.
- **Section 3.3, Fase 3 (Soundness audit):** negative tests submit inputs outside the permitted interval and must fail (Pass/Fail), assuring absence of under-constrained structures **before** any performance collection.
- **Section 3.4, Metric 4 (Constraint count):** dual deterministic instrumentation — ACIR opcodes via `nargo info` (abstract complexity) and exact backend gates via `bb gates` (real cryptographic weight). Note: `Field` has no native ordering, so the baseline comparison strategy (e.g., arithmetic identity constraints of equivalent structure) must be defined in `plan.md` and justified against the methodology's isolation goal.

## Functional requirements

- FR-1: Four Noir packages under `circuits/`: `range_proof_field`, `range_proof_u8`, `range_proof_u32`, `range_proof_u64`, all members of the root workspace.
- FR-2: Each integer variant constrains `a <= v <= b` via comparison assertions; `v` is private, `a` and `b` are `pub`.
- FR-3: The `Field` baseline is structurally identical except for the absence of bit-width range constraints, per the isolation strategy defined in `plan.md`.
- FR-4: Positive tests: in-range inputs (lower bound, upper bound, interior point) prove successfully in every variant.
- FR-5: Negative tests: out-of-range inputs (`v < a`, `v > b`) fail constraint checking in every integer variant (`#[test(should_fail)]` or the mechanism appropriate to the installed Noir version).
- FR-6: A script collects, per variant, ACIR opcode counts (`nargo info`) and backend gate counts (`bb gates`) into a committed machine-readable file under `results/`.

## Out of scope

- Proof generation and verification pipeline (spec 002).
- Any timing measurement (specs 003/004).

## Acceptance criteria

- AC-1: `nargo test` passes at the workspace root, covering all four packages, including negative tests.
- AC-2: `nargo fmt --check` passes.
- AC-3: `nargo info` runs successfully for each package and the metrics script emits one record per variant with ACIR opcode count; backend gate counts included if `bb` is installed, otherwise the script degrades explicitly (recorded as pending for spec 002).
- AC-4: The four variants differ only in the numeric type of `v`, `a`, `b` (verified by diff review in the PR).

## Open questions

- Exact formulation of the `Field` baseline circuit so it compiles to a non-trivial but range-unconstrained relation (resolved in plan.md against current Noir semantics).
- Bound semantics for each width (e.g., full-width intervals vs. fixed application interval) — must be constant across variants to keep the comparison valid.
