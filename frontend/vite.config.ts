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
    host: true, // Questo permette al server di essere accessibile da altri dispositivi sulla stessa rete, utile per test su mobile.
    allowedHosts: [
      'vapter.szini.it',
      // Puoi aggiungere altri host qui se ne hai bisogno, ad esempio:
      // 'localhost',
      // '192.168.1.xxx', // Il tuo indirizzo IP locale se lo usi per test
    ],
    //host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://api_gateway:8080',
        changeOrigin: true,
      },
    },
  },
})