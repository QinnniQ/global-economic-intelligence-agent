import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts';
import { COUNTRIES, INDICATORS, INDICATOR_CODES, commonPeriod, type Analysis, type Country, type Indicator, type Series } from './domain';
import { REPORT_SOURCES } from './reportCatalog';
import { loadReportIndex, searchReports, type ReportHit, type SearchIndex } from './reportSearch';
import { SNAPSHOT_DATE } from './demo';
import type { PageExcerpt } from '../worker/reportExcerpts';
import { canGenerateLocally, LOCAL_MODEL, synthesizeLocally } from './localRag';
import './style.css';

type View = 'overview' | 'compare' | 'analyst' | 'methodology' | 'sources';
const countryEntries = Object.entries(COUNTRIES) as [Country, string][];
const indicatorEntries = Object.entries(INDICATORS) as [Indicator, typeof INDICATORS[Indicator]][];
const params = new URLSearchParams(location.search);
const initialCountry = (params.get('country') && Object.hasOwn(COUNTRIES, params.get('country')!) ? params.get('country') : 'NL') as Country;
const initialIndicator = (params.get('indicator') && Object.hasOwn(INDICATORS, params.get('indicator')!) ? params.get('indicator') : INDICATOR_CODES[0]) as Indicator;
const initialCountries = (params.get('countries') ?? 'NL,DE,FR').split(',').filter(c => Object.hasOwn(COUNTRIES, c)).slice(0, 4) as Country[];
const initialView = (['overview','compare','analyst','methodology','sources'].includes(params.get('view') ?? '') ? params.get('view') : 'overview') as View;
const initialMode = params.get('mode') === 'live' ? 'live' : 'demo';
const initialStart = Math.max(2000, Math.min(new Date().getFullYear() - 1, Number(params.get('start')) || 2010));
const initialEnd = Math.max(initialStart + 1, Math.min(new Date().getFullYear(), Number(params.get('end')) || new Date().getFullYear()));

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/${path}`, options);
  const content = await response.json();
  if (!response.ok) {
    const failure = content as { error?: string; requestId?: string };
    throw new Error(`${failure.error || 'The service is unavailable.'}${failure.requestId ? ` Request ID: ${failure.requestId}.` : ''}`);
  }
  return content as T;
}
const date = (iso: string) => new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }) + ' UTC';
const number = (n: number) => new Intl.NumberFormat('en-GB', { maximumFractionDigits: 2, minimumFractionDigits: 1 }).format(n);
const currentYear = new Date().getFullYear();

function CountryPicker({ value, onChange, label }: { value: Country; onChange: (c: Country) => void; label: string }) {
  return <label className="field"><span>{label}</span><select value={value} onChange={e => onChange(e.target.value as Country)}>
    {countryEntries.map(([code, name]) => <option key={code} value={code}>{name}{code === 'GB' ? ' (UK)' : code === 'US' ? ' (US)' : ''}</option>)}
  </select><small>Five supported economies</small></label>;
}

function Chart({ series, indicator, height = 300 }: { series: Series[]; indicator: Indicator; height?: number }) {
  const years = [...new Set(series.flatMap(s => s.observations.map(o => o.year)))].sort((a, b) => a - b);
  const rows = years.map(year => ({ year, ...Object.fromEntries(series.map(s => [s.country, s.observations.find(o => o.year === year)?.value ?? null])) }));
  const palette = ['#2366b3','#9b6a25','#654caa','#287b72'];
  const dashes = [undefined,'6 4','2 4','10 3 2 3'];
  return <div className="chart-wrap" role="img" aria-label={`${INDICATORS[indicator].name} ${series.every(s => s.observations.length <= 1) ? 'saved observation chart' : 'annual trend chart'}. Values are also shown in the data table.`}>
    <ResponsiveContainer width="100%" height={height}><LineChart data={rows} margin={{ top: 12, right: 16, left: 0, bottom: 5 }}>
      <CartesianGrid stroke="#e5e8e9" vertical={false}/><XAxis dataKey="year" tick={{ fill: '#536171', fontSize: 12 }}/>
      <YAxis tick={{ fill: '#536171', fontSize: 12 }} width={48} unit="%"/>
      <Tooltip formatter={(value, name) => [`${number(Number(value))}%`, COUNTRIES[name as Country] ?? String(name)]} labelFormatter={v => `Observation year ${v}`}/>
      {series.length > 1 && <Legend formatter={v => COUNTRIES[v as Country] ?? v}/>}
      {series.map((s, i) => <Line key={s.country} dataKey={s.country} name={s.country} type="monotone" connectNulls={false} stroke={palette[i]} strokeWidth={2.6} strokeDasharray={dashes[i]} dot={{ r: 2.5 }} activeDot={{ r: 5 }}/>) }
    </LineChart></ResponsiveContainer>
  </div>;
}

function DataTable({ series, indicator }: { series: Series[]; indicator: Indicator }) {
  const years = [...new Set(series.flatMap(s => s.observations.map(o => o.year)))].sort((a,b) => b-a);
  return <div className="table-scroll"><table><caption>{INDICATORS[indicator].name} · annual observations · {INDICATORS[indicator].unit}</caption><thead><tr><th scope="col">Year</th>{series.map(s => <th scope="col" key={s.country}>{COUNTRIES[s.country]}</th>)}</tr></thead><tbody>
    {years.map(year => <tr key={year}><th scope="row">{year}</th>{series.map(s => { const value = s.observations.find(o => o.year === year)?.value; return <td key={s.country}>{value === undefined ? '—' : number(value)}</td>; })}</tr>)}
  </tbody></table></div>;
}

let reportIndexPromise: Promise<SearchIndex> | null = null;
function ReportSearch() {
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<ReportHit[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function run(value: string) {
    const requested = value.trim();
    if (requested.length < 2) return;
    setSearched(false); setError(''); setLoading(true);
    try {
      reportIndexPromise ??= loadReportIndex().catch(failure => { reportIndexPromise = null; throw failure; });
      setHits(searchReports(await reportIndexPromise, requested));
      setSearched(true);
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Report search is unavailable.'); }
    finally { setLoading(false); }
  }
  return <section className="report-search panel" aria-label="Search report pages">
    <div className="eyebrow">REPORT PAGE SEARCH</div><h2>Find a page in the source reports.</h2>
    <p>Searches extracted terms across all 13 PDFs. Results link to publisher pages; read the original page before using it as evidence. This is lexical search, separate from the public analyst.</p>
    <form onSubmit={event => { event.preventDefault(); void run(query); }}><label className="field" htmlFor="report-query"><span>Topic or phrase</span></label><div className="report-search-controls"><input id="report-query" value={query} onChange={event => setQuery(event.target.value)} placeholder="For example: France inflation" minLength={2} maxLength={120}/><button className="primary" type="submit" disabled={loading || query.trim().length < 2}>{loading ? 'Searching…' : 'Search reports →'}</button></div></form>
    {error && <div className="state error" role="alert">{error}</div>}
    {searched && <div className="report-results" role="status"><strong>{hits.length ? `Top ${hits.length} matching PDF pages` : 'No matching PDF pages'}</strong>{hits.length > 0 && <ol>{hits.map(hit => <li key={`${hit.reportId}-${hit.page}`}><span>{hit.publisher} · {hit.issue}</span><strong>{hit.title} · PDF page {hit.page}</strong><small>Matched terms: {hit.matchedTerms.join(', ')}</small><a href={hit.url} target="_blank" rel="noopener noreferrer">Open publisher PDF at page {hit.page} ↗</a></li>)}</ol>}</div>}
  </section>;
}

function App() {
  const [view, setView] = useState<View>(initialView);
  const [mode, setMode] = useState<'demo' | 'live'>(initialMode);
  const [country, setCountry] = useState<Country>(initialCountry);
  const [indicator, setIndicator] = useState<Indicator>(initialIndicator);
  const [compCountries, setCompCountries] = useState<Country[]>(initialCountries.length >= 2 ? initialCountries : ['NL','DE']);
  const [start, setStart] = useState(initialStart), [end, setEnd] = useState(initialEnd);
  const [overview, setOverview] = useState<Series[]>([]), [comparison, setComparison] = useState<Series[]>([]);
  const [overviewError, setOverviewError] = useState(''), [compareError, setCompareError] = useState('');
  const [overviewLoading, setOverviewLoading] = useState(true), [compareLoading, setCompareLoading] = useState(false);
  const [question, setQuestion] = useState('What do the latest available economic indicators show?');
  const [analysis, setAnalysis] = useState<Analysis | null>(null), [analysisError, setAnalysisError] = useState(''), [analysing, setAnalysing] = useState(false), [exporting, setExporting] = useState(false);
  const [analystEngine, setAnalystEngine] = useState<'data' | 'rag'>('data');
  const [reportAnswer, setReportAnswer] = useState<{ question: string; country: Country; evidence: PageExcerpt[] } | null>(null);
  const [localAnswer, setLocalAnswer] = useState(''), [localError, setLocalError] = useState(''), [localLoading, setLocalLoading] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => { const next = new URLSearchParams({ view, mode, country, indicator, countries: compCountries.join(','), start: String(start), end: String(end) }); history.replaceState(null, '', `?${next.toString()}`); }, [view,mode,country,indicator,compCountries,start,end]);
  useEffect(() => { setAnalysis(null); setReportAnswer(null); setLocalAnswer(''); setLocalError(''); setAnalysisError(''); }, [country, mode, analystEngine]);
  useEffect(() => { if (view !== 'overview') return; const controller = new AbortController(); setOverviewLoading(true); setOverviewError(''); setOverview([]);
    Promise.allSettled(INDICATOR_CODES.map(code => api<Series>(`series?country=${country}&indicator=${code}&start=2000&end=${currentYear}&mode=${mode}`, { signal: controller.signal })))
      .then(results => { if (controller.signal.aborted) return;
        const available = results.flatMap(result => result.status === 'fulfilled' ? [result.value] : []);
        const missing = results.flatMap((result, i) => result.status === 'rejected' ? [INDICATORS[INDICATOR_CODES[i]].short] : []);
        const failure = results.find((result): result is PromiseRejectedResult => result.status === 'rejected');
        setOverview(available);
        if (available.length && !available.some(series => series.indicator === indicator)) setIndicator(available[0].indicator);
        if (failure) setOverviewError(`${missing.join(', ')} could not be retrieved. ${available.length ? 'Available indicators remain visible.' : 'No live indicators are available for this request.'} ${failure.reason instanceof Error ? failure.reason.message : 'Try again shortly.'}`);
      }).finally(() => { if (!controller.signal.aborted) setOverviewLoading(false); });
    return () => controller.abort(); }, [country, mode, view, retryKey]);
  useEffect(() => { if (view !== 'compare') return; const controller = new AbortController(); setCompareLoading(true); setCompareError(''); setComparison([]);
    Promise.allSettled(compCountries.map(code => api<Series>(`series?country=${code}&indicator=${indicator}&start=${start}&end=${end}&mode=${mode}`, { signal: controller.signal })))
      .then(results => { if (controller.signal.aborted) return;
        const available = results.flatMap(result => result.status === 'fulfilled' ? [result.value] : []);
        const missing = results.flatMap((result, i) => result.status === 'rejected' ? [COUNTRIES[compCountries[i]]] : []);
        setComparison(available);
        if (missing.length) setCompareError(`${missing.join(', ')} could not be retrieved. ${available.length >= 2 ? 'Available countries remain visible.' : 'At least two country series are needed to compare.'}`);
      }).finally(() => { if (!controller.signal.aborted) setCompareLoading(false); });
    return () => controller.abort(); }, [compCountries,indicator,start,end,mode,view,retryKey]);
  const overviewSelected = useMemo(() => overview.find(s => s.indicator === indicator), [overview,indicator]);
  const common = commonPeriod(comparison);
  const toggleCountry = (code: Country) => setCompCountries(prev => prev.includes(code) ? (prev.length > 2 ? prev.filter(v => v !== code) : prev) : (prev.length < 4 ? [...prev,code] : prev));
  async function ask() { setAnalysis(null); setReportAnswer(null); setLocalAnswer(''); setLocalError(''); setAnalysisError(''); setAnalysing(true);
    try {
      if (analystEngine === 'rag') {
        reportIndexPromise ??= loadReportIndex().catch(failure => { reportIndexPromise = null; throw failure; });
        const hits = searchReports(await reportIndexPromise, question, 5, true);
        const evidence = hits.length ? (await api<{ excerpts: PageExcerpt[] }>('report-excerpts', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ question, pages: hits.map(hit => ({ reportId: hit.reportId, page: hit.page })) }) })).excerpts : [];
        setReportAnswer({ question, country, evidence });
      }
      else setAnalysis(await api<Analysis>('analysis', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ question, country, mode }) }));
    }
    catch (error) { setAnalysisError((error as Error).message); } finally { setAnalysing(false); } }
  async function generateLocal() { if (!reportAnswer) return; setLocalAnswer(''); setLocalError(''); setLocalLoading(true);
    try { setLocalAnswer(await synthesizeLocally(reportAnswer.question, reportAnswer.evidence)); }
    catch (error) { setLocalError((error as Error).message); } finally { setLocalLoading(false); } }
  async function exportPdf() { if (!analysis) return; setExporting(true);
    try { const { renderBriefing } = await import('../worker/pdf'); const pdf = await renderBriefing(analysis);
      const blob = new Blob([pdf as BlobPart], { type: 'application/pdf' }); const href = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = href; a.download = `economic-briefing-${analysis.country.toLowerCase()}.pdf`; a.click(); setTimeout(() => URL.revokeObjectURL(href), 1000);
    } catch (error) { setAnalysisError((error as Error).message); } finally { setExporting(false); } }
  return <><a className="skip" href="#main">Skip to content</a><div className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">EI</span><span>ECONOMIC<br/>INTELLIGENCE</span></div>
      <div className="sidebar-label">WORKSPACE</div><nav aria-label="Primary navigation">
        {([['overview','Overview'],['compare','Compare'],['analyst','Ask the analyst'],['methodology','Methodology'],['sources','Source library']] as [View,string][]).map(([key,label],i) => <button key={key} className={`nav-item ${view === key ? 'active' : ''}`} onClick={() => setView(key)} aria-current={view === key ? 'page' : undefined}><span className="nav-index">0{i+1}</span>{label}<span className="nav-arrow">↗</span></button>)}
      </nav><div className="sidebar-bottom"><span className="dot"/> WORLD BANK DATA<br/><small>Annual observations · sourced</small></div>
    </aside><div className="main-area"><header className="topbar"><span>GLOBAL ECONOMIC INTELLIGENCE AGENT</span><span className="topbar-right">RESEARCH WORKSPACE <span className="topbar-rule"/> 2026</span></header>
      <main id="main" tabIndex={-1}><div className="mode-bar" role="group" aria-label="Data mode"><span>{mode === 'demo' ? `SAVED DEMONSTRATION · REVIEWED ${new Date(SNAPSHOT_DATE).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).toUpperCase()} · ROUNDED VALUES` : 'LIVE WORLD BANK API · ANNUAL SERIES'}</span><div><button className={mode === 'demo' ? 'on' : ''} onClick={()=>setMode('demo')} aria-pressed={mode === 'demo'}>Saved demo</button><button className={mode === 'live' ? 'on' : ''} onClick={()=>setMode('live')} aria-pressed={mode === 'live'}>Live data</button></div></div>
        {view === 'overview' && <><section className="page-heading"><div className="eyebrow">01 / ECONOMIC OVERVIEW</div><h1>An economy, in context.</h1><p>Inspect a dated snapshot, or switch to live World Bank data for historical trends. Every observation keeps its year and source.</p></section>
          <div className="control-strip"><CountryPicker value={country} onChange={setCountry} label="Economy"/><div className="control-note">Five supported economies<br/><strong>Annual World Bank series</strong></div></div>
          {overviewLoading && <div className="state" role="status">{mode === 'demo' ? 'Loading saved observations…' : 'Retrieving World Bank observations…'}</div>}
          {overviewError && <div className="state error" role="alert"><strong>{overview.length ? 'Some data could not be loaded.' : 'Data could not be loaded.'}</strong><p>{overviewError}</p><div className="state-actions"><button onClick={() => setRetryKey(n => n + 1)}>Retry this request</button>{mode === 'live' && <button onClick={() => setMode('demo')}>Use saved demonstration</button>}</div></div>}
          {!overviewLoading && overview.length > 0 && <><div className="metric-grid">{overview.map(s => { const latest = s.observations[0]; return <button className={`metric ${indicator === s.indicator ? 'selected' : ''}`} key={s.indicator} onClick={() => setIndicator(s.indicator)} aria-pressed={indicator === s.indicator}>
            <span className="metric-title">{INDICATORS[s.indicator].short}<span aria-hidden="true">↗</span></span><strong>{latest ? `${number(latest.value)}%` : '—'}</strong><span className="metric-foot">{latest ? `${latest.year} observation` : 'No observation'} · {s.unit}</span></button>; })}</div>
            {overviewSelected && <section className="panel"><div className="panel-head"><div><div className="eyebrow">{mode === 'demo' ? 'SAVED OBSERVATION' : 'HISTORICAL SERIES'}</div><h2>{INDICATORS[indicator].name}</h2><p>{INDICATORS[indicator].definition}</p></div><span className="source-tag">WORLD BANK · {mode === 'demo' ? 'SNAPSHOT' : 'ANNUAL'}</span></div>
              {overviewSelected.observations.length ? <><Chart series={[overviewSelected]} indicator={indicator}/><div className="panel-actions"><button className="text-button" onClick={() => setShowTable(!showTable)} aria-expanded={showTable}>{showTable ? 'Hide' : 'View'} underlying data <span>↘</span></button><a href={overviewSelected.sourceUrl} target="_blank" rel="noreferrer">Open source ↗</a></div>{showTable && <DataTable series={[overviewSelected]} indicator={indicator}/>}</> : <div className="state">No observations are available for this series.</div>}
              <div className="meta-line">{mode === 'demo' ? 'Snapshot reviewed' : overviewSelected.cacheStatus === 'cached' ? 'Cached live series; originally retrieved' : 'Retrieved'} {date(overviewSelected.retrievedAt)} · {overviewSelected.providerUpdatedAt ? `Provider update ${overviewSelected.providerUpdatedAt}` : 'Provider update date unavailable'} · Missing values are omitted</div></section>}
            <div className="editorial-note"><span>READING THE DATA</span><p>These are annual measurements, not real-time readings. GDP growth measures change in real output, inflation measures change in consumer prices, and unemployment is a modeled share of the labor force.</p></div>
          </>}
        </>}
        {view === 'compare' && <><section className="page-heading"><div className="eyebrow">02 / COUNTRY COMPARISON</div><h1>Compare on the same scale.</h1><p>Choose two to four economies, one indicator and a shared date window. Missing observations stay visible as gaps.</p></section>
          <div className="control-panel"><div className="field"><span>Economies <small>({compCountries.length} selected)</small></span><div className="country-checks">{countryEntries.map(([code,name]) => <label key={code} className={compCountries.includes(code) ? 'checked' : ''}><input type="checkbox" checked={compCountries.includes(code)} onChange={() => toggleCountry(code)} disabled={!compCountries.includes(code) && compCountries.length >= 4}/>{name}</label>)}</div></div><div className="compare-controls"><label className="field"><span>Indicator</span><select value={indicator} onChange={e => setIndicator(e.target.value as Indicator)}>{indicatorEntries.map(([code,meta]) => <option key={code} value={code}>{meta.short}</option>)}</select></label><label className="field"><span>From</span><select value={start} onChange={e => setStart(Math.min(Number(e.target.value),end-1))}>{Array.from({length:currentYear-1999},(_,i)=>2000+i).map(y=><option key={y}>{y}</option>)}</select></label><label className="field"><span>To</span><select value={end} onChange={e => setEnd(Math.max(Number(e.target.value),start+1))}>{Array.from({length:currentYear-1999},(_,i)=>2000+i).map(y=><option key={y}>{y}</option>)}</select></label></div></div>
          {compareLoading && <div className="state" role="status">{mode === 'demo' ? 'Loading saved country observations…' : 'Retrieving aligned country series…'}</div>}{compareError && <div className="state error" role="alert"><strong>{comparison.length >= 2 ? 'Some country data could not be loaded.' : 'Comparison could not be loaded.'}</strong><p>{compareError}</p><div className="state-actions"><button onClick={() => setRetryKey(n => n + 1)}>Retry this request</button>{mode === 'live' && <button onClick={() => setMode('demo')}>Use saved demonstration</button>}</div></div>}
          {!compareLoading && comparison.length >= 2 && <><section className="panel"><div className="panel-head"><div><div className="eyebrow">{mode === 'demo' ? 'SAVED CROSS-SECTION' : 'ALIGNED TREND'} / {start}–{end}</div><h2>{INDICATORS[indicator].name}</h2></div><span className="source-tag">UNIT: {INDICATORS[indicator].unit}</span></div><Chart series={comparison} indicator={indicator} height={350}/>
            <div className="comparison-summary">{common ? <><strong>{common}</strong><span>Latest year shared by displayed economies. {comparison.map(s => `${COUNTRIES[s.country]} ${s.observations.find(o=>o.year===common)?.value.toFixed(1) ?? '—'}%`).join(' · ')}</span></> : <span>No common observed year in this window.</span>}</div>
            <p className="small-copy">{mode === 'demo' ? 'Saved observations' : 'Latest individual observations'}: {comparison.map(s => `${COUNTRIES[s.country]} ${s.observations[0]?.year ?? 'none'}`).join(' · ')}. Differences in years can make latest-value comparisons misleading.</p>
            <DataTable series={comparison} indicator={indicator}/><div className="meta-line">{comparison.map(s=><div key={s.country}><a href={s.sourceUrl} target="_blank" rel="noreferrer">{COUNTRIES[s.country]} source ↗</a> · {s.stale ? 'Snapshot reviewed' : s.cacheStatus === 'cached' ? 'Cached; originally retrieved' : 'Retrieved'} {date(s.retrievedAt)}</div>)}</div></section></>}
        </>}
        {view === 'analyst' && <><section className="page-heading"><div className="eyebrow">03 / ASK THE ANALYST</div><h1>Ask, then inspect.</h1><p>Choose observed World Bank data or a report-grounded answer. Each path labels its evidence and limits.</p></section>
          <section className="question-panel"><div className="engine-picker" role="group" aria-label="Analysis mode"><button type="button" className={analystEngine === 'data' ? 'selected' : ''} onClick={() => setAnalystEngine('data')} aria-pressed={analystEngine === 'data'}>Observed data</button><button type="button" className={analystEngine === 'rag' ? 'selected' : ''} onClick={() => setAnalystEngine('rag')} aria-pressed={analystEngine === 'rag'}>Report RAG · on device</button></div><p className="engine-note">{analystEngine === 'rag' ? 'Searches the 13 indexed PDFs and shows page-linked excerpts. Optional model synthesis runs in your browser after a large download. No paid model API is called.' : 'Calculates findings from World Bank observations. No model call.'}</p><CountryPicker value={country} onChange={setCountry} label="Selected economy"/><label className="field"><span>Research question</span><textarea value={question} onChange={e => setQuestion(e.target.value)} maxLength={analystEngine === 'rag' ? 300 : 500} rows={3} placeholder={analystEngine === 'rag' ? 'What do recent reports say about Dutch growth risks?' : 'What do the latest available indicators show for the Netherlands?'}/></label><div className="suggestions"><span>TRY A QUESTION</span>{(analystEngine === 'rag' ? ['What do recent reports say about growth risks for the Netherlands?','What does the latest ECB bulletin say about inflation?'] : ['What do the latest available indicators show?','What is the latest unemployment observation?','What are the latest growth and inflation observations?']).map(q=><button key={q} onClick={()=>setQuestion(q)}>{q} ↗</button>)}</div><div className="question-actions"><button className="primary" onClick={ask} disabled={analysing || question.trim().length < 8}>{analysing ? analystEngine === 'rag' ? 'Searching reports…' : mode === 'demo' ? 'Calculating from saved observations…' : 'Retrieving and calculating…' : analystEngine === 'rag' ? 'Find report evidence' : 'Run analysis'} <span>→</span></button><small>Selected country: {COUNTRIES[country]} · {analystEngine === 'rag' ? 'No paid inference' : 'Deterministic calculation'}</small></div></section>
          {analysisError && <div className="state error" role="alert">{analysisError}</div>}
          {reportAnswer && <article className="analysis rag-answer"><div className="eyebrow">REPORT RETRIEVAL · NO PAID API</div><h2>Evidence from the reports</h2><p className="rag-question">{reportAnswer.question}</p><div className="analysis-meta">{reportAnswer.evidence.length} retrieved PDF pages · Source text is dated and may not describe current conditions</div>{reportAnswer.evidence.length ? <><ol className="rag-sources">{reportAnswer.evidence.map(item => <li key={`${item.reportId}:${item.page}`}><strong>{item.title}</strong> · {item.publisher}, {item.issue}, PDF page {item.page}<p>{item.text}</p><a href={item.url} target="_blank" rel="noopener noreferrer">Open publisher PDF at page {item.page} ↗</a></li>)}</ol><div className="local-generation"><h3>Optional on-device synthesis</h3><p>A small model can summarize these passages on your computer. First use downloads about 117 MB from Hugging Face and may take time. It makes no paid API call.</p><button className="primary secondary" onClick={generateLocal} disabled={localLoading || !canGenerateLocally()}>{localLoading ? 'Loading or generating locally…' : 'Generate on this device'}</button>{!canGenerateLocally() && <p>This browser does not support WebGPU. The retrieved evidence above is still available.</p>}{localError && <div className="state error" role="alert">{localError}</div>}{localAnswer && <div className="local-answer"><div className="eyebrow">EXPERIMENTAL LOCAL MODEL · {LOCAL_MODEL}</div><p>{localAnswer}</p><small>Check each statement against the linked report pages. The model may misread context.</small></div>}</div></> : <p>No relevant passages were retrieved. Try a more specific report topic or use Source library search.</p>}<div className="limitations"><h3>Limits</h3><p>Page search is lexical. Excerpts are selected automatically and may miss the best passage. Local model synthesis is experimental and is not a verified economic finding.</p></div></article>}
          {analysis && <article className="analysis"><div className="analysis-top"><div><div className="eyebrow">EVIDENCE-LED ASSESSMENT</div><h2>{COUNTRIES[analysis.country]} at a glance</h2><p>{analysis.question}</p></div><button className="primary secondary" onClick={exportPdf} disabled={exporting}>{exporting ? 'Preparing PDF…' : 'Export this briefing ↓'}</button></div>
            <div className="analysis-meta">Generated {date(analysis.generatedAt)} · {analysis.series.some(s=>s.stale) ? 'Saved demonstration' : 'Live annual observations'} · {analysis.mode === 'model' ? 'Model synthesis' : 'Deterministic analysis'}</div>
            {!!analysis.unavailableIndicators?.length && <div className="state error" role="status">Partial live briefing: {analysis.unavailableIndicators.map(code => INDICATORS[code].short).join(', ')} could not be loaded. Findings below use only the available indicators.</div>}
            <div className="analysis-columns"><div><h3>Key findings</h3>{analysis.findings.length ? <ol className="findings">{analysis.findings.map((f,i)=><li key={i}>{f.text} <span>{f.evidenceIds.map(id=><a key={id} href={`#${id.replaceAll(':','-')}`}>[{id}]</a>)}</span></li>)}</ol> : <p>There is not enough observed data for a finding.</p>}
              <h3>Interpretation</h3>{analysis.interpretation.map((s,i)=><p key={i}>{s}</p>)}<h3>Risks</h3>{analysis.risks.map((s,i)=><p key={i}>{s}</p>)}</div><aside className="evidence-rail"><h3>Source evidence</h3>{analysis.evidence.map(e=><div className="evidence-item" id={e.id.replaceAll(':','-')} key={e.id}><strong>{e.label}</strong><span>{e.detail}</span>{e.passage && <blockquote>“{e.passage}”</blockquote>}<a href={e.url} target="_blank" rel="noreferrer">{e.kind === 'report' ? `Open report page ${e.page} ↗` : 'View World Bank series ↗'}</a></div>)}<div className="report-status"><strong>Report excerpts</strong><p>{analysis.reportStatus}</p></div></aside></div>
            <div className="limitations"><h3>Limits of this assessment</h3><ul>{analysis.limitations.map((s,i)=><li key={i}>{s}</li>)}</ul></div>
            <details className="raw-evidence"><summary>Inspect supporting observations</summary>{analysis.series.map(s=><DataTable key={s.indicator} series={[s]} indicator={s.indicator}/>)}</details>
          </article>}
        </>}
        {view === 'methodology' && <><section className="page-heading"><div className="eyebrow">04 / METHODOLOGY</div><h1>What the evidence can say.</h1><p>A concise account of the sources, calculations, and deliberate limits of this release.</p></section><div className="method-grid"><section className="panel"><h2>Data</h2><p>Annual World Bank Indicators API observations for five countries. GDP growth and consumer-price inflation are annual percentage rates. Unemployment is the modeled ILO estimate, expressed as a percentage of the labor force.</p><p>The saved demonstration has rounded 2024 and 2025 values transcribed from official World Bank pages reviewed {date(SNAPSHOT_DATE)}. It has one observation per indicator and cannot establish a trend. Live mode retrieves full series. Missing observations are left blank; forecast-status observations are excluded.</p></section><section className="panel"><h2>Analysis</h2><p>Observed-data findings are calculated in application code. A change from one annual percentage value to another is reported in percentage points. No interpolation, forecast, causal explanation or personalized investment advice is generated.</p><p>Report RAG first searches a lexical page index over 13 PDFs. The Worker selects short passages from hash-verified local copies and links to the corresponding publisher PDF pages. Optional model synthesis runs only in the visitor's browser using WebGPU and a downloaded open model. It may be unavailable on some devices and can still misread evidence. No paid model API or server-side vector store is used.</p></section><section className="panel"><h2>Freshness and availability</h2><p>Live series are fetched through the Cloudflare Worker and cached for six hours. If some series fail, available findings remain visible and the missing indicators are named. Retrieval date is separate from observation year.</p><p>Observed-data exports are rendered from the exact analysis object displayed in the browser. The PDF does not rerun retrieval or generation. Report RAG answers currently have no PDF export.</p></section></div></>}
        {view === 'sources' && <><section className="page-heading"><div className="eyebrow">05 / SOURCE LIBRARY</div><h1>Read the original reports.</h1><p>Open the publisher PDFs in the local Chroma retrieval corpus. File fingerprints and index counts make the source set inspectable.</p></section>
          <div className="source-summary"><strong>{REPORT_SOURCES.length} reports</strong><span>{REPORT_SOURCES.reduce((total, report) => total + report.chunks, 0).toLocaleString('en-GB')} indexed chunks in the local Python prototype</span></div>
          <ReportSearch/>
          <div className="source-grid">{REPORT_SOURCES.map(report => <article className="source-card" key={report.id}><div className="source-card-top"><span>{report.publisher}</span><span>{report.issue}</span></div><h2>{report.title}</h2><p>{report.pages} PDF pages · {report.chunks.toLocaleString('en-GB')} stored chunks · index ID <code>{report.id}</code></p><div className="source-card-bottom"><a href={report.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${report.title} PDF from ${report.publisher} in a new tab`}>Open publisher PDF ↗</a><span>{report.publicPassage ? 'Public analyst: one curated passage' : 'Local prototype corpus'}</span></div><details><summary>Local file fingerprint</summary><code>SHA-256 {report.sha256}</code></details></article>)}</div>
          <div className="source-caveat"><strong>How this relates to the public analyst</strong><p>The Python prototype indexes these reports in a local Chroma store. The public Report RAG mode uses the separate lexical page index and short page excerpts, then can run an optional model on the visitor's device. It does not use the local Chroma vectors or a paid hosted vector store. The observed-data analyst uses only two manually reviewed 2025 passages. The 2026 local Chroma chunks retain page numbers; the original 2025 chunks did not.</p></div>
        </>}
      </main><footer>GLOBAL ECONOMIC INTELLIGENCE AGENT <span>Source: World Bank Indicators API · <a href="https://data.worldbank.org" target="_blank" rel="noreferrer">data.worldbank.org ↗</a></span></footer>
    </div></div></>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
