# Glimmer vs Luna — current performance

Same 5 Biomni-Plus tasks. Private endpoint published as `http://xxx.xx.xx.xx/v1`.

| | Glimmer (default) | Glimmer (compact harness) | gpt-5.6-luna |
|---|---|---|---|
| Agent accuracy | 48.3% | **85.0%** | 90.0% |
| Agent mean latency | 71.0s | **7.9s** | 9.8s |
| Failed tasks | APOE, Imatinib | none | none |

## Compact harness — task breakdown

| Task | Private `Muse-Glimmer-30B` `@ xxx.xx.xx.xx/v1` | Public `gpt-5.6-luna` |
|---|---|---|
| Genomics: TP53 | 11.53s · 75% | 4.22s · 100% |
| AD Risk: APOE4 | 5.64s · 100% | 18.92s · 100% |
| LabBench: Cas13a | 2.94s · 100% | 2.93s · 100% |
| Imatinib formula | 6.16s · 75% | 7.39s · 75% |
| DNA transcribe/translate | 13.40s · 75% | 15.63s · 75% |

Remaining keyword misses are lexical, not factual: Unicode subscripts in formulas, “pro-apoptotic” vs “apoptosis”, “peptide” vs “protein”.
