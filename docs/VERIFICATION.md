# Verification record — 20 October 2026

## Repository and deployment state

At inspection the checkout was on `main`, tracking `origin/main`, at `e3665dd` (“Attach economic intelligence custom domain”), with no existing user changes. The new code was deployed to the existing **preview** Worker as version `32fca619-fef7-45de-8056-f2bb49c54301`, then to the existing **production** Worker after user approval as version `ee986b90-75b6-4835-a574-cb714e50486a`. The public URLs in `web/wrangler.jsonc` were preserved. No paid service was enabled.

## Checks actually run

| Check | Result | What it establishes |
| --- | --- | --- |
| `npm test` in `web/` after edits | **18 tests passed** | Deterministic logic, mocked World Bank success/failure/pagination, report selection, request validation, health route and PDF construction. This is not proof of current provider availability. |
| `npm run build` in `web/` after UI/API edits | **Passed** | TypeScript and Vite built Worker and client. Vite warned that the main and PDF chunks exceed 500 kB; this is a performance follow-up, not a build failure. |
| Ten-question `web/eval/questions.v1.json` set, executed by a Vitest case | **10 fixture cases matched** expected indicator/report IDs or expected rejection | Saved-data deterministic behavior only. No model output or live data quality score. |
| SHA-256 on `data/reports_pdfs/ecb.pdf` and `oecd.pdf` | **Matched** the hashes in `web/worker/reports.ts` | The bundled PDF files match the indexed checksums. It does not establish licensing or that every report claim is true. |
| `python -m pytest -q` locally | **Not run: `pytest` missing** in the available Python 3.14 environment | CI runs the Python suite on Python 3.11; the tests mock model/retrieval behavior. |
| [GitHub Actions run 39418992213](https://github.com/QinnniQ/global-economic-intelligence-agent/actions/runs/39418992213) for commit `2ed393c` | **Passed:** web tests/build, Python 3.11 pytest/coverage, Docker image build | CI verifies the checked-in release on Ubuntu; Python tests use stubs and do not establish real model quality. |

## Browser and external-service observations

The existing production page at [econ.nickcloud.dev](https://econ.nickcloud.dev) loaded in the in-app browser. In saved mode, the Netherlands overview showed GDP growth **1.1% for 2024**; the analyst answered the exact question **“What do the latest available economic indicators show?”** with GDP growth 1.1% (2024), inflation 3.3% (2024), and modeled unemployment 3.9% (2025). Indicator links, an ECB page-11 contextual passage, limitations and the generated timestamp were visible. **Export this briefing** downloaded a PDF. Desktop and narrow initial browser views were inspected; a full automated mobile journey and accessibility audit were not completed.

Before the new deployment, the production **Live data** toggle for Netherlands showed “Data could not be loaded. The service could not complete this request.” Direct shell requests to both the World Bank and preview host failed DNS resolution in the sandbox; an in-app direct World Bank navigation timed out. **After deployment, both preview and production retrieved live observations through their Workers:** Netherlands GDP growth was 1.78% in 2025 and 1.07% in 2024; the UI showed retrieval on 20 October 2026 and provider update 8 October 2026. Both live analysts returned 2025 GDP growth 1.78%, inflation 3.2% and modeled unemployment 3.87%, with 0.71, −0.14 and +0.17 percentage-point changes from 2024 respectively. The preview GDP table exposed years back to 2000. Both `/api/health` routes returned `status:ok` and `upstreamChecked:false`. The earlier failure's root cause remains unestablished. No latency benchmark was conducted.

## Evaluation observations

- The ten saved-data cases cover answerable questions, irrelevant/missing report evidence, unsupported forecasts, aggregate requests, multi-country questions, a selection conflict and instruction-like text.
- Code checked evidence IDs and that one-observation fixture answers contain no percentage-point trend. Manual review of the deployed Netherlands overview found its indicator years, values and ECB passage label consistent with the fixture and displayed limitations.
- This is a small, versioned behavioral set. Retrieval relevance, claim support and uncertainty handling are partially inspected by humans and rules. There is **no generative output** to score, and no fabricated accuracy or latency percentage.

## Remaining risks and release checks

1. Investigate the live World Bank failure from the Worker side; capture request ID and status without logging user questions. Test an official API response from an unrestricted environment.
2. Preview health, saved analyst, saved Netherlands/Germany/France comparison, live overview/table, live analyst and PDF download were checked. At a 390×844 mobile viewport, the comparison controls and saved analyst/evidence layout were inspected and the saved question was run. Production health, saved analyst, live overview, live analyst and **live briefing PDF download** were then checked after deployment. This was a visual smoke check, not a comprehensive accessibility audit.
3. The two-passage corpus has limited recall. The Python/Chroma index is not validated for its embedding function or source provenance. Public vector RAG and model synthesis remain unavailable.
4. The Worker has only a per-isolate request guard; it is not a global rate limit. The browser bundle is relatively large.

Rollback, if a later deployment is made: select the previous Worker version in Cloudflare **Deployments**, or use `npx wrangler rollback --name global-economic-intelligence` for production after confirming the target version. [Cloudflare rollback guide](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/).

## Final interview review after the dropdown fix

On 20 October 2026, the production Worker was updated to version `154f8aba-ffb8-40da-a1dc-52e9318bb567` from commit `fd6c356`; `main` and `origin/main` matched. The changed release built successfully and all 18 web tests passed. The new Economy control was verified in preview and production as a native dropdown listing Netherlands, Germany, France, United Kingdom (UK), and United States (US). Preview selections of France, UK and US changed the URL, values and source links.

A fresh production browser review exercised the saved Netherlands overview and underlying data table, the three-country GDP comparison, the default saved analyst question with source evidence, and the methodology page. Live Netherlands Overview displayed 2025 GDP growth 1.78%, inflation 3.2%, and modeled unemployment 3.87%; the GDP table included 2024 at 1.07%, showed the original cached retrieval time, and labelled the provider update as 8 October 2026. These are point-in-time observations, not a guarantee of provider availability during the interview.

An independent preview browser request for the US reproduced World Bank timeouts for two indicators while inflation succeeded. The new partial-result behavior kept the inflation card and historical series visible, named the two unavailable indicators, displayed a request ID, and offered separated retry and saved-demo controls. The underlying intermittent timeout has not been traced to a specific provider or edge cause. The saved three-minute path is therefore the dependable demo route.
