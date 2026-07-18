#!/usr/bin/env python3
"""Native proving-time benchmark harness.

Implements the heavy-tailed benchmarking protocol of docs/methodology.md
(Fase 2) for the native execution environment: K burn-in blocks discarded to
mitigate cold-start effects, N recorded blocks, and block-randomized condition
ordering so cumulative machine state acts as stochastic noise rather than a
confounder. Every cycle is one `bb prove` subprocess timed with a monotonic
clock; failures are recorded, never retried.

The proof target is fixed at `evm` (keccak + ZK): the artifact under
measurement must be the artifact the deployed Solidity verifier accepts.
Stdlib only — no external dependencies.
"""

import argparse
import json
import platform
import random
import re
import secrets
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONDITIONS = ["range_proof_field", "range_proof_u8", "range_proof_u32", "range_proof_u64"]
VERIFIER_TARGET = "evm"
CANONICAL_INPUTS = {"v": "50", "a": "10", "b": "100"}


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, **kwargs)


def tool_version(cmd):
    try:
        out = run(cmd)
        return out.stdout.strip().splitlines()[-1] if out.returncode == 0 else None
    except FileNotFoundError:
        return None


def cpu_model():
    try:
        text = Path("/proc/cpuinfo").read_text()
        match = re.search(r"model name\s*:\s*(.+)", text)
        return match.group(1).strip() if match else platform.processor()
    except OSError:
        return platform.processor()


def total_ram_bytes():
    try:
        text = Path("/proc/meminfo").read_text()
        match = re.search(r"MemTotal:\s*(\d+) kB", text)
        return int(match.group(1)) * 1024 if match else None
    except OSError:
        return None


def git_commit():
    out = run(["git", "rev-parse", "HEAD"])
    return out.stdout.strip() if out.returncode == 0 else None


def prepare(workdir):
    """Compile the workspace and produce one witness + vk per condition,
    outside any timed region."""
    print("preparing: nargo compile")
    compile_run = run(["nargo", "compile"])
    if compile_run.returncode != 0:
        sys.exit(f"error: nargo compile failed:\n{compile_run.stderr}")

    witness_ms = {}
    for pkg in CONDITIONS:
        prover = REPO_ROOT / "circuits" / pkg / "Prover.toml"
        prover.write_text("".join(f'{k} = "{v}"\n' for k, v in CANONICAL_INPUTS.items()))
        start = time.monotonic_ns()
        execute = run(["nargo", "execute", "--package", pkg])
        witness_ms[pkg] = (time.monotonic_ns() - start) / 1e6
        if execute.returncode != 0:
            sys.exit(f"error: witness generation failed for {pkg}:\n{execute.stderr}")

        vk = REPO_ROOT / "results" / "proofs" / pkg / "vk"
        if not vk.is_file():
            sys.exit(f"error: {vk} missing; run scripts/prove-all.sh first")
        print(f"prepared {pkg}: witness in {witness_ms[pkg]:.1f} ms")
    return witness_ms


def prove_once(pkg, outdir):
    """One timed proving cycle. Returns (proving_ms, exit_code)."""
    start = time.monotonic_ns()
    proc = run([
        "bb", "prove",
        "-b", f"target/{pkg}.json",
        "-w", f"target/{pkg}.gz",
        "-k", f"results/proofs/{pkg}/vk",
        "-t", VERIFIER_TARGET,
        "-o", str(outdir),
    ])
    elapsed_ms = (time.monotonic_ns() - start) / 1e6
    return elapsed_ms, proc.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--burn-in", type=int, default=15, help="burn-in blocks, discarded (methodology: 15)")
    parser.add_argument("--samples", type=int, default=100, help="recorded blocks per condition (methodology: 100)")
    parser.add_argument("--seed", type=int, default=None, help="randomization seed (default: fresh, persisted)")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "results" / "native")
    parser.add_argument("--label", default="", help="free-form session label (e.g. 'pilot')")
    args = parser.parse_args()

    if shutil.which("bb") is None:
        sys.exit("error: bb not found in PATH")

    seed = args.seed if args.seed is not None else secrets.randbits(32)
    rng = random.Random(seed)
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scratch = args.output_dir / "raw" / f"session-{stamp}"
    scratch.mkdir(parents=True, exist_ok=True)
    session_path = args.output_dir / f"session-{stamp}.jsonl"

    witness_ms = prepare(scratch)

    header = {
        "type": "session",
        "label": args.label,
        "environment": "native",
        "verifier_target": VERIFIER_TARGET,
        "protocol": {"burn_in_blocks": args.burn_in, "sample_blocks": args.samples, "seed": seed},
        "conditions": CONDITIONS,
        "canonical_inputs": CANONICAL_INPUTS,
        "witness_generation_ms": witness_ms,
        "tools": {
            "nargo": tool_version(["nargo", "--version"]),
            "bb": tool_version(["bb", "--version"]),
            "python": platform.python_version(),
        },
        "machine": {
            "cpu": cpu_model(),
            "cores": len([l for l in Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("processor")]),
            "ram_bytes": total_ram_bytes(),
            "kernel": platform.release(),
            "os": platform.platform(),
        },
        "git_commit": git_commit(),
        "started_at": started.isoformat(),
    }

    failures = {pkg: 0 for pkg in CONDITIONS}
    with session_path.open("w") as out:
        out.write(json.dumps(header) + "\n")
        total_blocks = args.burn_in + args.samples
        for block in range(total_blocks):
            phase = "burnin" if block < args.burn_in else "measure"
            order = rng.sample(CONDITIONS, k=len(CONDITIONS))
            for position, pkg in enumerate(order):
                proving_ms, code = prove_once(pkg, scratch)
                ok = code == 0
                if phase == "measure" and not ok:
                    failures[pkg] += 1
                out.write(json.dumps({
                    "type": "cycle", "phase": phase, "block": block,
                    "position": position, "variant": pkg,
                    "proving_ms": round(proving_ms, 3),
                    "exit_code": code, "ok": ok,
                }) + "\n")
            if (block + 1) % 10 == 0 or block + 1 == total_blocks:
                print(f"block {block + 1}/{total_blocks} ({phase})")

    print(f"wrote {session_path}")
    for pkg, count in failures.items():
        if count:
            print(f"warning: {count} failed cycles for {pkg}", file=sys.stderr)


if __name__ == "__main__":
    main()
