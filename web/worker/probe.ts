import type { Country, Indicator, Series } from '../src/domain';
import { fetchSeries } from './worldbank';

export const PROBE_SERIES: { country: Country; indicator: Indicator }[] = [
  { country: 'NL', indicator: 'NY.GDP.MKTP.KD.ZG' },
  { country: 'US', indicator: 'FP.CPI.TOTL.ZG' },
  { country: 'GB', indicator: 'SL.UEM.TOTL.ZS' },
];

export type ProbeResult = { country: Country; indicator: Indicator; ok: boolean; latestYear?: number; providerUpdatedAt?: string | null; durationMs: number; errorType?: string };

export async function probeWorldBank(
  getSeries: typeof fetchSeries = fetchSeries,
  now = new Date(),
): Promise<ProbeResult[]> {
  const end = now.getUTCFullYear();
  return Promise.all(PROBE_SERIES.map(async ({ country, indicator }) => {
    const started = Date.now();
    try {
      const series: Series = await getSeries(country, indicator, end - 3, end);
      if (!series.observations.length) throw new Error('No recent observations');
      return { country, indicator, ok: true, latestYear: series.observations[0].year,
        providerUpdatedAt: series.providerUpdatedAt, durationMs: Date.now() - started };
    } catch (error) {
      return { country, indicator, ok: false, durationMs: Date.now() - started,
        errorType: error instanceof Error ? error.name : 'Unknown' };
    }
  }));
}
