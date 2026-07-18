// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {Test} from "forge-std/Test.sol";
import {RangeProofFieldVerifier} from "../src/RangeProofFieldVerifier.sol";
import {RangeProofU8Verifier} from "../src/RangeProofU8Verifier.sol";
import {RangeProofU32Verifier} from "../src/RangeProofU32Verifier.sol";
import {RangeProofU64Verifier} from "../src/RangeProofU64Verifier.sol";
import {ProofFixtures} from "./ProofFixtures.sol";

interface IHonkVerifier {
    function verify(bytes calldata proof, bytes32[] calldata publicInputs) external view returns (bool);
}

// Soundness gate for the on-chain side (methodology Fase 3): every verifier
// must accept the canonical valid proof and reject a corrupted one before any
// gas measurement is taken over these contracts.
contract RangeProofVerifiersTest is Test {
    IHonkVerifier fieldVerifier;
    IHonkVerifier u8Verifier;
    IHonkVerifier u32Verifier;
    IHonkVerifier u64Verifier;

    function setUp() public {
        fieldVerifier = IHonkVerifier(address(new RangeProofFieldVerifier()));
        u8Verifier = IHonkVerifier(address(new RangeProofU8Verifier()));
        u32Verifier = IHonkVerifier(address(new RangeProofU32Verifier()));
        u64Verifier = IHonkVerifier(address(new RangeProofU64Verifier()));
    }

    function assertAccepts(IHonkVerifier verifier, bytes memory proof, bytes32[] memory publicInputs) internal view {
        assertTrue(verifier.verify(proof, publicInputs), "valid proof rejected");
    }

    function assertRejects(IHonkVerifier verifier, bytes memory proof, bytes32[] memory publicInputs) internal view {
        // A corrupted proof must not verify: the generated Honk verifier
        // reverts on malformed input, but a false return also counts as
        // rejection.
        try verifier.verify(proof, publicInputs) returns (bool ok) {
            assertFalse(ok, "corrupted proof accepted");
        } catch {
            // expected: verifier reverted
        }
    }

    function corrupt(bytes memory proof) internal pure returns (bytes memory) {
        // Flip one byte in the middle of the proof body.
        proof[proof.length / 2] ^= 0xff;
        return proof;
    }

    function testFieldAcceptsValidProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.fieldProof();
        assertAccepts(fieldVerifier, proof, inputs);
    }

    function testU8AcceptsValidProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u8Proof();
        assertAccepts(u8Verifier, proof, inputs);
    }

    function testU32AcceptsValidProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u32Proof();
        assertAccepts(u32Verifier, proof, inputs);
    }

    function testU64AcceptsValidProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u64Proof();
        assertAccepts(u64Verifier, proof, inputs);
    }

    function testFieldRejectsCorruptedProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.fieldProof();
        assertRejects(fieldVerifier, corrupt(proof), inputs);
    }

    function testU8RejectsCorruptedProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u8Proof();
        assertRejects(u8Verifier, corrupt(proof), inputs);
    }

    function testU32RejectsCorruptedProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u32Proof();
        assertRejects(u32Verifier, corrupt(proof), inputs);
    }

    function testU64RejectsCorruptedProof() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u64Proof();
        assertRejects(u64Verifier, corrupt(proof), inputs);
    }

    function testRejectsWrongPublicInputs() public view {
        (bytes memory proof, bytes32[] memory inputs) = ProofFixtures.u64Proof();
        // Claim a different interval than the one the proof was generated for.
        inputs[1] = bytes32(uint256(40));
        assertRejects(u64Verifier, proof, inputs);
    }
}
