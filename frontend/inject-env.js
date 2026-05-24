import fs from 'fs';
import path from 'path';

const redirectsPath = path.resolve('public/_redirects');
const backendUrl = process.env.BACKEND_URL;

if (!backendUrl) {
  console.warn('⚠️ BACKEND_URL environment variable is not set. Skipping injection.');
  process.exit(0);
}

try {
  let content = fs.readFileSync(redirectsPath, 'utf8');
  // Handle both with and without trailing slash
  const sanitizedUrl = backendUrl.replace(/\/$/, '');
  content = content.replace(/BACKEND_URL/g, sanitizedUrl);
  fs.writeFileSync(redirectsPath, content);
  console.log(`✅ Successfully injected BACKEND_URL into _redirects: ${sanitizedUrl}`);
} catch (err) {
  console.error('❌ Failed to inject BACKEND_URL:', err.message);
  process.exit(1);
}
