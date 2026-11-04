import pandas as pd
from pipeline import normalize_url, title_key, dedupe, classify, looks_paywalled


def test_normalize_drops_tracking_and_www():
    a = "https://www.dailymail.co.uk/news/article-15595397/x.html?ns_mchannel=rss&ns_campaign=1490&ito=1490"
    b = "http://dailymail.co.uk/news/article-15595397/x.html"
    assert normalize_url(a) == normalize_url(b)
    assert normalize_url("https://csmonitor.com/a/b?icid=rss") == normalize_url("https://csmonitor.com/a/b/")


def test_normalize_keeps_real_params():
    assert normalize_url("https://x.com/story?id=5") != normalize_url("https://x.com/story?id=6")


def test_title_key():
    assert title_key("AI Rivals Found Rare Agreement...") == title_key("ai rivals found rare agreement")


def row(i, media, title, url, date="2026-09-15", lang="en"):
    return dict(id=str(i), indexed_date=date + " 01:00", language=lang, media_name=media,
                media_url=media, publish_date=date, title=title, url=url)


def test_dedupe_rules():
    df = pd.DataFrame([
        row(1, "dailymail.co.uk", "Texas park data center fight", "https://dailymail.co.uk/a.html"),
        row(2, "dailymail.co.uk", "Texas park data center fight", "https://dailymail.co.uk/a.html?ito=1490"),
        row(3, "dw.com", "KI Moratorium gefordert heute", "https://dw.com/de/x", lang="de"),
        row(4, "seattletimes.com", "Microsoft commits to sweeping AI privacy rules", "https://st.com/m", date="2026-09-14"),
        row(5, "sfgate.com", "Microsoft commits to sweeping AI privacy rules", "https://sfgate.com/m"),
        row(6, "chron.com", "Microsoft commits to sweeping AI privacy rules", "https://chron.com/m"),
        row(7, "buffalonews.com", "Letters", "https://bn.com/1"),
        row(8, "nypost.com", "Letters", "https://nyp.com/1"),
        row(9, "cnbc.com", "Different story about OpenAI", "https://cnbc.com/s"),
        row(10, "cnbc.com", "Different story about OpenAI", "https://cnbc.com/s-2"),
        row(11, "apnews.com", "AP Top News at 11:10 a.m. EDT", "https://ap.com/d"),
    ])
    kept, removed = dedupe(df)
    assert set(kept["id"]) == {"1", "4", "7", "8", "9"}
    reasons = dict(zip(removed["id"], removed["removed_reason"]))
    assert reasons["2"] == "duplicate_url_of:1"
    assert reasons["3"] == "not_english"
    assert reasons["5"] == "reprint_of:4" and reasons["6"] == "reprint_of:4"
    assert reasons["10"] == "same_title_same_outlet_of:9"
    assert reasons["11"] == "news_digest"
    ms = kept.set_index("id").loc["4"]
    assert ms["reprint_count"] == 2
    assert ms["reprint_outlets"] == "sfgate.com; chron.com"
    assert ms["reprint_urls"].split() == ["https://sfgate.com/m", "https://chron.com/m"]
    assert kept.set_index("id").loc["7", "reprint_count"] == 0   # generic title not grouped


def test_classify_and_paywall_flag():
    assert classify(200) == "ok" and classify(402) == "paywalled"
    assert classify(404) == "broken" and classify(403) == "forbidden"
    assert looks_paywalled('{"isAccessibleForFree": "False"}')
    assert not looks_paywalled('{"isAccessibleForFree": true}')


def test_load_status_repairs_mixed_column_file(tmp_path):
    from pipeline import load_status, append_rows, LINK_STATUS
    (tmp_path / LINK_STATUS).write_text(
        "id,status,http_status,final_url,checked_url,original_status\n"
        "a,ok,200,https://x/a,https://x/a,ok\n"
        "b,error,,,\"Proxy, failed\",https://x/b,error\n", encoding="utf-8")
    st = load_status(tmp_path)
    assert list(st["status"]) == ["ok", "error"]
    assert st.set_index("id").loc["b", "error"] == "Proxy, failed"
    assert st.set_index("id").loc["b", "checked_url"] == "https://x/b"
    append_rows(tmp_path / LINK_STATUS, [{"id": "c", "status": "broken", "checked_url": "u"}])
    st = load_status(tmp_path)
    assert list(st["id"]) == ["a", "b", "c"] and st.set_index("id").loc["c", "checked_url"] == "u"


def test_outcome_group():
    from pipeline import outcome_group
    assert outcome_group("ok", "ok") == "full_text"
    assert outcome_group("ok", "paywalled_flag") == "paywalled"
    assert outcome_group("forbidden", "") == "paywalled"
    assert outcome_group("blocked_by_robots", "") == "robots"
    assert outcome_group("broken", "") == "broken"
    assert outcome_group("ok", "no_text") == "other_failed"


def test_relevance_score_and_cutoff():
    from pipeline import relevance_score, best_cutoff
    assert relevance_score("Calls for an AI pause grow", "x") == 3
    assert relevance_score("t", "CEOs urge a slowdown.\n\nb\n\nc\n\nA moratorium was rejected.") == 3
    assert relevance_score("Anthropic IPO", "Shares rose.") == 0
    scores = pd.Series([0, 0, 1, 3, 5, 8]); labels = pd.Series([False, False, False, True, True, True])
    cut, table = best_cutoff(scores, labels)
    assert cut in (2, 3) and table["f1"].max() == 1.0
