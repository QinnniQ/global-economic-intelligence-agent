# Public API contract

All routes are same-origin under `/api`. Successful JSON responses include `x-request-id`. Failures use `{"error":"human-readable message","requestId":"UUID"}` and the same header. The Worker sends `Cache-Control: no-store` to browsers; only validated live series are retained in its private six-hour edge cache. Report retrieval uses no paid model API and has no visitor authentication. Inputs are allowlisted to five country codes (`NL`, `DE`, `FR`, `GB`, `US`) and three World Bank indicator codes (`NY.GDP.MKTP.KD.ZG`, `FP.CPI.TOTL.ZG`, `SL.UEM.TOTL.ZS`).

## `GET /api/health`

Returns HTTP 200: `{"status":"ok","upstreamChecked":false,"modelGenerationEnabled":false}`. The false value means the Worker has no server-side model generation. This confirms only the Worker handler is responding.

## `GET /api/catalog`

Returns `countries`, `indicators` (names, units and definitions), `modelGenerationEnabled:false`, and `onDeviceRagAvailable:true`. Browser generation still requires WebGPU and a model download.

## `GET /api/series`

Example: `/api/series?country=NL&indicator=NY.GDP.MKTP.KD.ZG&start=2020&end=2026&mode=live`.

`mode` is `live` (default) or `demo`. Years are integers from 1960 through the current UTC year, with `start <= end` and a maximum 65-year span. Unsupported inputs receive HTTP 400. Temporary World Bank failures receive 503; malformed provider data receives 502. HTTP 429 means the local request guard rejected rapid calls.

The response shape is:

```json
{
  "country": "NL",
  "indicator": "NY.GDP.MKTP.KD.ZG",
  "provider": "World Bank",
  "frequency": "annual",
  "name": "GDP growth (annual %)",
  "definition": "Annual percentage growth of GDP at market prices based on constant local currency.",
  "unit": "%",
  "sourceUrl": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=NL",
  "retrievedAt": "2026-10-15T00:00:00.000Z",
  "providerUpdatedAt": null,
  "observations": [{ "year": 2024, "value": 1.1 }],
  "stale": true
}
```

This exact example is `mode=demo`: the date is the saved review date, **not** a live retrieval. Live responses have `stale:false`, actual retrieval/provider dates, and `cacheStatus` of `network` or `cached`. `observations` can be empty. Null and forecast-status values are omitted and zero is preserved. The Worker retrieves all declared pages, up to 20, and rejects changing pagination metadata.

## `POST /api/analysis`

JSON request:

```json
{"country":"NL","mode":"demo","question":"What are the latest GDP growth and inflation observations?"}
```

`question` must be 8–500 trimmed characters; request body is capped at 1,500 characters. One selected country and supported topics are required. Country conflicts and unsupported aggregate or forecast questions return HTTP 400. The response is an `Analysis` object with `id`, `question`, `country`, `generatedAt`, `mode:"deterministic"`, `indicators`, validated `series`, `findings` (text and evidence IDs), `interpretation`, `risks`, `limitations`, `evidence` (indicator and optional report metadata), `reportStatus`, and optional `unavailableIndicators`. Live analysis retains successful series when another indicator fails, lists the missing indicator codes and adds a limitation. If none succeeds, it returns 503. The answer does not invoke a model. A report passage is included only if the curated index matches the question; its source URL, publication date, page, checksum and ingestion version are returned with it. Findings cite only known evidence IDs.

Example finding from the saved fixture:

```json
{"text":"GDP growth was 1.1% in 2024, the saved demonstration observation.","evidenceIds":["WB:NL:NY.GDP.MKTP.KD.ZG"]}
```

No API endpoint regenerates a PDF. `web/worker/pdf.ts` renders the displayed `Analysis` object in the browser. There is no public document ingestion endpoint.

## `POST /api/report-excerpts`

JSON request: `{"question":"Netherlands inflation","pages":[{"reportId":"ec_forecast_2026","page":138}]}`. The question must be 8–300 characters, the body at most 1,200 characters, and the `pages` array at most five entries. Report IDs and PDF page numbers are checked against the catalog. The browser selects candidate pages using the lexical index; the Worker reads hash-matched static page artifacts internally and returns short excerpts. Each response item has `reportId`, `title`, `publisher`, `issue`, `page`, `url` pointing to the publisher PDF page, and `text`. Invalid input returns 400 or 413, request guard rejection returns 429, and an asset failure returns 503. Direct requests for `/report-pages.v1/*` return 404. The removed `/api/rag` paid-model route returns 404. See [Public report RAG](PUBLIC_RAG.md) for the architecture and limits.
