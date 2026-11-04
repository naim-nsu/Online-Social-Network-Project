# Query refinement log (Team 6)

The professor asked us to include the actual search query and document how it is refined.
This file is the start of that log.

## Version 1 (used 2026-10-27)

The original Boolean query (see the Media Cloud export `.txt`), run on the UK, Germany, China and US National collections for 2026-01-01 to 2026-10-26.

Result: 7,856 stories, which became 6,512 after dedupe. Only about 924 titles (12%) mention pause, moratorium, ban, halt or superintelligence.

Problems found:

1. **Low precision.** The clause `(ban OR halt OR prohibition ...) AND (development OR training)`, combined with `AI`, matches any article that uses those common words anywhere. Examples are data-center bans, school AI policies and a newspaper cartoon.
2. **Missing word forms.** Exact terms like `pause` and `pausing` do not match `paused`, `pauses`, `halted` or `halts`. So "OpenAI paused training" can be missed.
3. **Key event coverage is uneven.** The weekly mean of stories per day:

| Event | Date | 7 days before | 7 days after |
|---|---|---|---|
| Hugging Face incident | 21 Jul | 32.1 | 29.4 |
| OpenAI training pause | 18 Aug | 20.9 | 36.6 |
| Ban Artificial Superintelligence Act introduced | 3 Sep | 28.4 | 33.9 |

There is no rise after the Hugging Face incident. It was reported as a security story, and the query only catches it when a pause or ban is mentioned in the same article.

## Version 2 (run 2026-11-01)

Check the syntax against the Media Cloud search guide before running. The new Media Cloud search supports `*` wildcards and `"..."~N` proximity, but test both on a small date range first.

```
(
  "artificial intelligence" OR AI OR "generative AI" OR "frontier AI"
  OR "large language model*" OR superintelligence OR AGI
)
AND
(
  "AI pause" OR "pause AI" OR PauseAI OR "AI moratorium" OR "moratorium on AI"
  OR "Pause Giant AI Experiments" OR "Statement on Superintelligence"
  OR "Ban Artificial Superintelligence Act" OR "superintelligence ban"
  OR "training pause" OR "paused training" OR "pause training"
  OR "pause development" OR "halt development"
  OR "(pause* OR halt* OR moratorium OR ban) (development OR training OR superintelligence OR \"frontier model*\")"~8
  OR ("Hugging Face" AND (attack OR breach OR hack* OR incident))
)
```

What changes and why:

- **Proximity instead of plain AND.** The pause/ban word has to appear within about 8 words of development, training or superintelligence, so random co-occurrence across a long article no longer counts. This should raise precision a lot.
- **Wildcards** (`pause*`, `halt*`) catch paused, pauses, halted and halting.
- **Event-specific phrases** cover the three key events directly. The Hugging Face line is broader, which is on purpose: the professor's question about whether events shift the themes (for example toward security) needs those articles too.

Proximity with an OR group inside quotes is not supported everywhere. If Media Cloud rejects it, use a few explicit pairs instead, such as `"pause development"~5 OR "halt training"~5 ...`.

## How to document each version

For each version, record:

1. the date it was run and the number of stories,
2. a **precision check**: code 50 random stories as relevant or not, and report the share that are relevant,
3. coverage around the 3 key events, using the table above.

Then keep the version with the best balance. Media Cloud story ids appear to be derived from the URL, so `pipeline.py check` should skip links that were already checked when you rerun it on a new export (use the same `output` folder).

### Version 2 results

Same collections and dates as v1. Result: 2,946 stories, 2,200 after dedupe (518 wire reprints, 156 non-English, mostly German, 71 same-title duplicates, 1 URL duplicate). 960 of these were also in v1, and 1,986 are new.

**What improved**

- The noise is mostly gone. The 562 v1 titles with "ban/moratorium/pause" that v2 dropped are mainly data-center moratoriums, social-media bans for children, sports bans and Ray-Ban glasses.
- The Hugging Face incident is now captured. Coverage went from 2.3 stories a day in the week before 21 Jul to 45.9 a day in the week after. "Hugging Face" appears in 241 titles in v2, against 56 in v1.
- The OpenAI training pause (18 Aug) is captured, for example "OpenAI paused AI training for two weeks...". There is no separate before/after jump, because it falls inside the Hugging Face aftermath.
- The Ban ASI Act (3 Sep) rose from 18.3 to 29.0 stories a day, with 75 stories on 3 Sep itself.
- A new candidate event shows up: **5 Jun, Anthropic's call for a way to pause AI development** (24 stories that day).

**What got worse (important)**

v2 **lost core pause-debate stories** that v1 had. I counted about 150 on-topic titles, for example:

- "Bernie Sanders Introduces Bill to Ban Artificial Superintelligence"
- "OpenAI to Halt Training of Some Models"
- "Johnson Says No Moratorium on AI, Would Give China Competitive Edge"
- "What could a global pause on AI look like?"
- the whole mid-September wave of "AI slowdown" stories, such as Zuckerberg, Trump and Vance reacting to CEOs calling for a slowdown

