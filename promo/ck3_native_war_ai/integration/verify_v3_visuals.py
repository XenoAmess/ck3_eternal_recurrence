"""Render one review frame for every V3 cue and keep exact source receipts."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))
from war_ai_promo.v3_visuals import make_v3_frame  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    asset_document = json.loads(args.assets.read_text(encoding="utf-8"))
    if asset_document.get("schema") != "ck3-war-ai.v3-context-frames.v1":
        raise ValueError("Unexpected V3 context frame manifest")
    args.output.mkdir(parents=True, exist_ok=False)
    receipts = []
    for row in ledger["cues"]:
        receipts.append(make_v3_frame(row, args.output / (row["id"] + ".png"), 0,
                                      ledger_path=args.ledger, assets=asset_document["assets"]))
    with (args.output / "receipts.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"schema": "ck3-war-ai.v3-all-cue-visual-review.v1", "frames": receipts,
                   "human_full_film_review": False}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"V3 all-cue visual preflight PASS: {len(receipts)} frames in {args.output}")


if __name__ == "__main__":
    main()
