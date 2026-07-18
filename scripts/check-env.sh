#!/usr/bin/env bash
# Verifies that the pinned toolchain (see CLAUDE.md) is installed.
# Exits non-zero if a required tool is missing so CI or a fresh clone fails fast.

set -u

status=0

check() {
  local name="$1" cmd="$2"
  if command -v "${cmd%% *}" >/dev/null 2>&1; then
    printf '%-22s %s\n' "$name" "$($cmd 2>/dev/null | head -n 1)"
  else
    printf '%-22s MISSING\n' "$name"
    status=1
  fi
}

check "nargo (Noir CLI)"     "nargo --version"
check "bb (Barretenberg)"    "bb --version"
check "forge (Foundry)"      "forge --version"
check "anvil (Foundry)"      "anvil --version"
check "python3"              "python3 --version"
check "node"                 "node --version"

exit "$status"
