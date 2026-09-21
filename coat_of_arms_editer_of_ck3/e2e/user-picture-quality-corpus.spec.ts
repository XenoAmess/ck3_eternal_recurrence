import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
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
  v5Budget1024Baseline: { totalLoss: number, edgeLoss: number, relativeImprovement: number }
}

const fixtureRoot = resolve('e2e/fixtures/pictures')
const corpus = JSON.parse(await readFile(resolve(fixtureRoot, 'cases.json'), 'utf8')) as {
  schema: string
  sourceArchive: { name: string, bytes: number, sha256: string }
  cases: PictureCase[]
}
const budget = Number.parseInt(process.env.COA_CORPUS_BUDGET ?? '128', 10)
if (!Number.isSafeInteger(budget) || budget < 1) throw new Error('COA_CORPUS_BUDGET must be a positive safe integer')
const requestedCaseIds = new Set(
  (process.env.COA_CORPUS_CASES ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean),
)
const unknownCaseIds = [...requestedCaseIds].filter(
  (caseId) => !corpus.cases.some((picture) => picture.id === caseId),
)
if (unknownCaseIds.length) throw new Error(`COA_CORPUS_CASES contains unknown ids: ${unknownCaseIds.join(', ')}`)
const selectedCases = requestedCaseIds.size
  ? corpus.cases.filter((picture) => requestedCaseIds.has(picture.id))
  : corpus.cases
const artifactRoot = process.env.COA_CORPUS_ARTIFACT_ROOT
  ? resolve('..', process.env.COA_CORPUS_ARTIFACT_ROOT)
  : resolve('test-results/user-picture-quality-corpus', `budget-${budget}`)
const sha256 = (bytes: Uint8Array | string) => createHash('sha256').update(bytes).digest('hex').toUpperCase()

