// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {Script} from "forge-std/Script.sol";
import {RangeProofFieldVerifier} from "../src/RangeProofFieldVerifier.sol";
import {RangeProofU8Verifier} from "../src/RangeProofU8Verifier.sol";
import {RangeProofU32Verifier} from "../src/RangeProofU32Verifier.sol";
import {RangeProofU64Verifier} from "../src/RangeProofU64Verifier.sol";

// Deploys the four UltraHonk verifiers (and their linked libraries) to the
// target RPC. Addresses are read from the broadcast artifacts by
// scripts/deploy-fork.sh.
contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        new RangeProofFieldVerifier();
        new RangeProofU8Verifier();
        new RangeProofU32Verifier();
        new RangeProofU64Verifier();
        vm.stopBroadcast();
    }
}
