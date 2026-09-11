"""
Head-to-head: Muse-Glimmer-30B (local v1) vs gpt-5.6-luna (OpenAI).

Measures raw knowledge latency/accuracy, generation throughput, and the
same 5 Biomni-Plus agent tasks used in benchmark_biomni_vs_claw.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from tabulate import tabulate

load_dotenv(override=True)
os.environ["CLAW_LEARN"] = "0"

root_dir = Path(__file__).resolve().parent
for p in [root_dir, root_dir / "biomni", root_dir / "clawagents_py" / "src"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from biomni_plus.agent import create_biomni_plus_agent

PUBLIC_GLIMMER_ENDPOINT = "http://xxx.xx.xx.xx/v1"
GLIMMER_BASE = os.getenv("GLIMMER_30B_BACKEND", PUBLIC_GLIMMER_ENDPOINT)
GLIMMER_MODEL = os.getenv("GLIMMER_30B_MODEL", "Muse-Glimmer-30B")
LUNA_MODEL = os.getenv("LUNA_MODEL", "gpt-5.6-luna")


def published_endpoint(url: str) -> str:
    """Never write raw IPv4 hosts into artifacts that may be committed."""
    if re.search(r"\d{1,3}(?:\.\d{1,3}){3}", url or ""):
        return PUBLIC_GLIMMER_ENDPOINT
    return url or PUBLIC_GLIMMER_ENDPOINT

BENCHMARK_TASKS = [
    {
        "id": "genomics_p53",
        "name": "Genomics: UniProt P04637 / TP53",
        "prompt": (
            "What is the official gene symbol and primary tumor suppressor "
            "function of UniProt P04637? State the gene symbol clearly and "
            "summarize its mechanism in 2 sentences."
        ),
        "ground_truth_keywords": ["TP53", "tumor", "DNA", "apoptosis"],
    },
    {
        "id": "ad_genetics_apoe",
        "name": "AD Risk: APOE4 Isoform & Chromosome",
        "prompt": (
            "Analyze the genetic risk of the APOE epsilon 4 (APOE4) allele in "
            "Alzheimer's Disease. What chromosome is APOE located on, and how "
            "does APOE4 impair amyloid-beta clearance?"
        ),
        "ground_truth_keywords": ["APOE", "19", "amyloid", "clearance"],
    },
    {
        "id": "lab_bench_crispr",
        "name": "LabBench QA: RNA-targeting Cas Enzyme",
        "prompt": (
            "Which CRISPR-Cas enzyme is an RNA-guided endonuclease that "
            "specifically targets and cleaves single-stranded RNA rather than "
            "double-stranded DNA? Options: A. Cas9, B. Cas12a, C. Cas13a, "
            "D. Cas3. Include your final answer as [ANSWER]C[/ANSWER]."
        ),
        "ground_truth_keywords": ["[ANSWER]C[/ANSWER]", "Cas13", "C"],
    },
    {
        "id": "chemoinformatics_imatinib",
        "name": "Chemoinformatics: Imatinib Molecular Formula",
        "prompt": (
            "What is the chemical formula, molecular weight (~493.6 g/mol), "
            "and target kinase (BCR-ABL) of the oncology drug Imatinib? "
            "Provide exact details."
        ),
        "ground_truth_keywords": ["C29H31N7O", "493", "ABL", "kinase"],
    },
    {
        "id": "bio_pipeline_dna",
        "name": "Bioinformatics Code: DNA Transcription & Translation",
        "prompt": (
            "Write and execute a Python script to verify: (1) transcribe DNA "
            "sequence 'ATGGGCAAGTAA' to mRNA, (2) translate it to amino acids, "
            "and (3) output the resulting peptide sequence."
        ),
        "ground_truth_keywords": ["AUG", "MGK", "peptide", "protein"],
    },
]

THROUGHPUT_PROMPT = (
    "Write a 180-word scientific paragraph on TP53 as a tumor suppressor, "
    "including DNA damage response and apoptosis. Do not use bullet points."
)

MODELS = [
    {
        "id": "glimmer_30b",
        "label": "Muse-Glimmer-30B",
        "model": GLIMMER_MODEL,
        "base_url": GLIMMER_BASE,
        "api_key": os.getenv("GLIMMER_API_KEY", "not-needed"),
        "omit_temperature": False,
        "temperature": 0,
    },
    {
        "id": "luna",
        "label": "gpt-5.6-luna",
        "model": LUNA_MODEL,
        "base_url": None,
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "omit_temperature": True,
        "temperature": None,
    },
]


def evaluate_keywords(output: str, keywords: List[str]) -> float:
    if not output:
        return 0.0
    blob = output.lower()
    return sum(1 for kw in keywords if kw.lower() in blob) / len(keywords)


def _message_text(message: Any) -> str:
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning is None and isinstance(message, dict):
        reasoning = message.get("reasoning_content")
    parts = [p for p in (content, reasoning) if p]
    return "\n".join(parts)


def _usage_dict(usage: Any) -> Dict[str, int]:
    if not usage:
        return {}
    details = getattr(usage, "completion_tokens_details", None)
    if details is None and isinstance(usage, dict):
        details = usage.get("completion_tokens_details")
    reasoning = 0
    if details is not None:
        reasoning = int(getattr(details, "reasoning_tokens", 0) or 0)
        if not reasoning and isinstance(details, dict):
            reasoning = int(details.get("reasoning_tokens") or 0)
    if not reasoning and isinstance(usage, dict):
        reasoning = int(usage.get("reasoning_tokens") or 0)
    return {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or (usage.get("prompt_tokens") if isinstance(usage, dict) else 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or (usage.get("completion_tokens") if isinstance(usage, dict) else 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or (usage.get("total_tokens") if isinstance(usage, dict) else 0) or 0),
        "reasoning_tokens": reasoning,
    }


def make_client(spec: Dict[str, Any]) -> OpenAI:
    kwargs: Dict[str, Any] = {"api_key": spec["api_key"] or "not-needed"}
    if spec["base_url"]:
        kwargs["base_url"] = spec["base_url"]
    return OpenAI(**kwargs)


def raw_complete(
    spec: Dict[str, Any],
    prompt: str,
    *,
    max_tokens: int = 512,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    client = make_client(spec)
    kwargs: Dict[str, Any] = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_tokens,
        "timeout": timeout,
    }
    if not spec["omit_temperature"]:
        kwargs["temperature"] = spec["temperature"]
    start = time.time()
    try:
        resp = client.chat.completions.create(**kwargs)
        elapsed = time.time() - start
        choice = resp.choices[0]
        message = choice.message
        content = message.content or ""
        scored = content or _message_text(message)
        usage = _usage_dict(resp.usage)
        return {
            "success": True,
            "elapsed": elapsed,
            "content": content,
            "scored_text": scored,
            "finish_reason": choice.finish_reason,
            "usage": usage,
            "tok_per_sec": (usage.get("completion_tokens") or 0) / elapsed if elapsed else 0.0,
            "error_msg": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "elapsed": time.time() - start,
            "content": "",
            "scored_text": "",
            "finish_reason": None,
            "usage": {},
            "tok_per_sec": 0.0,
            "error_msg": f"{type(exc).__name__}: {exc}",
        }


def raw_ttft(spec: Dict[str, Any], prompt: str, *, max_tokens: int = 64) -> Dict[str, Any]:
    client = make_client(spec)
    kwargs: Dict[str, Any] = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if not spec["omit_temperature"]:
        kwargs["temperature"] = spec["temperature"]
    start = time.time()
    first = None
    usage = {}
    text_parts: List[str] = []
    try:
        stream = client.chat.completions.create(**kwargs)
        for chunk in stream:
            if getattr(chunk, "usage", None):
                usage = _usage_dict(chunk.usage)
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None) or getattr(delta, "reasoning_content", None)
            if piece:
                if first is None:
                    first = time.time() - start
                text_parts.append(piece)
        elapsed = time.time() - start
        return {
            "success": True,
            "ttft": first,
            "elapsed": elapsed,
            "usage": usage,
            "chars": sum(len(p) for p in text_parts),
            "error_msg": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "ttft": first,
            "elapsed": time.time() - start,
            "usage": usage,
            "chars": sum(len(p) for p in text_parts),
            "error_msg": f"{type(exc).__name__}: {exc}",
        }


def run_agent_task(spec: Dict[str, Any], prompt: str, *, timeout: float = 240.0) -> Dict[str, Any]:
    start = time.time()

    def _invoke() -> str:
        agent = create_biomni_plus_agent(
            model=spec["model"],
            data_path=str(root_dir / "data"),
            modules=["database", "literature", "genomics", "pharmacology", "biochemistry"],
            is_ad_specialized=True,
            max_iterations=15,
            streaming=False,
            api_key=spec["api_key"],
            base_url=spec["base_url"],
        )
        return agent.go(prompt)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            output = pool.submit(_invoke).result(timeout=timeout)
        return {
            "success": True,
            "elapsed": time.time() - start,
            "output": str(output or ""),
            "error_msg": None,
        }
    except FuturesTimeout:
        return {
            "success": False,
            "elapsed": time.time() - start,
            "output": "",
            "error_msg": f"timeout after {timeout:.0f}s",
        }
    except Exception as exc:
        return {
            "success": False,
            "elapsed": time.time() - start,
            "output": "",
            "error_msg": f"{type(exc).__name__}: {exc}",
        }


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def pct(value: float) -> str:
    return f"{value * 100:.0f}%"


OUTPUT_PREFIX = "glimmer_vs_luna"


def write_outputs(payload: Dict[str, Any], table_raw: str, table_agent: str, table_sum: str) -> None:
    json_path = root_dir / f"{OUTPUT_PREFIX}_results.json"
    md_path = root_dir / f"{OUTPUT_PREFIX}_summary.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str))
    md_path.write_text(
        "\n".join(
            [
                "# Muse-Glimmer-30B vs gpt-5.6-luna",
                "",
                f"- Glimmer endpoint: `{published_endpoint(GLIMMER_BASE)}`",
                f"- Glimmer model: `{GLIMMER_MODEL}`",
                f"- Luna model: `{LUNA_MODEL}`",
                f"- Date: {time.strftime('%Y-%m-%d %H:%M %Z')}",
                "",
                "## Aggregate",
                "",
                table_sum,
                "",
                "## Raw knowledge (no tools)",
                "",
                table_raw,
                "",
                "## Biomni-Plus agent tasks",
                "",
                table_agent,
                "",
            ]
        )
    )
    print(f"\nSaved {json_path.name} and {md_path.name}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Muse-Glimmer-30B vs gpt-5.6-luna")
    parser.add_argument(
        "--models",
        default="glimmer_30b,luna",
        help="Comma-separated model ids: glimmer_30b,luna",
    )
    parser.add_argument(
        "--phase",
        default="all",
        choices=("all", "raw", "agent"),
        help="Which phases to run",
    )
    parser.add_argument(
        "--output-prefix",
        default="glimmer_vs_luna",
        help="Basename for results json/md files",
    )
    args = parser.parse_args()
    selected = {m.strip() for m in args.models.split(",") if m.strip()}
    global MODELS, OUTPUT_PREFIX
    OUTPUT_PREFIX = args.output_prefix
    MODELS = [spec for spec in MODELS if spec["id"] in selected]
    if not MODELS:
        raise SystemExit(f"No models matched {selected!r}")
    run_raw = args.phase in ("all", "raw")
    run_agent = args.phase in ("all", "agent")
    _run_benchmark(run_raw=run_raw, run_agent=run_agent)


def _run_benchmark(*, run_raw: bool, run_agent: bool) -> None:
    if any(spec["id"] == "luna" for spec in MODELS) and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required to run gpt-5.6-luna.")

    print("=" * 88)
    print("Muse-Glimmer-30B vs gpt-5.6-luna")
    print(f"Glimmer: {GLIMMER_MODEL} @ {GLIMMER_BASE}")
    print(f"Luna:    {LUNA_MODEL} @ OpenAI")
    print("=" * 88)

    raw_rows: List[List[Any]] = []
    agent_rows: List[List[Any]] = []
    raw_results: List[Dict[str, Any]] = []
    agent_results: List[Dict[str, Any]] = []
    throughput: Dict[str, Any] = {}
    ttft: Dict[str, Any] = {}

    if run_raw:
        print("\n--- Raw knowledge (direct chat, no tools) ---")
    for task in BENCHMARK_TASKS if run_raw else []:
        task_pack = {"task": task["id"], "models": {}}
        print(f"\n▶ {task['name']}")
        for spec in MODELS:
            res = raw_complete(spec, task["prompt"], max_tokens=2048)
            score = evaluate_keywords(res["scored_text"], task["ground_truth_keywords"])
            res["score"] = score
            task_pack["models"][spec["id"]] = res
            status = "ok" if res["success"] else "fail"
            print(
                f"  {spec['label']:<22} {res['elapsed']:6.2f}s  "
                f"match {score*100:3.0f}%  {res['tok_per_sec']:5.1f} tok/s  {status}"
            )
            if res["error_msg"]:
                print(f"    error: {res['error_msg'][:220]}")
            raw_rows.append(
                [
                    task["name"],
                    spec["label"],
                    f"{res['elapsed']:.2f}s",
                    f"{score*100:.0f}%",
                    res["usage"].get("completion_tokens", 0),
                    res["usage"].get("reasoning_tokens", 0),
                    f"{res['tok_per_sec']:.1f}",
                    "Passed" if score >= 0.5 else "Failed",
                ]
            )
        raw_results.append(task_pack)

    if run_raw:
        print("\n--- Throughput + TTFT ---")
    for spec in MODELS if run_raw else []:
        thru = raw_complete(spec, THROUGHPUT_PROMPT, max_tokens=256)
        first = raw_ttft(spec, "Reply with the word PONG and nothing else.", max_tokens=32)
        throughput[spec["id"]] = thru
        ttft[spec["id"]] = first
        print(
            f"  {spec['label']:<22} gen {thru['elapsed']:.2f}s  "
            f"{thru['tok_per_sec']:.1f} tok/s  "
            f"ttft {first.get('ttft') if first.get('ttft') is not None else 'n/a'}"
        )

    if run_agent:
        print("\n--- Biomni-Plus agent tasks ---")
    for task in BENCHMARK_TASKS if run_agent else []:
        task_pack = {"task": task["id"], "models": {}}
        print(f"\n▶ {task['name']}")
        for spec in MODELS:
            res = run_agent_task(spec, task["prompt"], timeout=240.0)
            score = evaluate_keywords(res["output"], task["ground_truth_keywords"])
            res["score"] = score
            task_pack["models"][spec["id"]] = {
                **res,
                "output": (res["output"] or "")[:4000],
            }
            status = "ok" if res["success"] else "fail"
            print(
                f"  {spec['label']:<22} {res['elapsed']:6.2f}s  "
                f"match {score*100:3.0f}%  {status}"
            )
            if res["error_msg"]:
                print(f"    error: {res['error_msg'][:220]}")
            agent_rows.append(
                [
                    task["name"],
                    spec["label"],
                    f"{res['elapsed']:.2f}s",
                    f"{score*100:.0f}%",
                    "Passed" if score >= 0.5 else "Failed",
                    (res["error_msg"] or "")[:80],
                ]
            )
        agent_results.append(task_pack)

    def collect(phase: List[Dict[str, Any]], model_id: str, key: str) -> List[float]:
        return [float(item["models"][model_id][key]) for item in phase if model_id in item["models"]]

    summary_rows = []
    for spec in MODELS:
        mid = spec["id"]
        raw_lat = collect(raw_results, mid, "elapsed")
        raw_score = collect(raw_results, mid, "score")
        agent_lat = collect(agent_results, mid, "elapsed")
        agent_score = collect(agent_results, mid, "score")
        thru = throughput.get(mid) or {}
        first = ttft.get(mid) or {}
        summary_rows.append(
            [
                spec["label"],
                f"{mean(raw_lat):.2f}s" if raw_lat else "n/a",
                f"{mean(raw_score)*100:.1f}%" if raw_score else "n/a",
                f"{thru['tok_per_sec']:.1f}" if thru.get("tok_per_sec") is not None else "n/a",
                f"{first['ttft']:.3f}s" if first.get("ttft") is not None else "n/a",
                f"{mean(agent_lat):.2f}s" if agent_lat else "n/a",
                f"{mean(agent_score)*100:.1f}%" if agent_score else "n/a",
            ]
        )

    raw_table = tabulate(
        raw_rows,
        headers=["Task", "Model", "Latency", "Accuracy", "Compl. toks", "Reason toks", "tok/s", "Status"],
        tablefmt="github",
    )
    agent_table = tabulate(
        agent_rows,
        headers=["Task", "Model", "Latency", "Accuracy", "Status", "Error"],
        tablefmt="github",
    )
    summary_table = tabulate(
        summary_rows,
        headers=[
            "Model",
            "Raw mean lat",
            "Raw accuracy",
            "Gen tok/s",
            "TTFT",
            "Agent mean lat",
            "Agent accuracy",
        ],
        tablefmt="github",
    )

    print("\n" + "=" * 88)
    print("RAW KNOWLEDGE")
    print("=" * 88)
    print(raw_table)
    print("\n" + "=" * 88)
    print("BIOMNI-PLUS AGENT")
    print("=" * 88)
    print(agent_table)
    print("\n" + "=" * 88)
    print("AGGREGATE")
    print("=" * 88)
    print(summary_table)

    payload = {
        "meta": {
            "glimmer_backend": published_endpoint(GLIMMER_BASE),
            "glimmer_model": GLIMMER_MODEL,
            "luna_model": LUNA_MODEL,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
        "raw": raw_results,
        "throughput": throughput,
        "ttft": ttft,
        "agent": agent_results,
    }
    write_outputs(payload, raw_table, agent_table, summary_table)


if __name__ == "__main__":
    main()
