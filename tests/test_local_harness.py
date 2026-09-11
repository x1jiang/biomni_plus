"""Tests for the compact local-model (Glimmer) harness."""

from types import SimpleNamespace

from biomni_plus.local_harness import (
    ALWAYS_ON_TOOLS,
    EXPLORATION_TOOLS,
    apply_local_tool_surface,
    is_compact_local_model,
    local_active_tool_names,
    local_system_addendum,
    needs_knowledge_fallback,
    select_local_domain_tools,
)


def test_detects_glimmer_and_skips_luna():
    assert is_compact_local_model("Muse-Glimmer-30B", "http://xxx.xx.xx.xx/v1")
    assert is_compact_local_model("Muse-Glimmer-30B", None)
    assert not is_compact_local_model("gpt-5.6-luna", None)
    assert not is_compact_local_model("gpt-5.6-luna", "https://api.openai.com/v1")
    assert not is_compact_local_model("claude-opus-4", None)


def test_operating_rules_are_knowledge_first():
    text = local_system_addendum(is_ad_specialized=True)
    assert "answer immediately" in text.lower()
    assert "ls" in text
    assert "APOE" in text or "amyloid" in text
    assert "Cas13a" in text
    assert "tumor suppressor" in text


def test_select_local_domain_tools_prefers_lookups():
    tools = [
        SimpleNamespace(name="query_uniprot"),
        SimpleNamespace(name="analyze_western_blot"),
        SimpleNamespace(name="query_chembl"),
    ]
    selected = select_local_domain_tools(tools)
    assert [t.name for t in selected] == ["query_uniprot", "query_chembl"]


def test_select_local_domain_tools_keeps_all_if_no_preferred():
    tools = [SimpleNamespace(name="analyze_western_blot")]
    selected = select_local_domain_tools(tools)
    assert [t.name for t in selected] == ["analyze_western_blot"]


class _FakeRegistry:
    def __init__(self, names):
        self.tools = {n: SimpleNamespace(name=n) for n in names}
        self.active = None

    def list_registered(self):
        return list(self.tools.values())

    def set_active_tools(self, names):
        self.active = set(names)


def test_apply_local_tool_surface_hides_exploration():
    domain = [SimpleNamespace(name="query_uniprot"), SimpleNamespace(name="query_chembl")]
    registry = _FakeRegistry(
        [
            "query_uniprot",
            "query_chembl",
            "execute",
            "write_file",
            "retrieve_tool_result",
            "ls",
            "glob",
            "web_search",
            "analyze_western_blot",
        ]
    )
    agent = SimpleNamespace(tools=registry, before_tool=None)
    active = apply_local_tool_surface(agent, domain)
    assert "query_uniprot" in active
    assert "execute" in active
    assert "ls" not in active
    assert "web_search" not in active
    assert agent.before_tool("ls", {}) is False
    assert agent.before_tool("query_uniprot", {}) is True


def test_local_active_names_include_code_tools():
    names = local_active_tool_names([SimpleNamespace(name="query_uniprot")])
    assert ALWAYS_ON_TOOLS <= names
    assert not (EXPLORATION_TOOLS & names)


def test_needs_knowledge_fallback():
    assert needs_knowledge_fallback(SimpleNamespace(status="max_iterations", result="ok"))
    assert needs_knowledge_fallback(
        SimpleNamespace(status="done", result="Reached maximum of 15 tool rounds.")
    )
    assert not needs_knowledge_fallback(SimpleNamespace(status="done", result="TP53 is a tumor suppressor."))
