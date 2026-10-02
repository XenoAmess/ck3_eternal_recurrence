"""Bootstrap import failures retain diagnostics without reaching native APIs."""

from __future__ import annotations

import builtins
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/xar_autoplayer/process_watchdog.py"
)


@pytest.mark.parametrize("failed_import", ["win32api", "environment"])
@pytest.mark.parametrize("receipt_state", ["new", "existing", "missing_directory"])
def test_import_failure_preserves_bound_receipt_and_original_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    failed_import: str, receipt_state: str,
) -> None:
    record_dir = tmp_path / "records"
    if receipt_state != "missing_directory":
        record_dir.mkdir()
    record = record_dir / "runtime.json"
    ready = record_dir / "ready.json"
    error_path = record.with_suffix(".watchdog_error")
    original_receipt = b"previous immutable RED receipt\n"
    if receipt_state == "existing":
        error_path.write_bytes(original_receipt)
    marker = tmp_path / "unsafe-cleanup.json"
    marker_bytes = b'{"nonce":"synthetic-nonce","status":"RED"}\n'
    marker.write_bytes(marker_bytes)
    monkeypatch.setattr(sys, "argv", [
        str(SOURCE), "12345", "synthetic-parent.exe", "synthetic-creation",
        "synthetic-nonce", str(ready), str(record), str(marker),
        "synthetic-unused-game.exe",
    ])
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    original_import = builtins.__import__
    imported_native: list[str] = []

    def controlled_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("win32"):
            imported_native.append(name)
            if name == failed_import:
                raise ModuleNotFoundError("synthetic missing " + failed_import)
            return SimpleNamespace()
        if failed_import == "environment" and name in {
            "environment", "xar_autoplayer.environment",
        }:
            raise ModuleNotFoundError("synthetic missing environment")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", controlled_import)
    namespace = {
        "__name__": "xar_autoplayer._watchdog_import_fixture",
        "__package__": "xar_autoplayer",
        "__file__": str(SOURCE),
    }
    with pytest.raises(ModuleNotFoundError, match="synthetic missing " + failed_import):
        exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)

    if not imported_native or "main" in namespace or ready.exists():
        raise AssertionError("import failure reached operational watchdog code")
    if marker.read_bytes() != marker_bytes:
        raise AssertionError("import failure changed the unsafe marker")
    if receipt_state == "existing":
        if error_path.read_bytes() != original_receipt:
            raise AssertionError("bootstrap diagnostic replaced an old receipt")
    elif receipt_state == "missing_directory":
        if record_dir.exists():
            raise AssertionError("bootstrap diagnostic created a missing attempt directory")
    else:
        receipt = json.loads(error_path.read_text(encoding="utf-8"))
        expected = {
            "schema": "xar.watchdog-early-import-error.v1",
            "stage": "early-import", "nonce": "synthetic-nonce",
            "parent_pid": 12345, "watchdog_pid": os.getpid(),
            "watchdog_parent_pid": os.getppid(), "python": sys.executable,
            "error_type": "ModuleNotFoundError",
            "error": "synthetic missing " + failed_import,
        }
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise AssertionError("bootstrap diagnostic identity or exception differs")
        if "ModuleNotFoundError: synthetic missing " + failed_import not in receipt["traceback"]:
            raise AssertionError("bootstrap diagnostic omitted the original traceback")
        start = record.with_name(record.stem + ".synthetic-nonce.watchdog_start.json")
        if json.loads(start.read_text(encoding="utf-8"))["watchdog_pid"] != os.getpid():
            raise AssertionError("existing early-start observation was not preserved")
    if record_dir.exists() and list(record_dir.glob("*.tmp")):
        raise AssertionError("bootstrap diagnostic left an unpublished temporary receipt")
