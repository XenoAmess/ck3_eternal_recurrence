"""Prelaunch proof that the military-summary wrappers are in the loaded playset.

This check is intentionally independent of a live CK3 process.  It inspects the
profile's enabled mod descriptors, finds every provider of the private MIL4
script-value wrapper file, and requires exactly one byte-identical provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


WRAPPER_RELATIVE_PATH = Path(
    "common/script_values/xar_mcp_military_preparation_summary_v1.txt"
)
EXPECTED_DEFINITIONS = {
    "xar_mcp_military_current_strength_final": "current_military_strength",
    "xar_mcp_military_max_strength_final": "max_military_strength",
    "xar_mcp_military_number_of_knights_final": "number_of_knights",
    "xar_mcp_military_max_number_of_knights_final": "max_number_of_knights",
    "xar_mcp_military_maa_gold_expense_relative_final": (
        "character_men_at_arms_expense_gold_relative"
    ),
}
_PATH_RE = re.compile(r'^\s*path\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _resolve_outer_descriptor(profile: Path, entry: str) -> Path:
    path = Path(entry.replace("/", "\\"))
    if path.is_absolute():
        return path
    return profile / path


def _resolve_mod_root(profile: Path, outer_descriptor: Path) -> Path | None:
    text = outer_descriptor.read_text(encoding="utf-8-sig")
    match = _PATH_RE.search(text)
    if match is None:
        return None
    raw = match.group(1)
    path = Path(raw.replace("/", "\\"))
    if path.is_absolute():
        return path
    return (profile / path).resolve()


def inspect_profile(profile: Path, expected_wrapper: Path) -> dict[str, Any]:
    profile = profile.resolve()
    expected_wrapper = expected_wrapper.resolve()
    expected_bytes = expected_wrapper.read_bytes()
    load_path = profile / "dlc_load.json"
    load = json.loads(load_path.read_text(encoding="utf-8-sig"))
    enabled = load.get("enabled_mods")
    if not isinstance(enabled, list) or not all(isinstance(item, str) for item in enabled):
        raise ValueError("dlc_load.json enabled_mods is not a string list")

    descriptors: list[dict[str, Any]] = []
    providers: list[dict[str, Any]] = []
    for entry in enabled:
        outer = _resolve_outer_descriptor(profile, entry)
        descriptor: dict[str, Any] = {
            "entry": entry,
            "outer_descriptor": str(outer),
            "outer_descriptor_exists": outer.is_file(),
            "mod_root": None,
        }
        if outer.is_file():
            root = _resolve_mod_root(profile, outer)
            descriptor["mod_root"] = None if root is None else str(root)
            if root is not None:
                wrapper = root / WRAPPER_RELATIVE_PATH
                if wrapper.is_file():
                    data = wrapper.read_bytes()
                    providers.append(
                        {
                            "entry": entry,
                            "path": str(wrapper),
                            "sha256": _sha256(data),
                            "byte_identical": data == expected_bytes,
                        }
                    )
        descriptors.append(descriptor)

    expected_text = expected_bytes.decode("utf-8-sig")
    definition_checks = {
        key: bool(
            re.search(
                rf"(?ms)^\s*{re.escape(key)}\s*=\s*\{{\s*value\s*=\s*"
                rf"{re.escape(expression)}\s*\}}\s*$",
                expected_text,
            )
        )
        for key, expression in EXPECTED_DEFINITIONS.items()
    }
    checks = {
        "enabled_mod_descriptors_exist": all(
            item["outer_descriptor_exists"] for item in descriptors
        ),
        "enabled_mod_roots_resolved": all(item["mod_root"] is not None for item in descriptors),
        "exactly_one_loaded_wrapper_provider": len(providers) == 1,
        "loaded_wrapper_byte_identical": (
            len(providers) == 1 and providers[0]["byte_identical"] is True
        ),
        "expected_wrapper_definitions_complete": all(definition_checks.values()),
    }
    return {
        "schema": "xar.ck3.private.military_preparation_live_profile_preflight_v1",
        "status": "green" if all(checks.values()) else "red",
        "profile": str(profile),
        "expected_wrapper": {
            "path": str(expected_wrapper),
            "sha256": _sha256(expected_bytes),
            "definition_checks": definition_checks,
        },
        "enabled_mods": enabled,
        "descriptors": descriptors,
        "providers": providers,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument(
        "--expected-wrapper",
        type=Path,
        default=(
            Path(__file__).resolve().parents[2]
            / "mod_bridge"
            / WRAPPER_RELATIVE_PATH
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_profile(args.profile, args.expected_wrapper)
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError) as error:
        result = {
            "schema": "xar.ck3.private.military_preparation_live_profile_preflight_v1",
            "status": "red",
            "profile": str(args.profile.resolve()),
            "error": f"{type(error).__name__}: {error}",
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
