"""Compare A05 day28-31 native pursuit controls with the frozen 004 source.

Only original response bytes are read. Matching IDs and dates alone do not
establish equal replay values; this report checks every non-revision leaf in
the native battle-control snapshots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


def control(path: Path, day: int) -> tuple[dict, dict]:
    response = json.loads(path.read_text(encoding="utf-8"))
    if response.get("result") != "CALL_COMPLETED" or response.get("body", {}).get("accepted") is not True:
        raise ValueError(f"incomplete native response: {path}")
    snapshot = response["body"]["battle_control_snapshot"]
    expected_date = 53146896 + (day - 28) * 24
    if (snapshot.get("combat_id"), snapshot.get("observed_date_raw"), snapshot.get("phase"), snapshot.get("phase_day")) != (
        16777218, expected_date, "pursuit", day - 28,
    ):
        raise ValueError(f"combat/date/phase identity mismatch: {path}")
    return snapshot, identity(path)


def without_revision(value, *, omit_new_terminal_baseline=False):
    if isinstance(value, dict):
        omitted = {"snapshot_revision"}
        if omit_new_terminal_baseline:
            omitted.add("stored_terminal_loss_baseline_raw")
        return {key: without_revision(item, omit_new_terminal_baseline=omit_new_terminal_baseline)
                for key, item in value.items() if key not in omitted}
    if isinstance(value, list):
        return [without_revision(item, omit_new_terminal_baseline=omit_new_terminal_baseline)
                for item in value]
    return value


def differences(left, right, path="") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            item_path = f"{path}.{key}" if path else key
            if key not in left or key not in right:
                result.append(item_path)
            else:
                result.extend(differences(left[key], right[key], item_path))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [path + ".length"]
        return [item for index, (lvalue, rvalue) in enumerate(zip(left, right))
                for item in differences(lvalue, rvalue, f"{path}[{index}]")]
    return [] if left == right else [path]


def side_summary(snapshot: dict, side: str) -> dict:
    row = snapshot[side]
    entries = row["levy_entries"] + row["men_at_arms_entries"]
    return {"ordered_army_ids": [army["public_cunit_id"] for army in row["ordered_armies"]],
            "regiment_count": len(entries),
            "soft_raw_q100000": sum(item["soft_casualties_raw"] for item in entries),
            "current_raw_q100000": sum(item["current_fighting_raw"] for item in entries),
            "stored_terminal_loss_baseline_raw_q100000": row.get("stored_terminal_loss_baseline_raw"),
            "participant_hard_total_raw_q100000": row["participant_hard_total_raw"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a05-root", type=Path, required=True)
    parser.add_argument("--004-root", dest="root004", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new append-only path")
    rows = []
    for day in range(28, 32):
        path_a05 = args.a05_root / "ck3-output" / "interactive-requests-responses" / f"e2t-s02-d{day}-control.json"
        path_004 = args.root004 / "ck3-output" / "interactive-requests-responses" / f"term-d{day}-control.json"
        a05, a05_source = control(path_a05, day)
        old, old_source = control(path_004, day)
        changed = differences(without_revision(a05), without_revision(old))
        pursuit_changed = differences(without_revision(a05, omit_new_terminal_baseline=True),
                                      without_revision(old, omit_new_terminal_baseline=True))
        rows.append({"day": day, "date_raw": a05["observed_date_raw"],
                     "a05_source": a05_source, "source_004_file": old_source,
                     "a05_snapshot_revision": a05["snapshot_revision"],
                     "revision_004": old["snapshot_revision"],
                     "non_revision_leaf_differences": len(changed),
                     "first_100_different_paths": changed[:100],
                     "pursuit_leaf_differences_after_terminal_baseline_extension": len(pursuit_changed),
                     "first_100_pursuit_different_paths": pursuit_changed[:100],
                     "a05": {"phase_day": a05["phase_day"], "winner_raw": a05["winner_raw"],
                             "attacker": side_summary(a05, "attacker"),
                             "defender": side_summary(a05, "defender")},
                     "source_004": {"phase_day": old["phase_day"], "winner_raw": old["winner_raw"],
                                    "attacker": side_summary(old, "attacker"),
                                    "defender": side_summary(old, "defender")}})
    source_save = identity(args.root004 / "trace-d27-immutable.ck3")
    capture_path = args.a05_root / "ck3-output" / "capture-report.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture["checkpoint_source"]["save"]["sha256"] != source_save["sha256"]:
        raise ValueError("A05 managed capture is not loaded from the frozen 004 day27 save")
    result = {"schema": "ck3.episode02.a05-vs-004-pursuit-controls.v1",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "shared_day27_source_save": source_save,
              "a05_capture_report": identity(capture_path),
              "rows": rows,
              "all_non_revision_native_control_leaves_equal": all(row["non_revision_leaf_differences"] == 0 for row in rows),
              "all_pursuit_control_leaves_equal_after_terminal_baseline_extension": all(
                  row["pursuit_leaf_differences_after_terminal_baseline_extension"] == 0 for row in rows),
              "limits": ["Control equality is a native readback fact, not footage clean-span certification.",
                         "A05 is a new cold-load run; 004 footage and A05 footage are not one uninterrupted recording."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": identity(args.output)["sha256"],
                      "different_leaves_by_day": {row["day"]: row["non_revision_leaf_differences"] for row in rows},
                      "pursuit_differences_by_day": {
                          row["day"]: row["pursuit_leaf_differences_after_terminal_baseline_extension"] for row in rows}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
