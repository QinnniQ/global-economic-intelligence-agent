# Interview preparation, in plain English

Use these as explanations of **the current repository**. Adapt the first-person wording only where it accurately reflects your own work. Repository history cannot establish who personally made each decision or how much was independently authored.

## 30-second overview

“The Global Economic Intelligence Agent is a small economic research workspace. A visitor can compare annual World Bank indicators for five countries, ask a bounded question, inspect the exact observations and source links behind the answer, and export that displayed briefing. The public application uses React and a Cloudflare Worker. Numerical findings are calculated in code, while a tiny reviewed report index adds dated context. It has a saved demo for reliability and a live data mode. I am careful to label the public analyst as deterministic, not an LLM or autonomous agent.”

## 90-second technical explanation

“The React front end calls same-origin `/api` routes on a Cloudflare Worker. The Worker validates country, indicator, year range and question length. In live mode it requests World Bank's Indicators API, handles pagination, timeout, transient retries, nulls, forecast flags and malformed values, and caches validated series for six hours. Each response keeps the observation year separate from retrieval time and any provider update date.

“For an analyst question, deterministic code selects supported indicators and calculates descriptive findings. Changes between annual rates are percentage-point changes. A two-passage, manually reviewed report index can return page-linked context when the country and topic match. A separate Source library search indexes pages of all 13 PDFs and opens the publisher file at the matching page; it does not write the analyst answer. Indicator values come from the World Bank series or the labelled saved fixture. The PDF export uses the analysis already on screen. The separate Python/Chroma/OpenAI code is a local prototype, not the deployed backend. Its local store has 9,317 vectors using Chroma's default MiniLM model.”

## Five-minute deeper walkthrough

1. **Problem and user:** Someone preparing a quick country briefing needs to know what an annual indicator actually says, when it was observed, and where it came from. The app constrains scope to five countries and three indicators to make source tracking and verification feasible.
2. **Data boundary:** `web/worker/worldbank.ts` calls the official API. It validates the two-element JSON response, follows pages, excludes null or nonnumeric values, preserves genuine zero, sorts years and keeps source metadata. `web/worker/index.ts` bounds inputs and returns consistent JSON errors and request IDs.
3. **Calculation boundary:** `web/src/domain.ts` and `web/worker/analysis.ts` compute findings. A 3.3% rate becoming 3.9% is a rise of **0.6 percentage points**, not 0.6%. One observation is not a trend; gaps between years are disclosed.
4. **Evidence boundary:** `web/worker/reports.ts` holds two verified excerpts with publisher, URL, publication date, page, stable passage ID, checksum and ingestion version. Matching is curated by geography, indicator and terms. This is retrieval, but neither vector search nor generative RAG. Citation-ID validation catches unknown IDs; human review is still needed to decide if a claim is supported.
5. **Operations:** `web/wrangler.jsonc` deploys assets and API to the same Worker with preview and production names. The Worker cache lasts up to six hours and is local to a Cloudflare data centre. `/api/health` checks application response only; a separate scheduled probe checks representative World Bank series. GitHub's external monitor checks the public host. Weekly checks compare all 15 saved values with the API and scan two accessible official report indexes for newly linked editions. Changes create review issues rather than silently changing the site. If one live analysis indicator fails, the successful findings remain visible and the missing series are named.
6. **Verification:** `web/tests/product.test.ts` has 23 passing tests for deterministic logic, mocked World Bank responses, API routes, partial analysis, PDF construction and the page search. The versioned ten-question analyst set checks evidence and rejection behavior; a separate 30-case search set checks report discoverability and abstention. Commit `7b8776c` passed the web, Python and Docker CI jobs. On 20 October, the new production release was browser-checked in Source library and saved/live analyst modes, and the external production probe passed. Scheduled alert delivery has not yet been observed.

## Technology glossary tied to files

| Term | What it means here |
| --- | --- |
| **API** | Documented HTTP routes in `web/worker/index.ts` that let the browser request catalog, series, analysis and health data. See `docs/API.md`. |
| **Backend** | The public Cloudflare Worker: input validation, World Bank requests, caching and deterministic analysis. |
| **React** | The front-end framework in `web/src/main.tsx`; TypeScript is the language used by front and Worker. |
| **Cloudflare Worker** | The hosted JavaScript runtime serving the API and built site. It is hosting, not a model or database. |
| **Embeddings** | Numeric vectors used to compare text meaning. The local Python file explicitly selects Chroma's default ONNX MiniLM embedding function. Its 9,317 vectors cover 13 PDF editions; the 4,767 original vectors were independently recomputed and matched. The public app uses no embeddings. |
| **Vector search** | Nearest-neighbor lookup over embeddings. The public PDF page search uses word frequencies, not vectors. The local Chroma artifact is separate from the public Worker and needs retrieval and citation evaluation before any public vector-search claim. |
| **RAG** | Retrieval-augmented generation: retrieve documents, supply them to a model, and generate a grounded answer. The public app retrieves context but does not generate with a model, so call it curated retrieval with deterministic analysis. |
| **Caching** | Temporarily reusing a validated live series for six hours. `web/worker/index.ts` uses Cloudflare's Cache API; `retrievedAt` remains the original fetch time. |
| **CI/CD** | GitHub Actions in `.github/workflows/ci.yml` tests and builds on push/PR. Deployment is by explicit Wrangler scripts in `web/scripts/deploy.mjs`, not automatic production release. |
| **Deployment** | Publishing the Vite-built assets and Worker with Wrangler using `web/wrangler.jsonc`. A successful local build does not update the public URL. |