test.describe.serial(`user picture quality corpus at budget ${budget}`, () => {
  for (const picture of selectedCases) {
    test(`${picture.id}: ${picture.file}`, async ({ page }) => {
      test.setTimeout(budget >= 1_024 ? 15 * 60_000 : 6 * 60_000)
      const inputPath = resolve(fixtureRoot, picture.file)
      const inputBytes = await readFile(inputPath)
      expect(inputBytes.byteLength).toBe(picture.bytes)
      expect(sha256(inputBytes)).toBe(picture.sha256)

      await page.addInitScript(() => {
        Object.defineProperty(navigator, 'clipboard', {
          configurable: true,
          value: {
            writeText: async (text: string) => {
              Object.assign(window, { __coaClipboardPayload: text })
            },
          },
        })
      })
      await page.goto('/')
      await expect(page.getByText(/ck3-1\.19\.0\.6-base-complete/)).toBeVisible({ timeout: 30_000 })
      await page.locator('.fit-budget input').fill(String(budget))
      await page.locator('.image-drop input').setInputFiles({
        name: picture.file,
        mimeType: picture.mimeType,
        buffer: inputBytes,
      })
      const fitStartedAt = Date.now()
      await page.getByRole('button', { name: '开始本地拟合' }).click()
      await expect(page.getByText(/完成 · .*从完整库评估 \d+ 个构图/)).toBeVisible({
        timeout: budget >= 1_024 ? 14 * 60_000 : 5 * 60_000,
      })
      const fitElapsedMilliseconds = Date.now() - fitStartedAt

      const reportElement = page.locator('.fit-report')
      const rawEvidence = await reportElement.getAttribute('data-fit-evidence')
      if (!rawEvidence) throw new Error('missing machine-readable fit evidence')
      const evidence = JSON.parse(rawEvidence)
      expect(evidence.provenance.layerBudget).toBe(budget)
      expect(evidence.provenance.algorithm).toBe('ck3-coa-browser-fit-v10-epsilon-quality-first')
      expect(evidence.provenance.surfaceMaskApplied).toBe(true)
      expect(evidence.provenance.fullAssetFinalization).toMatchObject({
        contract: 'full-dds-epsilon-multiscale-joint-contour-v4',
        searchAssetContract: 'fit-index-rgba32-v2',
        finalAssetContract: 'decoded-exact-dds-mip-v1',
        multiscaleSelection: {
          contract: 'epsilon-q-e0-perceptual-v2-96-230-512-w20-45-35-v1',
          scales: [96, 230, 512],
        },
        jointRefinement: {
          contract: 'exact-dds-fixed-budget-coordinate-replacement-v1',
        },
        contourRefinement: {
          contract: 'epsilon-q-contour-fixed-budget-replacement-v1',
        },
      })
      expect(evidence.provenance.fullAssetFinalization.rescoredCandidates).toBeGreaterThanOrEqual(1)
      expect(evidence.provenance.drawnInstances).toBeLessThanOrEqual(budget)
      if (budget === 1_024) {
        expect(evidence.metrics.totalLoss).toBeLessThanOrEqual(picture.v5Budget1024Baseline.totalLoss + 1e-12)
        expect(evidence.metrics.edgeLoss).toBeLessThanOrEqual(picture.v5Budget1024Baseline.edgeLoss + 1e-12)
        expect(evidence.metrics.relativeImprovement).toBeGreaterThanOrEqual(
          picture.v5Budget1024Baseline.relativeImprovement - 1e-12,
        )
      }

      const candidateCards = page.getByTestId('candidate-comparison').locator('.candidate-card')
      const paretoCandidateCount = await candidateCards.count()
      expect(paretoCandidateCount).toBeGreaterThanOrEqual(1)
      expect(paretoCandidateCount).toBeLessThanOrEqual(3)
      expect(evidence.paretoCandidates).toHaveLength(paretoCandidateCount)
      const paretoCandidates = []
      for (let index = 0; index < paretoCandidateCount; index += 1) {
        const card = candidateCards.nth(index)
        await card.getByRole('button', { name: '复制候选代码' }).click()
        const candidateSource = await page.evaluate(() => (
          (window as typeof window & { __coaClipboardPayload?: string }).__coaClipboardPayload ?? ''
        ))
        const candidateParsed = parseCoatOfArms(candidateSource)
        const candidateErrors = candidateParsed.diagnostics.filter((item) => item.severity === 'error')
        const candidateStats = coatOfArmsDocumentStats(candidateParsed.coatOfArms, candidateSource)
        expect(candidateErrors).toEqual([])
        expect(serializeCoatOfArms(candidateParsed.coatOfArms)).toBe(candidateSource)
        expect(evidence.paretoCandidates[index].stats).toEqual(candidateStats)
        const previewUrl = await card.locator('.candidate-shield-preview').getAttribute('src')
        if (!previewUrl?.startsWith('data:image/png;base64,')) {
          throw new Error(`missing Pareto candidate ${index + 1} preview`)
        }
        paretoCandidates.push({
          index: index + 1,
          source: candidateSource,
          previewBytes: Buffer.from(previewUrl.slice('data:image/png;base64,'.length), 'base64'),
          parseErrors: candidateErrors.length,
          ...evidence.paretoCandidates[index],
        })
      }
      for (const candidate of paretoCandidates) {
        expect(paretoCandidates.some((other) => (
          other !== candidate
          && other.perceptualMetricsV2.totalLoss <= candidate.perceptualMetricsV2.totalLoss
          && other.metrics.totalLoss <= candidate.metrics.totalLoss
          && other.metrics.edgeLoss <= candidate.metrics.edgeLoss
          && other.stats.drawnInstances <= candidate.stats.drawnInstances
          && (
            other.perceptualMetricsV2.totalLoss < candidate.perceptualMetricsV2.totalLoss
            || other.metrics.totalLoss < candidate.metrics.totalLoss
            || other.metrics.edgeLoss < candidate.metrics.edgeLoss
            || other.stats.drawnInstances < candidate.stats.drawnInstances
          )
        ))).toBe(false)
      }

      const fitPreviewUrl = await page.getByTestId('fit-preview').getAttribute('src')
      const editorPreviewUrl = await page.getByTestId('editor-preview').getAttribute('src')
      expect(fitPreviewUrl).toBe(editorPreviewUrl)
      await expect(page.getByTestId('visual-transform-box')).toHaveCount(0)
      const currentCandidatePreview = page.getByTestId('current-candidate-preview')
      await expect(currentCandidatePreview).toHaveAttribute('src', editorPreviewUrl!)
      const previewProjection = await page.evaluate(() => {
        const editor = document.querySelector<HTMLElement>('.shield')!
        const candidate = document.querySelector<HTMLElement>('[data-testid="current-candidate-preview"]')!
        const editorBounds = editor.getBoundingClientRect()
        const candidateBounds = candidate.getBoundingClientRect()
        return {
          editorClipPath: getComputedStyle(editor).clipPath,
          candidateClipPath: getComputedStyle(candidate).clipPath,
          editorAspectRatio: editorBounds.width / editorBounds.height,
          candidateAspectRatio: candidateBounds.width / candidateBounds.height,
        }
      })
      expect(previewProjection.candidateClipPath).toBe(previewProjection.editorClipPath)
      expect(previewProjection.candidateAspectRatio).toBeCloseTo(previewProjection.editorAspectRatio, 2)
      if (!editorPreviewUrl?.startsWith('data:image/png;base64,')) throw new Error('missing canonical preview')
      const previewBytes = Buffer.from(editorPreviewUrl.slice('data:image/png;base64,'.length), 'base64')

      await page.getByRole('button', { name: '复制 CK3 代码' }).click()
      const source = await page.evaluate(() => (
        (window as typeof window & { __coaClipboardPayload?: string }).__coaClipboardPayload ?? ''
      ))
      const parsed = parseCoatOfArms(source)
      const parseErrors = parsed.diagnostics.filter((item) => item.severity === 'error')
      const parsedInstances = parsed.coatOfArms.coloredEmblems.reduce(
        (sum, emblem) => sum + emblem.instances.length,
        0,
      )
      expect(parseErrors).toEqual([])
      expect(parsedInstances).toBe(evidence.provenance.drawnInstances)
      expect(serializeCoatOfArms(parsed.coatOfArms)).toBe(source)

      const caseDirectory = resolve(artifactRoot, picture.id)
      await mkdir(caseDirectory, { recursive: true })
      await writeFile(resolve(caseDirectory, 'coat_of_arms.txt'), source, 'utf8')
      await writeFile(resolve(caseDirectory, 'canonical-preview-230.png'), previewBytes)
      for (const candidate of paretoCandidates) {
        const suffix = String(candidate.index).padStart(2, '0')
        await writeFile(resolve(caseDirectory, `pareto-candidate-${suffix}.txt`), candidate.source, 'utf8')
        await writeFile(resolve(caseDirectory, `pareto-candidate-${suffix}.png`), candidate.previewBytes)
      }
      await page.locator('.image-fit-panel').screenshot({ path: resolve(caseDirectory, 'input-and-fit-report.png') })
      await page.locator('.preview-pane').screenshot({ path: resolve(caseDirectory, 'editor-preview-panel.png') })

      const repository = resolve('..')
      const headCommit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim()
      const patch = execFileSync(
        'git',
        ['diff', '--binary', 'HEAD', '--', 'coat_of_arms_editer_of_ck3'],
        { cwd: repository },
      )
      const report = {
        schema: 'ck3-coa-user-picture-quality-evidence-v1',
        status: 'browser-passed-native-mcp-pending',
        generatedAt: new Date().toISOString(),
        sourceRevision: { headCommit, workingTreePatchSha256: sha256(patch) },
        corpus: {
          schema: corpus.schema,
          sourceArchive: corpus.sourceArchive,
          case: picture,
        },
        configuration: {
          userDrawInstanceBudget: budget,
          randomSeed: null,
          scoringContract: evidence.provenance.scoringContract,
          rendererContract: evidence.provenance.rendererContract,
          surfaceMaskApplied: evidence.provenance.surfaceMaskApplied,
        },
        metrics: evidence.metrics,
        paretoCandidates: paretoCandidates.map((candidate) => ({
          index: candidate.index,
          sourceFile: `pareto-candidate-${String(candidate.index).padStart(2, '0')}.txt`,
          previewFile: `pareto-candidate-${String(candidate.index).padStart(2, '0')}.png`,
          sourceSha256: sha256(candidate.source),
          previewSha256: sha256(candidate.previewBytes),
          parseErrors: candidate.parseErrors,
          metrics: candidate.metrics,
          perceptualMetricsV2: candidate.perceptualMetricsV2,
          reconstructionMode: candidate.reconstructionMode,
          textureNames: candidate.textureNames,
          multiscaleMetrics: candidate.multiscaleMetrics,
          stats: candidate.stats,
        })),
        perceptualMetricsV2: evidence.provenance.perceptualScoringShadow?.selected ?? null,
        fitElapsedMilliseconds,
        v5Budget1024Baseline: picture.v5Budget1024Baseline,
        provenance: evidence.provenance,
        counts: {
          userBudget: budget,
          drawnInstances: evidence.provenance.drawnInstances,
          logicalLayers: evidence.provenance.logicalLayers,
          coloredEmblemBlocks: evidence.provenance.coloredEmblemBlocks,
          utf8Bytes: Buffer.byteLength(source, 'utf8'),
          lines: source ? (source.match(/\n/g)?.length ?? 0) + 1 : 0,
        },
        integrity: {
          sourceSha256: sha256(source),
          canonicalPreviewSha256: sha256(previewBytes),
          fitAndEditorPreviewByteIdentical: true,
          parseErrors: parseErrors.length,
          serializeParseExact: true,
          parsedInstances,
        },
        evidenceLevel: {
          inputToBrowserFitMetrics: 'measured',
          fitPreviewToEditorPreview: 'byte-identical',
          ck3ApplyCopyRoundTrip: 'pending-mcp',
          nativeSpatialPixelComparison: 'pending-mcp-framebuffer-capability',
        },
      }
      await writeFile(resolve(caseDirectory, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
      console.info(JSON.stringify({
        case: picture.id,
        budget,
        fitElapsedMilliseconds,
        metrics: evidence.metrics,
        perceptualMetricsV2: report.perceptualMetricsV2,
        counts: report.counts,
      }))
    })
  }
})
