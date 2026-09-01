"""Reusable scoreboard source-query/action/later-query acceptance cell.

The exact-build bridge can acknowledge its native semantic activation, but it
does not advertise production capability before a paused live artifact proves
the provider-owned observation transition.  This cell therefore preserves the
ACK and independent later read while keeping the current acceptance result RED.
"""

from __future__ import annotations

from typing import Protocol

from .zhongguo_scoreboard_action_contract import (
    verify_zhongguo_scoreboard_action_v1_postcondition,
)


class _ScoreboardService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...

    def activate_zhongguo_scoreboard_v1(
        self,
        request_nonce: str,
        action: str,
        *,
        expected_revision: int,
        expected_native_revision: int,
        expected_connection_generation: int,
        expected_player_character_id: int,
        expected_provider_session_id: str,
        expected_observation_sequence: int,
        expected_observed_state_revision: int,
        expected_tree_fingerprint_v1: str,
        expected_semantic_fingerprint_v1: str,
        expected_window_instance_pointer: str,
        expected_target_instance_pointer: str,
        expected_target_vtable_pointer: str,
    ) -> dict[str, object]: ...


_WINDOW_ID = "zg361_scoreboard_window"
_MODAL_ID = "zg361_scoreboard_modal"
_CLOSE_ID = "zg361_scoreboard_header_close"
_ENTRY_IDS = (
    "zg361_scoreboard_entry_managed",
    "zg361_scoreboard_entry_received",
    "zg361_scoreboard_entry_system",
)


def _available(value: object, expected_type: type, label: str) -> object:
    if not isinstance(value, dict) or value.get("status") != "available":
        raise ValueError(f"{label} is unavailable")
    observed = value.get("value")
    if expected_type is int and isinstance(observed, bool):
        raise ValueError(f"{label} has the wrong type")
    if not isinstance(observed, expected_type):
        raise ValueError(f"{label} has the wrong type")
    return observed


