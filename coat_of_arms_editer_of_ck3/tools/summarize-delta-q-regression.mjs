import { readFile, readdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const [rootArgument, outputArgument, budgetArgument] = process.argv.slice(2)
const budget = Number.parseInt(budgetArgument ?? '', 10)
if (!rootArgument || !outputArgument || !Number.isSafeInteger(budget) || budget < 1) {
  throw new Error('usage: node tools/summarize-delta-q-regression.mjs <report-root> <output.json> <budget>')
}

const root = resolve(rootArgument)
const output = resolve(outputArgument)
const caseIds = (await readdir(root, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory() && entry.name.startsWith('picture-'))
  .map((entry) => entry.name)
  .sort()

const rows = []
for (const id of caseIds) {
  const report = JSON.parse(await readFile(resolve(root, id, 'report.json'), 'utf8'))
  rows.push({
    id,
    status: report.status,
    algorithm: report.provenance.algorithm,
    finalizationContract: report.provenance.fullAssetFinalization?.contract ?? null,
    layerBudget: report.configuration.userDrawInstanceBudget,
    drawnInstances: report.counts.drawnInstances,
    logicalLayers: report.counts.logicalLayers,
    coloredEmblemBlocks: report.counts.coloredEmblemBlocks,
    utf8Bytes: report.counts.utf8Bytes,
    lines: report.counts.lines,
    legacyTotalLoss: report.metrics.totalLoss,
    legacyEdgeLoss: report.metrics.edgeLoss,
    perceptualLossV2: report.perceptualMetricsV2?.totalLoss ?? null,
    paretoCandidates: report.paretoCandidates.length,
    fitElapsedMilliseconds: report.fitElapsedMilliseconds,
    parseErrors: report.integrity.parseErrors,
    serializeParseExact: report.integrity.serializeParseExact,
    fitAndEditorPreviewByteIdentical: report.integrity.fitAndEditorPreviewByteIdentical,
    sourceSha256: report.integrity.sourceSha256,
    canonicalPreviewSha256: report.integrity.canonicalPreviewSha256,
  })
}

const totalFitMilliseconds = rows.reduce((sum, row) => sum + row.fitElapsedMilliseconds, 0)
const checks = {
  caseCountMatches: rows.length === 7,
  exactCaseSet: JSON.stringify(caseIds) === JSON.stringify([
    'picture-01', 'picture-02', 'picture-03', 'picture-04',
    'picture-05', 'picture-06', 'picture-07',
  ]),
  budgetMatches: rows.every((row) => row.layerBudget === budget),
  withinLayerBudget: rows.every((row) => row.drawnInstances <= budget),
  algorithmMatches: rows.every((row) => row.algorithm === 'ck3-coa-browser-fit-v9-quality-first'),
  finalizationMatches: rows.every((row) => row.finalizationContract === 'full-dds-rescore-repair-pareto-v3'),
  parseSerializePassed: rows.every((row) => row.parseErrors === 0 && row.serializeParseExact),
  previewProjectionPassed: rows.every((row) => row.fitAndEditorPreviewByteIdentical),
  finiteMetrics: rows.every((row) => [
    row.legacyTotalLoss,
    row.legacyEdgeLoss,
    row.perceptualLossV2,
  ].every((value) => Number.isFinite(value) && value >= 0)),
}
const passed = Object.values(checks).every((value) => value === true)

const summary = {
  schema: 'ck3-coa-delta-q-regression-summary-v1',
  status: passed ? 'browser-passed-native-mcp-pending' : 'red',
  root: rootArgument,
  budget,
  rows,
  aggregates: {
    totalFitMilliseconds,
    totalFitMinutes: totalFitMilliseconds / 60_000,
    maximumFitMilliseconds: Math.max(...rows.map((row) => row.fitElapsedMilliseconds)),
    maximumDrawnInstances: Math.max(...rows.map((row) => row.drawnInstances)),
    maximumUtf8Bytes: Math.max(...rows.map((row) => row.utf8Bytes)),
    generationLatencyRole: 'diagnostic-only',
  },
  checks,
}
await writeFile(output, `${JSON.stringify(summary, null, 2)}\n`, 'utf8')
process.stdout.write(`${JSON.stringify({ status: summary.status, aggregates: summary.aggregates, checks })}\n`)
if (!passed) process.exitCode = 1
