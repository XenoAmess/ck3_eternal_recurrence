"""Fail closed on A05's exact native facts and card artifact identity.

This checks small JSON sources and card files. It never decodes or hashes raw video.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from render_calculation_cards import DATA, ROOT, require, validate, verify_a05_sources


FACTS = ROOT / "e2-09-a05-writer-facts-20260928-v3.json"
HISTORICAL_FACTS = ROOT / "e2-09-a05-writer-facts-20260928-v2.json"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify_terminal_frame(writer: dict, post: dict, date_raw: int) -> None:
    """Bind A05's native terminal writer to its paused postbattle snapshot."""
    body = writer.get("body") or {}
    frame = post.get("body") or {}
    source = body.get("source") or {}
    transition = body.get("battle_terminal_transition") or {}
    prior = transition.get("prior") or {}
    journal = transition.get("terminal_journal") or {}
    removal = transition.get("removal") or {}
    subject = transition.get("subject") or {}
    successor = transition.get("successor") or {}
    revision = frame.get("revision")
    native_revision = frame.get("native_revision")
    snapshot_id = frame.get("snapshot_id")
    require(writer.get("result") == post.get("result") == "CALL_COMPLETED" and
            body.get("accepted") is True and body.get("status") == "available" and
            transition.get("status") == "available" and
            body.get("battle_terminal_transition_ready") is True and
            type(revision) is int and type(native_revision) is int and
            isinstance(snapshot_id, str) and bool(snapshot_id) and
            frame.get("paused") is True and frame.get("date_raw") == date_raw and
            body.get("queried_revision") == source.get("revision") == revision and
            body.get("queried_native_revision") == source.get("native_revision") ==
            body.get("snapshot_revision") == transition.get("snapshot_revision") ==
            native_revision and
            body.get("queried_snapshot_id") == source.get("snapshot_id") ==
            snapshot_id and
            source.get("date_raw") == transition.get("observed_date_raw") == date_raw and
            source.get("paused") is True,
            "A05 terminal writer and snapshot native frame binding")
    require(transition.get("prior_combat_id") == prior.get("combat_id") == 16777218 and
            transition.get("subject_public_cunit_id") == 18 and
            prior.get("terminal_kind") == "normal_result" and
            journal.get("event_status") == "observed" and
            removal.get("prior_combat_strictly_resolves") is False and
            removal.get("prior_province_contains_prior_combat_id") is False and
            subject.get("exists") is True and subject.get("native_carmy_id") == 18 and
            subject.get("combat_backlink_id") is None and
            subject.get("active_combat_id") is None and
            successor.get("state") == "subject_retreating" and
            (prior.get("battle_warscore") or {}).get("war_id") == 4,
            "A05 terminal closure and ArmyID 18 / WarID 4 identity")


def main() -> None:
    receipt = json.loads(FACTS.read_text(encoding="utf-8"))
    index = json.loads(DATA.read_text(encoding="utf-8"))
    validate(index)
    a = index["replays"]["A05"]
    require(receipt["schema"] == "xar.war-ai.episode02.a05-writer-card-facts.v3" and
            sha(HISTORICAL_FACTS) == receipt["supersedes_receipt_sha256"] ==
            "5EA9CCE31A58510182EF13A02F88066ED218D787586C64F92B0C4C293FCB116F" and
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
    verify_terminal_frame(
        json.loads(Path(a["source_terminal"]).read_text(encoding="utf-8")),
        json.loads(Path(a["source_post_snapshot"]).read_text(encoding="utf-8")),
        a["terminal_date_raw"],
    )
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
