import { defineConfig, devices } from '@playwright/test'

const testingProductionBuild = process.env.COA_E2E_USE_PREVIEW === 'true'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'cross-browser-core.spec.ts',
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  reporter: 'line',
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    locale: 'zh-CN',
    headless: true,
  },
  webServer: {
    command: testingProductionBuild
      ? 'pnpm preview --host 127.0.0.1 --port 4173 --strictPort'
      : 'pnpm dev --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
    timeout: 60_000,
  },
})
