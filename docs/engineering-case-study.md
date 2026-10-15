# Engineering case study: Global Economic Intelligence Agent

## Problem and audit

The starting repository combined FastAPI, Streamlit, a World Bank fetcher, Chroma, OpenAI calls and ReportLab. Its README described a broad product, but inspection found a thinner implementation: the fetcher did not paginate or time out, country detection matched substrings (`us` in ordinary words), the agent made one model call per indicator before a final call, and the Chroma code initialized an OpenAI embedding object that was not used by its `add` or `query_texts` calls. Those calls both used the collection default, but the model and ingestion version were not recorded. The public ingestion route had no authorization. PDF export reran the analysis and wrote to a country-wide filename, so simultaneous exports could overwrite one another. Existing tests covered only smoke and keyword cases.

I kept the local Python prototype intact as a research reference and built a bounded public experience around three indicators and five supported countries. This scope allows every visible number to carry a year, unit and source.

## Consequential choices

1. **One Cloudflare Worker plus static React assets.** This integrates the public UI and API under one origin and avoids claiming that a Python/Chroma process runs on Cloudflare's ephemeral local filesystem. The original collection is not migrated; doing so responsibly would require passage metadata repair, a compatible embedding pipeline, and a reindex check.
2. **Deterministic analysis first.** World Bank observations are parsed and checked, then application code calculates latest values and percentage-point changes. The public answer does not ask a model to infer arithmetic or invent a forecast. No paid inference is enabled.
3. **A small, inspectable report index.** Two passages were checked against local PDF page text and linked to official publisher PDFs. Retrieval requires country and topic relevance. The report is contextual evidence, not a substitute for a cited indicator value. This is intentionally narrower than general RAG.
4. **Export the displayed object.** The browser renders a PDF from the analysis already on screen. Concurrent visitors do not share a filename or storage path, and export cannot silently change conclusions.
5. **Separate saved data and live data.** The saved demonstration uses dated, rounded World Bank values, so it remains useful without the upstream API or a model. A single saved observation is never described as a trend. Live mode is the route to full historical charts.

## Architecture and operations

See the README diagram. The Cloudflare Worker validates parameters and fetches annual World Bank series with an eight-second timeout, bounded retry, explicit pagination and a six-hour edge cache. It has no database, persistent local directory or secret. Preview and production use separate Worker names. The client keeps comparisons in the URL and builds a PDF only when asked.

Per-isolate throttling and bounded inputs are useful guardrails; they are not an account-wide rate limit. A Cloudflare account rule should be added for public scale. The current report index needs editorial updates when reports age. The initial React bundle is larger than ideal because of charting; PDF code is lazy-loaded.

## Verification and honest limits

Unit tests cover parsing, evidence selection, arithmetic, pagination, failures, citation IDs and isolated PDF generation. The saved-demo flows were inspected in a browser at desktop and mobile widths. A representative PDF was rendered and visually reviewed. CI runs without paid calls. The development environment blocked direct access to `api.worldbank.org`, so the live API and Cloudflare runtime still need smoke tests after deployment. Wrangler reported no authenticated account, so no live URL is claimed.

The next evidence-system milestone is a fully versioned ingestion pipeline: record publisher/title/date/page/URL/checksum for each passage, normalize and hash documents, reindex on content or embedding-model changes, store vectors and passages in durable Cloudflare services or an explicitly operated backend, and evaluate relevance and support against the versioned question set before enabling model synthesis.
