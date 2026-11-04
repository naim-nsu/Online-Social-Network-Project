# Outlet coverage (draft for the methods / limitations section)

Of the 3,496 unique English-language stories retrieved with query v3 (173 outlets, 1 January to 26 October 2026), we obtained the full text of 2,079 (59.5%). Collection respected each site's robots.txt and did not bypass paywalls. 1,200 stories (34.3%) were behind a paywall or marked by the publisher as not freely accessible. 98 (2.8%) were excluded by robots.txt, 5 links were broken, and 114 (3.3%) failed for technical reasons such as timeouts or rate limits.

Coverage varies strongly by outlet:

- **Fully or almost fully covered:** The Guardian (99%), TechCrunch (99%), Wired (98%), The Independent (98%), Fox News (96%), CNBC (84%), and tech and online outlets such as Gizmodo, Engadget, TechRadar and IBTimes (100%). Several right-leaning outlets are also fully covered (New York Post, Breitbart, Daily Caller).
- **Poorly or not covered:** business and financial media, namely Fortune (0.5% of 206), Business Insider (0%), Bloomberg (2%), Reuters (0%) and Forbes (28%). Also several major general-news outlets: CNN, USA Today, LA Times, The Atlantic, Boston Globe, Chicago Tribune and PBS (all 0%). The Verge reached 8%.

**Implication.** The full-text corpus over-represents tech media, UK quality press and right-leaning US outlets, and under-represents business and financial media. This is relevant for H1, because industry voices are likely quoted most in exactly those business outlets. Paywalled articles are excluded from the analysis and not retrieved from other sources. Analyses based on metadata (publication counts, timing around key events) use all stories in the analysis window (1 June to 26 October 2026: 3,170 stories). Text-based analyses (actors, arguments, topics) use only the freely accessible full texts, and we report this coverage bias as a limitation. In particular, voices quoted mainly in the business press may be underrepresented.

_Full per-outlet table: `output/04_outlet_coverage.csv`._
