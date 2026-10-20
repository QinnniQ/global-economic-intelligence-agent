import { INDICATORS, type Country, type Indicator, type Series } from './domain';
import snapshot from './demoSnapshot.json';

// Rounded World Bank country page values, reviewed 2026-10-15. This is a small
// demonstration rather than a historical API extract or current-period estimate.
export const SNAPSHOT_DATE = snapshot.reviewedAt;
export const SNAPSHOT_SOURCES = snapshot.sources;
const values = snapshot.values as Record<Country, Record<Indicator, { year: number; value: number }>>;
export function demoSeries(country: Country, indicator: Indicator, start = 2000, end = 2026): Series {
  const observation = values[country][indicator];
  return { country, indicator, provider: 'World Bank', frequency: 'annual', name: INDICATORS[indicator].name,
    definition: INDICATORS[indicator].definition, unit: INDICATORS[indicator].unit,
    sourceUrl: `https://data.worldbank.org/indicator/${indicator}?locations=${country}`,
    retrievedAt: SNAPSHOT_DATE, providerUpdatedAt: null, stale: true,
    observations: observation.year >= start && observation.year <= end ? [observation] : [] };
}
