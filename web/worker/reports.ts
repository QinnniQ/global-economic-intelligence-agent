import type { Country, Evidence, Indicator } from '../src/domain';

// Manually reviewed locations in the versioned repository PDFs. This small index
// is deterministic; it must not be mistaken for a complete semantic retrieval corpus.
const PASSAGES: { evidence: Evidence; countries: Country[]; indicators: Indicator[]; terms: RegExp }[] = [
  {
    evidence: {
      id: 'ECB-2025-07-P11', kind: 'report', label: 'Economic Bulletin, Issue 7 / 2025',
      url: 'https://www.ecb.europa.eu/pub/pdf/ecbu/eb202507.en.pdf#page=11',
      publicationDate: '2025-11-13', page: 11, ingestionVersion: 1,
      documentChecksum: 'cea88accb46726306dae6dab81937d6a5efdcfd4f302e94ed2fc9fdf6bba4e4b',
      detail: 'European Central Bank · page 11 · published 13 November 2025 · quarterly real GDP context, not the annual World Bank series',
      passage: 'real GDP increased by 0.6% in Spain, by 0.5% in France and by 0.4% in the Netherlands',
    }, countries: ['NL','FR'], indicators: ['NY.GDP.MKTP.KD.ZG'], terms: /\b(gdp|growth|economy|economic|macro|overview|indicators?)\b/i,
  },
  {
    evidence: {
      id: 'OECD-2025-09-P13', kind: 'report', label: 'OECD Economic Outlook, Interim Report, September 2025',
      url: 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/09/oecd-economic-outlook-interim-report-september-2025_ae3d418b/67b10c01-en.pdf#page=13',
      publicationDate: '2025-09-23', page: 13, ingestionVersion: 1,
      documentChecksum: 'f3d64751363d12e1dd140b69ebb2c81ac7697f27ec6bf55194ce9f4484fb96df',
      detail: 'OECD · page 13 · published 23 September 2025 · contemporaneous labour-market commentary, not the modeled annual series',
      passage: 'the unemployment rate has increased in South Africa, India, Canada, France, Australia, Germany and the United States',
    }, countries: ['DE','FR','US'], indicators: ['SL.UEM.TOTL.ZS'], terms: /\b(unemployment|jobless|labou?r|economy|economic|macro|overview|indicators?)\b/i,
  },
];

export function retrieveReports(question: string, country: Country, indicators: Indicator[]): Evidence[] {
  return PASSAGES.filter(p => p.countries.includes(country) && p.indicators.some(code => indicators.includes(code)) && p.terms.test(question)).map(p => ({ ...p.evidence }));
}

export function validateEvidenceIds(ids: string[], evidence: Evidence[]): boolean {
  const valid = new Set(evidence.map(e => e.id));
  return ids.every(id => valid.has(id));
}
