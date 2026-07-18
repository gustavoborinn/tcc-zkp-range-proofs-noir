#!/usr/bin/env node
// Unattended WASM benchmark session driver.
//
// Prepares circuit artifacts and witnesses natively (outside any timed
// region), starts the COOP/COEP server, launches the *installed* Chrome as a
// real headful window via Playwright (headless mode would change the V8
// execution profile the methodology cares about), runs the harness page, and
// exits when the session has been persisted. Manual runs (opening the URL in
// Chrome yourself) remain fully supported without this driver.

import { spawn, execFileSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { chromium } from "playwright";

const REPO_ROOT = new URL("../..", import.meta.url).pathname;
const CONDITIONS = ["range_proof_field", "range_proof_u8", "range_proof_u32", "range_proof_u64"];
const PORT = 8787;

const args = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const [k, v] = a.replace(/^--/, "").split("=");
    return [k, v ?? true];
  }),
);
const burnin = args.burnin ?? 15;
const samples = args.samples ?? 100;
const seed = args.seed ?? ((Math.random() * 2 ** 32) >>> 0);
const label = args.label ?? "";

console.log("preparing artifacts and witnesses (native, untimed)");
execFileSync("nargo", ["compile"], { cwd: REPO_ROOT, stdio: "pipe" });
for (const pkg of CONDITIONS) {
  writeFileSync(`${REPO_ROOT}/circuits/${pkg}/Prover.toml`, 'v = "50"\na = "10"\nb = "100"\n');
  execFileSync("nargo", ["execute", "--package", pkg], { cwd: REPO_ROOT, stdio: "pipe" });
  if (!existsSync(`${REPO_ROOT}/target/${pkg}.gz`)) {
    throw new Error(`witness missing for ${pkg}`);
  }
}

console.log("building harness bundle");
execFileSync("npx", ["vite", "build"], { cwd: `${REPO_ROOT}/benchmarks/wasm`, stdio: "pipe" });

console.log(`starting server on :${PORT}`);
const server = spawn("python3", ["benchmarks/wasm/server.py", String(PORT)], {
  cwd: REPO_ROOT,
  stdio: ["ignore", "inherit", "inherit"],
});
process.on("exit", () => server.kill());
await new Promise((resolve) => setTimeout(resolve, 1000));

const url =
  `http://127.0.0.1:${PORT}/benchmarks/wasm/dist/index.html` +
  `?burnin=${burnin}&samples=${samples}&seed=${seed}&label=${label}`;
console.log(`launching Chrome (headful): ${url}`);

const browser = await chromium.launch({ channel: "chrome", headless: false });
const page = await browser.newPage();
page.on("console", (msg) => {
  if (msg.type() === "error") console.error(`browser: ${msg.text()}`);
});
await page.goto(url);

const timeoutMs = 60 * 60 * 1000;
await page.waitForFunction(
  () => window.__sessionDone || window.__sessionError,
  undefined,
  { timeout: timeoutMs, polling: 1000 },
);
const done = await page.evaluate(() => window.__sessionDone);
const error = await page.evaluate(() => window.__sessionError);

await browser.close();
server.kill();

if (error) {
  console.error(`session failed: ${error}`);
  process.exit(1);
}
console.log(`session complete: ${done}`);
