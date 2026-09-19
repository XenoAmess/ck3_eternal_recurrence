#!/usr/bin/env node
/** Record a readable, full-length coat-of-arms editor demonstration for r9. */

import { createHash } from 'node:crypto'
import { mkdir, rename, stat, writeFile, readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from '@playwright/test'

const outputDirectory = resolve(process.argv[2] ?? '../artifacts/project-causality/coa-r9')
const productionUrl = 'https://xenoamess.github.io/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/'
await mkdir(outputDirectory, { recursive: true })

const browser = await chromium.launch({ channel: 'msedge', headless: true })
const context = await browser.newContext({
  viewport: { width: 2560, height: 1440 },
  locale: 'zh-CN',
  permissions: ['clipboard-read', 'clipboard-write'],
  recordVideo: { dir: outputDirectory, size: { width: 2560, height: 1440 } },
})
const page = await context.newPage()
const nonGetRequests = []
page.on('request', (request) => {
  if (request.method() !== 'GET') nonGetRequests.push(`${request.method()} ${request.url()}`)
})

async function hold(milliseconds) {
  await page.waitForTimeout(milliseconds)
}

async function scrollTo(locator, holdMilliseconds = 3500) {
  await locator.scrollIntoViewIfNeeded()
  await hold(holdMilliseconds)
}

let video
try {
  await page.goto(productionUrl, { waitUntil: 'networkidle', timeout: 120_000 })
  await page.getByRole('heading', { name: '家徽工坊' }).waitFor({ state: 'visible' })
  video = page.video()
  await hold(4500)

  const workspace = page.locator('.workspace')
  await scrollTo(workspace, 3500)
  await page.getByRole('button', { name: '载入实机样例' }).click()
  await hold(4000)
  await page.getByRole('button', { name: '解析并载入' }).click()
  await page.getByText('没有解析诊断', { exact: true }).waitFor({ state: 'visible' })
  await page.locator('.shield img').waitFor({ state: 'visible' })
  await hold(7000)

  await page.screenshot({
    path: resolve(outputDirectory, 'coat-of-arms-editor-r9.png'),
    fullPage: false,
  })

  // Move through the real editing surface at reading speed.  The capture uses
  // the production page itself; no mock overlay or explanatory diagram is
  // substituted for the product.
  const scrollHeight = await page.evaluate(() => document.documentElement.scrollHeight)
  const viewportHeight = 1440
  const stops = [0.28, 0.46, 0.64, 0.82]
  for (const fraction of stops) {
    await page.evaluate(
      ({ y }) => window.scrollTo({ top: y, behavior: 'smooth' }),
      { y: Math.max(0, (scrollHeight - viewportHeight) * fraction) },
    )
    await hold(5500)
  }

  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
  await hold(3500)
  await page.getByRole('button', { name: '复制 CK3 代码' }).click()
  await hold(4500)
  if (nonGetRequests.length) {
    throw new Error(`production capture made non-GET requests: ${nonGetRequests.join(', ')}`)
  }
} finally {
  await context.close()
  await browser.close()
}

if (!video) throw new Error('Playwright did not expose a recorded video')
const recordedPath = await video.path()
const finalVideo = resolve(outputDirectory, 'coat-of-arms-editor-r9.webm')
await rename(recordedPath, finalVideo)

async function sha256(path) {
  return createHash('sha256').update(await readFile(path)).digest('hex').toUpperCase()
}

const screenshot = resolve(outputDirectory, 'coat-of-arms-editor-r9.png')
const videoInfo = await stat(finalVideo)
const screenshotInfo = await stat(screenshot)
const record = {
  format_version: 1,
  kind: 'project_causality_r9_coat_of_arms_production_capture',
  captured_utc: new Date().toISOString(),
  source_url: productionUrl,
  capture_boundary: 'Public static production page; GET requests only; no CK3, MCP, backend, login, upload or publication.',
  viewport: { width: 2560, height: 1440 },
  video: { path: finalVideo, bytes: videoInfo.size, sha256: await sha256(finalVideo) },
  screenshot: { path: screenshot, bytes: screenshotInfo.size, sha256: await sha256(screenshot) },
  non_get_requests: nonGetRequests,
}
await writeFile(
  resolve(outputDirectory, 'coat-of-arms-editor-r9.capture.json'),
  `${JSON.stringify(record, null, 2)}\n`,
  'utf8',
)
console.log(JSON.stringify(record, null, 2))
