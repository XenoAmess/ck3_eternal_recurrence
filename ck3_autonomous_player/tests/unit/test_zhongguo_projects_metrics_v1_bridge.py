from __future__ import annotations

import json
from pathlib import Path
import unittest

import jsonschema
import pytest

from xar_autoplayer.bridge.zhongguo_projects_metrics_postcondition_contract import (
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
    ZhongguoProjectsMetricsQueryV1,
    bind_projects_metrics_event_snapshots_v1,
    normalize_native_zhongguo_projects_metrics_v1,
    parse_query_zhongguo_projects_metrics_v1_step,
    query_zhongguo_projects_metrics_v1_step,
)


ROOT = Path(__file__).resolve().parents[3]


def _typed(value: int | str) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _identity() -> dict[str, object]:
    return {
        "owner_character_id": _typed(147),
        "subject_character_id": _typed(361),
        "cycle_serial": _typed(9),
        "case_serial": _typed(26),
    }


def _unavailable() -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": "variable_absent",
    }


def _unavailable_identity() -> dict[str, object]:
    return {key: _unavailable() for key in (
        "owner_character_id", "subject_character_id", "cycle_serial", "case_serial"
    )}


def _native_frame() -> dict[str, object]:
    readiness = {
        key: True
        for key in (
            "player_subject_binding_ready", "owner_binding_ready",
            "source_identity_ready", "result_identity_ready",
            "contribution_ready", "metrics_ready",
            "same_project_case_identity", "receipt_lineage_ready",
            "result_operation_committed", "same_frame_ready", "ready",
        )
    }
    identity = _identity()
    return {
        "schema_version": 1,
        "status": "available",
        "capability": QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
        "case_kind": "zhongguo.projects-metrics.project-correlation",
        "request_nonce": "projects.26",
        "snapshot_revision": 51,
        "date_raw": 800,
        "paused": True,
        "player_character_id": 361,
        "requested_owner_character_id": 147,
        "checkpoint_state": "p3_result_committed",
        "source_identity": identity,
        "result_identity": _identity(),
        "projects_metrics": {
            "source_identity": _identity(),
            "result_identity": _identity(),
            "contribution": {
                "identity": _identity(),
                "receipt_id": _typed(26001),
                "receipt_revision": _typed(9),
                "value": _typed(20),
                "provider_observed": True,
            },
            "metrics_result": {
                "identity": _identity(),
                "source_contribution_receipt_id": _typed(26001),
                "source_contribution_receipt_revision": _typed(9),
                "metrics_revision": _typed(3),
                "dictionary_key": _typed("metric_dictionary_subject_v1"),
                "provider_observed": True,
            },
        },
        "readiness": readiness,
        "source_backend_id": "native-headless",
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "backend_id": "ck3-1.19.0.6-native-zhongguo-projects-metrics-postcondition-v1",
            "consumer_id": "xar-autoplayer-zhongguo-projects-metrics-postcondition-v1",
            "allowlist_id": "zg361-cp26-direct-p3m229-lineage-v2",
            "variable_context_for_scope_rva": "0x3329A40",
            "variable_identifier_table_rva": "0x3B971A0",
            "variable_identifier_lookup_rva": "0x3B97020",
            "variable_identifier_name_rva": "0x3B97090",
            "character_storage_slot_rva": "0x570C130",
            "character_fallback_slot_rva": "0x570C138",
        },
        "unavailable_reason": None,
    }


def test_step_round_trip_and_malformed_prefix_fail_closed() -> None:
    step = query_zhongguo_projects_metrics_v1_step(147, "projects.26")
    assert parse_query_zhongguo_projects_metrics_v1_step(step) == (
        ZhongguoProjectsMetricsQueryV1(147, "projects.26")
    )
    assert parse_query_zhongguo_projects_metrics_v1_step(step + "-extra") is None


