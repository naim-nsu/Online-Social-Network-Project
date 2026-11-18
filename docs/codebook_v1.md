# Codebook v1 – The AI Pause Debate (Team 6)

Version 1, 18 Nov 2026 (before the pilot). Working copy: the team's shared doc; this file is the snapshot in the repo.

## 1. Purpose and scope

We code **who says what** about pausing, slowing, banning or regulating AI development: each statement gets an actor, an actor type, a stance and an argument. These codes feed RQ1–RQ2 and the tests of H1 (actor type × stance), H2 (stance × argument), H4 (themes by stance) and H5 (actor coalitions).

- **Corpus:** the 907 articles labelled relevant by the LLM filter (Sonnet 5.5, validated: kappa 0.69, recall 0.96), from the ±7-day windows around 5 Jun, 21 Jul, 18 Aug, 3 Sep and 13 Sep 2026.
- **Use:** humans code the pilot (10 articles) and the gold standard (~80–120 articles); the LLM extraction then applies the same rules to all 907 and is validated against the gold standard.
- **Version:** v1, before the pilot. Rules marked *pilot check* are the ones to test first.

## 2. Unit of analysis: the statement

A statement is **one actor taking a position or giving an argument** on AI risk or on pausing, slowing, banning or regulating AI development.

**Code it when** the position is attributed to an identifiable person or organisation:

- a direct quote ("We need a pause," said X)
- an indirect quote or paraphrase (X warned that…)
- a reported action that carries a position (X introduced a bill to ban…; X signed the statement)
- the author's own view, **only** in op-eds, columns and editorials: the actor is the author, typed by the affiliation printed with the piece (an unsigned editorial = "\<outlet\> editorial board", media & other)

**Do not code**

- unnamed groups without an identifiable actor ("critics say", "some experts")
- facts with no position ("The bill was introduced on 3 Sep")
- a reporter's framing in a news piece
- dismissive commentary that does not engage with the debate (same rule as the relevance filter)

**Counting rule:** one actor + one stance + one main argument = one statement per article. If the same actor repeats the same point, code it once. If the same actor makes a second, different argument, that is a second statement.

## 3. Variables at a glance

Coders fill five variables per statement.

| Variable | Values | Used for |
| --- | --- | --- |
| actor | Normalised name of a person or organisation | RQ1, network |
| actor_org | Affiliation of a person when speaking | Actor type, alias table |
| actor_type | industry / academia / civil society / government & politics / international org / media & other | H1, H5 |
| stance | pro / anti / neutral | H1, H2, H4 |
| argument | One of 10 categories (section 6) | H2, H4 |

