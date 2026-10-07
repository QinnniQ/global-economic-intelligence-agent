# Inspectable analysis trace

This small **offline fixture** shows the data flow tested in `tests/test_core.py`. Its indicator value, report passage, and model response are invented for the test. It makes no claim about live economic conditions or model accuracy.

| Step | Fixture value |
| --- | --- |
| User question | “What is Germany's inflation outlook?” |
| Detected country and indicator | `DE`, `FP.CPI.TOTL.ZG` (consumer-price inflation) |
| Macro data supplied to the summarizer | `2025: 2.1` (synthetic percentage) |
| Retrieved report passage supplied to the final prompt | `[sample_chunk_1] Price pressure eased in the sample report.` |
| Stubbed final response | “The fixture's inflation is 2.1%. The sample report notes easing price pressure [sample_chunk_1].” |

The API result includes `raw_data`, `rag_passages`, `rag_sources: ["sample_chunk_1"]`, and `rag_status: "passages_found"`, so a reviewer can inspect the data and passage alongside the answer. In a real run, Chroma passage IDs use the source PDF stem and chunk number, such as `weo_chunk_7`.

**When retrieval returns no passages:** the final prompt explicitly tells the model to state that report evidence is unavailable and to use only the macro data. The result sets `rag_sources: []` and `rag_status: "no_report_evidence"`. The offline test checks this path too.

**Limit:** a passage ID identifies an indexed chunk, not a PDF page. The system asks the model for passage citations but does not yet verify every generated citation or factual claim. This trace verifies prompt and response wiring, not end-to-end answer quality. Run the project with live API access and review the returned passages before relying on an economic conclusion.
