# Three-minute interview demonstration

**Verified release entry point:** [production economic workspace](https://econ.nickcloud.dev/?view=overview&mode=demo&country=NL&indicator=NY.GDP.MKTP.KD.ZG&countries=NL%2CDE%2CFR&start=2010&end=2026). Choose **Saved demo**. Production version `ee986b90-75b6-4835-a574-cb714e50486a` was deployed and checked on 20 October 2026. The [preview Worker](https://global-economic-intelligence-preview.nicholai-gay.workers.dev) remains available as a second entry point.

| Time | Exact action | What to say and show |
| --- | --- | --- |
| 0:00–0:35 | Open the link. Select Netherlands and GDP growth. Open **View underlying data**. | “This is a research workspace for annual economic observations. The saved mode is explicitly dated and rounded; the 2024 Netherlands GDP-growth observation is 1.1%. The table, year, unit and World Bank source are inspectable.” |
| 0:35–1:05 | Switch to **Compare**; keep Netherlands, Germany and France; select GDP growth. | “The comparison aligns observations by year. It does not imply that each country's latest observation is from the same year. The saved fixture only supports a cross-section, not a trend.” |
| 1:05–2:15 | Open **Ask the analyst**. Keep Netherlands and the default question **What do the latest available economic indicators show?** Click **Run analysis**. | “The Worker selects supported indicators and deterministic code calculates the findings. This answer shows 2024 GDP growth 1.1%, 2024 inflation 3.3%, and 2025 modeled unemployment 3.9% of the labor force. Each finding links to its indicator. The ECB page-linked excerpt is dated context, not proof of the annual World Bank values. The interface explicitly says these single saved observations do not establish a trend.” |
| 2:15–2:40 | Open **Inspect supporting observations** and scroll to **Limits of this assessment**. | “The user can inspect raw values and the limitations. Missing observations would be omitted, rather than turned into zero.” |
| 2:40–3:00 | Click **Export this briefing**. | “The PDF is made from the analysis object already displayed. Export does not silently retrieve or generate a second answer.” |

## Live-data branch, only when it works

On **production**, switch to **Live data** on Overview and inspect Netherlands GDP growth. On 20 October 2026, both production and preview returned 2025 GDP growth **1.78%**, 2024 **1.07%**, provider update **8 October 2026**, and a dated retrieval. The live analyst reported a **0.71 percentage-point** increase. Check it again before the interview because an earlier production request failed transiently. If it fails, say: “The provider path is temporarily unavailable, so I’m using the explicitly dated saved demonstration. The app surfaces the failure rather than inventing a live value.” The release includes **Retry this request** and **Use saved demonstration**.

## Useful follow-up questions

- “Is this RAG?” — “The public app retrieves a small, reviewed report index and attaches relevant passages, but it is curated retrieval and deterministic analysis. It is not semantic vector RAG or an LLM-generated answer.”
- “Where is the AI?” — “There is a separate local Python/OpenAI prototype. Its Chroma embedding configuration is unverified, so I did not present it as a public capability. Adding grounded model synthesis would be a next step after a versioned index and evaluation.”
- “What fails safely?” — “Unsupported countries or topics are rejected, null observations are omitted, upstream failure is shown, and citations must resolve to supplied evidence IDs.”
