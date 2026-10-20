"""Finite C23 saved-frontier feeder sources; compose bytes in RAM only.

No main operation writes a file or calls Task/Game/SDK/Native/OBS/desktop APIs.
The existing ordinary feeder algorithms remain inverse-checked source inputs.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

OWN = Path(__file__).resolve().parent
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
DEADLINE = '2026-10-20T01:48:56.993837Z'
ADMISSION = 'ROOT-C23-COLD-FEEDER-ADMISSION100.json'
FEEDER = 'root_p37c23_same_game_loop_feeder100.py'
LEDGER = 'root_continuity_window_c23_100.py'
LAUNCHER = 'launch_c23_feeder100.py'
BASES = {
 'root_p37c18_same_game_loop_feeder93.py': (33211, '7f061bb0b6782d857ce7c11ea73228a656493fde32a0607c880f47bc00c1176b'),
 'root_continuity_window_c18_93.py': (32658, 'ee1a2b324c8c96277154c4a5113da21bd64c99511f612206aaa2a234791882e5'),
 'launch_c18_feeder93.py': (2459, 'f6097214339d6e759d8559009a53672e181ef527cc2c6ee239458c99019116b5'),
}
DEPENDENCIES = {
 'prepare_c23_full_enabled_cold_controls_v1.py': (29500, '423706af13d8565332b8ed6e50e5d29b107666e54aac607d2e44afba70b8e0d9'),
 'prepare_full_batch_timing_sources_v1.py': (7282, '112d4154a4ac39261749c2be0be0097f1b8c188b7905cbd97091dc89765ef1a8'),
 'full_lifecycle_timing_v1.py': (2480, 'dcbb92b3852123a24dac29f35f182eea6a731a46104d1837478c2990052a32ca'),
 'full_batch_timing_v1.py': (7638, '197e4308b7d0f5a70a8c3474ec0b58581997f3e60bfc2d8414c668dae07c8e0b'),
 'c23_source_abort_checkpoint_inputs_v1.py': (15280, 'cdc3d000e253f22db9c70a0314dab040878e731d5abf44a751a06166bc2370c9'),
}
MAP = (
 ('root_continuity_window_c18_93', 'root_continuity_window_c23_100'),
 ('root_p37c18_same_game_loop_feeder93.py', 'root_p37c23_same_game_loop_feeder100.py'),
 ('P37C18', 'P37C23'),
 ('REQUEST-ADMISSION-CLOSED-C18', 'REQUEST-ADMISSION-CLOSED-C23'),
 ('p37-queue/ROOT-C18-NORMAL-SOURCE-WARM-BOUND.json', 'p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json'),
 ('ROOT-ACTUAL-GAME-LAUNCH-C11.json', 'ROOT-ACTUAL-GAME-LAUNCH-C23.json'),
 ('root_score_month_samples_c16', 'root_score_month_samples_c23'),
)

ADMITTED = '''def admitted():
    global BASELINE_CYCLES, BASELINE_DATE_RAW
    a = c23_checked_file(N / "ROOT-C23-COLD-FEEDER-ADMISSION100.json", 32768)
    c23_require(a.get("schema") == "xar.C23-saved-frontier-feeder/v1"
        and a.get("machine_id") == "xenoamess-full-tower-eb9d2c1186"
        and a.get("ordinary_cycle_credit") == 0 and a.get("original_actions_replayed") is False
        and a.get("window_origin_reset") is False
        and a.get("review_deadline_utc") == "2026-10-20T01:48:56.993837Z",
        "exact C23 source-only preparation is not an actual cold admission")
    refs = a.get("sources")
    c23_require(isinstance(refs, dict) and set(refs) ==
        {"cold_admission", "cold_bound", "actual_Game", "map_admission", "old_ledger"},
        "all five actual cold references required")
    cold = c23_checked(refs["cold_admission"]); marker = c23_checked(refs["cold_bound"])
    game = c23_checked(refs["actual_Game"]); current = c23_checked(refs["map_admission"])
    old = c23_checked(refs["old_ledger"], 16384)
    c23_require(refs["old_ledger"]["bytes"] == 7921 and refs["old_ledger"]["sha256"] ==
        "51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8"
        and Path(refs["old_ledger"]["path"]).resolve() != CONTINUITY_WINDOW.resolve(),
        "immutable historical predecessor archive required before alignment")
    from root_p37c23_cold_resume import cold_inputs
    from root_c23_source_abort_checkpoint_inputs import (
        validate_frozen_business, current_recording_inputs_v1)
    seed, governance, checkpoint, prelaunch, closed = cold_inputs(cold)
    freeze = c23_checked(cold["sdk_freeze"], 2 * 1024**2)
    business = validate_frozen_business(cold, freeze, c23_checked)
    recording = current_recording_inputs_v1(cold, c23_checked)
    frontier_ref = cold["source_abort_index"]
    c23_require(frontier_ref["bytes"] == 9089 and frontier_ref["sha256"] ==
        "312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce",
        "exact F99 saved authority required")
    frontier = c23_checked(frontier_ref, 16384)
    original_ref = cold["original_state"]; save_ref = cold["save_response"]
    c23_require(original_ref["bytes"] == 9054 and original_ref["sha256"] ==
        "c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8"
        and save_ref["bytes"] == 10236 and save_ref["sha256"] ==
        "5b0844c484d3ca23ab73e7b6af9db528398fe40eef62648128d3bd4e1578853b",
        "original saved state and SAVE10480 row required; no large SAVE body read")
    original = c23_checked(original_ref, 16384); saved = c23_checked(save_ref, 16384)
    opening = marker.get("opening_frame")
    c23_require(isinstance(opening, dict) and marker.get("schema") ==
        "xar.c23.normal-checkpoint-cold-bound/v1" and marker.get("machine_id") == a["machine_id"]
        and Path(refs["cold_bound"]["path"]).resolve() == MARKER.resolve()
        and marker.get("completed_cycles") == 4753 and marker.get("T0_date_raw") == 53144328
        and marker.get("new_ordinary_cycle_credit") == 0 and marker.get("AUTO_or_MET_replayed") is False
        and marker.get("checkpoint") == checkpoint == original.get("actual_saved_checkpoint")
        and saved.get("result", {}).get("structured_content", {}).get("checkpoint") == checkpoint
        and seed == original and original.get("completed_cycles") == 4753
        and original.get("counts", {}).get("checkpoint_saved") == 74
        and frontier.get("completed_cycles") == 4753 and frontier.get("date_raw") == 53274624
        and frontier.get("checkpoint_saved_count") == 74 and frontier.get("next_sequence") == 10481
        and frontier.get("new_SDK_pair_published") is False
        and opening.get("date_raw") == 53274624 and opening.get("actor_character_id") == 40526
        and opening.get("episode_run_id") == "native-40526-1bec95182886"
        and type(opening.get("native_revision")) is int and opening["native_revision"] > 0,
        "cold opening must retain already accounted SAVE10480 frontier")
    c23_require(type(game.get("pid")) is int and game["pid"] > 0
        and type(game.get("creation_filetime")) is int and game["creation_filetime"] > 134368995759027619
        and isinstance(game.get("creation_date"), str) and bool(game["creation_date"])
        and (game["pid"], game["creation_filetime"]) != (30852, 134368995759027619)
        and game.get("old_save_loaded") is True and game.get("load_save_name") == "xar_checkpoint"
        and cold.get("new_Game") == {k: game[k] for k in ("pid", "creation_filetime", "creation_date")}
        and recording["binding"]["Game_pid"] == game["pid"]
        and recording["binding"]["Game_creation_filetime"] == game["creation_filetime"]
        and current.get("status") == "GREEN" and current.get("reviewer") == "/root"
        and current.get("machine_id") == a["machine_id"] and current.get("actual_initial_frame") == opening
        and current.get("game_pid") == game["pid"] and current.get("game_creation_filetime") == game["creation_filetime"]
        and Path(refs["actual_Game"]["path"]).resolve() == (N / "ROOT-ACTUAL-GAME-LAUNCH-C23.json").resolve()
        and old.get("status") == "repair_required" and old.get("last_settled_cycles") == 4734
        and old.get("last_settled_date_raw") == 53274408 and old.get("start_date_raw") == 53144328
        and old.get("target_date_raw") == 53407128 and old.get("machine_id") == a["machine_id"]
        and old.get("game_binding") == {"pid": 30852, "creation_date": "20261019160615.902761+000"},
        "new actual Game/Root map and historical predecessor differ")
    spec = c23_checked(a["feeder_task_spec"], 16384); nonce = a.get("feeder_task_nonce")
    c23_require(isinstance(nonce, str) and len(nonce) == 32
        and all(c in "0123456789abcdef" for c in nonce)
        and spec.get("schema") == "xar.interactive-task-owner/v1" and spec.get("role") == "feeder"
        and spec.get("machine_id") == a["machine_id"] and spec.get("nonce") == nonce
        and spec.get("task_name") == "XARG2ManagedOwner-" + nonce
        and Path(spec["stage"]).resolve() == (N / "launch_c23_feeder100.py").resolve()
        and spec.get("stage_sha256") == sha(Path(spec["stage"]))
        and spec.get("stage_args") == ["--first-control-sequence", str(a.get("first_control_sequence"))]
        and spec.get("stop_path") is None and "XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1" not in spec.get("env", {}),
        "actual fixed feeder Task SPEC/nonce/stage/arguments required")
    c23_require(c23_ref(Path(__file__)) == a["feeder_source"]
        and Path(a["continue_marker"]).resolve() == (N / "ROOT-C23-FIRST-FULL-CONTINUE100.json").resolve()
        and not Path(a["continue_marker"]).exists()
        and datetime.now(timezone.utc) < datetime.fromisoformat(a["review_deadline_utc"].replace("Z", "+00:00")),
        "exact timed feeder source, absent create-only marker and original deadline required")
    first = a.get("first_control_sequence")
    c23_require(type(first) is int and first >= 10481 and next_sequence() == first
        and not request_path(first, INBOX).exists() and not request_path(first, OUTBOX).exists(),
        "first FULL must be unused actual NEXT and published by this timed feeder")
    BASELINE_CYCLES = 4753; BASELINE_DATE_RAW = 53144328
    return {**a, "old_ledger": old, "opening": opening, "game": game,
        "saved_authority": {"frontier": frontier_ref, "state": original_ref, "SAVE10480": save_ref},
        "business_commit": business["commit"]}
'''

ATTACH = '''def continuity_attach(v, first_control=3, resume_admission=None):
    if resume_admission is not None or first_control != v["first_control_sequence"]:
        raise ValueError("only actual new C23 first FULL is admitted")
    ledger = WindowLedger(CONTINUITY_WINDOW); old = ledger.load()
    source = {"admission": c23_ref(N / "ROOT-C23-COLD-FEEDER-ADMISSION100.json"),
        "predecessor": v["sources"]["old_ledger"], **v["saved_authority"]}
    if old != v["old_ledger"]:
        raise ValueError("original predecessor changed; no reset or inferred continuation")
    return ledger.apply("C23_saved_frontier_aligned", {
        "machine_id": v["machine_id"], "evidence_id": "C23-saved10480:" + source["admission"]["sha256"],
        "source": source, "old_ledger": old, "game": v["game"], "frame": v["opening"]})
'''

HELPERS = '''def c23_require(ok, why):
    if not ok:
        raise ValueError("C23 feeder denied: " + why)


def c23_checked_file(path, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    c23_require(len(raw) <= limit, "bounded JSON input exceeded")
    value = json.loads(raw)
    c23_require(isinstance(value, dict), "JSON object required")
    return value


def c23_checked(ref, limit=65536):
    path = Path(ref["path"]).resolve(strict=True)
    c23_require(type(ref.get("bytes")) is int and 0 < ref["bytes"] <= limit, "bounded exact ref required")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    c23_require(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"],
        "actual source bytes changed: " + str(path))
    value = json.loads(raw)
    c23_require(isinstance(value, dict), "JSON object required")
    return value


def c23_ref(path):
    path = Path(path).resolve(strict=True)
    c23_require(path.stat().st_size <= 65536, "finite metadata/source reference only")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def c23_gate_expected(v, sequence, result, response, fields):
    c23_require(fields.get("full_timing_origin") == "new_submission_same_producer"
        and fields.get("full_timing_control_sequence") == sequence
        and fields.get("full_timing_clock") == "monotonic_ns"
        and type(fields.get("full_submit_monotonic_ns")) is int
        and type(fields.get("full_receipt_validated_monotonic_ns")) is int
        and fields["full_submit_monotonic_ns"] <= fields["full_receipt_validated_monotonic_ns"]
        and fields.get("full_wall_ns") ==
            fields["full_receipt_validated_monotonic_ns"] - fields["full_submit_monotonic_ns"],
        "first FULL lacks this producer's actual publish-to-validated-receipt origin")
    return {"machine_id": v["machine_id"], "feeder_task_nonce": v["feeder_task_nonce"],
        "feeder_task_spec": v["feeder_task_spec"], "feeder_source": v["feeder_source"],
        "first_control_sequence": sequence, "request": c23_ref(request_path(sequence, INBOX)),
        "response": c23_ref(response), "date_raw": result["actual_end_date_raw"],
        "completed_cycles": result["cumulative_cycles"], "full_lifecycle": fields,
        "review_deadline_utc": v["review_deadline_utc"],
        "hold_started_at_utc": datetime.now(timezone.utc).isoformat()}


def c23_accept_continue(marker, expected):
    c23_require(isinstance(marker, dict) and set(marker) ==
        {"schema", "reviewer", "reviewed_at_utc", "first_batch"}
        and marker.get("schema") == "xar.C23-first-FULL-root-continue/v1"
        and marker.get("reviewer") == "/root" and marker.get("first_batch") == expected,
        "Root continue marker must bind exact first FULL, Task and source")
    at = datetime.fromisoformat(marker["reviewed_at_utc"].replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(expected["review_deadline_utc"].replace("Z", "+00:00"))
    started = datetime.fromisoformat(expected["hold_started_at_utc"])
    c23_require(at.tzinfo is not None and started <= at <= datetime.now(timezone.utc) < deadline,
        "Root review must be actual and within the original deadline")
    return True


def c23_first_batch_hold(v, sequence, result, response, fields):
    expected = c23_gate_expected(v, sequence, result, response, fields)
    marker = Path(v["continue_marker"])
    status("root_review_hold", control_sequence=sequence, first_batch=expected,
        next_control_sequence=result["next_sequence"], continue_marker=str(marker),
        game_sdk_obs_calls=0, next_FULL_published=False)
    while True:
        if STOP.exists() or (N / "REQUEST-ADMISSION-CLOSED-C23").exists() or (N / "EXIT-SDK-P37C23").exists():
            status("operator_stopped", control_sequence=sequence, first_batch_hold=True)
            return False
        if datetime.now(timezone.utc) >= datetime.fromisoformat(v["review_deadline_utc"].replace("Z", "+00:00")):
            status("operator_stopped", control_sequence=sequence, first_batch_hold=True, original_review_deadline_reached=True)
            return False
        if marker.exists():
            return c23_accept_continue(c23_checked_file(marker, 16384), expected)
        time.sleep(.2)


'''

BRANCH = '''    if kind == "C23_saved_frontier_aligned":
        frame = frame_binding(details["frame"]); new = game_binding(details["game"])
        if (state != details["old_ledger"] or state["status"] != "repair_required"
                or state["machine_id"] != "xenoamess-full-tower-eb9d2c1186"
                or state["game_binding"] != {"pid": 30852, "creation_date": "20261019160615.902761+000"}
                or details["game"].get("creation_filetime", 0) <= 134368995759027619
                or state["start_date_raw"] != 53144328 or state["target_date_raw"] != 53407128
                or state["last_settled_cycles"] != 4734 or state["last_settled_date_raw"] != 53274408
                or frame["date_raw"] != 53274624 or frame["actor_character_id"] != 40526
                or frame["episode_run_id"] != "native-40526-1bec95182886"
                or details["source"]["predecessor"]["sha256"] != "51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8"
                or details["source"]["frontier"]["sha256"] != "312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce"
                or details["source"]["state"]["sha256"] != "c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8"
                or details["source"]["SAVE10480"]["sha256"] != "5b0844c484d3ca23ab73e7b6af9db528398fe40eef62648128d3bd4e1578853b"):
            raise ValueError("finite C23 saved-frontier alignment differs")
        state.update(status="running", game_binding=new, latest_binding=frame,
            last_settled_cycles=4753, last_settled_date_raw=53274624,
            cold_handoff_count=state.get("cold_handoff_count", 0) + 1,
            previous_interruption=state.get("interruption"),
            C23_saved_frontier_alignment={"source": details["source"],
                "historical_predecessor_cycles": 4734, "historical_predecessor_date_raw": 53274408,
                "already_settled_saved_cycles": 4753, "already_settled_saved_date_raw": 53274624,
                "already_settled_alignment_cycles": 19, "checkpoint_saved_count": 74,
                "ordinary_cycle_credit": 0, "replayed_cycles": 0,
                "failed10476_or_cycle4754_credit": 0, "new_FULL_success_inferred": False,
                "monotonic_origin_inferred": False, "window_origin_reset": False})
        return state
'''


def require(ok, why):
    if not ok:
        raise ValueError('C23 finite source: ' + why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source(path, expected):
    count, digest = expected
    require(0 < count <= 65536, 'finite source limit required')
    with Path(path).open('rb') as stream:
        raw = stream.read(count + 1)
    require(len(raw) == count and sha(raw) == digest, 'exact source pin differs: ' + str(path))
    return raw


def ref(path, raw):
    return {'path': str(Path(path).resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def functions(raw, names, env):
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == set(names), 'finite unchanged function selection differs')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact pinned finite functions>', 'exec'), env)
    return env


def timing_transform(raw, source_ref, deps):
    # Exact source functions, unchanged AST. Avoid importing or building the
    # unrelated eighteen-control graph merely to call its finite timing entry.
    timing = functions(deps['prepare_full_batch_timing_sources_v1.py'],
        {'_change', '_finish', 'transform_feeder'}, {'ast': ast})
    tool = SimpleNamespace(transform_feeder=timing['transform_feeder'])
    def load_tool(name):
        require(name == 'prepare_full_batch_timing_sources_v1.py', 'unexpected dependency request')
        return tool
    entry = functions(deps['prepare_c23_full_enabled_cold_controls_v1.py'],
        {'require', 'sha', 'transform_cold_feeder_source'}, {'hashlib': hashlib, 'load_tool': load_tool})
    return entry['transform_cold_feeder_source'](raw, source_ref=source_ref)


def swap(text, old, new, changes):
    require(text.count(old) == 1, 'one exact seam required: ' + old[:80])
    changes.append((old, new))
    return text.replace(old, new, 1)


def replace_function(text, name, replacement, changes):
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = text.splitlines(keepends=True)
    old = ''.join(lines[node.lineno-1:node.end_lineno])
    return swap(text, old, replacement.rstrip('\n') + '\n', changes)


def inverse(text, changes, original):
    for old, new in reversed(changes):
        require(text.count(new) == 1, 'inverse seam must be unambiguous')
        text = text.replace(new, old, 1)
    require(text == original, 'unapproved original bytes changed')
    return True


def port(text):
    original = text
    for old, new in MAP:
        text = text.replace(old, new)
    restored = text
    for old, new in reversed(MAP):
        restored = restored.replace(new, old)
    require(restored == original, 'namespace inverse differs')
    return text


def build_sources():
    base = {name: source(T / name, pin) for name, pin in BASES.items()}
    deps = {name: source(OWN / name, pin) for name, pin in DEPENDENCIES.items()}
    original = port(base['root_p37c18_same_game_loop_feeder93.py'].decode())
    feeder = original
    changes = []
    feeder = replace_function(feeder, 'admitted', ADMITTED, changes)
    feeder = replace_function(feeder, 'continuity_attach', ATTACH, changes)
    feeder = swap(feeder, 'def main(first_control: int, continuity_resume_admission=None) -> None:\n'
        '    continuity_attach(admitted(), first_control, continuity_resume_admission)\n',
        'def main(first_control: int, continuity_resume_admission=None) -> None:\n'
        '    verified = admitted()\n'
        '    continuity_attach(verified, first_control, continuity_resume_admission)\n', changes)
    feeder = swap(feeder, '    first_path = request_path(first_control, INBOX)\n',
        '    first_source = publish_or_follow(first_control)\n'
        '    if first_source != "published_new_exact_control":\n'
        '        raise ValueError("C23 first FULL must have this timed producer origin")\n'
        '    first_path = request_path(first_control, INBOX)\n', changes)
    feeder = swap(feeder, '    first = True\n    status("following_actual_control",',
        '    first = True\n    first_batch_reviewed = False\n    status("following_actual_control",', changes)
    feeder = swap(feeder,
        '    previous_cycles: int | None = BASELINE_CYCLES if continuity_resume_admission is not None else None\n',
        '    previous_cycles: int | None = BASELINE_CYCLES\n', changes)
    feeder = swap(feeder,
        '        source = publish_or_follow(following)\n'
        '        status("following_actual_control", continuity_window=stable, control_sequence=following,\n',
        '        if not first_batch_reviewed:\n'
        '            if not c23_first_batch_hold(verified, sequence, result, response, full_wall_fields):\n'
        '                return\n'
        '            first_batch_reviewed = True\n'
        '        source = publish_or_follow(following)\n'
        '        status("following_actual_control", continuity_window=stable, control_sequence=following,\n', changes)
    feeder = swap(feeder, 'def admitted():\n', HELPERS + 'def admitted():\n', changes)
    inverse(feeder, changes, original)
    before = ref(T / FEEDER, feeder.encode())
    feeder, timing_report = timing_transform(feeder.encode(), before, deps)
    ledger_original = base['root_continuity_window_c18_93.py'].decode()
    ledger_changes = []
    ledger = swap(ledger_original, '    if kind == "C18_source_warm_verified":\n',
        BRANCH + '    if kind == "C18_source_warm_verified":\n', ledger_changes)
    inverse(ledger, ledger_changes, ledger_original)
    launcher = port(base['launch_c18_feeder93.py'].decode())
    launch_changes = []
    launcher = swap(launcher,
        '    require_published_full(args.first_control_sequence, inbox=ROOT / "p37-requests", read=read)\n',
        '    # The timed feeder itself validates actual admission and publishes its first FULL.\n', launch_changes)
    inverse(launcher, launch_changes, port(base['launch_c18_feeder93.py'].decode()))
    graph = {FEEDER: feeder, LEDGER: ledger.encode(), LAUNCHER: launcher.encode()}
    for name, raw in graph.items():
        compile(raw, name, 'exec')
    generated = sum(map(len, graph.values()))
    require(generated <= 98304, 'single runtime feeder 96KiB cap exceeded')
    participating = sum(map(len, base.values())) + sum(map(len, deps.values())) + generated
    # Includes three retained raw/source copies plus finite JSON qualification
    # fixtures and selected-function workspaces. This is a logical payload
    # ceiling, not measured Python resident memory or AST object memory.
    logical_upper = participating * 3 + 196608
    require(logical_upper <= 2621440, 'complete logical participation ceiling exceeded')
    report = {'schema': 'xar.C23-cold-feeder-source-graph/v1', 'machine_id': MACHINE,
        'source_only': True, 'startup_admitted': False, 'actual_Runtime_H': 'NOTRUN',
        'source_bases': [ref(T / n, b) for n, b in base.items()],
        'source_dependencies': [ref(OWN / n, b) for n, b in deps.items()],
        'generated': {n: {'bytes': len(b), 'sha256': sha(b)} for n, b in graph.items()},
        'generated_bytes': generated, 'runtime_single_materialization_cap': 98304,
        'logical_participating_payload_bytes': participating,
        'logical_participating_upper_bytes': logical_upper, 'actual_process_resident_peak_measured': False,
        'timing': timing_report, 'algorithm_inverse_pass': True,
        'first_batch_gate': 'one Task; new timed publish, validated receipt, persisted batch and ledger, zero-RPC Root HOLD',
        'original_deadline_utc': DEADLINE, 'no_new_day_cycle_or_speed_credit': True,
        'outputs_materialized': False, 'D_writes': 0, 'Task_Game_SDK_Native_OBS_desktop_calls': 0}
    return graph, report


if __name__ == '__main__':
    graph, report = build_sources()
    print(json.dumps(report, separators=(',', ':')))
