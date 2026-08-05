import path from "node:path";

import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
    // Excludes the `output: "standalone"` build's copy of the whole
    // workspace (including this very tests/ dir) under .next/standalone —
    // otherwise every test file runs twice after `next build` has been run
    // once. Both the ".next" symlink and its ".next.nosync" real target
    // (see docs/architecture.md's iCloud-sync notes) need excluding.
    exclude: [...configDefaults.exclude, "e2e/**", ".next/**", ".next.nosync/**"],
  },
});
