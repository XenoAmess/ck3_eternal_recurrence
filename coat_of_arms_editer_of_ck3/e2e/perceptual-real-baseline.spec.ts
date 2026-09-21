import { createHash } from 'node:crypto'
import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

interface PictureCase {
  id: string
  file: string
  mimeType: string
  bytes: number
  sha256: string
}

const fixtureRoot = resolve('e2e/fixtures/pictures')
const baselineRoot = resolve('../docs/coat-of-arms-fit-artifacts/user-picture-corpus-v14-pareto-budget-1024')
const artifactPath = process.env.COA_PERCEPTUAL_REAL_ARTIFACT
  ? resolve('..', process.env.COA_PERCEPTUAL_REAL_ARTIFACT)
  : undefined
const corpusPath = resolve(fixtureRoot, 'cases.json')
const metricPath = resolve('src/domain/perceptualFitMetrics.ts')
const manifestPath = resolve('public/asset-packs/ck3-1.19.0.6/manifest.json')
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

const corpusBytes = await readFile(corpusPath)
const corpus = JSON.parse(corpusBytes.toString('utf8')) as { cases: PictureCase[] }

test('records deterministic perceptual-v2 shadow scores for all seven real baselines', async ({ page }) => {
  test.setTimeout(5 * 60_000)
  const cases = await Promise.all(corpus.cases.map(async (picture) => {
    const report = JSON.parse(await readFile(resolve(baselineRoot, picture.id, 'report.json'), 'utf8')) as {
      paretoCandidates: Array<{ index: number, sourceFile: string, sourceSha256: string }>
    }
    const primary = report.paretoCandidates.find((candidate) => candidate.index === 1)
    if (!primary) throw new Error(`${picture.id} has no primary Pareto candidate`)
    const [source, inputBytes] = await Promise.all([
      readFile(resolve(baselineRoot, picture.id, primary.sourceFile), 'utf8'),
      readFile(resolve(fixtureRoot, picture.file)),
    ])
    expect(sha256(source)).toBe(primary.sourceSha256)
    expect(sha256(inputBytes)).toBe(picture.sha256)
    expect(inputBytes.byteLength).toBe(picture.bytes)
    return {
      ...picture,
      source,
      sourceSha256: primary.sourceSha256,
      inputBase64: inputBytes.toString('base64'),
    }
  }))

  await page.goto('/')
  const result = await page.evaluate(async (inputs) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [parserModule, rendererModule, ddsModule, inputModule, metricModule] = await Promise.all([
      dynamicImport('/src/domain/parser.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/dds.ts'),
      dynamicImport('/src/domain/imageInput.ts'),
      dynamicImport('/src/domain/perceptualFitMetrics.ts'),
    ])
    const manifest = await fetch('/asset-packs/ck3-1.19.0.6/manifest.json').then((response) => response.json())
    const textureCache = new Map<string, unknown>()
    const loadTexture = async (kind: string, name: string) => {
      const key = `${kind}/${name}`
      if (textureCache.has(key)) return textureCache.get(key)
      const entry = manifest.assets.find((item: { kind: string, name: string }) => (
        item.kind === kind && item.name === name
      ))
      if (!entry) throw new Error(`missing exact DDS ${key}`)
      const buffer = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
        .then((response) => response.arrayBuffer())
      const texture = ddsModule.decodeDds(new Uint8Array(buffer))
      textureCache.set(key, texture)
      return texture
    }
    const surfaceMask = await loadTexture('surface_mask', 'coa_mask_texture.dds')
    const rows = []
    for (const input of inputs) {
      const parsed = parserModule.parseCoatOfArms(input.source)
      const errors = parsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error')
      if (errors.length) throw new Error(`${input.id} parse errors: ${JSON.stringify(errors)}`)
      const pattern = await loadTexture('pattern', parsed.coatOfArms.pattern)
      const names = [...new Set(parsed.coatOfArms.coloredEmblems.map(
        (emblem: { texture: string }) => emblem.texture,
      ))] as string[]
      const coloredEmblems = Object.fromEntries(await Promise.all(names.map(async (name) => (
        [name, await loadTexture('colored_emblem', name)]
      ))))
      const bytes = Uint8Array.from(atob(input.inputBase64), (character) => character.charCodeAt(0))
      const file = new File([bytes], input.file, { type: input.mimeType })
      const decodeTargetAt = async (resolution: number) => {
        if (resolution <= 256) return (await inputModule.decodeFitImageFile(file, resolution)).image
        const bitmap = await createImageBitmap(file)
        try {
          const canvas = document.createElement('canvas')
          canvas.width = resolution
          canvas.height = resolution
          const context = canvas.getContext('2d', { willReadFrequently: true })
          if (!context) throw new Error('2D context unavailable')
          context.clearRect(0, 0, resolution, resolution)
          const ratio = Math.min(resolution / bitmap.width, resolution / bitmap.height)
          const width = bitmap.width * ratio
          const height = bitmap.height * ratio
          context.drawImage(bitmap, (resolution - width) / 2, (resolution - height) / 2, width, height)
          return { width: resolution, height: resolution, pixels: context.getImageData(0, 0, resolution, resolution).data }
        } finally {
          bitmap.close()
        }
      }
      const resolutions = []
      for (const resolution of [96, 230, 512]) {
        const target = await decodeTargetAt(resolution)
        const rendered = rendererModule.renderCoatOfArms(
          parsed.coatOfArms,
          { pattern, coloredEmblems, surfaceMask },
          manifest.named_colors ?? {},
          resolution,
        )
        if (!rendered) throw new Error(`${input.id} exact DDS render failed at ${resolution}px`)
        const first = metricModule.measurePerceptualFitMetricsV2(target, rendered)
        const repeated = metricModule.measurePerceptualFitMetricsV2(target, rendered)
        resolutions.push({
          resolution,
          metrics: first,
          deterministicRepeat: JSON.stringify(first) === JSON.stringify(repeated),
        })
      }
      rows.push({
        id: input.id,
        file: input.file,
        inputSha256: input.sha256,
        sourceSha256: input.sourceSha256,
        resolutions,
      })
    }
    return {
      scoringContract: metricModule.PERCEPTUAL_FIT_SCORING_CONTRACT,
      assetPack: {
        packId: manifest.pack_id,
        build: manifest.ck3_build,
        sourceManifestSha256: manifest.source_manifest_sha256,
      },
      rows,
    }
  }, cases)

  expect(result.rows).toHaveLength(7)
  for (const row of result.rows) {
    expect(row.resolutions.map((item) => item.resolution)).toEqual([96, 230, 512])
    expect(row.resolutions.every((item) => item.deterministicRepeat)).toBe(true)
    for (const { metrics } of row.resolutions) {
      expect(Number.isFinite(metrics.totalLoss)).toBe(true)
      expect(metrics.totalLoss).toBeGreaterThanOrEqual(0)
      expect(metrics.structure.targetComponents).toBeGreaterThanOrEqual(0)
      expect(metrics.structure.renderedComponents).toBeGreaterThanOrEqual(0)
    }
  }

  if (artifactPath) {
    const [metricBytes, manifestBytes] = await Promise.all([
      readFile(metricPath),
      readFile(manifestPath),
    ])
    const report = {
      schema: 'ck3-coa-perceptual-real-baseline-shadow-v1',
      status: 'browser-passed-shadow-only',
      predecessor: '../user-picture-corpus-v14-pareto-budget-1024/',
      corpus: {
        casesSha256: sha256(corpusBytes),
        caseCount: corpus.cases.length,
      },
      scoring: {
        contract: result.scoringContract,
        implementationSha256: sha256(metricBytes),
        role: 'shadow-only-no-selection-effect',
      },
      assetPack: {
        ...result.assetPack,
        manifestSha256: sha256(manifestBytes),
      },
      resolutions: [96, 230, 512],
      rows: result.rows,
      gates: {
        expectedCases: 7,
        observedCases: result.rows.length,
        finiteNonNegativeMetrics: true,
        deterministicRepeat: true,
        status: 'passed',
      },
    }
    await writeFile(artifactPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  }
})
