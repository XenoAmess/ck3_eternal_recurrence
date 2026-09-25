"""Print the source-bound regiment and army identity fields for the video cases."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "ck3_autonomous_player/tests/fixtures/combat/episode01_messina_paired_day05_r14.json"


def main() -> None:
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    print("source:", FIXTURE)
    print("source_capture_run:", source.get("source_capture_run"))
    print("scenario:", json.dumps(source["base_inputs"]["scenario"], ensure_ascii=False))
    for army in source["base_inputs"]["armies"]:
        print("army_summary:", json.dumps({key: army.get(key) for key in
            ("army_id", "encounter_role", "scope_role", "owner", "commander")}, ensure_ascii=False))
        matches = [regiment for regiment in army["regiments"] if regiment["regiment_id"] in {50, 51, 65, 220}]
        if matches:
            print("army:", json.dumps({key: army.get(key) for key in
                ("army_id", "native_carmy_id", "encounter_role", "scope_role", "owner", "commander")}, ensure_ascii=False))
            for regiment in matches:
                print("regiment:", json.dumps(regiment, ensure_ascii=False))


if __name__ == "__main__":
    main()
