"""LLM relevance filter for the event-window articles (Team 6, AI pause debate).

Uses Claude (Anthropic API) to label each article relevant / not relevant
according to the codebook rule agreed on 17.11.2026.

Run on your own computer, in the same folder as pipeline.py:

    pip install anthropic
    set ANTHROPIC_API_KEY=sk-ant-...        (Windows; macOS/Linux: export ...)

    python llm_relevance.py validate --model haiku   # 1. 100 gold articles -> F1 vs gold
    python llm_relevance.py run --model haiku        # 2. all 1,083 window articles

    --model haiku | sonnet | opus   (default: haiku). Start with haiku; if its kappa on
    validate is below 0.6 (or recall below 0.9), try sonnet, then opus. Use the SAME model for run.

Both steps can be stopped (Ctrl+C) and restarted: finished articles are cached in
output/06_llm_cache_<model>.jsonl (one cache per model) and are not sent again.

Outputs (output/):
    06_llm_validation.csv      validate: gold label, LLM label, reason per article
    06_llm_relevance.csv       run: id, metadata, llm_relevant, llm_reason (no full text)
    06_relevant_articles.csv   run: full rows of the relevant articles (team-only, contains text)

Approximate cost (validate / run): haiku $0.05 / under $0.50,
sonnet $0.35 / $3-4, opus $0.70 / $7-8.
"""
from __future__ import annotations

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import pandas as pd
from tqdm import tqdm

MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
MODEL = MODELS["haiku"]  # set from --model in main()
WORKERS = 4
ARTICLES = "03_articles.csv"
SCORES = "05_relevance_scores.csv"      # ids + event windows of the 1,083 articles
GOLD = "05_relevance_sample.xlsx"       # 100 gold labels (column `relevant`)
CACHE = "06_llm_cache_{model}.jsonl"
VALIDATION = "06_llm_validation.csv"
LLM_RELEVANCE = "06_llm_relevance.csv"
RELEVANT = "06_relevant_articles.csv"

SYSTEM = """You classify English-language news articles for a research project on the \
public debate about pausing or slowing down frontier AI development (June-October 2026).

Label an article RELEVANT if it is about AI risk, or about slowing, pausing, banning, \
halting or regulating AI development. This includes:
- calls for or against an AI pause, moratorium, slowdown or ban (e.g. the "Pacing the \
Frontier" call, the Ban Artificial Superintelligence Act, the OpenAI training pause, \
Anthropic's pause mechanism), and reactions to them;
- coverage of the rogue-AI / Hugging Face incident (AI models escaping a sandbox, hacking \
other companies, acting without permission), even if no pause is mentioned;
- articles about AI safety, existential or catastrophic AI risk, or how AI should be \
regulated or restricted, including local bans or moratoria on AI use.

Label an article NOT RELEVANT if AI is only background: product launches, business or \
stock news, data-center infrastructure, energy or environment, or a passing mention. \
Also NOT RELEVANT: commentary that only dismisses the debate (e.g. calls it hype) without \
engaging with the arguments.

Judge the article as a whole, not single keywords. Answer with the JSON schema only."""

SCHEMA = {
    "type": "object",
    "properties": {
        "relevant": {"type": "boolean"},
        "reason": {"type": "string", "description": "One short sentence."},
    },
    "required": ["relevant", "reason"],
    "additionalProperties": False,
}

_lock = threading.Lock()


def classify(client: anthropic.Anthropic, title: str, outlet: str, text: str) -> dict:
    params = dict(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user",
                   "content": f"Outlet: {outlet}\nTitle: {title}\n\n{text}"}],
    )
    if MODEL != MODELS["haiku"]:
        # if the model declines, the API retries on a fallback model in the same call
        # (not offered for Haiku; a refusal there is just recorded and retried next run)
        params.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    response = client.beta.messages.create(**params)
    if response.stop_reason == "refusal":
        return {"relevant": None, "reason": "", "error": "refusal"}
    if response.stop_reason == "max_tokens":
        return {"relevant": None, "reason": "", "error": "max_tokens"}
    raw = "".join(b.text for b in response.content if b.type == "text")
    out = json.loads(raw)
    return {"relevant": bool(out["relevant"]), "reason": out["reason"], "error": ""}


def load_cache(path: Path) -> dict[str, dict]:
    cache = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if not rec.get("error"):
                    cache[rec["id"]] = rec
    return cache


