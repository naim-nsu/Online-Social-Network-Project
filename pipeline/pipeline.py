"""
AI Pause Debate (Team 6): clean, check and download the Media Cloud export.

Steps (run one at a time or all together):
    python pipeline.py dedupe   --input <content.csv or content.zip>
    python pipeline.py check
    python pipeline.py download [--max-batches N] [--pdf]
    python pipeline.py report   (articles per outlet: full text vs paywalled)
    python pipeline.py relevance (run twice: 1. make sample sheet, 2. after labelling, apply cutoff)
    python pipeline.py all      --input <content.csv or content.zip>

All outputs go to --out (default: ./output). Every step can be stopped and
re-run: work already done is skipped.

Rules this script follows:
  * robots.txt is respected; disallowed URLs are not fetched.
  * At most one request per second per website.
  * Paywalls are never bypassed. Paywalled / blocked / broken links are
    listed in paywalled_for_library.csv for lookup via the university
    account (Nexis Uni, Factiva, PressReader ...).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
import trafilatura
from tqdm import tqdm

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (compatible; AIPauseDebateResearch/1.0; "
    "university seminar project, non-commercial text analysis)"
)
TIMEOUT = 15            # seconds per request
RETRIES = 2             # extra attempts on timeouts / connection errors
PER_SITE_DELAY = 1.0    # seconds between two requests to the same website
WORKERS = 8             # different websites are contacted in parallel
BATCH_SIZE = 50         # articles per download batch
MIN_WORDS = 150         # less text than this = teaser / paywall page
MIN_TITLE_WORDS = 4     # shorter titles are too generic to mark as reprints

TRACKING_PARAMS = re.compile(
    r"^(utm_.*|ns_.*|ito|icid|cmpid|cmp|ref|refsrc|src|source|rss|"
    r"fbclid|gclid|mc_cid|mc_eid|smid|sr_share|traffic_source|taid|"
    r"partner|feed|output|outputtype|mod|guccounter)$",
    re.IGNORECASE,
)

# Titles of roundup pages that bundle many unrelated stories
DIGEST_TITLES = (r"^AP Top .*News at|^The Latest:|Morning Squawk|Morning Rundown|"
                 r"Daily Open:|Fortune Tech:|as it happened|Live Updates|live blog|"
                 r"newsletter|^Full transcript")

# File names inside the output folder
DEDUPED = "01_deduped.csv"
REMOVED = "01_removed.csv"
LINK_STATUS = "02_link_status.csv"
LIBRARY = "paywalled_for_library.csv"
BATCH_DIR = "articles"
ARTICLES = "03_articles.csv"
PDF_DIR = "pdfs"
COVERAGE = "04_outlet_coverage.csv"
RELEVANCE_SCORES = "05_relevance_scores.csv"
RELEVANCE_SAMPLE = "05_relevance_sample.xlsx"
RELEVANT = "05_relevant_articles.csv"


# --------------------------------------------------------------------------
# Step 1: dedupe
# --------------------------------------------------------------------------
def normalize_url(url: str) -> str:
    """Return a comparable form of a URL (no scheme, www, tracking params)."""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not TRACKING_PARAMS.match(k)]
    return urlunsplit(("", host, path, urlencode(sorted(query)), "")).lstrip("/")


def title_key(title: str) -> str:
    """Lowercase title with punctuation and spacing removed."""
    t = str(title).lower().strip().removesuffix("...").strip()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def load_export(path: Path) -> pd.DataFrame:
    """Read the Media Cloud content CSV, directly or from the zip."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            return pd.read_csv(io.BytesIO(zf.read(name)), dtype=str)
    return pd.read_csv(path, dtype=str)


