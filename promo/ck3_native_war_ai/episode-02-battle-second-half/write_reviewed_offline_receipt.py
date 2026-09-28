"""Freeze an operator-reviewed fresh Steam offline image for managed CK3.

This never decides whether Steam is offline. The operator must first view the
exact moved screenshot at original resolution and explicitly attest that the
current Steam UI shows 离线模式 and that the desktop is responsive.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freshness-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--i-reviewed-current-offline-ui", action="store_true")
    args = parser.parse_args()
    if not args.i_reviewed_current_offline_ui:
        parser.error("explicit original-image visual review is required")
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be a new file in an existing external attempt")
    freshness = json.loads(args.freshness_receipt.read_text(encoding="utf-8"))
    if freshness.get("schema") != "ck3.steam_fresh_desktop_frame.v1" or \
            freshness.get("moving_edge_changed") is not True or \
            freshness.get("restored_rect") != freshness.get("before_rect") or \
            (args.freshness_receipt.parent / "steam-frame-stale.json").exists():
        parser.error("freshness receipt does not prove a responsive restored frame")
    captured = datetime.fromisoformat(freshness["captured_at_utc"])
    now = datetime.now(timezone.utc)
    if captured.tzinfo is None:
        parser.error("freshness timestamp must have a timezone")
    age = (now - captured).total_seconds()
    if not 0 <= age <= 120:
        parser.error("reviewed frame must be no older than 120 seconds")
    screenshot = Path(freshness["moved_path"])
    current = identity(screenshot)
    if current["sha256"] != str(freshness["moved_sha256"]).upper() or \
            (freshness.get("moved_identity") is not None and
             current != freshness["moved_identity"]):
        parser.error("reviewed screenshot bytes differ from freshness receipt")
    with Image.open(screenshot) as image:
        if list(image.size) != freshness.get("desktop_size"):
            parser.error("screenshot dimensions differ from original desktop")
    result = {
        "observed_at": now.isoformat(),
        "current_offline_ui_observed": True,
        "observation": "Operator reviewed this exact original fresh screenshot; Steam UI visibly reads 离线模式; desktop response checked.",
        "reviewer": args.reviewer,
        "screenshot": current,
        "freshness_receipt": identity(args.freshness_receipt),
        "receipt_writer": identity(Path(__file__)),
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(args.output)


if __name__ == "__main__":
    main()
