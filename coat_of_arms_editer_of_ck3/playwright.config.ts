import { defineConfig } from '@playwright/test'

const runningInCi = Boolean(process.env.CI)
const testingProductionBuild = process.env.COA_E2E_USE_PREVIEW === 'true'

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    locale: 'zh-CN',
    browserName: 'chromium',
    channel: runningInCi ? undefined : 'msedge',
    headless: true,
    launchOptions: {
      args: runningInCi
        ? ['--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader', '--use-angle=swiftshader']
        : [],
    },
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
