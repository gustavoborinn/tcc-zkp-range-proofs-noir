#!/usr/bin/env python3
"""EVM gas instrumentation on a local Sepolia fork (spec 005).

Implements methodology section 3.4, metric 2: forks Sepolia at the latest
block with anvil (sterile environment), deploys the four UltraHonk verifiers,
submits each variant's canonical verification transaction twice, and records
exact, decomposed gas figures. Any nondeterminism or EIP-7623 inconsistency
hard-fails the run — these are deterministic metrics, not samples.

Requires: anvil, forge, cast on PATH; proof artifacts from scripts/prove-all.sh.
SEPOLIA_RPC_URL overrides the default public fork endpoint.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from eip_costs import blob_projection, decompose_gas_used, floor_binds

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_RPC = "http://127.0.0.1:8545"
# anvil's first default funded account (local fork only, never a real key)
KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
VARIANTS = {
    "range_proof_field": "RangeProofFieldVerifier",
    "range_proof_u8": "RangeProofU8Verifier",
    "range_proof_u32": "RangeProofU32Verifier",
    "range_proof_u64": "RangeProofU64Verifier",
}


def run(cmd, cwd=REPO_ROOT, check=True):
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and proc.returncode != 0:
        sys.exit(f"error: {' '.join(cmd[:3])}... failed:\n{proc.stderr[-2000:]}")
    return proc


def cast(*args):
    return run(["cast", *args]).stdout.strip()


def main():
    rpc = os.environ.get("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")

    anvil = subprocess.Popen(
        ["anvil", "--fork-url", rpc, "--port", "8545", "--silent"],
        cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(120):
            if run(["cast", "chain-id", "--rpc-url", LOCAL_RPC], check=False).returncode == 0:
                break
            time.sleep(0.5)
        else:
            sys.exit("error: anvil fork did not start")

        chain_id = cast("chain-id", "--rpc-url", LOCAL_RPC)
        fork_block = int(cast("block-number", "--rpc-url", LOCAL_RPC))
        print(f"forked chain {chain_id} at block {fork_block}")

        run(["forge", "script", "script/Deploy.s.sol:Deploy",
             "--rpc-url", LOCAL_RPC, "--private-key", KEY, "--broadcast"],
            cwd=REPO_ROOT / "contracts")
        broadcast = REPO_ROOT / "contracts" / "broadcast" / "Deploy.s.sol" / chain_id / "run-latest.json"
        txs = json.loads(broadcast.read_text())["transactions"]
        addresses = {
            t["contractName"]: t["contractAddress"]
            for t in txs if t["transactionType"] == "CREATE" and t["contractName"] in VARIANTS.values()
        }

        records = []
        for pkg, contract in VARIANTS.items():
            addr = addresses[contract]
            proof_dir = REPO_ROOT / "results" / "proofs" / pkg
            proof_hex = "0x" + (proof_dir / "proof").read_bytes().hex()
            pub_bytes = (proof_dir / "public_inputs").read_bytes()
            inputs = "[" + ",".join(
                "0x" + pub_bytes[i:i + 32].hex() for i in range(0, len(pub_bytes), 32)
            ) + "]"

            calldata_hex = cast("calldata", "verify(bytes,bytes32[])", proof_hex, inputs)
            calldata = bytes.fromhex(calldata_hex[2:])

            gas_runs = []
            for _ in range(2):
                receipt = json.loads(cast(
                    "send", addr, "verify(bytes,bytes32[])", proof_hex, inputs,
                    "--rpc-url", LOCAL_RPC, "--private-key", KEY, "--json",
                ))
                if int(receipt["status"], 16) != 1:
                    sys.exit(f"error: verification transaction reverted for {pkg}")
                gas_runs.append(int(receipt["gasUsed"], 16))
            if gas_runs[0] != gas_runs[1]:
                sys.exit(f"error: nondeterministic gasUsed for {pkg}: {gas_runs}")
            gas_used = gas_runs[0]

            if floor_binds(gas_used, calldata):
                sys.exit(f"error: EIP-7623 floor binds for {pkg}; decomposition invalid")
            parts = decompose_gas_used(gas_used, calldata)
            payload = len((proof_dir / "proof").read_bytes()) + len(pub_bytes)
            record = {"variant": pkg, "verifier_address": addr,
                      **parts, "blob": blob_projection(payload)}
            records.append(record)
            print(f"{pkg}: gasUsed={gas_used} execution={parts['pure_execution_gas']} "
                  f"calldata_std={parts['calldata_standard_cost']} "
                  f"calldata_floor={parts['calldata_floor_cost']} "
                  f"blob_gas={record['blob']['fractional_blob_gas']}")

        out = REPO_ROOT / "results" / "gas" / "gas-metrics.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "chain_id": int(chain_id),
            "fork_block": fork_block,
            "rpc_source": "sepolia (public endpoint, fork only affects state, not results)",
            "compilation_profile": {"optimizer_runs": 1, "reason": "EIP-170 fit (spec 002)"},
            "determinism": "each gasUsed identical across 2 runs (hard-checked)",
            "eip7623": {"standard_token_cost": 4, "floor_per_token": 10, "tx_base": 21000},
            "variants": records,
        }, indent=2) + "\n")
        print(f"wrote {out}")
    finally:
        anvil.terminate()


if __name__ == "__main__":
    main()
