"""R13 branch of the shared locked-route replay, using R0175 reader/clock code."""
from __future__ import annotations
import copy
import datetime
import watched_stop


def require(ok, message):
    if not ok:
        raise ValueError(message)


def replay_r13(index, archive, repo, *, reader_type, verifier_loader, check_rejections=False):
    require(index.get("schema") == "episode04.locked-route.portable-originals.v1" and index.get("case") == "R13", "R13 archive schema missing")
    reader = reader_type(index, archive)
    require(not any("r09" in p.lower() or "CLOSED" in p for p in reader.entries), "R09 or future close mixed into R13")
    machine = index["machine_id"]; run = index["run_id"]; case = index["case_directory"]+"/"
    require(machine not in ("", "unknown") and case == "locked-routes-helper-a02/locked-r13-a01/", "explicit R13 source identity missing")
    sources = {row["path"]: row for row in index["production_sources"]}
    verify_path = "promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py"
    clock_path = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
    verify = verifier_loader(repo/verify_path, sources[verify_path]["sha256"], "r13_existing_locked_route_verify")
    clock, definition_pins = watched_stop.production_clock(repo/clock_path, sources[clock_path]["sha256"])
    base = reader.member(case+"baseline.actual.json")
    ack = reader.member(case+"alt-move.ack.actual.json")
    final = reader.member(case+"alt-move.arrival.actual.json")
    session = reader.ref(base["session_receipt"])
    runtime = reader.ref(base["runtime_proof"])
    binding = base["binding"]
    require(all(row.get("machine_id") == machine and row.get("run_id") == run for row in (base, ack, final)), "R13 source machine/run changed")
    require(ack["binding"] == final["binding"] == binding, "R13 binding changed")
    require(runtime.get("machine_id") == machine and session.get("machine_id") == machine
            and session.get("pid") == binding["pid"]
            and session.get("creation_filetime_100ns", session.get("process_create_time_100ns")) == binding["process_create_time_100ns"], "R13 original process custody differs")
    refs = {"baseline": base["baseline"], "new_move_post": base["new_move_post"], "locked": ack["locked"],
            "post": final["post"], "first_arrival": final["first_arrival"], "arrival": final["arrival"]}
    frames = {name: verify.frame(reader.ref(row["snapshot"], body=True), reader.ref(row["strength"], body=True), binding)
              for name, row in refs.items()}
    verify.stationary(frames["baseline"])
    require(frames["baseline"]["province"] == base["original_province"]
            and frames["baseline"]["date"] == base["starting_date_raw"], "normal stationary baseline changed")
    initial_target = base["initial_target"]
    initial_route = verify.preview_path(reader.ref(base["initial_preview"], body=True), frames["baseline"], initial_target)
    verify.action_once(reader.ref(base["initial_move_request"]), reader.ref(base["initial_move_response"], body=True),
                       "move-army-"+str(binding["army_id"])+"-to-"+str(initial_target), frames["baseline"])
    verify.same_paused_applied(frames["baseline"], frames["new_move_post"])
    require(frames["new_move_post"]["route"] == initial_route == base["original_route"] and len(initial_route) >= 2, "normal new Move differs from actual preview")
    require(frames["locked"]["province"] == frames["new_move_post"]["province"]
            and frames["locked"]["route"] == initial_route and frames["locked"]["date"] >= frames["new_move_post"]["date"], "not the same independently started locked edge")
    preview = reader.ref(ack["alternate_preview"], body=True)
    request = reader.ref(ack["request"]); response = reader.ref(ack["response"], body=True)
    alternate = ack["alternate_target"]
    def consequence(*, proposed=preview, front=frames["first_arrival"], target=alternate):
        return verify.r13(frames["locked"], frames["post"], front, frames["arrival"], proposed, request, response, target)
    business = consequence()
    require(frames["post"]["route"] == ack["expected_route"], "committed alternate differs from recorded expected route")
    prefix = run+"/requests/"
    requests = {p[len(prefix):]: reader.member(p) for p in reader.entries if p.startswith(prefix)}
    response_prefix = run+"/responses/"
    responses = {p[len(response_prefix):]: p for p in reader.entries if p.startswith(response_prefix)}
    require(set(requests) == set(responses), "R13 original request/response pairs incomplete")
    clocks = [reader.member(p) for p in reader.entries if p.startswith(case+"day-") and p.endswith(".clock-complete.actual.json")]
    clocks.sort(key=lambda row: row["starting_date_raw"])
    require(bool(clocks), "R13 actual clocks absent")
    expected = frames["new_move_post"]["date"]; generations = set(); checked = []; first_inputs = None
    for row in clocks:
        require(row.get("machine_id") == machine and row.get("run_id") == run
                and row["starting_date_raw"] == expected, "R13 clock gap or identity drift")
        before = reader.ref(row["before"]["snapshot"], body=True)
        after = reader.ref(row["after"]["snapshot"], body=True)
        for snapshot in (before, after):
            require(snapshot.get("episode_run_id") == binding["episode"]
                    and snapshot.get("played_character", {}).get("character_id") == binding["actor"]
                    and snapshot.get("diagnostics", {}).get("bridge_pid") == binding["pid"]
                    and snapshot.get("diagnostics", {}).get("connection_generation") == binding["generation"], "clock snapshot outside owned R13 runtime")
        arm = reader.ref(row["arm_response"]); status = reader.ref(row["status_response"])
        require(all(e.get("machine_id") == machine and e.get("is_error") is False for e in (arm, status)), "R13 clock response refused")
        arm_request = arm["request"]; arm_body = arm["body"]; status_body = status["body"]
        claim = reader.member(case+"day-"+str(expected)+".once.claim.json")
        require(claim["binding"] == binding and claim["starting_date_raw"] == expected
                and claim["target_date_raw"] == arm_body["tactical_daily_sentinel"]["target_date_raw"]
                and claim["watch_army_id"] == binding["army_id"] and claim["speed"] == 3, "clock original onceclaim differs")
        require(arm_request["arguments"].get("expected_revision") == before["revision"], "R13 Arm did not use before frame revision")
        arm_prefix, sequence = arm_request["request_id"].removesuffix("-arm-watch-first").rsplit("-", 1)
        resume_name = arm_prefix+"-"+str(int(sequence)+1).zfill(3)+"-resume-once.json"
        require(resume_name in requests and resume_name in responses, "R13 original Resume missing")
        resume = reader.member(responses[resume_name])
        require(requests[resume_name].get("tool") == "ck3_execute_step"
                and requests[resume_name].get("arguments") == {"step": "resume-map", "expected_revision": None}
                and resume.get("machine_id") == machine and resume.get("is_error") is False
                and resume["body"].get("accepted") is True, "R13 original Resume not acknowledged")
        inputs = dict(before=before, after=after, arm_body=arm_body, status_body=status_body, watch_army_id=binding["army_id"])
        value = watched_stop.check_clock(clock, **inputs)
        require(value == row["validated_burst"] and before["date_raw"] == expected
                and after["date_raw"] == row["date_raw"], "R13 production clock projection differs")
        require(value["generation"] not in generations, "R13 generation repeated")
        generations.add(value["generation"]); checked.append(value); expected = after["date_raw"]
        if first_inputs is None: first_inputs = inputs
    require(expected == frames["arrival"]["date"], "R13 clocks do not reach actual alternate arrival")
    case_requests = [r for r in requests.values() if r.get("request_id", "").startswith("r13-")]
    steps = [(r.get("arguments") or {}).get("step", "") for r in case_requests]
    moves = [r for r in case_requests if r.get("tool") == "ck3_move_army" and r.get("arguments", {}).get("army_id") == binding["army_id"]]
    require(len(moves) == 2 and sum(r["arguments"].get("target_province_id") == initial_target for r in moves) == 1
            and sum(r["arguments"].get("target_province_id") == alternate for r in moves) == 1, "initial/alternate typed Moves missing or repeated")
    arm_count = sum(step.startswith("research-arm-tactical-daily-sentinel-v1-") for step in steps)
    resume_count = steps.count("resume-map")
    require(arm_count == resume_count == len(clocks), "R13 Arm/Resume repeated or missing")
    original = reader.member(case+"r13-final-report-a01/RESULT.actual.json")["result"]
    require(original["result"] == business and original["burst_checks"] == checked, "R13 original final report differs from replay")
    recording = reader.member("recording-reroute-pipeline-closure.actual-a01.json")
    require(recording.get("machine_id") == machine, "recorder source machine differs")
    media = index["media_scope"]
    require(media.get("actual_alt_arrival_within_clip") is False and media.get("endpoint_shot_credit") is False,
            "off-clip arrival cannot acquire endpoint-shot credit")
    rejected = []
    if check_rejections:
        def rejects(label, function):
            try: function()
            except (ValueError, KeyError, TypeError): rejected.append({"case": label, "rejected": True}); return
            raise ValueError("mutated R13 evidence admitted: "+label)
        rejects("alternate equals old tail", lambda: consequence(target=business["old_tail_avoided"]))
        changed = copy.deepcopy(preview); changed["route_preview"]["route_province_ids"][0] = 999999
        rejects("fresh preview does not preserve locked first edge", lambda: consequence(proposed=changed))
        wrong_front = copy.deepcopy(frames["first_arrival"]); wrong_front["province"] = alternate
        rejects("independent original-front arrival changed", lambda: consequence(front=wrong_front))
        wrong_clock = copy.deepcopy(first_inputs); wrong_clock["status_body"]["tactical_daily_sentinel"]["generation"] += 1
        rejects("actual stop generation changed", lambda: watched_stop.check_clock(clock, **wrong_clock))
    return {"schema": "episode04.r0176.r13.offline-replay.v1", "status": "PASS", "scope": "R13 supplied native observations only; runtime close and R09 excluded",
            "machine_id": machine, "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_head": index["source_head"], "run_id": run, "binding": binding, "business": business,
            "critical_complete_queries": index["query_count"], "archived_request_response_pairs": len(requests),
            "clock_generations": len(clocks), "actual_total_natural_days": (expected-frames["new_move_post"]["date"])//24,
            "clock_checks": checked, "one_day_sampling_claim": False,
            "original_case_action_counts": {"initial_Move": 1, "alternate_Move": 1, "Arm": arm_count, "Resume": resume_count},
            "production_clock_definitions": definition_pins, "production_clock_source": clock.source_resolution, "rejection_checks": rejected,
            "archive_members_integrity_checked": len(reader.entries), "replayed_member_count": len(reader.read_pins),
            "R09_responses_archived_or_replayed": 0, "CLOSED_archived": False, "runtime_close_qualified": False,
            "media": media, "continuous_clean_review": False, "human_video_approval": False,
            "historical_absolute_paths_followed": 0, "archive_extraction_performed": False,
            "new_live_evidence": False, "game_actions_sent": 0, "video_save_DLL_EXE_bodies_read": 0}
