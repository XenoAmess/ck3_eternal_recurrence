"""The retired a11 entry must refuse before any operational side effect."""

from __future__ import annotations

from pathlib import Path

import pytest

from xar_autoplayer import h3937_combined_once_enable as once


@pytest.mark.parametrize(("name", "args"), [
    ("_require_live_screen_lease", ()),
    ("_managed_screen_heartbeat", ()),
    ("_require_go", ({},)),
    ("issue_screen_challenge", (Path("unused-entry.py"),)),
    ("run_exact_once", ("unused-nonce",)),
    ("main", ("unused-nonce",)),
    ("supervise_exact_once", (Path("unused-entry.py"),)),
])
def test_retired_entry_refuses_before_bus_process_or_file_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, args: tuple[object, ...],
) -> None:
    output = tmp_path / "must-not-be-created"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "SCREEN", tmp_path / "must-not-be-created-screen")
    calls: list[str] = []

    def forbidden(*unused_args: object, **unused_kwargs: object) -> None:
        calls.append("side effect")
        raise AssertionError("retired entry reached operational code")

    for attribute in (
        "_require_entry_blob", "_require_live_screen_lease", "_require_exact_admission",
        "_require_go", "_image_inventory", "_managed_screen_heartbeat", "_write_json",
        "_git", "_sha",
    ):
        if attribute != name:
            monkeypatch.setattr(once, attribute, forbidden)
    monkeypatch.setattr(once.subprocess, "Popen", forbidden)
    monkeypatch.setattr(once.subprocess, "run", forbidden)
    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", forbidden)

    with pytest.raises(RuntimeError, match="RED: historical H3937 a11.*retired"):
        getattr(once, name)(*args)
    if calls or output.exists() or once.SCREEN.exists():
        raise AssertionError("retired entry had an operational side effect")