## Likely questions and defensible answers

**Why use deterministic calculations?** Because annual indicator values and arithmetic must be reproducible. A model can help summarize evidence later, but should not invent or silently adjust numbers.

**How do you know a citation supports a sentence?** Code checks that the ID exists in the returned evidence. That is necessary but insufficient; a reviewer still checks the actual observation or passage against the claim. No independent model-quality score is claimed.

**What happens when World Bank is down?** The API returns a traceable error after bounded attempts. On Overview and Compare, successful series remain visible when another request fails. The UI names unavailable series and offers retry or the explicitly dated saved demonstration. It never silently presents the snapshot as live.

**Why no public LLM?** The current Worker has no configured model service, cost control or validated vector index. A model path without grounded evaluation would weaken the reliability of the demo.

**Was the original agent RAG?** Yes, the local Python design extracts text from PDFs, chunks it, stores passages in Chroma, retrieves passages for a question, and supplies them to an OpenAI model for answer synthesis. That is distinct from the currently deployed Cloudflare demo, which uses curated retrieval and deterministic analysis. The local code now explicitly selects Chroma's default local MiniLM embedding function. Retrieval relevance and answer quality still need evaluation.

**Is the local Python prototype production ready?** No. It uses FastAPI, Chroma and OpenAI code, but it is separate from the public Worker. The new 2026 chunks have PDF page metadata; legacy chunks still lack it. Retrieval relevance and model answer quality still need work. Some Python tests mock the model and retrieval, so they do not establish real quality.

**How do you keep it robust and current?** “I keep the saved demo dated, run live World Bank requests with validation, bounded retries and a six-hour cache, and retain successful indicators when another fails. A scheduled Worker probe checks the upstream directly; GitHub checks the public routes. Weekly jobs compare all 15 saved values with World Bank and flag new links on accessible official report indexes. Those checks create a review task rather than silently publishing new figures or reports. The source catalog, PDF hashes, page search and a sample stored vector are checked in CI. I can restore a checksummed local Chroma archive. The remaining gaps are publisher coverage, global rate limiting and proven alert delivery.”

**What would you build next?** Use the new scheduled probe and public monitor to investigate intermittent provider timeouts by region and request ID, without logging questions. Then expand the publisher watch beyond the two accessible indexes, add verified page metadata to legacy Chroma chunks, and measure retrieval and claim support before adding bounded server-side synthesis.

## Three actual limitations

1. The public analyst has only two curated passages. Page search covers all 13 PDFs, but it is lexical navigation, not semantic RAG or proof that an answer is supported.
2. Live World Bank mode has succeeded, but an intermittent provider timeout was also reproduced on 20 October 2026. Partial data handling protects the interface, but it does not make the upstream source continuously available. Keep the saved mode ready.
3. The saved fixture has a single rounded observation per indicator. It supports a dependable cross-section but no trend or current-period inference.

## How to discuss AI coding assistance

You may say the repository was developed or reviewed with AI assistance **only if that matches your own experience**. This review read the public and local paths, checked report-file checksums, ran the TypeScript tests and build, exercised the deployed saved analyst and PDF, and numerically verified all stored Chroma vectors against its default embedding function. It did **not** validate model output, prove when or where the Chroma vectors were created, or establish who authored earlier commits. Confirm your own contribution and review history before making personal claims.

## Interview rehearsal for 21 October 2026

- Lead with the user problem and the evidence trail, then explain React, the Worker, and the World Bank API. Do not start with the technology list.
- Demo the saved path first. It gives you stable numbers and lets you show the source table, comparison, bounded analyst, report context, limitations, and PDF in three minutes. Use live mode as an optional second branch.
- In Source library, search **“Netherlands inflation”** and open a publisher PDF page. Explain that this page finder searches the reports, while the analyst uses two reviewed passages. A linked page is a lead for inspection, not an automatically validated claim.
- State the reliability improvement concretely: independent live series can succeed even if one fails; a scheduled Worker probe and external public monitor detect provider failures; weekly checks flag saved-value revisions and new links for human review.
- If asked “Where is the AI?”, distinguish the two versions. The original local Python agent implements PDF retrieval plus OpenAI synthesis. The current public demo uses deterministic analysis and curated retrieval; it is not the hosted RAG service. Explain the validation work needed before deploying the Python synthesis path.
- If asked “What did you personally do?”, describe only work you can personally substantiate. Separate decisions you made from implementation you reviewed or produced with AI assistance.
- Ask the interviewer how their teams validate source quality and claim support in client-facing AI systems, and how they decide when a deterministic workflow should gain a model step. These connect this project's trade-offs to Xebia's stated emphasis on [trusted data foundations](https://nl.xebia.com/) and [engineering craftsmanship](https://xebia.com/careers/?filters=Netherlands).
