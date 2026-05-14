import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [vue()],
    server: {
      host: env.VITE_HOST || '0.0.0.0',
      port: parseInt(env.VITE_PORT) || 5173,
    }
  }
})
