"""Replay a closed R12 archive using exact native frames and production clocks.

Reads only the named ZIP, index and repository Python sources. No path found
inside historical evidence is opened; no archive extraction or game command.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import watched_stop


class ReplayError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ReplayError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_python(path, expected_sha, name):
    require(sha(path.read_bytes()) == expected_sha, "repository verifier source pin changed")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArchiveReader:
    def __init__(self, index, archive):
        require(archive.stat().st_size == index["archive"]["bytes"], "archive byte count changed")
        raw = archive.read_bytes()
        require(len(raw) <= 12*1024**2 and sha(raw) == index["archive"]["sha256"], "archive SHA changed")
        self.archive = zipfile.ZipFile(io.BytesIO(raw))
        self.entries = {row["path"]: row for row in index["files"]}
        require(len(self.entries) == len(index["files"]), "duplicate index entry")
        members = self.archive.infolist()
        require(len(members) == len(self.entries) and {m.filename for m in members} == set(self.entries), "archive membership differs")
        require(sum(m.file_size for m in members) <= 96*1024**2, "uncompressed archive exceeds finite replay budget")
        self.by_pin = {}; self.cache = {}; self.read_pins = set()
        for member in members:
            path = PurePosixPath(member.filename)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in member.filename, "unsafe archive member")
            row = self.entries[member.filename]
            require(member.file_size == row["bytes"] and member.file_size <= 16*1024**2, "member size differs")
            data = self.archive.read(member)
            require(sha(data) == row["sha256"], "member pin differs: " + member.filename)
            self.by_pin.setdefault((row["sha256"], row["bytes"]), []).append(member.filename)

    def member(self, relative, *, body=False):
        require(relative in self.entries, "unarchived member: " + relative)
        if relative not in self.cache:
            self.cache[relative] = json.loads(self.archive.read(relative))
        self.read_pins.add(relative)
        result = self.cache[relative]
        return result.get("body", result) if body and isinstance(result, dict) else result

    def ref(self, ref, *, body=False):
        require(type(ref) is dict and type(ref.get("bytes")) is int, "exact original reference missing")
        candidates = self.by_pin.get((ref.get("sha256"), ref["bytes"]), [])
        require(bool(candidates), "referenced exact bytes are not archived")
        # Equal pins identify equal immutable content. Historical path strings
        # remain labels only; never resolve them against a local filesystem.
        return self.member(candidates[0], body=body)


def replay(index, archive, repo, *, check_rejections=False):
    if index.get("case") == "R13":
        from replay_r13 import replay_r13
        return replay_r13(index, archive, repo, reader_type=ArchiveReader, verifier_loader=load_python, check_rejections=check_rejections)
    require(index.get("schema") == "episode04.r0175.portable-originals.v1", "unsupported archive schema")
    reader = ArchiveReader(index, archive)
    machine = index["machine_id"]
    require(isinstance(machine, str) and machine not in ("", "unknown"), "source machine missing")
    run = index["run_id"]
    case = "locked-routes-helper-a02/locked-r12-a01/"
    source_rows = {row["path"]: row for row in index["production_sources"]}
    verify_relative = "promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py"
    clock_relative = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
    verify = load_python(repo/verify_relative, source_rows[verify_relative]["sha256"], "closed_run_locked_routes_verify")
    clock, definition_pins = watched_stop.production_clock(repo/clock_relative, source_rows[clock_relative]["sha256"])
    baseline = reader.member(case+"baseline.actual.json")
    ready = reader.member(case+"capture-ready.actual.json")
    ack = reader.member(case+"halt.ack.actual.json")
    arrival = reader.member(case+"halt.arrival.actual.json")
    nextday = reader.member(case+"halt.nextday.actual.json")
    session = reader.member(case+"session.actual.json")
    closed = reader.member("CLOSED.actual-a01.json")
    binding = baseline["binding"]
    require(all(row.get("machine_id") == machine and row.get("run_id") == run
                for row in (baseline, ready, ack, arrival, nextday, closed)), "case machine/run mismatch")
    require(all(row["binding"] == binding for row in (ready, ack, arrival)), "case binding changed")
    require(session.get("machine_id") == machine and session.get("pid") == binding["pid"]
            and session.get("creation_filetime_100ns", session.get("process_create_time_100ns")) == binding["process_create_time_100ns"], "session creation binding differs")
    require(closed.get("source_head") == index["source_head"]
            and closed.get("process_pid") == binding["pid"]
            and closed.get("process_create_time_100ns") == binding["process_create_time_100ns"], "closed process identity differs")
    runtime = reader.ref(baseline["runtime_proof"])
    require(runtime.get("machine_id") == machine, "runtime source machine differs")
    frame_refs = {"baseline": baseline["baseline"], "new_move_post": baseline["new_move_post"],
                  "locked": ready["locked"], "post": arrival["post"], "arrival": arrival["arrival"], "nextday": nextday["frame"]}
    frames = {name: verify.frame(reader.ref(refs["snapshot"], body=True), reader.ref(refs["strength"], body=True), binding)
              for name, refs in frame_refs.items()}
    verify.stationary(frames["baseline"])
    target = baseline["initial_target"]
    preview = verify.preview_path(reader.ref(baseline["initial_preview"], body=True), frames["baseline"], target)
    verify.action_once(reader.ref(baseline["initial_move_request"]), reader.ref(baseline["initial_move_response"], body=True),
                       "move-army-"+str(binding["army_id"])+"-to-"+str(target), frames["baseline"])
    verify.same_paused_applied(frames["baseline"], frames["new_move_post"])
    require(frames["new_move_post"]["route"] == preview and len(preview) >= 2, "initial normal Move preview/post differ")
    require(frames["locked"]["province"] == frames["new_move_post"]["province"]
            and frames["locked"]["route"] == preview and frames["locked"]["date"] >= frames["new_move_post"]["date"], "locked frame is not original first edge")
    result = verify.r12(frames["locked"], frames["post"], frames["arrival"],
                        reader.ref(ack["request"]), reader.ref(ack["response"], body=True))
    verify.stationary(frames["nextday"])
    require(frames["nextday"]["province"] == frames["arrival"]["province"]
            and frames["nextday"]["date"] == frames["arrival"]["date"]+24, "nextday stationary consequence missing")
    request_prefix = run+"/requests/"; response_prefix = run+"/responses/"
    requests = {p[len(request_prefix):]: reader.member(p) for p in reader.entries if p.startswith(request_prefix)}
    response_paths = {p[len(response_prefix):]: p for p in reader.entries if p.startswith(response_prefix)}
    require(set(requests) == set(response_paths), "original request/response membership differs")
    clocks = [reader.member(p) for p in reader.entries if p.startswith(case+"day-") and p.endswith(".clock-complete.actual.json")]
    clocks.sort(key=lambda x: x["starting_date_raw"])
    require(bool(clocks), "actual clock chain absent")
    expected = frames["new_move_post"]["date"]; generations = set(); checked = []; recovery_rows = []
    first_clock_inputs = None
    for row in clocks:
        require(row.get("machine_id") == machine and row.get("run_id") == run and row["starting_date_raw"] == expected, "clock machine/run/gap differs")
        before = reader.ref(row["before"]["snapshot"], body=True)
        after = reader.ref(row["after"]["snapshot"], body=True)
        arm_envelope = reader.ref(row["arm_response"])
        status_envelope = reader.ref(row["status_response"])
        require(all(e.get("machine_id") == machine and e.get("is_error") is False for e in (arm_envelope, status_envelope)), "clock response rejected/wrong machine")
        arm_request = arm_envelope["request"]
        prefix, sequence = arm_request["request_id"].removesuffix("-arm-watch-first").rsplit("-", 1)
        resume_name = prefix+"-"+str(int(sequence)+1).zfill(3)+"-resume-once.json"
        require(resume_name in requests, "original Resume request missing")
        resume_request = requests[resume_name]
        resume = reader.member(response_paths[resume_name])
        require(resume_request.get("tool") == "ck3_execute_step"
                and resume_request.get("arguments") == {"step": "resume-map", "expected_revision": None}
                and resume.get("machine_id") == machine and resume.get("is_error") is False
                and resume["body"].get("accepted") is True, "original Resume not positively acknowledged")
        require(arm_request["arguments"].get("expected_revision") == before["revision"], "Arm did not bind its before frame")
        inputs = dict(before=before, after=after, arm_body=arm_envelope["body"], status_body=status_envelope["body"], watch_army_id=binding["army_id"])
        value = watched_stop.check_clock(clock, **inputs)
        require(value == row["validated_burst"] and value["starting_date_raw"] == expected and row["date_raw"] == after["date_raw"], "stored clock projection differs from production replay")
        generation = value["generation"]
        require(generation not in generations, "clock generation reused")
        generations.add(generation); expected = after["date_raw"]; checked.append(value)
        if first_clock_inputs is None: first_clock_inputs = inputs
        if row.get("readonly_recovery") is True:
            failure_key = "original_failed_readonly" if "original_failed_readonly" in row else "original_refused_status"
            failure = reader.ref(row[failure_key])
            require(failure.get("is_error") is True and "revision mismatch" in str(failure).lower(), "original readonly refusal missing")
            if "original_refused_status" in row:
                require(row.get("Arm_Resume_reissued") is False
                        and status_envelope["request"]["arguments"] == watched_stop.status_query_arguments(), "status recovery rewrote original action custody")
            else:
                require(row.get("Arm_Resume_status_reissued") is False, "readonly recovery claims a reissued action")
                original_stop = reader.ref(row["original_paused_stop"], body=True)
                watched_stop.same_stopped_army(original_stop, after, binding["army_id"])
            recovery_rows.append({"starting_date_raw": row["starting_date_raw"], "ending_date_raw": row["date_raw"], "scope": "original Arm/Resume retained; readonly publication recovery"})
    require(expected == frames["nextday"]["date"], "clock chain does not reach nextday endpoint")
    case_requests = [r for r in requests.values() if r.get("request_id", "").startswith("r12-")]
    steps = [(r.get("arguments") or {}).get("step", "") for r in case_requests]
    arm_count = sum(s.startswith("research-arm-tactical-daily-sentinel-v1-") for s in steps)
    resume_count = steps.count("resume-map")
    halt_count = steps.count("halt-army-"+str(binding["army_id"]))
    move_count = sum(r.get("tool") == "ck3_move_army" and r.get("arguments", {}).get("army_id") == binding["army_id"] for r in case_requests)
    require(arm_count == resume_count == len(clocks) and halt_count == move_count == 1, "original case actions were duplicated or missing")
    stored = reader.member(case+"r12-final-report-a01/RESULT.actual.json")["result"]
    require(stored["result"] == result and stored["burst_checks"] == checked, "original final report differs from replay")
    natural_days = (expected-frames["new_move_post"]["date"])//24
    require(closed.get("actual_total_natural_days") == natural_days and closed.get("clock_generations") == len(clocks), "closed clock summary differs")
    rejection_checks = []
    if check_rejections:
        def rejects(label, function):
            try: function()
            except (ValueError, KeyError, TypeError): rejection_checks.append({"case": label, "rejected": True}); return
            raise ReplayError("mutated evidence admitted: "+label)
        wrong_ref = dict(frame_refs["locked"]["strength"], sha256="0"*64)
        rejects("changed exact reference pin", lambda: reader.ref(wrong_ref))
        wrong_strength = copy.deepcopy(frames["locked"]["strength"]); wrong_strength["queried_revision"] += 1
        rejects("snapshot/query revision mismatch", lambda: verify.frame(frames["locked"]["snapshot"], wrong_strength, binding))
        wrong_clock = copy.deepcopy(first_clock_inputs); wrong_clock["status_body"]["tactical_daily_sentinel"]["generation"] += 1
        rejects("stop generation changed", lambda: watched_stop.check_clock(clock, **wrong_clock))
        early = copy.deepcopy(first_clock_inputs); early["after"] = copy.deepcopy(early["before"])
        rejects("paused publication before actual date advancement", lambda: watched_stop.check_clock(clock, **early))
    return {"schema": "episode04.r0175.offline-replay.v1", "status": "PASS", "scope": "offline replay of archived R0175 native observations",
            "machine_id": machine, "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "source_head": index["source_head"],
            "run_id": run, "binding": binding, "business": result, "nextday_stationary": True,
            "critical_complete_queries": index["query_count"], "all_original_request_response_pairs": len(requests),
            "clock_generations": len(clocks), "actual_total_natural_days": natural_days, "clock_checks": checked,
            "one_day_sampling_claim": False, "readonly_recoveries": recovery_rows,
            "original_case_action_counts": {"initial_Move": move_count, "Halt": halt_count, "Arm": arm_count, "Resume": resume_count},
            "production_clock_definitions": definition_pins, "production_clock_source": clock.source_resolution, "rejection_checks": rejection_checks,
            "archive_members_integrity_checked": len(reader.entries), "replayed_member_count": len(reader.read_pins),
            "historical_absolute_paths_followed": 0, "unarchived_queries_replayed": 0, "archive_extraction_performed": False,
            "source_claims_only": {"game_tree_gone": closed.get("game_tree_gone"), "process_exit_code": closed.get("actual_final_process_exit_code")},
            "progress": {"core": {"completed": 4, "total": 14}, "business": {"completed": 2, "total": 11}},
            "continuous_clean_review": False, "human_video_approval": False, "new_live_evidence": False,
            "game_actions_sent": 0, "video_save_DLL_EXE_bodies_read": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-rejections", action="store_true")
    args = parser.parse_args()
    require(not args.output.exists(), "append-only replay output already exists")
    try:
        index = json.loads(args.index.read_bytes())
        archive = args.archive or args.index.resolve().parent/index["archive"]["path"]
        result = replay(index, archive, args.repo.resolve(), check_rejections=args.check_rejections); code = 0
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        result = {"status": "NOT-QUALIFIED", "error": str(error), "new_live_evidence": False, "game_actions_sent": 0}; code = 1
    with args.output.open("xb") as stream: stream.write((json.dumps(result, indent=2, ensure_ascii=False)+"\n").encode())
    print(json.dumps({key: result[key] for key in ("status", "error", "machine_id", "clock_generations", "actual_total_natural_days", "critical_complete_queries") if key in result}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
