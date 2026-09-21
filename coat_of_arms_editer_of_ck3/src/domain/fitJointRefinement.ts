import type { DecodedDds } from './dds'
import {
  renderCoatOfArms,
  resolveColor,
  type NamedColorMap,
  type RenderedCoatOfArms,
} from './renderer'
import type { CoatOfArms, CoatOfArmsInstance, ColoredEmblem } from './types'

export const JOINT_REFINEMENT_CONTRACT =
  'exact-dds-fixed-budget-coordinate-replacement-v1' as const

export interface JointRefinementRenderAssets {
  pattern?: DecodedDds
  coloredEmblems: Record<string, DecodedDds>
  texturedEmblems?: Record<string, DecodedDds>
  surfaceMask?: DecodedDds
}

export interface JointRefinementObjectiveInput {
  coatOfArms: CoatOfArms
  rendered: RenderedCoatOfArms
  phase: 'baseline' | 'candidate'
}

/** Lower values are better. Every call receives a complete exact-DDS render. */
export type JointRefinementObjective = (input: JointRefinementObjectiveInput) => number

export interface JointRefinementStageOptions {
  id: string
  passes: number
  positionSteps?: readonly number[]
  scaleSteps?: readonly number[]
  rotationSteps?: readonly number[]
  colorSteps?: readonly number[]
  tryColorCandidates?: boolean
  tryTextureReplacements?: boolean
}

export interface JointRefinementOptions {
  assets: JointRefinementRenderAssets
  namedColors: NamedColorMap
  objective: JointRefinementObjective
  /** Includes the baseline render. */
  maxEvaluations?: number
  renderSize?: number
  minimumImprovement?: number
  tieTolerance?: number
  eligibleTextures?: readonly string[]
  /** Stable input order is used as the replacement tie order. */
  maxReplacementCandidates?: number
  colorCandidates?: readonly string[]
  stages?: readonly JointRefinementStageOptions[]
  positionRange?: readonly [number, number]
  scaleMagnitudeRange?: readonly [number, number]
}

export type JointRefinementMove =
  | {
    kind: 'color'
    blockIndex: number
    instanceIndex: number
    flatInstanceIndex: number
    colorIndex: 0 | 1 | 2
    before: string
    after: string
  }
  | {
    kind: 'position'
    blockIndex: number
    instanceIndex: number
    flatInstanceIndex: number
    axis: 0 | 1
    before: number
    after: number
  }
  | {
    kind: 'scale'
    blockIndex: number
    instanceIndex: number
    flatInstanceIndex: number
    axis: 0 | 1
    before: number
    after: number
  }
  | {
    kind: 'rotation'
    blockIndex: number
    instanceIndex: number
    flatInstanceIndex: number
    before: number
    after: number
  }
  | {
    kind: 'texture-replacement'
    blockIndex: number
    instanceIndex: number
    flatInstanceIndex: number
    before: string
    after: string
  }

export interface AcceptedJointRefinementMove {
  stageId: string
  pass: number
  lossBefore: number
  lossAfter: number
  move: JointRefinementMove
}

export interface JointRefinementStageReceipt {
  id: string
  lossBefore: number
  lossAfter: number
  passesPlanned: number
  passesAttempted: number
  evaluatedMoves: number
  acceptedMoves: number
  terminationReason: 'passes-complete' | 'no-improvement' | 'evaluation-budget'
}

export interface JointRefinementReceipt {
  contract: typeof JOINT_REFINEMENT_CONTRACT
  deterministic: true
  renderer: 'complete-decoded-dds'
  evaluationBudget: number
  objectiveEvaluations: number
  evaluatedMoves: number
  acceptedMoves: AcceptedJointRefinementMove[]
  lossBefore: number
  lossAfter: number
  drawnInstancesBefore: number
  drawnInstancesAfter: number
  keptIncumbent: boolean
  stages: JointRefinementStageReceipt[]
  terminationReason: 'complete' | 'no-improvement' | 'evaluation-budget'
}

export interface JointRefinementResult {
  coatOfArms: CoatOfArms
  receipt: JointRefinementReceipt
}

interface InstanceReference {
  blockIndex: number
  instanceIndex: number
  flatInstanceIndex: number
}

interface MoveProposal {
  move: JointRefinementMove
  apply: (coatOfArms: CoatOfArms) => void
}

