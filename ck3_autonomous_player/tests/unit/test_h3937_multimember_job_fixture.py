"""No-CK3 integration proof for the local venv redirector Job fixture."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if not (TOOLS / "build_release.py").is_file():
    TOOLS = Path(r"D:\workspace\ck3_eternal_recurrence\tools")
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def _fixture_module():
    if os.name != "nt":
        pytest.skip("Windows Job APIs required")
    pytest.importorskip("psutil")
    pytest.importorskip("pythoncom")
    pytest.importorskip("win32com")
    from xar_autoplayer import h3937_multimember_job_fixture as fixture
    return fixture


def test_rejects_any_other_executable_before_creating_attempt(tmp_path: Path) -> None:
    fixture = _fixture_module()
    output = tmp_path / "refused"
    with pytest.raises(ValueError, match="frozen main venv"):
        fixture.run_no_ck3_fixture(
            output=output, python_executable=tmp_path / "ck3.exe")
    _require(not output.exists(), "rejected executable created an attempt")


def test_rejects_base_python_byte_drift_before_creating_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture_module()
    if not fixture.FIXTURE_PYTHON.is_file():
        pytest.skip("frozen main venv unavailable")
    output = tmp_path / "base-byte-drift"
    monkeypatch.setattr(fixture, "FIXTURE_BASE_PYTHON_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="base Python bytes differ"):
        fixture.run_no_ck3_fixture(
            output=output, python_executable=fixture.FIXTURE_PYTHON)
    _require(not output.exists(), "base Python drift created an attempt")


def test_venv_launcher_and_child_are_distinct_job_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture_module()
    if not fixture.FIXTURE_PYTHON.is_file():
        pytest.skip("frozen main venv unavailable")
    if hashlib.sha256(fixture.FIXTURE_PYTHON.read_bytes()).hexdigest().upper() != (
            fixture.FIXTURE_PYTHON_SHA256):
        pytest.skip("frozen main venv bytes unavailable")

    hostile = tmp_path / "hostile-pythonpath"
    hostile.mkdir()
    canary = tmp_path / "sitecustomize-executed"
    (hostile / "sitecustomize.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(canary)!r}).write_text('executed')\n",
        encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(hostile))
    monkeypatch.setenv("PYTHONHOME", str(hostile))
    output = tmp_path / "run"
    result = fixture.run_no_ck3_fixture(
        output=output, python_executable=fixture.FIXTURE_PYTHON,
        timeout_seconds=30)
    _require(result["status"] == "RAW_UNSEALED", str(result.get("error")))
    _require(result["full_chain_deadline_proven"] is False,
             "raw receipt claimed deadline proof")
    _require(result["ck3_launch_attempted"] is False, "CK3 boundary")
    _require(result["authority_bus_touched"] is False, "bus boundary")
    _require(result["screen_touched"] is False, "screen boundary")
    _require(not canary.exists(), "sitecustomize executed before fixed snippet")
    _require(result["isolated_python_flags"] == ["-I", "-S", "-u"],
             "Python startup isolation flags")
    _require(result["child_environment_keys"] == ["SystemRoot"],
             "uncontrolled child environment")
    _require(result["job_before_resume"] == {"active": 1, "total": 1},
             "pre-resume Job membership")
    _require(result["job_with_child"]["active"] >= 2, "multi-member Job")
    _require(result["job_after_cleanup"]["active"] == 0, "Job tree cleanup")
    _require(result["launcher_returncode"] == 0, "launcher exit")
    launcher = result["launcher_identity"]
    child = result["actual_identity"]
    _require(launcher["pid"] != child["pid"], "launcher/child PID distinction")
    _require(child["parent_pid"] == launcher["pid"], "parent linkage")
    _require(result["launcher_identity_with_child"]["creation_filetime_100ns"] ==
             launcher["creation_filetime_100ns"], "launcher creation drift")
    _require(launcher["job_member"] is True and child["job_member"] is True,
             "IsProcessInJob")
    _require(launcher["wmi_toolhelp_cross_checked"] is True,
             "launcher cross-check")
    _require(child["wmi_toolhelp_cross_checked"] is True, "child cross-check")
    _require(launcher["executable_sha256"] == fixture.FIXTURE_PYTHON_SHA256,
             "launcher executable bytes")
    _require(child["executable_sha256"] == fixture.FIXTURE_BASE_PYTHON_SHA256,
             "actual child executable bytes")
    _require(result["base_python_post_sha256"] ==
             fixture.FIXTURE_BASE_PYTHON_SHA256, "base executable drift")
    terminal = output / "terminal-observation.json"
    _require(json.loads(terminal.read_text(encoding="utf-8")) == result,
             "terminal receipt differs")
    before = hashlib.sha256(terminal.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        fixture.run_no_ck3_fixture(
            output=output, python_executable=fixture.FIXTURE_PYTHON,
            timeout_seconds=30)
    _require(hashlib.sha256(terminal.read_bytes()).hexdigest() == before,
             "create-only receipt changed")
    _require((output / "unsafe-marker.json").is_file(), "unsafe marker removed")


def test_deadline_retains_red_marker_and_empties_job(tmp_path: Path) -> None:
    fixture = _fixture_module()
    if not fixture.FIXTURE_PYTHON.is_file():
        pytest.skip("frozen main venv unavailable")
    if hashlib.sha256(fixture.FIXTURE_PYTHON.read_bytes()).hexdigest().upper() != (
            fixture.FIXTURE_PYTHON_SHA256):
        pytest.skip("frozen main venv bytes unavailable")

    output = tmp_path / "deadline"
    result = fixture.run_no_ck3_fixture(
        output=output, python_executable=fixture.FIXTURE_PYTHON,
        timeout_seconds=4)
    _require(result["status"] == "RED", "deadline incorrectly accepted")
    _require(result["watchdog_fired"] is True or
             str(result.get("error", "")).startswith("TimeoutError:"),
             "deadline was not observed")
    _require(result["job_after_cleanup"]["active"] == 0,
             "Job tree remained after deadline")
    _require((output / "unsafe-marker.json").is_file(), "unsafe marker removed")
    _require((output / "terminal-observation.json").is_file(),
             "terminal RED receipt missing")
