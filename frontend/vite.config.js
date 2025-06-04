import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Proxy API requests to Flask backend
      '/get': 'http://192.168.0.141:5000',
      '/set': 'http://localhost:5000',
      '/set_Pins': 'http://localhost:5000',
      '/set_Kasa': 'http://localhost:5000',
      '/set_stage': 'http://localhost:5000',
      '/find_kasa': 'http://localhost:5000',
      '/api': 'http://localhost:5000'
    }
  }
});
