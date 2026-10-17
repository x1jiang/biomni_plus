# Hard Biomedical Reasoning Benchmark

- Private Endpoint: `http://xxx.xx.xx.xx/v1`
- Spark Model: `meta-models/Muse-Spark-Open-816B-A42B`

| Hard Task                                                             | Model                        | Latency   | Strict Rubric Score   |
|-----------------------------------------------------------------------|------------------------------|-----------|-----------------------|
| Pharmacogenomics: CYP2C19*2/*3 & Clopidogrel Bioactivation            | Muse-Spark-816B-A42B         | 79.79s    | 6/6 (100%)            |
| Pharmacogenomics: CYP2C19*2/*3 & Clopidogrel Bioactivation            | gpt-5.6-luna                 | 4.13s     | 6/6 (100%)            |
| Pharmacogenomics: CYP2C19*2/*3 & Clopidogrel Bioactivation            | gpt-4o-mini (small baseline) | 1.47s     | 5/6 (83%)             |
| Structural Oncology: BCR-ABL1 T315I Gatekeeper & STAMP Inhibition     | Muse-Spark-816B-A42B         | 98.76s    | 6/6 (100%)            |
| Structural Oncology: BCR-ABL1 T315I Gatekeeper & STAMP Inhibition     | gpt-5.6-luna                 | 4.05s     | 6/6 (100%)            |
| Structural Oncology: BCR-ABL1 T315I Gatekeeper & STAMP Inhibition     | gpt-4o-mini (small baseline) | 1.62s     | 6/6 (100%)            |
| AD Protective Genetics: APOE3 Christchurch & RELN-COLBOS Epistasis    | Muse-Spark-816B-A42B         | 72.75s    | 6/6 (100%)            |
| AD Protective Genetics: APOE3 Christchurch & RELN-COLBOS Epistasis    | gpt-5.6-luna                 | 13.15s    | 0/6 (0%)              |
| AD Protective Genetics: APOE3 Christchurch & RELN-COLBOS Epistasis    | gpt-4o-mini (small baseline) | 1.76s     | 4/6 (67%)             |
| Coding Frameshift Math: Single-Nucleotide Deletion & Premature Stop   | Muse-Spark-816B-A42B         | 109.50s   | 6/6 (100%)            |
| Coding Frameshift Math: Single-Nucleotide Deletion & Premature Stop   | gpt-5.6-luna                 | 6.12s     | 6/6 (100%)            |
| Coding Frameshift Math: Single-Nucleotide Deletion & Premature Stop   | gpt-4o-mini (small baseline) | 3.04s     | 5/6 (83%)             |
| CRISPR Engineering: HBB E6V Transversion & pegRNA Architecture        | Muse-Spark-816B-A42B         | 60.48s    | 6/6 (100%)            |
| CRISPR Engineering: HBB E6V Transversion & pegRNA Architecture        | gpt-5.6-luna                 | 4.16s     | 5/6 (83%)             |
| CRISPR Engineering: HBB E6V Transversion & pegRNA Architecture        | gpt-4o-mini (small baseline) | 2.25s     | 4/6 (67%)             |
| Quantitative Clinical Genetics: HWE & Bayesian Posterior Carrier Risk | Muse-Spark-816B-A42B         | 85.53s    | 6/6 (100%)            |
| Quantitative Clinical Genetics: HWE & Bayesian Posterior Carrier Risk | gpt-5.6-luna                 | 3.95s     | 6/6 (100%)            |
| Quantitative Clinical Genetics: HWE & Bayesian Posterior Carrier Risk | gpt-4o-mini (small baseline) | 5.91s     | 3/6 (50%)             |
