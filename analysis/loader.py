"""Session dataset loading for the statistical analysis (spec 006).

Every session file is validated through the protocol contract
(benchmarks/native/validate_session.py) before parsing — the analysis never
consumes a dataset the validator would reject.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "benchmarks" / "native" / "validate_session.py"
CONDITIONS = ["range_proof_field", "range_proof_u8", "range_proof_u32", "range_proof_u64"]


class Session:
    def __init__(self, path: Path):
        self.path = path
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise ValueError(f"{path} rejected by protocol validator:\n{result.stdout}{result.stderr}")

        lines = path.read_text().splitlines()
        self.header = json.loads(lines[0])
        cycles = [json.loads(line) for line in lines[1:]]
        self.samples = {c: [] for c in CONDITIONS}
        self.failures = {c: 0 for c in CONDITIONS}
        for cycle in cycles:
            if cycle["phase"] != "measure":
                continue
            if cycle["ok"]:
                self.samples[cycle["variant"]].append(cycle["proving_ms"])
            else:
                self.failures[cycle["variant"]] += 1

    @property
    def environment(self) -> str:
        return self.header["environment"]

    @property
    def n_planned(self) -> int:
        return self.header["protocol"]["sample_blocks"]

    def ok_rate(self, condition: str) -> float:
        return len(self.samples[condition]) / self.n_planned


def latest_session(directory: Path) -> Session:
    """Loads the most recent session in a results directory."""
    files = sorted(directory.glob("session-*.jsonl"))
    if not files:
        raise FileNotFoundError(f"no session files in {directory}")
    return Session(files[-1])


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())
