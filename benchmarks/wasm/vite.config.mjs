import { defineConfig } from "vite";

// Builds the harness page into a static bundle (dist/) that scripts serve
// with COOP/COEP headers. Vite resolves bb.js's bare specifiers and bundles
// its module workers (`new Worker(new URL(...), { type: "module" })`), which
// plain <script type="module"> loading cannot do.
export default defineConfig({
  base: "./",
  build: {
    target: "esnext",
    outDir: "dist",
    chunkSizeWarningLimit: 10000,
  },
  worker: {
    format: "es",
  },
});
