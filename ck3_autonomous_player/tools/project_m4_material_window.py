"""File-only owner entry for the explicit M4 window and existing materials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def read_object(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("M4 input must be a JSON object: " + str(path))
    return value


def write_object(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--window-ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--snapshot-json", type=Path)
    parser.add_argument("--window-id")
    parser.add_argument("--start-date-raw", type=int)
    parser.add_argument("--end-date-raw", type=int)
    parser.add_argument("--campaign-root-json", type=Path)
    parser.add_argument("--faction-receipt-json", type=Path, action="append", default=[])
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.m4_material_window_v1 import (
        collect_m4_materials_v1, project_m4_window_progress_v1, select_m4_window_v1,
    )

    selected = any(value is not None for value in (
        args.window_id, args.start_date_raw, args.end_date_raw,
    ))
    if selected:
        if any(value is None for value in (
            args.snapshot_json, args.window_id, args.start_date_raw, args.end_date_raw,
        )):
            parser.error("selection requires snapshot JSON, window ID and both explicit dates")
        window = select_m4_window_v1(
            read_object(args.snapshot_json), window_id=args.window_id,
            start_date_raw=args.start_date_raw, end_date_raw=args.end_date_raw,
        )
        write_object(args.window_ledger, window)
    else:
        window = read_object(args.window_ledger)
        if not window:
            parser.error("refresh requires a previously selected explicit window ledger")
    root = read_object(args.campaign_root_json)
    root = root.get("campaign_root_context", root)
    materials = collect_m4_materials_v1(
        episode_run_id=window["episode_run_id"], actor_character_id=window["actor_character_id"],
        construction=read_object(args.state_dir / "construction-formal-pending-v1.json"),
        council=read_object(args.state_dir / "private-council-formal-v1.json"),
        sway=read_object(args.state_dir / "active-scheme-sway-formal-private-v1.json"),
        campaign_root=root,
        faction_receipts=[read_object(path) for path in args.faction_receipt_json],
    )
    result = project_m4_window_progress_v1(window, materials)
    result["input_paths"] = {
        "window_ledger": str(args.window_ledger), "state_dir": str(args.state_dir),
        "campaign_root": str(args.campaign_root_json) if args.campaign_root_json else None,
        "faction_receipts": [str(path) for path in args.faction_receipt_json],
    }
    write_object(args.output, result)
    print(json.dumps({"status": "observed", "output": str(args.output),
                      "material_parts_observed": result["material_parts_observed"],
                      "material_parts_total": 3, "game_commands_issued": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
