/// <reference lib="webworker" />

import { fitImageToCoatOfArms, resizeFitImage, type ImageFitProgress } from './imageFitter'
import { createWebGl2BatchScorer } from './webglBatchScorer'
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
    const batchScorer = createWebGl2BatchScorer(resizeFitImage(image, options.resolution ?? 40))
    try {
      const result = fitImageToCoatOfArms(image, patterns, emblems, {
        ...options,
        batchSearchRequested: true,
        batchScorer: batchScorer ?? undefined,
        onProgress: (progress: ImageFitProgress) => reply({ kind: 'progress', progress }),
        onCheckpoint: (checkpoint) => reply({ kind: 'checkpoint', checkpoint }),
      })
      reply({ kind: 'result', ok: true, result })
    } finally {
      batchScorer?.dispose()
    }
  } catch (error) {
    reply({
      kind: 'result',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    })
  }
}
