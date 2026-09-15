/// <reference lib="webworker" />

import { fitImageToCoatOfArms, type ImageFitProgress } from './imageFitter'

type Request = Parameters<typeof fitImageToCoatOfArms>

self.onmessage = (event: MessageEvent<Request>) => {
  try {
    const [image, patterns, emblems, options] = event.data
    const result = fitImageToCoatOfArms(image, patterns, emblems, {
      ...options,
      onProgress: (progress: ImageFitProgress) => self.postMessage({ kind: 'progress', progress }),
    })
    self.postMessage({ kind: 'result', ok: true, result })
  } catch (error) {
    self.postMessage({
      kind: 'result',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    })
  }
}
