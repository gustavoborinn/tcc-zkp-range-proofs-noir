// WASM32 proving benchmark harness (docs/methodology.md, Fase 2).
//
// Mirrors the native protocol of benchmarks/native/run_benchmark.py: K burn-in
// blocks discarded (also forcing V8 tier-up, Liftoff -> TurboFan), N recorded
// blocks, each block a seeded random permutation of the four conditions,
// witnesses prepared natively and fetched outside the timed region, failures
// recorded and never retried. The proof target is fixed at `evm` so the
// measured artifact is the one the deployed Solidity verifier accepts.

import { Barretenberg, BackendType, UltraHonkBackend } from "@aztec/bb.js";

const CONDITIONS = ["range_proof_field", "range_proof_u8", "range_proof_u32", "range_proof_u64"];
const VERIFIER_TARGET = "evm";

const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const log = (msg) => { logEl.textContent += msg + "\n"; };
const status = (msg) => { statusEl.textContent = msg; };

// Deterministic PRNG so the block ordering is reproducible from the seed.
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function permutation(rng, items) {
  const arr = items.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

async function main() {
  const params = new URLSearchParams(location.search);
  const burnIn = parseInt(params.get("burnin") ?? "15", 10);
  const samples = parseInt(params.get("samples") ?? "100", 10);
  const seed = parseInt(params.get("seed") ?? String((Math.random() * 2 ** 32) >>> 0), 10);
  const label = params.get("label") ?? "";

  if (!crossOriginIsolated) {
    status("FATAL: crossOriginIsolated is false — COOP/COEP headers missing; refusing to measure.");
    window.__sessionError = "not cross-origin isolated";
    return;
  }

  const threads = navigator.hardwareConcurrency;
  status(`preparing (threads=${threads}, seed=${seed}, K=${burnIn}, N=${samples})`);

  const rng = mulberry32(seed);
  const startedAt = new Date().toISOString();

  // Preparation stage — everything heavy happens outside the timed region.
  const api = await Barretenberg.new({ backend: BackendType.WasmWorker, threads });
  const backends = {};
  const witnesses = {};
  for (const pkg of CONDITIONS) {
    const artifact = await (await fetch(`/target/${pkg}.json`)).json();
    const witness = new Uint8Array(await (await fetch(`/target/${pkg}.gz`)).arrayBuffer());
    backends[pkg] = new UltraHonkBackend(artifact.bytecode, api);
    witnesses[pkg] = witness;
    log(`prepared ${pkg} (witness ${witness.length} bytes)`);
  }

  const header = {
    type: "session",
    label,
    environment: "wasm",
    verifier_target: VERIFIER_TARGET,
    protocol: { burn_in_blocks: burnIn, sample_blocks: samples, seed },
    conditions: CONDITIONS,
    canonical_inputs: { v: "50", a: "10", b: "100" },
    tools: {
      bbjs: "5.0.0-nightly.20260324",
      backend_type: "WasmWorker",
    },
    browser: {
      user_agent: navigator.userAgent,
      hardware_concurrency: threads,
      cross_origin_isolated: crossOriginIsolated,
    },
    started_at: startedAt,
  };

  const records = [JSON.stringify(header)];
  const totalBlocks = burnIn + samples;
  let lastProof = null;

  for (let block = 0; block < totalBlocks; block++) {
    const phase = block < burnIn ? "burnin" : "measure";
    const order = permutation(rng, CONDITIONS);
    for (let position = 0; position < order.length; position++) {
      const pkg = order[position];
      let provingMs = null;
      let ok = false;
      let error = null;
      const t0 = performance.now();
      try {
        const result = await backends[pkg].generateProof(witnesses[pkg], { verifierTarget: VERIFIER_TARGET });
        provingMs = performance.now() - t0;
        ok = true;
        if (phase === "measure") lastProof = { pkg, ...result };
      } catch (err) {
        provingMs = performance.now() - t0;
        error = String(err);
      }
      records.push(JSON.stringify({
        type: "cycle", phase, block, position, variant: pkg,
        proving_ms: Math.round(provingMs * 1000) / 1000,
        exit_code: ok ? 0 : 1, ok, ...(error ? { error } : {}),
      }));
    }
    if ((block + 1) % 10 === 0 || block + 1 === totalBlocks) {
      status(`block ${block + 1}/${totalBlocks} (${phase})`);
    }
  }

  // Persist one measured proof so the pipeline coherence check (native
  // bb verify against the same vk) can be replayed from browser output.
  if (lastProof) {
    header.last_proof = {
      variant: lastProof.pkg,
      proof_base64: btoa(String.fromCharCode(...lastProof.proof)),
      public_inputs: lastProof.publicInputs,
    };
    records[0] = JSON.stringify(header);
  }

  status("uploading session…");
  const response = await fetch("/session", { method: "POST", body: records.join("\n") });
  const { written } = await response.json();
  status(`done: ${written}`);
  window.__sessionDone = written;
  await api.destroy();
}

main().catch((err) => {
  status(`FATAL: ${err}`);
  window.__sessionError = String(err);
});
