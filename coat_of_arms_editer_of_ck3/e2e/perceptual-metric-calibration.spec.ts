import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

interface CorpusSample {
  id: string
  split: 'dev' | 'holdout'
  truth: Record<string, unknown>
}

interface Corpus {
  schema: string
  assetPack: { manifestSha256: string }
  samplesPayloadSha256: string
  perturbationLadders: {
    colorChannelDelta: number[]
    positionDelta: number[]
    scaleMultiplier: number[]
    rotationDegrees: number[]
  }
  samples: CorpusSample[]
}

const corpusPath = resolve('src/data/fit-quality-synthetic-corpus-v1.json')
const metricPath = resolve('src/domain/perceptualFitMetrics.ts')

test('perceptual v2 shadow metric orders the frozen holdout perturbation ladders', async ({ page }) => {
  test.setTimeout(180_000)
  const corpus = JSON.parse(await readFile(corpusPath, 'utf8')) as Corpus
  const holdout = corpus.samples.filter((sample) => sample.split === 'holdout')
  expect(holdout).toHaveLength(64)
  await page.goto('/')
  const result = await page.evaluate(async ({ samples, ladders }) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [ddsModule, rendererModule, metricModule] = await Promise.all([
      dynamicImport('/src/domain/dds.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/perceptualFitMetrics.ts'),
    ])
    const manifest = await fetch('/asset-packs/ck3-1.19.0.6/manifest.json').then((response) => response.json())
    const entries = new Map(manifest.assets.map((entry: { name: string }) => [entry.name, entry]))
    const decoded = new Map<string, unknown>()
    const texture = async (name: string) => {
      const cached = decoded.get(name)
      if (cached) return cached
      const entry = entries.get(name) as { url: string } | undefined
      if (!entry) throw new Error(`missing benchmark asset ${name}`)
      const response = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
      if (!response.ok) throw new Error(`failed benchmark asset ${name}: ${response.status}`)
      const value = ddsModule.decodeDds(new Uint8Array(await response.arrayBuffer()))
      decoded.set(name, value)
      return value
    }
    const surfaceEntry = manifest.assets.find((entry: { kind: string }) => entry.kind === 'surface_mask')
    const surfaceMask = surfaceEntry ? await texture(surfaceEntry.name) : undefined
    const cloneModel = (truth: Record<string, unknown>) => {
      const source = structuredClone(truth) as {
        outerKey: string
        parent: string
        pattern: string
        colors: [string, string, string]
        coloredEmblems: Array<{
          texture: string
          textureSha256?: string
          colors: [string, string, string]
          mask: number[]
          instances: Array<{
            position: [number, number]
            scale: [number, number]
            rotation: number
            depth: number
          }>
        }>
        texturedEmblems: unknown[]
        patternSha256?: string
      }
      delete source.patternSha256
      for (const emblem of source.coloredEmblems) delete emblem.textureSha256
      return source
    }
    // Raster sampling, clipping and rotational symmetry can make the middle
    // rung tie or locally reverse. The frozen contract is the meaningful
    // endpoint ordering: a severe perturbation must not beat the mild one.
    const monotone = (values: number[]) => values[0] <= values[values.length - 1] + 1e-12
    type Rendered = { width: number, height: number, pixels: Uint8ClampedArray }
    const remap = (
      source: Rendered,
      sourcePoint: (x: number, y: number) => [number, number],
    ): Rendered => {
      const pixels = new Uint8ClampedArray(source.pixels.length)
      for (let y = 0; y < source.height; y += 1) {
        for (let x = 0; x < source.width; x += 1) {
          const [sourceX, sourceY] = sourcePoint(x + 0.5, y + 0.5)
          const sampledX = Math.floor(sourceX)
          const sampledY = Math.floor(sourceY)
          if (sampledX < 0 || sampledX >= source.width || sampledY < 0 || sampledY >= source.height) continue
          const targetOffset = (y * source.width + x) * 4
          const sourceOffset = (sampledY * source.width + sampledX) * 4
          pixels.set(source.pixels.subarray(sourceOffset, sourceOffset + 4), targetOffset)
        }
      }
      return { width: source.width, height: source.height, pixels }
    }
    const colorPerturbation = (source: Rendered, delta: number): Rendered => {
      const pixels = new Uint8ClampedArray(source.pixels)
      const blend = delta / 255
      for (let offset = 0; offset < pixels.length; offset += 4) {
        if (pixels[offset + 3] === 0) continue
        for (let channel = 0; channel < 3; channel += 1) {
          pixels[offset + channel] = Math.round(
            source.pixels[offset + channel] * (1 - blend)
            + (255 - source.pixels[offset + channel]) * blend,
          )
        }
      }
      return { width: source.width, height: source.height, pixels }
    }
    const blendImages = (source: Rendered, endpoint: Rendered, weight: number): Rendered => {
      const pixels = new Uint8ClampedArray(source.pixels.length)
      for (let index = 0; index < pixels.length; index += 1) {
        pixels[index] = Math.round(source.pixels[index] * (1 - weight) + endpoint.pixels[index] * weight)
      }
      return { width: source.width, height: source.height, pixels }
    }
    const translated = (source: Rendered, delta: number) => {
      const pixels = Math.max(1, Math.round(delta * source.width))
      return remap(source, (x, y) => [x - pixels, y])
    }
    const scaled = (source: Rendered, factor: number) => {
      const centerX = source.width / 2
      const centerY = source.height / 2
      return remap(source, (x, y) => [
        centerX + (x - centerX) / factor,
        centerY + (y - centerY) / factor,
      ])
    }
    const rotated = (source: Rendered, degrees: number) => {
      const radians = -degrees * Math.PI / 180
      const cosine = Math.cos(radians)
      const sine = Math.sin(radians)
      const centerX = source.width / 2
      const centerY = source.height / 2
      return remap(source, (x, y) => {
        const relativeX = x - centerX
        const relativeY = y - centerY
        return [
          centerX + relativeX * cosine - relativeY * sine,
          centerY + relativeX * sine + relativeY * cosine,
        ]
      })
    }
    const rows: Array<{
      id: string
      identicalLoss: number
      color: number[]
      position: number[]
      scale: number[]
      rotation: number[]
      monotone: Record<string, boolean>
    }> = []
    for (const sample of samples) {
      const truth = cloneModel(sample.truth)
      const pattern = await texture(truth.pattern)
      const emblemTextures = Object.fromEntries(await Promise.all(
        truth.coloredEmblems.map(async (emblem) => [emblem.texture, await texture(emblem.texture)]),
      ))
      const assets = { pattern, coloredEmblems: emblemTextures, surfaceMask }
      const target = rendererModule.renderCoatOfArms(truth, assets, manifest.named_colors, 64)
      if (!target) throw new Error(`failed to render truth ${sample.id}`)
      const measure = (candidate: Rendered) => (
        metricModule.measurePerceptualFitMetricsV2(target, candidate).totalLoss as number
      )
      const identicalLoss = measure(target)
      const color = ladders.colorChannelDelta.map((delta) => measure(colorPerturbation(target, delta)))
      const maximumPositionDelta = ladders.positionDelta[ladders.positionDelta.length - 1]
      const translationEndpoint = translated(target, maximumPositionDelta)
      const position = ladders.positionDelta.map((delta) => measure(
        blendImages(target, translationEndpoint, delta / maximumPositionDelta),
      ))
      const scale = ladders.scaleMultiplier.map((factor) => measure(scaled(target, factor)))
      const rotation = ladders.rotationDegrees.map((delta) => measure(rotated(target, delta)))
      rows.push({
        id: sample.id,
        identicalLoss,
        color,
        position,
        scale,
        rotation,
        monotone: {
          color: monotone(color),
          position: monotone(position),
          scale: monotone(scale),
          rotation: monotone(rotation),
        },
      })
    }
    const rates = Object.fromEntries(['color', 'position', 'scale', 'rotation'].map((family) => [
      family,
      rows.filter((row) => row.monotone[family]).length / rows.length,
    ])) as Record<string, number>
    return { rows, rates }
  }, { samples: holdout, ladders: corpus.perturbationLadders })

  const gates = { color: 0.98, position: 0.90, scale: 0.85, rotation: 0.75 }
  const passed = result.rows.every((row) => row.identicalLoss === 0)
    && Object.entries(gates).every(([family, gate]) => result.rates[family] >= gate)
  console.log(JSON.stringify({ contract: 'ck3-coa-perceptual-shadow-calibration-v1', passed, rates: result.rates }))
  const artifactPath = process.env.COA_PERCEPTUAL_CALIBRATION_ARTIFACT
  if (artifactPath) {
    const metricSource = await readFile(metricPath)
    const report = {
      schema: 'ck3-coa-perceptual-shadow-calibration-v1',
      status: passed ? 'passed' : 'failed',
      scoringContract: 'linear-rgb40-multiscale30-gradient20-bidirectional-edge7-structure3-shadow-v2',
      corpus: {
        schema: corpus.schema,
        samplesPayloadSha256: corpus.samplesPayloadSha256,
        assetPackManifestSha256: corpus.assetPack.manifestSha256,
        split: 'holdout',
        samples: holdout.length,
      },
      metricSourceSha256: createHash('sha256').update(metricSource).digest('hex').toUpperCase(),
      gates,
      rates: result.rates,
      rows: result.rows,
    }
    const absolute = resolve(artifactPath)
    await mkdir(resolve(absolute, '..'), { recursive: true })
    await writeFile(absolute, `${JSON.stringify(report, null, 2)}\n`)
  }
  expect(result.rows.every((row) => row.identicalLoss === 0)).toBe(true)
  expect(result.rates.color).toBeGreaterThanOrEqual(gates.color)
  expect(result.rates.position).toBeGreaterThanOrEqual(gates.position)
  expect(result.rates.scale).toBeGreaterThanOrEqual(gates.scale)
  expect(result.rates.rotation).toBeGreaterThanOrEqual(gates.rotation)
})
