/// <reference lib="webworker" />

import { fitImageToCoatOfArms, type ImageFitProgress } from './imageFitter'
import {
  FIT_WORKER_PROTOCOL,
  type FitWorkerPayload,
  type FitWorkerResponse,
  type FitWorkerStartRequest,
} from './fitWorkerProtocol'

self.onmessage = (event: MessageEvent<FitWorkerStartRequest>) => {
  const request = event.data
  if (
    request.protocol !== FIT_WORKER_PROTOCOL
    || request.kind !== 'start'
    || !Number.isSafeInteger(request.runId)
    || !Number.isSafeInteger(request.revision)
  ) return
  const reply = (message: FitWorkerPayload) => {
    self.postMessage({
      protocol: FIT_WORKER_PROTOCOL,
      runId: request.runId,
      revision: request.revision,
      ...message,
    } satisfies FitWorkerResponse)
  }
  try {
    const [image, patterns, emblems, options] = request.args
    const result = fitImageToCoatOfArms(image, patterns, emblems, {
      ...options,
      onProgress: (progress: ImageFitProgress) => reply({ kind: 'progress', progress }),
      onCheckpoint: (checkpoint) => reply({ kind: 'checkpoint', checkpoint }),
    })
    reply({ kind: 'result', ok: true, result })
  } catch (error) {
    reply({
      kind: 'result',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    })
  }
}
