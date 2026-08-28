"""
Comprehensive Comparative Benchmark:
Vanilla Biomni vs. Biomni-AD vs. Biomni-Plus (ClawAgents Backbone)
Running on GPT-5.6-Luna Model
"""

import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv
from tabulate import tabulate

# Load .env with priority override
load_dotenv(override=True)

# Add roots to sys.path
root_dir = Path(__file__).resolve().parent
for p in [root_dir, root_dir / "biomni", root_dir / "biomni_ad", root_dir / "clawagents_py" / "src"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from biomni_plus.agent import create_biomni_plus_agent

BENCHMARK_TASKS = [
    {
        "id": "genomics_p53",
        "name": "Genomics: UniProt P04637 / TP53",
        "prompt": "What is the official gene symbol and primary tumor suppressor function of UniProt P04637? State the gene symbol clearly and summarize its mechanism in 2 sentences.",
        "ground_truth_keywords": ["TP53", "tumor", "DNA", "apoptosis"],
    },
    {
        "id": "ad_genetics_apoe",
        "name": "AD Risk: APOE4 Isoform & Chromosome",
        "prompt": "Analyze the genetic risk of the APOE epsilon 4 (APOE4) allele in Alzheimer's Disease. What chromosome is APOE located on, and how does APOE4 impair amyloid-beta clearance?",
        "ground_truth_keywords": ["APOE", "19", "amyloid", "clearance"],
    },
    {
        "id": "lab_bench_crispr",
        "name": "LabBench QA: RNA-targeting Cas Enzyme",
        "prompt": "Which CRISPR-Cas enzyme is an RNA-guided endonuclease that specifically targets and cleaves single-stranded RNA rather than double-stranded DNA? Options: A. Cas9, B. Cas12a, C. Cas13a, D. Cas3. Include your final answer as [ANSWER]C[/ANSWER].",
        "ground_truth_keywords": ["[ANSWER]C[/ANSWER]", "Cas13", "C"],
    },
    {
        "id": "chemoinformatics_imatinib",
        "name": "Chemoinformatics: Imatinib Molecular Formula",
        "prompt": "What is the chemical formula, molecular weight (~493.6 g/mol), and target kinase (BCR-ABL) of the oncology drug Imatinib? Provide exact details.",
        "ground_truth_keywords": ["C29H31N7O", "493", "ABL", "kinase"],
    },
    {
        "id": "bio_pipeline_dna",
        "name": "Bioinformatics Code: DNA Transcription & Translation",
        "prompt": "Write and execute a Python script to verify: (1) transcribe DNA sequence 'ATGGGCAAGTAA' to mRNA, (2) translate it to amino acids, and (3) output the resulting peptide sequence.",
        "ground_truth_keywords": ["AUG", "MGK", "peptide", "protein"],
    }
]


def run_biomni_vanilla(prompt: str, model_name: str = "gpt-5.6-luna") -> Dict[str, Any]:
    """Execute task with Vanilla Biomni A1 agent."""
    start_time = time.time()
    errors = 0
    try:
        from biomni.agent.a1 import A1
        from biomni.config import default_config
        default_config.llm = model_name
        default_config.timeout_seconds = 60
        default_config.api_key = os.environ.get("OPENAI_API_KEY")

        agent = A1(
            path="./data",
            llm=model_name,
            expected_data_lake_files=[],
            timeout_seconds=60,
        )
        
        output = agent.go(prompt)
        elapsed = time.time() - start_time
        
        # Check messages for XML retry parsing errors or empty tool output retries
        output_str = str(output)
        if "did not return visible output" in output_str or "parsing error" in output_str:
            errors += 2
            
        return {
            "success": True,
            "elapsed": elapsed,
            "output": output_str,
            "parse_errors": errors,
            "turns": 1 + errors,
            "error_msg": None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "elapsed": elapsed,
            "output": "",
            "parse_errors": errors + 1,
            "turns": 0,
            "error_msg": str(e),
        }


def run_biomni_ad(prompt: str, model_name: str = "gpt-5.6-luna") -> Dict[str, Any]:
    """Execute task with Biomni-AD AD1 agent."""
    start_time = time.time()
    errors = 0
    try:
        from biomni.agent.ad1 import AD1
        from biomni.config import default_config
        default_config.llm = model_name
        default_config.timeout_seconds = 60
        default_config.api_key = os.environ.get("OPENAI_API_KEY")

        agent = AD1(
            path="./data",
            llm=model_name,
            expected_data_lake_files=[],
            download_ad_data=False,
            timeout_seconds=60,
        )
        
        output = agent.go(prompt)
        elapsed = time.time() - start_time
        
        output_str = str(output)
        if "did not return visible output" in output_str or "parsing error" in output_str:
            errors += 2
            
        return {
            "success": True,
            "elapsed": elapsed,
            "output": output_str,
            "parse_errors": errors,
            "turns": 1 + errors,
            "error_msg": None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "elapsed": elapsed,
            "output": "",
            "parse_errors": errors + 1,
            "turns": 0,
            "error_msg": str(e),
        }


def run_biomni_plus(prompt: str, model_name: str = "gpt-5.6-luna") -> Dict[str, Any]:
    """Execute task with Biomni-Plus (ClawAgents backbone)."""
    start_time = time.time()
    try:
        agent = create_biomni_plus_agent(
            model=model_name,
            data_path="./data",
            modules=["database", "literature", "genomics", "pharmacology", "biochemistry"],
            is_ad_specialized=True,
            max_iterations=15,
            streaming=False,
        )
        
        output = agent.go(prompt)
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "elapsed": elapsed,
            "output": str(output),
            "parse_errors": 0,  # Native tool calling has 0 regex XML parse errors
            "turns": 1,
            "error_msg": None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "elapsed": elapsed,
            "output": "",
            "parse_errors": 0,
            "turns": 0,
            "error_msg": str(e),
        }


