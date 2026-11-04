# Team 6 analysis plan (v3, 2026-11-03)

_Who says what, about which themes, and who leads the debate? News media in the AI pause debate, compared with Bluesky and Hacker News (the other two teams)._


**Scope decisions (v3, 3 Nov):**

- **Analysis window: 1 June to 26 October 2026.** That is 3,170 of the 3,496 deduplicated stories (91%). It covers all five key events.
- **Paywalled articles are excluded.** There is no Nexis supplement and no cross-check. The analysis uses only the full texts we could download legally, and the paywall bias is reported as a limitation.
- The joint lead/lag question (C1) stays pending in section 5.2.

**Update v2.1:** the former Reddit team was refused a Reddit research API, and on Prof. Hacker's advice switched to **Bluesky**. Their contact person has agreed to the WhatsApp group and will check the time window, events and keywords.

v2 builds on v1 (kept as `analysis_plan_v1.md`) and focuses on the two points from Prof. Hacker's reply:

- **(A)** the COIN lead/lag question
- **(B)** inductive themes linked to actors and events

Open questions are marked **❓**.

---

## 1. Framing in the COIN seminar

The seminar ("Hidden Signals", Gloor, Hacker and Wolf) studies **Collaborative Innovation Networks**: small, self-organising swarms of insiders who pick up new ideas before the mainstream does. Its toolkit is **honest signals** (rotating leadership, responsiveness, balanced contribution, sentiment, connectors, shared attention), network analysis and the question of whether **the mood or attention of a swarm forecasts what happens later**.

Read through that lens, the three teams map neatly:

| Layer | Platform | Team | COIN role |
|---|---|---|---|
| Insider swarm | Hacker News (developers, researchers) | Hacker News team | "Coolhunters" / early signal |
| Engaged public, plus many journalists, academics and policy people | Bluesky | former Reddit team | Swarm / bridge between insiders and press |
| Mainstream | News media | **Team 6** | Amplifier / agenda-setter |

**The COIN question for our project:** does the insider debate lead the press, or does the press set the agenda that insiders react to? And does this differ by event and by theme?

Bluesky changes the picture a little. Many journalists and researchers post there, so it may act as a **bridge**: reacting quickly to insiders and sharing press articles. That gives a testable chain, Hacker News → Bluesky → press, or the reverse.

This gives the paper a clear "Related work" anchor: Gloor's coolhunting and swarm creativity, agenda-setting theory, and intermedia agenda-setting between social media and news.

---

## 2. Research questions and hypotheses (revised)

| | Statement | Main test |
|---|---|---|
| **RQ1** | Who are the central voices in the news debate? | Actor network centrality |
| **RQ2** | Which positions and arguments do they use? | Statement coding: actor, stance, argument |
| **RQ3** | Which themes structure the debate, and how are they tied to actors and events? | BERTopic on paragraphs |
| **H1** | Industry actors oppose a pause more often than academia, civil society or government | Chi-square, actor type × stance |
| **H2** | The pro-pause side argues with risk/safety; the anti-pause side argues with economics/innovation and geopolitics (China) | Chi-square, stance × argument |
| **H3** | Key events shift the news debate toward new themes (e.g. security after Hugging Face, governance after the Ban ASI Act) | Theme shares before vs after each event |
| **H4** | Pro- and anti-pause actors emphasise different themes, i.e. they talk past each other | Jensen-Shannon divergence plus permutation test |
| **H5 (exploratory)** | Coalitions form across actor types (e.g. industry and civil society on the pro-pause side) | Community detection in the actor network |

The old H3 ("coverage rises after events") is no longer a hypothesis. It stays as a descriptive figure. The COIN lead/lag question (RQ4, C1a to C1c) depends on the other two teams' data, so it is listed under **open questions (section 5.2)** for now.


---

## 3. Our core analysis: themes linked to actors and events (RQ3, H3, H4, H5)

### 3.1 Corpus preparation

- **Restrict to 1 Jun to 26 Oct.** That leaves roughly 1,900 full texts. The exact number follows once the relevance step runs.
- A **relevance filter** on those full texts: keyword score plus 100 hand-coded articles to fix the threshold, with F1 ≥ 0.85.
- Text-level near-duplicate removal, for reprints with different titles.

### 3.2 Statements: who says what (RQ1, RQ2)

