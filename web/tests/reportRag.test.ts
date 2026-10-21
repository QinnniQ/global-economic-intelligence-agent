import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { REPORT_SOURCES } from '../src/reportCatalog';
import { searchReports, type SearchIndex } from '../src/reportSearch';
import { loadExcerpts, selectExcerpt } from '../worker/reportExcerpts';
import worker from '../worker/index';

const root = new URL('../public/', import.meta.url);
const index = JSON.parse(readFileSync(new URL('report-search-index.v1.json', root), 'utf8')) as SearchIndex;
const assets = { fetch: async (request: Request) => {
  const name = new URL(request.url).pathname.split('/').at(-1);
  return Response.json(JSON.parse(readFileSync(new URL(`report-pages.v1/${name}`, root), 'utf8')));
} } as unknown as Fetcher;

describe('no-charge report retrieval', () => {
  it('keeps page assets tied to verified catalog hashes and counts', () => {
    for (const report of REPORT_SOURCES) {
      const data = JSON.parse(readFileSync(new URL(`report-pages.v1/${report.id}.json`, root), 'utf8'));
      expect(data.id).toBe(report.id);
      expect(data.sha256).toBe(report.sha256);
      expect(data.pages).toHaveLength(report.pages);
    }
  });
  it('selects short relevant passages and preserves publisher page links', async () => {
    expect(selectExcerpt('The meeting starts today. Inflation risks remain elevated in Europe as energy prices rise. Growth is slower.', 'inflation risks')).toMatch(/Inflation risks/);
    const hits = searchReports(index, 'Netherlands inflation', 5);
    const excerpts = await loadExcerpts('Netherlands inflation', hits.map(hit => ({ reportId: hit.reportId, page: hit.page })), 'https://example.test', assets);
    expect(excerpts.length).toBeGreaterThan(0);
    expect(excerpts.length).toBeLessThanOrEqual(5);
    expect(excerpts.every(item => item.url.endsWith(`#page=${item.page}`) && item.text.length <= 721)).toBe(true);
  });
  it('prefers the actual country section over incidental country mentions', () => {
    const hits = searchReports(index, 'What do recent reports say about growth risks for the Netherlands?', 5, true);
    expect(hits[0]).toMatchObject({ reportId: 'ec_forecast_2026', page: 138 });
    expect(hits).toHaveLength(1);
    const forecast = JSON.parse(readFileSync(new URL('report-pages.v1/ec_forecast_2026.json', root), 'utf8'));
    const excerpt = selectExcerpt(forecast.pages[137], 'What do recent reports say about growth risks for the Netherlands?');
    expect(excerpt).toMatch(/Netherlands|NETHERLANDS/);
    expect(excerpt).not.toMatch(/Graph III/);
  });
  it('rejects unknown pages and blocks direct corpus downloads and paid RAG routes', async () => {
    expect(await loadExcerpts('Netherlands inflation', [{ reportId: 'unknown', page: 1 }, { reportId: 'ecb', page: 10000 }], 'https://example.test', assets)).toEqual([]);
    const env = { ASSETS: assets } as unknown as Parameters<typeof worker.fetch>[1];
    const ctx = { waitUntil: () => undefined } as unknown as Parameters<typeof worker.fetch>[2];
    expect((await worker.fetch(new Request('https://example.test/report-pages.v1/ecb.json'), env, ctx)).status).toBe(404);
    expect((await worker.fetch(new Request('https://example.test/api/rag', { method: 'POST' }), env, ctx)).status).toBe(404);
  });
});
