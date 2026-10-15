"""Pure lookup of already-authored story rows. No external imports or actions."""
from pathlib import Path
import argparse
import json

def load_source_delta(base=None):
    root = Path(base) if base is not None else Path(__file__).resolve().parent
    return json.loads((root / "claim-shot-agent-map.json").read_text(encoding="utf-8"))

def claims_by_source_id(source_id, base=None):
    return [row for row in load_source_delta(base)["paragraphs"] if source_id in row["source_ids"]]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paragraph")
    parser.add_argument("--source-id")
    args = parser.parse_args()
    if (args.paragraph is None) == (args.source_id is None):
        parser.error("choose exactly one of --paragraph or --source-id")
    rows = load_source_delta()["paragraphs"]
    selected = [row for row in rows if row["paragraph_id"] == args.paragraph] if args.paragraph else claims_by_source_id(args.source_id)
    print(json.dumps(selected, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
