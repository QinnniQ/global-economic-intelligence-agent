import { COUNTRIES, INDICATORS, changeInPoints, detectIndicators, resolveCountry, type Analysis, type Country, type Evidence, type Finding, type Series } from '../src/domain';
import { fetchSeries } from './worldbank';
import { retrieveReports, validateEvidenceIds } from './reports';

const fmt = (n: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 1 }).format(n);

export function buildAnalysis(question: string, country: Country, series: Series[], now = new Date().toISOString()): Analysis {
  const findings: Finding[] = [];
  const evidence: Evidence[] = [];
  const limitations: string[] = [];
  for (const s of series) {
    const id = `WB:${s.country}:${s.indicator}`;
    const latest = s.observations[0];
    evidence.push({ id, kind: 'indicator', label: `${COUNTRIES[s.country]} · ${INDICATORS[s.indicator].name}`, url: s.sourceUrl,
      detail: `${s.frequency}; ${s.unit}; ${s.stale ? 'saved snapshot reviewed' : s.cacheStatus === 'cached' ? 'cached, originally retrieved' : 'retrieved'} ${s.retrievedAt.slice(0, 10)}${s.providerUpdatedAt ? `; provider update ${s.providerUpdatedAt}` : ''}` });
    if (!latest) { limitations.push(`No ${INDICATORS[s.indicator].short.toLowerCase()} observation was available in the requested window.`); continue; }
    findings.push({ text: `${INDICATORS[s.indicator].short} was ${fmt(latest.value)}${s.unit.startsWith('%') ? s.unit : ` ${s.unit}`} in ${latest.year}, ${s.stale ? 'the saved demonstration observation' : 'the latest available annual observation'}.`, evidenceIds: [id] });
    const delta = changeInPoints(s.observations);
    if (delta !== null) {
      const prior = s.observations[1];
      const direction = Math.abs(delta) < 0.05 ? 'changed by less than 0.05 percentage points' : `${delta > 0 ? 'rose' : 'fell'} by ${fmt(Math.abs(delta))} percentage points`;
      findings.push({ text: `From ${prior.year} to ${latest.year}, ${s.indicator === 'NY.GDP.MKTP.KD.ZG' ? 'GDP growth' : INDICATORS[s.indicator].short.toLowerCase()} ${direction}.`, evidenceIds: [id] });
      if (latest.year - prior.year > 1) limitations.push(`${INDICATORS[s.indicator].short}: the two latest observations are ${latest.year - prior.year} years apart.`);
    }
  }
  if (!findings.length) limitations.push('No supported indicator observations were available. An assessment would be unsupported.');
  const reports = retrieveReports(question, country, series.map(s => s.indicator));
  evidence.push(...reports);
  if (!findings.every(f => validateEvidenceIds(f.evidenceIds, evidence))) throw new Error('A finding refers to an unknown source.');
  limitations.push('Annual indicators can be published or revised after the observation year; retrieval today does not make them current-period estimates.');
  limitations.push('These descriptive changes do not establish causes or constitute a forecast or personal investment advice.');
  return { id: crypto.randomUUID(), question, country, generatedAt: now, mode: 'deterministic',
    indicators: series.map(s => s.indicator), series, findings,
    interpretation: findings.length ? [series.some(s => s.observations.length > 1)
      ? 'The figures describe observed direction and level. They do not, by themselves, identify the policy, trade, or domestic forces behind the movement.'
      : 'These single observations describe levels only. They do not establish a trend or explain the forces behind the reported values.'] : [],
    risks: ['Differences in publication timing, revisions, and the modeled nature of unemployment can affect a cross-indicator reading.'],
    limitations, evidence, reportStatus: reports.length
      ? 'Related dated report excerpts are shown for context. Their publication periods and measures can differ from the annual indicator series.'
      : 'No relevant verified report passage is attached to this answer. Indicator sources are available below.' };
}

export async function analyse(question: string, selected: Country, getSeries = fetchSeries): Promise<Analysis> {
  if (question.length < 8 || question.length > 500) throw new Error('Enter a question between 8 and 500 characters.');
  const country = resolveCountry(question, selected);
  const indicators = detectIndicators(question);
  if (!indicators.length) throw new Error('This release supports GDP growth, consumer-price inflation, and unemployment. Try a question about one of those indicators.');
  const results = await Promise.all(indicators.map(indicator => getSeries(country, indicator, 2000, new Date().getUTCFullYear())));
  return buildAnalysis(question, country, results);
}
