import fs from 'fs';
import path from 'path';

const templatePath = path.resolve('public/_redirects.template');
const redirectsPath = path.resolve('public/_redirects');

// Attempt to load from .env or .env.local files if process.env.BACKEND_URL is missing
let backendUrl = process.env.BACKEND_URL;

if (!backendUrl) {
  const envFiles = ['.env.local', '.env'];
  for (const file of envFiles) {
    const envPath = path.resolve(file);
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8');
      const match = content.match(/^BACKEND_URL=(.+)$/m);
      if (match) {
        backendUrl = match[1].trim().replace(/['"]/g, '');
        console.log(`💡 Loaded BACKEND_URL from ${file}`);
        break;
      }
    }
  }
}

if (!backendUrl) {
  console.warn('⚠️ BACKEND_URL environment variable is not set and not found in .env files. Skipping injection.');
  process.exit(0);
}

try {
  let content = fs.readFileSync(templatePath, 'utf8');
  // Handle both with and without trailing slash
  const sanitizedUrl = backendUrl.replace(/\/$/, '');
  content = content.replace(/BACKEND_URL/g, sanitizedUrl);
  fs.writeFileSync(redirectsPath, content);
  console.log(`✅ Successfully injected BACKEND_URL into _redirects: ${sanitizedUrl}`);
} catch (err) {
  console.error('❌ Failed to inject BACKEND_URL:', err.message);
  process.exit(1);
}
