"""Inventory frozen native control receipts for nonzero loser pursuit screen.

Read-only: no game launch or native call. The output is a candidate index, not
evidence that a candidate has a paired save or a native pursuit writeback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def scan(root: Path) -> dict:
    paths = sorted(root.glob("*/ck3-output/interactive-requests-responses/*control.json"))
    counts = {"files": len(paths), "available": 0, "pursuit": 0,
              "pursuit_with_winner": 0, "loser_screen_positive": 0,
              "loser_screen_times_soft_positive": 0}
    candidates = []
    pursuit_zero = []
    for path in paths:
        data = path.read_bytes()
        try:
            response = json.loads(data)
            snapshot = response["body"]["battle_control_snapshot"]
        except (KeyError, TypeError, ValueError):
            continue
        if snapshot.get("status") != "available":
            continue
        counts["available"] += 1
        if snapshot.get("phase") != "pursuit":
            continue
        counts["pursuit"] += 1
        winner = snapshot.get("winner_side")
        if winner not in ("attacker", "defender"):
            continue
        counts["pursuit_with_winner"] += 1
        loser = "defender" if winner == "attacker" else "attacker"
        entries = [entry for key in ("levy_entries", "men_at_arms_entries", "knight_entries")
                   for entry in snapshot[loser].get(key, [])]
        winner_entries = [entry for key in ("levy_entries", "men_at_arms_entries", "knight_entries")
                          for entry in snapshot[winner].get(key, [])]
        winner_positive = sum(isinstance(entry.get("effective_screen_raw"), int)
                              and entry["effective_screen_raw"] > 0
                              for entry in winner_entries)
        positive = [entry for entry in entries
                    if isinstance(entry.get("effective_screen_raw"), int)
                    and entry["effective_screen_raw"] > 0]
        active = [entry for entry in positive
                  if isinstance(entry.get("soft_casualties_raw"), int)
                  and entry["soft_casualties_raw"] > 0]
        row = {
            "path": str(path), "sha256": sha256(data),
            "combat_id": snapshot.get("combat_id"),
            "date_raw": snapshot.get("observed_date_raw"),
            "phase_day": snapshot.get("phase_day"),
            "winner_side": winner, "loser_side": loser,
            "loser_entry_count": len(entries),
            "winner_positive_screen_count": winner_positive,
            "loser_positive_screen_count": len(positive),
            "loser_active_screen_count": len(active),
            "loser_positive_entries": [
                {key: entry.get(key) for key in (
                    "bucket", "regiment_id", "native_carmy_id", "public_cunit_id",
                    "owner_character_id", "current_fighting_raw",
                    "soft_casualties_raw", "effective_screen_raw")}
                for entry in positive],
        }
        if positive:
            counts["loser_screen_positive"] += 1
            if active:
                counts["loser_screen_times_soft_positive"] += 1
            candidates.append(row)
        else:
            pursuit_zero.append({key: row[key] for key in (
                "path", "sha256", "combat_id", "date_raw", "phase_day",
                "winner_side", "loser_side", "loser_entry_count",
                "winner_positive_screen_count")})
    return {"schema": "ck3.frozen_pursuit_screen_candidate_inventory.v1",
            "root": str(root), "counts": counts, "candidates": candidates,
            "pursuit_zero_receipts": pursuit_zero}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    result = scan(args.root)
    if args.check_sidecar:
        if json.loads(args.check_sidecar.read_text(encoding="utf-8")) != result:
            raise ValueError("frozen pursuit candidate inventory changed")
        print(json.dumps({"counts": result["counts"],
                          "sha256": sha256(args.check_sidecar.read_bytes()), "ok": True}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"counts": result["counts"], "sha256": sha256(args.output.read_bytes()),
                          "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
