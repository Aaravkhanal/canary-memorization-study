# Experiment Timeline – Canary Memorization Study

| # | Job | Description | Start (local = UTC + 5:30) | End (local) | Status |
|---|-----|-------------|---------------------------|------------|--------|
| 1 | Medium‑model pre‑training (exp 018) | 25.7 M‑param model, 180 M tokens (≈11 k steps) | 2026‑10‑04 08:20 AM | – | Queued |
| 2 | Large‑model pre‑training (exp 022) | 48.1 M‑param model, full TinyStoriesV2 (≈545 M tokens) | 2026‑10‑04 08:20 AM | – | Queued |
| 3 | Canary freq 100 – baseline | Small model (≈14 M) trained on frequency‑100 corpus, baseline architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 4 | Canary freq 100 – learned‑pos | Same as #3 but with `variant_a_learned_pos` architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 5 | Canary freq 500 – baseline | Small model trained on frequency‑500 corpus, baseline architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 6 | Canary freq 500 – learned‑pos | Same as #5 but with `variant_a_learned_pos` architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 7 | Full‑split loss eval – medium model | Compute val‑loss / perplexity for 512 / 1024‑token contexts (medium checkpoint) | – | – | Queued |
| 8 | Full‑split loss eval – large model | Same as #7 but for the large model checkpoint | – | – | Queued |
| 9 | Memorization evaluation | `scripts/eval_memorization.py` on every new canary checkpoint | – | – | Queued |
|10 | Novelty evaluation | `scripts/eval_novelty.py` on every new canary checkpoint | – | – | Queued |
|11 | Trade‑off aggregation & plot | `scripts/analyze_tradeoff.py` – combines memorisation + novelty results into CSV & PNG | – | – | Queued |
|12 | Git add | Stage modified/untracked files in the repo | 2026‑10‑04 11:43 AM | 2026‑10‑04 11:44 AM | Completed |
|13 | Git commit | Commit: “Add tradeoff results and labelling files” | 2026‑10‑04 11:45 AM | 2026‑10‑04 11:45 AM | Completed |
|14 | Git push | Push to `origin/main` | 2026‑10‑04 11:47 AM | 2026‑10‑04 11:50 AM | Completed |

*All timestamps are local (UTC + 5:30).*
