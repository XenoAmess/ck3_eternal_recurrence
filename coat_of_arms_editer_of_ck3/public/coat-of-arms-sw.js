const CACHE_PREFIX = 'ck3-coa-pages-'
const version = new URL(self.location.href).searchParams.get('v') || 'unversioned'
const CACHE_NAME = `${CACHE_PREFIX}${version}`
const scopeUrl = new URL(self.registration.scope)

async function putSuccessful(cache, request, response) {
  if (response && response.ok) await cache.put(request, response.clone())
  return response
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME)
  return (await cache.match(request))
    || putSuccessful(cache, request, await fetch(request))
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME)
  try {
    return await putSuccessful(cache, request, await fetch(request))
  } catch (error) {
    const cached = await cache.match(request)
      || (request.mode === 'navigate' ? await cache.match(scopeUrl.href) : undefined)
    if (cached) return cached
    throw error
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME)
    try {
      await putSuccessful(cache, scopeUrl.href, await fetch(scopeUrl.href, { cache: 'reload' }))
    } finally {
      await self.skipWaiting()
    }
  })())
})

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys()
    await Promise.all(keys
      .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map((key) => caches.delete(key)))
    await self.clients.claim()
  })())
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== scopeUrl.origin || !url.pathname.startsWith(scopeUrl.pathname)) return

  const relativePath = url.pathname.slice(scopeUrl.pathname.length)
  const immutable = relativePath.startsWith('assets/')
    || /^asset-packs\/[^/]+\/assets\/[0-9a-f]{64}\.(?:dds|rgba)$/.test(relativePath)
  event.respondWith(immutable ? cacheFirst(request) : networkFirst(request))
})
