# Team 6: step-by-step to-do list (updated 18.11.2026)

Scope: ±7 days around the five events (5 Jun, 21 Jul, 18 Aug, 3 Sep, 13 Sep 2026), 1,083 full texts. Paywalled articles excluded.

✅ = done · 🧑 = team · 🤖 = Claude builds it, the team runs it

## Done
- ✅ Query v1 → v3, Media Cloud export, dedupe, link check, download (2,079 full texts), outlet coverage report
- ✅ Status meetings 22.10 and 05.11
- ✅ Event windows confirmed (±7 days, event day = "after")
- ✅ Relevance sample labelled by two coders (kappa 0.58), disagreements resolved, gold = 81/100, rule confirmed
- ✅ LLM provider: Anthropic; `llm_relevance.py` written

## Thu 19.11 – status meeting 3
1. ✅ LLM relevance filter done 18.11 with Sonnet (kappa 0.69, recall 0.96): 907 of 1,083 relevant. Was: run `python llm_relevance.py validate --model haiku --out ../data`. Accept if kappa ≥ 0.6 and recall ≥ 0.9, else try `--model sonnet`. Then `run` with the same model.
2. 🤖 Codebook draft v1 (actor, actor type, stance, argument categories, examples).
3. ✅ 3 Sep / 13 Sep overlap: one September episode with three periods (pre 27 Aug–2 Sep / between 3–12 Sep / post 13–19 Sep); overlap-free test as robustness check (decided 18.11).
4. 🧑 Slides: relevance check (kappa → resolved → rule), keyword filter fails, LLM filter + validation numbers, codebook draft, timeline below.

## By 26.11 – pilot week
5. 🧑 Two coders code the same 10 articles with codebook v1. 🤖 Agreement script, 🧑 fix unclear rules → codebook v2.
6. 🤖 BERTopic script on paragraphs; 🧑 first run (independent of the coding).
7. 🤖 Daily news CSV in the shared format for the other teams.

## Thu 03.12 – status meeting 4
8. 🧑 Double-code ~80–120 articles: all four members, split into two pairs (~60 articles per pair, ~10 h per person).
9. 🤖 Krippendorff's α per variable (target ≥ 0.67); 🧑 resolve disagreements → gold standard. Plan for a second round if α is too low.
10. 🧑 First BERTopic results: topics labelled and mapped to the seven themes.
11. 🧑 **Go / no-go for the joint lead/lag analysis (C1a–C1c).** If the other teams have not confirmed coverage of our window and events by now, move it to "future work".

## Thu 17.12 – status meeting 5
12. 🤖 LLM statement extraction (Anthropic, JSON schema); 🧑 run on all relevant articles.
13. 🤖 Validation against the gold standard (F1 / accuracy per variable).
14. 🤖 Actor alias table and network build (networkx → Gephi).

## Christmas break (18.12 – 06.01)
15. 🧑 Write the paper sections that need no results: Introduction, Related work, Hypotheses, Method (incl. query refinement and outlet coverage).

## Thu 07.01 – status meeting 6
16. 🤖 Analysis notebook. 🧑 Show H1–H3 complete (chi-square, themes before vs after events) and first H4 / H5 numbers (divergence, coalitions).

## Thu 28.01.2027 – final presentation (14:00–16:00, online)
17. 🧑 Finish H4 / H5, Gephi figures, 15–20 slides (10–12 min + 3 min Q&A).

## Fri 12.02.2027 – final paper
18. 🧑 Results, Discussion, Weaknesses & future work; code and results attached. Confirm the exact deadline with the instructors (the site says "two weeks after", 12.02 is 15 days).
