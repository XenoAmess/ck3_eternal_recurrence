import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from '@playwright/test'

const [, , inputArgument, outputArgument, sizeArgument = '1024'] = process.argv
if (!inputArgument || !outputArgument) {
  throw new Error('usage: node tools/rasterize_svg.mjs <input.svg> <output.png> [size]')
}
const size = Number(sizeArgument)
if (!Number.isSafeInteger(size) || size < 8 || size > 4096) {
  throw new Error('size must be an integer in 8..4096')
}

const source = await readFile(resolve(inputArgument), 'utf8')
const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage({ viewport: { width: size, height: size } })
  await page.setContent(`<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg{display:block;width:${size}px;height:${size}px}</style>${source}`)
  const svg = page.locator('svg')
  if (await svg.count() !== 1) throw new Error('input must contain exactly one root svg')
  await svg.screenshot({ path: resolve(outputArgument), animations: 'disabled' })
} finally {
  await browser.close()
}
