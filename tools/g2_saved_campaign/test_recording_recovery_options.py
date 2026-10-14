"""Synthetic CLI/stop-marker tests; no watchdog or runtime process is started."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

import recording_recovery_adapter as adapter
import root_launch_recording_watchdog as launcher


@pytest.mark.parametrize("explicit", [False, True])
def test_launcher_default_dry_run_and_optional_forwarding(monkeypatch, tmp_path, explicit):
    session = tmp_path / "session"
    session.mkdir()
    for name in ("control", "site", "sdk", "helper"):
        (tmp_path / name).mkdir()
    (session / "ROOT-OBS-PROFILE.json").write_text(json.dumps({"control_dependencies": str(tmp_path / "control")}), encoding="utf-8")
    (session / "ROOT-ACTUAL-SDK-PROCESSES-PINNED-P42.json").write_text("{}", encoding="utf-8")
    files = {}
    for name in ("initial-recording-request", "overlay-source", "provider-source", "feeder-template", "main-python", "base-python"):
        files[name] = tmp_path / name
        files[name].write_text("synthetic", encoding="utf-8")
    root = tmp_path / "dry-run"
    argv = ["synthetic-launcher", "--session", str(session), "--sdk-prefix", "p42",
        "--dependency-root", str(tmp_path / "site"), "--sdk-source", str(tmp_path / "sdk"),
        "--helper-root", str(tmp_path / "helper"), "--launch-root", str(root),
        "--adapter-sha256", hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest()]
    for name, path in files.items():
        argv.extend(["--" + name, str(path)])
    stop = session / "future-custom-feeder-stop"
    if explicit:
        argv.extend(["--attach-only", "--feeder-stop-marker", str(stop)])
    probes = []
    def probe(command, **kw):
        probes.append(command)
        assert "--sdk-source" in command
        return SimpleNamespace(returncode=0, stdout='{"synthetic":true}', stderr="")
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(launcher.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    monkeypatch.setattr(launcher.subprocess, "run", probe)
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: pytest.fail("dry-run started a process"))
    launcher.main()
    plan = json.loads((root / "LAUNCH-PLAN.json").read_text(encoding="utf-8"))
    assert len(probes) == 2 and plan["attach_only"] is explicit
    assert ("--attach-only" in plan["argv"]) is explicit
    assert ("--feeder-stop-marker" in plan["argv"]) is explicit
    if explicit:
        assert plan["argv"][plan["argv"].index("--feeder-stop-marker") + 1] == str(stop.resolve())
    assert not stop.exists() and not (root / "LAUNCH-REQUEST.json").exists()
    parsed = adapter.parser().parse_args(plan["argv"][5:])
    assert parsed.attach_only is explicit
    assert parsed.feeder_stop_marker == (stop.resolve() if explicit else None)


@pytest.mark.parametrize("explicit", [False, True])
def test_settle_respects_custom_or_default_feeder_stop(tmp_path, explicit):
    q, root = tmp_path / "queue", tmp_path / "watchdog"
    q.mkdir()
    attempt = root / "synthetic-recovery"
    attempt.mkdir(parents=True)
    stop = tmp_path / ("custom-stop" if explicit else "ROOT-CONTINUOUS-FEEDER-STOP-P42")
    stop.touch()
    adapter.atomic(q / "ROOT-CUMULATIVE-LOOP-STATE.json", {"completed_cycles": 7, "pending_cycle": None})
    adapter.atomic(q / "CUMULATIVE-TURN-000007.json", {"auto_sequence": 90, "after_metrics_response": "synthetic-metrics"})
    adapter.atomic(attempt / "control-full_loop.json", {"request": {"sequence": 102}})
    instance = adapter.ActualAdapter.__new__(adapter.ActualAdapter)
    instance.n, instance.q, instance.root = tmp_path, q, root
    instance.c = SimpleNamespace(sdk_prefix="p42", feeder_stop_marker=stop if explicit else None)
    instance.journal = {"active": {"id": "synthetic-recovery", "phase": "settle",
        "original_pending": {"auto_sequence": 90, "global_turn": 7}, "old_request": "old", "new_request": "new"}}
    instance.control = lambda *args: {"status": "bounded_loop_finished", "same_SDK_continuation_available": True}
    instance.platform = SimpleNamespace(spawn=lambda *a, **k: pytest.fail("stopped feeder restarted"))
    instance.save = lambda: None
    assert instance.finish_continuation() == "complete"
    assert instance.journal["active"] is None
    assert instance.journal["current_request"] == "new"
    assert not (attempt / "feeder-launch-intent.json").exists()
