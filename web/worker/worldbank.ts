import { COUNTRIES, INDICATORS, type Country, type Indicator, type Observation, type Series } from '../src/domain';

export class UpstreamError extends Error { constructor(message: string, public status = 502) { super(message); } }

export function parseWorldBank(payload: unknown, country: Country, indicator: Indicator, start: number, end: number, retrievedAt: string): Series {
  if (!Array.isArray(payload) || payload.length !== 2 || !payload[0] || typeof payload[0] !== 'object' || !Array.isArray(payload[1])) {
    throw new UpstreamError('World Bank returned an unexpected response.');
  }
  const meta = payload[0] as Record<string, unknown>;
  const pages = Number(meta.pages);
  if (!Number.isInteger(pages) || pages < 1 || pages > 20) throw new UpstreamError('World Bank pagination metadata is invalid.');
  const observations: Observation[] = [];
  for (const row of payload[1]) {
    if (!row || typeof row !== 'object') continue;
    const r = row as Record<string, unknown>;
    const year = Number(r.date);
    if (!Number.isInteger(year) || year < start || year > end || typeof r.value !== 'number') continue;
    const value = r.value;
    if (Number.isFinite(value)) observations.push({ year, value });
  }
  observations.sort((a, b) => b.year - a.year);
  const unique = observations.filter((o, i) => i === 0 || o.year !== observations[i - 1].year);
  const sourceUrl = `https://data.worldbank.org/indicator/${indicator}?locations=${country}`;
  return { country, indicator, provider: 'World Bank', frequency: 'annual', name: INDICATORS[indicator].name,
    definition: INDICATORS[indicator].definition, unit: INDICATORS[indicator].unit, sourceUrl,
    retrievedAt, providerUpdatedAt: typeof meta.lastupdated === 'string' ? meta.lastupdated : null,
    observations: unique, stale: false };
}

export async function fetchSeries(country: Country, indicator: Indicator, start: number, end: number, fetcher: typeof fetch = fetch): Promise<Series> {
  if (!Object.hasOwn(COUNTRIES, country) || !Object.hasOwn(INDICATORS, indicator)) throw new UpstreamError('Unsupported country or indicator.', 400);
  const url = new URL(`https://api.worldbank.org/v2/country/${country}/indicator/${indicator}`);
  url.search = new URLSearchParams({ format: 'json', date: `${start}:${end}`, per_page: '1000', page: '1' }).toString();
  const retrievedAt = new Date().toISOString();
  const getPage = async (): Promise<unknown> => {
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const response = await fetcher(url, { signal: AbortSignal.timeout(8000), headers: { accept: 'application/json' } });
        if (response.status === 429 || response.status >= 500) throw new UpstreamError('World Bank is temporarily unavailable.', 503);
        if (!response.ok) throw new UpstreamError('World Bank could not provide this series.');
        return await response.json();
      } catch (error) {
        if (attempt === 1 || error instanceof UpstreamError && error.status !== 503) throw error instanceof UpstreamError ? error : new UpstreamError('World Bank did not respond in time.', 503);
        await new Promise(r => setTimeout(r, 200));
      }
    }
    throw new UpstreamError('World Bank is temporarily unavailable.', 503);
  };
  const first = await getPage();
  const base = parseWorldBank(first, country, indicator, start, end, retrievedAt);
  const pages = Number((first as unknown[])[0] && ((first as unknown[])[0] as Record<string, unknown>).pages);
  for (let page = 2; page <= pages; page++) {
    url.searchParams.set('page', String(page));
    const next = parseWorldBank(await getPage(), country, indicator, start, end, retrievedAt);
    base.observations.push(...next.observations);
  }
  base.observations = [...new Map(base.observations.map(o => [o.year, o])).values()].sort((a, b) => b.year - a.year);
  return base;
}