def label_all(arts: pd.DataFrame, out: Path) -> pd.DataFrame:
    """Classify every row of arts (needs id, title, media_name, text); uses the cache."""
    cache_path = out / CACHE.format(model=MODEL)
    cache = load_cache(cache_path)
    todo = arts[~arts["id"].isin(cache)]
    print(f"[llm] {len(arts)} articles, {len(arts) - len(todo)} already done, {len(todo)} to send")
    if len(todo):
        client = anthropic.Anthropic(max_retries=6)

        def work(row):
            try:
                rec = classify(client, row.title, row.media_name, row.text)
            except (anthropic.BadRequestError, json.JSONDecodeError, KeyError) as e:
                rec = {"relevant": None, "reason": "", "error": f"{type(e).__name__}: {e}"[:300]}
            rec["id"] = row.id
            with _lock, open(cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return rec

        with ThreadPoolExecutor(WORKERS) as pool:
            futures = [pool.submit(work, r) for r in todo.itertuples()]
            for fut in tqdm(as_completed(futures), total=len(futures)):
                rec = fut.result()
                if not rec.get("error"):
                    cache[rec["id"]] = rec
                else:
                    tqdm.write(f"  {rec['id'][:12]}: {rec['error']}")
    res = pd.DataFrame([cache[i] for i in arts["id"] if i in cache],
                       columns=["id", "relevant", "reason"])
    missing = len(arts) - len(res)
    if missing:
        print(f"  {missing} articles failed (see errors above). Run the same command again to retry them.")
    return res.rename(columns={"relevant": "llm_relevant", "reason": "llm_reason"})


def metrics(gold: pd.Series, pred: pd.Series) -> dict:
    tp = int((gold & pred).sum()); fp = int((~gold & pred).sum())
    fn = int((gold & ~pred).sum()); tn = int((~gold & ~pred).sum())
    n = tp + fp + fn + tn
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n**2
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec,
            "recall": rec, "f1": f1, "accuracy": po, "kappa": kappa}


def load_articles(out: Path) -> pd.DataFrame:
    arts = pd.read_csv(out / ARTICLES, dtype=str).fillna("")
    window = pd.read_csv(out / SCORES, dtype=str)[["id", "event_windows", "nearest_event"]]
    return arts.merge(window, on="id", how="inner")   # the 1,083 event-window texts


def run_validate(out: Path) -> None:
    gold = pd.read_excel(out / GOLD, dtype={"id": str})[["id", "relevant"]]
    arts = load_articles(out)
    sample = arts.merge(gold, on="id", how="inner")
    res = label_all(sample, out)
    df = sample[["id", "title", "media_name", "nearest_event", "relevant"]].merge(res, on="id")
    df.rename(columns={"relevant": "gold"}).to_csv(out / VALIDATION, index=False)
    m = metrics(df["relevant"].astype(int).astype(bool), df["llm_relevant"].astype(bool))
    print(f"\n  {MODEL} vs gold on {m['n']} articles:")
    print(f"  precision {m['precision']:.3f}  recall {m['recall']:.3f}  F1 {m['f1']:.3f}  "
          f"accuracy {m['accuracy']:.3f}  kappa {m['kappa']:.3f}")
    print(f"  (tp {m['tp']}, fp {m['fp']}, fn {m['fn']}, tn {m['tn']})")
    print("  For comparison: Abid vs Naim before resolving: 85% agreement, kappa 0.58.")
    print("  Keyword baseline (keep all): F1 0.895, kappa 0.")
    wrong = df[df["relevant"].astype(int).astype(bool) != df["llm_relevant"].astype(bool)]
    if len(wrong):
        print(f"\n  {len(wrong)} disagreements (gold -> LLM):")
        for r in wrong.itertuples():
            print(f"   {r.relevant} -> {int(r.llm_relevant)}  {r.media_name}: {r.title[:70]}\n"
                  f"          LLM: {r.llm_reason}")
    print(f"\n  Details: {out / VALIDATION}. Good enough if kappa >= 0.6 and recall >= 0.9\n"
          f"  (F1 alone is not enough: keeping everything already scores F1 0.895). Then run: "
          f"python llm_relevance.py run --model <same model>")


def run_all(out: Path) -> None:
    arts = load_articles(out)
    res = label_all(arts, out)
    df = arts.merge(res, on="id", how="left")
    meta = [c for c in ["id", "publish_date", "media_name", "title", "url", "event_windows",
                        "nearest_event", "llm_relevant", "llm_reason"] if c in df.columns]
    df[meta].to_csv(out / LLM_RELEVANCE, index=False)
    kept = df[df["llm_relevant"] == True]  # noqa: E712  (NaN = failed, not kept)
    kept.to_csv(out / RELEVANT, index=False)
    print(f"\n  {len(kept)} of {len(arts)} articles relevant -> {out / RELEVANT}")
    print("  per event window:")
    for ev in sorted(set(";".join(arts["event_windows"]).replace(":before", "")
                         .replace(":after", "").split(";")) - {""}):
        n_all = arts["event_windows"].str.contains(ev).sum()
        n_kept = kept["event_windows"].str.contains(ev).sum()
        print(f"    {ev}: {n_kept} of {n_all}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["validate", "run"])
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--model", choices=list(MODELS), default="haiku")
    args = ap.parse_args()
    global MODEL
    MODEL = MODELS[args.model]
    print(f"[llm] model: {MODEL}")
    run_validate(args.out) if args.step == "validate" else run_all(args.out)


if __name__ == "__main__":
    main()
