"""Existing normal Service retains its decisions and read counts with a sink."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_g2_normal_council_service_compound_v1 import NormalCouncilDriver
from xar_autoplayer.bridge import service


def test_existing_normal_planner_stage_receipts_do_not_change_work(tmp_path, monkeypatch):
    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    results, counts = [], []
    sink = tmp_path / "planning-stages.jsonl"
    for label, enabled in (("without_sink", False), ("with_sink", True)):
        driver = NormalCouncilDriver(tmp_path / label)
        original_snapshot = driver.take_internal_semantic_snapshot
        original_caps = driver.capabilities
        observed_calls = {"snapshot": 0, "capabilities": 0}

        def snapshot():
            observed_calls["snapshot"] += 1
            return original_snapshot()

        def capabilities():
            observed_calls["capabilities"] += 1
            return original_caps()

        driver.take_internal_semantic_snapshot = snapshot
        driver.capabilities = capabilities
        if enabled:
            monkeypatch.setenv("XAR_CK3_ARMY_TIMING_JSONL", str(sink))
        else:
            monkeypatch.delenv("XAR_CK3_ARMY_TIMING_JSONL", raising=False)
        with patch.object(service, "choose_one_life_turn", return_value=baseline) as chooser:
            results.append(service.GameplayBridgeService(driver).plan_turn())
            counts.append({**observed_calls, "chooser": chooser.call_count,
                "council_final_gates": driver.query_calls, "root": driver.root_calls,
                "submit": driver.submit_calls, "receipt": driver.receipt_calls})
        if not enabled:
            assert not sink.exists()
    assert results[0] == results[1]
    assert counts[0] == counts[1]
    assert counts[0]["chooser"] == counts[0]["council_final_gates"] == 1
    assert counts[0]["submit"] == counts[0]["receipt"] == 0
    rows = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    stages = {row["stage"] for row in rows}
    assert stages == {"service.normal_plan_turn", "service.planner_capabilities",
        "service.planner_history_rows", "service.planner_choose",
        "service.planner_public_plan_copy"}
    assert all(type(row["elapsed_ns"]) is int and row["elapsed_ns"] >= 0 for row in rows)
    assert all(set(row) == {"schema", "stage", "step", "elapsed_ns", "finished_at_utc",
                           "native_request_id"} for row in rows)
    for stage in stages - {"service.planner_capabilities"}:
        assert sum(row["stage"] == stage for row in rows) == 1
