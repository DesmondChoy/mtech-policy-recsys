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

// Folder mappings (corrected: use processed transcripts only)
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
    src: path.join(backendBase, 'data', 'transcripts', 'processed'),
    dest: path.join(publicBase, 'data', 'transcripts', 'processed')
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

// === Transcript Index Generation ===
const transcriptsProcessedDir = path.join(backendBase, 'data', 'transcripts', 'processed');
const transcriptsIndexPath = path.join(publicBase, 'transcripts_index.json');
const customerIdsPath = path.join(publicBase, 'customer_ids.json');
let transcriptIndex = {};

if (fs.existsSync(transcriptsProcessedDir)) {
  for (const fname of fs.readdirSync(transcriptsProcessedDir)) {
    if (fname.endsWith('.json')) {
      // UUID is the last section before .json, after the last underscore
      const uuid = fname.replace(/^.*_([^_]+-[^_]+-[^_]+-[^_]+-[^_]+)\.json$/, '$1');
      if (uuid && uuid.length > 10) {
        transcriptIndex[uuid] = fname;
      }
    }
  }
  fs.writeFileSync(transcriptsIndexPath, JSON.stringify(transcriptIndex, null, 2));
  console.log(`Transcript index generated at ${transcriptsIndexPath}`);

  // Write customer_ids.json for dropdown (always overwrite)
  const customerIds = Object.keys(transcriptIndex);
  fs.writeFileSync(customerIdsPath, JSON.stringify(customerIds, null, 2));
  console.log(`Customer IDs written to ${customerIdsPath}`);
} else {
  console.warn(`Processed transcripts directory does not exist: ${transcriptsProcessedDir}`);
}

// === Report Index Generation ===
const resultsPublicDir = path.join(publicBase, 'results');

if (fs.existsSync(resultsPublicDir)) {
  console.log(`Scanning ${resultsPublicDir} for report indices...`);
  for (const uuidEntry of fs.readdirSync(resultsPublicDir, { withFileTypes: true })) {
    if (uuidEntry.isDirectory()) {
      const uuidDirPath = path.join(resultsPublicDir, uuidEntry.name);
      const reportFiles = [];
      try {
        for (const reportEntry of fs.readdirSync(uuidDirPath, { withFileTypes: true })) {
          // Match filenames like policy_comparison_report_INSURER_uuid.md or policy_comparison_report_INSURER.md
          // Be flexible with potential UUID presence at the end
          if (reportEntry.isFile() && reportEntry.name.startsWith('policy_comparison_report_') && reportEntry.name.endsWith('.md')) {
            // Exclude the main recommendation report if it follows a similar pattern by mistake
            if (!reportEntry.name.startsWith('policy_comparison_report_recommendation_report_')) {
               reportFiles.push(reportEntry.name);
            }
          }
        }
        if (reportFiles.length > 0) {
          const indexPath = path.join(uuidDirPath, 'index.json');
          fs.writeFileSync(indexPath, JSON.stringify(reportFiles.sort(), null, 2));
          console.log(`  - Created index for ${uuidEntry.name} at ${indexPath}`);
        } else {
          // console.log(`  - No reports found for ${uuidEntry.name}, skipping index.`);
        }
      } catch (err) {
        console.error(`  - Error processing directory ${uuidDirPath}:`, err);
      }
    }
  }
  console.log('Report index generation complete.');
} else {
  console.warn(`Public results directory does not exist: ${resultsPublicDir}`);
}
