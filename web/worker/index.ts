import { COUNTRIES, INDICATORS, detectIndicators, isCountry, isIndicator, resolveCountry, type Country, type Indicator, type Series } from '../src/domain';
import { analyse } from './analysis';
import { fetchSeries, UpstreamError } from './worldbank';
import { demoSeries } from '../src/demo';
import { buildAnalysis } from './analysis';

interface Env { ASSETS: Fetcher; }
const json = (data: unknown, status = 200, id?: string) => Response.json(data, { status, headers: { 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', ...(id ? { 'x-request-id': id } : {}) } });
const problem = (message: string, status = 400, id?: string) => json({ error: message, requestId: id }, status, id);
const validYear = (n: number) => Number.isInteger(n) && n >= 1960 && n <= new Date().getUTCFullYear();
const buckets = new Map<string, { minute: number; count: number }>();
function allowRequest(request: Request, route: string): boolean {
  // Fast local guard. An account-level Cloudflare rule is required for global limits.
  const minute = Math.floor(Date.now() / 60000);
  if (buckets.size > 5000) buckets.clear();
  const key = `${request.headers.get('CF-Connecting-IP') ?? 'local'}:${route}`;
  const bucket = buckets.get(key);
  if (!bucket || bucket.minute !== minute) { buckets.set(key, { minute, count: 1 }); return true; }
  bucket.count++;
  return bucket.count <= (route === 'series' ? 60 : 12);
}

async function loadLiveSeries(country: Country, indicator: Indicator, start: number, end: number, origin: string, ctx: ExecutionContext): Promise<Series> {
  const cache = (caches as unknown as { default: Cache }).default;
  const key = new Request(`${origin}/api/series?country=${country}&indicator=${indicator}&start=${start}&end=${end}`);
  const cached = await cache.match(key);
  if (cached) return { ...await cached.json() as Series, cacheStatus: 'cached' };
  const series = await fetchSeries(country, indicator, start, end);
  ctx.waitUntil(cache.put(key, new Response(JSON.stringify(series), { headers: { 'cache-control': 'public, max-age=21600' } })));
  return { ...series, cacheStatus: 'network' };
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const requestId = crypto.randomUUID();
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/api/')) return env.ASSETS.fetch(request);
    try {
      if (url.pathname === '/api/health' && request.method === 'GET') return json({ status: 'ok', upstreamChecked: false, modelGenerationEnabled: false }, 200, requestId);
      if (url.pathname === '/api/catalog' && request.method === 'GET') return json({ countries: COUNTRIES, indicators: INDICATORS, modelGenerationEnabled: false }, 200, requestId);
      if (url.pathname === '/api/series' && request.method === 'GET') {
        if (!allowRequest(request, 'series')) return problem('Request limit reached. Try again shortly.', 429, requestId);
        const country = (url.searchParams.get('country') ?? '').toUpperCase();
        const indicator = url.searchParams.get('indicator') ?? '';
        const start = Number(url.searchParams.get('start') ?? 2000), end = Number(url.searchParams.get('end') ?? new Date().getUTCFullYear());
        const mode = url.searchParams.get('mode') ?? 'live';
        if (!isCountry(country) || !isIndicator(indicator) || !validYear(start) || !validYear(end) || start > end || end - start > 65 || !['demo', 'live'].includes(mode)) return problem('Unsupported country, indicator, date range, or mode.', 400, requestId);
        if (mode === 'demo') return json(demoSeries(country, indicator, start, end), 200, requestId);
        return json(await loadLiveSeries(country, indicator, start, end, url.origin, ctx), 200, requestId);
      }
      if (url.pathname === '/api/analysis' && request.method === 'POST') {
        if (!allowRequest(request, 'analysis')) return problem('Request limit reached. Try again shortly.', 429, requestId);
        const raw = await request.text();
        if (raw.length > 1500) return problem('Question too long.', 413, requestId);
        let body: { question?: unknown; country?: unknown; mode?: unknown } | null;
        try { body = JSON.parse(raw); } catch { return problem('Invalid request body.', 400, requestId); }
        if (!body || typeof body !== 'object' || typeof body.question !== 'string' || typeof body.country !== 'string' || !isCountry(body.country)) return problem('Select a supported country and enter a question.', 400, requestId);
        if (body.mode !== 'demo' && body.mode !== 'live') return problem('Select saved demonstration or live data.', 400, requestId);
        const question = body.question.trim();
        const country = body.country;
        if (question.length < 8 || question.length > 500) return problem('Enter a question between 8 and 500 characters.', 400, requestId);
        if (body.mode === 'demo') {
          const resolved = resolveCountry(question, country);
          const codes = detectIndicators(question);
          if (!codes.length) return problem('This release supports GDP growth, consumer-price inflation, and unemployment. Try a question about one of those indicators.', 400, requestId);
          const analysis = buildAnalysis(question, resolved, codes.map(code => demoSeries(resolved, code)));
          analysis.limitations.unshift('Saved demonstration: values are rounded to one decimal and have one observation per indicator. Source pages were reviewed on 15 October 2026.');
          return json(analysis, 200, requestId);
        }
        return json(await analyse(question, country, (code, indicator, start, end) => loadLiveSeries(code, indicator, start, end, url.origin, ctx)), 200, requestId);
      }
      return problem('Not found.', 404, requestId);
    } catch (error) {
      const status = error instanceof UpstreamError ? error.status : error instanceof Error && /Select|handles one country|outside this release|names |between 8|This release supports/.test(error.message) ? 400 : 503;
      const message = error instanceof Error && status !== 503 ? error.message : 'The service could not complete this request. Try again shortly.';
      console.error(JSON.stringify({ requestId, path: url.pathname, status, errorType: error instanceof Error ? error.name : 'Unknown' }));
      return problem(message, status, requestId);
    }
  },
} satisfies ExportedHandler<Env>;
