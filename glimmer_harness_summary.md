# Glimmer vs Luna — current performance

Same 5 Biomni-Plus tasks. Private endpoint published as `http://xxx.xx.xx.xx/v1`.

| | Glimmer (default) | Glimmer (harness v2) | Glimmer (now) | gpt-5.6-luna |
|---|---|---|---|---|
| Agent accuracy | 48.3% | 85.0% | **95.0%** | 90.0% |
| Agent mean latency | 71.0s | 7.9s | **8.2s** | 9.8s |
| Failed tasks | APOE, Imatinib | none | none | none |

## Latest task breakdown

| Task | Private `Muse-Glimmer-30B` `@ xxx.xx.xx.xx/v1` | Public `gpt-5.6-luna` |
|---|---|---|
| Genomics: TP53 | 13.50s · 100% | 4.22s · 100% |
| AD Risk: APOE4 | 5.99s · 100% | 18.92s · 100% |
| LabBench: Cas13a | 3.06s · 100% | 2.93s · 100% |
| Imatinib formula | 7.83s · 100% | 7.39s · 75% |
| DNA transcribe/translate | 10.57s · 75% | 15.63s · 75% |

DNA still says “peptide” not “protein”. TP53 is correct but slower because Glimmer spends tokens on hidden reasoning plus per-task agent startup.
