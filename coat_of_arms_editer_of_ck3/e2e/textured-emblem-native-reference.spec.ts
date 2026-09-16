import { expect, test } from '@playwright/test'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const artifactDirectory = resolve(
  '..',
  'docs',
  'coat-of-arms-fit-artifacts',
  'textured-emblem-browser-r31',
)
const assetPackDirectory = resolve('public', 'asset-packs', 'ck3-1.19.0.6')
const source = `coa = {
  pattern = "pattern_solid.dds"
  color1 = rgb { 64 128 192 }
  color2 = white
  color3 = black

  textured_emblem = {
    texture = "_default.dds"
  }
}
`

const sha256 = (value: Buffer | string) => createHash('sha256').update(value).digest('hex').toUpperCase()

test('freezes the exact-pack textured emblem preview for calibrated native comparison', async ({ page }) => {
  const nonGetRequests: string[] = []
  page.on('request', (request) => {
    if (request.method() !== 'GET') nonGetRequests.push(request.url())
  })

  await page.goto('/')
  await expect(page.getByText(/ck3-1\.19\.0\.6/).first()).toBeVisible({ timeout: 20_000 })
  await page.locator('.code-input textarea').fill(source)
  await page.getByRole('button', { name: '解析并载入' }).click()
  await expect(page.locator('.preview-caption')).toContainText('1 个受限纹理层')
  const preview = page.locator('img.shader-preview')
  await expect(preview).toBeVisible()
  const dimensions = await preview.evaluate(async (element) => {
    const image = element as HTMLImageElement
    await image.decode()
    return [image.naturalWidth, image.naturalHeight]
  })
  expect(dimensions).toEqual([230, 230])
  const previewDataUrl = await preview.getAttribute('src')
  if (!previewDataUrl?.startsWith('data:image/png;base64,')) {
    throw new Error('missing exact-pack textured emblem PNG preview')
  }

  await mkdir(artifactDirectory, { recursive: true })
  const previewBytes = Buffer.from(
    previewDataUrl.slice('data:image/png;base64,'.length),
    'base64',
  )
  await writeFile(resolve(artifactDirectory, 'coat_of_arms.txt'), source, 'ascii')
  await writeFile(resolve(artifactDirectory, 'canonical-preview-230.png'), previewBytes)

  const manifestBytes = await readFile(resolve(assetPackDirectory, 'manifest.json'))
  const manifest = JSON.parse(manifestBytes.toString('utf8')) as {
    pack_id: string
    ck3_build: string
    source_manifest_sha256: string
    assets: Array<{
      kind: string
      name: string
      url: string
      asset_sha256: string
    }>
  }
  const selectedAssets = await Promise.all([
    ['pattern', 'pattern_solid.dds'],
    ['textured_emblem', '_default.dds'],
    ['surface_mask', 'coa_mask_texture.dds'],
  ].map(async ([kind, name]) => {
    const entry = manifest.assets.find((asset) => asset.kind === kind && asset.name === name)
    if (!entry) throw new Error(`exact asset pack is missing ${kind}/${name}`)
    const bytes = await readFile(resolve(assetPackDirectory, entry.url))
    expect(sha256(bytes)).toBe(entry.asset_sha256.toUpperCase())
    return {
      kind,
      name,
      bytes: bytes.length,
      sha256: sha256(bytes),
    }
  }))
  const expectedManifestSha256 = (
    await readFile(resolve(assetPackDirectory, 'manifest.sha256'), 'utf8')
  ).trim().split(/\s+/)[0].toUpperCase()
  const repository = resolve('..')
  const headCommit = execFileSync('git', ['rev-parse', 'HEAD'], {
    cwd: repository,
    encoding: 'utf8',
  }).trim()
  const workingTreePatch = execFileSync(
    'git',
    [
      'diff',
      '--binary',
      'HEAD',
      '--',
      'coat_of_arms_editer_of_ck3',
      'ck3_autonomous_player/native_bridge/research/run_frontend_gui_route_v1_live_acceptance.py',
    ],
    { cwd: repository },
  )
  const report = {
    schema: 'ck3-coa-textured-emblem-browser-reference-v1',
    artifactVersion: 'textured-emblem-browser-r31',
    status: 'browser-reference-passed-native-pixel-pending',
    generatedAt: new Date().toISOString(),
    sourceRevision: {
      headCommit,
      workingTreePatchSha256: sha256(workingTreePatch),
    },
    source: {
      file: 'coat_of_arms.txt',
      asciiBytes: Buffer.byteLength(source, 'ascii'),
      sha256: sha256(source),
      structure: {
        logicalLayers: 0,
        coloredEmblemBlocks: 0,
        texturedEmblemBlocks: 1,
        drawnInstances: 0,
      },
    },
    reference: {
      file: 'canonical-preview-230.png',
      dimensions,
      pngBytes: previewBytes.length,
      sha256: sha256(previewBytes),
      rendererContract: 'exact-1.19.0.6-browser-cpu-renderer-v1',
      surfaceMaskApplied: true,
      colorSpace: 'browser-srgb-byte-domain',
    },
    assetPack: {
      packId: manifest.pack_id,
      ck3Build: manifest.ck3_build,
      manifestSha256: sha256(manifestBytes),
      expectedManifestSha256,
      manifestHashMatchesReceipt: sha256(manifestBytes) === expectedManifestSha256,
      sourceManifestSha256: manifest.source_manifest_sha256,
      selectedAssets,
    },
    nativeComparisonContract: {
      route: 'calibrated-framebuffer-v3',
      calibration: 'reference-independent-red-green-surface-plus-nine-uv-anchors',
      canonicalResolution: [230, 230],
      thresholdsDeclaredBeforeNativeRun: {
        maximumMeanAbsoluteError: 0.10,
        maximumColorMse: 0.03,
        maximumEdgeLoss: 0.16,
        maximumSpatialMeanAbsoluteError8x8: 0.25,
      },
      copyReapplyThresholdsDeclaredBeforeNativeRun: {
        maximumMeanAbsoluteError: 0.01,
        maximumColorMse: 0.001,
        maximumEdgeLoss: 0.02,
        maximumSpatialMeanAbsoluteError8x8: 0.03,
      },
    },
    privacy: {
      nonGetRequestCount: nonGetRequests.length,
      nonGetRequests,
      userContentUploaded: false,
    },
    evidenceLevel: {
      browserRegression: 'passed',
      transferIntegrity: 'pending-native-run',
      ck3ApplyCopyRoundTrip: 'pending-native-run',
      nativePixelComparison: 'pending-native-run',
    },
  }
  expect(nonGetRequests).toEqual([])
  expect(report.assetPack.manifestHashMatchesReceipt).toBe(true)
  await writeFile(
    resolve(artifactDirectory, 'report.json'),
    `${JSON.stringify(report, null, 2)}\n`,
    'utf8',
  )
})