def _widgets(value: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = value.get("widgets")
    if not isinstance(rows, list) or len(rows) != 15:
        raise ValueError("scoreboard fixed widget projection is incomplete")
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("scoreboard widget row is malformed")
        identity = row.get("stable_identity")
        if not isinstance(identity, str) or identity in result:
            raise ValueError("scoreboard widget identity is malformed")
        result[identity] = row
    return result


def _action_target(
    source: dict[str, object],
) -> tuple[str, dict[str, object]]:
    widgets = _widgets(source)
    modal = widgets.get(_MODAL_ID)
    if modal is None:
        raise ValueError("scoreboard modal witness is absent")
    modal_visible = _available(
        modal.get("effective_visible"), bool, "scoreboard modal visibility"
    )
    if modal_visible is True:
        target = widgets.get(_CLOSE_ID)
        if target is None:
            raise ValueError("scoreboard close target is absent")
        return "close", target
    visible_entries = []
    for identity in _ENTRY_IDS:
        row = widgets.get(identity)
        if row is not None and _available(
            row.get("effective_visible"), bool, f"{identity} visibility"
        ) is True:
            visible_entries.append(row)
    if len(visible_entries) != 1:
        raise ValueError("scoreboard open entry is not unique")
    return "open", visible_entries[0]


def _paused_revision(service: _ScoreboardService, label: str) -> int:
    snapshot = service.snapshot()
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        raise ValueError(f"{label} lacks a paused snapshot")
    revision = snapshot.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise ValueError(f"{label} lacks a public revision")
    return revision


def run_zhongguo_scoreboard_action_cell(
    service: _ScoreboardService,
    *,
    nonce_prefix: str = "zg361.scoreboard.action-cell",
) -> dict[str, object]:
    """Run source query -> typed action result -> independent later query.

    A current fail-closed bridge returns ``result=RED`` and preserves all
    three frames.  Only an independently queried, provider-observed-revision-
    advanced verified postcondition may ever return GREEN.
    """

    evidence: dict[str, object] = {
        "schema_version": 1,
        "cell_id": "scoreboard_named_widget_action_and_postcondition_matrix",
        "result": "RED",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "source_query": None,
        "action_request": None,
        "action_result": None,
        "later_query": None,
        "verified_postcondition": None,
        "verified_pass": False,
        "production_capability_advertised": False,
        "failure_reason": None,
    }
    try:
        source_revision = _paused_revision(service, "scoreboard source")
        source = service.query_zhongguo_scoreboard_state_v1(
            f"{nonce_prefix}.source", expected_revision=source_revision
        )
        evidence["source_query"] = source
        if source.get("status") != "available":
            raise ValueError("scoreboard source query is unavailable")
        binding = source.get("binding")
        if not isinstance(binding, dict):
            raise ValueError("scoreboard source query lacks its binding")
        widgets = _widgets(source)
        window = widgets.get(_WINDOW_ID)
        if window is None:
            raise ValueError("scoreboard window witness is absent")
        action, target = _action_target(source)
        request = {
            "request_nonce": f"{nonce_prefix}.dispatch",
            "action": action,
            "expected_revision": binding.get("revision"),
            "expected_native_revision": binding.get("native_revision"),
            "expected_connection_generation": binding.get(
                "connection_generation"
            ),
            "expected_player_character_id": binding.get(
                "player_character_id"
            ),
            "expected_provider_session_id": source.get(
                "provider_session_id"
            ),
            "expected_observation_sequence": source.get(
                "observation_sequence"
            ),
            "expected_observed_state_revision": source.get(
                "observed_state_revision"
            ),
            "expected_tree_fingerprint_v1": source.get(
                "tree_fingerprint_v1"
            ),
            "expected_semantic_fingerprint_v1": source.get(
                "semantic_fingerprint_v1"
            ),
            "expected_window_instance_pointer": _available(
                window.get("instance_pointer"), str, "window pointer"
            ),
            "expected_target_instance_pointer": _available(
                target.get("instance_pointer"), str, "target pointer"
            ),
            "expected_target_vtable_pointer": _available(
                target.get("vtable_pointer"), str, "target vtable"
            ),
        }
        evidence["action_request"] = request
        action_result = service.activate_zhongguo_scoreboard_v1(
            str(request["request_nonce"]),
            str(request["action"]),
            expected_revision=int(request["expected_revision"]),
            expected_native_revision=int(request["expected_native_revision"]),
            expected_connection_generation=int(
                request["expected_connection_generation"]
            ),
            expected_player_character_id=int(
                request["expected_player_character_id"]
            ),
            expected_provider_session_id=str(
                request["expected_provider_session_id"]
            ),
            expected_observation_sequence=int(
                request["expected_observation_sequence"]
            ),
            expected_observed_state_revision=int(
                request["expected_observed_state_revision"]
            ),
            expected_tree_fingerprint_v1=str(
                request["expected_tree_fingerprint_v1"]
            ),
            expected_semantic_fingerprint_v1=str(
                request["expected_semantic_fingerprint_v1"]
            ),
            expected_window_instance_pointer=str(
                request["expected_window_instance_pointer"]
            ),
            expected_target_instance_pointer=str(
                request["expected_target_instance_pointer"]
            ),
            expected_target_vtable_pointer=str(
                request["expected_target_vtable_pointer"]
            ),
        )
        evidence["action_result"] = action_result
        evidence["production_capability_advertised"] = action_result.get(
            "production_capability_advertised"
        )

        later_revision = _paused_revision(service, "scoreboard later query")
        later = service.query_zhongguo_scoreboard_state_v1(
            f"{nonce_prefix}.later", expected_revision=later_revision
        )
        evidence["later_query"] = later
        if action_result.get("accepted") is not True:
            reason = action_result.get("rejection_reason")
            if not isinstance(reason, str) or not reason:
                raise ValueError("scoreboard unavailable action lacks a reason")
            evidence["failure_reason"] = reason
            return evidence
        if action_result.get("production_capability_advertised") is not True:
            evidence["failure_reason"] = (
                "provider_owned_revision_verification_unavailable"
            )
            return evidence
        ack = action_result.get("action_ack")
        if not isinstance(ack, dict):
            raise ValueError("scoreboard action ACK is absent")
        source_metadata = later.get("source")
        if not isinstance(source_metadata, dict):
            raise ValueError("scoreboard later query lacks source metadata")
        proof = verify_zhongguo_scoreboard_action_v1_postcondition(
            ack,
            post_state=later,
            observed_revision=later_revision,
            observed_connection_generation=int(
                source_metadata["connection_generation"]
            ),
        )
        evidence["verified_postcondition"] = proof
        evidence["verified_pass"] = proof.get("postcondition_verified") is True
        if evidence["verified_pass"] is not True:
            raise ValueError("scoreboard postcondition was not verified")
        evidence["result"] = "GREEN"
        return evidence
    except Exception as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        return evidence
