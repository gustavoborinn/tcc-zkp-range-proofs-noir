# 1. Introduction

## 1.1 Context and Motivation

Public blockchains provide a transparent execution environment for smart contracts. This transparency is useful for auditability and consensus, but it also creates a privacy cost: contract rules often require users to reveal the exact data that proves their eligibility. A contract that checks solvency, age, token balance, or compliance status may only need to know whether a value satisfies a condition, yet the standard execution model exposes the value itself to the network. This tension is central to privacy-preserving applications on Ethereum-compatible systems.

Zero-Knowledge Proofs (ZKPs) address this problem by allowing a prover to convince a verifier that a statement is true without revealing the underlying witness. In this work, the relevant statement is a range relation: a private value `v` belongs to a public interval `[a, b]`. A Range Proof makes it possible to validate a private attribute, such as a balance or eligibility score, while disclosing only that the attribute satisfies the required bounds. This property is especially relevant for public ledgers, where transaction data and contract inputs can be inspected by anyone [Goldwasser et al., Year; Bunz et al., 2018; Buterin, 2013].

The practical adoption of Range Proofs, however, depends on engineering constraints as much as on cryptographic correctness. A proof that preserves privacy but takes too long to generate on a user's device, produces artifacts that are too large, or requires excessive EVM gas may be unsuitable for real smart contract workflows. The problem is sharper in client-side proving, where WebAssembly (WASM32) enables browser execution but introduces memory limits, compilation behavior, garbage collection effects, and threading constraints that differ from native execution. For this reason, the evaluation of a ZK circuit must measure not only whether the proof system works, but also how it behaves under the execution environments where users are expected to generate proofs.

Noir offers a high-level language for writing ZK circuits and compiling them to ACIR, an intermediate representation consumed by proof backends such as Barretenberg. In the Noir ecosystem, comparisons and integer constraints can be expressed with familiar programming constructs, while the backend translates them into arithmetic constraints, lookup tables, and proof artifacts. This abstraction improves developer ergonomics, but it does not remove the computational cost of range checks. Different numeric widths, such as `u8`, `u32`, and `u64`, may impose different proving costs because they affect how range constraints are represented and proved within UltraHonk [Noir Documentation, 2026; Barretenberg Documentation, Year].

## 1.2 Research Problem

The research problem addressed in this thesis is the practical viability of validating private attributes in Ethereum-compatible smart contracts through Noir-based Zero-Knowledge Range Proofs. The central relation is simple: prove that a hidden value `v` satisfies `a <= v <= b`, where `v` remains private and the interval bounds are public. The difficulty lies in determining the computational cost of this privacy guarantee when the circuit is compiled, proved, and verified through the actual toolchain used by developers.

This problem has two technical dimensions. The first is architectural: the prover may run as a native binary or inside a browser through WASM32, and these environments do not expose the same performance behavior. The second is cryptographic and representational: the use of restricted integer types may introduce lookup-related overhead compared with an unrestricted `Field` baseline. A defensible evaluation must isolate these dimensions and measure their effect on proving time, proof size, circuit complexity, backend gate count, and EVM verification cost.

## 1.3 Objectives

The general objective of this thesis is to develop, deploy, and evaluate a Zero-Knowledge Range Proof circuit in Noir for validating private attributes in Ethereum-compatible smart contracts.

The specific objectives are:

1. To implement a Noir circuit that proves the relation `a <= v <= b` without revealing the private value `v`.
2. To compile the circuit through the Noir and Barretenberg toolchain, using ACIR and UltraHonk as the proof pipeline.
3. To generate and deploy an EVM-compatible Solidity verifier, accounting for bytecode-size constraints such as EIP-170.
4. To compare native and WASM32 proving environments through repeated latency measurements.
5. To evaluate the effect of numeric widths by comparing `Field`, `u8`, `u32`, and `u64` circuit variants.
6. To measure deterministic artifacts, including proof size, ACIR opcodes, backend gates, execution gas, and data publication costs.
7. To validate the logical soundness of the circuit through negative tests that attempt to prove invalid inputs.

## 1.4 Research Question and Hypotheses

The thesis is guided by the following research question:

How viable is a Noir/UltraHonk Range Proof for privacy-preserving validation of private attributes in Ethereum-compatible smart contracts when evaluated across native and WASM32 proving environments and across different numeric bit-widths?

