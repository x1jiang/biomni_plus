"""
Biomni Tool Adapter for ClawAgents Engine.
Dynamically bridges Biomni 180+ domain tools into ClawAgents Tool protocol.
"""

import asyncio
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure biomni is in sys.path
biomni_root = Path(__file__).resolve().parent.parent / "biomni"
if str(biomni_root) not in sys.path:
    sys.path.insert(0, str(biomni_root))

from clawagents.tools.registry import ToolResult, Tool, format_tool_error


def _map_param_type(t: str) -> str:
    t_lower = str(t).lower()
    if "int" in t_lower:
        return "integer"
    elif "float" in t_lower or "number" in t_lower:
        return "number"
    elif "bool" in t_lower:
        return "boolean"
    elif "list" in t_lower or "array" in t_lower:
        return "array"
    elif "dict" in t_lower or "object" in t_lower:
        return "object"
    return "string"


class BiomniTool:
    """ClawAgents-compatible Tool wrapping a Biomni domain function."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Dict[str, Any]],
        func: Callable,
        module_name: str,
        keywords: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self._func = func
        self.module_name = module_name
        self.keywords = keywords or [module_name, name]
        self.cacheable = False

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            loop = asyncio.get_running_loop()
            
            # Execute synchronously in worker thread to prevent event loop blocking
            if inspect.iscoroutinefunction(self._func):
                res = await self._func(**args)
            else:
                res = await loop.run_in_executor(None, lambda: self._func(**args))
            
            # Format output
            if isinstance(res, (dict, list)):
                output_str = json.dumps(res, indent=2, default=str)
            else:
                output_str = str(res)

            return ToolResult(success=True, output=output_str)
        except Exception as e:
            err_msg = format_tool_error(e)
            return ToolResult(success=False, output="", error=f"Biomni Tool Error in {self.name}: {err_msg}")


def get_biomni_claw_tools(
    modules: Optional[List[str]] = None,
    exclude_modules: Optional[List[str]] = None,
) -> List[Tool]:
    """
    Load and return Biomni tools wrapped as ClawAgents Tools.
    
    Args:
        modules: Specific module names to include (e.g. ['database', 'genomics', 'pharmacology', 'literature'])
        exclude_modules: Module names to exclude
    """
    from biomni.utils import read_module2api

    module2api = read_module2api()
    tools: List[Tool] = []
    
    selected_modules = modules or list(module2api.keys())

    for mod_path, api_list in module2api.items():
        mod_short = mod_path.replace("biomni.tool.", "")
        if modules and mod_short not in modules and mod_path not in modules:
            continue
        if exclude_modules and (mod_short in exclude_modules or mod_path in exclude_modules):
            continue

        # Try to import the actual implementation module
        try:
            impl_mod = importlib.import_module(mod_path)
        except Exception as e:
            # If optional bio dependency is missing, log and skip gracefully
            continue

        for api_desc in api_list:
            func_name = api_desc.get("name")
            if not func_name or not hasattr(impl_mod, func_name):
                continue
            
            func = getattr(impl_mod, func_name)
            doc = api_desc.get("description", "")
            
            params: Dict[str, Dict[str, Any]] = {}
            for req in api_desc.get("required_parameters", []):
                pname = req.get("name")
                if pname:
                    params[pname] = {
                        "type": _map_param_type(req.get("type", "str")),
                        "description": req.get("description", ""),
                        "required": True,
                    }
            for opt in api_desc.get("optional_parameters", []):
                pname = opt.get("name")
                if pname:
                    params[pname] = {
                        "type": _map_param_type(opt.get("type", "str")),
                        "description": opt.get("description", ""),
                        "required": False,
                    }

            biomni_tool = BiomniTool(
                name=func_name,
                description=doc,
                parameters=params,
                func=func,
                module_name=mod_short,
                keywords=[mod_short, func_name.replace("_", " ")],
            )
            tools.append(biomni_tool)

    return tools
