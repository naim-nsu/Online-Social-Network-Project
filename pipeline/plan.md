# Plan: dedupe, link check and download script for the Media Cloud export

Status: **draft, waiting for Adnan's approval.** No code is written yet.

## 1. What I found in your files

| File | What it is | Key numbers |
|---|---|---|
| Screenshot | Query settings | Collections: UK, Germany, China, US (National). Dates 2026-01-01 to 2026-10-26 |
| `...-counts.csv` | Daily counts for the attention graph | 299 days, columns `date, count, total_count, ratio`. Sum = 7,856 (matches the content file) |
| `...-content.zip` | One CSV of stories + one TXT with the query | 7,856 rows, columns `id, indexed_date, language, media_name, media_url, publish_date, title, url`. No empty cells. 225 outlets |

Things that matter for the script:

1. **No exact duplicate URLs, but 123 near duplicates.** Same article with tracking junk, for example `...html` and `...html?ns_mchannel=rss&ito=1490` (Daily Mail), or `?icid=rss` (CSMonitor). 685 URLs carry a `?query`.
2. **1,245 rows share a title with another row.** These are mostly wire stories (AP and similar) reprinted by many outlets. Example: "Microsoft commits to sweeping AI privacy rules..." appears 18 times (Seattle Times, SFGate, Chron, US News, OC Register...). Only 184 of them are the same title at the *same* outlet, which are true duplicates.
3. **45 rows are not English** (39 German, plus pt/ja/es/fr). Your scope is English news.
4. **Many hits look off topic.** Only 924 of 7,856 titles mention pause, moratorium, ban, halt or superintelligence. The query is broad because `(ban OR halt ...) AND development` catches stories like data center bans or a newspaper cartoon. This script will not filter on topic, but it will keep the full text so a relevance filter can run on it later.
5. **Coverage spikes** in the counts file: 14 to 16 September 2026 (131 to 136 stories a day) and around 23 September. That fits H3. For the graph I'd plot `ratio` (share of all stories), not just `count`, because the total news volume changes day to day.
6. Chinese sources are thin: globaltimes.cn (74) and chinanews.net (29).

## 2. What the script will do

One Python script, `pipeline.py`, with three steps you can run separately or together:

```
python pipeline.py dedupe     # step 1
python pipeline.py check      # step 2
python pipeline.py download   # step 3, 50 articles per batch
python pipeline.py all        # all three
```

### Step 1: Find and remove duplicates
- Normalize each URL: lowercase host, drop `www.`, `http`/`https`, trailing `/`, `#fragment`, and tracking parameters (`utm_*`, `ns_*`, `ito`, `icid`, `cmpid`, `ref`...). Real parameters (like an article id) are kept.
- **Remove** rows with the same normalized URL (the 123 cases) and rows with the same title at the same outlet on the same day.
- **Remove** non-English rows (45).
- **Syndicated wire copies** (same title, different outlets): see the open question below.
- Output: `01_deduped.csv` plus `01_removed.csv` that lists every removed row and the reason, so you can report it in the methods section.

### Step 2: Check whether links work
- Respect each site's `robots.txt`. A URL that is disallowed is marked `blocked_by_robots` and skipped.
- Send a light request (HEAD, falling back to GET) with an honest User-Agent that names the project, a 15 second timeout, and 2 retries.
- Max 1 request per second per website, so we never hammer one outlet.
- Record: HTTP status, final URL after redirects, and a status label: `ok`, `broken` (404/410, DNS error), `paywalled` (401/402/403 or a paywall page), `blocked_by_robots`, `timeout`, `error`.
- Output: `02_link_status.csv`.

### Step 3: Download working articles, 50 at a time
- Takes only `ok` links from step 2.
- Downloads in batches of 50. After each batch it saves `articles/batch_001.jsonl`, `batch_002.jsonl`... and a checkpoint, then pauses briefly before the next batch.
- **Resumable:** if it stops (crash, laptop closed), rerunning skips articles already saved. `--max-batches 3` lets you run just 3 batches (150 articles) and stop.
- Main text is extracted with `trafilatura` (removes menus, ads, comments). Each record keeps the Media Cloud metadata plus `text`, `word_count`, `downloaded_at`.
- **No paywall bypass.** If the page only shows a teaser (for example under 150 words, or a paywall flag in the page data), the article is marked `paywalled_partial` and the partial text is not counted as a full article.
- **Paywalled links are stored separately** in `paywalled_for_library.csv` (from both step 2 and step 3), with title, outlet, publish date, URL and reason. These columns are what you need to look each article up in Nexis Uni, Factiva or PressReader with your university account.
- At the end, all batches are merged into `03_articles.csv` (one row per article, ready for coding or NER/LLM extraction), plus a short summary: how many ok, broken, paywalled.

### Libraries
`pandas`, `requests`, `trafilatura`, `tqdm` (progress bar). Python standard library for robots.txt. All installable with one `pip install`.

### Testing before I hand it over
- Unit tests for the URL normalizer and dedupe rules using the real duplicate examples above (Daily Mail, CSMonitor, the 18 Microsoft reprints).
- A dry run of steps 2 and 3 on about 20 URLs. Note: my cloud machine goes through a proxy, so some news sites may refuse it. The real run should happen on your computer.

## 3. Open question for you

**What should happen to syndicated wire copies (same story reprinted by different outlets)?**

- **A. Keep one copy for download, but count the reprints (recommended).** One canonical article is downloaded, and a column `reprint_count` / `reprint_outlets` records where else it ran. This avoids coding the same statements 18 times (which would inflate actors in the discourse network), while still showing reach.
- B. Keep every copy. More downloads, and the same quotes appear many times in your statement data.
- C. Remove them completely, keeping only exact duplicates removed. Same as A without the reach columns.

## 4. Notes
- Optional PDF output (one PDF per working article via a headless browser) is offered as a switch; waiting on Adnan's answer.
- The "brainstorming" skill was used for this analysis. A "ponytail" skill is **not available** in my session. I will write the code following the same idea (small, clean, readable functions) unless you tell me what ponytail should add.
- Topic relevance filtering (dropping the off-topic hits) is not in this script. It is a good next step once the full texts are downloaded.
