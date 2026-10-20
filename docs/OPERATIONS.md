# Operations and freshness

## Production checks

The Cloudflare Worker runs a scheduled probe at 06:15 and 18:15 UTC. It requests Netherlands GDP growth, United States inflation and United Kingdom unemployment directly from World Bank and logs country, indicator, HTTP outcome and duration. A failure raises a Worker scheduled event error. Workers Logs must be enabled to review these events; do not log visitor questions.

GitHub Actions also runs `scripts/monitor_production.mjs` at 06:30 and 18:30 UTC. It checks `/api/health` and the same representative public live series. A failed run opens or updates `[Monitor] Production data probe failing`; a recovered run closes it. The health route alone does not check World Bank. The external monitor may see cached validated series, while the scheduled Worker probe bypasses that cache. Together they distinguish public availability from direct provider access. Neither proves every country, indicator or Cloudflare region is healthy.

To run the public probe locally: `node scripts/monitor_production.mjs`. The Worker configuration is in `web/wrangler.jsonc`; deployment must include the production `triggers` and `observability` fields. Review failed GitHub workflow logs and Worker scheduled logs before changing cache or timeout behavior.

## Dated data and reports

The saved fixture is `web/src/demoSnapshot.json`, reviewed 15 October 2026. `python scripts/check_data_freshness.py` compares its 15 same-year values with World Bank, reports the latest observed year, and writes `tmp/demo_snapshot_candidate.json`. A difference above 0.051 percentage points or a review older than 30 days fails the weekly workflow and opens a review issue. Review source revisions and choose a new dated fixture before publishing; the script never changes the public values automatically.

`python scripts/check_report_freshness.py --check` scans the European Commission forecast and ECB bulletin indexes for new dated report links. The reviewed baseline is `data/report_watch_baseline.json`. A new link opens a review issue; validate the edition, official PDF, page count, extraction, checksum and rights before changing `data/report_manifest.json`. Federal Reserve, World Bank, OECD and UN catalog pages returned HTTP 403 to an ordinary scripted request on 20 October 2026, so this automatic watch covers two publishers. Check the other four official catalogs manually until accessible feeds or APIs are available. Do not bypass publisher access restrictions.

After reviewing a new source, update the manifest, ingest it into a **copy** of the local store, regenerate `web/src/reportCatalog.ts` and `web/public/report-search-index.v1.json`, run vector and search evaluations, then deploy preview before production. The 2026 Chroma records carry page metadata. The seven legacy report chunks do not; public page search derives page numbers independently from the verified PDFs.

## Reproducibility and storage

`data/report_manifest.json` is the source catalog. `scripts/generate_report_catalog.py --check` checks PDF hashes, page counts and Chroma counts against the generated UI catalog. `scripts/build_report_search.py --check` regenerates the page-level term index and checks exact bytes. Both run in CI. `scripts/verify_chroma_vectors.py` recomputes a stored vector with the configured local embedding function. The public Worker does not read Chroma.

The Chroma store is currently a tracked 54 MB local artifact. It is **not** a hosted vector service. Before ingestion, run `python scripts/chroma_archive.py create --archive tmp/chroma-backup-YYYY-MM-DD.zip`; the script takes a consistent SQLite backup and includes the index segment files plus manifest with SHA-256 checksums. Run `verify --archive ...`, then `restore --archive ... --destination tmp/chroma-restore-test` and recheck a vector against the restored `chroma_store`. A tested 20 October archive is in ignored `tmp/chroma-backup-2026-10-20.zip`; copy it to durable off-machine storage because a local archive alone is not disaster recovery. `.dockerignore` omits local temporary files and web build outputs from the legacy Python image. Migrating the binary store out of Git requires a durable artifact host before removing it from the repository.

For rollback, select the prior Worker version in Cloudflare Deployments or use Wrangler rollback after confirming the target. The saved demo remains available when live World Bank retrieval fails.
