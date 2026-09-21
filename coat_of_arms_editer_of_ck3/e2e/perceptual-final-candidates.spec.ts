import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
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
const sourceRoot = resolve('../docs/coat-of-arms-fit-artifacts/delta-q-residual-repair-v1/real-budget-1024-v9-final-quality-first')
const baselinePath = resolve('../docs/coat-of-arms-fit-artifacts/delta-q-perceptual-shadow-v1/real-v14-shadow-report.json')
const outputPath = resolve('../docs/coat-of-arms-fit-artifacts/delta-q-final-multires-v1/report.json')
const corpus = JSON.parse(await readFile(resolve(fixtureRoot, 'cases.json'), 'utf8')) as { cases: PictureCase[] }
const baseline = JSON.parse(await readFile(baselinePath, 'utf8')) as {
  rows: Array<{
    id: string
    resolutions: Array<{ resolution: number, metrics: { totalLoss: number } }>
  }>
}
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test('re-scores all seven quality-first winners at 96, 230 and 512px', async ({ page }) => {
  test.setTimeout(10 * 60_000)
  const cases = await Promise.all(corpus.cases.map(async (picture) => {
    const report = JSON.parse(await readFile(resolve(sourceRoot, picture.id, 'report.json'), 'utf8'))
    const [inputBytes, candidates] = await Promise.all([
      readFile(resolve(fixtureRoot, picture.file)),
      Promise.all(report.paretoCandidates.map(async (candidate: {
        index: number
        sourceFile: string
        sourceSha256: string
      }) => ({
        index: candidate.index,
        source: await readFile(resolve(sourceRoot, picture.id, candidate.sourceFile), 'utf8'),
        sourceSha256: candidate.sourceSha256,
      }))),
    ])
    const source = await readFile(resolve(sourceRoot, picture.id, 'coat_of_arms.txt'), 'utf8')
    expect(sha256(source)).toBe(report.integrity.sourceSha256)
    expect(sha256(inputBytes)).toBe(picture.sha256)
    expect(candidates[0].source).toBe(source)
    for (const candidate of candidates) expect(sha256(candidate.source)).toBe(candidate.sourceSha256)
    return {
      ...picture,
      candidates,
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
      const entry = manifest.assets.find((item: { kind: string, name: string }) => item.kind === kind && item.name === name)
      if (!entry) throw new Error(`missing exact DDS ${key}`)
      const buffer = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`).then((response) => response.arrayBuffer())
      const texture = ddsModule.decodeDds(new Uint8Array(buffer))
      textureCache.set(key, texture)
      return texture
    }
    const surfaceMask = await loadTexture('surface_mask', 'coa_mask_texture.dds')
    const rows = []
    for (const input of inputs) {
      const bytes = Uint8Array.from(atob(input.inputBase64), (character) => character.charCodeAt(0))
      const file = new File([bytes], input.file, { type: input.mimeType })
      const bitmap = await createImageBitmap(file)
      const candidates = []
      try {
        for (const candidate of input.candidates) {
          const parsed = parserModule.parseCoatOfArms(candidate.source)
          const errors = parsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error')
          if (errors.length) throw new Error(`${input.id} candidate ${candidate.index} parse errors: ${JSON.stringify(errors)}`)
          const pattern = await loadTexture('pattern', parsed.coatOfArms.pattern)
          const names = [...new Set(parsed.coatOfArms.coloredEmblems.map((emblem: { texture: string }) => emblem.texture))] as string[]
          const coloredEmblems = Object.fromEntries(await Promise.all(names.map(async (name) => (
            [name, await loadTexture('colored_emblem', name)]
          ))))
          const resolutions = []
          for (const resolution of [96, 230, 512]) {
            const canvas = document.createElement('canvas')
            canvas.width = resolution
            canvas.height = resolution
            const context = canvas.getContext('2d', { willReadFrequently: true })
            if (!context) throw new Error('2D context unavailable')
            const ratio = Math.min(resolution / bitmap.width, resolution / bitmap.height)
            const width = bitmap.width * ratio
            const height = bitmap.height * ratio
            context.drawImage(bitmap, (resolution - width) / 2, (resolution - height) / 2, width, height)
            const target = {
              width: resolution,
              height: resolution,
              pixels: context.getImageData(0, 0, resolution, resolution).data,
            }
            const rendered = rendererModule.renderCoatOfArms(
              parsed.coatOfArms,
              { pattern, coloredEmblems, surfaceMask },
              manifest.named_colors ?? {},
              resolution,
            )
            if (!rendered) throw new Error(`${input.id} candidate ${candidate.index} exact DDS render failed at ${resolution}px`)
            const metrics = metricModule.measurePerceptualFitMetricsV2(target, rendered)
            const repeated = metricModule.measurePerceptualFitMetricsV2(target, rendered)
            resolutions.push({
              resolution,
              metrics,
              deterministicRepeat: JSON.stringify(metrics) === JSON.stringify(repeated),
            })
          }
          candidates.push({ index: candidate.index, sourceSha256: candidate.sourceSha256, resolutions })
        }
      } finally {
        bitmap.close()
      }
      rows.push({ id: input.id, inputSha256: input.sha256, candidates })
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

  const baselineById = new Map(baseline.rows.map((row) => [row.id, row]))
  const rows = result.rows.map((row) => {
    const candidates = row.candidates.map((candidate) => ({
      ...candidate,
      resolutions: candidate.resolutions.map((item) => {
      const baselineLoss = baselineById.get(row.id)?.resolutions
        .find((candidate) => candidate.resolution === item.resolution)?.metrics.totalLoss
      if (baselineLoss === undefined || !Number.isFinite(baselineLoss)) {
        throw new Error(`missing v14 ${item.resolution}px baseline for ${row.id}`)
      }
      return {
        ...item,
        baselineLoss,
        relativeImprovement: (baselineLoss - item.metrics.totalLoss) / baselineLoss,
      }
      }),
    }))
    return { ...row, candidates, resolutions: candidates[0].resolutions }
  })
  const improvements96 = rows.map((row) => row.resolutions.find((item) => item.resolution === 96)!.relativeImprovement)
  const sorted96 = [...improvements96].sort((left, right) => left - right)
  const median96 = sorted96[Math.floor(sorted96.length / 2)]
  const worst96 = Math.min(...improvements96)
  const aggregateByResolution = [96, 230, 512].map((resolution) => {
    const selectedImprovements = rows.map((row) => (
      row.resolutions.find((item) => item.resolution === resolution)!.relativeImprovement
    ))
    const oracleImprovements = rows.map((row) => {
      const candidates = row.candidates.map((candidate) => (
        candidate.resolutions.find((item) => item.resolution === resolution)!
      ))
      return Math.max(...candidates.map((item) => item.relativeImprovement))
    })
    const median = (values: number[]) => [...values].sort((left, right) => left - right)[Math.floor(values.length / 2)]
    return {
      resolution,
      selectedMedianRelativeImprovement: median(selectedImprovements),
      selectedWorstRelativeImprovement: Math.min(...selectedImprovements),
      oracleMedianRelativeImprovement: median(oracleImprovements),
      oracleWorstRelativeImprovement: Math.min(...oracleImprovements),
      selectedIsResolutionBestCases: rows.filter((row) => {
        const selected = row.resolutions.find((item) => item.resolution === resolution)!.metrics.totalLoss
        const best = Math.min(...row.candidates.map((candidate) => (
          candidate.resolutions.find((item) => item.resolution === resolution)!.metrics.totalLoss
        )))
        return selected <= best + 1e-12
      }).length,
    }
  })

  expect(rows).toHaveLength(7)
  expect(rows.every((row) => row.candidates.every((candidate) => (
    candidate.resolutions.every((item) => item.deterministicRepeat)
  )))).toBe(true)
  expect(rows.every((row) => row.candidates.every((candidate) => (
    candidate.resolutions.every((item) => Number.isFinite(item.metrics.totalLoss))
  )))).toBe(true)
  expect(median96).toBeGreaterThanOrEqual(0.15)
  expect(worst96).toBeGreaterThanOrEqual(-0.02)
  expect(aggregateByResolution.every((item) => item.selectedWorstRelativeImprovement >= -0.02)).toBe(true)

  const report = {
    schema: 'ck3-coa-delta-q-final-multires-v1',
    status: 'browser-full-dds-passed-native-mcp-pending',
    sourceRoot: '../delta-q-residual-repair-v1/real-budget-1024-v9-final-quality-first',
    baseline: '../delta-q-perceptual-shadow-v1/real-v14-shadow-report.json',
    resolutions: [96, 230, 512],
    scoringContract: result.scoringContract,
    assetPack: result.assetPack,
    rows,
    aggregateByResolution,
    gates: {
      deterministicRepeat: true,
      finiteMetrics: true,
      medianRelativeImprovement96: median96,
      worstRelativeImprovement96: worst96,
      medianGatePassed: median96 >= 0.15,
      worstGatePassed: worst96 >= -0.02,
    },
    evidenceBoundary: {
      ck3ApplyCopyRoundTrip: 'pending-mcp',
      nativeSpatialPixelComparison: 'pending-mcp-framebuffer',
    },
  }
  await mkdir(resolve(outputPath, '..'), { recursive: true })
  await writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
})
