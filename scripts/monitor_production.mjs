/** Check the public API from outside Cloudflare; fail the scheduled workflow on bad data. */
const base = process.env.MONITOR_BASE_URL ?? 'https://econ.nickcloud.dev';
const end = new Date().getUTCFullYear();
const checks = [
  { name: 'app health', path: '/api/health', valid: body => body.status === 'ok' },
  ...[
    ['NL', 'NY.GDP.MKTP.KD.ZG'],
    ['US', 'FP.CPI.TOTL.ZG'],
    ['GB', 'SL.UEM.TOTL.ZS'],
  ].map(([country, indicator]) => ({
    name: `${country} ${indicator}`,
    path: `/api/series?country=${country}&indicator=${indicator}&start=${end - 3}&end=${end}&mode=live`,
    valid: body => body.country === country && body.indicator === indicator &&
      Array.isArray(body.observations) && body.observations.some(row => Number.isInteger(row.year) && Number.isFinite(row.value)),
  })),
];

export async function monitor(fetcher = fetch) {
  const results = [];
  for (const check of checks) {
    let failure = 'unknown';
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const response = await fetcher(new URL(check.path, base), { signal: AbortSignal.timeout(20000) });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const body = await response.json();
        if (!check.valid(body)) throw new Error('Response failed schema or observation check');
        results.push({ name: check.name, ok: true, requestId: response.headers.get('x-request-id') });
        failure = '';
        break;
      } catch (error) {
        failure = error instanceof Error ? error.message : 'Unknown error';
        if (attempt === 0) await new Promise(resolve => setTimeout(resolve, 1500));
      }
    }
    if (failure) results.push({ name: check.name, ok: false, error: failure });
  }
  return results;
}

if (process.argv[1] && new URL(import.meta.url).pathname.toLowerCase().endsWith(process.argv[1].replaceAll('\\', '/').toLowerCase())) {
  const results = await monitor();
  for (const result of results) console.log(JSON.stringify(result));
  if (results.some(result => !result.ok)) process.exitCode = 1;
}
