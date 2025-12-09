# The Agent Discovery Problem

## Problem Statement

Agents don't naturally explore available tools before attempting tasks. They're task-focused: receive request → attempt solution. They don't think "let me see what tools exist first."

## What We Tried

### 1. Tool Description ("Use this to see capabilities")

```yaml
registry.list:
  description: "List all tools... Use this to see what capabilities are available."
```

**Result**: Agent didn't call it. Description is only read if agent already considers calling the tool.

### 2. MCP Prompt (Assistant role as "thought")

```python
WORKFLOW_PROMPT = """I should check what tools are available before attempting this task..."""
```

**Result**: Prompts aren't auto-injected. Client must explicitly request them. Never triggered.

### 3. Start-Here Tool ("ALWAYS call this first")

```yaml
agent.start-here:
  description: "ALWAYS call this first before attempting any task..."
```

**Result**: Better signal, but still not called mid-session. Agent already "in flow."

## Key Insights

### Agent Psychology

| Behavior | Implication |
|----------|-------------|
| Task-focused | Jumps to solving, not exploring |
| Description-blind | Only reads descriptions for tools it's considering |
| Session-contextual | Mid-session agents won't "reset" to check tools |
| Instruction-following | Responds to explicit commands, not suggestions |

### What "ALWAYS" Means

- In a **tool description**: A suggestion the agent may not read
- In a **system prompt**: An instruction the agent follows
- In **training**: Baked-in behavior

### When Discovery Might Work

| Scenario | Likelihood |
|----------|------------|
| Fresh session, no task yet | Higher |
| Agent explicitly told "use agent-tools" | Higher |
| Mid-task, focused on user request | Lower |
| Complex multi-step task | Lower (already planning) |

## Recommendations

### For Tool Authors

1. **Name tools clearly**: `start-here` > `list` for discovery
2. **Lead with imperatives**: "ALWAYS call this first..." not "Use this to..."
3. **Don't rely on descriptions alone**: They're suggestions, not instructions

### For System Integrators

1. **Auto-inject prompts**: Client should inject workflow prompt at session start
2. **System instructions**: Add "Always call agent-start-here first" to system prompt
3. **Onboarding flow**: First message could be pre-filled with tool check

### For Agent Training

The real solution is training-level: agents should learn to explore capabilities before acting. Until then, we work around it.

## The Irony

We built a tool registry system to help agents create and use tools. The agent that built it never naturally used the discovery mechanism it created.

This isn't a failure—it's data. The discovery problem is real and requires multiple layers of mitigation, not just good descriptions.
