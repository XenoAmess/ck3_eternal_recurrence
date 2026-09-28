"""Fail closed on A05's exact native facts and card artifact identity.

This checks small JSON sources and card files. It never decodes or hashes raw video.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from render_calculation_cards import DATA, ROOT, require, validate, verify_a05_sources


FACTS = ROOT / "e2-09-a05-writer-facts-20260928-v2.json"
HISTORICAL_FACTS = ROOT / "e2-09-a05-writer-facts-20260928.json"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    receipt = json.loads(FACTS.read_text(encoding="utf-8"))
    index = json.loads(DATA.read_text(encoding="utf-8"))
    validate(index)
    a = index["replays"]["A05"]
    require(receipt["schema"] == "xar.war-ai.episode02.a05-writer-card-facts.v2" and
            sha(HISTORICAL_FACTS) == receipt["supersedes_receipt_sha256"] ==
            "22F3943DC4BF77CD64C4C74846253702C217966EBBABE3F265724D715E5E42B6" and
            receipt["usage_scope"] == "current-a05-paired-writer-edit-proxy" and
            receipt["media_review_status"] == "ENCODED_UNREVIEWED" and
            receipt["clean_spans_certified"] is False and
            receipt["human_review_completed"] is False,
            "A05 fact receipt scope")
    provenance = receipt["field_provenance"]
    require("writer does not expose" in provenance["uncapped_score"] and
            "not a separate cap field" in provenance["single_battle_cap"] and
            "does not expose a separate battle-score component" in provenance["war_total"],
            "A05 writer versus derived/static versus poststate boundaries")
    for name, source in receipt["sources"].items():
        path = Path(source["path"])
        require(path.is_file(), f"missing A05 source {name}")
        if name == "raw_video":
            require(path.stat().st_size == source["bytes"] and
                    source["sha256"] == a["raw_video_sha256_reported_by_recorder"] and
                    source["hash_provenance"] ==
                    "recorder_final_reported_and_file_size_checked_not_rehashed_for_this_card",
                    "A05 raw recorder-reported identity")
        else:
            require(sha(path) == source["sha256"] and
                    ("bytes" not in source or path.stat().st_size == source["bytes"]),
                    f"A05 source bytes or SHA: {name}")
    source_field = {
        "preflight": "source_preflight",
        "start_readback": "source_start_readback",
        "writer_response": "source_terminal",
        "paused_post_snapshot": "source_post_snapshot",
        "same_recorder_observe": "source_observe",
        "same_recorder_terminal_verify": "source_same_recorder_verify",
        "recorder_final": "source_recorder_final",
    }
    for source_name, field in source_field.items():
        require(receipt["sources"][source_name]["sha256"] == a[field + "_sha256"],
                f"A05 receipt/index source: {source_name}")
    verify_a05_sources(a)
    run = receipt["run_identity"]
    preflight = json.loads(Path(receipt["sources"]["preflight"]["path"]).read_text(encoding="utf-8"))
    require((run["source_save_sha256"], run["start_date_raw"],
             run["terminal_date_raw"], run["combat_id"], run["war_id"],
             run["army_id"], run["province_id"], run["player_character_id"]) ==
            (a["source_save_sha256"], a["start_date_raw"],
             a["terminal_date_raw"], 16777218, 4, 18, 2633, 29829),
            "A05 receipt run identity")
    require(run["game_exe_sha256"] == preflight["game"]["sha256"] ==
            index["game"]["exe_sha256"] and
            run["bridge_dll_sha256"] == preflight["bridge_dll"]["sha256"],
            "A05 exact build and candidate DLL")
    facts = receipt["native_writer_facts"]
    expected = {
        "hard_loss_numerator_raw_q100000": a["hard_loss_numerator_raw_q100000"],
        "denominator_people": a["denominator_people"],
        "integer_ratio_raw_q100000": a["ratio_raw_q100000"],
        "selected_cb_battle_scale_raw_q100000": a["cb_scale_raw_q100000"],
        "uncapped_score_raw_q100000": a["uncapped_score_raw_q100000"],
        "single_battle_cap_raw_q100000": a["single_battle_cap_raw_q100000"],
        "battle_row_positive_magnitude_raw_q100000": a["row_magnitude_raw_q100000"],
        "war_attacker_relative_delta_raw_q100000":
            a["war_attacker_relative_delta_raw_q100000"],
    }
    require(all(facts[key] == value for key, value in expected.items()) and
            facts["denominator_buckets_native_add_order_people"] ==
            a["denominator_buckets_people"] and
            receipt["paused_poststate_facts"]["player_relative_war_score"] ==
            a["post_snapshot_player_relative_war_score"],
            "A05 receipt calculated values")
    for name in ("card_index", "renderer", "current_a05_card"):
        artifact = receipt["artifacts"][name]
        path = ROOT / artifact["path_relative_to_this_file"]
        require(path.is_file() and path.stat().st_size == artifact["bytes"] and
                sha(path) == artifact["sha256"], f"A05 card artifact: {name}")
    require(sha(ROOT / "e2-09-calculation.svg") ==
            receipt["artifacts"]["historical_024_card_preserved_sha256"],
            "historical 024 card bytes retained")
    print(f"A05 fact receipt GREEN sha256={sha(FACTS)}")


if __name__ == "__main__":
    main()
