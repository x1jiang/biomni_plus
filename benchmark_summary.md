# Biomedical AI Agent Comparative Benchmark — GPT-5.6-Luna

### Aggregate Performance Summary

| Engine             | Mean Latency   |   Total Retries / Parse Errors | Mean Accuracy   | Speedup vs Vanilla   |
|--------------------|----------------|--------------------------------|-----------------|----------------------|
| Biomni (Vanilla)   | 40.45s         |                              0 | 95.0%           | 1.00x (Baseline)     |
| Biomni-AD          | 22.66s         |                              0 | 90.0%           | 1.78x                |
| Biomni-Plus (Claw) | 12.76s         |                              0 | 83.3%           | 3.17x                |

### Detailed Task Breakdown

| Task Name                                            | Engine             | Latency   |   Parse/Retry Errs | Accuracy Match   | Status   |
|------------------------------------------------------|--------------------|-----------|--------------------|------------------|----------|
| Genomics: UniProt P04637 / TP53                      | Biomni (Vanilla)   | 25.80s    |                  0 | 100%             | Passed   |
| Genomics: UniProt P04637 / TP53                      | Biomni-AD          | 23.42s    |                  0 | 100%             | Passed   |
| Genomics: UniProt P04637 / TP53                      | Biomni-Plus (Claw) | 3.74s     |                  0 | 100%             | Passed   |
| AD Risk: APOE4 Isoform & Chromosome                  | Biomni (Vanilla)   | 129.49s   |                  0 | 100%             | Passed   |
| AD Risk: APOE4 Isoform & Chromosome                  | Biomni-AD          | 28.60s    |                  0 | 100%             | Passed   |
| AD Risk: APOE4 Isoform & Chromosome                  | Biomni-Plus (Claw) | 20.41s    |                  0 | 100%             | Passed   |
| LabBench QA: RNA-targeting Cas Enzyme                | Biomni (Vanilla)   | 11.63s    |                  0 | 100%             | Passed   |
| LabBench QA: RNA-targeting Cas Enzyme                | Biomni-AD          | 12.43s    |                  0 | 100%             | Passed   |
| LabBench QA: RNA-targeting Cas Enzyme                | Biomni-Plus (Claw) | 4.70s     |                  0 | 67%              | Passed   |
| Chemoinformatics: Imatinib Molecular Formula         | Biomni (Vanilla)   | 22.99s    |                  0 | 100%             | Passed   |
| Chemoinformatics: Imatinib Molecular Formula         | Biomni-AD          | 32.52s    |                  0 | 75%              | Passed   |
| Chemoinformatics: Imatinib Molecular Formula         | Biomni-Plus (Claw) | 8.04s     |                  0 | 75%              | Passed   |
| Bioinformatics Code: DNA Transcription & Translation | Biomni (Vanilla)   | 12.34s    |                  0 | 75%              | Passed   |
| Bioinformatics Code: DNA Transcription & Translation | Biomni-AD          | 16.35s    |                  0 | 75%              | Passed   |
| Bioinformatics Code: DNA Transcription & Translation | Biomni-Plus (Claw) | 26.90s    |                  0 | 75%              | Passed   |
