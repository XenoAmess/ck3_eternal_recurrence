"""Read archived R0173 receipts with the production payment consumer; no SDK or desktop."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

REPO = Path(__file__).resolve().parents[4]
DEFAULT = REPO / "docs/ck3-native-ai/evidence/episode04-r0173-20261015"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(directory):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    archive = directory / manifest["archive"]["path"]
    raw = archive.read_bytes()
    require(len(raw) == manifest["archive"]["bytes"], "Archive size differs")
    require(hashlib.sha256(raw).hexdigest() == manifest["archive"]["sha256"], "Archive SHA differs")
    machine = manifest["machine_id"]
    receipts = {}
    with zipfile.ZipFile(archive) as source:
        require(set(source.namelist()) == set(manifest["files"]), "Archive member set differs")
        require(len(source.namelist()) == len(manifest["files"]), "Duplicate archive names")
        for name, pin in manifest["files"].items():
            require(0 < source.getinfo(name).file_size <= 16 * 1024 * 1024, "Member size limit")
            data = source.read(name)
            require(len(data) == pin["bytes"] and hashlib.sha256(data).hexdigest() == pin["sha256"], name)
            receipts[name] = json.loads(data.decode("utf-8-sig"))

    def body(name):
        envelope = receipts[name]
        require(envelope.get("machine_id") == machine and envelope.get("is_error") is False, name)
        require(envelope["sdk_result"]["structured_content"] == envelope["body"], "SDK envelope differs")
        return envelope["body"]

    sys.path[:0] = [str(REPO), str(REPO / "ck3_autonomous_player/src")]
    from xar_autoplayer.bridge.war_payment_observations_v1 import JOURNAL_KEY, normalize_journal
    from xar_autoplayer.bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1

    before = body("cash21-before.json")
    cash = body("cash21.json")
    require(before["paused"] and before["date_raw"] == 53145552, "Cash frame differs")
    normalize_war_cash_current_resources_v1(cash, snapshot=before)
    # The live wrapper intentionally binds this machine. An archived replay
    # supplies the preserved producer machine to the same strict pure reader.
    journal = normalize_journal(cash[JOURNAL_KEY], snapshot=before, machine_id=machine)
    session = journal["current_session"]
    require(session["pid"] == 14544 and session["process_create_time_100ns"] == 134365403777766761,
            "Historical owned process differs")
    require(session["connection_generation"] == 1 and session["player_character_full_id"] == 31254,
            "Historical actor/generation differs")
    require(session["controlled_window_id"] == 1 and journal["sampling"]["epoch"] == 1, "Window differs")
    claims = journal["qualified_boarding_debits"]
    require(len(claims) == 1, "Expected one strictly recomputed boarding debit")
    debit = claims[0]
    require(debit["writer_sequence"] == 16 and debit["gateway_sequence"] == 17
            and debit["transition_sequence"] == 18, "Recomputed source chain differs")
    writer = next(row for row in journal["records"] if row["journal_sequence"] == 16)
    require(writer["kind"] == 3 and writer["amount_raw"] == 300000, "Positive personal SUB differs")

    def army(frame):
        require(frame["episode_run_id"] == "native-31254-3072c36153e4", "Historical episode differs")
        require(frame["diagnostics"]["bridge_pid"] == 14544
                and frame["diagnostics"]["connection_generation"] == 1, "Historical frame owner differs")
        rows = [row for row in frame["player_armies"] if row["army_id"] == 18]
        require(len(rows) == 1 and rows[0]["owner_character_id"] == 31254, "Army differs")
        return rows[0]

    sea = army(body("day21-final.json"))
    require(sea["army_state"] == "embarked" and sea["current_province_id"] == 1036, "No sea posterior")
    halt = body("halt-request.json")
    require(halt["step"] == "halt-army-18" and halt["accepted"], "Original Halt request differs")
    for name, date in (("halt-after-asynchronous.json", 53145552), ("day22-final.json", 53145576)):
        frame = body(name)
        row = army(frame)
        require(frame["paused"] and frame["date_raw"] == date, "Halt endpoint date differs")
        require(row["current_province_id"] == 1036 and row["route_read_status"] == "complete_empty"
                and row["route_source_count"] == 0 and row["route_province_ids"] == []
                and row["move_target_province_id"] is None, "Halt stationary posterior differs")
    progress = receipts["day21-summary.json"]["actual_movement_progress"]
    require(progress["normalized_edge_progress"]["raw"] == 9799
            and progress["loaded_movement_lock_cutoff"]["raw"] == 50000, "Actual lock operands differ")
    clock = receipts["day22-summary.json"]["clock"]
    require(clock["generation"] == 22 and clock["completed_daily_ticks"] == 1
            and clock["overshoot_days"] == 0 and clock["pause_observed"], "Next-day clock differs")
    shutdown = receipts["bootstrap-result.json"]["session"]
    require(shutdown["process_exit_code"] == 0 and shutdown["shutdown"]["tree_gone"], "Session not closed")
    return {"result": "archived-case-verified", "machine_id": machine, "boarding_gold": 3,
            "R11_native_outcome": True, "R07_original_card_complete": False,
            "maintenance_attribution": "unclosed", "instruction_local_write_observed": False,
            "current_machine_acceptance": False, "human_video_approval": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT)
    print(json.dumps(verify(parser.parse_args().evidence), ensure_ascii=False))
