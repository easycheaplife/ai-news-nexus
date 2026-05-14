import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000';

  return {
    plugins: [
      vue(),
      {
        name: 'log-api-url',
        configureServer(_server) {
          console.log('\n  \x1b[32m➜\x1b[0m  \x1b[1mAPI URL:\x1b[0m \x1b[36m' + apiUrl + '\x1b[0m\n');
        }
      }
    ],
    server: {
      host: env.VITE_HOST || '0.0.0.0',
      port: parseInt(env.VITE_PORT) || 5173,
    }
  }
})
