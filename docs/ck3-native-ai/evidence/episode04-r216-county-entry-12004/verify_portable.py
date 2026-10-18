"""Verify R216 exact small originals and its deliberately narrow research claim."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile


def need(value, why):
    if not value:
        raise ValueError(why)


def verify(index_path, zip_path):
    index = json.loads(index_path.read_bytes())
    need(index.get("schema") == "xar.e04.r216-county-entry-portable-index.v1", "index schema")
    need(index.get("machine_id") == "desktop-3fevhd2-1c74096080", "source machine")
    data = zip_path.read_bytes()
    expected = index["evidence_zip"]
    need(len(data) == expected["bytes"] and hashlib.sha256(data).hexdigest() == expected["sha256"], "zip bytes/SHA")
    originals = {}
    with zipfile.ZipFile(zip_path) as package:
        need(sorted(package.namelist()) == sorted(index["members"]), "zip membership")
        for name, row in index["members"].items():
            need(name.startswith(("independent/", "run/", "media/", "admission/")) and ".." not in Path(name).parts, "unsafe member name")
            raw = package.read(name)
            need(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "member bytes/SHA: " + name)
            if name.endswith(".json"):
                originals[name] = json.loads(raw)
    proof = originals["independent/ROOT-DELIVERY.actual.json"]
    need(proof["machine_id"] == index["machine_id"] and proof["retained_positive_invocations"] == 17 and
         proof["qualified_dated_including_zero"] == 23 and proof["retained_physical_debit"] == 236 and
         proof["endpoint_net"] == -236 and proof["army_at_invocation_observed"] is False and
         proof["complete_army_county_debit"] is None and proof["R04_entire_card_closed"] is False,
         "independent review boundary")
    events = originals["independent/ORIGINAL-SMALL.exact.json"]["writer_verdict"]["events"]
    debits = [event["actual_physical_soldier_debit"] for event in events]
    need(len(events) == 23 and sum(v > 0 for v in debits) == 17 and sum(v == 0 for v in debits) == 6 and
         sum(debits) == 236 and {event["observed_date_raw"] for event in events} == {53147544}, "retained physical event arithmetic")
    small = originals["independent/SMALL-INPUTS.actual.json"]
    fixed = originals["independent/ARRIVAL-FIXED-COUNTERS.actual.json"]
    need(small["writer_fences"]["latest_sequence"] == 0 and
         fixed["actual_loss_writer_family"]["oldest_available_sequence"] == 872 and
         fixed["actual_loss_writer_family"]["overwritten_events"] == 871 and
         originals["independent/ORIGINAL-SMALL.exact.json"]["writer_verdict"]["reasons"] == ["requested_window_overwritten"],
         "actual incomplete global writer window")
    terminal = originals["run/R04-BAYEUX-TERMINAL.json"]
    need(terminal["arrived"] is True and terminal["actual_days"] == 7 and terminal["Move_attempts"] == 1 and
         terminal["finalprovince"] == 1513 and terminal["OFFclear"] is True and terminal["Save"] is True and
         terminal["errors"] == [], "actor terminal")
    media = originals["media/MEDIA-REVIEW.actual.json"]["media"]
    need(media["duration_seconds"] == 179.0 and media["full_decode_single_thread_exit_code"] == 0 and
         media["independent_arrival_verified_inside_recording"] is False and
         media["formal_dynamic_shot_qualified"] is False and media["human_full_speed_review"] is False,
         "limited media boundary")
    need(index["credit"] == {"research_closed": 10, "research_total": 14,
                             "business_closed": 7, "business_total": 11,
                             "dynamic_closed": 0, "dynamic_total": 11,
                             "ABC_closed": 0, "ABC_total": 3}, "credit boundary")
    return {"status": "PASS_EXACT_ORIGINALS_AND_NARROW_R216_FACTS", "machine_id": index["machine_id"],
            "member_count": len(index["members"]), "R04_entire_card_closed": False,
            "same_army_at_invocation_observed": False, "SDK_calls": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=Path(__file__).with_name("index.json"))
    parser.add_argument("--zip", type=Path, default=Path(__file__).with_name("evidence.zip"))
    args = parser.parse_args()
    print(json.dumps(verify(args.index, args.zip), ensure_ascii=False))


if __name__ == "__main__":
    main()
