"""Portable host fixtures; actual A34 metadata projections, no disk fixture/OS.
The original capture launch return expression is compiled from repository source.
Only path namespaces and consequential pins are rebased in RAM.
"""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PureWindowsPath
import unittest
from typing import Literal, Never
from tools.g2_saved_campaign import current_saved_recording_only_owner_v1 as c

ACTUAL: c.Obj = c.obj(json.loads(r'''{"projections":{"old_job":{"session_id":"c1596f4f-6c7f-475c-96d9-d3cde51112de","pid":265360,"game_creation_filetime":134370765451291729,"profile_path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\ROOT-OBS-PROFILE-C23.json","profile_sha256":"586767d8ae87dc694cdc89d46def25cc0bf5c57eb2936f390a04592344850884"},"old_profile":{"profile_name":"ManagedWindowCapture-4e5c020462c34dc2a61321c200698a63","collection_name":"ManagedWindowCapture-4e5c020462c34dc2a61321c200698a63","continuous":true,"deadline_utc":null,"max_output_bytes":null,"recording_root":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\recordings","storage_review_at_utc":"2026-10-21T20:30:00+00:00"},"profile":{"profile_name":"ManagedWindowCapture-57cc247bb7a14440bc937c6ef4d30524","collection_name":"ManagedWindowCapture-57cc247bb7a14440bc937c6ef4d30524","continuous":true,"deadline_utc":null,"max_output_bytes":null,"recording_root":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\recordings","storage_review_at_utc":"2026-10-21T20:30:00+00:00"},"old_obs_closed":{"schema":"xar.root-owned-OBS-close-once/v1","machine_id":"xenoamess-full-tower-eb9d2c1186","observed_at_utc":"2026-10-21T17:26:16.020273+00:00","pid":46880,"creation_filetime":"134370765893814181","hwnd":"140776280","image":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\obs-portable\\bin\\64bit\\obs64.exe","original_launch_ref":{"path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\recordings\\c1596f4f-6c7f-475c-96d9-d3cde51112de\\obs-launch.json","bytes":977,"sha256":"82eaaa8950ca2f5997dbeeb490affd7f86d2515dc17b48798acaaed2f095d7ee"},"original_worker_failed_ref":{"path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\recordings\\c1596f4f-6c7f-475c-96d9-d3cde51112de\\failed.json","bytes":4298,"sha256":"f1d5fd318e931ed3b402e834de4f2593389b1394a994407a92a291f7e903784d"},"method":"single_WM_CLOSE_with_held_process_handle","StopRecord_calls":0,"Game_publisher_personalOBS_calls":0,"close_request_posted":true,"wait_result":0,"process_exit_observed":true,"exit_code":0,"normal_zero_exit":true,"submission_count":1,"repeated_close_calls":0},"old_closed_state":{"machine_id":"xenoamess-full-tower-eb9d2c1186","observed_at_utc":"2026-10-21T17:28:58.314738+00:00","status":"SAME_GAME_AND_PUBLISHER_LIVE_OLD_WORKER_AND_OBS_CLOSED","Game":{"pid":265360,"creation_filetime":"134370765451291729","executable":"Z:\\SteamLibrary\\steamapps\\common\\Crusader Kings III\\binaries\\ck3.exe"},"publisher":{"pid":268544,"creation_filetime":"134370765872090736","executable":"C:\\Users\\xenoa\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"},"old_worker":{"pid":193592,"creation_filetime":"134370765876099472","kernel_exit_observed":true,"wait_result":0,"exit_code":1},"old_OBS_closed":{"path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c23-source23-native30-cold100\\current-saved-a34-runtime-prep01\\ROOT-A34-OLD-OBS-CLOSE-RESULT01.json","bytes":1335,"sha256":"e6427aa82fc8a517c9dbec7660f0ae3abc66efcba9cd303e0156b8069698938d"},"old_request":{"path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\ROOT-OBS-RECORDING-REQUESTED-C23.json","bytes":577,"sha256":"38ada4326a8498b4b6b75ccafeabcdad9a99caa45c1b861e27e9f800148d3bfe"},"publisher_started":{"path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\decision-text-publisher-c23\\STARTED.json","bytes":2225,"sha256":"a12325a0b9477d7dd2d463487c3dfc0bb47eda860a10b0a802910b0d06acada6"},"Game_SDK_Action_calls":0},"old_obs_launch":{"pid":46880,"creation_filetime":134370765893814181,"executable":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\obs-portable\\bin\\64bit\\obs64.exe"},"old_request":{"schema":"xar.ck3.obs-window-capture.v3","session_id":"c1596f4f-6c7f-475c-96d9-d3cde51112de","worker_pid":193592,"worker_creation_filetime":134370765876099472,"worker_executable":"C:\\Users\\xenoa\\AppData\\Local\\Programs\\Python\\Python313\\python.exe","receipt_root":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a34\\recordings\\c1596f4f-6c7f-475c-96d9-d3cde51112de","state":"requested","runtime_qualified":false,"capture_admission_stage":"saved_map","map_ready_claimed":false,"generation":"Source28-A15"},"launch":{"pid":265360,"creation_filetime":134370765451291729},"placement":{"pid":265360,"creation_filetime":134370765451291729,"hwnd":98242022,"status":"GREEN","target_desktop_id":"964b3ff9-3cf7-4ba9-881b-47444f31cfbe"}},"actual_input_pins":{"old_job":{"bytes":16855,"sha256":"9ffba3c7775d069fde2a288acae02402e5e05fb825dbdd1a45211e90f913331a"},"old_profile":{"bytes":5330,"sha256":"586767d8ae87dc694cdc89d46def25cc0bf5c57eb2936f390a04592344850884"},"profile":{"bytes":5683,"sha256":"7712d7192ce0cb78082a96625d46812e313d4881ec6f5df0cf106e3ad355da60"},"old_obs_closed":{"bytes":1335,"sha256":"e6427aa82fc8a517c9dbec7660f0ae3abc66efcba9cd303e0156b8069698938d"},"old_closed_state":{"bytes":1684,"sha256":"90ecdb890b63d39a9a4c01c94b5377b09428f7b1ac1b15ebadde9aed6a239416"},"old_obs_launch":{"bytes":977,"sha256":"82eaaa8950ca2f5997dbeeb490affd7f86d2515dc17b48798acaaed2f095d7ee"},"old_request":{"bytes":577,"sha256":"38ada4326a8498b4b6b75ccafeabcdad9a99caa45c1b861e27e9f800148d3bfe"},"launch":{"bytes":6126,"sha256":"9c5db3b675d4d930da3b243d5d2c4980e7c59a72ec0ed4bf6f5d7feeac58dcee"},"placement":{"bytes":3691,"sha256":"ee9aebdaa35800326d8a0872a822b552d84cfdac9d235b371abc417cfa3f4f20"}}}'''))
BASE = Path(__file__).resolve().parent / "_recording_only_fixture_not_created"
NATIVE_ROOT = "D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime-a34"


