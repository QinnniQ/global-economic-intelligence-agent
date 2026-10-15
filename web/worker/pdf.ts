import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import { COUNTRIES, INDICATORS, type Analysis } from '../src/domain';

const clean = (value: string) => value.replace(/[\u2018\u2019]/g, "'").replace(/[\u2013\u2014]/g, '-').replace(/[^\x20-\x7E]/g, ' ').trim();

export async function renderBriefing(analysis: Analysis): Promise<Uint8Array> {
  const pdf = await PDFDocument.create();
  pdf.setTitle(`Economic briefing - ${COUNTRIES[analysis.country]}`);
  pdf.setAuthor('Global Economic Intelligence Agent');
  pdf.setSubject(clean(analysis.question));
  const regular = await pdf.embedFont(StandardFonts.Helvetica);
  const bold = await pdf.embedFont(StandardFonts.HelveticaBold);
  const navy = rgb(0.08, 0.16, 0.25), blue = rgb(0.1, 0.32, 0.62), muted = rgb(0.37, 0.43, 0.48);
  let page = pdf.addPage([595, 842]); let y = 782; let pageNo = 1;
  const footer = () => { page.drawLine({ start: { x: 48, y: 42 }, end: { x: 547, y: 42 }, color: rgb(.82,.85,.87) });
    page.drawText(`Economic Intelligence  /  ${analysis.id.slice(0, 8)}  /  ${pageNo}`, { x: 48, y: 27, size: 8, font: regular, color: muted }); };
  const nextPage = () => { footer(); page = pdf.addPage([595, 842]); pageNo++; y = 784; };
  const ensure = (height: number) => { if (y - height < 65) nextPage(); };
  const line = (text: string, font = regular, size = 10, color = navy, gap = 15) => {
    ensure(gap); page.drawText(clean(text), { x: 48, y, size, font, color }); y -= gap;
  };
  const paragraph = (text: string, opts: { font?: typeof regular; size?: number; color?: typeof navy; indent?: number } = {}) => {
    const size = opts.size ?? 10; const font = opts.font ?? regular; const indent = opts.indent ?? 0;
    const words = clean(text).split(/\s+/); let current = '';
    for (const word of words) {
      const candidate = current ? `${current} ${word}` : word;
      if (font.widthOfTextAtSize(candidate, size) > 499 - indent && current) {
        ensure(13); page.drawText(current, { x: 48 + indent, y, size, font, color: opts.color ?? navy }); y -= 13; current = word;
      } else current = candidate;
    }
    if (current) { ensure(13); page.drawText(current, { x: 48 + indent, y, size, font, color: opts.color ?? navy }); y -= 13; }
    y -= 2;
  };
  const heading = (title: string) => { y -= 4; ensure(26); line(title.toUpperCase(), bold, 10, blue, 17); };
  page.drawRectangle({ x: 0, y: 810, width: 595, height: 32, color: navy });
  page.drawText('GLOBAL ECONOMIC INTELLIGENCE AGENT', { x: 48, y: 821, size: 9, font: bold, color: rgb(1,1,1) });
  line('ECONOMIC BRIEFING', bold, 20, navy, 31);
  line(COUNTRIES[analysis.country], bold, 16, blue, 30);
  paragraph(`Question: ${analysis.question}`, { font: bold, size: 11 });
  paragraph(`Analysis generated: ${analysis.generatedAt} UTC  |  Method: ${analysis.mode === 'deterministic' ? 'deterministic evidence summary' : 'model assisted'}`, { color: muted, size: 9 });
  heading('Key findings');
  analysis.findings.forEach((f, i) => paragraph(`${i + 1}. ${f.text} [${f.evidenceIds.join(', ')}]`));
  heading('Indicator table');
  for (const s of analysis.series) {
    const latest = s.observations[0];
    paragraph(`${INDICATORS[s.indicator].short}  |  ${latest ? `${latest.value.toFixed(2)}${s.unit.startsWith('%') ? '' : ' '}${s.unit}, ${latest.year}` : 'No observation'}  |  ${s.stale ? 'snapshot reviewed' : 'retrieved'} ${s.retrievedAt.slice(0, 10)}`);
  }
  heading('Interpretation and risks');
  analysis.interpretation.forEach(item => paragraph(item));
  analysis.risks.forEach(item => paragraph(item));
  heading('Report evidence'); paragraph(analysis.reportStatus);
  for (const e of analysis.evidence.filter(item => item.kind === 'report')) {
    paragraph(`${e.id} - ${e.label}, page ${e.page}, published ${e.publicationDate}`, { font: bold, size: 9 });
    if (e.passage) paragraph(`"${e.passage}"`, { size: 9 });
  }
  heading('Sources');
  for (const e of analysis.evidence) { paragraph(`${e.id} - ${e.label}`, { font: bold, size: 9 }); paragraph(`${e.detail} | ${e.url}`, { size: 8, color: muted }); }
  heading('Limitations'); analysis.limitations.forEach((v, i) => paragraph(`${i + 1}. ${v}`));
  footer();
  return pdf.save();
}