def test_native_frame_normalizes_and_satisfies_json_schema() -> None:
    normalized = normalize_native_zhongguo_projects_metrics_v1(
        _native_frame(),
        expected_query=ZhongguoProjectsMetricsQueryV1(147, "projects.26"),
        expected_snapshot_revision=51,
        expected_date_raw=800,
        expected_player_character_id=361,
    )
    schema = json.loads((
        ROOT / "ck3_autonomous_player/schemas/zhongguo-projects-metrics-"
        "postcondition-v1.schema.json"
    ).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(normalized)


def test_direct_cp26_ready_p3_absent_frame_normalizes_and_satisfies_schema() -> None:
    frame = _native_frame()
    frame["checkpoint_state"] = "cp26_ready_p3_absent"
    frame["result_identity"] = _unavailable_identity()
    frame["projects_metrics"]["result_identity"] = _unavailable_identity()
    frame["projects_metrics"]["metrics_result"] = {
        "identity": _unavailable_identity(),
        "source_contribution_receipt_id": _unavailable(),
        "source_contribution_receipt_revision": _unavailable(),
        "metrics_revision": _unavailable(),
        "dictionary_key": _unavailable(),
        "provider_observed": True,
    }
    frame["readiness"] = {
        "player_subject_binding_ready": True,
        "owner_binding_ready": True,
        "source_identity_ready": True,
        "result_identity_ready": False,
        "contribution_ready": True,
        "metrics_ready": False,
        "same_project_case_identity": False,
        "receipt_lineage_ready": False,
        "result_operation_committed": False,
        "same_frame_ready": True,
        "ready": False,
    }
    normalized = normalize_native_zhongguo_projects_metrics_v1(
        frame,
        expected_query=ZhongguoProjectsMetricsQueryV1(147, "projects.26"),
        expected_snapshot_revision=51,
        expected_date_raw=800,
        expected_player_character_id=361,
    )
    schema = json.loads((
        ROOT / "ck3_autonomous_player/schemas/zhongguo-projects-metrics-"
        "postcondition-v1.schema.json"
    ).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(normalized)


def test_facade_binds_source_result_and_connection_generation() -> None:
    business = {
        **_native_frame(),
        "binding": {
            "connection_generation": 7, "snapshot_id": "result-51",
            "revision": 19, "native_revision": 51,
            "player_character_id": 361,
        },
    }
    source = {"binding": {
        "connection_generation": 7, "snapshot_id": "source-50",
        "revision": 18, "native_revision": 50,
    }}
    result = {"binding": {
        "connection_generation": 7, "snapshot_id": "result-51",
        "revision": 19, "native_revision": 51,
    }}
    bound = bind_projects_metrics_event_snapshots_v1(business, source, result)
    assert bound["binding"]["source_snapshot_id"] == "source-50"
    drifted = {"binding": {**result["binding"], "connection_generation": 8}}
    with pytest.raises(ValueError, match="generation drifted"):
        bind_projects_metrics_event_snapshots_v1(business, source, drifted)


def test_default_adapter_does_not_advertise_before_paused_live() -> None:
    adapter = (ROOT / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp").read_text(encoding="utf-8")
    assert QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY not in adapter


class OptimizedContractTests(unittest.TestCase):
    def test_step_schema_facade_and_default_off(self) -> None:
        query = ZhongguoProjectsMetricsQueryV1(147, "projects.26")
        step = query_zhongguo_projects_metrics_v1_step(147, "projects.26")
        self.assertEqual(parse_query_zhongguo_projects_metrics_v1_step(step), query)
        normalized = normalize_native_zhongguo_projects_metrics_v1(
            _native_frame(), expected_query=query,
            expected_snapshot_revision=51, expected_date_raw=800,
            expected_player_character_id=361,
        )
        schema = json.loads((
            ROOT / "ck3_autonomous_player/schemas/zhongguo-projects-metrics-"
            "postcondition-v1.schema.json"
        ).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(normalized)
        adapter = (ROOT / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp").read_text(encoding="utf-8")
        self.assertNotIn(QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY, adapter)


if __name__ == "__main__":
    unittest.main()
