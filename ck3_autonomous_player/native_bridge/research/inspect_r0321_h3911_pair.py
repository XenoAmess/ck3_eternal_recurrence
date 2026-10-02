"""Print a bounded structural summary of the exact H3911 driver and report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=Path)
    parser.add_argument("--tail", type=int, default=30)
    args = parser.parse_args()
    document = json.loads(args.driver.read_text(encoding="utf-8"))
    print("root_keys", sorted(document))
    for key in ("schema_version", "episode_run_id", "history_index", "date_raw", "pipe_name"):
        print(key, document.get(key))
    for key in ("checkpoint", "episode", "bridge", "session", "native_session"):
        value = document.get(key)
        if isinstance(value, dict):
            print(key, {k: v for k, v in value.items() if not isinstance(v, (dict, list))})
            print(key + "_keys", sorted(value))
    rows = document.get("command_history", [])
    print("command_history_length", len(rows))
    for index, row in enumerate(rows[-args.tail :], start=len(rows) - args.tail):
        if not isinstance(row, dict):
            print("row", index, type(row).__name__)
            continue
        result = row.get("result")
        print("row", index, "index", row.get("index"), "command", row.get("command"),
              "ok", row.get("ok"), "result_status",
              result.get("status") if isinstance(result, dict) else None,
              "result_keys", sorted(result) if isinstance(result, dict) else None)


if __name__ == "__main__":
    main()
