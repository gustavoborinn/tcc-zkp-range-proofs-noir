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

## 2026-07-17 · spec 002 — bb CLI requires an explicit EVM verifier target

**Observation:** bb 5.0.0-nightly.20260324 selects hash function and ZK settings via `-t/--verifier_target`: `evm` (keccak + ZK) for Solidity verification vs. the native default (poseidon2). Older flag styles (`--scheme`, `--oracle_hash`) are deprecated aliases. `forge create` cannot deploy the generated verifier (dynamic library linking); `forge script` handles library deployment and linking automatically.

**Evidence:** `bb prove --help-extended`; failed `forge create` run ("Dynamic linking not supported"); successful `forge script` broadcast.

**Decision:** The EVM pipeline (`scripts/prove-all.sh`, `scripts/generate-verifiers.sh`, `scripts/deploy-fork.sh`) uses `-t evm` consistently; deployment goes through `contracts/script/Deploy.s.sol`.

**Thesis implication:** Open methodological decision flagged for specs 003/004: proving-time benchmarks must fix one verifier target, and `-t evm` (keccak transcript) is the one that matches the deployed scenario. The choice and its rationale must be stated before latency collection begins.

## 2026-07-17 · spec 002 — Backend gates differentiate bit-widths; ACIR does not

**Observation:** Backend gate counts (`bb gates`, `circuit_size`): field = 40, u8 = 93, u32 = 2,791, u64 = 2,838 — while ACIR opcodes stay flat (11) for all integer variants. The dominant jump (~30x) sits between u8 and u32, not between u32 and u64.

**Evidence:** `results/circuit-metrics.json` (collected, bb 5.0.0-nightly.20260324).

**Decision:** Both layers are reported side by side; the u8→u32 threshold is treated as a first-class analysis subject (lookup-table machinery activation), not smoothed over.

**Thesis implication:** Empirically validates the methodology's dual instrumentation (section 3.4, metric 4) and refines the expectation of `docs/expected_results.md`: cost growth is a step function driven by backend lookup structures, not a linear function of bit-width.

## 2026-07-17 · spec 002 — Proof size grows stepwise; VK is constant

**Observation:** UltraHonk proof sizes with `-t evm`: field = 4,928 B, u8 = 5,312 B, u32 = u64 = 7,232 B. Verification key fixed at 1,888 B and public inputs at 64 B (two 32-byte words) across all variants.

**Evidence:** `results/proof-metrics.json`; artifacts in `results/proofs/`.

**Decision:** Canonical inputs (`v=50, a=10, b=100`) fixed across variants so artifacts stay structurally comparable.

**Thesis implication:** Consistent with succinct-proof expectations (`docs/expected_results.md`): proving cost can rise with bit-width while the artifact stays compact; the u32/u64 tie suggests size tracks circuit-size brackets (log growth), a point for the results chapter.

## 2026-07-17 · spec 002 — Verifiers fit EIP-170 with ~330 bytes of margin

**Observation:** With `optimizer_runs = 1`, every generated verifier compiles to 24,243–24,246 bytes of runtime bytecode — under the EIP-170 limit (24,576) by only ~330 bytes. All four deployed successfully to an anvil fork of Sepolia (chain id 11155111, block 11,295,933); valid proofs accepted on-chain (receipt `gasUsed`: field 1,935,854; u8 2,003,352; u32 2,340,916; u64 2,340,880), corrupted proofs and wrong public inputs rejected.

**Evidence:** `forge build --sizes`; `scripts/deploy-fork.sh` output; Foundry test suite (9/9).

**Decision:** Split-verifier topology not needed; `optimizer_runs = 1` retained. The ~330-byte margin is documented as a fragility: any future bb verifier growth may cross the limit.

**Thesis implication:** Directly answers the methodology's Fase 1 question: the generic UltraHonk verifier that historically exceeded EIP-170 (~33 KB) now fits after aggressive optimization — the deployment constraint is real but currently satisfiable without architectural workarounds. On-chain gas already exhibits the bit-width ordering that spec 005 will measure rigorously.

## 2026-07-18 · spec 003 — Latency benchmarks fix the verifier target at `evm`

**Observation:** bb proves against different transcripts per target: `evm` (keccak) vs. native default (poseidon2). The artifact whose latency matters for the thesis is the one the deployed Solidity verifier accepts.

**Decision:** All proving-time measurements — native (spec 003) and WASM (spec 004) — use `-t evm`, closing the open decision from spec 002. Additional protocol decisions: witness generation happens outside the timed region (deterministic input preparation; proving itself is randomized per run, keeping cycles independent); the verification key is precomputed and passed via `-k` (bb otherwise recomputes it inside `bb prove`); the timed unit is the wall-clock of the `bb prove` subprocess via monotonic clock, including constant process startup — documented as an additive component shared by all conditions.

**Thesis implication:** The environment comparison (Axis A) and bit-width comparison (Axis B) are internally consistent and match the deployment scenario. The startup caveat must accompany the native results; Brunner-Munzel, being rank-based, is unaffected by shared additive constants within a condition pair.

## 2026-07-18 · spec 003 — Pilot session: the u8→u32 step function reappears in proving time

**Observation:** Full-protocol pilot (K=15 burn-in, N=100 samples per condition, seeded block randomization, zero failures) on the development machine: median proving times field = 38.6 ms (IQR 36.7–40.4), u8 = 41.6 ms (39.6–44.0), u32 = 97.9 ms (93.8–101.6), u64 = 96.2 ms (93.7–98.8).

**Evidence:** `results/native/session-20260718T025555Z.jsonl` (seed 2928077471, machine metadata in the session header); validated by `benchmarks/native/validate_session.py`.

**Decision:** Session labeled `pilot`; official sessions for the thesis run on a quiet machine with the same harness. The dataset is committed as the first end-to-end exercise of the schema contract that spec 006 consumes.

**Thesis implication:** Proving latency reproduces the backend-gate step function (u8→u32 jump ≈ 2.4x in time vs. 30x in gates; u32 ≈ u64 in both) — evidence that lookup-table activation, not bit-width per se, drives the cost. Also note u64 median slightly below u32: an early sign that Axis B differences between adjacent wide types may be statistically indistinguishable, exactly what Brunner-Munzel with Holm-Bonferroni will test.
