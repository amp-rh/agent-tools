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

All changes require tests. Run the full suite before submitting:

```bash
uv run pytest                    # All tests
uv run pytest tests/test_X.py    # Specific test file
uv run pytest -v --tb=short      # Verbose with short tracebacks
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

Then:
1. Implement the function (replace `raise NotImplementedError`)
2. Write tests
3. Run `uv run pytest tests/test_namespace/test_tool_name.py`

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