Agreement (Krippendorff's α ≥ 0.67) is measured on actor_type, stance and the main argument.

## 4. Actors

### 4.1 Actor and actor_org

- **actor** = the speaker's full name as first given ("Dario Amodei", not "Amodei" or "the CEO"). For organisations, the official short name ("OpenAI", "Future of Life Institute").
- A spokesperson, "a company statement" or an unnamed employee speaking for the organisation → actor = the **organisation**.
- **actor_org** = the person's affiliation in the role they speak in, as the article states it. Leave empty for organisations.
- Names are merged later in the alias table ("Altman", "Sam Altman", "OpenAI's CEO" → one actor), so coders do not need to look anything up.

### 4.2 Actor type

Code the type of the role the actor speaks in, not their background.

| Actor type | Includes | Examples |
| --- | --- | --- |
| industry | AI labs, tech and other companies, their executives and staff (incl. lab safety researchers), investors, industry associations | OpenAI, Anthropic, Google DeepMind, Meta, Nvidia, a16z |
| academia | Universities and public research institutes, researchers speaking as academics | MIT professor, Mila, Oxford researcher |
| civil society | NGOs, think tanks, advocacy groups, unions, foundations, named activists | Future of Life Institute, PauseAI, Center for AI Safety, AI Now |
| government & politics | Legislators, ministers, heads of state, parties, regulators, government agencies, courts | Sen. Bernie Sanders, the White House, UK AI Security Institute, EU Commission |
| international org | Bodies of several states | UN, OECD, G7 |
| media & other | Journalists and columnists, celebrities, religious leaders, members of the public, polls | A Guardian columnist, the Pope, a YouGov poll |

## 5. Stance

Stance always answers one question: **is this actor for or against pausing, slowing or banning frontier AI development?**

| Stance | Definition | Example (illustrative) |
| --- | --- | --- |
| pro | Supports a pause, moratorium, slowdown, ban or cap on frontier development, including support tied to a condition or a trigger mechanism | "We should halt training of systems beyond GPT-5 level"; "a pause mechanism we can trigger when models cross a threshold" |
| anti | Opposes a pause, slowdown or ban, including "regulate instead of pausing" and "not unless our rivals stop too" | "A pause would only hand the lead to China." |
| neutral | Takes no side on a pause: discusses AI risk or calls for regulation without saying anything for or against a pause | "Congress must pass binding safety standards"; "The bill splits Silicon Valley." |

**Decision steps**

1. Does the statement say something for or against a pause, moratorium, slowdown, halt or ban?
   - For it, with or without conditions → **pro**
   - Against it, including "regulation instead" or "only if rivals join" when the point is to reject restraint now → **anti**
2. No position on a pause (risk talk, regulation only, analysis) → **neutral**. What the statement is about is still captured by the argument (e.g. A4, A5, A10).

When a condition is attached, code the direction the actor argues for: "we should pause once X" → pro; "we must not pause unless X" → anti. *Pilot check:* do coders apply this direction rule consistently?

## 6. Argument categories

Code the **main reason** the actor gives for their stance (one argument per statement). Each category maps to one of the seven BERTopic themes, so H4 can compare statements and themes directly.

| # | Category | Definition | Example from our corpus | Usual stance | BERTopic theme |
| --- | --- | --- | --- | --- | --- |
| A1 | Existential / catastrophic risk | AI could kill, disempower or gravely harm humanity | Krueger: "a smarter, more competitive species than you … might cause your extinction" (Mother Jones, 23 Aug) | pro | existential risk |
| A2 | Loss of control & security | AI acting outside human control: escapes, hacking, deception (incl. the Hugging Face incident) | Parikh (METR): models "trying to circumvent constraints and act deceptively" (TechCrunch, 27 Jul) | pro | security & hacking |
| A3 | Safety not ready yet | Alignment, testing or institutions lag behind capabilities and need time | Anthropic: an option to "slow or temporarily pause" so alignment research can "keep up" (5 Jun) | pro | existential risk |
| A4 | Current harms & rights | Harms happening now: deepfakes, bias, privacy, children, misinformation | Gould (UK minister): banning deepfakes and child-abuse imagery tools (GB News, 14 Sep) | neutral | ethics & rights |
| A5 | Accountability & public control | Companies cannot self-govern; the public or elected bodies must decide | Whitmer: regulation that "protects the public … the companies just can't do that themselves" (CNBC, 18 Sep) | pro / neutral | ethics & rights |
| A6 | Economy & jobs | Growth, investment, jobs, competitiveness (or job loss as a reason to slow) | Trump: "the jobs are enormous" from AI plants and data centers (Fox News, 23 Aug) | anti | economy & jobs |
| A7 | Innovation & benefits | AI brings progress, cures, science; slowing loses the benefits | Thibeau: AI can "redefine our economy and transform the country for the good" (Fox News, 16 Sep) | anti | innovation & progress |
| A8 | China & geopolitical race | A pause lets rivals (mostly China) win; security dilemma | Scalise: "a race between the United States and China, and America has got to win" (Daily Caller, 15 Sep) | anti | China & geopolitics |
| A9 | Overblown or unworkable | Risks are hype or fearmongering, or a pause cannot be enforced | Lambert: "Anthropic has overhyped the risks" (Wired, 22 Jul) | anti | existential risk |
| A10 | Governance design | How to govern: treaties, licensing, testing, thresholds, pause triggers | Warner: "secure testing with government agencies engaged" (Independent, 23 Jul) | neutral | regulation & law |

"Usual stance" is a tendency, not a rule: code what the actor actually says. Job loss used as a reason to slow down is A6 with stance pro. Examples are short excerpts from articles in the corpus; the full texts are not in this repository.

## 7. Hard cases

| Case | Rule | Corpus example → code |
| --- | --- | --- |
| Lab leader backs slowing down | Code what they say, even if it goes against the H1 expectation | Altman: "no amount of American competitive pressure should justify recklessness" (Houston Chronicle, 14 Sep) → industry, pro, A3 |
| Restraint only if rivals join | Code the direction: a warning against restraint now → anti | Amodei: if "China defects" after US restraint, it could gain "geopolitical dominance" (Guardian, 19 Sep) → industry, anti, A8 |
| Foreign government rejects the warnings | Dismissal that still engages with the debate is coded | China's foreign ministry (Guo Jiakun): "Fearmongering … will only disrupt the process of global AI governance" (SFGate, 14 Sep) → government, neutral, A9 |
| Unnamed sources | Not coded | "tech insiders told The Post" (NY Post, 19 Sep) → skip |
| A speaker reports others' position | Code the speaker's own position only; code the named others only if the article reports their position as fact | "all the big US labs and Bernie Sanders got together to call for a treaty" (NY Post, 17 Sep) → code the speaker if he takes a side; check the article for the labs' own call |
| Lab safety researcher | Always industry, even if speaking about risk | Hubinger (Anthropic): extinction risk "within the next decade" over 10% (Express, 15 Sep) → industry, neutral, A1 |
| Report or study with an author organisation | Actor = the organisation that published it | A loss-of-control incident report (Guardian, 29 Aug) → actor = the publishing body |
| Same actor, several arguments | One statement per distinct argument | An actor citing China and then jobs → two statements (A8, A6) |

*Pilot check:* the Guo Jiakun and Hubinger cases are deliberately borderline. If coders disagree on them, the stance rule needs one more sentence.

## 8. Coding sheet and procedure

One row per statement, in one Excel sheet per coder.

| Column | Content |
| --- | --- |
| article_id | id from `06_relevant_articles.csv` |
| statement_id | article_id + running number (…_01, …_02) |
| snippet | The quote or sentence the code is based on (max ~40 words) |
| actor / actor_org | See 4.1 |
| actor_type | Dropdown, see 4.2 |
| stance | Dropdown, see 5 |
| argument | Dropdown A1–A10, see 6 |
| notes | Doubts, hard-case number |

**Procedure**

1. **Pilot (by 26.11):** two coders code the same 10 articles independently, compare, and fix unclear rules → codebook v2.
2. **Double-coding (by 03.12):** all four members in two pairs, ~60 articles per pair, sampled across the five event windows.
3. **Agreement:** Krippendorff's α per variable (actor_type, stance, argument). Target ≥ 0.67, ideally ≥ 0.80. Below target → refine the rule, recode a fresh sample.
4. **Gold standard:** pairs resolve their disagreements; the resolved codes validate the LLM extraction (F1 per variable).

Statements are matched across coders by article and actor. A statement found by only one coder counts as a disagreement on "is this a statement".

Filled coding sheets (named `coding_*.xlsx`) contain article snippets; `.gitignore` keeps them out of this public repository.
