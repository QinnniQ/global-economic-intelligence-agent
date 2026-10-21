import { REPORT_SOURCES } from '../src/reportCatalog';

export type PageRequest = { reportId: string; page: number };
export type PageExcerpt = { reportId: string; title: string; publisher: string; issue: string; page: number; url: string; text: string };

const byId = new Map(REPORT_SOURCES.map(source => [source.id, source]));
const words = (value: string) => [...new Set((value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').match(/[a-z][a-z0-9]{2,23}/g) ?? []).filter(word => !['the', 'for', 'what', 'about', 'does', 'from', 'with', 'have', 'this', 'that', 'their', 'there', 'which', 'report', 'reports', 'recent', 'latest', 'say', 'said', 'economic', 'economy'].includes(word)))];

export function selectExcerpt(pageText: string, question: string): string {
  const terms = words(question);
  const sentences = pageText.split(/(?<=[.!?])\s+(?=[A-Z0-9])/).map(sentence => sentence.trim()).filter(sentence => sentence.length >= 45 && sentence.length <= 650 && !/\b(?:Graph|Table)\s+[IVX\d]/i.test(sentence));
  const scored = sentences.map((sentence, index) => {
    const lower = sentence.toLowerCase();
    const matched = terms.filter(term => new RegExp(`\\b${term}\\b`).test(lower));
    return { sentence, index, score: matched.length * 3 + (matched.length === terms.length && terms.length ? 2 : 0) - sentence.length / 1200 };
  }).sort((a, b) => b.score - a.score || a.index - b.index);
  return scored.slice(0, 2).filter(item => item.score > 0 && item.score >= scored[0].score * 0.7).map(item => item.sentence.slice(0, 360)).join(' ') || '';
}

export async function loadExcerpts(question: string, requested: PageRequest[], origin: string, assets: Fetcher): Promise<PageExcerpt[]> {
  const unique = [...new Map(requested.map(item => [`${item.reportId}:${item.page}`, item])).values()].slice(0, 5);
  const valid = unique.filter(item => Number.isInteger(item.page) && item.page > 0 && item.page <= (byId.get(item.reportId)?.pages ?? 0));
  const reportIds = [...new Set(valid.map(item => item.reportId))];
  const loaded = await Promise.all(reportIds.map(async id => {
    const response = await assets.fetch(new Request(`${origin}/report-pages.v1/${id}.json`));
    if (!response.ok) throw new Error('The report text index could not be loaded.');
    const data = await response.json() as { version?: unknown; id?: unknown; sha256?: unknown; pages?: unknown };
    const report = byId.get(id)!;
    if (data.version !== 1 || data.id !== id || data.sha256 !== report.sha256 || !Array.isArray(data.pages) || data.pages.length !== report.pages) throw new Error('The report text index is invalid.');
    return [id, data.pages] as const;
  }));
  const pages = new Map(loaded);
  return valid.flatMap(item => {
    const report = byId.get(item.reportId)!;
    const raw = pages.get(item.reportId)?.[item.page - 1];
    const text = typeof raw === 'string' ? selectExcerpt(raw, question) : '';
    return text ? [{ reportId: report.id, title: report.title, publisher: report.publisher, issue: report.issue, page: item.page, url: `${report.url}#page=${item.page}`, text }] : [];
  });
}
