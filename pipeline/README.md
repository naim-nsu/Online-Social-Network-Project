# Article pipeline (AI Pause Debate, Team 6)

`pipeline.py` cleans the Media Cloud export, checks every link, and downloads the
working articles in batches of 50. Run it on your own computer.
`llm_relevance.py` then decides which event-window articles are relevant (Anthropic API).

In this repository the data lives in `data/`, not `output/`: run the scripts from `pipeline/` with `--out ../data`.

## Setup (once)
```
pip install -r requirements.txt
pip install openpyxl   # for the relevance Excel sheet
# only if you want PDFs too:
pip install playwright
python -m playwright install chromium
```

## Run
Put the Media Cloud zip (or the CSV inside it) next to the script, then:
```
python pipeline.py dedupe   --input mc-onlinenews-mediacloud-20261027182443-content.zip
python pipeline.py check
python pipeline.py download --max-batches 2      # 100 articles, then stop
python pipeline.py download                      # everything that is left
python pipeline.py download --pdf                # same, plus one PDF per article
```
`python pipeline.py all --input <zip>` runs everything in one go.

You can stop any step (Ctrl+C) and run it again: finished work is skipped, and
links that only failed temporarily (timeout, error, 429) are checked again.

## Output (in `--out`, default `output/`; in this repo `data/`)
| File | Content |
|---|---|
| `01_deduped.csv` | Articles kept. `reprint_count`, `reprint_outlets`, `reprint_urls` show where else a wire story ran |
| `01_removed.csv` | Every removed row with `removed_reason` (not_english, duplicate_url_of, same_title_same_outlet_of, reprint_of) |
| `02_link_status.csv` | Link check per article: ok, broken, paywalled, forbidden, blocked_by_robots, timeout, error |
| `batches/batch_001.jsonl` ... | Downloaded articles, 50 per file, with metadata and full text (team-only) |
| `03_articles.csv` | All full-text articles in one table, ready for coding / NER (team-only) |
| `paywalled_for_library.csv` | Links to look up with the university account (paywalled, teaser only, blocked, broken), with title, outlet and date |
| `04_outlet_coverage.csv` | From `python pipeline.py report`: per outlet, how many articles came as full text, paywalled, robots-blocked, broken, plus coverage % |
| `05_relevance_scores.csv` | From `python pipeline.py relevance`: keyword score and event-window tags (`event_windows`, `nearest_event`) for the 1,083 window texts, no text |
| `05_relevance_sample.xlsx` | From `python pipeline.py relevance` (1st run): 100 articles to label 1/0 in the `relevant` column (team-only, holds snippets) |
| `05_relevant_articles.csv` | From `python pipeline.py relevance` (2nd run, after labelling): window articles above the best keyword cutoff. The best cutoff was 0, so it holds all 1,083 (team-only) |
| `06_llm_validation.csv` | From `python llm_relevance.py validate`: Claude's label vs the 100 gold labels |
| `06_llm_relevance.csv` | From `python llm_relevance.py run`: LLM label + reason for all 1,083 window texts (no text) |
| `06_relevant_articles.csv` | Full rows of the 907 relevant articles: **the corpus for coding and BERTopic** (team-only) |
| `pdfs/` | Only with `--pdf` |

## LLM relevance filter (after the relevance step)
The keyword cutoff keeps everything (see `relevance_check.md`), so relevance is decided by Claude:
```
pip install anthropic
set ANTHROPIC_API_KEY=sk-ant-...      # macOS/Linux: export ANTHROPIC_API_KEY=...
python llm_relevance.py validate --model sonnet --out ../data   # 100 gold articles, prints kappa / recall
python llm_relevance.py run --model sonnet --out ../data        # all 1,083 articles
```
Accept a model only if kappa ≥ 0.6 and recall ≥ 0.9 on the gold labels. Result on 18.11.2026: Haiku failed (kappa 0.54), **Sonnet passed** (kappa 0.69, recall 0.96) and labelled 907 of 1,083 articles relevant. Finished articles are cached per model, so an interrupted run (e.g. no API credit left) continues where it stopped.

## Rules built in
- robots.txt is respected; disallowed links are not fetched.
- At most 1 request per second per website (8 websites in parallel).
- No paywall bypass. A page with under 150 words of text, or one the publisher
  marks as not free (`paywalled_flag`, text not stored), is recorded and goes to the library list. Pages where no text could be extracted are `no_text`.
- If an article link is dead or paywalled but the same wire story ran at another
  outlet, the script tries that reprint instead (`original_status` shows this).

Settings (batch size, delays, timeouts) are at the top of `pipeline.py`.
Tests: `python -m pytest test_pipeline.py`.
