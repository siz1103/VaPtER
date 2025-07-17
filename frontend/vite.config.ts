import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['vapter.szini.it', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: 'http://api_gateway:8080',
        changeOrigin: true,
      },
    },
  },
})