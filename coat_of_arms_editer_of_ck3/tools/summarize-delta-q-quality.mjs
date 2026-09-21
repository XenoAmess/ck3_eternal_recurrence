import { readFile, readdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'

const [baselineArgument, finalArgument, outputArgument] = process.argv.slice(2)
if (!baselineArgument || !finalArgument || !outputArgument) {
  throw new Error('usage: node tools/summarize-delta-q-quality.mjs <v14-shadow.json> <final-root> <output.json>')
}

const baselinePath = resolve(baselineArgument)
const finalRoot = resolve(finalArgument)
const outputPath = resolve(outputArgument)
const baseline = JSON.parse(await readFile(baselinePath, 'utf8'))
const legacyBaselineRoot = resolve(dirname(baselinePath), baseline.predecessor)
const baselineById = new Map(baseline.rows.map((row) => [
  row.id,
  row.resolutions.find((item) => item.resolution === 96)?.metrics.totalLoss,
]))
const caseIds = (await readdir(finalRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory() && entry.name.startsWith('picture-'))
  .map((entry) => entry.name)
  .sort()

const rows = []
for (const id of caseIds) {
  const report = JSON.parse(await readFile(resolve(finalRoot, id, 'report.json'), 'utf8'))
  const legacyBaseline = JSON.parse(await readFile(resolve(legacyBaselineRoot, id, 'report.json'), 'utf8'))
  const baselineLoss = baselineById.get(id)
  if (!Number.isFinite(baselineLoss)) throw new Error(`missing 96px v14 baseline for ${id}`)
  const selectedLoss = report.perceptualMetricsV2.totalLoss
  const bestCandidate = [...report.paretoCandidates]
    .sort((left, right) => left.perceptualMetricsV2.totalLoss - right.perceptualMetricsV2.totalLoss
      || left.index - right.index)[0]
  rows.push({
    id,
    baselinePerceptualLossV2: baselineLoss,
    selectedPerceptualLossV2: selectedLoss,
    selectedRelativeImprovement: (baselineLoss - selectedLoss) / baselineLoss,
    bestParetoIndex: bestCandidate.index,
    bestParetoPerceptualLossV2: bestCandidate.perceptualMetricsV2.totalLoss,
    bestParetoRelativeImprovement: (baselineLoss - bestCandidate.perceptualMetricsV2.totalLoss) / baselineLoss,
    selectedLegacyTotalLoss: report.metrics.totalLoss,
    selectedLegacyEdgeLoss: report.metrics.edgeLoss,
    baselineLegacyTotalLoss: legacyBaseline.metrics.totalLoss,
    baselineLegacyEdgeLoss: legacyBaseline.metrics.edgeLoss,
    legacyTotalNonRegression: report.metrics.totalLoss <= legacyBaseline.metrics.totalLoss + 1e-12,
    legacyEdgeNonRegression: report.metrics.edgeLoss <= legacyBaseline.metrics.edgeLoss + 1e-12,
    fitElapsedMilliseconds: report.fitElapsedMilliseconds,
    drawnInstances: report.counts.drawnInstances,
    paretoCandidates: report.paretoCandidates.map((candidate) => ({
      index: candidate.index,
      reconstructionMode: candidate.reconstructionMode,
      drawnInstances: candidate.stats.drawnInstances,
      legacyTotalLoss: candidate.metrics.totalLoss,
      legacyEdgeLoss: candidate.metrics.edgeLoss,
      perceptualLossV2: candidate.perceptualMetricsV2.totalLoss,
    })),
  })
}

const median = (values) => {
  const sorted = [...values].sort((left, right) => left - right)
  return sorted[Math.floor(sorted.length / 2)]
}
const totalFitMilliseconds = rows.reduce((sum, row) => sum + row.fitElapsedMilliseconds, 0)
const summary = {
  schema: 'ck3-coa-delta-q-quality-summary-v1',
  baseline: baselineArgument,
  finalRoot: finalArgument,
  cases: rows,
  aggregates: {
    caseCount: rows.length,
    selectedMedianRelativeImprovement: median(rows.map((row) => row.selectedRelativeImprovement)),
    selectedWorstRelativeImprovement: Math.min(...rows.map((row) => row.selectedRelativeImprovement)),
    bestParetoMedianRelativeImprovement: median(rows.map((row) => row.bestParetoRelativeImprovement)),
    bestParetoWorstRelativeImprovement: Math.min(...rows.map((row) => row.bestParetoRelativeImprovement)),
    totalFitMilliseconds,
    totalFitMinutes: totalFitMilliseconds / 60_000,
    generationLatencyRole: 'diagnostic-only',
    formerPerformanceReferenceMilliseconds: 14.1 * 60_000 * 1.25,
    perceptualMedianGatePassed: median(rows.map((row) => row.selectedRelativeImprovement)) >= 0.15,
    perceptualWorstCaseGatePassed: Math.min(...rows.map((row) => row.selectedRelativeImprovement)) >= -0.02,
    legacyTotalNonRegressionCases: rows.filter((row) => row.legacyTotalNonRegression).length,
    legacyEdgeNonRegressionCases: rows.filter((row) => row.legacyEdgeNonRegression).length,
    withinLayerBudget: rows.every((row) => row.drawnInstances <= 1_024),
  },
}
await writeFile(outputPath, `${JSON.stringify(summary, null, 2)}\n`, 'utf8')
process.stdout.write(`${JSON.stringify(summary.aggregates)}\n`)
