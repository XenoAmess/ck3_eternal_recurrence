import { readFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(process.argv[2] ?? 'dist')
const forbidden = [
  '/api/ck3/coat-of-arms',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
  'VITE_ENABLE_CK3_COMPANION',
  'VITE_CK3_COMPANION_URL',
]

async function files(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const nested = await Promise.all(entries.map((entry) => {
    const path = resolve(directory, entry.name)
    return entry.isDirectory() ? files(path) : [path]
  }))
  return nested.flat()
}

const matches = []
for (const path of await files(root)) {
  const content = await readFile(path)
  for (const marker of forbidden) {
    if (content.includes(Buffer.from(marker))) matches.push({ path, marker })
  }
}

if (matches.length) {
  for (const match of matches) console.error(`${match.path}: forbidden production marker ${match.marker}`)
  process.exitCode = 1
} else {
  console.log(`production boundary passed: ${root} contains none of ${forbidden.length} forbidden markers`)
}
