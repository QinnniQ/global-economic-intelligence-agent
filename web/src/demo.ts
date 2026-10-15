import { INDICATORS, type Country, type Indicator, type Series } from './domain';

// Rounded World Bank country page values, reviewed 2026-10-15. This is a small
// demonstration rather than a historical API extract or current-period estimate.
export const SNAPSHOT_DATE = '2026-10-15T00:00:00.000Z';
export const SNAPSHOT_SOURCES = [
  'https://data.worldbank.org/?locations=BE-NL-LU-DE-FR-IT',
  'https://data.worldbank.org/?locations=GB-DE-US-FR',
];
const values: Record<Country, Record<Indicator, { year: number; value: number }>> = {
  NL: { 'NY.GDP.MKTP.KD.ZG': { year: 2024, value: 1.1 }, 'FP.CPI.TOTL.ZG': { year: 2024, value: 3.3 }, 'SL.UEM.TOTL.ZS': { year: 2025, value: 3.9 } },
  DE: { 'NY.GDP.MKTP.KD.ZG': { year: 2024, value: -0.5 }, 'FP.CPI.TOTL.ZG': { year: 2024, value: 2.3 }, 'SL.UEM.TOTL.ZS': { year: 2025, value: 3.7 } },
  FR: { 'NY.GDP.MKTP.KD.ZG': { year: 2024, value: 1.2 }, 'FP.CPI.TOTL.ZG': { year: 2024, value: 2.0 }, 'SL.UEM.TOTL.ZS': { year: 2025, value: 7.5 } },
  GB: { 'NY.GDP.MKTP.KD.ZG': { year: 2024, value: 1.1 }, 'FP.CPI.TOTL.ZG': { year: 2024, value: 3.3 }, 'SL.UEM.TOTL.ZS': { year: 2025, value: 4.7 } },
  US: { 'NY.GDP.MKTP.KD.ZG': { year: 2024, value: 2.8 }, 'FP.CPI.TOTL.ZG': { year: 2024, value: 2.9 }, 'SL.UEM.TOTL.ZS': { year: 2025, value: 4.2 } },
};
export function demoSeries(country: Country, indicator: Indicator, start = 2000, end = 2026): Series {
  const observation = values[country][indicator];
  return { country, indicator, provider: 'World Bank', frequency: 'annual', name: INDICATORS[indicator].name,
    definition: INDICATORS[indicator].definition, unit: INDICATORS[indicator].unit,
    sourceUrl: `https://data.worldbank.org/indicator/${indicator}?locations=${country}`,
    retrievedAt: SNAPSHOT_DATE, providerUpdatedAt: null, stale: true,
    observations: observation.year >= start && observation.year <= end ? [observation] : [] };
}
