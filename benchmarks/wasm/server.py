#!/usr/bin/env python3
"""Static server for the WASM benchmark harness.

Serves the repository root with the COOP/COEP headers required for
cross-origin isolation (methodology section 3.3: SharedArrayBuffer and thread
parallelism are unavailable without them), plus a POST endpoint that persists
a completed benchmark session to results/wasm/, enriching the session header
with machine metadata and the git commit — information the browser cannot
know about the host.
"""

import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PORT = 8787


def cpu_model():
    try:
        match = re.search(r"model name\s*:\s*(.+)", Path("/proc/cpuinfo").read_text())
        return match.group(1).strip() if match else platform.processor()
    except OSError:
        return platform.processor()


def total_ram_bytes():
    try:
        match = re.search(r"MemTotal:\s*(\d+) kB", Path("/proc/meminfo").read_text())
        return int(match.group(1)) * 1024 if match else None
    except OSError:
        return None


def git_commit():
    out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
    return out.stdout.strip() if out.returncode == 0 else None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        if str(path).endswith(".wasm"):
            return "application/wasm"
        return super().guess_type(path)

    def do_POST(self):
        if self.path != "/session":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()

        lines = body.splitlines()
        header = json.loads(lines[0])
        header["machine"] = {
            "cpu": cpu_model(),
            "cores": len([l for l in Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("processor")]),
            "ram_bytes": total_ram_bytes(),
            "kernel": platform.release(),
            "os": platform.platform(),
        }
        header["git_commit"] = git_commit()

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        outdir = REPO_ROOT / "results" / "wasm"
        outdir.mkdir(parents=True, exist_ok=True)
        out = outdir / f"session-{stamp}.jsonl"
        out.write_text("\n".join([json.dumps(header)] + lines[1:]) + "\n")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"written": str(out.relative_to(REPO_ROOT))}).encode())
        print(f"session written: {out}")

    def log_message(self, fmt, *args):
        pass  # keep benchmark output readable


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    print(f"serving {REPO_ROOT} on http://127.0.0.1:{port} with COOP/COEP")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
