export const COUNTRIES = {
  NL: 'Netherlands', DE: 'Germany', FR: 'France', GB: 'United Kingdom', US: 'United States',
} as const;
export type Country = keyof typeof COUNTRIES;

export const INDICATORS = {
  'NY.GDP.MKTP.KD.ZG': { short: 'GDP growth', name: 'GDP growth (annual %)', unit: '%', definition: 'Annual percentage growth of GDP at market prices based on constant local currency.' },
  'FP.CPI.TOTL.ZG': { short: 'Inflation', name: 'Inflation, consumer prices (annual %)', unit: '%', definition: 'Annual percentage change in the consumer price index.' },
  'SL.UEM.TOTL.ZS': { short: 'Unemployment', name: 'Unemployment, total (% of labor force), modeled ILO estimate', unit: '% of labor force', definition: 'Share of the labor force without work, available for work and seeking work; modeled ILO estimate.' },
} as const;
export type Indicator = keyof typeof INDICATORS;
export const INDICATOR_CODES = Object.keys(INDICATORS) as Indicator[];

export type Observation = { year: number; value: number };
export type Series = {
  country: Country; indicator: Indicator; provider: 'World Bank'; frequency: 'annual';
  name: string; definition: string; unit: string; sourceUrl: string; retrievedAt: string;
  providerUpdatedAt: string | null; observations: Observation[]; stale: boolean; cacheStatus?: 'cached' | 'network';
};
export type Evidence = { id: string; label: string; url: string; detail: string; kind: 'indicator' | 'report'; passage?: string; publicationDate?: string; page?: number; documentChecksum?: string; ingestionVersion?: number };
export type Finding = { text: string; evidenceIds: string[] };
export type Analysis = {
  id: string; question: string; country: Country; generatedAt: string; mode: 'deterministic' | 'model';
  indicators: Indicator[]; series: Series[]; findings: Finding[]; interpretation: string[];
  risks: string[]; limitations: string[]; evidence: Evidence[]; reportStatus: string;
  unavailableIndicators?: Indicator[];
};

export function isCountry(value: string): value is Country { return Object.hasOwn(COUNTRIES, value); }
export function isIndicator(value: string): value is Indicator { return Object.hasOwn(INDICATORS, value); }

const ALIASES: Record<string, Country | 'EA' | 'EU'> = {
  'netherlands': 'NL', 'dutch': 'NL', 'nl': 'NL', 'germany': 'DE', 'deutschland': 'DE', 'de': 'DE',
  'france': 'FR', 'fr': 'FR', 'united kingdom': 'GB', 'britain': 'GB', 'british': 'GB', 'uk': 'GB', 'gb': 'GB',
  'united states': 'US', 'america': 'US', 'usa': 'US', 'u.s.': 'US', 'us': 'US',
  'euro area': 'EA', 'eurozone': 'EA', 'european union': 'EU', 'eu': 'EU',
};

export function parseCountries(question: string): { countries: Country[]; unsupportedAggregates: ('EU' | 'EA')[] } {
  const found = new Set<Country>(); const unsupportedAggregates = new Set<'EU' | 'EA'>();
  const normalized = question.toLowerCase();
  for (const [alias, code] of Object.entries(ALIASES).sort((a, b) => b[0].length - a[0].length)) {
    const pattern = new RegExp(`(^|[^a-z])${alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}($|[^a-z])`, 'i');
    if (pattern.test(normalized)) { if (code === 'EA' || code === 'EU') unsupportedAggregates.add(code); else found.add(code); }
  }
  return { countries: [...found], unsupportedAggregates: [...unsupportedAggregates] };
}

export function resolveCountry(question: string, selected?: Country): Country {
  const parsed = parseCountries(question);
  if (parsed.unsupportedAggregates.length) throw new Error(`${parsed.unsupportedAggregates.map(v => v === 'EU' ? 'European Union' : 'Euro area').join(' and ')} aggregate data is outside this release. Choose a supported country.`);
  if (parsed.countries.length > 1) throw new Error('This analyst handles one country at a time. Use Compare for multi-country questions.');
  if (selected && parsed.countries.length === 0) return selected;
  if (selected && parsed.countries[0] && parsed.countries[0] !== selected) throw new Error(`The question names ${COUNTRIES[parsed.countries[0]]}, but ${COUNTRIES[selected]} is selected. Change the country selector or edit the question.`);
  if (parsed.countries[0]) return parsed.countries[0];
  if (selected) return selected;
  throw new Error('Select a country to analyse.');
}

export function detectIndicators(question: string): Indicator[] {
  const q = question.toLowerCase();
  const out: Indicator[] = [];
  if (/\b(gdp|growth|output|economy)\b/.test(q)) out.push('NY.GDP.MKTP.KD.ZG');
  if (/\b(inflation|consumer prices|cpi|prices)\b/.test(q)) out.push('FP.CPI.TOTL.ZG');
  if (/\b(unemployment|jobless|labou?r market)\b/.test(q)) out.push('SL.UEM.TOTL.ZS');
  return out.length ? out : /\b(economy|economic|macro|overview|indicators?|latest)\b/.test(q) ? [...INDICATOR_CODES] : [];
}

export function changeInPoints(observations: Observation[]): number | null {
  if (observations.length < 2) return null;
  const sorted = [...observations].sort((a, b) => b.year - a.year);
  return sorted[0].value - sorted[1].value;
}

export function commonPeriod(series: Series[]): number | null {
  if (!series.length) return null;
  const years = series.map(s => new Set(s.observations.map(o => o.year)));
  return [...years[0]].filter(y => years.every(set => set.has(y))).sort((a, b) => b - a)[0] ?? null;
}
