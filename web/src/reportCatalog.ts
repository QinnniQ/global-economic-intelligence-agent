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

// Snapshot of data/report_manifest.json and the local Chroma index.
// Publisher links open the same report editions; the hash identifies the local file.
export const REPORT_SOURCES: ReportSource[] = [
  { id: 'ec_forecast_2026', title: 'European Economic Forecast', publisher: 'European Commission', issue: 'Spring 2026', pages: 246, chunks: 1296, url: 'https://economy-finance.ec.europa.eu/document/download/3360898c-cd40-46c0-b170-7adfcb993add_en?filename=ip341_en.pdf', sha256: '6d6dac3c4f1cecfa7c1b8e518eef22828a55f64d41264500026cbc0bb77da4e5', publicPassage: false },
  { id: 'ecb_2026', title: 'Economic Bulletin', publisher: 'European Central Bank', issue: 'Issue 6 / 2026', pages: 157, chunks: 613, url: 'https://www.ecb.europa.eu/pub/pdf/ecbu/eb202606.en.pdf', sha256: 'dce104a6108c33a97f1fa86648794a1287016b189b1631f82b9e635ef3f9d520', publicPassage: false },
  { id: 'frmp_2026', title: 'Monetary Policy Report', publisher: 'Federal Reserve', issue: 'July 2026', pages: 77, chunks: 287, url: 'https://www.federalreserve.gov/monetarypolicy/files/20260710_mprfullreport.pdf', sha256: 'd8109da697abd4c58a5f1fb074d4b5cbcd197df1baf9e1f6e7620e5812e14a37', publicPassage: false },
  { id: 'gep_2026', title: 'Global Economic Prospects', publisher: 'World Bank', issue: 'June 2026', pages: 200, chunks: 1175, url: 'https://thedocs.worldbank.org/en/doc/2b672b3b0415d6b66c45b66579db4ef5-0050012026/original/GEP-Jun-2026.pdf', sha256: '26b979eb197c903798b65d085ee5541c8e346d552d932c3c138a0c3d5950629f', publicPassage: false },
  { id: 'oecd_2026', title: 'OECD Economic Outlook, Interim Report: Weathering Successive Shocks', publisher: 'OECD', issue: 'September 2026', pages: 25, chunks: 105, url: 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/09/oecd-economic-outlook-interim-report-september-2026_8312492f/f751d02b-en.pdf', sha256: '1b6f0ed6d7d84d35bec56a9b1710fa787aa2243cd9ebfddcd0c9504227f86f6e', publicPassage: false },
  { id: 'un_wesp_2026', title: 'World Economic Situation and Prospects', publisher: 'United Nations', issue: '2026', pages: 216, chunks: 1074, url: 'https://desapublications.un.org/file/21554/download', sha256: '64020fc687899e1b43ff8e35c99fdf124a86248fbed2894aa546835bfa99d5c3', publicPassage: false },
  { id: 'ecb', title: 'Economic Bulletin', publisher: 'European Central Bank', issue: 'Issue 7 / 2025', pages: 126, chunks: 467, url: 'https://www.ecb.europa.eu/pub/pdf/ecbu/eb202507.en.pdf', sha256: 'cea88accb46726306dae6dab81937d6a5efdcfd4f302e94ed2fc9fdf6bba4e4b', publicPassage: true },
  { id: 'fm', title: 'Fiscal Monitor: Spending Smarter', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 106, chunks: 573, url: 'https://www.imf.org/-/media/files/publications/fiscal-monitor/2025/october/english/text.pdf?la=en', sha256: '002c7852a34747e55741646ad750463cc63a554587bd5f6dbaff0e1bb8b9b440', publicPassage: false },
  { id: 'frmp', title: 'Monetary Policy Report', publisher: 'Federal Reserve', issue: 'February 2025', pages: 83, chunks: 280, url: 'https://www.federalreserve.gov/publications/files/20250207_mprfullreport.pdf', sha256: '728293cfbfeb672979115ab969cf6ec85cd62977f643eaee397334c6a9534ebd', publicPassage: false },
  { id: 'gep', title: 'Global Economic Prospects', publisher: 'World Bank', issue: 'June 2025', pages: 254, chunks: 1524, url: 'https://thedocs.worldbank.org/en/doc/8bf0b62ec6bcb886d97295ad930059e9-0050012025/original/GEP-June-2025.pdf', sha256: 'f3f1f5153c7c04a09271b0e7740566857e5f795bbbc7e002d832a534c27f5715', publicPassage: false },
  { id: 'gfsr', title: 'Global Financial Stability Report: Shifting Ground beneath the Calm', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 126, chunks: 777, url: 'https://www.imf.org/-/media/files/publications/gfsr/2025/october/english/text.pdf', sha256: 'ea0e690ff12999b97a76508ddc0d39fc42f3af3d90dec304f0315ccc1986343b', publicPassage: false },
  { id: 'oecd', title: 'OECD Economic Outlook, Interim Report', publisher: 'OECD', issue: 'September 2025', pages: 24, chunks: 96, url: 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/09/oecd-economic-outlook-interim-report-september-2025_ae3d418b/67b10c01-en.pdf', sha256: 'f3d64751363d12e1dd140b69ebb2c81ac7697f27ec6bf55194ce9f4484fb96df', publicPassage: true },
  { id: 'weo', title: 'World Economic Outlook: Global Economy in Flux', publisher: 'International Monetary Fund', issue: 'October 2025', pages: 186, chunks: 1050, url: 'https://www.imf.org/-/media/files/publications/weo/2025/october/english/text.pdf', sha256: 'a0ece6ccdd7d40f38f453dd77728c67d8d5ccf79558ed6a6c778850767abd093', publicPassage: false },
];
