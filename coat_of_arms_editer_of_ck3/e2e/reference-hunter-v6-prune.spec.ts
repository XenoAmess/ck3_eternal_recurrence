import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const inputPath = resolve('../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v6-compressed/coat_of_arms.txt')
const targetPath = resolve('../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v4/target.png')
const artifactDirectory = resolve('test-results/reference-hunter-v6-pruned')
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test('reaches an exact leave-one-out fixed point for hunter v6', async ({ page }) => {
  test.setTimeout(10 * 60 * 1000)
  const inputSource = await readFile(inputPath, 'utf8')
  const targetBytes = await readFile(targetPath)
  await page.goto('/')
  const result = await page.evaluate(async ({ source, targetBase64 }) => {
    const dynamicImport = (path: string) => import(/* @vite-ignore */ path)
    const [parserModule, prunerModule, serializerModule, rendererModule, ddsModule, inputModule] = await Promise.all([
      dynamicImport('/src/domain/parser.ts'),
      dynamicImport('/src/domain/coatOfArmsPruner.ts'),
      dynamicImport('/src/domain/serializer.ts'),
      dynamicImport('/src/domain/renderer.ts'),
      dynamicImport('/src/domain/dds.ts'),
      dynamicImport('/src/domain/imageInput.ts'),
    ])
    const parsed = parserModule.parseCoatOfArms(source)
    const errors = parsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error')
    if (errors.length) throw new Error(`hunter compression parse errors: ${JSON.stringify(errors)}`)
    const bytes = Uint8Array.from(atob(targetBase64), (character) => character.charCodeAt(0))
    const targetFile = new File([bytes], 'hunter.png', { type: 'image/png' })
    const target = (await inputModule.decodeFitImageFile(targetFile)).image
    const manifest = await fetch('/asset-packs/ck3-1.19.0.6/manifest.json').then((response) => response.json())
    const loadTexture = async (kind: string, name: string) => {
      const entry = manifest.assets.find((item: { kind: string, name: string }) => (
        item.kind === kind && item.name === name
      ))
      if (!entry) throw new Error(`missing ${kind}/${name}`)
      const buffer = await fetch(`/asset-packs/ck3-1.19.0.6/${entry.url}`)
        .then((response) => response.arrayBuffer())
      return ddsModule.decodeDds(new Uint8Array(buffer))
    }
    const pattern = await loadTexture('pattern', parsed.coatOfArms.pattern)
    const emblemNames = [...new Set(parsed.coatOfArms.coloredEmblems.map(
      (emblem: { texture: string }) => emblem.texture,
    ))] as string[]
    const coloredEmblems = Object.fromEntries(await Promise.all(emblemNames.map(async (name) => (
      [name, await loadTexture('colored_emblem', name)]
    ))))
    const started = performance.now()
    const pruned = prunerModule.pruneRedundantInstances(
      parsed.coatOfArms,
      target,
      pattern,
      coloredEmblems,
      undefined,
      {},
      {
        searchResolution: 96,
        validationResolutions: [230, 512],
        numericLossTolerance: 1e-12,
        allowedVisualDifferenceBytes: 0,
      },
    )
    const elapsedMilliseconds = performance.now() - started
    const outputSource = serializerModule.serializeCoatOfArms(pruned.coatOfArms)
    const reparsed = parserModule.parseCoatOfArms(outputSource)
    const pixelChecks = []
    for (const resolution of [96, 230, 512]) {
      const assets = { pattern, coloredEmblems }
      const before = rendererModule.renderCoatOfArms(parsed.coatOfArms, assets, {}, resolution)
      const after = rendererModule.renderCoatOfArms(pruned.coatOfArms, assets, {}, resolution)
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
    return {
      outputSource,
      receipt: pruned.receipt,
      elapsedMilliseconds,
      parseErrors: reparsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error').length,
      serializeParseExact: serializerModule.serializeCoatOfArms(reparsed.coatOfArms) === outputSource,
      pixelChecks,
    }
  }, { source: inputSource, targetBase64: targetBytes.toString('base64') })

  expect(result.receipt.drawnInstancesBefore).toBe(1008)
  expect(result.receipt.drawnInstancesAfter + result.receipt.removedInstances).toBe(1008)
  expect(result.receipt.finalNecessityEvidence).toHaveLength(result.receipt.drawnInstancesAfter)
  expect(new Set(result.receipt.finalNecessityEvidence.map((item: { instanceId: number }) => item.instanceId)).size)
    .toBe(result.receipt.drawnInstancesAfter)
  expect(result.receipt.finalNecessityEvidence.every((item: { removed: boolean }) => item.removed === false)).toBe(true)
  expect(result.receipt.finalNecessityEvidence.every((item: { measurements: object[] }) => item.measurements.length >= 1)).toBe(true)
  expect(result.receipt.finalNecessityEvidence.every(
    (item: { reason: string }) => item.reason === 'changes-search-pixels',
  )).toBe(true)
  expect(Math.abs(result.receipt.finalMetrics.totalLoss - result.receipt.initialMetrics.totalLoss)).toBeLessThanOrEqual(1e-12)
  expect(Math.abs(result.receipt.finalMetrics.edgeLoss - result.receipt.initialMetrics.edgeLoss)).toBeLessThanOrEqual(1e-12)
  expect(result.parseErrors).toBe(0)
  expect(result.serializeParseExact).toBe(true)
  expect(result.pixelChecks).toEqual([96, 230, 512].map((resolution) => ({
    resolution,
    differingBytes: 0,
    maximumDifference: 0,
  })))

  await mkdir(artifactDirectory, { recursive: true })
  await writeFile(resolve(artifactDirectory, 'coat_of_arms.txt'), result.outputSource, 'utf8')
  const repository = resolve('..')
  const workingTreePatch = execFileSync(
    'git',
    ['diff', '--binary', 'HEAD', '--', 'coat_of_arms_editer_of_ck3'],
    { cwd: repository },
  )
  const report = {
    schema: 'ck3-coa-exact-instance-prune-evidence-v1',
    artifactVersion: 'xenoamess-hunter-v6-pruned',
    predecessor: '../xenoamess-hunter-v6-compressed/',
    generatedAt: new Date().toISOString(),
    sourceRevision: {
      headCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim(),
      workingTreePatchSha256: sha256(workingTreePatch),
    },
    fixedGates: {
      searchResolution: 96,
      validationResolutions: [230, 512],
      numericLossTolerance: 1e-12,
      allowedVisualDifferenceBytes: 0,
      allowedMaximumPixelDifference: 0,
    },
    input: {
      path: '../xenoamess-hunter-v6-compressed/coat_of_arms.txt',
      utf8Bytes: Buffer.byteLength(inputSource, 'utf8'),
      sha256: sha256(inputSource),
      targetSha256: sha256(targetBytes),
    },
    output: {
      utf8Bytes: Buffer.byteLength(result.outputSource, 'utf8'),
      lines: result.outputSource.match(/\n/g)?.length ?? 0,
      sha256: sha256(result.outputSource),
    },
    elapsedMilliseconds: result.elapsedMilliseconds,
    necessitySummary: (() => {
      const measurements = result.receipt.finalNecessityEvidence.map(
        (item: { measurements: Array<{
          differingBytes: number
          maximumByteDifference: number
          colorLossDelta: number
          edgeLossDelta: number
          totalLossDelta: number
        }> }) => item.measurements[0],
      )
      const range = (values: number[]) => ({ minimum: Math.min(...values), maximum: Math.max(...values) })
      return {
        retainedInstancesMeasured: measurements.length,
        reasonCounts: { changesSearchPixels: measurements.length },
        differingBytes: range(measurements.map((item) => item.differingBytes)),
        maximumByteDifference: range(measurements.map((item) => item.maximumByteDifference)),
        colorLossDelta: range(measurements.map((item) => item.colorLossDelta)),
        edgeLossDelta: range(measurements.map((item) => item.edgeLossDelta)),
        totalLossDelta: range(measurements.map((item) => item.totalLossDelta)),
      }
    })(),
    receipt: result.receipt,
    parseErrors: result.parseErrors,
    serializeParseExact: result.serializeParseExact,
    pixelChecks: result.pixelChecks,
  }
  await writeFile(resolve(artifactDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
})
