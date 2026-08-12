import { defineConfig } from 'vite'

export default defineConfig({
  // Serve the root index.html directly
  root: '.',
  publicDir: 'public',
  server: {
    port: 5173,
    open: '/index.html',
    host: 'localhost',
    // Proxy API calls to FastAPI backend so no CORS issues when served via Vite
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  preview: {
    port: 4173,
    open: true,
  },
})
