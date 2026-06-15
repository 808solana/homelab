"""Rules-based router.

This is v1 of Love's routing intelligence: cheap, deterministic keyword
heuristics. It returns a route key (which maps to a model in config.MODELS)
plus a short human-readable reason that we surface to the user as "why this
model." Later milestones replace this with learned routing fed by Hermes.

Keep it simple and debuggable. When you add a route, add it to config.MODELS too.
"""
from __future__ import annotations

# Order matters: the first matching bucket wins.
CODE_HINTS = (
    "code", "function", "bug", "error", "stack trace", "traceback", "compile",
    "regex", "python", "javascript", "typescript", "java ", "rust", "golang",
    "sql", "html", "css", "react", "api", "docker", "git ", "refactor",
    "exception", "syntax", "debug", "npm", "pip ",
)

REASONING_HINTS = (
    "prove", "proof", "why does", "why is", "explain why", "reason through",
    "analyze", "analyse", "step by step", "step-by-step", "logic", "logical",
    "theorem", "derive", "calculate", "math", "equation", "trade-off",
    "tradeoff", "compare", "evaluate", "strategy", "implications",
)


def choose_route(query: str) -> tuple[str, str]:
    """Return (route_key, reason). reason is shown to the user verbatim."""
    q = query.lower()

    if any(h in q for h in CODE_HINTS):
        return "code", "this looks like a coding task"

    if any(h in q for h in REASONING_HINTS):
        return "reasoning", "this needs multi-step reasoning"

    # Short, simple questions go to the fast/cheap model.
    if len(q.split()) <= 8:
        return "fast", "short, simple query"

    return "default", "general query"
