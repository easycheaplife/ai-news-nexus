import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendUrl = env.BACKEND_URL || 'http://localhost:8000';

  return {
    plugins: [
      vue(),
      {
        name: 'log-api-url',
        configureServer(_server) {
          console.log('\n  \x1b[32m➜\x1b[0m  \x1b[1mBackend URL:\x1b[0m \x1b[36m' + backendUrl + '\x1b[0m\n');
        }
      }
    ],
    server: {
      host: env.VITE_HOST || '0.0.0.0',
      port: parseInt(env.VITE_PORT) || 5173,
      strictPort: true,
      fs: {
        strict: true,
        allow: ['..'], // Allows files in the project root and above as needed by Vite, but we'll filter them below
        deny: ['.env', '.env.*', '*.{php,cgi,pl,conf,sql,log,sh,bash,passwd,version}']
      },
      // 🛡️ Custom security middleware to intercept malicious path traversal attempts
      proxy: {
        '/api': { target: backendUrl, changeOrigin: true },
        '/f': { target: backendUrl, changeOrigin: true },
        '/media': { target: backendUrl, changeOrigin: true },
        '/etc/passwd': { 
          target: 'http://localhost', 
          bypass: (_req, res) => { 
            if (res) {
              res.statusCode = 403; 
              res.end('Forbidden'); 
            }
            return false; 
          } 
        },
        '/proc/version': { 
          target: 'http://localhost', 
          bypass: (_req, res) => { 
            if (res) {
              res.statusCode = 403; 
              res.end('Forbidden'); 
            }
            return false; 
          } 
        }
      }
    }
  }
})
