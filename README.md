# The AI Pause Debate: Who Says What? – Team 6

Actors and arguments in English-language news media on pausing, slowing or banning frontier AI development (June–October 2026). Team project in the COIN seminar "Hidden Signals" (Fall 2026, Bamberg / Cologne / Lucerne).

## Questions

- **RQ1** Who are the central voices in the news debate on an AI pause?
- **RQ2** Which positions (for / against) and arguments do they use?
- **RQ3** Which themes structure the debate, tied to actors and events?
- **H1–H5** actor type × stance, stance × argument, events shift themes, the two sides talk past each other, cross-actor coalitions. Details: [`docs/analysis_plan.md`](docs/analysis_plan.md).

## Data so far

| Step | Stories |
|---|---|
| Media Cloud export, query v3 (UK / US / DE / CN national, English) | 4,989 |
| After removing duplicates, wire reprints and digests | 3,496 |
| Full texts within ±7 days of the five key events | 1,083 |
| Relevant to the debate (LLM filter, validated on 100 gold labels) | 907 |

Key events: 5 Jun (Anthropic pause mechanism), 21 Jul (Hugging Face incident), 18 Aug (OpenAI training pause), 3 Sep (Ban Artificial Superintelligence Act), 13 Sep ("Pacing the Frontier" slowdown call).

## Repository

| Folder | Contents |
|---|---|
| [`pipeline/`](pipeline/) | `pipeline.py` (dedupe, link check, download, coverage report, relevance sample), `llm_relevance.py` (LLM relevance filter), tests, query log, relevance check report |
| [`docs/`](docs/) | Analysis plan, codebook, step-by-step to-do list |
| [`data/`](data/) | Metadata only (see [`data/README.md`](data/README.md)) |

How to run the pipeline: [`pipeline/README.md`](pipeline/README.md). Run the scripts from `pipeline/` with `--out ../data`.

## Data policy

Full article texts were collected without paywall bypass and with robots.txt respected, for use within the team only. They are never committed here; `.gitignore` blocks them. Paywalled outlets are under-represented; see [`pipeline/coverage_paragraph.md`](pipeline/coverage_paragraph.md).

## Status (19 Nov 2026)

Relevance filter done (907 articles). Codebook v1 written; pilot coding next. Timeline: [`docs/next_steps.md`](docs/next_steps.md).
