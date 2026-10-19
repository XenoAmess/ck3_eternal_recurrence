"""Conditional diagnostic fixtures; no live App, Driver, Native or Game."""

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


TOOLS = Path(__file__).resolve().parents[3] / "tools/g2_saved_campaign"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("child_focus_diag_fixture", TOOLS / "lifestyle_child_focus_once_diagnostic_v1.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Server:
    def tool(self):
        return lambda function: function


@pytest.mark.parametrize("reason,query_count", [
    ("native_lifestyle_current_state_current_lifestyle_getter_failed", 1),
    ("native_lifestyle_current_state_current_lifestyle_key_read_failed", 1),
    ("published_native_frame_or_main_thread_stale", 0),
])
def test_only_the_exact_preceding_same_frame_errors_admit_one_original_read(tmp_path, reason, query_count):
    snapshot = {"snapshot_id": "native:3134", "revision": 2, "native_revision": 3134,
                "date_raw": 53188032, "episode_run_id": "native-40526-synthetic",
                "paused": True, "map_ready": True,
                "played_character": {"character_id": 40526, "alive": True},
                "diagnostics": {"bridge_pid": 153556, "connection_generation": 5,
                                "hello": {"pid": 153556}}}
    frame = MODULE._frame(snapshot)
    prior = {"schema": "xar.app-owned-lifestyle-current-state-once-diagnostic.v1",
             "machine_id": "synthetic-machine",
             "method": "NativeDriver.query_player_lifestyle_current_state_private_v1",
             "status": "observed", "same_frame": True, "query_attempted": True,
             "before": frame, "after": frame,
             "original_method_return": {"native_error": reason}}
    prior_path = tmp_path / "prior.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    calls = []
    expected = {"current_focus": {"available": True, "presence": "present", "key": "education_learning"},
                "native_legal": False}
    def read(**kwargs):
        calls.append(kwargs)
        return expected
    driver = SimpleNamespace(_session_bridge_pid=153556,
        allow_private_lifestyle_formal_trial=True,
        take_internal_semantic_snapshot=lambda: snapshot,
        query_child_education_focus_private_v1=read)
    function = MODULE.install_child_focus_once_diag(
        _Server(), driver, evidence_path=tmp_path / "child.json",
        lifestyle_diagnostic_path=prior_path, machine_id="synthetic-machine")
    result = function(expected_revision=2)
    assert len(calls) == query_count
    if query_count:
        assert result["original_method_return"] == expected
        assert calls == [{"child_full_id": 40526, "target_key": "education_stewardship", "expected_revision": 2}]
        assert result["same_frame"] is True
    else:
        assert result["status"] == "diagnostic_failed"
        assert "query_attempted" not in result
    with pytest.raises(RuntimeError, match="already attempted"):
        function(expected_revision=2)
    assert len(calls) == query_count
