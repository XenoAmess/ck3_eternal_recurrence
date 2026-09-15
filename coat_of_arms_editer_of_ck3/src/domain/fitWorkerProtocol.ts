import type {
  FitImage,
  FitTextureCandidate,
  ImageFitCheckpoint,
  ImageFitOptions,
  ImageFitProgress,
  ImageFitResult,
} from './imageFitter'

export const FIT_WORKER_PROTOCOL = 'ck3-coa-fit-worker-v1' as const

export type FitTaskState =
  | 'idle'
  | 'preparing'
  | 'running'
  | 'paused'
  | 'cancelled'
  | 'completed'
  | 'failed'

export interface FitWorkerStartRequest {
  protocol: typeof FIT_WORKER_PROTOCOL
  kind: 'start'
  runId: number
  revision: number
  args: [FitImage, FitTextureCandidate[], FitTextureCandidate[], ImageFitOptions]
}

interface FitWorkerMessageBase {
  protocol: typeof FIT_WORKER_PROTOCOL
  runId: number
  revision: number
}

export type FitWorkerPayload =
  | { kind: 'progress', progress: ImageFitProgress }
  | { kind: 'checkpoint', checkpoint: ImageFitCheckpoint }
  | { kind: 'result', ok: true, result: ImageFitResult }
  | { kind: 'result', ok: false, error: string }

export type FitWorkerResponse = FitWorkerMessageBase & FitWorkerPayload

export function isCurrentFitWorkerMessage(
  message: FitWorkerResponse,
  runId: number,
  revision: number,
): boolean {
  return message.protocol === FIT_WORKER_PROTOCOL
    && message.runId === runId
    && message.revision === revision
}
