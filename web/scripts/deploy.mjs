import { spawnSync } from 'node:child_process';
import { readFileSync, appendFileSync } from 'node:fs';
import { resolve } from 'node:path';

const stage = process.argv[2];
if (!['preview', 'production'].includes(stage)) throw new Error('Choose preview or production.');
const run = (command, args, env = process.env) => {
  const result = spawnSync(command, args, { stdio: 'inherit', shell: process.platform === 'win32', env });
  if (result.status !== 0) process.exit(result.status ?? 1);
};

run('npm', ['run', 'build'], { ...process.env, CLOUDFLARE_ENV: stage });
const config = resolve('dist/global_economic_intelligence_agent/wrangler.json');
const expected = stage === 'preview' ? 'global-economic-intelligence-preview' : 'global-economic-intelligence';
const actual = JSON.parse(readFileSync(config, 'utf8')).name;
if (actual !== expected) throw new Error(`Built Worker name ${actual} does not match ${expected}.`);
// Transformers.js loads ONNX WASM from its CDN at runtime. Vite also copies a
// 25.6 MiB fallback file that exceeds Cloudflare's per-asset limit; omit it.
appendFileSync(resolve('dist/client/.assetsignore'), 'ort-wasm-simd-threaded.asyncify-*.wasm\n');
run('npx', ['wrangler', 'deploy', '--config', config]);