- **Codebook.** The unit is one statement (actor plus position or argument). Variables:
  - actor
  - actor type: industry / academia / civil society / government & politics / international organisation / other
  - country
  - stance: pro-pause / anti-pause / conditional / neutral
  - argument category
- **Gold standard.** About 120 articles (about 300 statements), double-coded. Target Krippendorff's α ≥ 0.67 per variable, ideally ≥ 0.80.
- **Automated extraction** on the remaining relevant articles:
  - Recommended: LLM-assisted extraction to JSON, validated against the gold standard with F1 and accuracy per variable.
  - Fallback without an LLM: spaCy NER and quote rules for the actor, plus a small classifier for stance. (Not needed: the team confirmed LLM API access on 2026-11-03.)
- Normalise actor names with an alias table.

### 3.3 Themes with BERTopic (RQ3)

- Unit: **paragraph**, so each statement inherits the theme of its paragraph.
- Use sentence-transformer embeddings with default settings. Reduce to about 15 to 30 topics and label them by hand.
- Map the topics to a short theme list (security, risk, economy, China/geopolitics, regulation, innovation, ethics). The same list can later be shared with the other teams for the lead/lag part.
- Use `topics_over_time` with event lines. This gives the main figure for H3.

### 3.4 Tests

- **H3 (events shift themes):** compare theme shares in the 14 days before and after each event, with a chi-square test or a proportion test per theme. Add one interrupted time-series model per event as a robustness check.
  - The window starts on 1 Jun, so **5 Jun has no "before" period**. It serves as the opening event, and H3 is tested on 21 Jul, 18 Aug, 3 Sep and 13 Sep.
  - 18 Aug falls inside the Hugging Face aftermath, so use 7-day windows for it and report the overlap.
- **H4 (talking past each other):** compare the theme distribution of pro-pause and anti-pause statements with Jensen-Shannon divergence, against a permutation baseline of 1,000 shuffles of the stance labels. Add a figure of theme shares by stance.
- **H5 (coalitions):** build an actor network in which two actors are linked when they share stance and argument or theme. Run Louvain community detection and report the share of communities that mix actor types. Show an actor–theme two-mode network for the paper figure.
- **RQ1:** degree and betweenness centrality in the actor network, plus the top actors per stance.
- **H1, H2:** chi-square with Cramér's V. Robustness check: excluding the largest outlet (The Guardian) to make sure one outlet does not drive the result.

---

## 4. Timeline, aligned to the seminar dates

| Status meeting | Goal by then |
|---|---|
| **Thu 05.11** | Present the query log, key events, coverage table and this plan. Agree on the shared format with the other teams |
| **Thu 19.11** | Relevance filter done. Codebook piloted. Daily news CSV (relevant articles) ready |
| **Thu 03.12** | Double coding and α done. First BERTopic run. Decide whether the joint lead/lag part goes ahead |
| **Thu 17.12** | Automated extraction validated. Topics labelled |
| **Thu 07.01** | H1, H2, H3, H4 and H5 results. Draft paper |
| **Thu 28.01.2027** | Final presentation (15 to 20 slides, 10 to 12 min) and paper (10 to 20 pages plus code) |

**Paper structure required by the seminar:** Introduction, Related work, Hypotheses, Method, Results, Discussion, Weaknesses & future work.

---

## 5. Open questions **❓**

### 5.1 Practical

1. ~~Do we have LLM API access with a small budget?~~ Resolved 2026-11-03: yes, so 3.2 uses LLM-assisted extraction.
2. Have the other teams agreed to the shared CSV format and the dictionaries?
3. Can Bluesky (search API, `since`/`until`) and Hacker News (Algolia API) cover 1 Jun to 26 Oct with timestamps and URLs?
4. **Overlap:** Project C originally covered Hacker News *and* Bluesky. Do both other teams now work on Bluesky? If so, they should agree on who does what: for example the Hacker News team keeps sentiment on HN, and the new Bluesky team does tribes and networks on Bluesky. Otherwise one platform would be analysed twice and the comparison would have only two sources.

### 5.2 Joint COIN question with the Bluesky and Hacker News teams (pending)

This part goes ahead only once the other teams confirm their data covers the same window and events. It is not part of our core plan yet.

