export type ReportSource = {
  id: string;
  title: string;
  publisher: string;
  issue: string;
  pages: number;
  chunks: number;
  url: string;
  sha256: string;
  publicPassage: boolean;
};

// Snapshot of the seven PDFs in data/reports_pdfs and their original Chroma index.
// Publisher links open the same report editions; the hash identifies the local file.
export const REPORT_SOURCES: ReportSource[] = [
  { id: 'ecb', title: 'Economic Bulletin', publisher: 'European Central Bank', issue: 'Issue 7 / 2025', pages: 126, chunks: 467, url: 'https://www.ecb.europa.eu/pub/pdf/ecbu/eb202507.en.pdf', sha256: 'cea88accb46726306dae6dab81937d6a5efdcfd4f302e94ed2fc9fdf6bba4e4b', publicPassage: true },
  { id: 'fm', title: 'Fiscal Monitor: Spending Smarter', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 106, chunks: 573, url: 'https://www.imf.org/-/media/files/publications/fiscal-monitor/2025/october/english/text.pdf?la=en', sha256: '002c7852a34747e55741646ad750463cc63a554587bd5f6dbaff0e1bb8b9b440', publicPassage: false },
  { id: 'frmp', title: 'Monetary Policy Report', publisher: 'Federal Reserve', issue: 'February 2025', pages: 83, chunks: 280, url: 'https://www.federalreserve.gov/publications/files/20250207_mprfullreport.pdf', sha256: '728293cfbfeb672979115ab969cf6ec85cd62977f643eaee397334c6a9534ebd', publicPassage: false },
  { id: 'gep', title: 'Global Economic Prospects', publisher: 'World Bank', issue: 'June 2025', pages: 254, chunks: 1524, url: 'https://thedocs.worldbank.org/en/doc/8bf0b62ec6bcb886d97295ad930059e9-0050012025/original/GEP-June-2025.pdf', sha256: 'f3f1f5153c7c04a09271b0e7740566857e5f795bbbc7e002d832a534c27f5715', publicPassage: false },
  { id: 'gfsr', title: 'Global Financial Stability Report: Shifting Ground beneath the Calm', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 126, chunks: 777, url: 'https://www.imf.org/-/media/files/publications/gfsr/2025/october/english/text.pdf', sha256: 'ea0e690ff12999b97a76508ddc0d39fc42f3af3d90dec304f0315ccc1986343b', publicPassage: false },
  { id: 'oecd', title: 'OECD Economic Outlook, Interim Report', publisher: 'OECD', issue: 'September 2025', pages: 24, chunks: 96, url: 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/09/oecd-economic-outlook-interim-report-september-2025_ae3d418b/67b10c01-en.pdf', sha256: 'f3d64751363d12e1dd140b69ebb2c81ac7697f27ec6bf55194ce9f4484fb96df', publicPassage: true },
  { id: 'weo', title: 'World Economic Outlook: Global Economy in Flux', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 186, chunks: 1050, url: 'https://www.imf.org/-/media/files/publications/weo/2025/october/english/text.pdf', sha256: 'a0ece6ccdd7d40f38f453dd77728c67d8d5ccf79558ed6a6c778850767abd093', publicPassage: false },
];
