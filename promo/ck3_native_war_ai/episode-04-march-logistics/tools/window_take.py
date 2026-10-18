"""Episode 04 owned CK3 client-window take; parameterized for a public CaseClient.

No game, desktop, SDK or FFmpeg operation occurs on import. The caller owns
CaseClient and the normal game close. This module only owns one raw recorder.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

def bind_repo(repo):
    repo = Path(repo).resolve(strict=True)
    tools = repo / "promo/ck3_native_war_ai/episode-04-march-logistics/tools"
    integration = repo / "promo/ck3_native_war_ai/integration"
    need(tools.is_dir() and integration.is_dir(), "explicit repository recorder sources missing")
    sys.path[:0] = [str(tools), str(integration), str(repo / "tools"),
                    str(repo / "ck3_autonomous_player/src")]
    return repo, tools, integration


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def utc():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    path = Path(path).resolve(strict=True)
    need(path.is_file() and not path.is_symlink(), "regular evidence file required: " + str(path))
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def pinned(actual, expected):
    return isinstance(expected, dict) and all(actual.get(k) == expected.get(k) for k in ("path", "bytes", "sha256"))


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_once(path, value):
    path = Path(path)
    need(path.parent.is_dir(), "receipt parent missing: " + str(path))
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TakeSpec:
    """Frozen actual input references, with no inferred machine/run identity."""

    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve(strict=True)
        c = read(self.config_path)
        need(c.get("schema") == "xar.e04.owned-window-take-input.v1", "window take config schema differs")
        self.machine_id = c["machine_id"]
        self.source_head = c["source_head"]
        self.repo, self.tools, self.integration = bind_repo(c["repo_root"])
        self.scene = Path(c["scene_root"]).resolve()
        self.live = Path(c["run_dir"]).resolve()
        self.keeper_root = Path(c["keeper_root"]).resolve()
        self.screen_task = c["screen_task"]
        self.capacity_ref = c["capacity"]
        self.offline_ref = c["steam_offline_review"]
        self.ffmpeg_ref = c["ffmpeg"]
        self.runtime = Path(c["runtime"]).resolve()
        self.products = Path(c["products"]).resolve()
        self.product_key = c["product_key"]
        self.case_key = c["case_key"]
        self.context = Path(c["context"]).resolve()
        self.prepared = Path(c["prepared"]).resolve()
        self.state_dir = Path(c["state_dir"]).resolve()
        self.raw_root = Path(c["raw_root"]).resolve()
        self.take_id = c["take_id"]
        self.workdir = self.raw_root / self.take_id
        self.output = Path(c["case_output"]).resolve()
        self.ui_output = Path(c["ui_case_output"]).resolve()
        self.query_prefix = c["query_prefix"]
        self.ui_query_prefix = c["ui_query_prefix"]
        self.army_id = c["army_id"]
        self.content_kind = c["content_kind"]
        self.expected_size = c["expected_client_size"]
        self.record_seconds = c["recording_seconds"]
        self.raw_budget_bytes = c["raw_budget_bytes"]
        self.hard_seconds = c["hard_terminal_seconds"]
        self.normal_close_reserve = c["normal_close_reserve_seconds"]
        self.cleanup_reserve = c["cleanup_reserve_seconds"]
        self.min_seconds = c["minimum_recording_seconds"]
        self.observer_result = Path(c["observer_result"]).resolve() if c.get("observer_result") else None
        self.awaiting = Path(c["camera_awaiting"]).resolve() if c.get("camera_awaiting") else None
        self.signal = Path(c["camera_signal"]).resolve() if c.get("camera_signal") else None
        self.label = c["receipt_label"]
        need(all(isinstance(x, str) and x for x in (self.machine_id, self.source_head,
             self.screen_task, self.take_id, self.query_prefix, self.ui_query_prefix, self.label)),
             "explicit nonempty actual identity/take/control labels required")
        need(self.query_prefix != self.ui_query_prefix and
             all(x.replace("-", "").replace("_", "").isalnum() for x in
                 (self.take_id, self.query_prefix, self.ui_query_prefix, self.label)),
             "unique alphanumeric public namespaces required")
        need(self.scene.is_dir() and self.live.is_dir() and self.keeper_root.is_dir() and
             self.raw_root.parent == self.scene and self.output.parent == self.live and
             self.ui_output.parent == self.live and self.output != self.ui_output,
             "actual scene/live/keeper/output placement differs")
        need(self.content_kind in ("army-supply", "map-context") and
             (self.content_kind != "army-supply" or type(self.army_id) is int) and
             len(self.expected_size) == 2 and all(type(x) is int and x >= 360 for x in self.expected_size),
             "explicit shot type/Army ID/even client dimensions required")
        need(all(x % 2 == 0 for x in self.expected_size) and
             type(self.record_seconds) is int and 1 <= self.record_seconds <= 3600 and
             type(self.hard_seconds) is int and self.record_seconds <= self.hard_seconds <= self.record_seconds + 60 and
             type(self.min_seconds) is int and 1 <= self.min_seconds <= self.record_seconds and
             type(self.raw_budget_bytes) is int and self.raw_budget_bytes > 0 and
             type(self.normal_close_reserve) is int and self.normal_close_reserve >= 120 and
             type(self.cleanup_reserve) is int and self.cleanup_reserve >= 120,
             "recording duration/hard deadline/close reserves differ")
        need((self.awaiting is None) == (self.signal is None) and
             (self.awaiting is None or self.awaiting.parent == self.signal.parent == self.live / c["camera_output_name"]),
             "camera coordination paths must be paired in one public output")

    def receipt(self, kind):
        return self.scene / (self.label + "-" + kind + ".actual.json")

    def reserve(self):
        return self.normal_close_reserve + self.cleanup_reserve + 5

    def capacity(self):
        ref = pin(self.capacity_ref["path"])
        need(pinned(ref, self.capacity_ref), "root-adopted capacity exact pin changed")
        c = read(ref["path"])
        b = c["capture_bounds"]
        need(c.get("admitted") is True and c.get("budget_status") == "GREEN" and
             c.get("machine_id") == self.machine_id and c.get("run_id") == self.live.name and
             c.get("source_head") == self.source_head and
             Path(c["scene_root"]).resolve() == self.scene and
             Path(c["raw_workdir"]).resolve() == self.raw_root and
             c["component_ceiling_bytes"]["raw"] == self.raw_budget_bytes and
             b["max_recording_seconds"] == self.record_seconds and
             b["recording_hard_stop_seconds"] == self.hard_seconds and
             b["normal_close_reserve_seconds"] == self.normal_close_reserve and
             b["cleanup_save_reserve_seconds"] == self.cleanup_reserve and
             b["client_only"] is True and
             datetime.now(timezone.utc) < timestamp(c["quota_review_at_utc"]),
             "current Root capacity does not admit this client-only take")
        head = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        need(head == self.source_head, "live source HEAD changed")
        return c, ref

    def admission(self, seconds, client):
        """May run both before and AFTER canonical creates workdir."""
        c, ref = self.capacity()
        b = c["capture_bounds"]
        deadline = timestamp(b["absolute_phase_deadline_utc"])
        room = seconds + self.reserve()
        need(seconds == self.record_seconds and client.remaining() > room and
             (deadline - datetime.now(timezone.utc)).total_seconds() > room,
             "actual hold/purpose lacks recording plus normal close and cleanup")
        client.guard(reserve=self.reserve())
        return {"machine_id": self.machine_id, "run_id": self.live.name,
                "capacity": ref, "seconds": seconds,
                "hold_remaining_seconds": client.remaining(), "normal_close_and_cleanup_reserve_seconds": self.reserve()}


class KeeperView:
    def __init__(self, spec, client):
        self.spec, self.client = spec, client
        self.task_id = client.frozen["screen_task"]

    def require_live(self):
        from ck3_mod_acceptance_keeper import live_lease
        self.client.guard(reserve=self.spec.reserve())
        live_lease(self.client.keeper, self.client.frozen, deadline=time.monotonic() + 10)

    @contextmanager
    def process_create_gate(self):
        self.require_live()
        yield
        self.require_live()


class RunningTake:
    def __init__(self, spec, recorder):
        self.spec, self.recorder = spec, recorder
        self.start_ns = recorder.start_ns
        self.lock = threading.Lock()
        self.finish_requested = False
        self.finish_error = None
        self.timer = threading.Timer(spec.record_seconds, self.finish_once)
        self.timer.daemon = True

    def finish_once(self):
        with self.lock:
            if self.finish_requested:
                return
            self.finish_requested = True
        try:
            self.recorder.finish()
        except BaseException as error:
            self.finish_error = repr(error)
            try:
                self.recorder.abort()
            except BaseException as cleanup:
                self.finish_error += "; abort: " + repr(cleanup)


def owner(spec):
    """Read current public host/keeper and exact CK3 client; no focus/move."""
    from ck3_mod_acceptance_keeper import live_lease
    from capture_recorder import inspect_owned_client
    from ck3_live_run_id import current_machine_id
    need(current_machine_id() == spec.machine_id, "this machine differs from actual take input")
    cap, cap_ref = spec.capacity()
    ready = read(spec.live / "ready-context.json")
    frozen = read(spec.live / "frozen-argv.json")
    need(ready["run_id"] == frozen["run_id"] == spec.live.name and
         frozen["screen_task"] == spec.screen_task and
         frozen["identity_allocation"]["machine_id"] == spec.machine_id and
         Path(ready["keeper_root"]).resolve() == spec.keeper_root and
         Path(frozen["state_dir"]).resolve() == spec.state_dir,
         "current public runtime owner identity differs")
    lease = live_lease(spec.keeper_root, frozen, deadline=time.monotonic() + 10)
    report = read(spec.live / "native-report.json")
    need(report.get("phase") == "hold" and report.get("error") is None and
         not report.get("finished_at") and not report.get("hold_finished_by_control_plan") and
         time.time() + spec.reserve() < report["hold_until_utc_estimated"],
         "public host is not held with normal-close room")
    control = read(spec.state_dir / "control/ck3.json")
    source = inspect_owned_client(control["ck3_pid"])
    need(source["owned_ck3_pid"] == control["ck3_pid"] and
         source["output_size"] == spec.expected_size and not source["occluding_windows"],
         "actual foreground CK3 client differs from planned window size")
    return cap, cap_ref, ready, frozen, lease, report, control, source


def prepare_only(spec, output):
    """Root-only original screenshot and exact CK3 client crop for direct review."""
    import pyautogui
    from PIL import Image
    output = Path(output).resolve()
    need(output.parent == spec.scene and not output.exists(), "fresh scene-local frame directory required")
    cap, cap_ref, _, _, lease, _, control, before = owner(spec)
    picture = pyautogui.screenshot()
    need(list(picture.size) == before["desktop"] == list(pyautogui.size()),
         "desktop geometry changed during original screenshot")
    after = owner(spec)[-1]
    for key in ("owned_ck3_pid", "owned_ck3_create_time", "hwnd", "client_screen_rect", "desktop", "output_size"):
        need(before[key] == after[key], "CK3 client changed while capturing: " + key)
    output.mkdir()
    desktop_file = output / "desktop-original.png"
    client_file = output / "ck3-client-original.png"
    picture.save(desktop_file)
    picture.crop(tuple(before["client_screen_rect"])).save(client_file)
    with Image.open(client_file) as check:
        need(list(check.size) == spec.expected_size, "client crop size differs")
    return write_once(output / "capture.actual.json", {
        "schema": "xar.e04.owned-client-original-frame.v1", "machine_id": spec.machine_id,
        "observed_at_utc": utc(), "run_id": spec.live.name, "source_head": cap["source_head"],
        "capacity": cap_ref, "lease_sequence_observed": lease["lease"]["sequence"],
        "pid": control["ck3_pid"], "source": before,
        "desktop_original": pin(desktop_file), "client_original": pin(client_file),
        "native_snapshot_at_capture": "not queried by screen-only prepare",
        "recording_started": False, "whole_desktop_recorded": False, "video_approved": False})


def review(spec, capture_path, *, content, no_hover):
    """Root directly inspects the original pixels before writing this receipt."""
    need(no_hover and content == spec.content_kind, "actual Root original client content/no-hover review required")
    frame = read(capture_path)
    need(frame.get("schema") == "xar.e04.owned-client-original-frame.v1" and
         frame["machine_id"] == spec.machine_id and frame["run_id"] == spec.live.name,
         "original frame identity differs")
    for key in ("desktop_original", "client_original"):
        need(pinned(pin(frame[key]["path"]), frame[key]), "reviewed original image bytes changed")
    return write_once(Path(capture_path).parent / "ROOT-REVIEW.actual.json", {
        "schema": "xar.e04.owned-client-root-review.v1", "machine_id": spec.machine_id,
        "run_id": spec.live.name, "reviewed_at_utc": utc(), "reviewer": "/root",
        "capture": pin(capture_path), "client_original": frame["client_original"],
        "root_reviewed_window_only": True, "root_reviewed_no_hover": True,
        "content": content, "visual_supply_value_claimed_by_code": False,
        "human_final_video_approval": False})


def fresh_ui(spec, wrapped, frame, actor):
    """Current exact .4 provider can query Army UI but cannot force its pane."""
    if spec.content_kind != "army-supply":
        return {"status": "map-context-only", "army_window_visible_proof": False}
    name = "army-window-current"
    row = wrapped.execute_plan([{"id": name, "tool": "ck3_query_ingame_ui_window_v1",
        "args": {"window_kind": "army", "expected_revision": frame["revision"]},
        "fresh_revision": False}], name)[0]
    need(row.get("ok") is True and not row.get("error"), "native Army UI readback failed; preserve original request")
    value = row["result"]
    need(value.get("window_kind") == "army" and value.get("effective_visible") is True and
         value.get("window_exists") is True and value.get("subject_id_available") is True and
         value.get("current_subject_id") == spec.army_id and
         value.get("owner_character_id_available") is True and value.get("owner_character_id") == actor and
         value.get("verification_pending") is False and value.get("date_raw") == frame["date_raw"] and
         value.get("paused") is True and
         value.get("tree", {}).get("truncated") is False,
         "Army native window is not visibly bound to chosen army; a siege pane is insufficient")
    return {"status": "army-window-visible-native-readback", "army_window_visible_proof": True,
            "public_step_id": row["continuation_public_step_id"], "result": value}


def start(spec, context, client, *, reviewed_frame):
    """Exactly one canonical recorder Start, using a new public query namespace."""
    from capture_recorder import OwnedRecorder, inspect_owned_client
    import recorder_job
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_full_army import FullArmyResultClient
    from ck3_mod_acceptance_recorder import require_no_legacy_blue_overlay

    need(Path(recorder_job.__file__).resolve() == (spec.integration / "recorder_job.py").resolve(strict=True),
         "canonical managed recorder Job dependency differs")
    need(current_machine_id() == spec.machine_id and
         Path(context["run_dir"]).resolve() == spec.live and client.live.resolve() == spec.live,
         "same actual machine/public CaseClient required")
    cap, cap_ref = spec.capacity()
    # This is the sole fresh-workdir check. start_admission runs again AFTER
    # OwnedRecorder creates workdir, so it must never require absence.
    need(not spec.workdir.exists() and not spec.receipt("claim").exists() and
         (spec.signal is None or not spec.signal.exists()),
         "take workdir/claim/signal has already been attempted")
    offline = read(spec.offline_ref["path"])
    need(pinned(pin(spec.offline_ref["path"]), spec.offline_ref) and
         offline.get("machine_id") == spec.machine_id and offline.get("run_id") == spec.live.name and
         offline.get("steam_offline_confirmed") is True and offline.get("direct_image_review") is True,
         "current-machine Steam offline original review missing")
    review_row = read(reviewed_frame)
    need(review_row.get("schema") == "xar.e04.owned-client-root-review.v1" and
         review_row.get("machine_id") == spec.machine_id and review_row.get("run_id") == spec.live.name and
         review_row.get("reviewer") == "/root" and review_row.get("content") == spec.content_kind and
         review_row.get("root_reviewed_window_only") is True and
         review_row.get("root_reviewed_no_hover") is True and
         0 <= (datetime.now(timezone.utc) - timestamp(review_row["reviewed_at_utc"])).total_seconds() <= 120,
         "fresh Root original CK3 client visual review absent")
    frame_ref = review_row["capture"]
    need(pinned(pin(frame_ref["path"]), frame_ref), "reviewed capture receipt changed")
    frame_source = read(frame_ref["path"])
    need(frame_source.get("schema") == "xar.e04.owned-client-original-frame.v1" and
         frame_source["machine_id"] == spec.machine_id and frame_source["run_id"] == spec.live.name and
         pinned(pin(frame_source["client_original"]["path"]), frame_source["client_original"]) and
         pinned(pin(frame_source["desktop_original"]["path"]), frame_source["desktop_original"]) and
         0 <= (datetime.now(timezone.utc) - timestamp(frame_source["observed_at_utc"])).total_seconds() <= 180,
         "Root original frame changed or became stale")
    client.guard(reserve=spec.reserve())
    retained = client.retain_process()
    need(retained["pid"] == frame_source["pid"] and
         retained["create_time"] == frame_source["source"]["owned_ck3_create_time"],
         "retained CK3 PID/create-time differs from reviewed pixels")
    wrapped = FullArmyResultClient(client, prefix=spec.query_prefix)
    native = wrapped.snapshot()
    actor = context["saved_campaign"]["player_id"]
    need(native["map_ready"] is True and native["paused"] is True and
         native["diagnostics"]["bridge_pid"] == retained["pid"] and
         native["played_character"]["character_id"] == actor and
         not native.get("active_event") and not native.get("pending_character_interaction"),
         "fresh paused native map/player/modal identity differs")
    if spec.awaiting:
        awaited = read(spec.awaiting)
        need(awaited.get("machine_id") == spec.machine_id and
             awaited.get("run_id") == spec.live.name and
             awaited.get("bridge_pid") == retained["pid"] and
             awaited.get("date_raw") == native["date_raw"] and
             awaited.get("signal_path") == str(spec.signal) and
             awaited.get("coordination_only") is True,
             "current camera-awaiting checkpoint differs")
    else:
        awaited = None
    ui = fresh_ui(spec, wrapped, native, actor)
    current = inspect_owned_client(retained["pid"], retained["create_time"])
    for key in ("kind", "hwnd", "client_screen_rect", "output_size", "desktop", "owned_ck3_pid"):
        need(current[key] == frame_source["source"][key], "reviewed CK3 client changed: " + key)
    need(current["output_size"] == spec.expected_size and not current["occluding_windows"],
         "owned client is occluded or resized")
    legacy = require_no_legacy_blue_overlay()
    ffmpeg = pin(spec.ffmpeg_ref["path"])
    need(pinned(ffmpeg, spec.ffmpeg_ref), "exact approved FFmpeg binary changed")
    prepared = {"assets_root": str(spec.scene), "machine_id": spec.machine_id,
                "checkpoint": {"source": {"actor_id": actor}}}
    recorder = OwnedRecorder(spec.live, KeeperView(spec, client), spec.offline_ref["path"], prepared,
                            start_admission=lambda seconds: spec.admission(seconds, client))
    claim = write_once(spec.receipt("claim"), {
        "machine_id": spec.machine_id, "observed_at_utc": utc(), "run_id": spec.live.name,
        "config": pin(spec.config_path), "capacity": cap_ref, "offline": spec.offline_ref,
        "review": pin(reviewed_frame), "native_date_raw": native["date_raw"],
        "native_bridge_pid": retained["pid"], "native_army_ui": ui,
        "legacy_blue_overlay": legacy, "one_start_pending": True,
        "business_or_video_approved": False})
    try:
        ready = recorder.handle({"operation": "start", "workdir": str(spec.workdir),
            "ffmpeg": ffmpeg["path"], "ffmpeg_sha256": ffmpeg["sha256"],
            "target_pid": retained["pid"], "source_image": frame_source["desktop_original"]["path"],
            "seconds": spec.record_seconds}, native)
        need(ready.get("state") == "RECORDING" and
             ready["capture_source"]["kind"] == "gdigrab-desktop-client-region" and
             ready["capture_source"]["output_size"] == spec.expected_size,
             "canonical client-only Start is not proved")
        started = write_once(spec.receipt("started"), {
            "machine_id": spec.machine_id, "observed_at_utc": utc(), "run_id": spec.live.name,
            "claim": claim, "canonical_process_ready": pin(spec.workdir / "process-ready.json"),
            "capture_source": ready["capture_source"], "one_ffmpeg_job": True,
            "maximum_recording_seconds": spec.record_seconds,
            "video_or_business_approved": False})
        if awaited is not None:
            signal = {key: awaited[key] for key in ("machine_id", "run_id", "bridge_pid", "date_raw")}
            signal.update(camera_started=True, start_receipt=started)
            write_once(spec.signal, signal)
        take = RunningTake(spec, recorder)
        take.timer.start()
        return take
    except BaseException as error:
        secondary = None
        try:
            recorder.close()
        except BaseException as cleanup:
            secondary = repr(cleanup)
        write_once(spec.receipt("start-failure"), {
            "machine_id": spec.machine_id, "observed_at_utc": utc(), "run_id": spec.live.name,
            "claim": claim, "primary_error": repr(error), "cleanup_error": secondary,
            "recorder": recorder.report(), "same_take_replay_permitted": False,
            "business_or_video_approved": False})
        raise


def stop(take, *, primary_error=None):
    spec = take.spec
    secondary = None
    finish_reason = "primary_error" if primary_error is not None else "timer"
    try:
        if primary_error is None:
            while not take.finish_requested:
                elapsed = (time.monotonic_ns() - take.start_ns) / 1e9
                if spec.observer_result and elapsed >= spec.min_seconds and spec.observer_result.is_file():
                    try:
                        observed = read(spec.observer_result)
                    except (OSError, json.JSONDecodeError):
                        observed = None
                    if isinstance(observed, dict) and observed.get("machine_id") == spec.machine_id:
                        finish_reason = "actual_observer_result_after_minimum_duration"
                        take.timer.cancel()
                        break
                if elapsed >= spec.record_seconds:
                    break
                time.sleep(min(0.25, max(0.01, spec.record_seconds - elapsed)))
        take.finish_once()
        if take.timer.is_alive():
            take.timer.join(timeout=5)
    except BaseException as error:
        secondary = repr(error)
    finally:
        take.timer.cancel()
        try:
            take.recorder.close()
        except BaseException as error:
            secondary = (secondary + "; " if secondary else "") + "close: " + repr(error)
        terminal = take.recorder.report()
        raw_result = spec.workdir / "result.json"
        elapsed = (time.monotonic_ns() - take.start_ns) / 1e9
        result = {"schema": "xar.e04.owned-client-window-take-terminal.v1",
            "machine_id": spec.machine_id, "observed_at_utc": utc(), "run_id": spec.live.name,
            "state": terminal["state"], "capture_source": terminal["capture_source"],
            "recorder_result": pin(raw_result) if raw_result.is_file() else None,
            "primary_action_error": repr(primary_error) if primary_error else None,
            "recorder_finish_error": take.finish_error, "secondary_cleanup_error": secondary,
            "finish_reason": finish_reason, "elapsed_wall_seconds_at_terminal": elapsed,
            "planned_recording_max_seconds": spec.record_seconds,
            "hard_terminal_wall_seconds_met": elapsed <= spec.hard_seconds,
            "actual_observer_result": pin(spec.observer_result) if spec.observer_result and spec.observer_result.is_file() else None,
            "one_actual_ffmpeg_job_no_replay": True, "raw_video_human_approved": False,
            "business_result_inferred_from_video": False}
        receipt = write_once(spec.receipt("film-result"), result)
    return receipt
