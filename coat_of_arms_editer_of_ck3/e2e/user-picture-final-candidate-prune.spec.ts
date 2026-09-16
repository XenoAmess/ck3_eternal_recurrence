import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { gzipSync } from 'node:zlib'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'
import { coatOfArmsDocumentStats } from '../src/domain/documentStats'
import { parseCoatOfArms } from '../src/domain/parser'
import { serializeCoatOfArms } from '../src/domain/serializer'

interface PictureCase {
  id: string
  file: string
  mimeType: string
  bytes: number
  width: number
  height: number
  sha256: string
}

interface SourceCandidate {
  index: number
  sourceFile: string
  metrics: { colorLoss: number, edgeLoss: number, totalLoss: number }
  stats: { drawnInstances: number }
}

const enabled = process.env.COA_RUN_FINAL_CANDIDATE_PRUNE === 'true'
const fixtureRoot = resolve('e2e/fixtures/pictures')
const sourceRoot = resolve('../docs/coat-of-arms-fit-artifacts/user-picture-corpus-v14-pareto-budget-1024')
const artifactRoot = process.env.COA_PRUNE_ARTIFACT_ROOT
  ? resolve('..', process.env.COA_PRUNE_ARTIFACT_ROOT)
  : resolve('test-results/user-picture-final-candidate-prune')
const corpus = JSON.parse(await readFile(resolve(fixtureRoot, 'cases.json'), 'utf8')) as {
  schema: string
  sourceArchive: { name: string, bytes: number, sha256: string }
  cases: PictureCase[]
}
const requestedCaseIds = new Set(
  (process.env.COA_PRUNE_CASES ?? '').split(',').map((value) => value.trim()).filter(Boolean),
)
const requestedCandidateIndexes = new Set(
  (process.env.COA_PRUNE_CANDIDATES ?? '').split(',').map((value) => value.trim()).filter(Boolean)
    .map((value) => Number.parseInt(value, 10)),
)
const selectedCases = requestedCaseIds.size
  ? corpus.cases.filter((picture) => requestedCaseIds.has(picture.id))
  : corpus.cases
