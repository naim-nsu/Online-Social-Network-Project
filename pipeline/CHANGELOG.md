# pipeline.py change log

There is only one script. Each version keeps all earlier steps (`dedupe`, `check`, `download`) and adds to or fixes them. The latest version can always run every step.

| Date | Change | Affects |
|---|---|---|
| 2026-10-31 | First version: dedupe, check, download in batches of 50, optional `--pdf` | all |
| 2026-11-01 | Fix: link status file had rows with different column counts, and reading it crashed. The script now repairs old files automatically. Temporary failures are retried on rerun | check |
| 2026-11-02 | Dedupe also removes news digests (AP Top News, newsletters, live blogs). Download and library list only use articles in the current `01_deduped.csv`, so old results from another query don't mix in | dedupe, download |
| 2026-11-02 | Pages the publisher marks as not free: text is no longer stored (`paywalled_flag`). Empty extractions are labelled `no_text` | download |
| 2026-11-02 | New step `report`: outlet coverage table `04_outlet_coverage.csv` | report |
| 2026-11-02 | Download step retries articles that failed temporarily (rate limit, timeout, error) on the next run, and keeps only the latest attempt per article | download |
| 2026-11-03 | New step `relevance`: keeps 1 Jun to 26 Oct, scores each full text for pause-debate terms, makes a 100-article Excel sheet to label, then picks the cutoff with the best F1 and writes `05_relevant_articles.csv` | relevance |
| 2026-11-12 | `relevance` keeps only the ±7-day windows around the five events (1,083 texts) and tags `event_windows` / `nearest_event`; writes `05_relevance_scores.csv` | relevance |
| 2026-11-17 | New script `llm_relevance.py`: Claude labels relevance with the agreed rule; `validate` on the 100 gold labels, `run` on all window texts, cached per model | llm_relevance |
| 2026-11-18 | First real run: Haiku failed validation, Sonnet passed (kappa 0.69, recall 0.96); 907 of 1,083 relevant | llm_relevance |
