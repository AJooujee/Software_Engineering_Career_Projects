"""Regression tests for administrator bootstrap service integration."""

import ast
from pathlib import Path


BOOTSTRAP_MODULE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "cli"
    / "bootstrap_admin.py"
)


def test_bootstrap_user_mutations_include_audit_actor() -> None:
    """Keep CLI mutations compatible with audited service contracts."""

    syntax_tree = ast.parse(
        BOOTSTRAP_MODULE.read_text(encoding="utf-8")
    )
    audited_methods = {
        "change_user_role",
        "change_user_status",
    }
    calls_by_method: dict[str, list[ast.Call]] = {
        method: []
        for method in audited_methods
    }

    for node in ast.walk(syntax_tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in audited_methods
        ):
            calls_by_method[node.func.attr].append(node)

    for method, calls in calls_by_method.items():
        assert len(calls) == 1, (
            f"Expected one {method} call, found {len(calls)}."
        )

        actor_keywords = [
            keyword
            for keyword in calls[0].keywords
            if keyword.arg == "actor"
        ]

        assert len(actor_keywords) == 1, (
            f"{method} must provide exactly one audit actor."
        )

        actor_value = actor_keywords[0].value

        assert (
            isinstance(actor_value, ast.Name)
            and actor_value.id == "user"
        ), f"{method} must attribute the mutation to the bootstrap user."
