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

## 2026-07-18 · spec 004 — bb.js pairs exactly with native bb; browser proofs are pipeline-coherent

**Observation:** `@aztec/bb.js@5.0.0-nightly.20260324` exists on npm with the same version string as the native `bb`, and its API accepts `verifierTarget: 'evm'`. `Barretenberg.new({ backend: BackendType.WasmWorker })` must be forced: bb.js silently prefers the native binary when one is on PATH, which would corrupt the environment axis. Proofs generated in WASM (Node and real Chrome) are byte-compatible (7,232 B for u64) and verify against the native vk via `bb verify -t evm`.

**Evidence:** npm registry; installed type declarations; cross-verification runs (Node probe and the browser session's persisted proof, both exit 0).

**Decision:** Exact-version pairing enforced in `benchmarks/wasm/package.json` (no semver range). Every WASM session persists one measured proof so pipeline coherence is replayable from committed data.

**Thesis implication:** The environment comparison is apples-to-apples: same circuit, same witness, same proof format, same verifier — only the execution engine changes. This is the strongest possible internal validity for Axis A.

## 2026-07-18 · spec 004 — The bb.js browser build requires a bundler; the WASM binary ships inline

**Observation:** The bb.js browser build is unbundled ESM with bare specifiers (`pako`, `comlink`, `msgpackr`, `idb-keyval`) and module workers created via `new Worker(new URL(...), { type: 'module' })` — a plain `<script type="module">` cannot load it. The 3.5 MB WASM binary is embedded as a base64 data URL inside the module, so no external network fetch occurs (compatible with strict COEP).

**Evidence:** failed direct-import dry run (page hung with module resolution errors); `dest/browser/barretenberg_wasm/fetch_code/browser/` sources; successful Vite build emitting the workers as chunks.

**Decision:** Vite (`vite build`, `worker.format: 'es'`, static `dist/` output) bundles the harness; our COOP/COEP Python server serves the built page, keeping measurement serving free of dev-server transformations.

**Thesis implication:** Worth one paragraph on WASM deployment engineering: browser proving requires nontrivial toolchain support (bundler, cross-origin isolation, worker plumbing) that native proving does not — a qualitative cost of the WASM32 path beyond latency.

## 2026-07-18 · spec 004 — WASM pilot: uniform ~2.3–2.8x slowdown, same step function, zero failures

**Observation:** Full-protocol pilot in real Chrome 150 (headful, crossOriginIsolated, 12 threads, seed 871938275, zero failures): medians field = 102.8 ms, u8 = 116.1 ms, u32 = 227.7 ms, u64 = 225.8 ms. Against the native pilot: slowdown factors ≈ 2.7x, 2.8x, 2.3x, 2.3x. The u8→u32 step function reproduces in WASM; dispersion is modest (IQR widths ≈ 5–12 ms), with the expected long tail (u64 max 287 ms).

**Evidence:** `results/wasm/session-20260718T133509Z.jsonl`; native baseline `results/native/session-20260718T025555Z.jsonl`.

**Decision:** Pilot labeled `pilot`; official sessions on a quiet machine. The 15% failure-rate rule was armed but never triggered at these circuit sizes.

**Thesis implication:** Early evidence for Axis A's H1 (stochastic dominance of native) across all bit-widths, with a stable multiplicative penalty rather than pathological degradation — these circuits sit far below the wasm32 memory/gate ceilings, and that should frame the discussion of when browser proving is viable.

## 2026-07-18 · review — Timed-region asymmetry between environments is conservative for Axis A

**Observation:** The native harness times a fresh `bb prove` process per cycle (artifact/witness/vk loading included; process startup itself measured at ~0 ms), while the WASM harness times `generateProof` in a warm runtime with witnesses pre-fetched. The timed regions are therefore not perfectly symmetric.

**Evidence:** Harness designs (`benchmarks/native/run_benchmark.py` vs `benchmarks/wasm/harness.js`); `bb --version` timing floor ≈ 0 ms.

**Decision:** Kept as designed — each environment is measured the way it is actually used (CLI invocation vs. resident browser runtime), which is the methodology's ecological-validity stance. The asymmetry is documented instead of "corrected".

**Thesis implication:** The bias direction is conservative: per-cycle loading inflates native times, so the observed ~2.3–2.8x native advantage is a lower bound on the pure proving-engine gap. This must be stated alongside the Axis A results; it strengthens, not weakens, a native-dominance conclusion.

## 2026-07-18 · review — Brunner-Munzel degenerates under complete separation (pilot evidence)

**Observation:** Running Brunner-Munzel on the pilot sessions: every native-vs-WASM comparison and the native u32/u64-vs-field comparisons have completely separated samples (no overlap), making the BM variance estimate zero (division by zero; statistic undefined). Overlapping pairs behave normally (native u8 vs field: p ≈ 5.1e-11; native u32 vs u64: p ≈ 0.13, not significant).

**Evidence:** scipy `brunnermunzel` runs over `results/native/session-20260718T025555Z.jsonl` and `results/wasm/session-20260718T133509Z.jsonl`.

**Decision:** Spec 006 must implement an explicit saturation rule: when samples are completely separated, report the relative effect (exactly 0 or 1) with a documented exact bound (e.g., permutation-test p-value) instead of the asymptotic BM statistic. Requirement added to the spec before implementation.

**Thesis implication:** This is a "data too clear" condition, not a flaw: several hypothesis tests will saturate, and the results chapter should lean on effect sizes and distribution plots for those pairs, reserving formal test statistics for genuinely overlapping comparisons (e.g., adjacent wide types).

## 2026-07-18 · spec 005 — Gas decomposition reveals identical execution cost for u32 and u64

**Observation:** On the Sepolia fork (block 11,300,032), receipt `gasUsed` per verification: field 1,935,854; u8 2,003,352; u32 2,340,916; u64 2,340,880 — each identical across two runs (hard-checked). Decomposing via EIP-7623 (`pure_execution = gasUsed - 21000 - 4·tokens`): u32 and u64 have **exactly equal** execution gas (2,206,708); their 36-gas receipt difference is entirely calldata (zero-byte composition of the proof bytes). Field/u8/u32 execution: 1,838,390 / 1,899,684 / 2,206,708.

**Evidence:** `results/gas/gas-metrics.json`; `benchmarks/gas/eip_costs.py` unit-tested against hand-computed vectors, including the floor-boundary case where the receipt does not uniquely reveal execution gas (decomposition refuses).

**Decision:** Execution Gas is always reported decomposed, never as raw `gasUsed` (validity-review requirement FR-6). The EIP-7623 floor never binds for these execution-heavy transactions (asserted per variant).

**Thesis implication:** The deterministic-metric claim of the methodology is confirmed at receipt level, and the decomposition prevents a spurious u32-vs-u64 "difference" that a naive gasUsed comparison would report. On-chain verification cost mirrors the proof-size brackets (u32 = u64), not the bit-width — consistent with the succinctness narrative from spec 002.

## 2026-07-18 · spec 005 — Blob projection: proofs occupy 3.8–5.6% of one blob

**Observation:** Fractional EIP-4844 projection (payload = proof + public inputs, 1 blob-gas per byte at the 131,072-byte blob capacity): field 4,992; u8 5,376; u32/u64 7,296 blob-gas — i.e., 3.8–5.6% of a single blob per proof.

**Evidence:** `results/gas/gas-metrics.json` (`blob` records).

**Decision:** Reported in blob-gas units under the batching premise required by the methodology (payload rides a sequencer's blob; blob fee market pricing left symbolic).

**Thesis implication:** A rollup batching ~18–26 such proofs fills one blob, making the data-publication cost per proof orders of magnitude below the calldata path (76–113k gas standard, 191–283k floor) — the economic argument the methodology's fractional metric was designed to expose. Calldata floor cost (EIP-7623) is 2.5x the standard cost for these payloads, worth noting as the post-Pectra penalty on calldata-heavy usage.

## 2026-07-18 · spec 006 — Pilot hypothesis tests: both H1 axes supported; adjacent wide types indistinguishable

**Observation:** Full pipeline over the pilot sessions (alpha = 0.05, two-tailed): **Axis A** — native stochastically dominates WASM in all four conditions with complete separation (relative effect P(native<wasm) = 1.00; exact permutation bound p <= 2.21e-59 per pair). **Axis B** — all three variants reject H0 against the Field baseline in both environments under Holm-Bonferroni (native u8-vs-Field is the only overlapping pair: p = 5.06e-11, p_hat = 0.25). Supplementary: u32 vs u64 (native) is not significant (p = 0.13, p_hat = 0.44) — adjacent wide types are statistically indistinguishable, matching their identical execution gas and near-identical backend gates.

**Evidence:** `results/analysis/report.md` (input inventory lists session files, seeds, and git commits); unit-tested statistics module (`analysis/test_stats.py`, 13 tests: scipy reference values, Holm step-down cases, saturation rule, failure-gate boundary).

**Decision:** Saturated pairs are reported via the FR-3b rule (exact relative effect + permutation bound, marked "sat."), never via the undefined asymptotic statistic. The failure gate uses integer arithmetic — the 15% boundary (n = 85) is included, per the methodology's "more than 15%" wording; a float comparison misclassified the boundary during testing and was fixed.

**Thesis implication:** With pilot data, both alternative hypotheses of section 3.2 are supported, and the results chapter can already be drafted around: (1) uniform ~2.3–2.8x WASM penalty with dominance saturation; (2) bit-width cost as a step function whose interesting contrast is u8-vs-u32, not u32-vs-u64; (3) tests saturating because effects dwarf the noise — effect sizes and ECDF/violin plots carry the narrative where formal statistics degenerate. Official (non-pilot) sessions only need to replace the input files; the pipeline re-derives everything.

## 2026-07-18 · official collection — Dedicated sessions replicate the pilots

**Observation:** Official sessions (label `official`, dedicated run: AC power, no heavy concurrent load) replicate the pilot results within 1–4% on every median. Native: field 38.6 / u8 41.0 / u32 98.5 / u64 97.3 ms; WASM (Chrome 150): 104.5 / 117.9 / 237.5 / 234.3 ms; slowdowns 2.41–2.88x. Zero failures in 920 recorded cycles across both environments. All hypothesis-test conclusions unchanged: Axis A saturated dominance in all conditions; Axis B rejects H0 for every variant vs. Field under Holm-Bonferroni in both environments; supplementary u32-vs-u64 (native) remains non-significant (p = 0.053).

**Evidence:** `results/native/session-20260718T171730Z.jsonl` (seed 753410584), `results/wasm/session-20260718T171941Z.jsonl` (seed 3449093065); `results/analysis/report.md` regenerated from these inputs.

**Decision:** The `official` sessions are the datasets of record for the thesis; the `pilot` sessions remain committed as provenance and as evidence of result stability under background load.

**Thesis implication:** Pilot-vs-official agreement is itself reportable: the effects under study dwarf machine-load noise, supporting the robustness claims of the methodology (rank-based tests, block randomization). The u32-vs-u64 contrast sits at the significance boundary (p ≈ 0.05) in both collections — honest material for the discussion of when bit-width stops mattering.