const DEFAULT_STAGES: readonly JointRefinementStageOptions[] = [
  {
    id: 'coarse',
    passes: 4,
    positionSteps: [0.04],
    scaleSteps: [0.06],
    rotationSteps: [12],
    colorSteps: [0.08],
    tryColorCandidates: true,
    tryTextureReplacements: true,
  },
  {
    id: 'fine',
    passes: 6,
    positionSteps: [0.0125],
    scaleSteps: [0.02],
    rotationSteps: [3],
    colorSteps: [0.025],
    tryColorCandidates: false,
    tryTextureReplacements: false,
  },
]

const cloneInstance = (instance: CoatOfArmsInstance): CoatOfArmsInstance => ({
  position: [...instance.position],
  scale: [...instance.scale],
  rotation: instance.rotation,
  depth: instance.depth,
})

const cloneBlock = (block: ColoredEmblem): ColoredEmblem => ({
  texture: block.texture,
  colors: [...block.colors],
  mask: [...block.mask],
  instances: block.instances.map(cloneInstance),
})

export function cloneCoatOfArmsForJointRefinement(coatOfArms: CoatOfArms): CoatOfArms {
  return {
    outerKey: coatOfArms.outerKey,
    parent: coatOfArms.parent,
    pattern: coatOfArms.pattern,
    colors: [...coatOfArms.colors],
    coloredEmblems: coatOfArms.coloredEmblems.map(cloneBlock),
    texturedEmblems: coatOfArms.texturedEmblems.map((emblem) => ({ ...emblem })),
    rootPresence: coatOfArms.rootPresence ? {
      pattern: coatOfArms.rootPresence.pattern,
      colors: [...coatOfArms.rootPresence.colors],
    } : undefined,
  }
}

const drawnInstances = (coatOfArms: CoatOfArms): number => coatOfArms.coloredEmblems
  .reduce((total, block) => total + block.instances.length, 0)

const clamp = (value: number, range: readonly [number, number]): number =>
  Math.min(range[1], Math.max(range[0], value))

const sameNumber = (left: number, right: number): boolean => Object.is(left, right)

function validateRange(name: string, range: readonly [number, number]): void {
  if (!range.every(Number.isFinite) || range[0] >= range[1]) {
    throw new Error(`${name} 必须是递增的有限区间`)
  }
}

function validateSteps(name: string, values: readonly number[]): number[] {
  const result = values.map(Number)
  if (result.some((value) => !Number.isFinite(value) || value <= 0)) {
    throw new Error(`${name} 必须全部为正有限数`)
  }
  return [...new Set(result)]
}

function validatedStages(stages: readonly JointRefinementStageOptions[]): JointRefinementStageOptions[] {
  if (!stages.length) throw new Error('联合细化至少需要一个阶段')
  if (stages.length > 16) throw new Error('联合细化阶段数超过上限 16')
  return stages.map((stage) => {
    if (!stage.id.trim()) throw new Error('联合细化阶段 id 不能为空')
    if (!Number.isSafeInteger(stage.passes) || stage.passes < 1 || stage.passes > 64) {
      throw new Error(`联合细化阶段 ${stage.id} 的 passes 必须在 1..64`)
    }
    return {
      ...stage,
      positionSteps: validateSteps(`${stage.id}.positionSteps`, stage.positionSteps ?? []),
      scaleSteps: validateSteps(`${stage.id}.scaleSteps`, stage.scaleSteps ?? []),
      rotationSteps: validateSteps(`${stage.id}.rotationSteps`, stage.rotationSteps ?? []),
      colorSteps: validateSteps(`${stage.id}.colorSteps`, stage.colorSteps ?? []),
    }
  })
}

function instanceReferences(coatOfArms: CoatOfArms): InstanceReference[] {
  const result: InstanceReference[] = []
  let flatInstanceIndex = 0
  for (let blockIndex = 0; blockIndex < coatOfArms.coloredEmblems.length; blockIndex += 1) {
    const block = coatOfArms.coloredEmblems[blockIndex]
    for (let instanceIndex = 0; instanceIndex < block.instances.length; instanceIndex += 1) {
      result.push({ blockIndex, instanceIndex, flatInstanceIndex: flatInstanceIndex++ })
    }
  }
  return result
}

