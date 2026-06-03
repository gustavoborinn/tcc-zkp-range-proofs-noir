# Expected Results

This section describes the expected outcomes of the research before the final empirical measurements are collected. It does not report observed results. Its purpose is to state what the experiment is designed to produce and which tendencies are expected to be tested.

## Functional Correctness

The first expected result is a working Noir circuit that proves the predicate `a <= v <= b` while keeping `v` private and exposing only the interval bounds required by the verifier. Valid inputs are expected to generate acceptable proofs, and invalid inputs outside the interval are expected to fail during proof generation or verification. Negative tests should therefore confirm that the circuit is not under-constrained and that false claims about private attributes are rejected.

The Solidity verifier generated through Barretenberg is expected to validate UltraHonk proofs in an EVM-compatible environment. If the verifier exceeds the EIP-170 contract-size limit, the expected engineering outcome is either successful deployment after aggressive Solidity optimization or the adoption of a split-verifier architecture. In both cases, the result should make the deployment constraint explicit instead of treating verification as only an off-chain artifact.

## Proving-Time Behavior

Native proving is expected to be faster and more stable than WASM32 proving. The native Barretenberg execution path has direct access to the operating system memory model and avoids browser-specific constraints, while WASM32 execution depends on the browser engine, heap limits, compilation tiers, and thread availability. For this reason, the expected outcome for the environment comparison is a measurable latency penalty in the browser.

The WASM32 measurements are also expected to show higher dispersion than native measurements. Even after burn-in, browser execution may exhibit long-tail behavior caused by runtime scheduling, memory pressure, garbage collection, and JIT-related effects. The experiment is therefore expected to produce distributions that are better described through violin plots, empirical cumulative distribution functions, medians, interquartile ranges, and stochastic dominance tests than through mean-only summaries.

## Bit-Width and Lookup Cost

The `Field` circuit is expected to provide the baseline for isolating the cost of range restrictions. The `u8`, `u32`, and `u64` variants are expected to introduce additional proving work because integer comparisons and bounded numeric types require bit-width constraints and lookup-oriented mechanisms in the UltraHonk backend. The expected result is not necessarily a perfectly linear increase across bit-widths, since backend optimizations may decompose integers into smaller limbs or reuse lookup structures, but a measurable difference from the `Field` baseline is anticipated.

Among the integer variants, wider numeric types are expected to impose greater or equal circuit complexity than narrower types. This tendency should appear in ACIR opcode counts, backend gate counts, lookup-related work, or proving time. If proof size changes only slightly across variants, that outcome would still be consistent with a succinct proof system: the proving cost may increase even when the final proof artifact remains comparatively compact.

## EVM Verification and Data Costs

EVM execution gas for a fixed verifier and proof format is expected to behave deterministically. Unlike proving time, gas consumption should not require statistical hypothesis testing because the verifier contract executes the same bytecode over structurally equivalent inputs. The expected output is a direct comparison of verification cost across circuit variants, using transaction receipts from a controlled local fork.

Data publication costs are expected to be a central part of the economic analysis. Because proofs are submitted as calldata in a standalone EVM verifier, calldata gas should represent the practical cost of transmitting the proof to the contract. Blob-oriented costs are expected to function as a comparative projection for rollup or batching architectures, not as the direct cost model for the standalone verifier. This distinction should clarify which parts of the system are deployable as a direct smart contract and which parts would require additional infrastructure.

## Evaluation Artifacts

The research is expected to produce a set of reproducible artifacts: Noir circuit variants, generated proof and verifier artifacts, deployment or simulation scripts, benchmark logs, statistical summaries, and plots for proving-time distributions. The main quantitative outputs should include proving-time samples, failure rates when applicable, proof sizes in bytes, ACIR opcode counts, backend gate counts, execution gas, calldata gas estimates, and blob-gas projections.

The final results should allow the thesis to answer whether Noir-based Range Proofs are practical for privacy-preserving validation of private attributes under the chosen constraints. A positive result would not mean that all private smart contract applications become feasible, but that the evaluated predicate can be implemented, proved, and verified within measurable and reproducible cost boundaries. A negative or partially negative result would still be scientifically useful if it identifies the specific limiting factor, such as WASM32 latency, proof size, verifier bytecode size, or EVM data cost.

## Expected Contribution

The expected contribution is both technical and methodological. Technically, the work should provide an implementation path for validating hidden interval-bounded attributes in smart contracts through Noir and UltraHonk. Methodologically, it should provide a benchmark design that separates stochastic prover behavior from deterministic verifier and artifact metrics. This separation is expected to make the final analysis more reliable than a single aggregate performance number, especially in the presence of browser-based proving noise.
