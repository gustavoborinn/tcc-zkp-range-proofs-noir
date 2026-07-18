#!/usr/bin/env bash
# End-to-end proving pipeline (docs/methodology.md, Fase 1 and section 3.4
# metric 3). For each circuit variant: generate the witness with canonical
# inputs, produce an UltraHonk proof targeting EVM verification (keccak + ZK),
# verify it locally, and record artifact sizes. Proof artifacts land in
# results/proofs/<variant>/ and sizes in results/proof-metrics.json.
#
# Canonical inputs are identical across variants so proof artifacts are
# structurally comparable: v=50 (private), a=10, b=100 (public).
set -euo pipefail

cd "$(dirname "$0")/.."
out="results/proof-metrics.json"

command -v bb >/dev/null 2>&1 || { echo "error: bb not found in PATH" >&2; exit 1; }

bb_version=$(bb --version | tail -n 1)
nargo_version=$(nargo --version | head -n 1 | sed 's/nargo version = //')

nargo compile >/dev/null

records="[]"
for pkg in range_proof_field range_proof_u8 range_proof_u32 range_proof_u64; do
  echo "--- $pkg"
  printf 'v = "50"\na = "10"\nb = "100"\n' > "circuits/$pkg/Prover.toml"
  nargo execute --package "$pkg" >/dev/null

  dir="results/proofs/$pkg"
  mkdir -p "$dir"
  bb prove -b "target/$pkg.json" -w "target/$pkg.gz" -o "$dir" -t evm --write_vk >/dev/null
  bb verify -t evm -k "$dir/vk" -p "$dir/proof" -i "$dir/public_inputs" >/dev/null \
    || { echo "error: local verification failed for $pkg" >&2; exit 1; }

  proof_bytes=$(wc -c < "$dir/proof")
  vk_bytes=$(wc -c < "$dir/vk")
  public_inputs_bytes=$(wc -c < "$dir/public_inputs")
  records=$(jq --arg v "$pkg" --argjson p "$proof_bytes" --argjson k "$vk_bytes" --argjson i "$public_inputs_bytes" \
    '. += [{variant: $v, proof_bytes: $p, vk_bytes: $k, public_inputs_bytes: $i}]' <<<"$records")
  echo "    proof=$proof_bytes B, vk=$vk_bytes B, public_inputs=$public_inputs_bytes B, verified locally"
done

jq -n --argjson r "$records" --arg nv "$nargo_version" --arg bv "$bb_version" \
  '{nargo_version: $nv, bb_version: $bv, verifier_target: "evm",
    canonical_inputs: {v: 50, a: 10, b: 100}, proofs: $r}' > "$out"

echo "wrote $out"
