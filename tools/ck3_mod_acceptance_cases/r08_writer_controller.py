"""Existing finite writer controller, bound to the public CaseClient by its caller.

Extracted lifecycle from writer_root_driver_owner_v2.py SHA256 ef27ce235ae7158ccc1dc3fae2a84110761903bfcf7bbfaafd8e2df84a1f6746.
Historical host construction, CLI and machine paths are deliberately absent.
No import starts a process. The binder supplies load_config and RootRuntime.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import dataclass

RESEARCH = 'ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004'
SESSIONS = {}
SELECTOR = None
CARD = None

def load_config(value):
    raise ValueError('Original common CaseClient binder required')

class RootRuntime:
    def __init__(self, cfg):
        raise ValueError('Original common CaseClient binder required')

def need(ok, why):
    if not ok:
        raise ValueError(why)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def instant(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(parsed.tzinfo is not None, "UTC-aware deadline required")
    return parsed


def pin(path, limit=8 * 1024 * 1024):
    path = Path(path).resolve(strict=True)
    need(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= limit,
         "Bounded regular file required: " + str(path))
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def same_pin(a, b):
    return (type(a) is dict and type(b) is dict and Path(a["path"]).resolve() == Path(b["path"]).resolve()
            and type(a["bytes"]) is int and a["bytes"] == b["bytes"] and a["sha256"] == b["sha256"])


def read_pin(value, limit=1024 * 1024):
    actual = pin(value["path"], limit)
    need(same_pin(actual, value), "Exact file pin differs: " + str(value["path"]))
    # Small controls only. Large raw is read once by the existing actual consumer.
    return json.loads(Path(actual["path"]).read_text(encoding="utf-8-sig"))


def load_module(value, name):
    need(same_pin(pin(value["path"], 256 * 1024), value), "Pinned source differs")
    spec = importlib.util.spec_from_file_location(name, value["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    need(len(data) <= 8 * 1024 * 1024, "Bounded output exceeded")
    with Path(path).open("xb") as stream:
        stream.write(data)
    return pin(path)


def log_pin(path):
    path = Path(path).resolve(strict=True)
    need(path.is_file() and path.stat().st_size <= 8 * 1024 * 1024, "Bounded log required")
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def expected_binding(watch):
    x = watch["expected"]
    return {"pid": x["pid"], "process_create_time_100ns": x["created"],
            "connection_generation": x["generation"], "episode_run_id": x["episode"],
            "player_character_full_id": x["character_id"], "controlled_window_id": x["window"],
            "payment_epoch": x["epoch"], "date_raw": x["date"]}


def prepare(config_pin):
    """Root executes while paused; no observer executable is launched here."""
    cfg = load_config(config_pin)
    rt = RootRuntime(cfg)
    rt.guard()
    control = Path(cfg["control_root"]).resolve()
    need(not control.exists(), "Fresh prepare attempt required; never overwrite/retry an unknown one")
    ordinary=cfg["watch"].get("owner_binding_mode")=="native_campaign_owned_no_load_v2"
    card_pin=cfg.get("build_card") if ordinary else CARD
    need(type(card_pin) is dict,"Ordinary owner requires Root's exact new canonical build-card pin")
    card = load_module(card_pin, "xar_r206_writer_argv_card").make_card(cfg["watch"])
    control.mkdir()
    write(control / "ROOT-ARGV.actual.json", card)
    claim = write(control / "prepare.once.json", {"at_utc": stamp(), "config": config_pin,
                                                 "argv": card["prepare_argv"], "prepare_only": True})
    with (control / "prepare.stdout").open("xb") as out, (control / "prepare.stderr").open("xb") as err:
        result = subprocess.run(card["prepare_argv"], stdout=out, stderr=err, timeout=45, check=False,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    receipt = {"at_utc": stamp(), "config": config_pin, "claim": claim, "returncode": result.returncode,
               "stdout": log_pin(control / "prepare.stdout"), "stderr": log_pin(control / "prepare.stderr"),
               "observer_started": False}
    if result.returncode == 0:
        receipt["admission"] = pin(Path(cfg["watch"]["watch_output_root"]) / "ADMISSION.actual.json")
    write(control / "PREPARE-RESULT.actual.json", receipt)
    need(result.returncode == 0, "Actual prepare-only adapter rejected admission; never retry this directory")
    return receipt


def check_frame(snapshot, expected, *, after=False):
    d, actor = snapshot.get("diagnostics") or {}, snapshot.get("played_character") or {}
    need(snapshot.get("map_ready") is True and snapshot.get("paused") is True
         and actor.get("alive") is True and actor.get("character_id") == expected["character_id"]
         and snapshot.get("episode_run_id") == expected["episode"]
         and d.get("bridge_pid") == expected["pid"]
         and d.get("connection_generation") == expected["generation"], "Fresh owned paused map differs")
    need(type(snapshot.get("date_raw")) is int
         and snapshot["date_raw"] == expected["date"] + (24 if after else 0), "Exact native date differs")
    need(not snapshot.get("active_event") and not snapshot.get("pending_character_interaction"),
         "Native modal present; Root policy handoff, no day retry")


def check_clock(step, before, after):
    from xar_autoplayer.bridge.exact_one_day_postcondition import exact_day_postcondition
    contract = exact_day_postcondition(step, before, after)
    armed, stopped = step["exact_day_native_clock"]["armed"], step["exact_day_native_clock"]["stopped"]
    need(armed.get("state") == "armed" and type(armed.get("generation")) is int
         and armed["generation"] > 0 and type(stopped.get("generation")) is int
         and stopped.get("generation") == armed["generation"]
         and armed.get("starting_date_raw") == before["date_raw"]
         and armed.get("target_date_raw") == after["date_raw"]
         and type(armed.get("completed_daily_ticks")) is int and armed["completed_daily_ticks"] == 0
         and armed.get("abnormal") is False
         and type(armed.get("intermediate_pause_count")) is int
         and type(stopped.get("intermediate_pause_count")) is int
         and armed["intermediate_pause_count"] == stopped["intermediate_pause_count"] == 0,
         "Original native Arm/Stop generation or intermediate pause differs")
    return contract


def check_cash(body, snapshot, admission, repo):
    sys.path[:0] = [str(repo), str(repo / "ck3_autonomous_player/src")]
    from xar_autoplayer.bridge.war_cash_current_raw_context_v1 import validate_current_raw_context_v1
    from xar_autoplayer.bridge import war_payment_observations_v1 as payment
    validate_current_raw_context_v1(body, snapshot=snapshot)
    journal = payment.normalize_journal(body[payment.JOURNAL_KEY], snapshot=snapshot,
                                        machine_id=admission["machine_id"])
    for key, value in admission["expected_root_identity"].items():
        need(type(journal["current_session"][key]) is type(value)
             and journal["current_session"][key] == value, "Original owner/window changed: " + key)
    for key, value in admission["_driver_entry_session"].items():
        need(type(journal["current_session"].get(key)) is type(value)
             and journal["current_session"][key] == value, "Original witness/no-load session changed: " + key)
    sampling = journal["sampling"]
    need(journal["installed"] is True and journal["install_failure_flags"] == 0
         and journal["controlled_window_admitted"] is True and journal["read_complete"] is True
         and sampling["capture_enabled"] is True and sampling["busy"] is False
         and sampling["active_captures"] == 0 and sampling["epoch"] == admission["expected_payment_epoch"],
         "Original payment window/epoch no longer ON and idle")
    leaf, original = body["current_raw_context_v1"], admission["raw_leaf"]
    need(leaf["admission_ready"] is True and leaf["actor_identity_stable"] is True
         and leaf["character"] == original["character"]
         and leaf["values"]["context_identity_before"] == original["values"]["context_identity_before"],
         "Original Character/context identity changed")
    return {"window_id": journal["current_session"]["controlled_window_id"],
            "epoch": sampling["epoch"], "retained_records": sampling.get("retained_records"),
            "latest_sequence": journal["latest_sequence"], "oldest_sequence": journal["oldest_sequence"],
            "overwritten": journal["overwritten"], "publication_failures": journal["publication_failures"]}


@dataclass
class Session:
    cfg: dict
    config_pin: dict
    runtime: object
    card: dict
    admission: dict
    control: Path
    process: object
    stdout: object
    stderr: object
    started_ns: int
    ready: dict | None = None


def await_ready(process, ready_path, *, timeout=15, sleep=time.sleep, monotonic=time.monotonic):
    end = monotonic() + timeout
    while monotonic() < end:
        need(process.poll() is None, "Observer exited before a usable ready; no day submitted")
        if Path(ready_path).exists():
            need(Path(ready_path).stat().st_size <= 65536, "Bounded ready required")
            try:
                raw = Path(ready_path).read_bytes()
                value = json.loads(raw.decode("utf-8-sig"))
            except json.JSONDecodeError:
                # File is created and flushed by the actual observer; partial write is not ready.
                sleep(0.025)
                continue
            need(value.get("ready") is True and type(value.get("armed_thread_count")) is int
                 and value["armed_thread_count"] > 0, "Actual armed readiness absent")
            need(process.poll() is None, "Observer exited while ready was read")
            return {"value": value,
                    "pin": {"path": str(Path(ready_path).resolve()), "bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest()}, "ready_at_utc": stamp()}
        sleep(0.025)
    raise TimeoutError("Finite ready wait expired; no day submitted, do not restart")


def finalize(session):
    """No kill/terminate/detach commands; only wait for native natural cleanup then consume."""
    deadline_ns = session.started_ns + 45_000_000_000
    remaining = max(0.001, (deadline_ns - time.monotonic_ns()) / 1e9)
    try:
        code = session.process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        return {"status": "OBSERVER_STILL_LIVE_DO_NOT_CLOSE_GAME", "cleanup_proved": False,
                "process_id": session.process.pid, "handle_retained_in_module": True,
                "no_force_kill": True}
    session.stdout.close()
    session.stderr.close()
    consumer_out = session.control / "consume.stdout"
    consumer_err = session.control / "consume.stderr"
    write(session.control / "consume.once.json", {"at_utc": stamp(), "argv": session.card["consume_argv"],
                                                "observer_returncode": code})
    with consumer_out.open("xb") as out, consumer_err.open("xb") as err:
        consumed = subprocess.run(session.card["consume_argv"], stdout=out, stderr=err,
                                  timeout=20, check=False,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    need(consumed.returncode == 0, "Actual consumer rejected input; preserve original stdout/stderr")
    result_path = Path(session.cfg["watch"]["watch_output_root"]) / "ACTUAL-WRITERS.json"
    result_pin = pin(result_path)
    actual = read_pin(result_pin, 8 * 1024 * 1024)
    selected = load_module(SELECTOR, "xar_r206_writer_cd_selection").select(actual)
    selected["actual_consumer_result"] = result_pin
    selection_pin = write(session.control / "C-D-WRITERS.actual.json", selected)
    final = {"status": selected["status"], "observer_returncode": code,
             "actual_consumer_result": result_pin, "c_d_selection": selection_pin,
             "cleanup_proved": actual["cleanup_proved"], "terminal": actual["terminal"],
             "military_attribution": "unclosed", "paid_maintenance_raw": None}
    write(session.control / "OBSERVER-FINAL.actual.json", final)
    return final


def native_argv_matches(cfg,watch,admission):
    ordinary=cfg["watch"].get("owner_binding_mode")=="native_campaign_owned_no_load_v2"
    tail=["--ordinary-null-owner-binding"] if ordinary else []
    if ordinary:
        need(admission.get("schema")=="xar.maintenance.writer_pc.future-admission.v2"
             and cfg["watch"]["expected"]["episode"] is None
             and admission.get("expected_episode") is None
             and admission.get("owner_binding",{}).get("mode")=="native_campaign_owned_no_load_v2",
             "Explicit v2 ordinary admission required")
    else:
        need(admission.get("schema")=="xar.maintenance.writer_pc.future-admission.v1",
             "Legacy Root driver requires v1 admission")
    return admission["argv"]==[str(Path(cfg["watch"]["build_dir"]) / "maintenance_writer_cold_observer.exe"),
        "--enable-ck3-12004-data-watch","--fixture-meta",str(watch / "CURRENT-RAW-ADMISSION.meta.txt"),
        "--timeout-ms","30000","--raw",str(watch / "writer.raw.ndjson"),
        "--ready",str(watch / "writer.ready.json"),"--expected-hits","128",
        "--machine-id",cfg["watch"]["expected"]["machine"]]+tail


def observe_prepared(config_pin):
    """Root same-process entry. Return (session, result); retain module if cleanup pending."""
    cfg = load_config(config_pin)
    rt = RootRuntime(cfg)
    control = Path(cfg["control_root"]).resolve()
    need(control.is_dir() and str(control) not in SESSIONS, "Prepared new control attempt required")
    card = read_pin(pin(control / "ROOT-ARGV.actual.json"))
    prepared = read_pin(pin(control / "PREPARE-RESULT.actual.json"))
    need(prepared.get("returncode") == 0 and prepared.get("observer_started") is False
         and same_pin(prepared.get("config"), config_pin), "Exact successful prepare-only result required")
    watch = Path(cfg["watch"]["watch_output_root"]).resolve()
    admission = read_pin(pin(watch / "ADMISSION.actual.json"))
    need(same_pin(prepared.get("admission"), pin(watch / "ADMISSION.actual.json")),
         "Prepared admission bytes changed")
    need(admission.get("prepare_only") is True, "Actual prepare-only admission required")
    # Reuse existing strict original-cash/snapshot binding before starting the watcher.
    consumer_path = rt.repo / RESEARCH / "consume_writer_actual.py"
    consumer = load_module(pin(consumer_path), "xar_r206_writer_actual_consumer")
    consumer.configure(rt.repo)
    cash_bytes = Path(cfg["watch"]["cash_response"]).read_bytes()
    before_bytes = Path(cfg["watch"]["before_response"]).read_bytes()
    consumer.bind_inputs(admission, cash_bytes, before_bytes)
    original_cash = json.loads(cash_bytes.decode("utf-8-sig"))["body"]
    original_session = original_cash["war_payment_observations_v1"]["current_session"]
    admission["_driver_entry_session"] = {key: original_session[key] for key in (
        "pid", "process_create_time_100ns", "connection_generation", "loaded_game_epoch",
        "controlled_window_id", "same_owned_process_no_load_window", "game_state_identity_witness",
        "player_character_full_id")}
    need(admission["expected_root_identity"] == {
        "pid": cfg["watch"]["expected"]["pid"],
        "process_create_time_100ns": cfg["watch"]["expected"]["created"],
        "connection_generation": cfg["watch"]["expected"]["generation"],
        "controlled_window_id": cfg["watch"]["expected"]["window"],
        "player_character_full_id": cfg["watch"]["expected"]["character_id"]},
        "Prepared independent Root identity differs")
    need(admission["expected_payment_epoch"] == cfg["watch"]["expected"]["epoch"]
         and admission["expected_episode"] == cfg["watch"]["expected"]["episode"], "Prepared epoch/episode differs")
    argv = admission["argv"]
    need(native_argv_matches(cfg,watch,admission),"Exact versioned observer argv differs")
    rt.guard()
    write(control / "observer-start.once.json", {"at_utc": stamp(), "config": config_pin,
                                              "argv": argv, "unknown_start_never_replayed": True})
    out, err = (control / "observer.stdout").open("xb"), (control / "observer.stderr").open("xb")
    # A Popen exception leaves the claim intact. It is never silently retried.
    started_ns = time.monotonic_ns()
    try:
        proc = subprocess.Popen(argv, stdout=out, stderr=err,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except BaseException as exc:
        out.close()
        err.close()
        write(control / "OBSERVER-START-UNKNOWN.actual.json", {"at_utc": stamp(),
            "error": type(exc).__name__ + ": " + str(exc), "do_not_relaunch": True})
        raise
    session = Session(cfg, config_pin, rt, card, admission, control, proc, out, err, started_ns)
    SESSIONS[str(control)] = session
    primary, day = None, None
    prefix = cfg["request_prefix"]
    try:
        session.ready = await_ready(proc, watch / "writer.ready.json")
        write(control / "READY-OBSERVED.actual.json", session.ready)
        before, before_pin = rt.request(prefix + "-before", "ck3_take_snapshot", {"include_native_command_history": False})
        check_frame(before, cfg["watch"]["expected"])
        cash, cash_pin = rt.request(prefix + "-cash-before", "ck3_query_war_cash_current_resources_private_v1",
                                    {"expected_revision": before["revision"], "payment_sampling": "query"})
        before_window = check_cash(cash, before, admission, rt.repo)
        need(proc.poll() is None and time.monotonic_ns() - started_ns < 18_000_000_000,
             "Insufficient live finite watch headroom; no day submitted")
        need(before["date_raw"] + 24 <= rt.c["expected_start_date_raw"] + rt.c["maximum_days"] * 24,
             "The one day exceeds actual scene day admission")
        args = {"step": "life-advance-one-day", "expected_revision": None}
        write(control / "day.once.json", {"at_utc": stamp(), "request_id": prefix + "-day-once",
                                        "tool": "ck3_execute_step", "arguments": args,
                                        "before": before_pin, "cash_before": cash_pin,
                                        "unknown_result_never_replayed": True})
        step, step_pin, step_error = None, None, None
        try:
            step, step_pin = rt.request(prefix + "-day-once", "ck3_execute_step", args)
        except BaseException as exc:
            step_error = type(exc).__name__ + ": " + str(exc)
        # This independent read happens even after an unknown original day result.
        after, after_pin = rt.request(prefix + "-independent-after", "ck3_take_snapshot",
                                      {"include_native_command_history": False})
        check_frame(after, cfg["watch"]["expected"], after=True)
        contract = check_clock(step, before, after) if step is not None else None
        after_cash, after_cash_pin = rt.request(prefix + "-cash-after", "ck3_query_war_cash_current_resources_private_v1",
                                                {"expected_revision": after["revision"], "payment_sampling": "query"})
        after_window = check_cash(after_cash, after, admission, rt.repo)
        day = {"before": before_pin, "cash_before": cash_pin, "step": step_pin,
               "after": after_pin, "cash_after": after_cash_pin,
               "before_window": before_window, "after_window": after_window,
               "original_step_error": step_error, "composite_and_independent_contract": contract,
               "exact_day_qualified": contract is not None and step_error is None,
               "no_enable_clear_or_additional_Arm_Resume": True}
        write(control / "DAY-RESULT.actual.json", day)
        if step_error:
            raise RuntimeError("Original day remains unknown; no replay: " + step_error)
    except BaseException as exc:
        primary = type(exc).__name__ + ": " + str(exc)
        write(control / "PRIMARY-ERROR.actual.json", {"at_utc": stamp(), "error": primary,
                                                   "no_action_or_observer_retry": True})
    try:
        observer = finalize(session)
    except BaseException as exc:
        observer = {"status": "FINALIZATION_OR_CONSUMER_UNQUALIFIED", "cleanup_proved": False,
                    "error": type(exc).__name__ + ": " + str(exc),
                    "process_id": proc.pid, "process_exitcode": proc.poll(), "no_force_kill": True}
    result = {"at_utc": stamp(), "config": config_pin, "primary_error": primary,
              "day": day, "observer": observer, "single_process_handle_retained": True,
              "safe_to_begin_normal_close": observer.get("cleanup_proved") is True,
              "sampling_state": "preserved_unmodified_Root_collect_and_OFF_before_game_exit",
              "known_producer": False, "maintenance_attribution": "unclosed", "paid_maintenance_raw": None}
    write(control / "ROOT-WINDOW-RESULT.actual.json", result)
    return session, result