Reasons:

1. The debate often uses **"slowdown" / "slow down"**, which neither version searched for.
2. The grouped proximity clause probably did not work as intended in Media Cloud, so ordinary phrasings like "bill to ban artificial superintelligence" were missed.

**Precision (rough, titles only):** of 2,200 stories, about 127 titles mention pause/ban terms, 654 security or Hugging Face, and 323 safety or regulation. The other ~1,100 are mixed. Many are still related (AI risk, Anthropic warnings), but some are noise, including 50 "AP Top News at ..." digests and stories about migrants or a flight brawl. A real precision check needs a coded sample of 50.

## Version 3 (proposal)

Keep what v2 does well, bring back the v1 pause terms without the broad ban/development clause, and add "slowdown":

```
(
  "artificial intelligence" OR AI OR "generative AI" OR "frontier AI"
  OR "large language model*" OR superintelligence OR AGI
)
AND
(
  "AI pause" OR "pause AI" OR PauseAI OR "pause on AI" OR "global pause"
  OR "AI moratorium" OR "moratorium on AI" OR "Pause Giant AI Experiments"
  OR "Statement on Superintelligence"
  OR "AI slowdown" OR "slow down AI" OR "slowdown in AI" OR "slow the pace"
  OR "ban artificial superintelligence" OR "ban on superintelligence"
  OR "superintelligence ban" OR "Ban Artificial Superintelligence Act"
  OR "pause development"~5 OR "pause training"~5 OR "paused training"~5
  OR "halt development"~5 OR "halt training"~5 OR "slow development"~5
  OR ("Hugging Face" AND (hack* OR breach OR attack))
)
```

Before using v3, compare it with v1 and v2 using three checks:

1. **Recall:** do the sample titles listed above appear?
2. **Precision:** code 50 random titles.
3. **Events:** run the before/after table for the key events, including 5 Jun.

Drop AP digest titles ("AP Top ... News at") in the dedupe step.

### Version 3 results (run 2026-11-02)

Result: 4,989 stories, 3,714 after dedupe (1,006 wire reprints, 152 non-English, 116 same-title duplicates). v3 contains 2,827 of v2's 2,946 stories. The 119 it misses are mostly rogue-agent and security side stories.

**Recall check** (sample titles that v2 missed):

| Title | v1 | v2 | v3 |
|---|---|---|---|
| Sanders: Ban Artificial Superintelligence | yes | yes | yes |
| "What could a global pause on AI look like?" | yes | no | yes |
| Zuckerberg: no industry-wide slowdown | yes | no | yes |
| Trump dismisses AI slowdown calls | yes | no | yes |
| Hugging Face hack coverage | partly | yes | yes |
| OpenAI paused training for two weeks | yes | yes | yes |
| Anthropic urges a way to pause (5 Jun) | yes | yes | yes |
| "OpenAI to Halt Training of Some Models" | yes | no | no |
| "Johnson: No Moratorium on AI" | yes | no | no |

**Spikes:**

- Mid-September is now by far the largest wave: 317 stories on 14 Sep, against 111 in v2. This is the "Pacing the Frontier" / AI slowdown call by the big AI companies, with reactions from Trump, China, Zuckerberg and the markets. v2 largely missed it.
- 5 Jun (Anthropic) rises to 53 stories.
- Hugging Face (21 to 31 Jul) is unchanged.

**Noise:** about 2,000 of 3,714 titles do not match any topic keyword. There are 157 "AP Top News" digests, plus unrelated stories such as celebrity news and bond markets, which mostly come from digest or live-blog pages.

**Decision:** use v3. It keeps everything v2 found and adds the core slowdown debate. Remove the noise afterwards with (1) a filter for AP digests and live-blog titles and (2) a relevance check on the full text.

Optional v3.1: add `"Pacing the Frontier"`, `"no moratorium"`, `"halt training"` and `"halt"~3 "training"`.

**Why v3 misses those two v1 articles:** the events themselves are covered in v3. Only those two particular copies are missing.

- OpenAI halting training (27 to 28 Sep): v3 has the same story from The Guardian, Ars Technica and Metro. Only the Gizmodo copy is missing.
- Mike Johnson rejecting a moratorium (13 to 15 Sep): v3 has six articles, including Fox News ("Mike Johnson rejects AI moratorium over China threat..."), USA Today, The Verge and The Independent. Only the US News copy is missing.

v1 found those two copies through its broad clause, which matched `moratorium`/`halt` anywhere in the article together with `development`/`training` anywhere. That same clause produced the data-center noise. The narrow phrases in v3 (`"moratorium on AI"`, `"halt training"~5`) likely fail on them because Media Cloud matches the article text, and in those two articles the words are probably not close together (for example "no moratorium on artificial intelligence development"). Missing single copies when the story is still covered is an acceptable precision/recall trade-off.
