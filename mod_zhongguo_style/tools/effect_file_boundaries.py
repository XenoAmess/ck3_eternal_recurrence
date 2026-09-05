#!/usr/bin/env python3
"""Audit ZhongGuo scripted-effect file boundaries without launching CK3.

All runtime effect files target one to ten top-level effects per purpose shard.
More than twenty is a policy violation.  Legacy monoliths have been retired;
the compatibility set remains empty and must not be expanded to hide a miss.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parent.parent
EFFECT_ROOT = MOD_ROOT / "common" / "scripted_effects"
TARGET_MAX = 10
PRINCIPLE_MAX = 20
TOP_LEVEL_EFFECT_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.:-]+)[ \t]*=[ \t]*\{"
)

PRE_B2_COMPATIBILITY_FILES: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class EffectFileBoundary:
    file: str
    effects: int
    bytes: int
    target_met: bool
    principle_met: bool
    pre_b2_compatibility: bool


def top_level_effect_names(text: str) -> tuple[str, ...]:
    """Return brace-depth-zero effect assignment names in file order."""

    names: list[str] = []
    depth = 0
    for line in text.splitlines():
        code: list[str] = []
        quoted = False
        escaped = False
        for character in line:
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
                continue
            if character == '"':
                quoted = True
                continue
            if character == "#":
                break
            code.append(character)
        code_line = "".join(code)
        match = TOP_LEVEL_EFFECT_RE.match(code_line)
        if depth == 0 and match is not None:
            names.append(match.group("name"))
        depth += code_line.count("{") - code_line.count("}")
    return tuple(names)


def audit_effect_files(effect_root: Path = EFFECT_ROOT) -> tuple[EffectFileBoundary, ...]:
    rows: list[EffectFileBoundary] = []
    for path in sorted(effect_root.glob("*.txt"), key=lambda item: item.name.casefold()):
        payload = path.read_bytes()
        names = top_level_effect_names(payload.decode("utf-8-sig"))
        count = len(names)
        pre_b2 = path.name in PRE_B2_COMPATIBILITY_FILES
        rows.append(
            EffectFileBoundary(
                file=path.name,
                effects=count,
                bytes=len(payload),
                target_met=count <= TARGET_MAX,
                principle_met=pre_b2 or count <= PRINCIPLE_MAX,
                pre_b2_compatibility=pre_b2,
            )
        )
    return tuple(rows)


def audit_report(effect_root: Path = EFFECT_ROOT) -> dict[str, object]:
    rows = audit_effect_files(effect_root)
    violations = [asdict(row) for row in rows if not row.principle_met]
    target_misses = [
        asdict(row)
        for row in rows
        if not row.pre_b2_compatibility and not row.target_met
    ]
    return {
        "schema_version": 1,
        "policy": {
            "scope": "all ZhongGuo scripted-effect files",
            "target_max_effects_per_file": TARGET_MAX,
            "principle_max_effects_per_file": PRINCIPLE_MAX,
            "pre_b2_compatibility_files": sorted(PRE_B2_COMPATIBILITY_FILES),
        },
        "result": "GREEN" if not violations else "RED",
        "file_count": len(rows),
        "effect_count": sum(row.effects for row in rows),
        "target_miss_count": len(target_misses),
        "violation_count": len(violations),
        "maximum_non_legacy_effect_count": max(
            (row.effects for row in rows if not row.pre_b2_compatibility),
            default=0,
        ),
        "target_misses": target_misses,
        "violations": violations,
        "files": [asdict(row) for row in rows],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the complete JSON report")
    args = parser.parse_args()
    report = audit_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"{report['result']}: {report['file_count']} files / "
            f"{report['effect_count']} effects; "
            f"target misses={report['target_miss_count']}; "
            f">20 violations={report['violation_count']}; "
            f"max non-legacy={report['maximum_non_legacy_effect_count']}"
        )
        for row in report["violations"]:
            print(f"  - {row['file']}: {row['effects']} effects")
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
