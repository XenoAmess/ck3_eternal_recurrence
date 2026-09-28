"""Check A01 join facts against exact native JSON and current card bytes.

The raw MKV is only size checked; its SHA comes from the sealed recorder reports.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from render_calculation_cards import DATA, ROOT, require, validate, verify_a01_sources


FACTS = ROOT / "e2-06-07-a01-join-facts-20260928.json"


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
    a = index["replays"]["A01"]
    old = index["replays"]["085"]
    require(receipt["schema"] == "xar.war-ai.episode02.a01-join-card-facts.v1" and
            receipt["usage_scope"] == "current-a01-private-join-edit-proxy" and
            receipt["media_status"] == "PTS_CONTINUOUS_UNREVIEWED" and
            receipt["clean_spans_certified"] is False and
            receipt["human_review_completed"] is False,
            "A01 receipt scope")
    source_field = {
        "preflight": "source_preflight",
        "start_readback": "source_start_readback",
        "pre_snapshot": "source_pre_snapshot",
        "trace_begin": "source_trace_begin",
        "trace_finish": "source_trace_finish",
        "post_snapshot": "source_post_snapshot",
        "one_day_advance": "source_advance",
        "recorder_final": "source_recorder_final",
        "pts_audit": "source_pts_audit",
        "session_result": "source_session_result",
    }
    for name, source in receipt["sources"].items():
        path = Path(source["path"])
        require(path.is_file(), f"A01 source missing: {name}")
        if name == "raw_video":
            require(path.stat().st_size == source["bytes"] and
                    source["sha256"] == a["raw_video_sha256_reported_by_recorder"] and
                    source["hash_provenance"] ==
                    "recorder_final_and_pts_audit_reported_not_rehashed_for_cards",
                    "A01 raw recorder-reported identity")
        else:
            require(sha(path) == source["sha256"] and
                    ("bytes" not in source or path.stat().st_size == source["bytes"]),
                    f"A01 source SHA or bytes: {name}")
            require(source["sha256"] == a[source_field[name] + "_sha256"],
                    f"A01 index source SHA: {name}")
    verify_a01_sources(a)
    run = receipt["run_identity"]
    preflight = json.loads(Path(receipt["sources"]["preflight"]["path"]).read_text(encoding="utf-8"))
    require((run["source_save_sha256"], run["pre_date_raw"],
             run["post_date_raw"], run["joining_army_id"], run["war_id"],
             run["combat_id"], run["player_army_id"]) ==
            (a["source_save_sha256"], a["pre_date_raw"], a["date_raw"],
             a["joining_army_id"], 4, 16777218, 18) and
            run["game_exe_sha256"] == preflight["game"]["sha256"] ==
            index["game"]["exe_sha256"] and
            run["bridge_dll_sha256"] == preflight["bridge_dll"]["sha256"],
            "A01 run and exact build identity")
    facts = receipt["native_join_facts"]
    for field in (
        "incoming_regiments", "incoming_starting_people", "incoming_current_people",
        "zero_current_regiment_id", "zero_current_regiment_starting_people",
        "side0_before_cache_raw_q100000", "side0_before_entry_sum_raw_q100000",
        "side0_cache_minus_entry_raw_q100000", "side1_before_cache_raw_q100000",
        "side1_before_entry_sum_raw_q100000", "side1_cache_minus_entry_raw_q100000",
        "side0_after_cache_and_entry_raw_q100000",
        "side1_after_cache_and_entry_raw_q100000", "base_width_before",
        "final_width_before", "base_width_after", "final_width_after",
        "first_side0_fire_width_argument", "forest_width_multiplier_raw_q100000",
    ):
        require(facts[field] == a[field] == old[field],
                f"A01/085 independent numerical match: {field}")
    require(facts["private_trace"] is True and
            facts["production_trace_ready"] is False and
            facts["original_trace_ready"] is False and
            facts["full_mutable_transition_bundle_complete"] is False and
            receipt["poststate_facts"]["army18_exact_battle_control_membership_proven"] is False and
            receipt["poststate_facts"]["war4_player_relative_score"] == 0 and
            receipt["media_boundaries"]["clean_spans_certified"] is False and
            receipt["media_boundaries"]["human_review_completed"] is False and
            receipt["historical_comparison"]["same_run"] is False,
            "A01 private trace, membership, and media boundaries")
    for name, artifact in receipt["artifacts"].items():
        path = ROOT / artifact["path_relative_to_this_file"]
        require(path.is_file() and path.stat().st_size == artifact["bytes"] and
                sha(path) == artifact["sha256"], f"A01 artifact {name}")
    for card, expected in (("e2-06-calculation.svg",
                            receipt["historical_comparison"]["historical_card_e2_06_sha256"]),
                           ("e2-07-calculation.svg",
                            receipt["historical_comparison"]["historical_card_e2_07_sha256"])):
        require(sha(ROOT / card) == expected, f"historical 085 SVG preserved: {card}")
    print(f"A01 join fact receipt GREEN sha256={sha(FACTS)}")


if __name__ == "__main__":
    main()
