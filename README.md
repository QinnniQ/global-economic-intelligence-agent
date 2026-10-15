# Global Economic Intelligence Agent

An economic research workspace that asks: **What is happening in this economy, what evidence supports it, and what deserves closer attention?** The public app is React and TypeScript with a Cloudflare Worker API. It starts with a dated, genuine-data demonstration and offers a live World Bank mode.

[Nicholai Gay's AI engineering portfolio](https://profile.nickcloud.dev/) · [LinkedIn](https://www.linkedin.com/in/nicholai-gay-201905148/) · [CI status](https://github.com/QinnniQ/global-economic-intelligence-agent/actions/workflows/ci.yml)

![Economic overview in the saved demonstration, supplied by the project owner](docs/overview.png)

**Release status, 15 October 2026:** the app is deployed on Cloudflare at [econ.nickcloud.dev](https://econ.nickcloud.dev). The saved-data overview, comparison, source-linked analyst and PDF workflow were exercised in a browser. The Cloudflare preview and production Workers both served the app, and live Netherlands observations were retrieved through the deployed API. The custom domain homepage and API returned HTTP 200 over valid HTTPS. No paid model service is configured.

## Visitor experience

- Explore GDP growth, consumer-price inflation and modeled ILO unemployment for the Netherlands, Germany, France, the United Kingdom and the United States.
- Use a clearly labelled saved demonstration without any credentials. Live mode retrieves full annual World Bank series.
- Compare two to four countries across a chosen indicator and date window, with an aligned chart, table, common observation year and shareable URL.
- Ask a single-country question and inspect source-linked findings, relevant page-linked report passages and explicit limitations.
- Export the **displayed** analysis as a PDF in the browser. Export never reruns retrieval or analysis.

The public analyst is deterministic. It makes no paid model calls, forecasts, causal claims or personalized investment recommendations. The Python and Streamlit prototype remains for local research and is not part of the Cloudflare deployment.

## Run and verify

```bash
cd web
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://127.0.0.1:5173`. The saved demonstration needs no credentials. Live mode needs outbound access to `api.worldbank.org`.

```bash
cd web
npm test
npm run build
```

The legacy Python prototype can still be started with `docker compose up --build` after copying `.env.example` to `.env` and supplying an `OPENAI_API_KEY`. Ingestion is disabled unless `INGEST_ADMIN_TOKEN` is set, and Compose binds the legacy services to localhost. Its raw model endpoints must **not** be exposed publicly. The [offline analysis trace](docs/offline_trace.md) walks through its inspectable `raw_data`, `rag_passages`, `rag_sources`, and `rag_status` fields with stubbed evidence and no API key.

## Architecture

```mermaid
flowchart LR
  B[Browser: React workspace] -->|Same-origin /api| W[Cloudflare Worker]
  W --> WB[World Bank Indicators API]
  W --> S[Versioned rounded demonstration]
  W --> R[Reviewed report passage index]
  B -->|Displayed analysis object| P[Browser PDF renderer]
  L[Local-only Python prototype] --> C[(Local Chroma store)]
```

The Worker needs no database or persistent filesystem. Its static assets and API deploy together. The existing Chroma directory is a persistent **local** artifact; no Vectorize migration or reindex is claimed. Cloudflare's [React/Worker tutorial](https://developers.cloudflare.com/workers/vite-plugin/tutorial/), [Python package guidance](https://developers.cloudflare.com/workers/languages/python/packages/) and [Worker limits](https://developers.cloudflare.com/workers/platform/limits/) informed this choice.

## Data and evidence

The Worker accepts only five country codes and three indicator IDs. Live requests include a date range, page and page size. The adapter checks response shape, fetches reported pages (up to 20), drops null and malformed values without substituting zero, and records retrieval and provider-update timestamps. Requests time out after eight seconds and receive at most one retry for a temporary failure. Live series are cached for six hours. An upstream failure is displayed as an error; stale values are not silently substituted.

[Indicator definitions and units](web/src/domain.ts) distinguish GDP growth from GDP level and inflation from the CPI level. Changes between annual rates are reported in **percentage points**. Observation year is separate from retrieval date. The latest year may differ by country or indicator.

The [saved demonstration](web/src/demo.ts) contains World Bank values rounded to one decimal: 2024 GDP growth and inflation, and 2025 modeled unemployment. They were transcribed from official [Netherlands/Germany/France](https://data.worldbank.org/?locations=BE-NL-LU-DE-FR-IT) and [United Kingdom/Germany/United States/France](https://data.worldbank.org/?locations=GB-DE-US-FR) pages reviewed on 15 October 2026. The provider may revise those pages. The saved demo has **one observation per series** and cannot establish a trend.

The hosted [report index](web/worker/reports.ts) has two short passages reviewed against repository PDFs: ECB *Economic Bulletin* Issue 7 / 2025, page 11, and OECD *Interim Economic Outlook* September 2025, page 13. Stable passage IDs, title, publisher, official link, publication date, page, checksum and ingestion version are recorded. Retrieval requires matching geography and topic. Report excerpts are dated context, not validation of World Bank values. Numerical findings cite only the series used, and citation IDs are checked in code. Missing relevant passages are disclosed.

## Privacy and limits

The public app stores no prompts or PDFs. It has no client-side credentials, paid inference, public ingestion or file upload. React renders external text safely. API inputs are bounded. A small per-isolate request guard reduces rapid repeated calls; it is **not** a global rate limit. Configure an account-level Cloudflare rate limiting rule for `/api/*` before high-traffic promotion. Structured failure logs contain request ID, route, status and error type, not question text.

This release has five countries and three indicators. Its report index is curated rather than a general search corpus. It does not support EU or euro-area aggregates, multi-country analyst questions, forecasts or live LLM synthesis. Annual series and report dates can lag economic events. The PDF uses standard Helvetica and ASCII-normalised text for portability.

## Evaluation

`web/tests/product.test.ts` covers country aliases and ambiguity, null and zero values, pagination, mixed years, percentage-point changes, upstream failure, report relevance and malicious input, citation IDs, and concurrent isolated PDFs. The [question evaluation set](web/eval/questions.v1.json) defines evidence expectations and a human assessment rubric. Automated checks assess structure and arithmetic; human review is required for claim support and interpretation.

Measured locally on 15 October 2026: **14 web tests passed**, the TypeScript production build and production Worker dry run passed, and representative saved-demo and live-data one-page PDFs were rendered and visually inspected. Saved-demo browser flows were checked at desktop and mobile widths; a live Netherlands analyst answer returned annual World Bank data. No accuracy, latency or accessibility score is claimed.

Post-deploy smoke checks confirmed the preview homepage, saved-data comparison and analyst views, live World Bank series and live analyst answer. The production homepage, saved-data analyst and live World Bank series were also checked. New `workers.dev` routes briefly returned Cloudflare error 1042 during propagation; subsequent checks succeeded.

## Cloudflare deployment

[wrangler.jsonc](web/wrangler.jsonc) defines separate preview and production Worker names. The production Worker serves [econ.nickcloud.dev](https://econ.nickcloud.dev) as a Cloudflare Custom Domain and retains its [workers.dev URL](https://global-economic-intelligence.nicholai-gay.workers.dev). The [preview Worker](https://global-economic-intelligence-preview.nicholai-gay.workers.dev) has its own `workers.dev` URL. The existing `infernomics.nickcloud.dev` site remains untouched. No secret or paid service is required. For a fresh checkout or redeployment, from `web/`:

```bash
npx wrangler login
npm run deploy:preview
# Open the printed workers.dev URL and check overview, compare, analyst and PDF.
# Switch to Live data and verify a Netherlands series and timestamps.
npm run deploy:production
```

The scripts select the Cloudflare environment, build assets and Worker together, verify the intended Worker name, and deploy the generated configuration. The production configuration attaches only `econ.nickcloud.dev`; Cloudflare manages its DNS and certificate. Roll back the named Worker via its Cloudflare **Deployments** page or `npx wrangler rollback --name global-economic-intelligence` after selecting the previous version. See Cloudflare's [rollback instructions](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/).

Cloudflare lists a Free tier with 100,000 Worker requests/day and 10 ms CPU per invocation. Its Paid tier starts at US$5/month with usage-based overages. The app needs no paid model, D1, R2 or Vectorize, and renders PDFs in the browser to avoid Worker PDF CPU cost. Check [current pricing](https://developers.cloudflare.com/workers/platform/pricing/) before operating at scale. No paid service has been enabled.

## Additional material

- [Engineering case study](docs/engineering-case-study.md)
- [60–90 second demo script](docs/demo-script.md)
- [CV and LinkedIn wording](docs/portfolio-copy.md)
- [Versioned evaluation set](web/eval/questions.v1.json)
- [Legacy offline analysis trace](docs/offline_trace.md)
