# Team 6: step-by-step to-do list (from 2026-11-03)

Scope: articles from **1 Jun to 26 Oct 2026**. Paywalled articles are **excluded**, with no Nexis search.

✅ = done · 🧑 = you / the team · 🤖 = Claude builds it, you run it

## Before Thu 05.11 (status meeting)
1. 🧑 Prepare 4 to 5 slides:
   - query v1 → v3 and why (`query_refinement.md`)
   - the 5 key events
   - outlet coverage (`coverage_paragraph.md`)
   - revised RQs and hypotheses (`analysis_plan.md`, section 2)
   - lead/lag as an open joint question (section 5.2)
2. ✅ LLM API access: confirmed by the team (2026-11-03). Extraction in 3.2 is LLM-assisted.

## Week of 05.11: clean corpus (WP 3.1)
3. 🤖 Claude adds a `relevance` step to `pipeline.py`.
4. 🧑 Run `python pipeline.py relevance`. It keeps only 1 Jun to 26 Oct. It creates `05_relevance_sample.xlsx` with 100 articles.
5. 🧑 Open the Excel file and put `1` (about the pause/slowdown debate) or `0` (not about it) in the `relevant` column for each article. Ideally two team members do this separately. It takes about 1 to 2 hours.
6. 🧑 Run `python pipeline.py relevance` again. It reads your marks, picks the cutoff and writes `05_relevant_articles.csv`. Send Claude the summary it prints.

## By 19.11: codebook
10. 🤖 Claude drafts the codebook (actor, actor type, stance, argument categories, examples).
11. 🧑 Pilot: two people code the same 10 articles, compare, and fix unclear rules.

## By 03.12: gold standard and first topics
12. 🧑 Double-code about 120 articles (about 300 statements) in the coding sheet Claude prepares.
13. 🤖 Claude writes the script for Krippendorff's α and the gold standard. Target α ≥ 0.67.
14. 🤖 Claude writes the BERTopic script (on paragraphs). 🧑 You run it and label the topics with the team.

## By 17.12: automated extraction
15. 🤖 Claude writes the statement extraction: LLM-based if you have API access, otherwise NER plus rules. 🧑 You run it on all relevant articles.
16. 🤖 Validation script: F1 and accuracy against the gold standard.

## By 07.01: results
17. 🤖 Analysis notebook: H1 and H2 (chi-square), H3 (themes before vs after events), H4 (divergence), H5 (coalitions, network).
18. 🧑 Interpret the results and write the draft paper (Intro, Related work, Hypotheses, Method, Results, Discussion, Weaknesses).

## Ongoing
- 🧑 WhatsApp group with the Bluesky and HN contacts. Clarify whether both teams use Bluesky, and whether their data covers 1 Jun to 26 Oct. This decides whether the joint lead/lag part (section 5.2) goes ahead.