/**
 * Isolate one instance for a style mutation while preserving flattened source
 * order. Splitting a block changes neither draw count nor exact rendering.
 */
function isolateInstance(
  coatOfArms: CoatOfArms,
  blockIndex: number,
  instanceIndex: number,
): ColoredEmblem {
  const source = coatOfArms.coloredEmblems[blockIndex]
  if (source.instances.length === 1) return source
  const replacement: ColoredEmblem[] = []
  if (instanceIndex > 0) replacement.push({
    ...cloneBlock(source),
    instances: source.instances.slice(0, instanceIndex).map(cloneInstance),
  })
  const selected = { ...cloneBlock(source), instances: [cloneInstance(source.instances[instanceIndex])] }
  replacement.push(selected)
  if (instanceIndex + 1 < source.instances.length) replacement.push({
    ...cloneBlock(source),
    instances: source.instances.slice(instanceIndex + 1).map(cloneInstance),
  })
  coatOfArms.coloredEmblems.splice(blockIndex, 1, ...replacement)
  return selected
}

function rgbExpression(rgb: readonly number[]): string {
  const component = (value: number) => Number(value.toFixed(6)).toString()
  return `rgb { ${component(rgb[0])} ${component(rgb[1])} ${component(rgb[2])} }`
}

function normalizedRotation(value: number): number {
  const normalized = ((value + 180) % 360 + 360) % 360 - 180
  return Object.is(normalized, -0) ? 0 : normalized
}

function geometryProposal(
  reference: InstanceReference,
  move: JointRefinementMove,
  mutate: (instance: CoatOfArmsInstance) => void,
): MoveProposal {
  return {
    move,
    apply: (coatOfArms) => mutate(
      coatOfArms.coloredEmblems[reference.blockIndex].instances[reference.instanceIndex],
    ),
  }
}

function enumerateMoves(
  coatOfArms: CoatOfArms,
  stage: JointRefinementStageOptions,
  namedColors: NamedColorMap,
  colorCandidates: readonly string[],
  replacementTextures: readonly string[],
  positionRange: readonly [number, number],
  scaleMagnitudeRange: readonly [number, number],
): MoveProposal[] {
  const proposals: MoveProposal[] = []
  for (const reference of instanceReferences(coatOfArms)) {
    const block = coatOfArms.coloredEmblems[reference.blockIndex]
    const instance = block.instances[reference.instanceIndex]

    for (const axis of [0, 1] as const) {
      for (const step of stage.positionSteps ?? []) {
        for (const direction of [-1, 1] as const) {
          const after = clamp(instance.position[axis] + direction * step, positionRange)
          if (sameNumber(after, instance.position[axis])) continue
          proposals.push(geometryProposal(reference, {
            kind: 'position', ...reference, axis,
            before: instance.position[axis], after,
          }, (target) => { target.position[axis] = after }))
        }
      }
      for (const step of stage.scaleSteps ?? []) {
        for (const direction of [-1, 1] as const) {
          const sign = instance.scale[axis] < 0 ? -1 : 1
          const magnitude = clamp(Math.abs(instance.scale[axis]) + direction * step, scaleMagnitudeRange)
          const after = sign * magnitude
          if (sameNumber(after, instance.scale[axis])) continue
          proposals.push(geometryProposal(reference, {
            kind: 'scale', ...reference, axis,
            before: instance.scale[axis], after,
          }, (target) => { target.scale[axis] = after }))
        }
      }
    }

    for (const step of stage.rotationSteps ?? []) {
      for (const direction of [-1, 1] as const) {
        const after = normalizedRotation(instance.rotation + direction * step)
        if (sameNumber(after, instance.rotation)) continue
        proposals.push(geometryProposal(reference, {
          kind: 'rotation', ...reference, before: instance.rotation, after,
        }, (target) => { target.rotation = after }))
      }
    }

    for (const colorIndex of [0, 1, 2] as const) {
      const before = block.colors[colorIndex]
      const localCandidates: string[] = []
      const resolved = resolveColor(before, namedColors)
      if (resolved) {
        for (const step of stage.colorSteps ?? []) {
          for (const channel of [0, 1, 2] as const) {
            for (const direction of [-1, 1] as const) {
              const next = [...resolved]
              next[channel] = clamp(next[channel] + direction * step, [0, 1])
              localCandidates.push(rgbExpression(next))
            }
          }
        }
      }
      if (stage.tryColorCandidates) localCandidates.push(...colorCandidates)
      for (const after of new Set(localCandidates)) {
        if (after === before) continue
        const move: JointRefinementMove = {
          kind: 'color', ...reference, colorIndex, before, after,
        }
        proposals.push({
          move,
          apply: (candidate) => {
            isolateInstance(candidate, reference.blockIndex, reference.instanceIndex).colors[colorIndex] = after
          },
        })
      }
    }

    if (stage.tryTextureReplacements) {
      for (const after of replacementTextures) {
        if (after === block.texture) continue
        const move: JointRefinementMove = {
          kind: 'texture-replacement', ...reference, before: block.texture, after,
        }
        proposals.push({
          move,
          apply: (candidate) => {
            isolateInstance(candidate, reference.blockIndex, reference.instanceIndex).texture = after
          },
        })
      }
    }
  }
  return proposals
}

