#!/usr/bin/env bash
# Collects the deterministic circuit-complexity metrics required by
# docs/methodology.md section 3.4 (metric 4): ACIR opcodes per variant via
# `nargo info --json`. Backend gate counts (`bb gates`) are collected by the
# spec 002 pipeline once bb is installed; until then this script records them
# as pending so the gap is explicit rather than silent.
set -euo pipefail

cd "$(dirname "$0")/.."
out="results/circuit-metrics.json"

nargo_version=$(nargo --version | head -n 1 | sed 's/nargo version = //')
info=$(nargo info --json)

backend_status="pending: bb not installed"
if command -v bb >/dev/null 2>&1; then
  backend_status="pending: collection implemented in spec 002"
fi

records="[]"
for pkg in range_proof_field range_proof_u8 range_proof_u32 range_proof_u64; do
  acir=$(jq -r --arg p "$pkg" \
    '.programs[] | select(.package_name == $p) | .functions[] | select(.name == "main") | .opcodes' \
    <<<"$info")
  if [ -z "$acir" ] || [ "$acir" -eq 0 ]; then
    echo "error: package $pkg reports ${acir:-no} ACIR opcodes;" \
      "a zero-opcode circuit invalidates the experimental comparison" >&2
    exit 1
  fi
  records=$(jq --arg v "$pkg" --argjson a "$acir" \
    '. += [{variant: $v, acir_opcodes: $a, backend_gates: null}]' <<<"$records")
done

jq -n --argjson r "$records" --arg nv "$nargo_version" --arg bs "$backend_status" \
  '{nargo_version: $nv, backend_gates_status: $bs, circuits: $r}' > "$out"

echo "wrote $out"
jq . "$out"
