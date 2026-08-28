"""
Biomni-Plus: High-Performance Biomedical AI Agent with ClawAgents Backbone
"""

from biomni_plus.agent import create_biomni_plus_agent, BiomniPlusAgent
from biomni_plus.tools_adapter import get_biomni_claw_tools

__version__ = "0.1.0"
__all__ = ["create_biomni_plus_agent", "BiomniPlusAgent", "get_biomni_claw_tools"]
