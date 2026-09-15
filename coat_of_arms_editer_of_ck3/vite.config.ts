import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  define: {
    __COA_CACHE_VERSION__: JSON.stringify(process.env.VITE_COA_CACHE_VERSION || '0.1.0-local'),
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
