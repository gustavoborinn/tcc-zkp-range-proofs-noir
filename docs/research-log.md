# Research Log

Chronological record of empirical findings, design decisions, and toolchain facts produced during implementation. Each entry is objective and self-contained: what was observed, the evidence, the decision taken, and the implication for the thesis text or defense. Entries are appended in the same PR as the work that produced them (rule in `CLAUDE.md`).

Format: `## YYYY-MM-DD · <spec or scope> — <title>` with **Observation / Evidence / Decision / Thesis implication** fields as applicable.

---

## 2026-07-17 · spec 000 — Toolchain baseline established

**Observation:** Environment fixed at `nargo 1.0.0-beta.20` (satisfies the methodology's >= 0.38.0 floor), Foundry 1.1.0-stable, Python 3.12.3. Barretenberg CLI absent at foundation time.

**Decision:** Versions recorded in `CLAUDE.md` and pinned in CI (`noirup --version 1.0.0-beta.20`); no mid-experiment upgrades allowed.

**Thesis implication:** Reproducibility claim (methodology section 3.1) is backed by explicit version pinning in the repository and CI, citable in the methodology chapter.

## 2026-07-17 · spec 001 — Compiler eliminates trivial Field baseline formulations

**Observation:** Candidate baseline circuits over `Field` built on algebraic identities — e.g. `assert(d1 + d2 == b - a)` and `assert(d1 * d2 == (v - a) * (b - v))` — compile to **0 ACIR opcodes**: the Noir compiler proves them tautological and eliminates every constraint.

**Evidence:** `nargo info --json` on nargo 1.0.0-beta.20 reports `opcodes: 0` for both formulations; the adopted formulation reports 5.

**Decision:** Baseline fixed as `assert((v - a) * (b - v) != 0)`: binds the private witness to both public bounds through multiplicative arithmetic plus one inverse check, with no bit decomposition or lookup machinery. Guard added to `scripts/collect-circuit-metrics.sh`: any zero-opcode variant aborts metric collection.

**Thesis implication:** The baseline's predicate is intentionally different from a range check (ordering is inexpressible over a finite field — the very motivation for bit-width constraints). This must be stated when defending the baseline choice (methodology section 3.3): its role is isolating the fixed UltraHonk overhead, and a naive "identical circuit minus range checks" is not compilable to a nonzero circuit.

## 2026-07-17 · spec 001 — ACIR opcode counts do not differentiate bit-widths

**Observation:** The `u8`, `u32`, and `u64` variants compile to **identical** ACIR opcode counts (11 each; baseline: 5).

**Evidence:** `nargo info --json` per package; committed in `results/circuit-metrics.json`.

**Decision:** Report ACIR opcodes and backend gate counts side by side (dual instrumentation already required by methodology section 3.4, metric 4); treat ACIR parity as a finding, not a defect.

**Thesis implication:** ACIR abstracts bit-width — the width-dependent cost of range restrictions is expected to surface only in backend gates (`bb gates`) and proving time. This empirically validates the methodology's decision to instrument both the abstract (ACIR) and the backend (Barretenberg) layers, and matches the expectation in `docs/expected_results.md` that backend lookup optimizations may decouple circuit metrics from bit-width.

## 2026-07-17 · environment — Barretenberg version resolved by pairing, not manual choice

**Observation:** `bbup` (official installer) resolves the compatible Barretenberg version from the installed nargo: `nargo 1.0.0-beta.20` → `bb 5.0.0-nightly.20260324`.

**Evidence:** `bbup` output "Resolved to barretenberg version 5.0.0-nightly.20260324"; `bb --version` confirms.

**Decision:** `bb` version is always derived via `bbup`'s compatibility mapping, never picked manually; recorded in the `CLAUDE.md` stack table.

**Thesis implication:** The methodology's stack-pinning requirement ("`bb` version corresponding to `nargo`", section 3.1) is operationalized by an auditable, tool-resolved pairing — worth one sentence in the methodology chapter on how compatibility was guaranteed.
