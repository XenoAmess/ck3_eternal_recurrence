"""Project the hash-bound 092 native Army 22 join trace as observed data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


RESPONSE_SHA256 = {
    "c092-before-snapshot": "86AC61E91C25FFBE74F2B59A8ABE43C3EAC45C1CD0C151F82CF4750B42C63ED7",
    "c092-save-checkpoint": "680ED297430B1383B9CA28991D187C21BBDE3A5CB7E68893025A56D0CC2661EC",
    "c092-before-control": "F3F3ED616EE0AF6FB7B5C506A606941E61D1D46CE15F76D85BB509EDBF2761EA",
    "c092-trace-begin": "5A670C4A91E6375E6DC3936EF91EBA3DF0ED8D3F4E9D96BA46942C871CE4D159",
    "c092-life-advance": "B99B89BF717B07C028CB1AA51D80557C650766A115D37F92C308533EA9B77011",
    "c092-trace-finish": "FE017E2DE3EFF4A481FBBB14632BCE8981F4487E7CAEF97E7DA589971A02CAC8",
    "c092-after-snapshot": "AA7B0B70ACDD4BC4DFB023F362B152C818B08AC02F3816F08BBF91221883E929",
    "c092-after-control": "7D028EE00EEF7E8F778E58E0DD76076BD89D8A03A6C916DC3DB23BD19EA508F2",
}
OTHER_SHA256 = {
    "input-freeze": "4597C4AF13CBC0783B4D324E590B63F8435AD36E69E208F4B8D3CAFFBD26125E",
    "trace-begin-request": "5D5270594F7765FAD423F2FA3CAB0D0BE1B5BBBFE32A9BDC4060960F803F5951",
    "readonly-summary": "A1DD3CAB234108C44719E18688463F3FD812DBF709AB50018F43F16FB04AD6A3",
    "cleanup-check": "C3DC93EF76F2DDC198E63708DF8360A1A12E5C2EC1C9D7A51C65B04ED6E32C6F",
    "capture-report": "CEDC6A0AF7FD805BF1E715ED532CD65C86D7BB661DDC430E531CE24770052978",
}
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "22411F45F8B23262FE8752275801959A8EA1EB2310F848D805D8BD606231A5CF"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def _read(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == expected_sha, path
    value = json.loads(raw)
    assert isinstance(value, dict), path
    return value


def project(attempt_dir: Path) -> dict:
    response_dir = attempt_dir / "ck3-output" / "interactive-requests-responses"
    responses = {name: _read(response_dir / f"{name}.json", sha)
                 for name, sha in RESPONSE_SHA256.items()}
    freeze = _read(attempt_dir / "input-freeze.json", OTHER_SHA256["input-freeze"])
    request = _read(attempt_dir / "ck3-output" / "interactive-requests" /
                    "c092-trace-begin.json", OTHER_SHA256["trace-begin-request"])
    summary = _read(attempt_dir / "readonly-summary.json", OTHER_SHA256["readonly-summary"])
    cleanup = _read(attempt_dir / "cleanup-check.json", OTHER_SHA256["cleanup-check"])
    _read(attempt_dir / "ck3-output" / "capture-report.json", OTHER_SHA256["capture-report"])
    assert freeze["source"]["sha256"] == SAVE_SHA256
    assert freeze["bridge"]["sha256"] == BRIDGE_SHA256
    assert freeze["exe_sha256"] == EXE_SHA256
    assert freeze["combat_id"] == 16777218
    assert freeze["candidate_joining_army_id"] == 22
    assert freeze["capture_runtime_join_width"] is True
    assert freeze["capture_runtime_join_full_entries"] is True
    assert request["combat_id"] == freeze["combat_id"]
    assert request["candidate_joining_army_id"] == freeze["candidate_joining_army_id"]
    assert request["capture_runtime_join_width"] is True
    assert request["capture_runtime_join_full_entries"] is True
    assert all(response["result"] == "CALL_COMPLETED" for response in responses.values())
    assert cleanup["cleanup_ok"] is True and cleanup["capture_returncode"] == 0
    assert cleanup["shutdown"]["tree_gone"] is True
    assert cleanup["shutdown"]["job_active_processes_final"] == 0

    trace = responses["c092-trace-finish"]["body"]["managed_trace"]["trace"]
    readiness = trace["readiness"]
    assert trace["status"] == "captured"
    assert summary["trace"]["status"] == "bounded_trace_available"
    assert trace["failure_flags"] == summary["trace"]["failure_flags"] == 0
    assert trace["record_count"] == len(trace["records"]) == 7
    assert readiness["bounded_capture_complete"] is True
    assert readiness["post_counter_attack_pair_complete"] is True
    assert readiness["outgoing_damage_pair_complete"] is True
    assert readiness["full_mutable_transition_bundle_complete"] is False
    assert readiness["original_trace_ready"] is False
    assert [row["boundary"] for row in trace["records"]] == summary["trace"]["boundaries"]
    assert all(row["capture_failure_flags"] == 0 for row in trace["records"])
    assert summary["before"]["date_raw"] == 53146488
    assert summary["after"]["date_raw"] == 53146512
    assert summary["before"]["phase_day"] == 7
    assert summary["after"]["phase_day"] == 8

    widths = trace["runtime_join_width"]
    entries = trace["runtime_join_full_entries"]
    assert widths["status"] == "captured" and widths["first_failure_code"] == 0
    assert widths["count"] == len(widths["boundaries"]) == 3
    assert entries["status"] == "captured" and entries["first_failure_code"] == 0
    assert entries["count"] == len(entries["boundaries"]) == 2
    assert [row["side_index"] for row in widths["boundaries"]] == [-1, 0, 0]
    assert [row["phase_day"] for row in widths["boundaries"]] == [7, 7, 8]
    assert [row["base_width"] for row in widths["boundaries"]] == [1645, 2467, 2467]
    assert [row["final_width"] for row in widths["boundaries"]] == [1480, 2220, 2220]
    assert widths["boundaries"][2]["outgoing_width_argument"] == 2220

    join_rows = []
    for row in entries["boundaries"]:
        assert row["boundary"] in (0, 1)
        assert row["joined_side_index"] == (-1 if row["boundary"] == 0 else 0)
        assert len(row["incoming_regiments"]) == 13
        assert sum(regiment[1] for regiment in row["incoming_regiments"]) == 2570
        sides = []
        for side in row["sides"]:
            assert side["cached_fighting_total_raw"] - side["entry_current_sum_raw"] == side["cache_minus_entry_raw"]
            assert sum(entry[5] for entry in side["entries"]) == side["entry_current_sum_raw"]
            sides.append({
                "army_ids": side["army_ids"],
                "entry_count": len(side["entries"]),
                "cached_fighting_total_raw": side["cached_fighting_total_raw"],
                "entry_current_sum_raw": side["entry_current_sum_raw"],
                "cache_minus_entry_raw": side["cache_minus_entry_raw"],
            })
        join_rows.append({
            "boundary": row["boundary"],
            "joined_side_index": row["joined_side_index"],
            "incoming_regiment_count": len(row["incoming_regiments"]),
            "incoming_basic_soldiers": sum(regiment[1] for regiment in row["incoming_regiments"]),
            "joined_current_fighting_raw": sum(entry[5] for side in row["sides"]
                                               for entry in side["entries"] if entry[1] == 22),
            "sides": sides,
        })
    assert join_rows[0]["joined_current_fighting_raw"] == 0
    assert join_rows[1]["joined_current_fighting_raw"] == 256000000
    assert join_rows[0]["sides"][0]["cache_minus_entry_raw"] == 5627319
    assert join_rows[0]["sides"][1]["cache_minus_entry_raw"] == 6540081
    assert all(side["cache_minus_entry_raw"] == 0 for side in join_rows[1]["sides"])

    return {
        "schema": "ck3.native_active_join_trace_092.v1",
        "source": {
            "attempt": 92,
            "response_sha256": RESPONSE_SHA256,
            "other_sha256": OTHER_SHA256,
            "exe_sha256": EXE_SHA256,
            "bridge_sha256": BRIDGE_SHA256,
            "save_sha256": SAVE_SHA256,
            "materialized_checkpoint_sha256": summary["materialized_checkpoint_sha256"],
        },
        "identity": {
            "combat_id": freeze["combat_id"],
            "candidate_joining_army_id": freeze["candidate_joining_army_id"],
            "subject_owner_character_id": summary["before"]["mapping"]["subject_owner_character_id"],
            "subject_side_index": summary["before"]["mapping"]["subject_side_index"],
            "before_date_raw": summary["before"]["date_raw"],
            "after_date_raw": summary["after"]["date_raw"],
            "before_phase_day": summary["before"]["phase_day"],
            "after_phase_day": summary["after"]["phase_day"],
        },
        "observed": {
            "status": summary["trace"]["status"],
            "failure_flags": trace["failure_flags"],
            "readiness": readiness,
            "boundaries": [{
                "name": row["boundary"],
                "capture_failure_flags": row["capture_failure_flags"],
                "date_raw": row["native_date_raw"],
                "phase_day": row["phase_day"],
                "side_army_ids": [[army["army_id"] for army in side["armies"]]
                                  for side in row["sides"]],
            } for row in trace["records"]],
            "post_counter_attack": summary["trace"]["post_counter_attack"],
            "outgoing_damage": summary["trace"]["outgoing_damage"],
            "runtime_join_width": [{
                "boundary": row["boundary"],
                "side_index": row["side_index"],
                "phase_day": row["phase_day"],
                "base_width": row["base_width"],
                "final_width": row["final_width"],
                "outgoing_width_argument": row["outgoing_width_argument"],
                "side_fighting_total_raw": row["side_fighting_total_raw"],
            } for row in widths["boundaries"]],
            "runtime_join_full_entries": join_rows,
        },
        "active_resume": {
            "status": "unavailable",
            "missing_required_domains": summary["after"]["resume_missing_domains"],
        },
        "cleanup_ok": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = project(args.attempt_dir)
    if args.fixture is not None:
        assert result == json.loads(args.fixture.read_text(encoding="utf-8"))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        assert not args.output.exists(), args.output
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
