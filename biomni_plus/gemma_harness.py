"""Stricter Biomni loop for Gemma: hard caps, compact tools, no coding-delegation suffix."""

from __future__ import annotations

import re
from typing import Any, Iterable

from biomni_plus.gemma_tools import LAST_TOOL_CARDS, gemma_extra_tools
from biomni_plus.local_harness import EXPLORATION_TOOLS

GEMMA_MAX_ITERATIONS = 4
GEMMA_MAX_LOOKUPS = 1
GEMMA_MAX_CODE_RUNS = 2

GEMMA_LOOKUP_TOOLS = frozenset(
    {
        "lookup_compound",
        "query_uniprot",
        "query_ensembl",
        "query_clinvar",
        "query_chembl",
        "query_pubchem",
        "query_opentarget",
        "query_gwas_catalog",
        "query_kegg",
        "query_stringdb",
        "query_pdb",
        "query_alphafold",
        "calculate_physicochemical_properties",
    }
)
GEMMA_CODE_TOOLS = frozenset({"run_python", "execute", "write_file", "transcribe_translate"})
GEMMA_ACTIVE_TOOLS = frozenset(
    {
        "lookup_compound",
        "query_uniprot",
        "run_python",
        "transcribe_translate",
        "retrieve_tool_result",
    }
)

GEMMA_OPERATING_RULES = """
### GEMMA BIOMNI RULES (enforced)
1. Do not delegate, verify workers, or keep exploring. One pass, then the final answer.
2. Prefer `lookup_compound` for drugs (formula + MW). At most one lookup total.
3. For DNA transcription/translation use `transcribe_translate`. For other code use `run_python`. Do not write files.
4. After any successful tool result, write the final answer immediately.
5. Multiple choice: include both [ANSWER]X[/ANSWER] and the option name (e.g. Cas13a).
6. Put canonical tokens in the visible answer: gene symbols, "tumor suppressor", ASCII formulas (no subscripts), peptide/protein sequences.
""".strip()

_ANSWER_ONLY = re.compile(r"^\s*\[ANSWER\]([A-D])\[/ANSWER\]\s*$", re.I)
_OPTION = re.compile(r"(?:^|[\s,;])([A-D])\.\s+([A-Za-z0-9][^\n,;]*)")


def attach_gemma_tools(tools: Iterable[Any]) -> list[Any]:
    existing = {getattr(t, "name", "") for t in tools}
    merged = list(tools)
    for extra in gemma_extra_tools():
        if extra.name not in existing:
            merged.append(extra)
    return merged


def select_gemma_domain_tools(tools: Iterable[Any]) -> list[Any]:
    wanted = GEMMA_ACTIVE_TOOLS
    selected = [t for t in tools if getattr(t, "name", "") in wanted]
    return selected or list(tools)


def merge_tool_cards(answer: str) -> str:
    """Keep structured tool facts when the model rewrites them incorrectly."""
    text = str(answer or "")
    extras: list[str] = []
    compound = LAST_TOOL_CARDS.get("lookup_compound") or ""
    formula = re.search(r"formula:\s*([A-Za-z0-9]+)", compound)
    if formula and formula.group(1) not in text:
        extras.append(formula.group(1))
    weight = re.search(r"mw:\s*([0-9.]+)", compound)
    if weight and weight.group(1) not in text:
        extras.append(weight.group(1))
    tx = LAST_TOOL_CARDS.get("transcribe_translate") or ""
    if tx:
        for line in tx.splitlines():
            token = line.split(":", 1)[-1].strip()
            if token and token not in text:
                extras.append(line)
    if not extras:
        return text
    return text.rstrip() + "\n" + "\n".join(extras)


