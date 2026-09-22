import type {
  FullAssetFitAssets,
  FullAssetFitFinalizationOptions,
  FullAssetFitFinalizationReceipt,
} from './fitFinalizer'
import type { FitImage, ImageFitResult } from './imageFitter'
import type { NamedColorMap } from './renderer'

export const FIT_FINALIZER_WORKER_PROTOCOL = 'ck3-coa-fit-finalizer-worker-v1' as const

export interface FitFinalizerWorkerStartRequest {
  protocol: typeof FIT_FINALIZER_WORKER_PROTOCOL
  kind: 'start'
  runId: number
  revision: number
  args: [
    ImageFitResult,
    FitImage,
    FullAssetFitAssets,
    NamedColorMap,
    FullAssetFitFinalizationOptions,
  ]
}

export interface FullAssetFitFinalization {
  result: ImageFitResult
  receipt: FullAssetFitFinalizationReceipt
}

interface FitFinalizerWorkerMessageBase {
  protocol: typeof FIT_FINALIZER_WORKER_PROTOCOL
  runId: number
  revision: number
}

export type FitFinalizerWorkerPayload =
  | { kind: 'result', ok: true, finalization: FullAssetFitFinalization }
  | { kind: 'result', ok: false, error: string }

export type FitFinalizerWorkerResponse = FitFinalizerWorkerMessageBase & FitFinalizerWorkerPayload

export function isCurrentFitFinalizerWorkerMessage(
  message: FitFinalizerWorkerResponse,
  runId: number,
  revision: number,
): boolean {
  return message.protocol === FIT_FINALIZER_WORKER_PROTOCOL
    && message.runId === runId
    && message.revision === revision
}
