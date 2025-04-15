const fs = require('fs');
const path = require('path');

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

const projectRoot = path.resolve(__dirname, '../..');
const backendBase = projectRoot;
const publicBase = path.join(projectRoot, 'ux-webapp', 'public');

// Folder mappings
const mappings = [
  {
    src: path.join(backendBase, 'results'),
    dest: path.join(publicBase, 'results')
  },
  {
    src: path.join(backendBase, 'data', 'extracted_customer_requirements'),
    dest: path.join(publicBase, 'data', 'extracted_customer_requirements')
  },
  {
    src: path.join(backendBase, 'data', 'transcripts', 'raw', 'synthetic'),
    dest: path.join(publicBase, 'data', 'transcripts', 'raw', 'synthetic')
  },
  {
    src: path.join(backendBase, 'data', 'policies', 'raw'),
    dest: path.join(publicBase, 'data', 'policies', 'raw')
  }
];

for (const { src, dest } of mappings) {
  copyDir(src, dest);
  console.log(`Synced: ${src} -> ${dest}`);
}

console.log('Public asset sync complete.');
