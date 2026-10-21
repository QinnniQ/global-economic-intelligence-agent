# No-charge public report mode

The public analyst has two paths. **Observed data** calculates findings from saved or live World Bank observations. **Report RAG** retrieves pages from 13 hash-verified PDF editions and optionally synthesizes a short answer in the visitor's browser. It makes no paid inference API call. It does not use the local Python Chroma vectors.

## How it works

1. `scripts/build_report_search.py` builds the lexical page index from the verified PDFs.
2. `scripts/build_report_pages.py` verifies the same manifest SHA-256 hashes and page counts, then produces 13 deterministic page-text assets. Requests for those assets are blocked publicly by the Worker. The Worker reads them internally and returns at most five short excerpts per question.
3. The browser ranks PDF pages with the existing page index. Each returned excerpt includes the publisher, issue, PDF page and official link. Retrieval works without a model or special browser support.
4. If the visitor chooses **Generate on this device**, Transformers.js downloads a quantized SmolLM2-135M model from Hugging Face (about 117 MB for the main model file) and runs it through WebGPU on the visitor's device. The answer is labelled experimental and the original excerpts remain visible. If WebGPU or the download fails, retrieval still works.

The browser-generated text is **not** a verified economic finding. A small model can misread passages or invent links between them. The code withholds a local answer when it adds a numeric token absent from the retrieved excerpts, but that is only one guard. Check statements against the linked PDF page before using them. The corpus is dated and does not replace live World Bank observations.

The page index is lexical rather than semantic. The public mode is therefore retrieval-augmented generation when the optional on-device model runs, but it is **not Chroma vector RAG**. Without WebGPU it is a cited report retrieval tool. Describe that distinction plainly in the interview.

## Cost and privacy

There is no OpenAI API key, OpenAI vector store, Workers AI binding, or billable model call in this mode. The site serves static index and JavaScript assets, and the Worker serves short report excerpts. Model files come from Hugging Face directly to the browser and are cached by the browser when possible. Visitor questions are sent only to the same-origin Worker for excerpt selection; the optional synthesis runs locally. The project owner's Cloudflare plan and ordinary Worker request usage still follow Cloudflare's plan terms, so this design avoids **new model charges** rather than promising that all hosting is free under every account plan.

## Verification

Run `python scripts/build_report_pages.py --check` and `python scripts/build_report_search.py --check` using a Python environment with `pypdf`, then `cd web && npm test && npm run build`. The tests check report ID and page bounds, hash-matched artifact metadata, excerpt selection and that no paid model route is exposed. A browser journey should search a known report topic and open the publisher PDF at the displayed page. On-device generation was not run during this release check because it requires a large model download; log any later download or runtime failure and do not claim generation worked from a build alone.
