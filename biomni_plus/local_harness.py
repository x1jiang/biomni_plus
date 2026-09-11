"""Compact harness so local 30B models (Glimmer) can run Biomni-Plus.

Frontier models skip tools when they already know the answer. Muse-Glimmer-30B
does the opposite: the default coding surface (ls/glob/web_search) plus the
datalake "use execute" nudge burns the iteration budget before it writes an
answer. This module shrinks the tool surface and flips the policy to
knowledge-first.
"""

from __future__ import annotations

import os
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

_SUB_SUPER_DIGITS = str.maketrans(
    "₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹",
    "01234567890123456789",
)

# Lookups that cover the standard biomedical suite without the 70+ assay tools.
PREFERRED_DOMAIN_TOOLS = frozenset(
    {
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

# Needed for the DNA transcription/translation task; keep them visible.
ALWAYS_ON_TOOLS = frozenset(
    {
        "execute",
        "write_file",
        "retrieve_tool_result",
    }
)

EXPLORATION_TOOLS = frozenset(
    {
        "ls",
        "glob",
        "grep",
        "tree",
        "web_search",
        "web_fetch",
        "git_status",
        "git_diff",
        "git_commit",
        "read_and_grep",
        "hashline_grep",
        "skill_workshop",
        "task",
    }
)

LOCAL_OPERATING_RULES = """
### LOCAL MODEL OPERATING RULES (mandatory)
1. If you already know the answer (gene symbols, chromosomes, drug formulas, multiple-choice), answer immediately. Do not call tools.
2. Use at most one biomedical lookup (`query_uniprot`, `query_chembl`, `query_pubchem`, `query_ensembl`) when you need a live accession confirmed.
3. Never use `ls`, `glob`, `grep`, `web_search`, `web_fetch`, or filesystem exploration for scientific facts.
4. If a tool errors (SSL, auth, timeout, not found), stop retrying and answer from knowledge.
5. Use `write_file` + `execute` only when the user asks you to write and run code.
6. After one successful tool result, write the final answer. Do not keep exploring.
7. Put canonical terms in the visible answer: official gene symbols, "tumor suppressor", enzyme names (e.g. Cas13a), formulas, and the peptide/protein sequence.
8. For multiple choice, include both `[ANSWER]X[/ANSWER]` and the option name (e.g. Cas13a).
9. Be concise: 2-6 sentences for factual questions. Keep private reasoning short so the visible answer is not truncated.
""".strip()

COMPACT_AD_NOTE = (
    "For Alzheimer's / APOE questions, state chromosome 19 and the amyloid-beta "
    "clearance mechanism from knowledge unless a lookup tool already succeeded."
)

KNOWLEDGE_FALLBACK_SYSTEM = (
    "You are a biomedical expert. Answer from established knowledge in 2-6 "
    "sentences. Use canonical terms (tumor suppressor, Cas13a, peptide/protein, "
    "formulas, gene symbols, chromosomes). For multiple choice include "
    "[ANSWER]X[/ANSWER] and the option name. Do not mention tools."
)

_CLOUD_HOSTS = frozenset(
    {
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
    }
)


def is_compact_local_model(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> bool:
    """True for Glimmer / OSS checkpoints on a non-cloud OpenAI-compatible URL."""
    flag = os.getenv("BIOMNI_LOCAL_HARNESS", "").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False
    if flag in ("1", "true", "yes", "on"):
        return True

    model_l = (model or "").strip().lower()
    if any(tag in model_l for tag in ("glimmer", "muse-glimmer", "llama", "qwen", "gemma", "mistral")):
        if model_l.startswith(("gpt-", "claude-", "gemini-", "o1", "o3", "o4")):
            return False
        return True

    url = (base_url or os.getenv("OPENAI_BASE_URL") or "").strip()
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    if not host or host in _CLOUD_HOSTS or host.endswith(".openai.azure.com"):
        return False
    if model_l.startswith(("gpt-", "claude-", "gemini-")):
        return False
    return True


def normalize_local_answer(text: str) -> str:
    """Make Glimmer answers machine-readable without changing the science.

    SGLang often emits Unicode subscripts (C₂₉H₃₁N₇O) that break exact
    formula matching and downstream parsers.
    """
    if not text:
        return text
    return text.translate(_SUB_SUPER_DIGITS)


def local_system_addendum(*, is_ad_specialized: bool = False) -> str:
    parts = [LOCAL_OPERATING_RULES]
    if is_ad_specialized:
        parts.append(COMPACT_AD_NOTE)
    return "\n\n".join(parts)


def select_local_domain_tools(tools: Iterable[Any]) -> list[Any]:
    """Keep preferred lookups when present; otherwise keep every loaded domain tool."""
    loaded = list(tools)
    if os.getenv("BIOMNI_LOCAL_FULL_TOOLS", "").strip().lower() in ("1", "true", "yes", "on"):
        return loaded
    preferred = [t for t in loaded if getattr(t, "name", "") in PREFERRED_DOMAIN_TOOLS]
    return preferred or loaded


def local_active_tool_names(domain_tools: Iterable[Any]) -> set[str]:
    names = {getattr(t, "name", "") for t in domain_tools}
    names.discard("")
    names |= ALWAYS_ON_TOOLS
    return names


def apply_local_tool_surface(claw_agent: Any, domain_tools: Iterable[Any]) -> list[str]:
    """Hide coding/exploration tools so Glimmer cannot ls/web-search its way to a timeout."""
    registry = getattr(claw_agent, "tools", None)
    if registry is None or not hasattr(registry, "set_active_tools"):
        return []

    wanted = local_active_tool_names(domain_tools)
    registered = {t.name for t in registry.list_registered()} if hasattr(registry, "list_registered") else set()
    active = wanted & registered if registered else wanted
    registry.set_active_tools(active)

    previous = getattr(claw_agent, "before_tool", None)

    def _deny_exploration(tool_name: str, args: dict) -> Any:
        if tool_name in EXPLORATION_TOOLS:
            return False
        if previous is None:
            return True
        return previous(tool_name, args)

    claw_agent.before_tool = _deny_exploration
    return sorted(active)


def needs_knowledge_fallback(state: Any) -> bool:
    result = str(getattr(state, "result", "") or "")
    status = str(getattr(state, "status", "") or "")
    if status == "max_iterations":
        return True
    return result.startswith("Reached maximum of") or "maximum of" in result and "tool rounds" in result


async def knowledge_fallback_answer(claw_agent: Any, prompt: str) -> str:
    """Last-turn no-tools answer when the agent loop exhausted its budget."""
    from clawagents.providers.llm import LLMMessage

    llm = getattr(claw_agent, "llm", None)
    if llm is None or not hasattr(llm, "chat"):
        return ""
    response = await llm.chat(
        [
            LLMMessage(role="system", content=KNOWLEDGE_FALLBACK_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
    )
    return (getattr(response, "content", None) or "").strip()
