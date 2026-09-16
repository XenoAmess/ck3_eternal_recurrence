import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { execFileSync } from 'node:child_process'

const buildTimestamp = process.env.VITE_COA_BUILD_TIMESTAMP || new Date().toISOString()
const localGitHash = () => {
  try {
    return execFileSync('git', ['rev-parse', '--short=8', 'HEAD'], { encoding: 'utf8' }).trim()
  } catch {
    return '00000000'
  }
}
const gitHash = (
  process.env.VITE_COA_GIT_HASH
  || process.env.VITE_COA_CACHE_VERSION
  || localGitHash()
).slice(0, 8)

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  define: {
    __COA_CACHE_VERSION__: JSON.stringify(process.env.VITE_COA_CACHE_VERSION || '0.1.0-local'),
    __COA_BUILD_TIMESTAMP__: JSON.stringify(buildTimestamp),
    __COA_GIT_HASH__: JSON.stringify(gitHash),
  },
  plugins: [vue()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'element-plus',
              test: /node_modules[\\/]element-plus/,
              priority: 2,
            },
            {
              name: 'vue-runtime',
              test: /node_modules[\\/](?:@vue|vue)[\\/]/,
              priority: 1,
            },
          ],
        },
      },
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
})