function evenlySample<T>(values: readonly T[], maximum: number): T[] {
  if (values.length <= maximum) return [...values]
  if (maximum <= 0) return []
  return Array.from({ length: maximum }, (_, index) =>
    values[Math.floor((index + 0.5) * values.length / maximum)])
}

function exactLoss(
  coatOfArms: CoatOfArms,
  options: JointRefinementOptions,
  renderSize: number,
  phase: 'baseline' | 'candidate',
): number {
  const rendered = renderCoatOfArms(
    coatOfArms,
    options.assets,
    options.namedColors,
    renderSize,
  )
  if (!rendered) throw new Error('联合细化无法完成精确 DDS 渲染')
  const loss = options.objective({ coatOfArms, rendered, phase })
  if (!Number.isFinite(loss)) throw new Error('联合细化目标函数必须返回有限数')
  return loss
}

/**
 * Deterministic fixed-budget coordinate descent over a complete coat of arms.
 * Candidate acceptance always uses the complete decoded-DDS renderer. Style
 * edits isolate one source instance but never add a drawn instance.
 */
export function refineCoatOfArmsJointly(
  source: CoatOfArms,
  options: JointRefinementOptions,
): JointRefinementResult {
  const maxEvaluations = options.maxEvaluations ?? 4096
  const renderSize = options.renderSize ?? 230
  const minimumImprovement = options.minimumImprovement ?? 1e-12
  const tieTolerance = options.tieTolerance ?? 1e-15
  const positionRange = options.positionRange ?? [0, 1]
  const scaleMagnitudeRange = options.scaleMagnitudeRange ?? [0.01, 2]
  const maxReplacementCandidates = options.maxReplacementCandidates ?? 32
  if (!Number.isSafeInteger(maxEvaluations) || maxEvaluations < 1) {
    throw new Error('maxEvaluations 必须是正安全整数')
  }
  if (!Number.isSafeInteger(renderSize) || renderSize < 2 || renderSize > 2048) {
    throw new Error('renderSize 必须是 2..2048 的安全整数')
  }
  if (!Number.isFinite(minimumImprovement) || minimumImprovement < 0) {
    throw new Error('minimumImprovement 必须是非负有限数')
  }
  if (!Number.isFinite(tieTolerance) || tieTolerance < 0) {
    throw new Error('tieTolerance 必须是非负有限数')
  }
  if (!Number.isSafeInteger(maxReplacementCandidates) || maxReplacementCandidates < 0) {
    throw new Error('maxReplacementCandidates 必须是非负安全整数')
  }
  validateRange('positionRange', positionRange)
  validateRange('scaleMagnitudeRange', scaleMagnitudeRange)
  if (scaleMagnitudeRange[0] <= 0) throw new Error('scaleMagnitudeRange 下界必须大于 0')

  const stages = validatedStages(options.stages ?? DEFAULT_STAGES)
  const colorCandidates = [...new Set(options.colorCandidates ?? [])]
  for (const color of colorCandidates) {
    if (!resolveColor(color, options.namedColors)) throw new Error(`无法解析颜色候选：${color}`)
  }
  const eligibleTextures = [...new Set(options.eligibleTextures ?? [])]
  for (const texture of eligibleTextures) {
    if (!options.assets.coloredEmblems[texture]) {
      throw new Error(`替换候选没有精确 DDS：${texture}`)
    }
  }
  const replacementTextures = eligibleTextures.slice(0, maxReplacementCandidates)
  const originalInstances = drawnInstances(source)
  const original = cloneCoatOfArmsForJointRefinement(source)
  let incumbent = original
  const lossBefore = exactLoss(incumbent, options, renderSize, 'baseline')
  let incumbentLoss = lossBefore
  let objectiveEvaluations = 1
  let evaluatedMoves = 0
  const acceptedMoves: AcceptedJointRefinementMove[] = []
  const stageReceipts: JointRefinementStageReceipt[] = []
  let remainingPasses = stages.reduce((total, stage) => total + stage.passes, 0)

  for (const stage of stages) {
    const stageLossBefore = incumbentLoss
    let stageEvaluated = 0
    let stageAccepted = 0
    let passesAttempted = 0
    let terminationReason: JointRefinementStageReceipt['terminationReason'] = 'passes-complete'
    for (let pass = 0; pass < stage.passes; pass += 1) {
      if (objectiveEvaluations >= maxEvaluations) {
        terminationReason = 'evaluation-budget'
        break
      }
      passesAttempted += 1
      const proposals = enumerateMoves(
        incumbent,
        stage,
        options.namedColors,
        colorCandidates,
        replacementTextures,
        positionRange,
        scaleMagnitudeRange,
      )
      const remainingBudget = maxEvaluations - objectiveEvaluations
      const passBudget = Math.max(1, Math.floor(remainingBudget / Math.max(1, remainingPasses)))
      const selected = evenlySample(proposals, Math.min(remainingBudget, passBudget))
      let best: { proposal: MoveProposal, coatOfArms: CoatOfArms, loss: number } | null = null
      for (const proposal of selected) {
        const candidate = cloneCoatOfArmsForJointRefinement(incumbent)
        proposal.apply(candidate)
        if (drawnInstances(candidate) > originalInstances) {
          throw new Error('联合细化候选超过原始绘制实例预算')
        }
        const loss = exactLoss(candidate, options, renderSize, 'candidate')
        objectiveEvaluations += 1
        evaluatedMoves += 1
        stageEvaluated += 1
        if (
          loss < incumbentLoss - minimumImprovement
          && (!best || loss < best.loss - tieTolerance)
        ) best = { proposal, coatOfArms: candidate, loss }
      }
      remainingPasses -= 1
      if (!best) {
        terminationReason = objectiveEvaluations >= maxEvaluations
          ? 'evaluation-budget'
          : 'no-improvement'
        break
      }
      const previousLoss = incumbentLoss
      incumbent = best.coatOfArms
      incumbentLoss = best.loss
      stageAccepted += 1
      acceptedMoves.push({
        stageId: stage.id,
        pass,
        lossBefore: previousLoss,
        lossAfter: incumbentLoss,
        move: best.proposal.move,
      })
    }
    remainingPasses -= Math.max(0, stage.passes - passesAttempted)
    stageReceipts.push({
      id: stage.id,
      lossBefore: stageLossBefore,
      lossAfter: incumbentLoss,
      passesPlanned: stage.passes,
      passesAttempted,
      evaluatedMoves: stageEvaluated,
      acceptedMoves: stageAccepted,
      terminationReason,
    })
    if (objectiveEvaluations >= maxEvaluations) break
  }

  const keptIncumbent = acceptedMoves.length === 0
  const result = keptIncumbent ? original : incumbent
  const drawnInstancesAfter = drawnInstances(result)
  if (drawnInstancesAfter > originalInstances) {
    throw new Error('联合细化结果超过原始绘制实例预算')
  }
  const budgetExhausted = objectiveEvaluations >= maxEvaluations
  return {
    coatOfArms: result,
    receipt: {
      contract: JOINT_REFINEMENT_CONTRACT,
      deterministic: true,
      renderer: 'complete-decoded-dds',
      evaluationBudget: maxEvaluations,
      objectiveEvaluations,
      evaluatedMoves,
      acceptedMoves,
      lossBefore,
      lossAfter: incumbentLoss,
      drawnInstancesBefore: originalInstances,
      drawnInstancesAfter,
      keptIncumbent,
      stages: stageReceipts,
      terminationReason: budgetExhausted
        ? 'evaluation-budget'
        : keptIncumbent ? 'no-improvement' : 'complete',
    },
  }
}
