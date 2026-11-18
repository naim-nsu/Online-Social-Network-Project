# Data (metadata only)

Media Cloud query v3, collections UK / US / DE / CN national, English, 1 Jan to 26 Oct 2026. Text analyses use the ±7-day windows around the five key events (5 Jun, 21 Jul, 18 Aug, 3 Sep, 13 Sep 2026).

| File | What it holds |
|---|---|
| `01_deduped.csv` | 3,496 cleaned stories: id, outlet, date, title, URL, reprint list |
| `01_removed.csv` | 1,493 removed stories and the reason (wire reprint, digest, non-English, duplicate) |
| `02_link_status.csv` | Link check result per story (ok, paywalled, robots, broken ...) |
| `04_outlet_coverage.csv` | Full-text coverage per outlet (173 outlets) |
| `paywalled_for_library.csv` | Paywalled or blocked stories, for lookup through the university library |
| `05_relevance_scores.csv` | The 1,083 event-window full texts: event-window tags and keyword score (no text) |
| `06_llm_validation.csv` | LLM relevance label vs. the 100 gold labels, with the model's one-line reason |
| `06_llm_relevance.csv` | LLM relevance label and reason for all 1,083 window texts (907 relevant) |

The full article texts (`03_articles.csv`, `batches/*.jsonl`, `05_relevant_articles.csv`, `06_relevant_articles.csv`), the labelled sample (`05_relevance_sample.xlsx`) and filled coding sheets (`coding_*.xlsx`) are **not** in this repository. They were collected only for use within the team (no paywall bypass, robots.txt respected) and stay on the team's computers. Run `pipeline/pipeline.py` and `pipeline/llm_relevance.py` to rebuild them.
