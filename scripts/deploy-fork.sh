#!/usr/bin/env bash
# Deploys the four UltraHonk verifiers to a local anvil fork of Sepolia
# (docs/methodology.md, Fase 1 and section 3.4 metric 2: sterile environment,
# latest-block fork) and smoke-tests on-chain verification: a valid proof
# transaction must succeed and a corrupted one must revert. Full gas
# instrumentation is spec 005; this script proves deployability under EIP-170.
#
# Requires: anvil, forge, cast, xxd, jq; proofs from scripts/prove-all.sh.
# SEPOLIA_RPC_URL overrides the default public fork endpoint.
set -euo pipefail

cd "$(dirname "$0")/.."

rpc="${SEPOLIA_RPC_URL:-https://ethereum-sepolia-rpc.publicnode.com}"
local_rpc="http://127.0.0.1:8545"
# anvil's first default funded account (local fork only, never a real key)
key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

anvil --fork-url "$rpc" --port 8545 --silent &
anvil_pid=$!
trap 'kill $anvil_pid 2>/dev/null || true' EXIT

for _ in $(seq 1 60); do
  cast chain-id --rpc-url "$local_rpc" >/dev/null 2>&1 && break
  sleep 0.5
done
cast chain-id --rpc-url "$local_rpc" >/dev/null 2>&1 || { echo "error: anvil fork did not start" >&2; exit 1; }

fork_block=$(cast block-number --rpc-url "$local_rpc")
chain_id=$(cast chain-id --rpc-url "$local_rpc")
echo "forked chain id $chain_id at block $fork_block"

declare -A names=(
  [range_proof_field]=RangeProofFieldVerifier
  [range_proof_u8]=RangeProofU8Verifier
  [range_proof_u32]=RangeProofU32Verifier
  [range_proof_u64]=RangeProofU64Verifier
)

# forge script deploys the verifiers plus their linked external libraries in
# one broadcast; forge create cannot link dynamic libraries.
(cd contracts && forge script script/Deploy.s.sol:Deploy \
  --rpc-url "$local_rpc" --private-key "$key" --broadcast >/dev/null)

broadcast="contracts/broadcast/Deploy.s.sol/$chain_id/run-latest.json"
[ -f "$broadcast" ] || { echo "error: broadcast artifact not found at $broadcast" >&2; exit 1; }

for pkg in range_proof_field range_proof_u8 range_proof_u32 range_proof_u64; do
  name="${names[$pkg]}"
  echo "--- $name"
  addr=$(jq -r --arg n "$name" \
    '[.transactions[] | select(.transactionType == "CREATE" and .contractName == $n)][0].contractAddress' \
    "$broadcast")
  [ -n "$addr" ] && [ "$addr" != "null" ] || { echo "error: deploy failed for $name" >&2; exit 1; }
  code_bytes=$(( ($(cast code "$addr" --rpc-url "$local_rpc" | wc -c) - 3) / 2 ))
  echo "    deployed at $addr (runtime bytecode: $code_bytes bytes, EIP-170 limit: 24576)"

  proof_hex="0x$(xxd -p -c 0 "results/proofs/$pkg/proof")"
  pub_hex=$(xxd -p -c 0 "results/proofs/$pkg/public_inputs")
  inputs="[0x${pub_hex:0:64},0x${pub_hex:64:64}]"

  gas_used=$(cast send "$addr" "verify(bytes,bytes32[])" "$proof_hex" "$inputs" \
    --rpc-url "$local_rpc" --private-key "$key" --json | jq -r '.gasUsed')
  echo "    valid proof accepted on-chain (gasUsed: $((gas_used)))"

  corrupted="${proof_hex:0:1000}$(printf '%02x' $(( 0x${proof_hex:1000:2} ^ 0xff )))${proof_hex:1002}"
  if cast send "$addr" "verify(bytes,bytes32[])" "$corrupted" "$inputs" \
    --rpc-url "$local_rpc" --private-key "$key" --json >/dev/null 2>&1; then
    echo "error: corrupted proof was accepted by $name" >&2
    exit 1
  fi
  echo "    corrupted proof rejected on-chain"
done

echo "all verifiers deployed and smoke-tested on the Sepolia fork (block $fork_block)"
