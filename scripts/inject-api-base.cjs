const fs = require('fs');
const path = require('path');

const configPath = path.join(process.cwd(), '_site', 'js', 'config.js');
if (!fs.existsSync(configPath)) {
  throw new Error(`Built frontend config not found: ${configPath}`);
}

const apiBase = (process.env.WISEF_API_BASE || '').trim().replace(/\/$/, '');
const source = fs.readFileSync(configPath, 'utf8');
const marker = "'__WISEF_API_BASE__'";
if (!source.includes(marker)) {
  throw new Error('WISEF_API_BASE marker was not found in the built config');
}

fs.writeFileSync(configPath, source.replace(marker, JSON.stringify(apiBase)), 'utf8');
console.log(`WISEF_API_BASE injected: ${apiBase || '(same origin)'}`);