def clone(value: object) -> c.Obj:
    return c.obj(json.loads(json.dumps(value)))


def rebase(value: object) -> c.Json:
    if isinstance(value, dict):
        return {c.text(k): rebase(v) for k, v in value.items()}
    if isinstance(value, list):
        return [rebase(v) for v in value]
    if isinstance(value, str) and len(value) > 2 and value[1] == ":":
        path = PureWindowsPath(value).as_posix()
        if path.startswith(NATIVE_ROOT):
            return str(BASE / "runtime" / path[len(NATIVE_ROOT):].lstrip("/"))
        return str(BASE / "images" / PureWindowsPath(value).name)
    return c.json_value(value)


def capture_return(session: str, root: Path, image: str) -> object:
    path = Path(__file__).resolve().parents[1] / "ck3_obs_capture.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "launch_recording"]
    statement = functions[0].body[-1]
    if not isinstance(statement, ast.Return) or statement.value is None:
        raise AssertionError("actual capture producer return changed")
    expression = ast.Expression(statement.value)
    # The producer's original terminal expression, with fake subprocess results.
    return eval(compile(expression, str(path) + ":launch-return", "eval"), {}, {
        "SCHEMA": "xar.ck3.obs-window-capture.v3", "session": session,
        "worker": type("FakeSubprocess", (), {"pid": 600001})(),
        "worker_birth": 134370765999999999, "worker_executable": image, "root": root})


class Lease:
    def __init__(self, owner: Resources) -> None:
        self.owner = owner
    def wait_exit(self) -> int:
        self.owner.events.append("wait")
        self.owner.waited = True
        return self.owner.exit_code
    def close(self) -> None:
        if not self.owner.waited:
            raise AssertionError("released before actual wait")
        self.owner.events.append("release")