def dedupe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (kept rows, removed rows with a 'removed_reason' column)."""
    df = df.copy()
    df["norm_url"] = df["url"].map(normalize_url)
    df["title_key"] = df["title"].map(title_key)
    # earliest first, so the original story is kept and reprints are removed
    df = df.sort_values(["publish_date", "indexed_date"], kind="stable")
    removed = []

    def drop(mask: pd.Series, reason) -> None:
        nonlocal df
        out = df[mask].copy()
        out["removed_reason"] = reason(out) if callable(reason) else reason
        removed.append(out)
        df = df[~mask]

    # 1. not English
    drop(df["language"] != "en", "not_english")

    # 1b. news digests / live blogs: many unrelated stories on one page
    drop(df["title"].str.contains(DIGEST_TITLES, case=False, regex=True, na=False),
         "news_digest")

    # 2. same article, different URL spelling (tracking params etc.)
    first_id = df.groupby("norm_url")["id"].transform("first")
    drop(df["id"] != first_id, lambda o: "duplicate_url_of:" + first_id[o.index])

    # 3. same title at the same outlet on the same day
    keys = ["media_name", "title_key", "publish_date"]
    first_id = df.groupby(keys)["id"].transform("first")
    drop(df["id"] != first_id, lambda o: "same_title_same_outlet_of:" + first_id[o.index])

    # 4. wire reprints: same (non-generic) title at different outlets.
    #    Keep the earliest copy; remember where else it ran.
    long_title = df["title_key"].str.split().str.len() >= MIN_TITLE_WORDS
    groups = df[long_title].groupby("title_key")
    canon_id = groups["id"].transform("first")
    df["reprint_count"] = 0
    df["reprint_outlets"] = ""
    df["reprint_urls"] = ""
    for _, g in groups:
        if len(g) < 2:
            continue
        others = g.iloc[1:]
        df.loc[g.index[0], "reprint_count"] = len(others)
        df.loc[g.index[0], "reprint_outlets"] = "; ".join(others["media_name"])
        df.loc[g.index[0], "reprint_urls"] = " ".join(others["url"])
    is_reprint = pd.Series(False, index=df.index)
    is_reprint[canon_id.index] = canon_id != df.loc[canon_id.index, "id"]
    drop(is_reprint, lambda o: "reprint_of:" + canon_id[o.index])

    removed_df = pd.concat(removed) if removed else pd.DataFrame()
    return df.sort_index(), removed_df.drop(
        columns=["reprint_count", "reprint_outlets", "reprint_urls"], errors="ignore")


def run_dedupe(input_path: Path, out: Path) -> None:
    raw = load_export(input_path)
    kept, removed = dedupe(raw)
    kept.to_csv(out / DEDUPED, index=False)
    removed.to_csv(out / REMOVED, index=False)
    reasons = removed["removed_reason"].str.split(":").str[0].value_counts()
    print(f"[dedupe] {len(raw)} rows in, {len(kept)} kept, {len(removed)} removed")
    for reason, n in reasons.items():
        print(f"         {reason:28s} {n}")
    print(f"         -> {out / DEDUPED}\n         -> {out / REMOVED}")


# --------------------------------------------------------------------------
# Polite HTTP: one shared session, robots.txt, per-site rate limit
# --------------------------------------------------------------------------
class PoliteClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._robots: dict[str, RobotFileParser | None] = {}
        self._site_locks: dict[str, threading.Lock] = {}
        self._last_hit: dict[str, float] = {}
        self._lock = threading.Lock()

    def _site(self, url: str) -> str:
        p = urlsplit(url)
        return f"{p.scheme}://{p.netloc}"

    def _wait_turn(self, site: str) -> threading.Lock:
        with self._lock:
            lock = self._site_locks.setdefault(site, threading.Lock())
        lock.acquire()
        wait = self._last_hit.get(site, 0) + PER_SITE_DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        return lock

    def _release(self, site: str, lock: threading.Lock) -> None:
        self._last_hit[site] = time.monotonic()
        lock.release()

    def allowed(self, url: str) -> bool:
        site = self._site(url)
        if site not in self._robots:
            rp = RobotFileParser()
            lock = self._wait_turn(site)
            try:
                r = self.session.get(site + "/robots.txt", timeout=TIMEOUT)
                if r.status_code in (401, 403):
                    rp.disallow_all = True
                elif r.ok:
                    rp.parse(r.text.splitlines())
                else:
                    rp.allow_all = True  # no robots.txt = no restrictions
            except requests.RequestException:
                rp.allow_all = True
            finally:
                self._release(site, lock)
            self._robots[site] = rp
        return self._robots[site].can_fetch(USER_AGENT, url)

    def request(self, method: str, url: str, **kw) -> requests.Response:
        site = self._site(url)
        for attempt in range(RETRIES + 1):
            lock = self._wait_turn(site)
            try:
                return self.session.request(method, url, timeout=TIMEOUT,
                                            allow_redirects=True, **kw)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == RETRIES:
                    raise
            finally:
                self._release(site, lock)
        raise RuntimeError("unreachable")


# --------------------------------------------------------------------------
# Step 2: check links
# --------------------------------------------------------------------------
def classify(status: int) -> str:
    if 200 <= status < 400:
        return "ok"
    if status in (401, 402):
        return "paywalled"
    if status == 403:
        return "forbidden"      # paywall or bot protection
    if status in (404, 410):
        return "broken"
    if status == 429:
        return "rate_limited"
    return "error"


def check_one(client: PoliteClient, url: str) -> dict:
    """Check a single URL without downloading the body."""
    if not client.allowed(url):
        return {"status": "blocked_by_robots", "http_status": "", "final_url": ""}
    try:
        r = client.request("HEAD", url)
        if r.status_code in (403, 405, 400, 501) or r.status_code >= 500:
            r = client.request("GET", url, stream=True)  # some sites reject HEAD
            r.close()
        return {"status": classify(r.status_code), "http_status": r.status_code,
                "final_url": r.url}
    except requests.Timeout:
        return {"status": "timeout", "http_status": "", "final_url": ""}
    except requests.RequestException as e:
        broken = "Name or service not known" in str(e) or "NameResolution" in str(e)
        return {"status": "broken" if broken else "error", "http_status": "",
                "final_url": "", "error": str(e)[:200]}


def check_row(client: PoliteClient, row: pd.Series) -> dict:
    """Check the article URL; if it fails, try free reprints of the same story."""
    candidates = [row["url"]] + str(row.get("reprint_urls") or "").split()
    first = None
    for url in candidates:
        result = check_one(client, url)
        result["checked_url"] = url
        if first is None:
            first = result
        if result["status"] == "ok":
            result["original_status"] = first["status"]
            return {"id": row["id"], **result}
    return {"id": row["id"], **first, "original_status": first["status"]}


RETRYABLE = {"error", "timeout", "rate_limited"}  # retried on the next run


STATUS_COLS = ["id", "status", "http_status", "final_url", "error",
               "checked_url", "original_status"]


def load_status(out: Path) -> pd.DataFrame:
    """Link status table, keeping only the latest check of each article.

    Also repairs files written by the first version of this script, where
    rows with an 'error' value had one column more than the others.
    """
    path = out / LINK_STATUS
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]
    no_error = [c for c in STATUS_COLS if c != "error"]
    fixed = [dict(zip(STATUS_COLS if len(r) == len(STATUS_COLS) else no_error, r))
             for r in rows if r]
    st = pd.DataFrame(fixed).reindex(columns=STATUS_COLS).fillna("")
    st.to_csv(path, index=False)  # rewrite in the clean, fixed layout
    return st.drop_duplicates("id", keep="last")


def append_rows(path: Path, rows: list[dict]) -> None:
    if rows:
        pd.DataFrame(rows).reindex(columns=STATUS_COLS).to_csv(path, mode="a", index=False,
                                  header=not path.exists())


def run_check(out: Path) -> None:
    articles = pd.read_csv(out / DEDUPED, dtype=str).fillna("").drop_duplicates("id")
    status_path = out / LINK_STATUS
    done = set()
    if status_path.exists():
        # temporary failures (timeouts, errors, 429) are retried on a re-run
        st = load_status(out)
        done = set(st.loc[~st["status"].isin(RETRYABLE), "id"])
    todo = articles[~articles["id"].isin(done)]
    print(f"[check] {len(done)} already checked, {len(todo)} to go")

    client = PoliteClient()
    buffer: list[dict] = []
    with ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(check_row, client, row) for _, row in todo.iterrows()]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="checking"):
            buffer.append(fut.result())
            if len(buffer) >= 50:          # save progress regularly
                append_rows(status_path, buffer)
                buffer = []
    append_rows(status_path, buffer)

    print(load_status(out)["status"].value_counts().to_string())
    write_library_list(out)


# --------------------------------------------------------------------------
# Paywalled / unreachable links for the library
# --------------------------------------------------------------------------
def write_library_list(out: Path) -> None:
    articles = pd.read_csv(out / DEDUPED, dtype=str).fillna("")
    status = load_status(out)
    reasons = status[status["status"] != "ok"][["id", "status", "http_status"]]
    reasons = reasons.rename(columns={"status": "reason"})

    downloaded = load_downloaded(out)
    if not downloaded.empty:
        partial = downloaded[downloaded["download_status"] != "ok"]
        partial = partial[["id", "download_status"]].rename(
            columns={"download_status": "reason"})
        reasons = pd.concat([reasons, partial])

    lib = reasons.merge(articles, on="id", how="inner")  # only current export
    cols = ["id", "reason", "http_status", "title", "media_name", "publish_date",
            "url", "reprint_outlets"]
    lib = lib.reindex(columns=cols).sort_values(["media_name", "publish_date"])
    lib.to_csv(out / LIBRARY, index=False)
    print(f"[library] {len(lib)} links to look up with the university account "
          f"-> {out / LIBRARY}")


# --------------------------------------------------------------------------
# Step 3: download in batches of 50
# --------------------------------------------------------------------------
def looks_paywalled(html: str) -> bool:
    """Publisher-declared paywall flag (schema.org isAccessibleForFree)."""
    return bool(re.search(r'"isAccessibleForFree"\s*:\s*"?false', html, re.IGNORECASE))


def download_one(client: PoliteClient, row: pd.Series) -> dict:
    url = row["final_url"] or row["checked_url"]
    record = {"id": row["id"], "source_url": url,
              "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        r = client.request("GET", url)
    except requests.RequestException as e:
        return {**record, "download_status": "error", "text": "", "word_count": 0,
                "error": str(e)[:200]}
    if r.status_code != 200:
        return {**record, "download_status": classify(r.status_code),
                "text": "", "word_count": 0}

    html = r.text
    text = trafilatura.extract(html, url=url, include_comments=False,
                               include_tables=False, favor_precision=True) or ""
    words = len(text.split())
    if looks_paywalled(html):
        # Publisher marks the article as not free. Even if the full text is in
        # the page (hidden by the site's paywall script), we do not keep it.
        return {**record, "download_status": "paywalled_flag", "text": "",
                "word_count": words}
    if words == 0:
        state = "no_text"            # extraction failed (e.g. JavaScript page)
    elif words < MIN_WORDS:
        state = "paywalled_partial"  # teaser only
    else:
        state = "ok"
    return {**record, "download_status": state, "text": text, "word_count": words}


def save_pdf(urls_ids: list[tuple[str, str]], pdf_dir: Path) -> None:
    """Optional: print each page to PDF with a headless browser."""
    from playwright.sync_api import sync_playwright  # only needed with --pdf
    pdf_dir.mkdir(exist_ok=True)
    with sync_playwright() as p:
        # CHROMIUM_PATH is only needed if playwright cannot find its own browser
        browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        page = browser.new_page(user_agent=USER_AGENT)
        for art_id, url in urls_ids:
            target = pdf_dir / f"{art_id[:16]}.pdf"
            if target.exists():
                continue
            try:
                page.goto(url, timeout=TIMEOUT * 2000, wait_until="domcontentloaded")
                page.pdf(path=str(target), format="A4", print_background=False)
            except Exception as e:  # noqa: BLE001 - keep going on any page error
                print(f"  pdf failed for {url}: {e}")
            time.sleep(PER_SITE_DELAY)
        browser.close()


def load_downloaded(out: Path) -> pd.DataFrame:
    files = sorted((out / BATCH_DIR).glob("batch_*.jsonl"))
    rows = [json.loads(line) for f in files for line in f.open(encoding="utf-8")]
    df = pd.DataFrame(rows)
    # an article retried in a later batch: keep only its latest attempt
    return df.drop_duplicates("id", keep="last") if not df.empty else df


def run_download(out: Path, max_batches: int | None, pdf: bool, pause: float) -> None:
    articles = pd.read_csv(out / DEDUPED, dtype=str).fillna("")
    status = load_status(out)
    ok = status[status["status"] == "ok"].merge(articles, on="id", how="inner")

    batch_dir = out / BATCH_DIR
    batch_dir.mkdir(exist_ok=True)
    done = load_downloaded(out)
    # temporary failures (rate limit, timeout, error) are tried again
    done_ids = set(done.loc[~done["download_status"].isin(RETRYABLE), "id"]) \
        if not done.empty else set()
    todo = ok[~ok["id"].isin(done_ids)]
    batches = [todo.iloc[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    if max_batches:
        batches = batches[:max_batches]
    next_no = len(list(batch_dir.glob("batch_*.jsonl"))) + 1
    print(f"[download] {len(done_ids)} already saved, {len(todo)} to go, "
          f"running {len(batches)} batch(es) of up to {BATCH_SIZE}")

    client = PoliteClient()
    meta_cols = ["title", "media_name", "publish_date", "language", "url",
                 "reprint_count", "reprint_outlets"]
    for n, batch in enumerate(batches, start=next_no):
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(tqdm(pool.map(lambda r: download_one(client, r[1]),
                                         batch.iterrows()),
                                total=len(batch), desc=f"batch {n:03d}"))
        meta = batch.set_index("id")[meta_cols]
        path = batch_dir / f"batch_{n:03d}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for rec in results:
                rec = {**meta.loc[rec["id"]].to_dict(), **rec}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        good = sum(r["download_status"] == "ok" for r in results)
        print(f"  saved {path.name}: {good}/{len(results)} full articles")
        if pdf:
            save_pdf([(r["id"], r["source_url"]) for r in results
                      if r["download_status"] == "ok"], out / PDF_DIR)
        if n < next_no + len(batches) - 1:
            time.sleep(pause)

    merge_articles(out)
    write_library_list(out)


def merge_articles(out: Path) -> None:
    df = load_downloaded(out)
    if df.empty:
        print("[merge] nothing downloaded yet")
        return
    full = df[df["download_status"] == "ok"]
    full.to_csv(out / ARTICLES, index=False)
    print(f"[merge] {len(full)} full-text articles -> {out / ARTICLES}")
    print(df["download_status"].value_counts().to_string())


# --------------------------------------------------------------------------
# Step 4: outlet coverage report
# --------------------------------------------------------------------------
def outcome_group(link_status: str, download_status: str) -> str:
    """Collapse the detailed statuses into five report categories."""
    if download_status == "ok":
        return "full_text"
    if download_status in ("paywalled_flag", "paywalled_partial") or \
            link_status in ("paywalled", "forbidden"):
        return "paywalled"
    if link_status == "blocked_by_robots":
        return "robots"
    if link_status == "broken":
        return "broken"
    return "other_failed"


def run_report(out: Path) -> None:
    articles = pd.read_csv(out / DEDUPED, dtype=str).fillna("")
    status = load_status(out)[["id", "status"]].rename(columns={"status": "link_status"})
    df = articles.merge(status, on="id", how="left").fillna({"link_status": "not_checked"})
    downloaded = load_downloaded(out)
    if not downloaded.empty:
        df = df.merge(downloaded[["id", "download_status"]], on="id", how="left")
    else:
        df["download_status"] = ""
    df["download_status"] = df["download_status"].fillna("")
    df["outcome"] = [outcome_group(l, d) for l, d in zip(df["link_status"], df["download_status"])]

    cols = ["full_text", "paywalled", "robots", "broken", "other_failed"]
    table = pd.crosstab(df["media_name"], df["outcome"]).reindex(columns=cols, fill_value=0)
    table.insert(0, "articles", table.sum(axis=1))
    table["coverage_pct"] = (100 * table["full_text"] / table["articles"]).round(1)
    table = table.sort_values("articles", ascending=False)
    table.to_csv(out / COVERAGE)

    total = table[cols].sum()
    n = int(table["articles"].sum())
    print(f"[report] {n} articles from {len(table)} outlets")
    for c in cols:
        print(f"         {c:13s} {int(total[c]):5d}  ({100 * total[c] / n:.1f}%)")
    big = table[table["articles"] >= 20]
    print("\n  Largest outlets:")
    print(big.head(25).to_string())
    print(f"\n  Outlets with 0% full text (at least 10 articles): "
          f"{', '.join(table[(table['articles'] >= 10) & (table['full_text'] == 0)].index)}")
    print(f"  -> {out / COVERAGE}")


# --------------------------------------------------------------------------
# Step 5: relevance filter (score, hand-label a sample, pick the cutoff)
# --------------------------------------------------------------------------
WINDOW_START, WINDOW_END = "2026-06-01", "2026-10-26"
SAMPLE_SIZE = 100

# Terms that signal the pause / slowdown debate itself (case-insensitive)
RELEVANCE_TERMS = re.compile(
    r"\bpaus(?:e|es|ed|ing)\b|\bslow(?:down|-down| down| the pace)\b|\bmoratori(?:um|a)\b"
    r"|superintelligen|\bhalt(?:s|ed|ing)? (?:the )?(?:training|development)\b"
    r"|pacing the frontier|\bban(?:ning)? (?:on )?(?:artificial )?superintelligence"
    r"|hugging face (?:hack|breach|attack|incident)",
    re.IGNORECASE,
)


def relevance_score(title: str, text: str) -> int:
    """Hits in the title count 3x, in the first 3 paragraphs 2x, elsewhere 1x."""
    paras = [p for p in str(text).split("\n") if p.strip()]
    lead, body = " ".join(paras[:3]), " ".join(paras[3:])
    return (3 * len(RELEVANCE_TERMS.findall(str(title)))
            + 2 * len(RELEVANCE_TERMS.findall(lead))
            + len(RELEVANCE_TERMS.findall(body)))


def best_cutoff(scores: pd.Series, labels: pd.Series) -> tuple[int, pd.DataFrame]:
    """Try every cutoff; return the one with the highest F1 and the full table."""
    rows = []
    for c in sorted(set(scores)) + [scores.max() + 1]:
        pred = scores >= c
        tp = int((pred & labels).sum()); fp = int((pred & ~labels).sum())
        fn = int((~pred & labels).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        rows.append({"cutoff": c, "precision": round(prec, 3), "recall": round(rec, 3),
                     "f1": round(f1, 3), "kept_in_sample": int(pred.sum())})
    table = pd.DataFrame(rows)
    return int(table.loc[table["f1"].idxmax(), "cutoff"]), table


def run_relevance(out: Path) -> None:
    arts = pd.read_csv(out / ARTICLES, dtype=str).fillna("")
    arts = arts[(arts["publish_date"] >= WINDOW_START) & (arts["publish_date"] <= WINDOW_END)].copy()
    arts["relevance_score"] = [relevance_score(t, x) for t, x in zip(arts["title"], arts["text"])]
    arts[["id", "publish_date", "media_name", "title", "relevance_score"]].to_csv(
        out / RELEVANCE_SCORES, index=False)
    print(f"[relevance] {len(arts)} full texts between {WINDOW_START} and {WINDOW_END}")
    print("            score distribution: "
          + ", ".join(f"{k}: {v}" for k, v in
                      pd.cut(arts["relevance_score"], [-1, 0, 2, 5, 10, 10**6],
                             labels=["0", "1-2", "3-5", "6-10", ">10"]).value_counts(sort=False).items()))

    sample_path = out / RELEVANCE_SAMPLE
    if not sample_path.exists():
        # stratified by score, so both clear and borderline cases get labelled
        bins = pd.qcut(arts["relevance_score"].rank(method="first"), 5, labels=False)
        sample = (arts.groupby(bins, group_keys=False)
                      .apply(lambda g: g.sample(min(len(g), SAMPLE_SIZE // 5), random_state=42)))
        sample = sample.sample(frac=1, random_state=1)  # shuffle so scores are not in order
        sample["snippet"] = sample["text"].str.slice(0, 700)
        sample["relevant"] = ""
        sample["note"] = ""
        sample[["id", "relevant", "note", "title", "media_name", "publish_date", "snippet", "url"]
               ].to_excel(sample_path, index=False)
        print(f"\n  Next: open {sample_path}, put 1 (about the pause/slowdown debate) or 0 "
              f"(not about it) in the 'relevant' column for every row, save, and run this step again.")
        print("  The score is hidden in the sheet on purpose, so it does not influence your judgement.")
        return

    sheet = pd.read_excel(sample_path, dtype={"id": str})
    labelled = sheet[sheet["relevant"].astype(str).str.strip().isin(["0", "1", "0.0", "1.0"])]
    if len(labelled) < min(50, len(sheet)):
        print(f"\n  Only {len(labelled)} rows are labelled 0/1 in {sample_path}. Label at least 50 "
              f"(ideally all {SAMPLE_SIZE}) and run again.")
        return
    labelled = labelled.merge(arts[["id", "relevance_score"]], on="id", how="inner")
    y = labelled["relevant"].astype(float).astype(int).astype(bool)
    cutoff, table = best_cutoff(labelled["relevance_score"], y)
    print(f"\n  {len(labelled)} labelled articles, {int(y.sum())} relevant")
    print(table[table["cutoff"] <= cutoff + 5].to_string(index=False))
    kept = arts[arts["relevance_score"] >= cutoff]
    kept.to_csv(out / RELEVANT, index=False)
    best = table[table["cutoff"] == cutoff].iloc[0]
    print(f"\n  Chosen cutoff: score >= {cutoff}  (precision {best.precision}, recall {best.recall}, "
          f"F1 {best.f1} on the labelled sample)")
    print(f"  -> {len(kept)} of {len(arts)} articles kept -> {out / RELEVANT}")


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["dedupe", "check", "download", "report", "relevance", "all"])
    ap.add_argument("--input", type=Path,
                    help="Media Cloud content CSV or zip (needed for dedupe/all)")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--max-batches", type=int, default=None,
                    help="stop after this many batches of 50 (default: all)")
    ap.add_argument("--pause", type=float, default=5.0,
                    help="seconds to wait between batches (default 5)")
    ap.add_argument("--pdf", action="store_true",
                    help="also save each full article as a PDF (needs playwright)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if args.step in ("dedupe", "all"):
        if not args.input:
            ap.error("--input is required for dedupe")
        run_dedupe(args.input, args.out)
    if args.step in ("check", "all"):
        run_check(args.out)
    if args.step in ("download", "all"):
        run_download(args.out, args.max_batches, args.pdf, args.pause)
    if args.step in ("report", "all"):
        run_report(args.out)
    if args.step == "relevance":
        run_relevance(args.out)


if __name__ == "__main__":
    main()