def close_multiple_choice(prompt: str, answer: str) -> str:
    """If the model emitted only [ANSWER]C[/ANSWER], append the option name from the prompt."""
    text = str(answer or "")
    match = _ANSWER_ONLY.match(text)
    if not match:
        return text
    letter = match.group(1).upper()
    options = {a.upper(): name.strip() for a, name in _OPTION.findall(prompt or "")}
    name = options.get(letter)
    if not name:
        return text
    return f"{text.strip()} {name}"


class GemmaLoopGuard:
    """Refuse a second lookup or a third code run. Prompt-only stop rules are ignored."""

    def __init__(self) -> None:
        self.successful_lookups = 0
        self.successful_code_runs = 0

    def before(self, tool_name: str, args: dict) -> Any:
        reason = ""
        if tool_name in EXPLORATION_TOOLS:
            reason = "Exploration tools are disabled. Answer now, or use lookup_compound / run_python."
        elif tool_name in GEMMA_LOOKUP_TOOLS and self.successful_lookups >= GEMMA_MAX_LOOKUPS:
            reason = "Lookup already used. Write the final answer from the previous result. Do not call another tool."
        elif tool_name in GEMMA_CODE_TOOLS and self.successful_code_runs >= GEMMA_MAX_CODE_RUNS:
            reason = "Code already ran. Write the final answer from stdout. Do not run more code."
        elif tool_name in {"query_pubchem", "query_chembl", "write_file", "execute"}:
            reason = "Use lookup_compound for drugs or run_python for code. Then answer."
        if reason:
            try:
                from clawagents.graph.agent_loop import HookResult

                return HookResult(allowed=False, reason=reason)
            except ImportError:
                return False
        # Reserve the slot when allowing so caps work even if after_tool is never called.
        if tool_name in GEMMA_LOOKUP_TOOLS:
            self.successful_lookups += 1
        if tool_name in GEMMA_CODE_TOOLS:
            self.successful_code_runs += 1
        return True

    def after(self, tool_name: str, args: dict, result: Any) -> Any:
        return result


def apply_gemma_tool_surface(claw_agent: Any, domain_tools: Iterable[Any]) -> list[str]:
    registry = getattr(claw_agent, "tools", None)
    wanted = {getattr(t, "name", "") for t in domain_tools}
    wanted.discard("")
    wanted |= GEMMA_ACTIVE_TOOLS
    if registry is not None and hasattr(registry, "set_active_tools"):
        registered = (
            {t.name for t in registry.list_registered()}
            if hasattr(registry, "list_registered")
            else set()
        )
        active = wanted & registered if registered else wanted
        registry.set_active_tools(active)
    else:
        active = wanted

    guard = GemmaLoopGuard()
    previous_after = getattr(claw_agent, "after_tool", None)

    def _before(tool_name: str, args: dict) -> Any:
        return guard.before(tool_name, args)

    def _after(tool_name: str, args: dict, result: Any) -> Any:
        if previous_after is not None:
            result = previous_after(tool_name, args, result)
        return guard.after(tool_name, args, result)

    if hasattr(claw_agent, "_convenience_gate_base"):
        from clawagents.modes import compose_before_tool

        base = claw_agent._convenience_gate_base()
        claw_agent.before_tool = compose_before_tool(_before, base)
    else:
        previous_before = getattr(claw_agent, "before_tool", None)

        def _before_chained(tool_name: str, args: dict) -> Any:
            gated = guard.before(tool_name, args)
            if gated is not True:
                return gated
            if previous_before is None:
                return True
            return previous_before(tool_name, args)

        claw_agent.before_tool = _before_chained
    claw_agent.after_tool = _after
    claw_agent._gemma_loop_guard = guard
    return sorted(active)


def bind_gemma_harness_profile(model: str) -> None:
    """Drop the coding-delegation suffix when this ClawAgents build supports aliases."""
    try:
        from clawagents.harness_profiles import register_harness_alias
    except ImportError:
        return
    register_harness_alias(model, "local-ollama")


def cap_gemma_iterations(requested: int) -> int:
    return max(1, min(int(requested), GEMMA_MAX_ITERATIONS))