class Resources:
    def __init__(self) -> None:
        self.machine_id = "xenoamess-full-tower-eb9d2c1186"
        self.files: dict[str, bytes] = {}
        self.ids: dict[str, str] = {}
        self.events: list[str] = []
        self.waited = False
        self.exit_code = 0
        self.failure: str | None = None
        self.rename_count = 0
    def put(self, path: str, raw: bytes) -> c.RefV1:
        self.files[path] = raw
        self.ids[path] = str(1000 + len(self.ids))
        return c.RefV1(path, len(raw), hashlib.sha256(raw).hexdigest())
    def body(self, path: str, body: c.Obj) -> c.RefV1:
        return self.put(path, json.dumps(body).encode())
    def exact(self, reference: c.RefV1) -> bytes:
        raw = self.files[reference.path]
        if len(raw) != reference.bytes or hashlib.sha256(raw).hexdigest() != reference.sha256:
            raise ValueError("exact fake source")
        return raw
    def absent(self, path: str) -> bool:
        return path not in self.files
    def write_new(self, path: str, value: c.Obj) -> None:
        self.events.append("write:" + Path(path).name)
        if self.failure == path:
            raise OSError("injected publication failure")
        if path in self.files:
            raise FileExistsError(path)
        self.body(path, value)
    def rename_exact(self, before: c.RefV1, archive: str) -> tuple[c.RefV1, str, str]:
        self.rename_count += 1
        self.events.append("rename")
        if self.failure == archive:
            raise OSError("injected archive failure")
        raw = self.exact(before)
        if archive in self.files:
            raise FileExistsError(archive)
        identity = self.ids.pop(before.path)
        del self.files[before.path]
        self.files[archive] = raw
        self.ids[archive] = identity
        return c.RefV1(archive, before.bytes, before.sha256), identity, identity
    def require_live(self, identity: c.ProcessV1) -> None:
        self.events.append("live:" + str(identity.pid))
    def retain_worker(self, identity: c.ProcessV1) -> Lease:
        if self.failure == "retain":
            raise OSError("retention failure")
        self.events.append("retain:" + identity.birth)
        return Lease(self)
    def hold_unretained_worker(self, identity: c.ProcessV1, reason: str) -> Never:
        self.events.append("hold")
        raise RuntimeError("explicit custody unknown HOLD")


class Publisher:
    def __init__(self, path: str) -> None:
        self.__file__ = path
        self.calls = 0
    def read_text_binding(self, reference: c.Obj, *, game: c.Obj) -> object:
        self.calls += 1
        return {"validated": True}


class Capture:
    def __init__(self, path: str, publisher: Publisher) -> None:
        self.__file__ = path
        self.publisher = publisher
        self.calls = 0
        self.bad_request = False
    def decision_publisher_api(self) -> object:
        return self.publisher
    def validate_profile(self, value: object) -> object:
        profile = c.obj(value)
        if profile.get("continuous") is not True:
            raise ValueError("continuous")
        return None
    def _generation_helpers(self) -> object:
        raise AssertionError("fake resources retain the fake kernel lease")
    def launch_recording(self, profile_path: Path, recording_root: Path, pid: int,
                         hwnd: int, seconds: None, *, launch_receipt: Path, ffprobe: Path,
                         placement_receipt: Path, decision_publisher_receipt: Path,
                         continuous: Literal[True]) -> object:
        self.calls += 1
        session = "0f1d39bf-31c0-412e-b611-67bb53b1f401"
        value = c.obj(capture_return(session, recording_root / session,
                                    str(BASE / "images" / "python.exe")))
        if self.bad_request:
            value["worker_creation_filetime"] = True
        return value
    def read_capture_closed_receipt(self, receipt_root: Path, *, session_id: str,
                                   game_pid: int, game_creation_filetime: int,
                                   recording_worker_pid: int, recording_root: Path) -> object:
        return {"schema": "fake-validated-capture-close", "session_id": session_id}


