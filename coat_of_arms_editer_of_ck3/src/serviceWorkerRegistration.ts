declare const __COA_CACHE_VERSION__: string

export async function registerCoatOfArmsServiceWorker(): Promise<ServiceWorkerRegistration | undefined> {
  if (!('serviceWorker' in navigator)) return undefined
  const baseUrl = new URL(import.meta.env.BASE_URL, window.location.href)
  if (baseUrl.origin !== window.location.origin) return undefined
  const workerUrl = new URL('coat-of-arms-sw.js', baseUrl)
  workerUrl.searchParams.set('v', __COA_CACHE_VERSION__)
  return navigator.serviceWorker.register(workerUrl, { scope: baseUrl.pathname })
}
