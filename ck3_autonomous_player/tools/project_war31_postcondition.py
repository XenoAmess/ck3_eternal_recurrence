"""Offline WAR31 before/after report from existing native JSON artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from war31_postcondition_contract import project_war31_postcondition


def _read(path: Path) -> tuple[dict[str, object], str]:
    data = path.read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value, hashlib.sha256(data).hexdigest().upper()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--action-result", type=Path)
    parser.add_argument("--next-turn", type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--recovery-source-save", type=Path)
    parser.add_argument("--recovery-restored-save", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "before": args.before,
        "after": args.after,
        "action_result": args.action_result,
        "next_turn": args.next_turn,
        "recovery": args.recovery,
    }
    inputs = {name: _read(path) for name, path in paths.items() if path is not None}
    pair_paths = (args.recovery_source_save, args.recovery_restored_save)
    if args.recovery is not None and any(path is None for path in pair_paths):
        parser.error("--recovery requires both measured recovery save paths")
    if args.recovery is None and any(path is not None for path in pair_paths):
        parser.error("recovery save paths require --recovery")
    recovery_pair = (
        {
            "source_save_sha256": _hash_file(args.recovery_source_save),
            "restored_save_sha256": _hash_file(args.recovery_restored_save),
        }
        if args.recovery is not None
        else None
    )
    report = project_war31_postcondition(
        inputs["before"][0],
        inputs["after"][0],
        action_result=inputs.get("action_result", (None, ""))[0],
        next_turn_snapshot=inputs.get("next_turn", (None, ""))[0],
        recovery_snapshot=inputs.get("recovery", (None, ""))[0],
        recovery_pair=recovery_pair,
    )
    report["input_artifacts"] = {
        name: {"path": str(paths[name]), "sha256": digest}
        for name, (_, digest) in inputs.items()
    }
    if recovery_pair is not None:
        report["input_artifacts"].update(
            {
                "recovery_source_save": {
                    "path": str(args.recovery_source_save),
                    "sha256": recovery_pair["source_save_sha256"],
                },
                "recovery_restored_save": {
                    "path": str(args.recovery_restored_save),
                    "sha256": recovery_pair["restored_save_sha256"],
                },
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