| | Statement | Main test |
|---|---|---|
| **RQ4 (COIN)** | Do insider communities lead or follow press coverage of the same events? | Event study plus time-series lead/lag |
| **C1a (COIN, attention)** | For technical events (Hugging Face incident, OpenAI training pause), attention on Hacker News peaks **before** the press, with Bluesky in between. For political events (Ban ASI Act, CEO slowdown call), the press leads and Bluesky and Hacker News follow | Onset/peak comparison per event, plus cross-correlation |
| **C1b (COIN, themes)** | New themes (e.g. security after the Hugging Face incident) appear in insider discussion before they become dominant in the press | Lead/lag on theme-level daily series |
| **C1c (COIN, link sharing)** | Most Hacker News and Bluesky posts that link to news articles about an event appear **after** those articles are published, so the platforms amplify the press. The exception is the first hours of technical events | Match shared URLs to our corpus |

Open decisions:

- Should C1a keep the split between technical and political events, or use one direction for all events?
- Do the other teams agree to the shared format below?

#### Draft design (for discussion with the other teams)

##### a) What must be shared between the three teams

Agree on this in the WhatsApp group (contact persons: Adnan and the Bluesky team's contact; the Hacker News team's contact is still open). It is the only part that depends on other teams.

1. **Time window:** 1 Jun to 26 Oct 2026, or the common overlap if a team's data is shorter.
2. **Time unit:** calendar day in **UTC**. News dates from Media Cloud are only day-level, so we can't go finer.
3. **Key events:**
   - 5 Jun: Anthropic's pause mechanism
   - 21 Jul: Hugging Face incident
   - 18 Aug: OpenAI training pause
   - 3 Sep: Ban ASI Act
   - 13 Sep: CEO "Pacing the Frontier" slowdown call. For this one, the exact first day needs checking.
4. **A shared relevance dictionary**, so "about the pause debate" means the same on every platform. Start from our query v3 terms.
5. **A shared theme dictionary** with 6 to 8 themes and a short keyword list each:
   - security & hacking
   - existential / catastrophic risk
   - economy & jobs
   - China & geopolitics
   - regulation & law
   - innovation & progress
   - ethics & rights

   Each team tags its own posts or articles with it. This makes C1b possible without merging corpora.
6. **One CSV per team** in the same format:

```
date, platform, n_total, n_relevant, share_relevant,
n_theme_security, n_theme_risk, n_theme_economy, n_theme_china,
n_theme_regulation, n_theme_innovation, n_theme_ethics,
mean_sentiment (optional)
```

In addition, one file of shared links per platform:

```
post_id, created_at_utc, platform, url
```

##### b) Methods

1. **Event study.** This is the main analysis because it is easy to read and robust. For each event and platform, in a window from −7 to +21 days, measure:
   - **onset**: the first day above baseline + 2 SD, where the baseline is the 28 days before the window
   - **peak day**
   - **half-life**: the days until attention falls back to 50% of the peak

   Then compare onset and peak across platforms. Plot all three series per event, normalised to 1 at the peak.
2. **Cross-correlation** of the normalised daily series. Use the share, not the raw count, and first-difference it to remove the trend. Use lags from −7 to +7 days, both for the full period and per event window. A peak at a negative lag means the insider platform leads.
3. **Granger causality**, both directions (news → HN, HN → news, news ↔ Bluesky, HN ↔ Bluesky). Use a VAR on stationary series with the lag order chosen by AIC (at most 7). Report it as supporting evidence only, because daily data and 300 days give limited power.
4. **C1b (themes):** repeat steps 1 and 2 on the theme series, for example "security" share on HN vs in the news after 21 Jul.
5. **C1c (link sharing).** This is the most direct evidence. Hacker News stories are mostly links, and Bluesky posts often contain links. The other teams send us the URLs and timestamps from their posts. We normalise the URLs with the same function `pipeline.py` uses and match them to our 3,496 stories. For each match we get the time between press publication and the platform post, and we see which outlets insiders share most. Posts linking to *non-news* sources (blogs, arXiv, GitHub, company posts) that appear before any press article show where insiders get ahead of the press.

**Robustness checks:**

- raw counts vs shares
- with and without the biggest spike (14 Sep)
- news counted from all 3,170 stories in the window (metadata), not only the full texts. The paywall bias then doesn't affect the attention series.

##### c) What we deliver to the other teams

Our daily CSV in the agreed format, the event list, and the shared dictionaries. I can add a step to `pipeline.py` that writes this CSV.

---

