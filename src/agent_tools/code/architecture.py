"""code.architecture: Analyze code architecture and dependency structure."""
from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["architecture"]


# Layer ordering for clean architecture (inner to outer)
# Imports should only go from outer layers to inner layers
LAYER_ORDER = {
    "domain": 0,      # Entities, core business logic
    "entities": 0,
    "core": 0,
    "application": 1,  # Use cases, services
    "services": 1,
    "usecases": 1,
    "use_cases": 1,
    "interface": 2,    # Controllers, presenters
    "interfaces": 2,
    "adapters": 2,
    "controllers": 2,
    "presenters": 2,
    "infrastructure": 3,  # Frameworks, DB, external services
    "infra": 3,
    "db": 3,
    "database": 3,
    "external": 3,
    "frameworks": 3,
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

    def __init__(self):
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            # Get the top-level module name
            module = alias.name.split(".")[0]
            self.imports.add(module)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module:
            # For "from x.y import z", get "x"
            module = node.module.split(".")[0]
            self.imports.add(module)
        elif node.level > 0:
            # Relative import - mark as relative
            self.imports.add(f"__relative_{node.level}__")


def _get_layer(path: Path) -> int | None:
    """Determine the architecture layer from the path."""
    for part in path.parts:
        part_lower = part.lower()
        if part_lower in LAYER_ORDER:
            return LAYER_ORDER[part_lower]
    return None


def _analyze_file(file_path: Path, base_path: Path) -> ModuleInfo | None:
    """Analyze a single Python file for imports."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return None

    visitor = ImportVisitor()
    visitor.visit(tree)

    # Compute relative path for module name
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
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def _find_layer_violations(
    modules: dict[str, ModuleInfo], local_modules: set[str]
) -> list[tuple[str, str, int, int]]:
    """Find imports that violate layer boundaries.

    Returns list of (importing_module, imported_module, from_layer, to_layer)
    where from_layer < to_layer (inner importing from outer).
    """
    violations = []

    for module_name, info in modules.items():
        if info.layer is None:
            continue

        for imported in info.imports:
            # Only check local modules
            if imported not in local_modules:
                continue

            imported_info = modules.get(imported)
            if imported_info is None or imported_info.layer is None:
                continue

            # Violation: inner layer importing from outer layer
            if info.layer < imported_info.layer:
                violations.append((
                    module_name,
                    imported,
                    info.layer,
                    imported_info.layer,
                ))

    return violations


def _layer_name(layer_num: int) -> str:
    """Get a human-readable name for a layer number."""
    names = {
        0: "domain/core",
        1: "application/services",
        2: "interface/adapters",
        3: "infrastructure",
    }
    return names.get(layer_num, f"layer {layer_num}")


def architecture(path: str) -> str:
    """
    Analyze code architecture and dependency structure.

    Args:
        path: Directory or file to analyze

    Returns:
        Dependency report with circular dependencies and layer violations.
    """
    target = Path(path)

    if not target.exists():
        return f"Error: Path not found: {path}"

    # Collect all Python files
    if target.is_file():
        py_files = [target] if target.suffix == ".py" else []
        base_path = target.parent
    else:
        py_files = list(target.rglob("*.py"))
        py_files = [
            f for f in py_files
            if "__pycache__" not in str(f)
            and not any(p.startswith(".") for p in f.parts)
        ]
        base_path = target

    if not py_files:
        return f"No Python files found in {path}"

    # Analyze all files
    modules: dict[str, ModuleInfo] = {}
    for py_file in py_files:
        info = _analyze_file(py_file, base_path)
        if info:
            # Use stem for simple matching
            modules[py_file.stem] = info

    # Build local module set for filtering
    local_modules = set(modules.keys())

    # Build dependency graph (only local dependencies)
    dep_graph: dict[str, set[str]] = defaultdict(set)
    for module_name, info in modules.items():
        for imported in info.imports:
            if imported in local_modules and imported != module_name:
                dep_graph[module_name].add(imported)

    file_count = len(py_files)
    lines = [
        f"# Architecture Analysis: {path}",
        "",
        f"Analyzed {file_count} file{'s' if file_count != 1 else ''}.",
        "",
    ]

    issues_found = False

    # Find circular dependencies
    cycles = _find_cycles(dict(dep_graph))
    if cycles:
        issues_found = True
        lines.append("## Circular Dependencies")
        lines.append("")
        lines.append("The following circular dependencies were detected:")
        lines.append("")

        # Deduplicate cycles (same cycle can be found from different starting points)
        seen_cycles = set()
        for cycle in cycles:
            # Normalize cycle for comparison
            cycle_set = frozenset(cycle[:-1])  # Exclude repeated last element
            if cycle_set not in seen_cycles and len(cycle_set) > 1:
                seen_cycles.add(cycle_set)
                cycle_str = " → ".join(cycle)
                lines.append(f"- {cycle_str}")

        lines.append("")
        lines.append("**Recommendation**: Break cycles by introducing interfaces or")
        lines.append("moving shared code to a separate module.")
        lines.append("")

    # Find layer violations
    violations = _find_layer_violations(modules, local_modules)
    if violations:
        issues_found = True
        lines.append("## Layer Violations")
        lines.append("")
        lines.append("Inner layers should not depend on outer layers:")
        lines.append("")

        for importing, imported, from_layer, to_layer in violations:
            lines.append(
                f"- `{importing}` ({_layer_name(from_layer)}) imports "
                f"`{imported}` ({_layer_name(to_layer)})"
            )

        lines.append("")
        lines.append("**Recommendation**: Use dependency inversion - define interfaces")
        lines.append("in inner layers, implement in outer layers.")
        lines.append("")

    # Show dependency summary
    lines.append("## Dependency Graph")
    lines.append("")

    if dep_graph:
        for module_name in sorted(dep_graph.keys()):
            deps = sorted(dep_graph[module_name])
            if deps:
                dep_str = ", ".join(f"`{d}`" for d in deps)
                lines.append(f"- `{module_name}` → {dep_str}")
    else:
        lines.append("No internal dependencies between modules.")

    lines.append("")

    if not issues_found:
        lines.append("## Summary")
        lines.append("")
        lines.append("No circular dependencies or layer violations found.")

    return "\n".join(lines)

