# Contributing to agent-tools

## Development Setup

```bash
git clone https://github.com/amp-rh/agent-tools.git
cd agent-tools
uv sync              # Install dependencies
uv run pytest        # Verify tests pass
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
uv run ruff check .          # Lint
uv run ruff check --fix .    # Auto-fix issues
uv run ruff format .         # Format code
```

### Style Guidelines

- **Keep it simple**: Avoid over-engineering. Only make changes that are directly necessary.
- **Reduce, don't add**: Changes that reduce codebase size are preferable.
- **No speculative features**: Don't add error handling or validation for scenarios that can't happen.
- **DRY**: Reuse existing abstractions. Don't create helpers for one-time operations.

## Testing

All changes require tests. We encourage **Test-Driven Development (TDD)**.

### TDD Workflow

```
1. Write a failing test first
2. Write minimal code to make it pass
3. Refactor while keeping tests green
4. Repeat
```

**Why TDD for tools?**
- Forces you to think about the interface before implementation
- Tests serve as executable documentation
- Catches edge cases early
- Makes refactoring safe

### Example TDD Session

```python
# 1. Write the test first (tests/test_mytools/test_greet.py)
def test_greet_returns_greeting():
    result = greet("Alice")
    assert result == "Hello, Alice!"

def test_greet_handles_empty_name():
    result = greet("")
    assert "Hello" in result

# 2. Run tests - they fail (good!)
# uv run pytest tests/test_mytools/test_greet.py

# 3. Implement just enough to pass
def greet(name: str) -> str:
    return f"Hello, {name or 'stranger'}!"

# 4. Run tests - they pass
# 5. Refactor if needed, tests stay green
```

### Running Tests

```bash
uv run pytest                    # All tests
uv run pytest tests/test_X.py    # Specific test file
uv run pytest -v --tb=short      # Verbose with short tracebacks
uv run pytest -x                 # Stop on first failure
uv run pytest --lf               # Run last failed tests
```

### Test Structure

Tests mirror the source structure:
```
src/agent_tools/namespace/tool_name.py
tests/test_namespace/test_tool_name.py
```

## Branching

**Always create a new branch for changes.** Never commit directly to `main` or `dev`.

### Branch Naming Convention

```
<type>/<namespace>-<description>
```

| Type | Use For | Example |
|------|---------|---------|
| `tool/` | New tools | `tool/github-list-issues` |
| `feat/` | Features (non-tool) | `feat/mcp-resources` |
| `fix/` | Bug fixes | `fix/reload-cache-clear` |
| `refactor/` | Code improvements | `refactor/registry-structure` |
| `docs/` | Documentation | `docs/contribution-guide` |

### Examples

```bash
# Adding a new tool
git checkout -b tool/jira-create-issue

# Adding a feature
git checkout -b feat/observe-tracing

# Fixing a bug
git checkout -b fix/server-startup

# Refactoring
git checkout -b refactor/duplicate-removal
```

## Adding Tools

**Each new tool should be in its own branch** using the `tool/<namespace>-<tool-name>` convention.

### Workflow

```bash
# 1. Create branch
git checkout dev
git pull origin dev
git checkout -b tool/mytools-greet

# 2. Create tool via registry
registry.add(
  name="mytools.greet",
  description="What it does",
  parameters='[{"name": "param", "type": "string", "required": true}]'
)

# 3. Implement, test, commit
# ... edit src/agent_tools/mytools/greet.py ...
uv run pytest tests/test_mytools/test_greet.py
git add -A
git commit -m "feat(mytools): add greet tool"

# 4. Push and create PR
git push origin tool/mytools-greet
gh pr create --base dev
```

### What Gets Created

```
registry.add(name="namespace.tool-name", ...)
```

Creates:
- `tool_defs/namespace/tool-name.yaml` - Definition
- `src/agent_tools/namespace/tool_name.py` - Implementation stub
- `tests/test_namespace/test_tool_name.py` - Test stub

Then (using TDD):
1. **Write tests first** in `tests/test_namespace/test_tool_name.py`
2. Run tests - verify they fail (stub raises `NotImplementedError`)
3. **Implement** the function to make tests pass
4. Refactor if needed, keeping tests green
5. Run `uv run pytest tests/test_namespace/test_tool_name.py`

## Tool Aliases & Workflows

### Namespace Aliases

It's acceptable to expose the same tool under multiple namespace combinations for discoverability. An agent thinking "debug this" vs "observe this" should find relevant tools either way.

**Use symlinks to avoid code duplication:**

```bash
# Primary location
tool_defs/observe/session.yaml
src/agent_tools/observe/session.py

# Alias via symlinks
cd tool_defs/debug && ln -s ../observe/session.yaml session.yaml
cd src/agent_tools/debug && ln -s ../observe/session.py session.py
```

**Rules:**
- Primary location has the actual files
- Aliases are relative symlinks pointing to primary
- Tests only exist for the primary location
- Both names work identically at runtime

### Workflow References

Use Cursor `@` document links in tool descriptions to reference related tools that chain well together:

```yaml
# In tool_defs/code/refactor.yaml
description: |
  Refactor code using structured patterns.
  
  Often used with @tool_defs/code/lint.yaml to verify changes
  and @tool_defs/think/about.yaml for complex decisions.
```

This helps agents discover tool combinations without hardcoding workflows.

**When to add references:**
- Tools that are commonly used in sequence
- Tools that provide complementary functionality
- Tools that validate or extend each other's output

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `docs`: Documentation only
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(registry): add reload tool for hot-reloading
fix(server): handle missing tool gracefully
refactor: remove duplicate _load_registry wrappers
docs: update README with new tools
```

## Pull Requests

1. **Branch from `dev`**: Create feature branches from `dev`, not `main`
2. **Use naming convention**: See [Branching](#branching) section
3. **Keep focused**: One tool/feature/fix per PR
4. **Tests required**: All new code needs tests
5. **Update docs**: If adding features, update relevant docs
6. **Pass CI**: All tests must pass

### PR Checklist

- [ ] Branch follows naming convention (`tool/`, `feat/`, `fix/`, etc.)
- [ ] Tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Docs updated if needed
- [ ] Commit messages follow convention

## Architecture Notes

### MCP Primitives

The server exposes three MCP primitive types:

| Type | Purpose | Location |
|------|---------|----------|
| Tools | Callable functions | `tool_defs/`, `src/agent_tools/` |
| Prompts | Reusable text templates | `server.py` (`_list_prompts`, `_get_prompt`) |
| Resources | Read-only data | `server.py` (`_list_resources`, `_read_resource`) |

### Local vs External Tools

- **Local tools**: Python modules in `src/agent_tools/`, cached in `sys.modules`
- **External tools**: Proxied from other MCP servers via `mcp.connect`

Use `registry.reload` to clear local module cache after code changes.

### Entry Point Tools

Only these tools are directly exposed via MCP (others require `registry.execute`):
- `agent.start-here`
- `registry.execute`
- `registry.reload`
- `observe.log`, `observe.trace-call`, `observe.session`

## The `.cursor/` Directory

The `.cursor/` directory is **gitignored** and used as a local scratchpad:
- Agent notes, todos, learnings
- Investigation logs and discoveries
- Temporary data and experiments

**Do not commit anything from `.cursor/`** - it's for local working memory only.

If you find valuable patterns or learnings, move them to proper docs before they're lost.

## Questions?

Open an issue or check existing docs:
- `AGENTS.md` - Agent-focused project overview  
- `docs/discovery-problem.md` - Analysis of agent tool discovery

