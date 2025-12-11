"""registry tools."""
from __future__ import annotations

# Re-export everything from _base (the original registry module)
from agent_tools.registry._base import (
    CommandGenerator,
    StubGenerator,
    ToolManager,
    ValidationResult,
    _get_manager,
    _reset_manager,
    add_tool,
    execute_tool,
    generate_commands,
    list_tools,
    remove_tool,
    update_tool,
    validate_registry,
)

# Also export reload
from agent_tools.registry.reload import reload

__all__ = [
    "CommandGenerator",
    "StubGenerator",
    "ToolManager",
    "ValidationResult",
    "add_tool",
    "execute_tool",
    "generate_commands",
    "list_tools",
    "reload",
    "remove_tool",
    "update_tool",
    "validate_registry",
]