Two empirical hypotheses structure the performance evaluation. The first concerns the execution environment: native proving is expected to exhibit lower latency than WASM32 proving because browser execution introduces additional constraints related to memory, compilation tiers, and runtime behavior. The second concerns range restriction cost: integer-based range constraints are expected to add measurable overhead relative to a `Field` baseline, since bit-width restrictions require additional proof-system work through lookup-oriented mechanisms.

These hypotheses apply to proving time, which is stochastic and sensitive to execution conditions. Deterministic metrics, such as proof size, gate count, and EVM execution gas for a fixed compiled artifact, are not treated as stochastic variables. They are compared directly as structural outputs of the compilation and verification pipeline.

## 1.5 Scope and Delimitations

This work focuses on the range validation predicate itself and intentionally excludes complex business logic. The evaluated circuit proves that a private attribute lies within a public interval; it does not implement a complete financial, identity, voting, or compliance application. This delimitation keeps the experiment centered on the cost of the cryptographic predicate rather than on unrelated application behavior.

The study also focuses on Ethereum-compatible verification. Sepolia is used as the public testnet reference, while gas measurement is designed to run in a local fork to reduce noise from RPC rate limits, mempool behavior, and transaction propagation. The analysis considers the EVM after recent data-cost changes, including calldata-oriented costs and blob-oriented scenarios. Blob gas is treated as a comparative projection for batched or rollup-like architectures, not as a direct replacement for calldata in a standalone L1 verifier.

The browser-proving evaluation is limited to WASM32 execution with the practical constraints of modern browser engines. The work does not claim to generalize across all devices, browsers, or hardware classes. Instead, it provides a controlled benchmark that makes the architectural penalty of browser proving explicit.

## 1.6 Methodological Overview

The research follows an applied performance-evaluation design. The circuit is written in Noir, compiled with `nargo`, and proved with Barretenberg under UltraHonk. The verifier is generated as Solidity code and evaluated in an EVM-compatible environment. The experiment compares native proving with WASM32 proving and compares circuit variants based on `Field`, `u8`, `u32`, and `u64`.

Proving time is measured through repeated runs after a burn-in phase that reduces cold-start and compilation-tier effects, especially in the browser. The order of circuit variants is randomized in blocks to reduce bias caused by heap state and long-running session effects. Because WASM32 latency may be asymmetric, multimodal, or heavy-tailed, the analysis avoids normality-dependent tests and uses the Brunner-Munzel test for stochastic comparison. For multiple comparisons against the `Field` baseline, Holm-Bonferroni correction controls family-wise error.

Deterministic metrics are collected separately. ACIR opcode counts and backend gates describe circuit complexity; proof size describes the transmission artifact; EVM gas separates verification execution from data publication costs. Negative tests are executed before performance measurement to ensure that invalid private values outside the interval do not produce acceptable proofs.

## 1.7 Expected Contribution

The expected contribution of this thesis is a reproducible evaluation of Noir-based Range Proofs for smart contract privacy. Rather than presenting ZKPs only as a cryptographic abstraction, the work examines the operational cost of using them in a realistic Web3 development pipeline. The resulting analysis should help identify when a Range Proof is practical for private attribute validation, which parts of the pipeline dominate cost, and how execution environment and numeric representation affect the feasibility of deployment.

The work also contributes an experimental structure for evaluating ZK circuits under noisy client-side conditions. By separating stochastic and deterministic metrics, using non-parametric statistical testing, and accounting for EVM deployment constraints, the thesis provides a methodology that can be reused for other small ZK predicates beyond Range Proofs.

## 1.8 Thesis Structure

The remainder of this thesis is organized as follows. The literature review presents the foundations of Zero-Knowledge Proofs, Range Proofs, smart contracts, the EVM, Noir, Barretenberg, UltraHonk, lookup arguments, and WASM32 execution. The methodology chapter defines the experimental design, toolchain, variables, metrics, hypotheses, and statistical tests. The results chapter reports the functional validation, proving-time measurements, circuit complexity, proof size, and EVM cost analysis. The discussion interprets the findings in relation to privacy-preserving smart contract design and client-side proving constraints. The conclusion summarizes the answer to the research question, states the limitations of the work, and outlines future research directions.
