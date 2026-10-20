/** Page-level lexical search over the verified publisher PDFs. No model calls. */
export type SearchIndex = {
  version: 1;
  stopwords: string[];
  reports: { id: string; title: string; publisher: string; issue: string; url: string; sha256: string }[];
  pages: [reportIndex: number, pdfPage: number, length: number][];
  postings: Record<string, [pageIndex: number, frequency: number][]>;
};

export type ReportHit = {
  reportId: string; title: string; publisher: string; issue: string;
  page: number; url: string; matchedTerms: string[]; score: number;
};

export async function loadReportIndex(fetcher: typeof fetch = fetch): Promise<SearchIndex> {
  const response = await fetcher('/report-search-index.v1.json');
  if (!response.ok) throw new Error('The report search index could not be loaded. Try again shortly.');
  const index = await response.json() as SearchIndex;
  if (index.version !== 1 || !Array.isArray(index.pages) || !Array.isArray(index.reports) || !index.postings || !Array.isArray(index.stopwords)) {
    throw new Error('The report search index is invalid.');
  }
  return index;
}

export function searchReports(index: SearchIndex, query: string, limit = 8): ReportHit[] {
  const stopwords = new Set(index.stopwords);
  const normalized = query.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const queryTerms = [...new Set((normalized.match(/[a-z][a-z0-9]{1,23}/g) ?? []).filter(term => !stopwords.has(term)))].slice(0, 8);
  if (!queryTerms.length) return [];
  const total = index.pages.length;
  const averageLength = index.pages.reduce((sum, page) => sum + page[2], 0) / Math.max(total, 1);
  const reportTerms = index.reports.map(report => new Set((`${report.title} ${report.publisher} ${report.issue}`).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().match(/[a-z][a-z0-9]{1,23}/g) ?? []));
  const scores = new Map<number, { score: number; terms: string[] }>();
  for (const term of queryTerms) {
    const posting = index.postings[term] ?? [];
    const idf = Math.log(1 + (total - posting.length + 0.5) / (posting.length + 0.5));
    for (const [pageId, frequency] of posting) {
      const page = index.pages[pageId];
      if (!page) continue;
      const lengthRatio = page[2] / Math.max(averageLength, 1);
      const bm25 = idf * (frequency * 2.2) / (frequency + 1.2 * (0.25 + 0.75 * lengthRatio));
      const current = scores.get(pageId) ?? { score: 0, terms: [] };
      current.score += bm25;
      current.terms.push(term);
      scores.set(pageId, current);
    }
  }
  const ranked = [...scores.entries()].map(([pageId, match]) => {
    const [reportIndex, page] = index.pages[pageId];
    const report = index.reports[reportIndex];
    const coverage = match.terms.length / queryTerms.length;
    const year = Number(report.issue.match(/20\d{2}/)?.[0] ?? 0);
    const metadataMatches = queryTerms.filter(term => reportTerms[reportIndex].has(term)).length;
    const score = (match.score * (1 + coverage * 0.7) + metadataMatches * 2.5) * (year >= 2026 ? 1.05 : 1);
    return { reportId: report.id, title: report.title, publisher: report.publisher, issue: report.issue,
      page, url: `${report.url}#page=${page}`, matchedTerms: match.terms, score };
  }).sort((a, b) => b.score - a.score || a.reportId.localeCompare(b.reportId) || a.page - b.page);
  const perReport = new Map<string, number>();
  return ranked.filter(hit => {
    const used = perReport.get(hit.reportId) ?? 0;
    if (used >= 2) return false;
    perReport.set(hit.reportId, used + 1);
    return true;
  }).slice(0, limit);
}