class Fixture:
    def __init__(self) -> None:
        self.resources = Resources()
        r = self.resources
        projected = c.obj(rebase(ACTUAL["projections"]))
        self.n = BASE / "runtime"
        self.attempt = BASE / "attempt"
        self.evidence: c.Obj = {}
        def add(role: str, path: Path, value: c.Obj) -> c.RefV1:
            reference = r.body(str(path), value)
            self.evidence[role] = reference.wire()
            return reference
        state = c.obj(projected["old_closed_state"])
        game, publisher = c.obj(state["Game"]), c.obj(state["publisher"])
        old_request = c.obj(projected["old_request"])
        old_worker: c.Obj = {"pid": old_request["worker_pid"],
            "creation_filetime": str(old_request["worker_creation_filetime"]),
            "executable": old_request["worker_executable"]}
        old_obs = c.obj(projected["old_obs_launch"])
        obs_identity: c.Obj = {"pid": old_obs["pid"],
            "creation_filetime": str(old_obs["creation_filetime"]),
            "executable": old_obs["executable"]}
        sid = c.text(old_request["session_id"])
        old_root = self.n / "recordings" / sid
        old_profile = add("old_profile", self.n / "ROOT-OBS-PROFILE-C23.json",
                          c.obj(projected["old_profile"]))
        job = c.obj(projected["old_job"])
        job.update(profile_path=old_profile.path, profile_sha256=old_profile.sha256)
        add("old_job", old_root / "job.json", job)
        failed = add("old_failed", old_root / "failed.json", {"actual_projection": "WS timeout/watch.finish"})
        old_launch = add("old_obs_launch", old_root / "obs-launch.json", old_obs)
        closed = c.obj(projected["old_obs_closed"])
        closed.update(original_launch_ref=old_launch.wire(), original_worker_failed_ref=failed.wire())
        obs_close = add("old_obs_closed", self.attempt / "old-OBS-close.json", closed)
        started = add("publisher_started", self.n / "decision-text-publisher-c23" / "STARTED.json",
                      {"publisher": publisher, "game": game})
        requested = r.body(str(self.n / "ROOT-OBS-RECORDING-REQUESTED-C23.json"), old_request)
        current = r.body(str(self.n / "ROOT-CURRENT-OBS-RECORDING-REQUESTED-C23.json"), old_request)
        state.update(old_OBS_closed=obs_close.wire(), old_request=requested.wire(),
                     publisher_started=started.wire())
        add("old_closed_state", self.attempt / "old-closed-state.json", state)
        add("launch", self.n / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", c.obj(projected["launch"]))
        add("placement", self.n / "ROOT-GAME-PLACEMENT-C23.json", c.obj(projected["placement"]))
        add("profile", self.attempt / "OBS-PROFILE.json", c.obj(projected["profile"]))
        source = Path(c.__file__).resolve()
        self.evidence["controller"] = r.put(str(source), source.read_bytes()).wire()
        for role, filename in (("capture", "capture.py"), ("publisher_api", "publisher.py")):
            self.evidence[role] = r.put(str(BASE / filename), b"# fake loaded source\n").wire()
        self.publisher = Publisher(str(BASE / "publisher.py"))
        self.capture = Capture(str(BASE / "capture.py"), self.publisher)
        self.raw: c.Obj = {
            "schema": c.SCHEMA, "machine_id": r.machine_id,
            "admission_id": "8c013b72-d0dc-4c78-a15a-35cd931a78dc",
            "root_direct_execution_release": True, "runtime_root": str(self.n),
            "attempt_root": str(self.attempt), "recording_root": str(self.n / "recordings"),
            "game": game, "publisher": publisher, "old_worker": old_worker, "old_obs": obs_identity,
            "old_session_id": sid, "generation": "RECORDING_ONLY_TEST",
            "ffprobe": str(BASE / "ffprobe.exe"), "review_at_utc": "2026-10-21T20:30:00+00:00",
            "evidence": self.evidence,
            "requested": {"before": requested.wire(), "archive": str(self.attempt / "old-requested.json")},
            "current": {"before": current.wire(), "archive": str(self.attempt / "old-current.json")},
            "outputs": {k: str(self.attempt / (k + ".json"))
                        for k in ("intent", "archived", "started", "closed")}}
    def run(self) -> c.RecordingOnlyResultV1:
        return c.run_recording_only_owner_v1(c.parse_recording_only_admission_v1(self.raw),
            capture=self.capture, publisher=self.publisher, resources=self.resources,
            now_utc=lambda: datetime(2026, 10, 21, 18, tzinfo=timezone.utc))
    def repin(self, role: str, update: c.Obj) -> None:
        old = c.ref(self.evidence[role])
        body = c.obj(json.loads(self.resources.exact(old)))
        body.update(update)
        self.evidence[role] = self.resources.body(old.path, body).wire()


class RecordingOnlyTests(unittest.TestCase):
    def test_actual_null_profile_and_original_producer_to_canonical_and_owner(self) -> None:
        f = Fixture()
        before = dict(f.resources.files)
        result = f.run()
        self.assertTrue(result.normal_media)
        self.assertEqual(f.capture.calls, 1)
        self.assertEqual(result.worker.birth, "134370765999999999")
        self.assertLess(f.resources.events.index("retain:" + result.worker.birth),
                        f.resources.events.index("rename"))
        self.assertEqual(f.resources.events[-1], "release")
        for key in ("requested", "current"):
            rotation = c.obj(f.raw[key])
            old = c.ref(rotation["before"])
            self.assertEqual(f.resources.files[c.text(rotation["archive"])], before[old.path])
            wire = c.obj(json.loads(f.resources.files[old.path]))
            self.assertIs(type(wire["worker_creation_filetime"]), int)
            self.assertFalse(wire["map_ready_claimed"])
        archive = c.obj(json.loads(f.resources.files[str(f.attempt / "archived.json")]))
        self.assertEqual(archive["requested_source_file_id"], archive["requested_archive_file_id"])
        self.assertEqual(archive["current_source_file_id"], archive["current_archive_file_id"])
        owner = c.obj(json.loads(f.resources.files[str(f.attempt / "started.json")]))
        self.assertIs(type(c.obj(owner["worker"])["creation_filetime"]), str)
        self.assertFalse(owner["pixel_admitted"])
    def test_admission_json_roundtrip_and_wrong_scalar_types(self) -> None:
        f = Fixture()
        parsed = c.parse_recording_only_admission_v1(f.raw)
        self.assertEqual(c.parse_recording_only_admission_v1(clone(parsed.wire())), parsed)
        for value in (True, float(265360)):
            raw = clone(f.raw)
            c.obj(raw["game"])  # Validate without silently modifying a detached clone.
            game = c.obj(raw["game"])
            game["pid"] = value
            raw["game"] = game
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.parse_recording_only_admission_v1(raw)
    def test_missing_null_and_unknown_fields_reject_before_launch(self) -> None:
        for mutation in ("missing", "null", "unknown"):
            f = Fixture()
            if mutation == "missing":
                del f.raw["game"]
            elif mutation == "null":
                f.raw["game"] = None
            else:
                f.raw["alias"] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                f.run()
            self.assertEqual(f.capture.calls, 0)
    def test_continuous_deadline_must_remain_null(self) -> None:
        f = Fixture()
        f.repin("profile", {"deadline_utc": "2026-10-21T20:30:00+00:00"})
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 0)
    def test_review_expiry_rejects_without_launch(self) -> None:
        f = Fixture()
        f.raw["review_at_utc"] = "2026-10-21T17:00:00+00:00"
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 0)
    def test_same_profile_name_is_not_fresh(self) -> None:
        f = Fixture()
        old = c.ref(f.evidence["old_profile"])
        profile = c.obj(json.loads(f.resources.exact(old)))
        f.repin("profile", {"profile_name": profile["profile_name"]})
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 0)
    def test_original_source_drift_rejects_without_launch(self) -> None:
        f = Fixture()
        reference = c.ref(f.evidence["old_failed"])
        f.resources.files[reference.path] += b" "
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 0)
    def test_metadata_failure_waits_for_original_worker_no_retry(self) -> None:
        f = Fixture()
        f.resources.failure = str(f.attempt / "started.json")
        result = f.run()
        self.assertFalse(result.normal_media)
        self.assertIsNotNone(result.metadata_error)
        self.assertEqual(f.capture.calls, 1)
        self.assertTrue(f.resources.waited)
        self.assertEqual(f.resources.events[-1], "release")
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 1)
    def test_partial_archive_is_not_rolled_back_or_relaunched(self) -> None:
        f = Fixture()
        current = c.obj(f.raw["current"])
        f.resources.failure = c.text(current["archive"])
        result = f.run()
        self.assertFalse(result.normal_media)
        self.assertEqual(f.resources.rename_count, 2)
        self.assertTrue(f.resources.waited)
        self.assertEqual(f.capture.calls, 1)
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 1)
    def test_custody_failure_holds_without_canonical_publication(self) -> None:
        f = Fixture()
        before = dict(f.resources.files)
        f.resources.failure = "retain"
        with self.assertRaisesRegex(RuntimeError, "HOLD"):
            f.run()
        self.assertEqual(f.capture.calls, 1)
        self.assertIn("hold", f.resources.events)
        for name in ("requested", "current"):
            old = c.ref(c.obj(f.raw[name])["before"])
            self.assertEqual(f.resources.files[old.path], before[old.path])
    def test_nonzero_worker_does_not_claim_media_success(self) -> None:
        f = Fixture()
        f.resources.exit_code = 1
        result = f.run()
        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.normal_media)
        self.assertIsNone(result.closure)
    def test_legacy_birth_bool_rejected_not_rounded_or_replayed(self) -> None:
        f = Fixture()
        f.capture.bad_request = True
        with self.assertRaises(ValueError):
            f.run()
        self.assertEqual(f.capture.calls, 1)
        self.assertEqual(f.resources.rename_count, 0)


if __name__ == "__main__":
    unittest.main()
