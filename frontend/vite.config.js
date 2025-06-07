import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Proxy API requests to Flask backend
      '/get': 'http://192.168.0.141:5000',
      '/set': 'http://192.168.0.141:5000',
      '/set_Pins': 'http://192.168.0.141:5000',
      '/set_Kasa': 'http://192.168.0.141:5000',
      '/set_stage': 'http://192.168.0.141:5000',
      '/find_kasa': 'http://192.168.0.141:5000',
      '/api': 'http://192.168.0.141:5000',
      '/light_schedule': 'http://192.168.0.141:5000',
      '/ph_calibration': 'http://192.168.0.141:5000',
      '/ph_calibration_point': 'http://192.168.0.141:5000',
      '/email_settings': 'http://192.168.0.141:5000'
    }
  }
});
