"""
Template for generated tool stubs.

This file is NOT a tool - it's a reference for how stubs are generated.
The STUB_TEMPLATE constant is used by registry.add to create new tools.
"""

STUB_TEMPLATE = '''\
"""{namespace}.{tool_name}: {short_description}"""
from __future__ import annotations

__all__ = ["{function_name}"]


def {function_name}({typed_params}) -> str:
    """
    {description}

    Args:
{param_docs}

    Returns:
        Result message describing what was done.
    """
    # === IMPLEMENT BELOW ===

    raise NotImplementedError("{namespace}.{tool_name} not implemented")
'''

TEST_TEMPLATE = '''\
"""{namespace}.{tool_name} tests."""
import pytest

from agent_tools.{namespace}.{module_name} import {function_name}


class Test{class_name}:
    """Tests for {function_name}."""

    def test_{function_name}_not_implemented(self):
        """Verify stub raises NotImplementedError until implemented."""
        with pytest.raises(NotImplementedError):
            {function_name}({test_args})

    # === ADD YOUR TESTS BELOW ===
'''

INIT_TEMPLATE = '''\
"""{namespace} tools."""
from __future__ import annotations
'''

COMMAND_TEMPLATE = '''\
# {title}

{description}

## Parameters

{parameters}

## Usage

Use the `{tool_name}` MCP tool.{example}
'''
