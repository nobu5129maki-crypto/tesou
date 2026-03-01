/**
 * Vercel ビルド用 - public のファイルを dist にコピー
 */
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');
const distDir = path.join(__dirname, 'dist');

if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

const files = ['index.html', 'styles.css', 'app.js', 'manifest.json', 'sw.js', 'icon-192.png', 'icon-512.png'];
files.forEach(file => {
  const src = path.join(publicDir, file);
  const dest = path.join(distDir, file);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log('Copied:', file);
  }
});

console.log('Build complete');
