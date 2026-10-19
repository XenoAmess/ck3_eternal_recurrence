"""Synthetic App-owned diagnostic checks; never construct a live Driver."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


LEAF = Path(__file__).resolve().parents[3] / "tools/g2_saved_campaign/lifestyle_current_state_once_diagnostic_v1.py"
SPEC = importlib.util.spec_from_file_location("life_once_diag_fixture", LEAF)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Server:
    def tool(self):
        return lambda function: function


def _install(tmp_path, *, actor=40526):
    frame = {"snapshot_id": "native:3134", "revision": 2, "native_revision": 3134,
             "date_raw": 53188032, "episode_run_id": "native-40526-synthetic",
             "paused": True, "map_ready": True,
             "played_character": {"character_id": actor, "alive": True},
             "diagnostics": {"bridge_pid": 153556, "connection_generation": 5,
                             "hello": {"pid": 153556}}}
    calls = []
    original = {"status": "native_query_unavailable", "request_id": "synthetic-life-query",
                "native_error": "native_lifestyle_current_state_current_lifestyle_getter_failed"}
    def read(*, expected_revision):
        calls.append(expected_revision)
        return original
    driver = SimpleNamespace(
        take_internal_semantic_snapshot=lambda: frame,
        _session_bridge_pid=153556, allow_private_lifestyle_formal_trial=True,
        query_player_lifestyle_current_state_private_v1=read,
    )
    function = MODULE.install_once_diag(
        _Server(), driver, evidence_path=tmp_path / "once.json", machine_id="synthetic-machine",
        expected_owner_frame={"bridge_pid": 153556, "player_character_id": 40526,
            "date_raw": 53188032, "episode_run_id": "native-40526-synthetic",
            "min_native_revision": 3134},
    )
    return function, calls, original


def test_one_original_read_uses_new_public_revision_and_retains_native_reason(tmp_path):
    function, calls, original = _install(tmp_path)
    result = function(expected_revision=2)
    assert result["status"] == "observed"
    assert result["same_frame"] is True
    assert result["original_method_return"] == original
    assert calls == [2]
    assert result["gameplay_action_submitted"] is False
    with pytest.raises(RuntimeError, match="already attempted"):
        function(expected_revision=2)
    assert calls == [2]


def test_foreign_actor_rejected_before_query_and_cannot_retry(tmp_path):
    function, calls, _ = _install(tmp_path, actor=29829)
    result = function(expected_revision=2)
    assert result["status"] == "diagnostic_failed"
    assert "did not bind" in result["exception"]
    assert "query_attempted" not in result
    assert calls == []
    with pytest.raises(RuntimeError, match="already attempted"):
        function(expected_revision=2)
    assert calls == []
