import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server proxies the real control API (scripts/serve_web.py on :8502).
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: { '/api': { target: 'http://127.0.0.1:8502', changeOrigin: true } } },
  build: { outDir: 'dist', sourcemap: false, emptyOutDir: true }
});
