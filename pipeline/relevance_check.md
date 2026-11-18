# Relevance check (17.11.2026)

Sample: 100 articles from the 1,083 full texts in the ±7-day event windows, labelled independently by Abid and Naim (1 = about the AI pause/slowdown debate, 0 = not).

## 1. Inter-coder agreement

|              | Naim 0 | Naim 1 |
|---|---|---|
| **Abid 0**   | 16 | 7 |
| **Abid 1**   | 8 | 69 |

- Raw agreement: 85 / 100 = 0.85
- Cohen's kappa: **0.58** (moderate; below the usual 0.67–0.80 threshold for content analysis)
- Abid: 77 relevant, Naim: 76 relevant. The overall rate is the same; the coders differ on *which* articles count.

### The 15 disagreements show two different definitions

**Abid = 1, Naim = 0 (8 articles): coverage of the rogue-AI / Hugging Face incident** without explicit pause talk.
- ibtimes: OpenAI agents communicating across 10+ sites
- express.co.uk: readers debate whether AI is good or bad (after the HF attack)
- ibtimes: two OpenAI models went rogue and hacked another company
- ibtimes: OpenAI agents took over a German website
- independent.co.uk: experimental ChatGPT model attacks rival platform
- ibtimes.co.uk: unreleased model broke into another company's servers
- techcrunch: researchers used Claude to hack into OpenAI
- gizmodo: rogue models acting like "Memento"

**Abid = 0, Naim = 1 (7 articles): broader AI-risk / AI-regulation pieces**, or ones that mention a pause in passing.
- nbcnews: Trump bans CNN… (newsletter; Shapiro on AI regulation inside)
- ibtimes.co.uk: Mamdani one-year AI moratorium in NYC schools
- standard.co.uk: "don't trust the tech bros to save us from the AI apocalypse"
- hotair: AI doomerism overhyped but dangerous
- motherjones: EPA rule on data-center pollution
- cnbc: Sanders to Bannon "Pro-Human Assembly" (FLI)
- theguardian: OpenAI Astra release (mentions the pause in Astra training)

The codebook needs one sentence on (a) whether pure incident coverage counts and (b) whether a passing mention of a pause counts. Re-label these 15 against that rule.

## 2. Gold labels (final, resolved 17.11.2026)

Abid and Naim resolved the 15 disagreements together (`output/05_relevance_labels/05_relevance_disagreements_resolved.xlsx`): 12 set to 1, 3 set to 0.
- Set to 1: all 8 rogue-AI / Hugging Face incident pieces, the NBC newsletter (Shapiro on AI regulation), the NYC schools AI moratorium, the "tech bros / AI apocalypse" column, the Sanders–Bannon FLI assembly.
- Set to 0: "AI doomerism overhyped" (hotair), EPA data-center pollution (motherjones), OpenAI Astra release (guardian).

Codebook rule (confirmed by the team, 17.11.2026): **relevant = the article is about AI risk or about slowing, pausing, banning or regulating AI development, including coverage of the rogue-AI / Hugging Face incident. Not relevant = AI is only background (product launches, infrastructure/environment) or the article is a commentary on the debate without engaging with it.**

Gold = **81 relevant / 19 not**, in `output/05_relevance_sample.xlsx` (`relevant` = gold; `agree` = yes / resolved).

## 3. Keyword-score cutoff: does not work

`pipeline.py relevance` picks the cutoff with the best F1 on the gold labels:

| cutoff | precision | recall | F1 | kept in sample |
|---|---|---|---|---|
| **0 (keep all)** | 0.81 | 1.00 | **0.90** | 100 |
| 1 | 0.81 | 0.70 | 0.76 | 70 |
| 2 | 0.89 | 0.57 | 0.69 | 52 |
| 3 | 0.92 | 0.44 | 0.60 | 39 |

The best cutoff is 0, so **all 1,083 articles are kept** in `output/05_relevant_articles.csv`.
Reason: many relevant articles never use the keywords (e.g. Hugging Face incident pieces score 0), so any cutoff above 0 throws away 30%+ of relevant articles.

Estimated relevant share of the 1,083: about 81% (95% CI roughly 72–88%), i.e. about 880 articles.

## 4. Decision: LLM filter (17.11.2026)

The team chose the LLM route with the **Anthropic API**. Script: `llm_relevance.py` (see README).
1. `python llm_relevance.py validate --model haiku` labels the 100 gold articles and prints precision, recall, F1, kappa and every disagreement.
2. Accept the model if **kappa >= 0.6 and recall >= 0.9**. F1 alone is not a useful bar, because keeping everything already scores F1 0.895. Otherwise try `--model sonnet`, then `--model opus`.
3. `python llm_relevance.py run --model <same model>` labels all 1,083 articles and writes `06_llm_relevance.csv` (labels + reasons) and `06_relevant_articles.csv` (full rows, team-only).

## 5. Result (18.11.2026)

| Model | Kappa | Recall | Precision | Accuracy | Result |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | 0.54 | 0.98 | 0.89 | 88% | fails (kappa) |
| **Claude Sonnet 5.5** | **0.69** | **0.96** | **0.93** | **91%** | **passes** |

Sonnet missed 3 relevant gold articles and kept 6 borderline ones. The full run with Sonnet labelled **907 of 1,083 articles relevant (84%)**, close to the 81% expected from the gold sample.

| Event window | Articles | Relevant | Relevant before | Relevant after |
|---|---|---|---|---|
| 5 Jun | 60 | 32 | 3 | 29 |
| 21 Jul | 166 | 127 | 8 | 119 |
| 18 Aug | 74 | 56 | 28 | 28 |
| 3 Sep | 224 | 176 | 49 | 127 |
| 13 Sep | 646 | 597 | 133 | 464 |

The 3 Sep and 13 Sep windows overlap (87 articles, 81 relevant), so the rows add up to more than 907. The "before" sides of 5 Jun and 21 Jul are too thin for a before/after test; see `docs/analysis_plan.md` 3.4 for how H3 handles this and the September overlap.

`05_relevant_articles.csv` and `06_relevant_articles.csv` contain full texts: team-only, never push to the public GitHub repo.
