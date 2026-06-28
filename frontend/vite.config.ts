import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// base: './' makes built asset paths relative, so the SPA loads correctly when
// served by the local FastAPI server on any ephemeral port.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist' },
  server: {
    // Dev only: `npm run dev` (HMR) proxies /api to the backend.
    // Run the backend with CONVERTN2C_PORT=8756 to match.
    proxy: {
      '/api': 'http://127.0.0.1:8756',
    },
  },
})
