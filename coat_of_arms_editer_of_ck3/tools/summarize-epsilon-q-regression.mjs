import { readFile, readdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const [rootArgument, outputArgument, budgetArgument, baselineArgument] = process.argv.slice(2)
const budget = Number.parseInt(budgetArgument ?? '', 10)
if (!rootArgument || !outputArgument || !Number.isSafeInteger(budget) || budget < 1) {
  throw new Error('usage: node tools/summarize-epsilon-q-regression.mjs <report-root> <output.json> <budget> [delta-multires-report.json]')
}

const scales = [96, 230, 512]
const weights = new Map([[96, 0.20], [230, 0.45], [512, 0.35]])
const median = (values) => {
  if (!values.length) return null
  const sorted = [...values].sort((left, right) => left - right)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
}
const weightedLoss = (lossByScale) => scales.reduce(
  (sum, scale) => sum + lossByScale[scale] * weights.get(scale),
  0,
)

const root = resolve(rootArgument)
const output = resolve(outputArgument)
const caseIds = (await readdir(root, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory() && entry.name.startsWith('picture-'))
  .map((entry) => entry.name)
  .sort()

let historicalBaseline = null
if (baselineArgument) {
  const report = JSON.parse(await readFile(resolve(baselineArgument), 'utf8'))
  historicalBaseline = new Map(report.rows.map((row) => [
    row.id,
    Object.fromEntries(row.resolutions.map((entry) => [entry.resolution, entry.metrics.totalLoss])),
  ]))
}

const rows = []
for (const id of caseIds) {
  const report = JSON.parse(await readFile(resolve(root, id, 'report.json'), 'utf8'))
  const finalization = report.provenance.fullAssetFinalization
  const selection = finalization?.multiscaleSelection
  const currentIncumbentByScale = Object.fromEntries(
    (selection?.incumbentPerScale ?? []).map((entry) => [entry.resolution, entry.v2.totalLoss]),
  )
  const selectedByScale = Object.fromEntries(
    (selection?.selectedPerScale ?? []).map((entry) => [entry.resolution, entry.v2.totalLoss]),
  )
  const historicalByScale = historicalBaseline?.get(id) ?? null
  const baselineByScale = historicalByScale ?? currentIncumbentByScale
  const baselineLoss = scales.every((scale) => Number.isFinite(baselineByScale[scale]))
    ? weightedLoss(baselineByScale)
    : null
  const selectedLoss = scales.every((scale) => Number.isFinite(selectedByScale[scale]))
    ? weightedLoss(selectedByScale)
    : null
  const relativeImprovement = baselineLoss > 1e-12 && selectedLoss !== null
    ? (baselineLoss - selectedLoss) / baselineLoss
    : null
  rows.push({
    id,
    status: report.status,
    algorithm: report.provenance.algorithm,
    finalizationContract: finalization?.contract ?? null,
    baselineKind: historicalByScale ? 'delta-q-v9-historical' : 'same-run-search-incumbent',
    layerBudget: report.configuration.userDrawInstanceBudget,
    drawnInstances: report.counts.drawnInstances,
    utf8Bytes: report.counts.utf8Bytes,
    fitElapsedMilliseconds: report.fitElapsedMilliseconds,
    selectedVariant: selection?.selectedVariant ?? null,
    incumbentLoss: selection?.incumbentLoss ?? null,
    selectedLossAgainstCurrentSearch: selection?.selectedLoss ?? null,
    baselineByScale,
    currentSearchIncumbentByScale: currentIncumbentByScale,
    selectedByScale,
    baselineLoss,
    selectedLoss,
    relativeImprovement,
    scaleNonRegression: scales.every((scale) => (
      Number.isFinite(baselineByScale[scale])
      && Number.isFinite(selectedByScale[scale])
      && selectedByScale[scale] <= baselineByScale[scale] + 1e-12
    )),
    currentSearchScaleNonRegression: scales.every((scale) => (
      Number.isFinite(currentIncumbentByScale[scale])
      && Number.isFinite(selectedByScale[scale])
      && selectedByScale[scale] <= currentIncumbentByScale[scale] + 1e-12
    )),
    jointAcceptedMoves: finalization?.jointRefinement?.acceptedMoves?.length ?? null,
    contourAccepted: finalization?.contourRefinement?.acceptedCandidateAdded ?? null,
    parseErrors: report.integrity.parseErrors,
    serializeParseExact: report.integrity.serializeParseExact,
    fitAndEditorPreviewByteIdentical: report.integrity.fitAndEditorPreviewByteIdentical,
  })
}

const improvements = rows.map((row) => row.relativeImprovement).filter(Number.isFinite)
const target = budget >= 1_024 ? 0.10 : 0.05
const minimumImprovedCases = 5
const hardExample = rows.filter((row) => row.id === 'picture-03' || row.id === 'picture-06')
const evidenceChecks = {
  caseCountMatches: rows.length === 7,
  exactCaseSet: JSON.stringify(caseIds) === JSON.stringify([
    'picture-01', 'picture-02', 'picture-03', 'picture-04',
    'picture-05', 'picture-06', 'picture-07',
  ]),
  budgetMatches: rows.every((row) => row.layerBudget === budget),
  withinLayerBudget: rows.every((row) => row.drawnInstances <= budget),
  algorithmMatches: rows.every((row) => row.algorithm === 'ck3-coa-browser-fit-v14-epsilon-delta-safety-lane'),
  finalizationMatches: rows.every((row) => row.finalizationContract === 'full-dds-epsilon-multiscale-delta-gated-v6'),
  parseSerializePassed: rows.every((row) => row.parseErrors === 0 && row.serializeParseExact),
  previewProjectionPassed: rows.every((row) => row.fitAndEditorPreviewByteIdentical),
  finiteThreeScaleMetrics: rows.every((row) => scales.every((scale) => (
    Number.isFinite(row.baselineByScale[scale]) && Number.isFinite(row.selectedByScale[scale])
  ))),
  currentSearchPreservedAtEveryScale: rows.every((row) => row.currentSearchScaleNonRegression),
}
const qualityTargets = {
  requestedMedianRelativeImprovement: target,
  measuredMedianRelativeImprovement: median(improvements),
  medianTargetMet: (median(improvements) ?? Number.NEGATIVE_INFINITY) >= target,
  requestedImprovedCases: minimumImprovedCases,
  measuredImprovedCases: rows.filter((row) => (row.relativeImprovement ?? 0) > 1e-12).length,
  improvedCasesTargetMet: rows.filter((row) => (row.relativeImprovement ?? 0) > 1e-12).length >= minimumImprovedCases,
  allScalesNonRegressingAgainstBaseline: rows.every((row) => row.scaleNonRegression),
  hardExampleFivePercentMet: budget < 1_024
    ? null
    : hardExample.some((row) => (row.relativeImprovement ?? 0) >= 0.05)
      && hardExample.every((row) => row.scaleNonRegression),
}
const evidencePassed = Object.values(evidenceChecks).every((value) => value === true)
const targetMet = qualityTargets.medianTargetMet
  && qualityTargets.improvedCasesTargetMet
  && qualityTargets.allScalesNonRegressingAgainstBaseline
  && qualityTargets.hardExampleFivePercentMet !== false
const totalFitMilliseconds = rows.reduce((sum, row) => sum + row.fitElapsedMilliseconds, 0)
const summary = {
  schema: 'ck3-coa-epsilon-q-regression-summary-v1',
  status: evidencePassed
    ? targetMet ? 'browser-passed-quality-target-met-native-pending' : 'browser-passed-quality-target-missed-native-pending'
    : 'red',
  root: rootArgument,
  baseline: baselineArgument ?? 'same-run-search-incumbent',
  budget,
  objective: { scales, weights: Object.fromEntries(weights), contract: 'epsilon-q-e0-perceptual-v2-96-230-512-w20-45-35-v1' },
  rows,
  aggregates: {
    totalFitMilliseconds,
    totalFitMinutes: totalFitMilliseconds / 60_000,
    maximumFitMilliseconds: rows.length ? Math.max(...rows.map((row) => row.fitElapsedMilliseconds)) : null,
    medianRelativeImprovement: median(improvements),
    generationLatencyRole: 'diagnostic-only',
  },
  evidenceChecks,
  qualityTargets,
}
await writeFile(output, `${JSON.stringify(summary, null, 2)}\n`, 'utf8')
process.stdout.write(`${JSON.stringify({ status: summary.status, aggregates: summary.aggregates, evidenceChecks, qualityTargets })}\n`)
if (!evidencePassed) process.exitCode = 1
