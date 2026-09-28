"""Check the A05 pursuit card receipt against native controls and exact artifacts.

The original MKV is size checked only. This does not certify clean spans or a
human review of gameplay footage.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from render_calculation_cards import DATA, ROOT, require, validate, verify_a05_sources


FACTS = ROOT / "e2-02-03-a05-pursuit-facts-20260928.json"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def entries(control: dict, side: str) -> list[dict]:
    data = control[side]
    return data["levy_entries"] + data["men_at_arms_entries"]


def require_artifact(artifact: dict) -> None:
    path = ROOT / artifact["path_relative_to_this_file"]
    require(path.is_file() and path.stat().st_size == artifact["bytes"] and
            sha(path) == artifact["sha256"], f"A05 pursuit artifact: {path}")


def main() -> None:
    receipt = json.loads(FACTS.read_text(encoding="utf-8"))
    index = json.loads(DATA.read_text(encoding="utf-8"))
    validate(index)
    a = index["replays"]["A05"]
    old = index["replays"]["004"]
    require(receipt["schema"] == "xar.war-ai.episode02.a05-pursuit-card-facts.v1" and
            receipt["usage_scope"] == "current-a05-paired-pursuit-edit-proxy" and
            receipt["media_status"] == "ENCODED_UNREVIEWED" and
            receipt["clean_spans_certified"] is False and
            receipt["human_review_completed"] is False,
            "A05 pursuit fact scope")
    run = receipt["run_identity"]
    require((run["source_save_sha256"], run["start_date_raw"],
             run["pursuit_dates_raw"], run["combat_id"], run["war_id"],
             run["province_id"], run["retreating_army_id"]) ==
            (a["source_save_sha256"], 53146872,
             [53146896, 53146920, 53146944, 53146968],
             16777218, 4, 2633, 18) and
            run["game_exe_sha256"] == index["game"]["exe_sha256"] and
            "independent_cold_load" in run["source_relation"],
            "A05 pursuit run identity")

    sources = receipt["sources"]
    for name, source in sources.items():
        path = Path(source["path"])
        require(path.is_file() and path.stat().st_size == source["bytes"],
                f"A05 pursuit source size: {name}")
        if name == "raw_video":
            require(source["sha256"] == a["raw_video_sha256_reported_by_recorder"] and
                    source["hash_provenance"] ==
                    "recorder_final_reported_and_file_size_checked_not_rehashed_for_this_card",
                    "A05 recorder-reported raw identity")
        else:
            require(sha(path) == source["sha256"], f"A05 pursuit source SHA: {name}")
    for day in range(28, 32):
        require(sources[f"native_day{day}_control"]["sha256"] ==
                a[f"source_day{day}_control_sha256"], f"A05 d{day} index SHA")
    require(sources["a05_parity_report"]["sha256"] ==
            a["source_pursuit_parity_sha256"] and
            sources["a05_vs_004_control_audit"]["sha256"] ==
            a["source_pursuit_control_audit_sha256"] and
            sources["recorder_final"]["sha256"] ==
            a["source_recorder_final_sha256"],
            "A05 pursuit report and recorder binding")
    verify_a05_sources(a)

    controls = [json.loads(Path(sources[f"native_day{day}_control"]["path"])
                           .read_text(encoding="utf-8"))["body"]["battle_control_snapshot"]
                for day in range(28, 32)]
    for i, control in enumerate(controls):
        require((control["combat_id"], control["province_id"],
                 control["observed_date_raw"], control["phase"],
                 control["phase_day"], control["winner_raw"]) ==
                (16777218, 2633, run["pursuit_dates_raw"][i], "pursuit", i, 0),
                f"A05 d{28+i} native combat and pursuit phase")
        require([army["public_cunit_id"] for army in control["defender"]["ordered_armies"]] ==
                [18] and len(entries(control, "defender")) == 24,
                f"A05 d{28+i} retreating participant identity")
    initial = controls[0]
    native_levy = initial["defender"]["levy_entries"]
    native_maa = initial["defender"]["men_at_arms_entries"]
    f = receipt["native_pursuit_facts"]
    require((sum(row["soft_casualties_raw"] for row in native_levy),
             sum(row["soft_casualties_raw"] for row in native_maa),
             sum(row["effective_screen_raw"] for row in native_levy + native_maa)) ==
            (f["levy_soft_pool_raw_q100000"],
             f["men_at_arms_soft_pool_raw_q100000"],
             f["retreater_effective_screen_sum_raw_q100000"]) ==
            (62528090, 19904137, 0) and
            f["total_soft_pool_raw_q100000"] == 82432227,
            "A05 native soft pools and zero retreater screen")

    parity = json.loads(Path(sources["a05_parity_report"]["path"]).read_text(encoding="utf-8"))
    adapter = json.loads(Path(sources["adapter_provenance"]["path"]).read_text(encoding="utf-8"))
    audit = json.loads(Path(sources["a05_vs_004_control_audit"]["path"])
                       .read_text(encoding="utf-8"))
    require(parity["source_index_sha256"] == sources["adapter_index"]["sha256"] ==
            adapter["index"]["sha256"] and
            parity["terminal_source_sha256"] == a["source_terminal_sha256"] and
            adapter["schema"] == "ck3.episode02.a05-pursuit-parity-adapter.v1" and
            audit["schema"] == "ck3.episode02.a05-vs-004-pursuit-controls.v1" and
            audit["all_pursuit_control_leaves_equal_after_terminal_baseline_extension"] is True and
            audit["all_non_revision_native_control_leaves_equal"] is False,
            "A05 native adapter, comparator, and control audit identity")
    require(len(adapter["copies"]) == 5 and len(audit["rows"]) == 4 and
            len(parity["days"]) == 3,
            "A05 pursuit source coverage")
    for i, day in enumerate(range(28, 32)):
        copy = adapter["copies"][i]
        row = audit["rows"][i]
        original = sources[f"native_day{day}_control"]
        require(copy["original"]["sha256"] == copy["adapter_copy"]["sha256"] ==
                row["a05_source"]["sha256"] == original["sha256"] and
                row["source_004_file"]["sha256"] ==
                old[f"source_day{day}_control_sha256"] and
                row["pursuit_leaf_differences_after_terminal_baseline_extension"] == 0 and
                row["first_100_different_paths"] ==
                ["attacker.stored_terminal_loss_baseline_raw",
                 "defender.stored_terminal_loss_baseline_raw"],
                f"A05 versus 004 day {day} distinct source and equal pursuit state")
    terminal_copy = adapter["copies"][4]
    require(terminal_copy["original"]["sha256"] ==
            terminal_copy["adapter_copy"]["sha256"] ==
            a["source_terminal_sha256"], "A05 terminal adapter copy")

    native_hard = []
    for i, report_day in enumerate(parity["days"]):
        before = {r["regiment_id"]: r for r in entries(controls[i], "defender")}
        after = {r["regiment_id"]: r for r in entries(controls[i + 1], "defender")}
        require(len(before) == len(after) == 24 and set(before) == set(after),
                f"A05 d{28+i} regiment identity")
        soft_delta = sum(before[r]["soft_casualties_raw"] -
                         after[r]["soft_casualties_raw"] for r in before)
        owner_hard_delta = (controls[i + 1]["defender"]["participant_hard_total_raw"] -
                            controls[i]["defender"]["participant_hard_total_raw"])
        readable = [r for r in before if before[r]["hard_casualties_raw"] is not None and
                    after[r]["hard_casualties_raw"] is not None]
        readable_hard_delta = sum(after[r]["hard_casualties_raw"] -
                                  before[r]["hard_casualties_raw"] for r in readable)
        require(len(readable) == 23 and soft_delta == owner_hard_delta ==
                readable_hard_delta == report_day["native_total_soft_to_hard_raw"] ==
                report_day["native_owner_hard_ledger_delta_raw"] ==
                f["native_daily_soft_to_hard_raw_q100000"][i] and
                report_day["owner_hard_ledger_residual_raw"] == 0,
                f"A05 d{28+i} native soft-to-hard and readable ledger")
        for result in report_day["rows"]:
            r = result["regiment_id"]
            require(result["before_soft_raw"] == before[r]["soft_casualties_raw"] and
                    result["native_after_soft_raw"] == after[r]["soft_casualties_raw"] and
                    result["native_pursuit_hard_raw"] ==
                    before[r]["soft_casualties_raw"] - after[r]["soft_casualties_raw"] and
                    result["native_current_delta_raw"] ==
                    after[r]["current_fighting_raw"] - before[r]["current_fighting_raw"] == 0,
                    f"A05 d{28+i} regiment {r} exact native row")
        require(report_day["before_control_sha256"] ==
                sources[f"native_day{28+i}_control"]["sha256"] and
                report_day["after_control_sha256"] ==
                sources[f"native_day{29+i}_control"]["sha256"] and
                (report_day["exact_rows"], report_day["exact_hard_ledger_rows"],
                 report_day["stable_current_rows"]) == (24, 23, 24) and
                report_day["model_intermediates_raw"]["pursuit_damage"] ==
                f["model_pursuit_damage_raw_q100000_each_day"] == 75203000 and
                report_day["model_intermediates_raw"]["screen"] == 0 and
                report_day["model_intermediates_raw"]["toughness_soft"] ==
                f["daily_toughness_soft_raw_q100000"][i],
                f"A05 d{28+i} independent parity and modeled inputs")
        native_hard.append(soft_delta)
    require(native_hard == [2070677, 2097473, 2126119] and
            sum(native_hard) == f["native_total_soft_to_hard_raw_q100000"] == 6294269 and
            f["soft_exact_rows"] == [24, 24, 24] and
            f["readable_hard_exact_rows"] == [23, 23, 23] and
            f["stable_current_rows"] == [24, 24, 24] and
            f["unreadable_hard_rows"] == 3 and
            parity["terminal"]["kind"] == a["terminal_kind"] == "normal_result" and
            parity["terminal"]["winner_raw"] == a["terminal_winner_side"] == 0,
            "A05 three-day native pursuit result")
    require("no native scalar" in receipt["field_provenance"]["pursuit_damage_and_toughness_soft"] and
            "not zero" in receipt["field_provenance"]["per_regiment_parity"] and
            receipt["historical_comparison"]["same_run"] is False and
            receipt["media_boundaries"]["known_pts_gap_requires_clean_span_exclusion"] is True and
            receipt["media_boundaries"]["clean_spans_certified"] is False,
            "A05 modeled field, unavailable hard, distinct run, and media boundary")
    for artifact in receipt["artifacts"].values():
        require_artifact(artifact)
    require(sha(ROOT / "e2-02-calculation.svg") ==
            receipt["historical_comparison"]["historical_card_e2_02_sha256"] and
            sha(ROOT / "e2-03-calculation.svg") ==
            receipt["historical_comparison"]["historical_card_e2_03_sha256"],
            "old 004 card bytes retained")
    print(f"A05 pursuit fact receipt GREEN sha256={sha(FACTS)}")


if __name__ == "__main__":
    main()
