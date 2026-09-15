/// <reference lib="webworker" />

import {
  pruneRedundantInstances,
  type InstancePruneOptions,
  type InstancePruneProgress,
} from './coatOfArmsPruner'

type Request = Parameters<typeof pruneRedundantInstances>

self.onmessage = (event: MessageEvent<Request>) => {
  try {
    const [coatOfArms, target, pattern, coloredEmblems, surfaceMask, namedColors, options] = event.data
    const workerOptions: InstancePruneOptions = {
      ...options,
      onProgress: (progress: InstancePruneProgress) => self.postMessage({ kind: 'progress', progress }),
    }
    const result = pruneRedundantInstances(
      coatOfArms,
      target,
      pattern,
      coloredEmblems,
      surfaceMask,
      namedColors,
      workerOptions,
    )
    self.postMessage({ kind: 'result', ok: true, result })
  } catch (error) {
    self.postMessage({
      kind: 'result',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    })
  }
}
