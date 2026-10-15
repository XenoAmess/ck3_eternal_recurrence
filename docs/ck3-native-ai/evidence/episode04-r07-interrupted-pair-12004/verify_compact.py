"""Verify the compact interrupted R07 evidence; no game or external dependencies.

This checks the shipped fact projections and their archive pins. Complete cash
and Driver originals are deliberately not shipped, so this cannot rerun their
entire original native/session normalizer qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def daily(proof: dict, expected_count: int) -> dict:
    columns = proof["columns"]
    rows = [dict(zip(columns, row, strict=True)) for row in proof["rows"]]
    need(len(rows) == proof["summary_count"] == expected_count, "daily count changed")
    need(proof.get("all_checks_passed", proof.get("actual_all30_checks_passed")) is True,
         "original actual audit contains a failure")
    previous = 53146848
    fences: dict[int, int] = {}
    for ordinal, row in enumerate(rows, 1):
        segment = row["segment"]
        local_day = row["local_day"]
        need(row["absolute_day"] == ordinal and segment == (1 if ordinal <= 23 else 2),
             "absolute/segment day mismatch")
        need(local_day == (ordinal if segment == 1 else ordinal - 23), "local day mismatch")
        need(row["start_date_raw"] == previous
             and row["date_raw"] == previous + 24
             and row["clock_generation"] == ordinal, "daily date/clock chain changed")
        need((row["window"], row["payment_epoch"]) == ((1, 1) if segment == 1 else (3, 3)),
             "local admitted window/epoch changed")
        old = row.get("previous_payment_sequence", row.get("previous_local_payment"))
        latest = row.get("latest_payment_sequence", row.get("latest_local_payment"))
        need(old == fences.get(segment, 0) and type(latest) is int and latest >= old,
             "local payment fence changed")
        need(row["retained_payment"] <= 384 and row["retained_natural"] <= 56,
             "declared retention stop exceeded")
        need(row["checks_passed"] == row["checks_total"], "daily actual checks failed")
        need(len(row["summary_sha256"]) == 64 and row["summary_bytes"] > 0,
             "original daily source pin missing")
        if expected_count == 32:
            need(row["speed"] == 5 and row["completed_daily_ticks"] == 1
                 and row["overshoot_days"] == 0 and row["pause_observed"] is True,
                 "treatment clock/pause value changed")
        else:
            need(row["selectedProvince"] == 2624 and row["selectedInCombat"] is False,
                 "completed control day is not stationary/no-combat")
        previous = row["date_raw"]
        fences[segment] = latest
    return {"count": len(rows), "last_date_raw": previous, "local_terminal_fences": fences}


def causal(value: dict) -> dict:
    q = value["qualified"]
    need(q["requested_amount_raw"] == 100000 and q["payer_character_id"] == 31254
         and q["account_kind"] == 0 and q["land_id"] is None,
         "observed selected payment changed")
    need(q["entry_balance_bits"] == 25567301 and q["returned_balance_bits"] == 25467301
         and ((q["entry_balance_bits"] - q["requested_amount_raw"]) & ((1 << 64) - 1))
         == q["returned_balance_bits"], "whole-original returned balance mismatch")
    order = value["strict_nested_clock_order"]
    expected = ["natural_entry", "transition_entry", "gateway_entry", "writer_entry",
                "writer_return", "gateway_return", "transition_return", "natural_return"]
    need([row["stage"] for row in order] == expected, "causal event names changed")
    need(len({(row["clock_identity"], row["thread_id"]) for row in order}) == 1
         and all(a["sequence"] < b["sequence"] for a, b in zip(order, order[1:])),
         "causal event clock/thread/order changed")
    parent = value["natural_parent_return"]
    need(parent["original_called"] is True and parent["original_returned"] is True
         and parent["metadata"]["date_raw"] == parent["returned_date_raw"]
         and parent["metadata"]["absolute_day_raw"] == parent["returned_absolute_day_raw"],
         "natural returned-day fence changed")
    records = value["causal_records"]
    transition, gateway, writer = (records[key] for key in ("transition", "gateway", "writer"))
    need([transition["caller_return_rva"], gateway["caller_return_rva"], writer["caller_return_rva"]]
         == [0x2A9A8C5, 0x24E8F40, 0x28B99B2], "source caller chain changed")
    need(writer["amount_raw"] == gateway["amount_raw"] == 100000,
         "gateway/writer requested amount changed")
    for record in records.values():
        need(record["original_called"] is True and record["original_returned"] is True,
             "original callback return missing")
    for side in ("before", "after"):
        need(transition[side]["requested_unit_id"] == 93
             and transition[side]["army_id"] == 85
             and transition[side]["province_id"] == 1036,
             "actual selected Unit/CArmy/Province changed")
    need(transition["before"]["army_1d4"] == 0,
         "source observed transition guard changed")
    cohorts = value["cohorts"]
    need(len(cohorts) == 2 and cohorts[0]["full_DATA_signature"]
         == cohorts[1]["full_DATA_signature"], "start/end complete DATA changed")
    for cohort in cohorts:
        physical = {}
        for ar in cohort["full_DATA_signature"]:
            need(ar["native_data_record_count"] == len(ar["records"]), "DATA count changed")
            for chunk in ar["records"]:
                key = (chunk["persistent_regiment_id"], chunk["chunk_index"])
                pair = (chunk["current_soldiers"], chunk["maximum_soldiers"])
                need(key not in physical or physical[key] == pair, "DATA alias values conflict")
                physical[key] = pair
        need(len(physical) == 4
             and sum(pair[0] for pair in physical.values()) == 250
             and sum(pair[1] for pair in physical.values()) == 250, "physical cohort totals changed")
    need(value["full_v2_qualified"] is False and value["control_compared"] is False,
         "single-arm audit was promoted")
    return {"unit_id": 93, "native_carmy_id": 85, "payer": 31254,
            "actual_boarding_SUB_raw": 100000, "complete_DATA_stable": True}


def verify(directory: Path) -> dict:
    manifest = json.loads((directory / "MANIFEST.json").read_text(encoding="utf-8"))
    verifier_bytes = (directory / "verify_compact.py").read_bytes()
    need(len(verifier_bytes) == manifest["verifier"]["bytes"]
         and digest(verifier_bytes) == manifest["verifier"]["sha256"], "verifier source pin mismatch")
    doc_bytes = (directory / manifest["document"]["relative_from_evidence"]).read_bytes()
    need(len(doc_bytes) == manifest["document"]["bytes"]
         and digest(doc_bytes) == manifest["document"]["sha256"], "canonical document pin mismatch")
    archive = (directory / "compact-evidence.zip").read_bytes()
    need(len(archive) == manifest["archive"]["bytes"]
         and digest(archive) == manifest["archive"]["sha256"], "archive bytes/pin mismatch")
    expected = {row["name"]: row for row in manifest["members"]}
    with zipfile.ZipFile(directory / "compact-evidence.zip") as zipped:
        names = zipped.namelist()
        need(len(names) == len(set(names)) and set(names) == set(expected), "ZIP member set changed")
        need(sum(info.file_size for info in zipped.infolist()) <= 512 * 1024,
             "declared compact metadata bound exceeded")
        data = {}
        for name in names:
            raw = zipped.read(name)
            need(len(raw) == expected[name]["bytes"] and digest(raw) == expected[name]["sha256"],
                 "ZIP member pin mismatch: " + name)
            data[name] = json.loads(raw)
    treatment = daily(data["treatment/daily32.json"], 32)
    control = daily(data["control/daily30.json"], 30)
    payment = causal(data["treatment/causal-data.json"])
    partial = data["control/partial-windows.json"]
    need(partial["raw_complete_journals_consumed_independently"] is True
         and all(not row["selected_army_boarding_callbacks"] for row in partial["results"])
         and [row["through_absolute_day"] for row in partial["results"]] == [23, 30],
         "partial actual windows changed")
    failure = data["control/interruption.json"]
    selected = [row for row in failure["snapshot"]["player_armies"] if row["army_id"] == 93]
    need(len(selected) == 1 and selected[0]["in_combat"] is True
         and selected[0]["army_state_code"] == 2
         and failure["snapshot"]["date_raw"] == 53147592
         and failure["controlled_qualification"] is False, "real control interruption missing")
    for name in ("closure/R178-CLOSED.json", "closure/R179-CLOSED.json"):
        closed = data[name]
        need(closed["normal_exit_code"] == 0 and closed["game_recorder_SDK_keeper_closed"] is True,
             "actual normal close missing")
    need(data["closure/R179-CLOSED.json"]["source_freeze_released"] is True
         and data["closure/R179-CLOSED.json"]["both_scenes_normal_closed"] is True,
         "both-scene actual closure/thaw missing")
    need(data["closure/control-archive.json"]["completed_control_days"] == 30
         and data["closure/control-archive.json"]["control_N32_completed"] is False
         and data["closure/control-sampling-off.json"]["sampling_disabled_and_independently_read_back"] is True
         and data["closure/control-normal-save.json"]["checkpoint"]["status"] == "saved"
         and data["closure/control-normal-save.json"]["checkpoint"]["date_raw"] == 53147592,
         "actual archive/off/normal-save facts changed")
    need(manifest["status"] == "COMPETING_COMBAT_INTERRUPTED_CONTROL"
         and manifest["full_v2_qualified"] is False
         and manifest["original_v1_qualified"] is False
         and manifest["accepted_cards_delta"] == 0, "interrupted pair was promoted")
    return {"status": manifest["status"], "treatment": treatment, "control": control,
            "payment": payment, "both_normal_closed": True, "full_v2_qualified": False,
            "original_v1_qualified": False, "accepted_cards_delta": 0,
            "complete_raw_native_session_replay": False,
            "verification_scope": "shipped compact facts and original audit pins"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
