import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { DecodedDds } from './dds'
import {
  EPSILON_QUALITY_CORPUS_CONTRACT,
  EPSILON_QUALITY_SCENARIOS,
  renderEpsilonQualityScenario,
} from './epsilonQualityCorpus'
import { finalizeImageFitWithFullAssets } from './fitFinalizer'
import { fitImageToCoatOfArms, type FitTextureCandidate } from './imageFitter'
import { computeFitTextureShapeFeatures } from './shapeFeatures'

const benchmark = process.env.EPSILON_Q_RUN_HOLDOUT === '1' ? it : it.skip

function texture(kind: 'solid' | 'block' | 'circle' | 'diamond' | 'triangle'): DecodedDds {
  const size = 32
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const offset = (y * size + x) * 4
      const u = (x + 0.5) / size
      const v = (y + 0.5) / size
      const inside = kind === 'solid' || kind === 'block'
        ? true
        : kind === 'circle'
          ? Math.hypot(u - 0.5, v - 0.5) <= 0.48
          : kind === 'diamond'
            ? Math.abs(u - 0.5) + Math.abs(v - 0.5) <= 0.49
            : v >= 0.04 && v <= 0.96 && Math.abs(u - 0.5) <= v * 0.5
      if (inside) pixels[offset + (kind === 'solid' ? 0 : 2)] = kind === 'solid' ? 255 : 128
      pixels[offset + 3] = inside ? 255 : 0
    }
  }
  return { width: size, height: size, fourCC: 'BGRA8', pixels }
}

function fitAsset(name: string, decoded: DecodedDds): FitTextureCandidate {
  return {
    name,
    assetSha256: name.padEnd(64, '0').slice(0, 64).toUpperCase(),
    texture: decoded,
    shapeFeatures: computeFitTextureShapeFeatures(decoded),
  }
}

const median = (values: number[]): number => {
  const sorted = [...values].sort((left, right) => left - right)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
}

describe('Epsilon-Q sealed holdout benchmark', () => {
  benchmark('measures the frozen 16-scene holdout once with the product objective', async () => {
    const pattern = texture('solid')
    const exactAssets = {
      'ce_block_02.dds': texture('block'),
      'ce_billet.dds': texture('block'),
      'ce_circle.dds': texture('circle'),
      'ce_lozenge.dds': texture('diamond'),
      'ce_triangle_mask.dds': texture('triangle'),
    }
    const patterns = [fitAsset('pattern_solid.dds', pattern)]
    const emblems = Object.entries(exactAssets).map(([name, decoded]) => fitAsset(name, decoded))
    const rows = []
    for (const scenario of EPSILON_QUALITY_SCENARIOS.filter((item) => item.split === 'sealed-holdout')) {
      const target = renderEpsilonQualityScenario(scenario, 96)
      const targetPyramid = [96, 230, 512].map((size) => renderEpsilonQualityScenario(scenario, size))
      const searchResult = fitImageToCoatOfArms(target, patterns, emblems, {
        resolution: 48,
        pyramidImages: targetPyramid,
        maxPatterns: patterns.length,
        maxEmblemCandidates: emblems.length,
        maxLayers: 16,
        refinementCandidates: 16,
        beamWidth: 2,
        inputSha256: scenario.id.padEnd(64, '0').slice(0, 64).toUpperCase(),
        assetPackManifestSha256: 'E'.repeat(64),
      })
      const finalization = finalizeImageFitWithFullAssets(searchResult, target, {
        patterns: { 'pattern_solid.dds': pattern },
        coloredEmblems: exactAssets,
      }, {}, {
        targetPyramid,
        jointRefinementEvaluations: 256,
        contourReplacementEvaluations: 32,
        pruneDrawnInstanceLimit: 16,
      })
      const selection = finalization.receipt.multiscaleSelection
      const relativeImprovement = selection.incumbentLoss <= 1e-12
        ? 0
        : (selection.incumbentLoss - selection.selectedLoss) / selection.incumbentLoss
      rows.push({
        id: scenario.id,
        family: scenario.family,
        category: scenario.category,
        incumbentLoss: selection.incumbentLoss,
        selectedLoss: selection.selectedLoss,
        relativeImprovement,
        selectedVariant: selection.selectedVariant,
        incumbentPerScale: selection.incumbentPerScale,
        selectedPerScale: selection.selectedPerScale,
        drawnInstances: finalization.result.provenance.drawnInstances,
        jointAcceptedMoves: finalization.receipt.jointRefinement.acceptedMoves.length,
        contourAccepted: finalization.receipt.contourRefinement.acceptedCandidateAdded,
      })
    }
    const improvements = rows.map((row) => row.relativeImprovement)
    const categoryRows = [...new Set(rows.map((row) => row.category))].map((category) => {
      const categoryImprovements = rows
        .filter((row) => row.category === category)
        .map((row) => row.relativeImprovement)
      return { category, cases: categoryImprovements.length, medianRelativeImprovement: median(categoryImprovements) }
    })
    const measuredMedian = median(improvements)
    const report = {
      schema: 'ck3-coa-epsilon-q-sealed-holdout-v1',
      status: measuredMedian >= 0.05
        ? 'measured-quality-target-met'
        : 'measured-quality-target-missed',
      corpusContract: EPSILON_QUALITY_CORPUS_CONTRACT,
      split: 'sealed-holdout',
      configuration: {
        cases: rows.length,
        drawInstanceBudget: 16,
        objectiveContract: 'epsilon-q-e0-perceptual-v2-96-230-512-w20-45-35-v1',
        jointRefinementEvaluations: 256,
        contourReplacementEvaluations: 32,
      },
      rows,
      aggregates: {
        medianRelativeImprovement: measuredMedian,
        improvedCases: rows.filter((row) => row.relativeImprovement > 1e-12).length,
        allScalesNonRegressing: rows.every((row) => row.selectedPerScale.every((selected) => {
          const incumbent = row.incumbentPerScale.find((item) => item.resolution === selected.resolution)
          return incumbent && selected.v2.totalLoss <= incumbent.v2.totalLoss + 1e-12
        })),
        withinBudget: rows.every((row) => row.drawnInstances <= 16),
        byCategory: categoryRows,
      },
      evidenceBoundary: {
        inputs: 'programmatic-independent-families',
        assets: 'programmatic-native-shape-proxies',
        externalRealImageGeneralization: 'not-covered-by-this-holdout',
        nativeCk3: 'not-applicable-to-programmatic-assets',
      },
    }
    expect(rows).toHaveLength(16)
    expect(new Set(rows.map((row) => row.family)).size).toBe(16)
    expect(report.aggregates.allScalesNonRegressing).toBe(true)
    expect(report.aggregates.withinBudget).toBe(true)
    const output = resolve(process.env.EPSILON_Q_HOLDOUT_OUTPUT
      ?? '../docs/coat-of-arms-fit-artifacts/epsilon-q-v13-holdout/report.json')
    await mkdir(dirname(output), { recursive: true })
    await writeFile(output, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
    console.info(JSON.stringify({ status: report.status, aggregates: report.aggregates }))
  }, 30 * 60_000)
})
