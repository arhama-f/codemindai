import path from "node:path";

import { defineConfig } from "@playwright/test";

const VENV_BIN = path.resolve(__dirname, "../../.venv/bin");
const E2E_DATABASE_URL = "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind_e2e";
const REDIS_URL = "redis://localhost:6380/0";
const API_URL = "http://localhost:8010";
const WEB_URL = "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }]] : "list",
  use: {
    baseURL: WEB_URL,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${VENV_BIN}/uvicorn codemind_api.main:app --port 8010`,
      cwd: "../api",
      url: `${API_URL}/healthz`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        // Force Mock providers regardless of what's in apps/api/.env — the
        // E2E suite must never call a real external API.
        ANTHROPIC_API_KEY: "",
        GITHUB_PAT: "",
        GITHUB_TARGET_OWNER: "",
        GITHUB_TARGET_REPO: "",
        DATABASE_URL: E2E_DATABASE_URL,
        REDIS_URL,
      },
    },
    {
      command: "npm run dev",
      url: WEB_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        NEXT_PUBLIC_API_URL: API_URL,
      },
    },
    {
      command: `${VENV_BIN}/arq codemind_worker.settings.WorkerSettings`,
      cwd: "../worker",
      // arq has no HTTP endpoint to poll — wait for its actual startup log
      // line instead (confirmed via arq's source: worker.py logs this via a
      // stderr-attached logger on startup).
      wait: { stderr: /Starting worker for \d+ functions/ },
      stderr: "pipe",
      gracefulShutdown: { signal: "SIGTERM", timeout: 3_000 },
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        DATABASE_URL: E2E_DATABASE_URL,
        REDIS_URL,
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
