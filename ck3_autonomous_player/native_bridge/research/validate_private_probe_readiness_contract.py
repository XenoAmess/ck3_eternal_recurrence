"""Validate a private-probe runner against the live readiness helper signature.

The bounded live runners import the private ``_wait_for_readiness`` helper from
``native_auto_run.py``.  This validator keeps artifact-local runners from
inventing keyword arguments and also requires their character binding check to
remain an explicit post-readiness semantic-snapshot check.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Iterable


HELPER_NAME = "_wait_for_readiness"
CHARACTER_FIELD = "episode_character_id"
PRIVATE_PROBE_FORBIDDEN_KEYWORDS = frozenset({"expected_character_id"})


class ContractError(ValueError):
    """Raised when a runner does not match the readiness-call contract."""


def _single(
    rows: Iterable[ast.AST], *, description: str
) -> ast.AST:
    materialized = list(rows)
    if len(materialized) != 1:
        raise ContractError(
            f"expected exactly one {description}, found {len(materialized)}"
        )
    return materialized[0]


def readiness_keyword_contract(
    readiness_source: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the helper's required and optional keyword-only arguments."""

    tree = ast.parse(readiness_source)
    helper = _single(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == HELPER_NAME
        ),
        description=f"{HELPER_NAME} definition",
    )
    assert isinstance(helper, (ast.FunctionDef, ast.AsyncFunctionDef))
    if helper.args.vararg is not None or helper.args.kwarg is not None:
        raise ContractError(f"{HELPER_NAME} must not accept variadic arguments")
    positional = [argument.arg for argument in helper.args.posonlyargs + helper.args.args]
    if positional != ["driver"]:
        raise ContractError(
            f"{HELPER_NAME} positional contract differs: {positional!r}"
        )
    required = tuple(
        argument.arg
        for argument, default in zip(helper.args.kwonlyargs, helper.args.kw_defaults)
        if default is None
    )
    optional = tuple(
        argument.arg
        for argument, default in zip(helper.args.kwonlyargs, helper.args.kw_defaults)
        if default is not None
    )
    if not required:
        raise ContractError(f"{HELPER_NAME} has no keyword-only contract")
    return required, optional


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _constant_assignment(tree: ast.AST, name: str) -> int:
    assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            assignments.append(value)
    value = _single(assignments, description=f"{name} assignment")
    if (
        not isinstance(value, ast.Constant)
        or isinstance(value.value, bool)
        or not isinstance(value.value, int)
    ):
        raise ContractError(f"{name} must be assigned one integer literal")
    return value.value


def _is_snapshot_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    if not isinstance(node.targets[0], ast.Name) or node.targets[0].id != "snapshot":
        return False
    value = node.value
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "driver"
        and value.func.attr == "take_internal_semantic_snapshot"
        and not value.args
        and not value.keywords
    )


def _is_character_binding_check(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1:
        return False
    if not isinstance(node.ops[0], (ast.Eq, ast.NotEq)) or len(node.comparators) != 1:
        return False

    def is_snapshot_character_get(value: ast.AST) -> bool:
        return (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "snapshot"
            and value.func.attr == "get"
            and len(value.args) == 1
            and isinstance(value.args[0], ast.Constant)
            and value.args[0].value == CHARACTER_FIELD
            and not value.keywords
        )

    def is_expected_owner(value: ast.AST) -> bool:
        return isinstance(value, ast.Name) and value.id == "EXPECTED_OWNER"

    return (
        is_snapshot_character_get(node.left)
        and is_expected_owner(node.comparators[0])
    ) or (
        is_expected_owner(node.left)
        and is_snapshot_character_get(node.comparators[0])
    )


def validate_runner_contract(
    *,
    readiness_source: str,
    runner_source: str,
    expected_character_id: int,
) -> dict[str, object]:
    """Validate one runner and return its frozen, serializable contract."""

    required_keywords, optional_keywords = readiness_keyword_contract(readiness_source)
    tree = ast.parse(runner_source)
    call = _single(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _call_name(node) == HELPER_NAME
        ),
        description=f"{HELPER_NAME} call",
    )
    assert isinstance(call, ast.Call)
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Name) or call.args[0].id != "driver":
        raise ContractError(f"{HELPER_NAME} must receive only driver positionally")
    if any(keyword.arg is None for keyword in call.keywords):
        raise ContractError(f"{HELPER_NAME} call must not use **kwargs")
    actual_keywords = tuple(keyword.arg for keyword in call.keywords)
    supported_keywords = set(required_keywords) | set(optional_keywords)
    unsupported = sorted(set(actual_keywords) - supported_keywords)
    if unsupported:
        raise ContractError(
            f"unsupported {HELPER_NAME} keyword arguments: {unsupported!r}"
        )
    forbidden = sorted(set(actual_keywords) & PRIVATE_PROBE_FORBIDDEN_KEYWORDS)
    if forbidden:
        raise ContractError(
            f"private probe must not pass readiness keyword arguments: {forbidden!r}"
        )
    if actual_keywords != required_keywords:
        raise ContractError(
            f"{HELPER_NAME} keyword contract differs: "
            f"{actual_keywords!r} != {required_keywords!r}"
        )

    owner = _constant_assignment(tree, "EXPECTED_OWNER")
    if owner != expected_character_id:
        raise ContractError(
            f"EXPECTED_OWNER differs: {owner!r} != {expected_character_id!r}"
        )
    snapshot = _single(
        (node for node in ast.walk(tree) if _is_snapshot_assignment(node)),
        description="post-readiness semantic snapshot assignment",
    )
    check = _single(
        (node for node in ast.walk(tree) if _is_character_binding_check(node)),
        description=f"snapshot {CHARACTER_FIELD} binding check",
    )
    if not hasattr(call, "lineno") or not hasattr(snapshot, "lineno") or not hasattr(check, "lineno"):
        raise ContractError("runner nodes have no source locations")
    if not (call.lineno < snapshot.lineno < check.lineno):
        raise ContractError(
            "character binding must be checked from a semantic snapshot after readiness"
        )
    return {
        "schema": "xar.ck3.private_probe_readiness_call_contract_v1",
        "status": "green",
        "helper": HELPER_NAME,
        "positional_arguments": ["driver"],
        "keyword_arguments": list(required_keywords),
        "optional_helper_keyword_arguments": list(optional_keywords),
        "forbidden_private_probe_keyword_arguments": sorted(
            PRIVATE_PROBE_FORBIDDEN_KEYWORDS
        ),
        "expected_character_id": expected_character_id,
        "character_binding_source": "post-readiness internal semantic snapshot",
        "readiness_call_line": call.lineno,
        "snapshot_line": snapshot.lineno,
        "character_check_line": check.lineno,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-source", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    args = parser.parse_args(argv)
    result = validate_runner_contract(
        readiness_source=args.readiness_source.read_text(encoding="utf-8-sig"),
        runner_source=args.runner.read_text(encoding="utf-8-sig"),
        expected_character_id=args.expected_character_id,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
