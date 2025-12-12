"""code.architecture: Analyze code architecture and dependency structure."""
from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from agent_tools.code._formatters import format_header, format_section
from agent_tools.code._parsers import collect_py_files, parse_file

__all__ = ["architecture"]

# Layer ordering for clean architecture (inner to outer)
LAYER_ORDER = {
    "domain": 0, "entities": 0, "core": 0,
    "application": 1, "services": 1, "usecases": 1, "use_cases": 1,
    "interface": 2, "interfaces": 2, "adapters": 2, "controllers": 2, "presenters": 2,
    "infrastructure": 3, "infra": 3, "db": 3, "database": 3, "external": 3, "frameworks": 3,
}


@dataclass
class ModuleInfo:
    """Information about a Python module."""

    name: str
    path: Path
    imports: set[str] = field(default_factory=set)
    layer: int | None = None


class ImportVisitor(ast.NodeVisitor):
    """AST visitor that extracts import statements."""

    def __init__(self) -> None:
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            module = alias.name.split(".")[0]
            self.imports.add(module)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module:
            module = node.module.split(".")[0]
            self.imports.add(module)
        elif node.level > 0:
            self.imports.add(f"__relative_{node.level}__")


def _get_layer(path: Path) -> int | None:
    """Determine the architecture layer from the path."""
    for part in path.parts:
        if part.lower() in LAYER_ORDER:
            return LAYER_ORDER[part.lower()]
    return None


def _analyze_file(file_path: Path, base_path: Path) -> ModuleInfo | None:
    """Analyze a single Python file for imports."""
    tree = parse_file(file_path)
    if tree is None:
        return None

    visitor = ImportVisitor()
    visitor.visit(tree)

    try:
        rel_path = file_path.relative_to(base_path)
        module_name = str(rel_path.with_suffix("")).replace("/", ".")
    except ValueError:
        module_name = file_path.stem

    return ModuleInfo(
        name=module_name,
        path=file_path,
        imports=visitor.imports,
        layer=_get_layer(file_path),
    )


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all cycles in a directed graph using DFS."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def _find_layer_violations(
    modules: dict[str, ModuleInfo], local_modules: set[str]
) -> list[tuple[str, str, int, int]]:
    """Find imports that violate layer boundaries."""
    violations = []

    for module_name, info in modules.items():
        if info.layer is None:
            continue

        for imported in info.imports:
            if imported not in local_modules:
                continue

            imported_info = modules.get(imported)
            if imported_info is None or imported_info.layer is None:
                continue

            if info.layer < imported_info.layer:
                violations.append((module_name, imported, info.layer, imported_info.layer))

    return violations


def _layer_name(layer_num: int) -> str:
    """Get a human-readable name for a layer number."""
    names = {0: "domain/core", 1: "application/services", 2: "interface/adapters", 3: "infrastructure"}
    return names.get(layer_num, f"layer {layer_num}")


def _build_dependency_graph(
    modules: dict[str, ModuleInfo], local_modules: set[str]
) -> dict[str, set[str]]:
    """Build dependency graph from modules, filtering to local deps only."""
    graph: dict[str, set[str]] = defaultdict(set)
    for module_name, info in modules.items():
        for imported in info.imports:
            if imported in local_modules and imported != module_name:
                graph[module_name].add(imported)
    return dict(graph)


def _format_cycles(cycles: list[list[str]]) -> list[str]:
    """Format cycle information as markdown lines."""
    lines = ["The following circular dependencies were detected:", ""]

    seen_cycles: set[frozenset[str]] = set()
    for cycle in cycles:
        cycle_set = frozenset(cycle[:-1])
        if cycle_set not in seen_cycles and len(cycle_set) > 1:
            seen_cycles.add(cycle_set)
            lines.append(f"- {' → '.join(cycle)}")

    lines.extend([
        "",
        "**Recommendation**: Break cycles by introducing interfaces or",
        "moving shared code to a separate module.",
        "",
    ])
    return lines


def _format_violations(violations: list[tuple[str, str, int, int]]) -> list[str]:
    """Format layer violation information as markdown lines."""
    lines = ["Inner layers should not depend on outer layers:", ""]

    for importing, imported, from_layer, to_layer in violations:
        lines.append(
            f"- `{importing}` ({_layer_name(from_layer)}) imports "
            f"`{imported}` ({_layer_name(to_layer)})"
        )

    lines.extend([
        "",
        "**Recommendation**: Use dependency inversion - define interfaces",
        "in inner layers, implement in outer layers.",
        "",
    ])
    return lines


def _format_dependency_graph(graph: dict[str, set[str]]) -> list[str]:
    """Format dependency graph as markdown lines."""
    if not graph:
        return ["No internal dependencies between modules."]

    lines = []
    for module_name in sorted(graph.keys()):
        deps = sorted(graph[module_name])
        if deps:
            dep_str = ", ".join(f"`{d}`" for d in deps)
            lines.append(f"- `{module_name}` → {dep_str}")

    return lines


def architecture(path: str) -> str:
    """Analyze code architecture and dependency structure.

    Args:
        path: Directory or file to analyze

    Returns:
        Dependency report with circular dependencies and layer violations.
    """
    target = Path(path)

    if not target.exists():
        return f"Error: Path not found: {path}"

    py_files = collect_py_files(target)

    if not py_files:
        return f"No Python files found in {path}"

    base_path = target.parent if target.is_file() else target

    # Analyze all files
    modules: dict[str, ModuleInfo] = {}
    for py_file in py_files:
        info = _analyze_file(py_file, base_path)
        if info:
            modules[py_file.stem] = info

    local_modules = set(modules.keys())
    dep_graph = _build_dependency_graph(modules, local_modules)

    lines = [format_header("Architecture Analysis", path, len(py_files))]
    issues_found = False

    # Find and report circular dependencies
    cycles = _find_cycles(dep_graph)
    if cycles:
        issues_found = True
        lines.append(format_section("Circular Dependencies", _format_cycles(cycles)))

    # Find and report layer violations
    violations = _find_layer_violations(modules, local_modules)
    if violations:
        issues_found = True
        lines.append(format_section("Layer Violations", _format_violations(violations)))

    # Show dependency graph
    lines.append(format_section("Dependency Graph", _format_dependency_graph(dep_graph)))

    if not issues_found:
        lines.append("## Summary")
        lines.append("")
        lines.append("No circular dependencies or layer violations found.")

    return "\n".join(lines)
