/// <reference lib="webworker" />

import { finalizeImageFitWithFullAssets } from './fitFinalizer'
import {
  FIT_FINALIZER_WORKER_PROTOCOL,
  type FitFinalizerWorkerPayload,
  type FitFinalizerWorkerResponse,
  type FitFinalizerWorkerStartRequest,
} from './fitFinalizerWorkerProtocol'

self.onmessage = (event: MessageEvent<FitFinalizerWorkerStartRequest>) => {
  const request = event.data
  if (
    request.protocol !== FIT_FINALIZER_WORKER_PROTOCOL
    || request.kind !== 'start'
    || !Number.isSafeInteger(request.runId)
    || !Number.isSafeInteger(request.revision)
  ) return
  const reply = (message: FitFinalizerWorkerPayload) => {
    self.postMessage({
      protocol: FIT_FINALIZER_WORKER_PROTOCOL,
      runId: request.runId,
      revision: request.revision,
      ...message,
    } satisfies FitFinalizerWorkerResponse)
  }
  try {
    const [searchResult, target, assets, namedColors, options] = request.args
    reply({
      kind: 'result',
      ok: true,
      finalization: finalizeImageFitWithFullAssets(
        searchResult,
        target,
        assets,
        namedColors,
        options,
      ),
    })
  } catch (error) {
    reply({
      kind: 'result',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    })
  }
}
