/// <reference lib="webworker" />

import { fitImageToCoatOfArms } from './imageFitter'

type Request = Parameters<typeof fitImageToCoatOfArms>

self.onmessage = (event: MessageEvent<Request>) => {
  try {
    self.postMessage({ ok: true, result: fitImageToCoatOfArms(...event.data) })
  } catch (error) {
    self.postMessage({ ok: false, error: error instanceof Error ? error.message : String(error) })
  }
}

