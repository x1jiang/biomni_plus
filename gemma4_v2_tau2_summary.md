# Gemma4-12B v2 (Q4_K_M) on Biomni-Plus

Same 5-task suite and compact local harness as `glimmer_harness_summary.md`.

- Weights: `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` (`gemma4-v2-Q4_K_M.gguf`, 6.9 GB)
- Serve: `llama-server` 0.4.0 (build 10809) on Apple M5 Pro, 64 GB, Metal `-ngl 99`, `--jinja`, ctx 16384
- Endpoint: `http://127.0.0.1:18080/v1` as `gemma4-agentic-v2` (ClawAgents `gemma-agentic` profile)
- Date: 2026-09-11 23:00 CDT

## Aggregate vs existing baselines

| Model | Raw mean lat | Raw accuracy | Gen tok/s | TTFT | Agent mean lat | Agent accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Gemma4-12B-v2-Q4_K_M (local) | 15.71s | 80.0% | 27.8 | 0.221s | 43.25s | **83.3%** |
| Muse-Glimmer-30B + compact harness | 9.32s | 88.3% | 121.9 | 0.110s | **8.19s** | **95.0%** |
| Muse-Glimmer-30B (default tools) | — | — | — | — | 71.0s | 48.3% |
| gpt-5.6-luna | 4.45s | 90.0% | 68.1 | 0.820s | 9.82s | 90.0% |

Gemma lands between unharnessed Glimmer (48%) and harnessed Glimmer (95%) on agent keyword accuracy. It is much slower than both Glimmer-now and Luna: Imatinib spent 7 lookup rounds, DNA spent 10 write/execute rounds.

## Agent task breakdown

| Task | Gemma4-12B-v2 | Glimmer-30B (harness) | gpt-5.6-luna |
|---|---|---|---|
| Genomics: TP53 | 36.08s · 100% | 13.50s · 100% | 4.22s · 100% |
| AD Risk: APOE4 | **6.55s · 100%** | 5.99s · 100% | 18.92s · 100% |
| LabBench: Cas13a | 12.56s · 67% | 3.06s · 100% | 2.93s · 100% |
| Imatinib formula | 72.49s · 75% | 7.83s · 100% | 7.39s · 75% |
| DNA transcribe/translate | 88.58s · 75% | 10.57s · 75% | 15.63s · 75% |

## What the scores mean

- **CRISPR 67%** — correct `[ANSWER]C[/ANSWER]`, but the visible line never says `Cas13`. Same terse miss early Glimmer had.
- **Imatinib 75%** — after 7 `query_pubchem` / `query_chembl` calls it wrote `C29H31N7` (missing the oxygen). Raw knowledge used `C29H30N7O` (wrong H count).
- **DNA agent 75%** — executed code and printed `AUGGGCAAGUAA` / `MGK`. Keyword miss is `protein` vs `peptide`, same as Luna and Glimmer. Raw-only was worse: it invented peptide **MAS**.
- **TP53 raw 75%** — said TP53 / DNA / apoptosis, never the word `tumor`. Agent recovered 100% from knowledge (0 tools).

## Read

This checkpoint is a 12B coding/agentic specialist (tau2-telecom ~55% on the model card), not a biomedical generalist. On this suite it is usable locally, recovers the DNA peptide by running code, and answers APOE faster than Luna. It does not beat harnessed Glimmer-30B on accuracy or latency, and tool loops on Imatinib/DNA dominate wall time.

Reproduce (server already accepts the HF repo via `-hf`):

```bash
llama-server \
  -hf yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF:Q4_K_M \
  --alias gemma4-agentic-v2 \
  --ctx-size 16384 -ngl 99 -fa on --jinja \
  --host 127.0.0.1 --port 18080 --repeat-penalty 1.1 --temp 0

BIOMNI_LOCAL_HARNESS=1 \
uv run python benchmark_glimmer_vs_luna.py --models gemma4_v2 --phase all --output-prefix gemma4_v2_tau2
```