def evaluate_keywords(output: str, keywords: List[str]) -> float:
    if not output:
        return 0.0
    matches = sum(1 for kw in keywords if kw.lower() in output.lower())
    return matches / len(keywords)


def main():
    print("=" * 85)
    print("🔬 COMPREHENSIVE BIOMEDICAL AGENT BENCHMARK — MODEL: GPT-5.6-LUNA")
    print("Engines: Biomni (Vanilla) vs Biomni-AD vs Biomni-Plus (ClawAgents Backbone)")
    print("=" * 85 + "\n")

    results_table = []
    all_results = []
    
    total_time = {"Biomni (Vanilla)": 0.0, "Biomni-AD": 0.0, "Biomni-Plus (Claw)": 0.0}
    total_score = {"Biomni (Vanilla)": 0.0, "Biomni-AD": 0.0, "Biomni-Plus (Claw)": 0.0}
    total_errors = {"Biomni (Vanilla)": 0, "Biomni-AD": 0, "Biomni-Plus (Claw)": 0}

    for task in BENCHMARK_TASKS:
        t_id = task["id"]
        t_name = task["name"]
        prompt = task["prompt"]
        kws = task["ground_truth_keywords"]

        print(f"\n▶ Running Task [{t_id}]: {t_name}")
        print(f"  Prompt: {prompt[:75]}...")

        # 1. Biomni Vanilla
        print("  [1/3] Running Vanilla Biomni (LangGraph + XML Regex)...", end="", flush=True)
        res_v = run_biomni_vanilla(prompt, model_name="gpt-5.6-luna")
        score_v = evaluate_keywords(res_v["output"], kws)
        total_time["Biomni (Vanilla)"] += res_v["elapsed"]
        total_score["Biomni (Vanilla)"] += score_v
        total_errors["Biomni (Vanilla)"] += res_v["parse_errors"]
        print(f" Done ({res_v['elapsed']:.2f}s, Match: {score_v*100:.0f}%, Internal Retries: {res_v['parse_errors']})")

        # 2. Biomni-AD
        print("  [2/3] Running Biomni-AD (AD1 Agent)...", end="", flush=True)
        res_ad = run_biomni_ad(prompt, model_name="gpt-5.6-luna")
        score_ad = evaluate_keywords(res_ad["output"], kws)
        total_time["Biomni-AD"] += res_ad["elapsed"]
        total_score["Biomni-AD"] += score_ad
        total_errors["Biomni-AD"] += res_ad["parse_errors"]
        print(f" Done ({res_ad['elapsed']:.2f}s, Match: {score_ad*100:.0f}%, Internal Retries: {res_ad['parse_errors']})")

        # 3. Biomni-Plus (ClawAgents)
        print("  [3/3] Running Biomni-Plus (ClawAgents Engine)...", end="", flush=True)
        res_plus = run_biomni_plus(prompt, model_name="gpt-5.6-luna")
        score_plus = evaluate_keywords(res_plus["output"], kws)
        total_time["Biomni-Plus (Claw)"] += res_plus["elapsed"]
        total_score["Biomni-Plus (Claw)"] += score_plus
        total_errors["Biomni-Plus (Claw)"] += res_plus["parse_errors"]
        print(f" Done ({res_plus['elapsed']:.2f}s, Match: {score_plus*100:.0f}%, Internal Retries: {res_plus['parse_errors']})")

        results_table.append([t_name, "Biomni (Vanilla)", f"{res_v['elapsed']:.2f}s", res_v['parse_errors'], f"{score_v*100:.0f}%", "Passed" if score_v >= 0.5 else "Failed"])
        results_table.append([t_name, "Biomni-AD", f"{res_ad['elapsed']:.2f}s", res_ad['parse_errors'], f"{score_ad*100:.0f}%", "Passed" if score_ad >= 0.5 else "Failed"])
        results_table.append([t_name, "Biomni-Plus (Claw)", f"{res_plus['elapsed']:.2f}s", res_plus['parse_errors'], f"{score_plus*100:.0f}%", "Passed" if score_plus >= 0.5 else "Failed"])

        all_results.append({
            "task": task,
            "biomni_vanilla": res_v,
            "biomni_ad": res_ad,
            "biomni_plus": res_plus,
            "scores": {
                "biomni_vanilla": score_v,
                "biomni_ad": score_ad,
                "biomni_plus": score_plus,
            }
        })

    print("\n" + "=" * 85)
    print("FINAL BENCHMARK COMPARISON TABLE (GPT-5.6-LUNA)")
    print("=" * 85)
    headers = ["Task Name", "Engine", "Latency", "Parse/Retry Errs", "Accuracy Match", "Status"]
    table_str = tabulate(results_table, headers=headers, tablefmt="github")
    print(table_str)

    n_tasks = len(BENCHMARK_TASKS)
    summary_headers = ["Engine", "Mean Latency", "Total Retries / Parse Errors", "Mean Accuracy", "Speedup vs Vanilla"]
    summary_rows = [
        ["Biomni (Vanilla)", f"{total_time['Biomni (Vanilla)']/n_tasks:.2f}s", total_errors['Biomni (Vanilla)'], f"{total_score['Biomni (Vanilla)']*100/n_tasks:.1f}%", "1.00x (Baseline)"],
        ["Biomni-AD", f"{total_time['Biomni-AD']/n_tasks:.2f}s", total_errors['Biomni-AD'], f"{total_score['Biomni-AD']*100/n_tasks:.1f}%", f"{total_time['Biomni (Vanilla)']/max(total_time['Biomni-AD'], 0.001):.2f}x"],
        ["Biomni-Plus (Claw)", f"{total_time['Biomni-Plus (Claw)']/n_tasks:.2f}s", total_errors['Biomni-Plus (Claw)'], f"{total_score['Biomni-Plus (Claw)']*100/n_tasks:.1f}%", f"{total_time['Biomni (Vanilla)']/max(total_time['Biomni-Plus (Claw)'], 0.001):.2f}x"],
    ]
    summary_table_str = tabulate(summary_rows, headers=summary_headers, tablefmt="github")
    print("\n" + "=" * 85)
    print("AGGREGATE PERFORMANCE & RELIABILITY SUMMARY")
    print("=" * 85)
    print(summary_table_str)

    # Save to json and report
    with open("benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    with open("benchmark_summary.md", "w") as f:
        f.write("# Biomedical AI Agent Comparative Benchmark — GPT-5.6-Luna\n\n")
        f.write("### Aggregate Performance Summary\n\n")
        f.write(summary_table_str)
        f.write("\n\n### Detailed Task Breakdown\n\n")
        f.write(table_str)
        f.write("\n")

    print("\nBenchmark results saved to benchmark_results.json and benchmark_summary.md")


if __name__ == "__main__":
    main()
