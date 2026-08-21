"""Build the exact vanilla-default + Eternal Recurrence rules contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .errors import AgentError


MOD_RULES = (
    ("xar_enabled", "xar_on"),
    ("xar_inheritance", "xar_inherit_100"),
    ("xar_score_basis", "xar_score_growth"),
)


def declared_vanilla_rule_defaults(path: Path) -> list[tuple[str, str]]:
    """Read top-level defaults from the installed CK3 declaration file."""
    if not path.is_file():
        raise AgentError(f"vanilla game-rule declarations not found: {path}")
    text = path.read_text(encoding="utf-8-sig")
    defaults: list[tuple[str, str]] = []
    current_rule: str | None = None
    current_default: str | None = None
    depth = 0
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0]
        if depth == 0:
            match = re.match(r"^([A-Za-z0-9_]+)\s*=\s*\{", line)
            if match:
                current_rule = match.group(1)
                current_default = None
        if current_rule is not None and depth == 1 and current_default is None:
            match = re.match(
                r"^\s*default\s*=\s*([A-Za-z0-9_]+)\s*$", line
            )
            if match:
                current_default = match.group(1)
        depth += line.count("{") - line.count("}")
        if current_rule is not None and depth == 0:
            if current_default is None:
                raise AgentError(
                    f"vanilla game rule {current_rule} has no declared default"
                )
            defaults.append((current_rule, current_default))
            current_rule = None
    if current_rule is not None or depth != 0:
        raise AgentError("unbalanced vanilla game-rule declaration braces")
    if len(defaults) < 70:
        raise AgentError(
            f"vanilla game-rule profile unexpectedly short: {len(defaults)}"
        )
    settings = [setting for _, setting in defaults]
    if len(settings) != len(set(settings)):
        raise AgentError("vanilla game-rule defaults contain duplicate settings")
    return defaults


def rule_contract(path: Path) -> dict[str, object]:
    profile = [
        {"rule": rule, "setting": setting}
        for rule, setting in declared_vanilla_rule_defaults(path)
    ]
    profile.extend(
        {"rule": rule, "setting": setting} for rule, setting in MOD_RULES
    )
    settings = [entry["setting"] for entry in profile]
    if len(settings) != len(set(settings)):
        raise AgentError("combined game-rule profile contains duplicate settings")
    serialized = json.dumps(
        profile, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    return {
        "source": str(path.resolve()),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_vanilla_rule_count": len(profile) - len(MOD_RULES),
        "profile": profile,
        "profile_sha256": hashlib.sha256(serialized).hexdigest(),
        "ironman": False,
    }


def render_presets(contract: dict[str, object]) -> str:
    settings = [entry["setting"] for entry in contract["profile"]]
    return (
        'game_rules_preset={\n'
        '\tname="LastAppliedRules"\n'
        f'\tsetting={{ {" ".join(settings)} }}\n'
        '\tironman=no\n'
        '}\n'
    )


def parsed_preset_settings(text: str) -> tuple[list[str], bool]:
    match = re.search(
        r'name="LastAppliedRules"\s+setting=\{(.*?)\}\s+ironman=(yes|no)',
        text,
        re.DOTALL,
    )
    if not match:
        raise AgentError("LastAppliedRules block is missing or malformed")
    return match.group(1).split(), match.group(2) == "yes"
