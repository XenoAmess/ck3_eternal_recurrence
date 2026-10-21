"""Portable canonical producer/gate/consumer tests with explicit virtual I/O."""
from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Callable, Mapping
import unittest
from unittest.mock import patch

import root_saved_campaign_preflight as visual


def record(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError("fixture producer did not return a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise AssertionError("fixture producer key is not text")
        result[key] = item
    return result


def fixture_root() -> Path:
    return Path(__file__).resolve().parent / "VISUAL-PURE-RAM-NO-FILES"


def pin(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": 1, "sha256": "a" * 64}


def reviewed_values() -> dict[str, object]:
    root = fixture_root()
    job = root / "recordings" / "portable-session"
    at = "2026-10-21T00:01:00+00:00"
    return {
        "schema": "xar.ck3.decision-text-first-frame/v1",
        "machine_id": "portable-test", "status": "GREEN", "stage": "saved_map",
        "reviewer": "/root", "at_utc": at,
        "reviewed_at_utc": "2026-10-21T00:02:00+00:00",
        "game_pid": 1, "game_creation_filetime": 1, "game_creation_date": "portable",
        "recorder_session_id": "portable-session", "recording_job_root": str(job),
        "publisher_started": pin(root / "publisher.json"),
        "frame": {"label": "portable-review", "at_utc": at,
                  "game": pin(job / "game.png"), "scene": pin(job / "scene.png"),
                  "mutable_latest_frame": False},
        "before_selection_game_pixels_reviewed": True,
        "before_selection_decision_pixels_reviewed": True,
        "decision_text_visible": True, "legacy_blue_window_visible": False,
        "Game_map_visible": True, "film_title_visible": False,
        "observed_map_date": "1081-07-31", "observed_pause_banner": True,
        "native_source_dimensions": [2560, 1440], "native_capture_scale": [1, 1],
        "rich_actual_plan_visible": False,
        "initial_waiting_text_is_not_planner_output": True}


def saved_receipt() -> dict[str, object]:
    value = visual.build_saved_map_first_frame_v1(
        reviewed_values(), expected_machine_id="portable-test")
    decoded: object = json.loads(json.dumps(value, allow_nan=False))
    return record(decoded)


def actual_segment_gate(publisher: object) -> visual.SavedCampaignSegmentVerifierV1:
    path = Path(__file__).with_name("decision_text_admission.py")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef)
             and node.name in ("_digest", "verify_segment")]
    if {node.name for node in nodes} != {"_digest", "verify_segment"}:
        raise AssertionError("exact actual segment gate functions required")
    scope: dict[str, object] = {
        "Path": Path, "re": __import__("re"), "publisher": publisher,
        "FIRST_SCHEMA": "xar.ck3.decision-text-first-frame/v1"}
    statements: list[ast.stmt] = list(nodes)
    exec(compile(ast.Module(body=statements, type_ignores=[]), str(path), "exec"), scope)
    value: object = scope.get("verify_segment")
    if not callable(value) or not isinstance(value, visual.SavedCampaignSegmentVerifierV1):
        raise AssertionError("typed actual segment gate required")
    return value


@dataclass
class Args:
    first_frame_admission: Path


@dataclass
class Queue:
    launch: dict[str, object]
    record_job: Path
    args: Args


class Verifier:
    def __init__(self, first: dict[str, object]) -> None:
        self.first = first
        self.job: dict[str, object] = {"session_id": "portable-session"}
        self.calls = 0
        self.override: object = None
        self.use_override = False

    def __call__(
        self, n: Path, r: Path, launch: Mapping[str, object], root: Path,
        first_path: Path, read: visual.SavedCampaignJsonReaderV1,
        aware: Callable[[str], datetime], now: Callable[[], datetime],
    ) -> object:
        self.calls += 1
        if self.use_override:
            return self.override
        return deepcopy(self.job), {}, deepcopy(self.first)


def no_read(path: Path, limit: int = 1048576) -> object:
    raise AssertionError("portable visual test must not read recording assets")


def aware(value: str) -> datetime:
    return datetime.fromisoformat(value)


def environment() -> visual.SavedCampaignVisualEnvV1:
    return {"N": fixture_root(), "R": fixture_root().parent,
            "read": no_read, "aware": aware,
            "now": lambda: datetime(2026, 10, 21, 0, 3, tzinfo=timezone.utc)}


class One(IntEnum):
    VALUE = 1


class VisualTextPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = saved_receipt()
        self.verifier = Verifier(self.first)
        self.queue = Queue({"pid": 1, "creation_filetime": 1},
                           fixture_root() / "recordings" / "portable-session",
                           Args(fixture_root() / "FIRST.json"))
        module = ModuleType("root_continuous_segment_auto_c23")
        setattr(module, "verify_segment", self.verifier)
        self.modules = patch.dict(sys.modules, {module.__name__: module})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def call(self) -> visual.SavedCampaignVisualAdmissionV1:
        return visual.require_saved_campaign_visual(self.queue, environment())

    def test_canonical_builder_roundtrip_and_explicit_review(self) -> None:
        original = deepcopy(self.first)
        self.assertNotIn("decision_overlay_visible", self.first)
        self.assertEqual(self.call(), {
            "recording_session_id": "portable-session",
            "first_frame_admission": str(self.queue.args.first_frame_admission),
            "camera_required": False, "new_business_credit": 0})
        self.assertEqual(self.verifier.calls, 1)
        self.assertEqual(self.first, original)
        wrong = reviewed_values()
        wrong["decision_text_visible"] = False
        with self.assertRaisesRegex(ValueError, "explicit reviewed true"):
            visual.build_saved_map_first_frame_v1(wrong, expected_machine_id="portable-test")

    def test_canonical_fields_missing_null_wrong_and_old_alias(self) -> None:
        for key in ("schema", "stage", "Game_map_visible", "decision_text_visible",
                    "legacy_blue_window_visible"):
            for missing, wrong in ((True, None), (False, None), (False, "true"),
                                   (False, 1), (False, 1.0)):
                with self.subTest(key=key, missing=missing, wrong=wrong):
                    self.verifier.first = deepcopy(self.first)
                    if missing:
                        del self.verifier.first[key]
                    else:
                        self.verifier.first[key] = wrong
                    with self.assertRaises(ValueError):
                        self.call()
        for canonical, wrong_name in (
                ("decision_text_visible", "decision_overlay_visible"),
                ("decision_text_visible", "decisionTextVisible"),
                ("game_pid", "gamePid"),
                ("game_creation_filetime", "gameCreationFiletime")):
            self.verifier.first = deepcopy(self.first)
            del self.verifier.first[canonical]
            self.verifier.first[wrong_name] = True
            with self.subTest(wrong_name=wrong_name), self.assertRaises(ValueError):
                self.call()

    def test_dual_canonical_and_legacy_field_is_rejected(self) -> None:
        for value in (True, False, None):
            self.verifier.first = deepcopy(self.first)
            self.verifier.first["decision_overlay_visible"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.call()

    def test_integer_identity_exact_types_ranges_missing_and_null(self) -> None:
        for owner, key, maximum in (
                ("launch", "pid", 2**32), ("launch", "creation_filetime", 2**64),
                ("first", "game_pid", 2**32), ("first", "game_creation_filetime", 2**64)):
            for missing, wrong in ((True, None), (False, None), (False, True),
                                   (False, False), (False, 1.0), (False, One.VALUE),
                                   (False, "1"), (False, 0), (False, -1),
                                   (False, maximum)):
                self.queue.launch = {"pid": 1, "creation_filetime": 1}
                self.verifier.first = deepcopy(self.first)
                row = self.queue.launch if owner == "launch" else self.verifier.first
                if missing:
                    del row[key]
                else:
                    row[key] = wrong
                before = self.verifier.calls
                with self.subTest(owner=owner, key=key, wrong=wrong), self.assertRaises(ValueError):
                    self.call()
                self.assertEqual(self.verifier.calls - before, 0 if owner == "launch" else 1)
        self.queue.launch = {"pid": 2**32 - 1, "creation_filetime": 2**64 - 1}
        self.verifier.first.update(game_pid=2**32 - 1, game_creation_filetime=2**64 - 1)
        self.assertEqual(self.call()["new_business_credit"], 0)

    def test_review_and_recording_identity_required(self) -> None:
        for key in ("reviewer", "recorder_session_id"):
            for missing, wrong in ((True, None), (False, None), (False, ""),
                                   (False, False), (False, 1), (False, "foreign")):
                self.verifier.first = deepcopy(self.first)
                if missing:
                    del self.verifier.first[key]
                else:
                    self.verifier.first[key] = wrong
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    self.call()
        for value in (None, "", False, 1):
            self.verifier.first = deepcopy(self.first)
            self.verifier.job = {"session_id": value}
            with self.subTest(session_id=value), self.assertRaises(ValueError):
                self.call()
        self.verifier.job = {"session_id": "portable-session"}
        self.verifier.first = deepcopy(self.first)
        self.verifier.first["reviewer"] = "automatic_text_continuity"
        for key in ("schema", "stage", "Game_map_visible", "decision_text_visible",
                    "legacy_blue_window_visible"):
            del self.verifier.first[key]
        self.assertEqual(self.call()["recording_session_id"], "portable-session")

    def test_external_python_return_shape_is_checked(self) -> None:
        self.verifier.use_override = True
        values: tuple[object, ...] = (
            None, [], {}, ({}, {}), ({}, {}, {}, {}),
            ([], {}, self.first), (self.verifier.job, {}, []))
        for value in values:
            self.verifier.override = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.call()


    def test_external_verifier_requires_a_callable(self) -> None:
        module = ModuleType("root_continuous_segment_auto_c23")
        setattr(module, "verify_segment", SimpleNamespace(__call__=None))
        with patch.dict(sys.modules, {module.__name__: module}):
            with self.assertRaisesRegex(ValueError, "C23 segment verifier"):
                self.call()


    def test_real_builder_actual_segment_gate_and_consumer(self) -> None:
        root, job_root = fixture_root(), self.queue.record_job
        launch: dict[str, object] = {
            "pid": 1, "creation_filetime": 1, "creation_date": "portable", "pipe": "pipe"}
        self.queue.launch = launch
        bound: dict[str, object] = {"machine_id": "portable-test", "decision_text_file": str(root / "decision.txt")}
        policy = {"legacy_blue_overlay_retired": True, "legacy_window_count_at_start": 0}
        storage = {"disk_reserve_bytes": 1, "admission_path": str(root / "STORAGE-ADMISSION.json"),
                   "admission_sha256": "a" * 64, "approved_output_roots": [str(root)]}
        job: dict[str, object] = {
            "continuous": True, "pid": 1, "game_creation_filetime": 1,
            "hwnd": 3, "desktop_id": "desk", "launch": launch,
            "receipt_root": str(job_root), "capture_mode": "game_decision_text",
            "decision_text_publisher": bound, "decision_text_file": bound["decision_text_file"],
            "decision_text_publisher_receipt": self.first["publisher_started"],
            "storage": storage, "session_id": "portable-session",
            "decision_display_policy": policy, "recording_root": str(job_root)}
        started = {
            "state": "recording", "game_pid": 1, "game_creation_filetime": 1,
            "capture_mode": "game_decision_text", "decision_source": True,
            "decision_text_publisher": bound, "decision_display_policy": policy,
            "decision_settings": {"read_from_file": True, "file": bound["decision_text_file"]},
            "at_utc": "2026-10-21T00:00:00+00:00"}
        rows: dict[Path, object] = {
            job_root / "job.json": job, job_root / "started.json": started,
            self.queue.args.first_frame_admission: self.first,
            root / "STORAGE-ADMISSION.json": {
                "status": "ADMITTED", "machine_id": "portable-test",
                "approved_output_roots": [str(root)]}}
        pins: dict[Path, dict[str, object]] = {
            root / "STORAGE-ADMISSION.json": pin(root / "STORAGE-ADMISSION.json")}
        frame = record(self.first["frame"])
        for key in ("game", "scene"):
            item = record(frame[key])
            path = item["path"]
            if not isinstance(path, str):
                raise AssertionError("fixture frame path required")
            pins[Path(path)] = item
        seen: list[Path] = []

        def memory_read(path: Path, limit: int = 1048576) -> object:
            return deepcopy(rows[path])

        def memory_pin(path: Path, limit: int) -> dict[str, object]:
            seen.append(path)
            return deepcopy(pins[path])

        def memory_binding(reference: object, *, game: object) -> dict[str, object]:
            self.assertEqual(reference, self.first["publisher_started"])
            self.assertEqual(game, {"pid": 1, "creation_filetime": 1, "hwnd": 3, "desktop_id": "desk"})
            return bound

        def no_terminal(path: Path) -> bool:
            self.assertEqual(path.parent, job_root)
            self.assertIn(path.name, ("failed.json", "completed.json", "closed-file-probe.json", "capture_closed.json"))
            return False

        gate = actual_segment_gate(SimpleNamespace(pin=memory_pin, read_text_binding=memory_binding))
        module = ModuleType("root_continuous_segment_auto_c23")
        setattr(module, "verify_segment", gate)
        env = environment()
        env["read"] = memory_read
        with patch.dict(sys.modules, {module.__name__: module}), patch.object(Path, "exists", new=no_terminal):
            self.assertEqual(visual.require_saved_campaign_visual(self.queue, env)["new_business_credit"], 0)
            self.assertIn(job_root / "game.png", seen)
            self.assertIn(job_root / "scene.png", seen)
            self.first.update(stage="frontend", frontend_visible=True)
            with self.assertRaisesRegex(ValueError, "Game map and decision text"):
                visual.require_saved_campaign_visual(self.queue, env)
            self.first["stage"] = "saved_map"
            del self.first["frontend_visible"]
            changed = dict(pins[job_root / "game.png"])
            changed["bytes"] = 2
            pins[job_root / "game.png"] = changed
            with self.assertRaisesRegex(ValueError, "Root-reviewed frame changed"):
                visual.require_saved_campaign_visual(self.queue, env)

    def test_builder_missing_null_types_and_roundtrip(self) -> None:
        original = reviewed_values()
        for key in original:
            for missing in (True, False):
                row = deepcopy(original)
                if missing:
                    del row[key]
                else:
                    row[key] = None
                with self.subTest(key=key, missing=missing), self.assertRaises(ValueError):
                    visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        for key in ("game_pid", "game_creation_filetime"):
            for wrong in (True, False, 1.0, One.VALUE, "1", 0, -1):
                row = deepcopy(original)
                row[key] = wrong
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        row = deepcopy(original)
        row["decision_overlay_visible"] = row.pop("decision_text_visible")
        with self.assertRaises(ValueError):
            visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        built = visual.build_saved_map_first_frame_v1(original, expected_machine_id="portable-test")
        again: object = json.loads(json.dumps(built, allow_nan=False))
        self.assertEqual(visual.build_saved_map_first_frame_v1(again, expected_machine_id="portable-test"), built)
        self.assertEqual(original, reviewed_values())


    def test_builder_nested_paths_flags_and_pin_integer_domains(self) -> None:
        original = reviewed_values()
        for key in ("before_selection_game_pixels_reviewed",
                    "before_selection_decision_pixels_reviewed", "decision_text_visible",
                    "Game_map_visible", "initial_waiting_text_is_not_planner_output"):
            for wrong in (False, 1, 1.0, "true"):
                row = deepcopy(original)
                row[key] = wrong
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        for key in ("legacy_blue_window_visible", "film_title_visible"):
            for wrong in (True, 0, 0.0, "false"):
                row = deepcopy(original)
                row[key] = wrong
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        for wrong in (True, 1.0, One.VALUE, "1", 0, -1, 2**53):
            row = deepcopy(original)
            frame = record(row["frame"])
            game = record(frame["game"])
            game["bytes"] = wrong
            frame["game"] = game
            row["frame"] = frame
            with self.subTest(bytes=wrong), self.assertRaises(ValueError):
                visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")
        row = deepcopy(original)
        frame = record(row["frame"])
        game = record(frame["game"])
        job = row["recording_job_root"]
        if not isinstance(job, str):
            raise AssertionError("fixture recording root required")
        game["path"] = str(Path(job) / ".." / "escaped.png")
        frame["game"] = game
        row["frame"] = frame
        with self.assertRaisesRegex(ValueError, "absolute JSON path"):
            visual.build_saved_map_first_frame_v1(row, expected_machine_id="portable-test")

    def test_recovery_allowlist_uses_the_same_canonical_diagnostic(self) -> None:
        filename = visual.__file__
        if not isinstance(filename, str):
            raise AssertionError("public source filename required")
        path = Path(filename)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "qualify_zero_rpc_preflight")
        messages = {node.value for node in ast.walk(fn)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertIn("saved campaign needs actual reviewed Game map and decision text", messages)
        self.assertNotIn("saved campaign needs actual reviewed Game map and decision overlay", messages)


if __name__ == "__main__":
    unittest.main()