const sourceReports = new Map(await Promise.all(selectedCases.map(async (picture) => ([
  picture.id,
  JSON.parse(await readFile(resolve(sourceRoot, picture.id, 'report.json'), 'utf8')) as {
    paretoCandidates: SourceCandidate[]
  },
] as const))))
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test.describe('zero-regression fixed-point prune for final user-picture candidates', () => {
  test.describe.configure({ mode: 'parallel' })
  test.skip(!enabled, 'Set COA_RUN_FINAL_CANDIDATE_PRUNE=true to generate immutable evidence')

  for (const picture of selectedCases) {
    const sourceReport = sourceReports.get(picture.id)!
    const candidates = requestedCandidateIndexes.size
      ? sourceReport.paretoCandidates.filter((candidate) => requestedCandidateIndexes.has(candidate.index))
      : sourceReport.paretoCandidates

    for (const candidate of candidates) {
      test(`${picture.id} candidate ${candidate.index}`, async ({ page }) => {
        test.setTimeout(10 * 60_000)
        const sourcePath = resolve(sourceRoot, picture.id, candidate.sourceFile)
        const inputPath = resolve(fixtureRoot, picture.file)
        const [inputSource, inputBytes] = await Promise.all([
          readFile(sourcePath, 'utf8'),
          readFile(inputPath),
        ])
        expect(sha256(inputBytes)).toBe(picture.sha256)

        await page.goto('/')
        const result = await page.evaluate(async ({ source, targetBase64, targetName, targetMimeType }) => {
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
          if (errors.length) throw new Error(`candidate parse errors: ${JSON.stringify(errors)}`)
          const bytes = Uint8Array.from(atob(targetBase64), (character) => character.charCodeAt(0))
          const targetFile = new File([bytes], targetName, { type: targetMimeType })
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
          const surfaceMask = await loadTexture('surface_mask', 'coa_mask_texture.dds')
          const started = performance.now()
          const pruned = prunerModule.pruneRedundantInstances(
            parsed.coatOfArms,
            target,
            pattern,
            coloredEmblems,
            surfaceMask,
            manifest.named_colors,
            {
              mode: 'metric-pareto',
              searchResolution: 96,
              validationResolutions: [230, 512],
              numericLossTolerance: 1e-12,
              allowedVisualDifferenceBytes: 0,
              allowedCumulativeTotalLossIncrease: 0,
              allowedCumulativeEdgeLossIncrease: 0,
            },
          )
          const elapsedMilliseconds = performance.now() - started
          const outputSource = serializerModule.serializeCoatOfArms(pruned.coatOfArms)
          const reparsed = parserModule.parseCoatOfArms(outputSource)
          const assets = { pattern, coloredEmblems, surfaceMask }
          const pixelChecks = []
          let previewBase64 = ''
          for (const resolution of [96, 230, 512]) {
            const before = rendererModule.renderCoatOfArms(parsed.coatOfArms, assets, manifest.named_colors, resolution)
            const after = rendererModule.renderCoatOfArms(pruned.coatOfArms, assets, manifest.named_colors, resolution)
            if (!before || !after) throw new Error(`render unavailable at ${resolution}px`)
            let differingBytes = 0
            let maximumDifference = 0
            for (let index = 0; index < before.pixels.length; index += 1) {
              const difference = Math.abs(before.pixels[index] - after.pixels[index])
              if (difference > 0) differingBytes += 1
              maximumDifference = Math.max(maximumDifference, difference)
            }
            pixelChecks.push({ resolution, differingBytes, maximumDifference })
            if (resolution === 512) {
              const canvas = document.createElement('canvas')
              canvas.width = after.width
              canvas.height = after.height
              const context = canvas.getContext('2d')
              if (!context) throw new Error('2D canvas unavailable')
              context.putImageData(new ImageData(after.pixels, after.width, after.height), 0, 0)
              previewBase64 = canvas.toDataURL('image/png').slice('data:image/png;base64,'.length)
            }
          }
          return {
            outputSource,
            receipt: pruned.receipt,
            elapsedMilliseconds,
            parseErrors: reparsed.diagnostics.filter((item: { severity: string }) => item.severity === 'error').length,
            serializeParseExact: serializerModule.serializeCoatOfArms(reparsed.coatOfArms) === outputSource,
            pixelChecks,
            previewBase64,
            assetPack: {
              packId: manifest.pack_id,
              build: manifest.ck3_build,
              sourceManifestSha256: manifest.source_manifest_sha256,
            },
          }
        }, {
          source: inputSource,
          targetBase64: inputBytes.toString('base64'),
          targetName: picture.file,
          targetMimeType: picture.mimeType,
        })

        expect(result.receipt.contract).toBe('metric-pareto-leave-one-out-fixed-point-v1')
        expect(result.receipt.mode).toBe('metric-pareto')
        expect(result.receipt.drawnInstancesBefore).toBe(candidate.stats.drawnInstances)
        expect(result.receipt.drawnInstancesAfter + result.receipt.removedInstances)
          .toBe(result.receipt.drawnInstancesBefore)
        expect(result.receipt.finalNecessityEvidence).toHaveLength(result.receipt.drawnInstancesAfter)
        expect(result.receipt.finalNecessityEvidence.every((item: { removed: boolean }) => !item.removed)).toBe(true)
        expect(result.receipt.resolutionMetrics.every((item: {
          initial: { totalLoss: number, edgeLoss: number }
          final: { totalLoss: number, edgeLoss: number }
        }) => (
          item.final.totalLoss <= item.initial.totalLoss + 1e-12
          && item.final.edgeLoss <= item.initial.edgeLoss + 1e-12
        ))).toBe(true)
        expect(result.receipt.initialMetrics.totalLoss).toBeCloseTo(candidate.metrics.totalLoss, 12)
        expect(result.receipt.initialMetrics.edgeLoss).toBeCloseTo(candidate.metrics.edgeLoss, 12)
        expect(result.parseErrors).toBe(0)
        expect(result.serializeParseExact).toBe(true)

        const parsedOutput = parseCoatOfArms(result.outputSource)
        const outputStats = coatOfArmsDocumentStats(parsedOutput.coatOfArms, result.outputSource)
        expect(outputStats.drawnInstances).toBe(result.receipt.drawnInstancesAfter)
        expect(serializeCoatOfArms(parsedOutput.coatOfArms)).toBe(result.outputSource)
        const previewBytes = Buffer.from(result.previewBase64, 'base64')
        const receiptBytes = Buffer.from(`${JSON.stringify(result.receipt, null, 2)}\n`, 'utf8')
        const compressedReceipt = gzipSync(receiptBytes, { level: 9 })
        const suffix = String(candidate.index).padStart(2, '0')
        const candidateDirectory = resolve(artifactRoot, picture.id, `candidate-${suffix}`)
        await mkdir(candidateDirectory, { recursive: true })
        await Promise.all([
          writeFile(resolve(candidateDirectory, 'coat_of_arms.txt'), result.outputSource, 'utf8'),
          writeFile(resolve(candidateDirectory, 'preview-512.png'), previewBytes),
          writeFile(resolve(candidateDirectory, 'necessity-receipt.json.gz'), compressedReceipt),
        ])
        const repository = resolve('..')
        const patch = execFileSync('git', ['diff', '--binary', 'HEAD', '--', 'coat_of_arms_editer_of_ck3'], {
          cwd: repository,
        })
        const reasonCounts = result.receipt.finalNecessityEvidence.reduce(
          (counts: Record<string, number>, item: { reason: string }) => ({
            ...counts,
            [item.reason]: (counts[item.reason] ?? 0) + 1,
          }),
          {},
        )
        const report = {
          schema: 'ck3-coa-user-picture-final-candidate-prune-v1',
          status: 'browser-passed-native-mcp-pending',
          generatedAt: new Date().toISOString(),
          predecessor: `../../user-picture-corpus-v14-pareto-budget-1024/${picture.id}/${candidate.sourceFile}`,
          sourceRevision: {
            headCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim(),
            workingTreePatchSha256: sha256(patch),
          },
          input: {
            case: picture,
            sourceUtf8Bytes: Buffer.byteLength(inputSource, 'utf8'),
            sourceSha256: sha256(inputSource),
            targetSha256: sha256(inputBytes),
          },
          assetPack: result.assetPack,
          fixedGates: {
            scoringContract: 'alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1',
            rendererContract: 'cpu-rgba8-trilinear-dds-mip-pixel-center-native-clockwise-depth-descending-v4',
            searchResolution: 96,
            validationResolutions: [230, 512],
            numericLossTolerance: 1e-12,
            allowedCumulativeTotalLossIncrease: 0,
            allowedCumulativeEdgeLossIncrease: 0,
          },
          elapsedMilliseconds: result.elapsedMilliseconds,
          counts: {
            before: candidate.stats.drawnInstances,
            after: outputStats.drawnInstances,
            removed: result.receipt.removedInstances,
            logicalLayersAfter: outputStats.logicalLayers,
            coloredEmblemBlocksAfter: outputStats.coloredEmblemBlocks,
            utf8BytesAfter: outputStats.utf8Bytes,
            linesAfter: outputStats.lines,
          },
          metrics: result.receipt.resolutionMetrics,
          necessity: {
            contract: result.receipt.contract,
            fixedPointPasses: result.receipt.fixedPointPasses,
            evaluatedCandidates: result.receipt.evaluatedCandidates,
            retainedInstancesMeasured: result.receipt.finalNecessityEvidence.length,
            reasonCounts,
            completeReceiptFile: 'necessity-receipt.json.gz',
            completeReceiptUtf8Bytes: receiptBytes.byteLength,
            completeReceiptGzipBytes: compressedReceipt.byteLength,
            completeReceiptSha256: sha256(receiptBytes),
            completeReceiptGzipSha256: sha256(compressedReceipt),
          },
          output: {
            sourceFile: 'coat_of_arms.txt',
            sourceSha256: sha256(result.outputSource),
            previewFile: 'preview-512.png',
            previewSha256: sha256(previewBytes),
            parseErrors: result.parseErrors,
            serializeParseExact: result.serializeParseExact,
            pixelChecks: result.pixelChecks,
          },
          evidenceLevel: {
            browserFixedPointPrune: 'passed',
            ck3ApplyCopyRoundTrip: 'pending-mcp',
            nativeSpatialPixelComparison: 'pending-mcp',
          },
        }
        await writeFile(resolve(candidateDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
        console.info(JSON.stringify({
          case: picture.id,
          candidate: candidate.index,
          elapsedMilliseconds: result.elapsedMilliseconds,
          counts: report.counts,
        }))
      })
    }
  }
})
