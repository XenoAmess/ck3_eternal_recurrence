import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const inputPath = resolve('../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v4/coat_of_arms.txt')
const artifactDirectory = resolve('test-results/reference-hunter-compression')
const minimumByteReductionFraction = 0.10
const minimumBlockReductionFraction = 0.10
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test('safely compresses hunter v4 adjacent equal-style blocks', async ({ page }) => {
  test.setTimeout(2 * 60 * 1000)
  const inputSource = await readFile(inputPath, 'utf8')
  await page.goto('/')
  const result = await page.evaluate(async ({ source }) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [parserModule, optimizerModule, serializerModule, rendererModule, ddsModule] = await Promise.all([
      dynamicImport('/src/domain/parser.ts'),
      dynamicImport('/src/domain/coatOfArmsOptimizer.ts'),
      dynamicImport('/src/domain/serializer.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/dds.ts'),
    ])
    const parsed = parserModule.parseCoatOfArms(source)
    const errors = parsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error')
    if (errors.length) throw new Error(`hunter v4 parse errors: ${JSON.stringify(errors)}`)
    const compressed = optimizerModule.structurallyCompressCoatOfArms(parsed.coatOfArms)
    const compressedSource = serializerModule.serializeCoatOfArms(compressed.coatOfArms)
    const reparsed = parserModule.parseCoatOfArms(compressedSource)
    const reserialized = serializerModule.serializeCoatOfArms(reparsed.coatOfArms)
    const manifest = await fetch('/asset-packs/ck3-1.19.0.6/manifest.json').then((response) => response.json())
    const loadTexture = async (kind: string, name: string) => {
      const entry = manifest.assets.find((item: { kind: string, name: string }) => (
        item.kind === kind && item.name === name
      ))
      if (!entry) throw new Error(`missing ${kind}/${name}`)
      const bytes = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
        .then((response) => response.arrayBuffer())
      return ddsModule.decodeDds(new Uint8Array(bytes))
    }
    const pattern = await loadTexture('pattern', parsed.coatOfArms.pattern)
    const emblemNames = [...new Set(parsed.coatOfArms.coloredEmblems.map(
      (emblem: { texture: string }) => emblem.texture,
    ))] as string[]
    const coloredEmblems = Object.fromEntries(await Promise.all(emblemNames.map(async (name) => (
      [name, await loadTexture('colored_emblem', name)]
    ))))
    const pixelChecks = []
    for (const resolution of [96, 230, 512]) {
      const assets = { pattern, coloredEmblems }
      const before = rendererModule.renderCoatOfArms(parsed.coatOfArms, assets, {}, resolution)
      const after = rendererModule.renderCoatOfArms(compressed.coatOfArms, assets, {}, resolution)
      if (!before || !after) throw new Error(`render unavailable at ${resolution}px`)
      let differingBytes = 0
      let maximumDifference = 0
      for (let index = 0; index < before.pixels.length; index += 1) {
        const difference = Math.abs(before.pixels[index] - after.pixels[index])
        if (difference > 0) differingBytes += 1
        maximumDifference = Math.max(maximumDifference, difference)
      }
      pixelChecks.push({ resolution, differingBytes, maximumDifference })
    }
    const flatten = (coatOfArms: {
      coloredEmblems: Array<{
        texture: string
        colors: string[]
        mask: number[]
        instances: object[]
      }>
    }) => coatOfArms.coloredEmblems.flatMap((emblem) => emblem.instances.map((instance) => ({
      texture: emblem.texture,
      colors: emblem.colors,
      mask: emblem.mask,
      instance,
    })))
    return {
      receipt: compressed.receipt,
      compressedSource,
      parseErrors: reparsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error').length,
      serializeParseExact: reserialized === compressedSource,
      flattenedSequenceExact: JSON.stringify(flatten(parsed.coatOfArms))
        === JSON.stringify(flatten(compressed.coatOfArms)),
      pixelChecks,
    }
  }, { source: inputSource })

  const byteReductionFraction = 1 - result.receipt.utf8BytesAfter / result.receipt.utf8BytesBefore
  const blockReductionFraction = 1
    - result.receipt.coloredEmblemBlocksAfter / result.receipt.coloredEmblemBlocksBefore
  expect(result.receipt.drawnInstancesBefore).toBe(1000)
  expect(result.receipt.drawnInstancesAfter).toBe(1000)
  expect(byteReductionFraction).toBeGreaterThanOrEqual(minimumByteReductionFraction)
  expect(blockReductionFraction).toBeGreaterThanOrEqual(minimumBlockReductionFraction)
  expect(result.parseErrors).toBe(0)
  expect(result.serializeParseExact).toBe(true)
  expect(result.flattenedSequenceExact).toBe(true)
  expect(result.pixelChecks).toEqual([96, 230, 512].map((resolution) => ({
    resolution,
    differingBytes: 0,
    maximumDifference: 0,
  })))

  await mkdir(artifactDirectory, { recursive: true })
  await writeFile(resolve(artifactDirectory, 'coat_of_arms.txt'), result.compressedSource, 'utf8')
  const repository = resolve('..')
  const workingTreePatch = execFileSync(
    'git',
    ['diff', '--binary', 'HEAD', '--', 'coat_of_arms_editer_of_ck3'],
    { cwd: repository },
  )
  const report = {
    schema: 'ck3-coa-structural-compression-evidence-v1',
    artifactVersion: 'xenoamess-hunter-v4-compressed',
    predecessor: '../xenoamess-hunter-v4/',
    generatedAt: new Date().toISOString(),
    sourceRevision: {
      headCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim(),
      workingTreePatchSha256: sha256(workingTreePatch),
    },
    fixedGates: {
      minimumByteReductionFraction,
      minimumBlockReductionFraction,
      allowedPixelDifferenceBytes: 0,
      allowedMaximumPixelDifference: 0,
    },
    input: {
      path: '../xenoamess-hunter-v4/coat_of_arms.txt',
      utf8Bytes: Buffer.byteLength(inputSource, 'utf8'),
      sha256: sha256(inputSource),
    },
    output: {
      utf8Bytes: Buffer.byteLength(result.compressedSource, 'utf8'),
      sha256: sha256(result.compressedSource),
    },
    receipt: result.receipt,
    byteReductionFraction,
    blockReductionFraction,
    parseErrors: result.parseErrors,
    serializeParseExact: result.serializeParseExact,
    flattenedSequenceExact: result.flattenedSequenceExact,
    pixelChecks: result.pixelChecks,
  }
  await writeFile(resolve(artifactDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
})
