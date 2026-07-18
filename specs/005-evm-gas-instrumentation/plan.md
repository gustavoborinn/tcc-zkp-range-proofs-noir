# Plan: Spec 005 — EVM Gas Instrumentation

**Spec:** [spec.md](spec.md)
**Status:** approved

## Technical approach

A Python orchestrator (stdlib only) drives the sterile measurement environment required by methodology section 3.4, metric 2: it forks Sepolia at the latest block with `anvil`, deploys the four verifiers via `forge script` (library linking), submits one verification transaction per variant with the canonical proof artifacts, and extracts `gasUsed` from the receipts. All cost arithmetic lives in a pure module implemented **from the EIP texts** and covered by unit tests against hand-computed vectors.

### Cost model (verified against the EIP specifications)

- **EIP-7623 (fetched from eips.ethereum.org):** `tokens_in_calldata = zero_bytes + 4 * nonzero_bytes`; `tx.gasUsed = 21000 + max(4 * tokens + execution_gas, 10 * tokens)` for non-creation transactions. Verification calls are execution-heavy (~2M gas ≫ floor), so the standard branch binds; the orchestrator asserts this (`gasUsed - 21000 > 10 * tokens`) and decomposes: `pure_execution_gas = gasUsed - 21000 - 4 * tokens`. Reported metrics per variant: receipt `gasUsed`, pure execution gas, calldata standard cost (`4 * tokens`), calldata floor cost (`10 * tokens`, the EIP-7623 control metric), calldata size in bytes.
- **EIP-4844 (fractional blob projection):** one blob = 131,072 bytes and costs `GAS_PER_BLOB = 131,072` blob gas — i.e., 1 blob-gas per byte at full utilization. The projection reports payload bytes (proof + public inputs), the fraction of one blob it occupies, and the fractional blob gas under the batching premise required by the methodology (the payload rides a sequencer's blob, not a standalone Type-3 transaction). Blob gas is priced by its own fee market, so results stay in blob-gas units with the assumption documented.

### Determinism protocol

The verifier contract is stateless (calldata + arithmetic only), so gas is exact per compilation profile and fork rules. The orchestrator submits each variant's transaction twice and hard-fails on any divergence in `gasUsed` — variance would indicate an environment defect, not noise to average (methodology: deterministic metrics receive exact comparison, no hypothesis testing).

### Framing constraint carried from spec 002

Gas figures are conditional on the `optimizer_runs = 1` compilation profile — the only profile that fits EIP-170 without a split verifier. Size optimization raises runtime gas; this trade-off is recorded in the research log and must accompany the results chapter.

## Design

```
benchmarks/gas/eip_costs.py       # pure functions: tokens_in_calldata, EIP-7623 decomposition,
                                  # blob fraction/gas — no I/O, fully unit-testable
benchmarks/gas/test_eip_costs.py  # unittest: hand-computed vectors (incl. floor-binding cases)
benchmarks/gas/measure_gas.py     # orchestrator: anvil fork -> forge script deploy -> cast send x2
                                  # per variant -> receipt parse -> decomposition -> JSON
results/gas/gas-metrics.json      # committed dataset keyed by variant, fork block, chain id
```

Calldata is produced with `cast calldata "verify(bytes,bytes32[])" ...` (exact ABI encoding, no reimplementation), transactions with `cast send --json`; addresses come from the `forge script` broadcast artifact as in `scripts/deploy-fork.sh`. `SEPOLIA_RPC_URL` overrides the default public fork endpoint; the fork block and chain id are recorded in the dataset.

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| anvil fork not applying post-Pectra (Prague) rules | decomposition formula wrong | orchestrator cross-checks receipt `gasUsed` against the EIP-7623 identity using measured execution gas; hard-fails on inconsistency |
| Public RPC flakiness during fork | setup failures | RPC configurable; fork started once; failures abort loudly (never partial data) |
| Gas nondeterminism across runs | invalid deterministic claim | two-run identity check per variant, hard failure on divergence |

## Verification plan

1. `python3 -m unittest` passes on the cost module (vectors include zero/nonzero bytes and a synthetic floor-binding case).
2. `measure_gas.py` produces `results/gas/gas-metrics.json` with all four variants, two identical runs each, floor-branch assertion passing.
3. Dataset regenerated at a second fork block gives identical execution gas (block height only affects state, and the verifier is stateless).
