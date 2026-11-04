# Data (metadata only)

Media Cloud query v3, collections UK / US / DE / CN national, 1 Jan to 26 Oct 2026. Analysis window: 1 Jun to 26 Oct 2026.

| File | What it holds |
|---|---|
| `01_deduped.csv` | 3,496 cleaned stories: id, outlet, date, title, URL, reprint list |
| `01_removed.csv` | 1,493 removed stories and the reason (wire reprint, digest, non-English, duplicate) |
| `02_link_status.csv` | Link check result per story (ok, paywalled, robots, broken ...) |
| `04_outlet_coverage.csv` | Full-text coverage per outlet (173 outlets) |
| `paywalled_for_library.csv` | Paywalled or blocked stories, for lookup through the university library |

The full article texts (`03_articles.csv`, `batches/*.jsonl`) are **not** in this repository. They were collected only for use within the team (no paywall bypass, robots.txt respected) and stay on the team's computers. Run `pipeline/pipeline.py` to rebuild them.
