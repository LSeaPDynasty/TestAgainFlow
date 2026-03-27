import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Disable TypeScript checking in build
    rollupOptions: {
      onwarn(warning, warn) {
        // Suppress warnings
        if (warning.code === 'THIS_IS_UNDEFINED') return
        warn(warning)
      }
    }
  }
})
