# Gemma4-12B v2 after Gemma-Biomni harness

Same 5-task agent suite as `gemma4_v2_tau2_summary.md`. Compact local harness plus Gemma-specific loop caps and tools.

| | Baseline Gemma | After harness | Glimmer-30B harness | gpt-5.6-luna |
|---|---:|---:|---:|---:|
| Agent accuracy | 83.3% | **95.0%** | 95.0% | 90.0% |
| Agent mean latency | 43.3s | **20.8s** | 8.2s | 9.8s |

## Task breakdown

| Task | Baseline | After |
|---|---|---|
| Genomics: TP53 | 36.1s · 100% | 11.1s · 75% |
| AD Risk: APOE4 | 6.6s · 100% | 6.0s · 100% |
| LabBench: Cas13a | 12.6s · 67% | 8.6s · **100%** |
| Imatinib formula | 72.5s · 75% | 33.7s · **100%** |
| DNA transcribe/translate | 88.6s · 75% | 44.9s · **100%** |

TP53 dropped a keyword (`tumor`; it said “cancers”) while getting much faster. CRISPR/Imatinib/DNA gains are harness, not extra prompt memorization.

## What changed

- Hard caps: max 4 iterations, 1 lookup, 2 code runs (counted when the tool is allowed, not only on `after_tool`).
- Dropped PubChem/ChEMBL/write_file from the active set; added `lookup_compound` (PubChem formula card) and `transcribe_translate` (standard codon table).
- MCQ closer: `[ANSWER]C[/ANSWER]` → `Cas13a` from the prompt options.
- Prefer tool cards when the model rewrites them (`C29H30N7O` → keep PubChem `C29H31N7O`; keep `AUGGGCAAGUAA` / `MGK`).
- Server: `--reasoning-budget 256`.

## Still expensive

Imatinib and DNA still spend ~30–45s generating extra `run_python` drafts before the cap fires. The 12B checkpoint ignores “stop after one tool.” Further latency cuts need a harder stop (end the loop after the first successful card), not more tools.
