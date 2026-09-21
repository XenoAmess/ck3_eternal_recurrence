export const FIT_QUALITY_OBJECTIVE_CONTRACT =
  'epsilon-q-e0-perceptual-v2-96-230-512-w20-45-35-v1' as const

export const FIT_QUALITY_SCALES = [96, 230, 512] as const

export type FitQualityScale = typeof FIT_QUALITY_SCALES[number]

export type FitQualityLossByScale = Readonly<Record<FitQualityScale, number>>

export const FIT_QUALITY_SCALE_WEIGHTS: Readonly<Record<FitQualityScale, number>> = Object.freeze({
  96: 0.20,
  230: 0.45,
  512: 0.35,
})

export const FIT_QUALITY_NUMERIC_TOLERANCE = 1e-12

export interface FitQualityObjective {
  readonly contract: typeof FIT_QUALITY_OBJECTIVE_CONTRACT
  readonly lossByScale: FitQualityLossByScale
  readonly weightedLoss: number
}

export type FitQualityOrder = -1 | 0 | 1

function validateTolerance(tolerance: number): void {
  if (!Number.isFinite(tolerance) || tolerance < 0) {
    throw new Error('拟合质量数值容差必须是非负有限数')
  }
}

function validateLoss(scale: FitQualityScale, loss: number): void {
  if (!Number.isFinite(loss) || loss < 0) {
    throw new Error(`${scale}px 拟合损失必须是非负有限数`)
  }
}

export function createFitQualityObjective(lossByScale: FitQualityLossByScale): FitQualityObjective {
  for (const scale of FIT_QUALITY_SCALES) validateLoss(scale, lossByScale[scale])
  const frozenLosses = Object.freeze({
    96: lossByScale[96],
    230: lossByScale[230],
    512: lossByScale[512],
  })
  return Object.freeze({
    contract: FIT_QUALITY_OBJECTIVE_CONTRACT,
    lossByScale: frozenLosses,
    weightedLoss: FIT_QUALITY_SCALES.reduce(
      (sum, scale) => sum + frozenLosses[scale] * FIT_QUALITY_SCALE_WEIGHTS[scale],
      0,
    ),
  })
}

export function fitQualityHasNoScaleRegression(
  candidate: FitQualityObjective,
  baseline: FitQualityObjective,
  tolerance = FIT_QUALITY_NUMERIC_TOLERANCE,
): boolean {
  validateTolerance(tolerance)
  return FIT_QUALITY_SCALES.every(
    (scale) => candidate.lossByScale[scale] <= baseline.lossByScale[scale] + tolerance,
  )
}

/**
 * Compare one replacement candidate with its incumbent. A positive result keeps
 * the incumbent, a negative result selects the candidate, and zero preserves
 * their existing stable order.
 *
 * The per-scale no-regression gate runs before the weighted objective. The
 * optional secondary comparator therefore only decides numerically tied
 * quality, so instance count or source size can never buy a quality regression.
 */
export function compareFitQualityCandidate(
  candidate: FitQualityObjective,
  incumbent: FitQualityObjective,
  compareQualityTie: () => number = () => 0,
  tolerance = FIT_QUALITY_NUMERIC_TOLERANCE,
): FitQualityOrder {
  validateTolerance(tolerance)
  if (!fitQualityHasNoScaleRegression(candidate, incumbent, tolerance)) return 1
  if (candidate.weightedLoss < incumbent.weightedLoss - tolerance) return -1
  if (candidate.weightedLoss > incumbent.weightedLoss + tolerance) return 1
  const tieOrder = compareQualityTie()
  if (!Number.isFinite(tieOrder)) throw new Error('拟合质量平局比较器必须返回有限数')
  return tieOrder < 0 ? -1 : tieOrder > 0 ? 1 : 0
}
