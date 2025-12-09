"""think.about: Pause and think deeply about a problem before acting."""
from __future__ import annotations

__all__ = ["about"]


def about(problem: str) -> str:
    """
    Pause and think deeply about a problem before acting.

    Args:
        problem: The problem or situation to think through

    Returns:
        Structured thinking prompts to guide analysis.
    """
    return f"""## Thinking About: {problem}

### 1. Clarify the Problem
- What exactly is being asked?
- What would "solved" look like?
- Who cares about this and why?

### 2. What Do I Know?
- What facts do I have?
- What have I verified vs assumed?
- What's missing that I need to find out?

### 3. What Are the Options?
- What approaches could work?
- What's the simplest thing that might work?
- What would an expert do differently?

### 4. What Could Go Wrong?
- What assumptions might be wrong?
- What edge cases exist?
- What's the worst case if I'm wrong?

### 5. Next Step
Based on the above, what is the ONE next action?

---
*Take time with each section. The goal is clarity, not speed.*
"""
