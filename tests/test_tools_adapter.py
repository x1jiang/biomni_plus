"""
Tests for Biomni-Plus tools adapter.
"""

from biomni_plus.tools_adapter import get_biomni_claw_tools

def test_load_database_tools():
    tools = get_biomni_claw_tools(modules=["database"])
    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "query_uniprot" in tool_names or "query_pdb" in tool_names

def test_tool_schema_mapping():
    tools = get_biomni_claw_tools(modules=["database"])
    for t in tools:
        assert hasattr(t, "name")
        assert hasattr(t, "description")
        assert hasattr(t, "parameters")
        assert hasattr(t, "execute")
        assert isinstance(t.parameters, dict)
