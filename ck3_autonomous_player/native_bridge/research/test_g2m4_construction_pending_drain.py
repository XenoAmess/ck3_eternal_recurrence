"""Focused no-launch tests for the R754 forced-pending drain."""

from __future__ import annotations

import ast
import inspect

from run_g2m4_paused_world_building_action import (
    drain_official_pending_interactions_for_construction_read,
)


PENDING = {
    "instance_id": 855_638_016,
    "sender_character_id": 30_629,
    "auto_accept_notification": False,
}


def snapshot(
    revision: int,
    *,
    pending: dict[str, object] | None,
    active_event: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "native_revision": revision,
        "date_raw": 53_178_384,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [],
        "player_armies": [],
        "active_event": active_event,
        "pending_character_interaction": pending,
    }


class Service:
    def __init__(
        self,
        snapshots: list[dict[str, object]],
        outcomes: list[dict[str, object] | BaseException],
    ) -> None:
        self.snapshots = snapshots
        self.outcomes = outcomes
        self.snapshot_calls = 0
        self.auto_turn_calls = 0

    def snapshot(self) -> dict[str, object]:
        value = self.snapshots[min(self.snapshot_calls, len(self.snapshots) - 1)]
        self.snapshot_calls += 1
        return value

    def auto_turn(self) -> dict[str, object]:
        value = self.outcomes[self.auto_turn_calls]
        self.auto_turn_calls += 1
        if isinstance(value, BaseException):
            raise value
        return value


def outcome(
    status: str,
    phase: str,
    selected_step: str | None,
    *,
    required_step: str | None = None,
    required_capabilities: list[str] | None = None,
) -> dict[str, object]:
    plan = {
        "phase": phase,
        "selected_step": selected_step,
        "required_step": required_step,
        "required_capabilities": required_capabilities,
    }
    result: dict[str, object] = {"status": status, "plan": plan}
    if selected_step is not None:
        result["selected_step"] = selected_step
    return result


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    service = Service(
        [
            snapshot(6, pending=PENDING),
            snapshot(7, pending=PENDING),
            snapshot(8, pending=None),
        ],
        [
            outcome(
                "executed",
                "pending_character_interaction_query",
                "query-pending-character-interaction-context-v1",
            ),
            outcome(
                "executed",
                "pending_character_interaction_degraded_reject",
                "reject-pending-character-interaction",
            ),
        ],
    )
    drained = drain_official_pending_interactions_for_construction_read(
        service, max_turns=4
    )
    require(drained["status"] == "scene_eligible", "query/reject did not drain")
    require(drained["turns_used"] == 2, "drain did not use exactly two turns")
    require(
        drained["construction_read_permitted"] is True,
        "eligible scene did not permit the later read",
    )
    require(service.auto_turn_calls == 2, "official auto_turn count changed")
    require(
        drained["construction_action_submits"] == 0,
        "construction action was resubmitted",
    )

    missing = Service(
        [snapshot(6, pending=PENDING)],
        [
            outcome(
                "blocked",
                "pending_character_interaction_evidence_required",
                None,
                required_step="query-pending-character-interaction-context-v1",
                required_capabilities=[
                    "query-pending-character-interaction-context-v1"
                ],
            )
        ],
    )
    blocked = drain_official_pending_interactions_for_construction_read(missing)
    require(blocked["status"] == "capability_red", "missing handler was hidden")
    require(
        blocked["required_step"]
        == "query-pending-character-interaction-context-v1",
        "exact missing typed handler was not exposed",
    )
    require(
        blocked["construction_read_permitted"] is False,
        "blocked scene incorrectly permitted construction read",
    )

    exhausted = Service(
        [snapshot(6, pending=PENDING), snapshot(7, pending=PENDING)],
        [
            outcome(
                "executed",
                "pending_character_interaction_query",
                "query-pending-character-interaction-context-v1",
            )
        ],
    )
    bounded = drain_official_pending_interactions_for_construction_read(
        exhausted, max_turns=1
    )
    require(
        bounded["status"] == "capability_red"
        and str(bounded["issue"]).startswith("bounded_pending_drain_exhausted"),
        "bounded drain did not stop on the still-pending scene",
    )
    require(
        bounded["construction_read_permitted"] is False,
        "exhausted drain incorrectly permitted construction read",
    )

    event_after_reply = Service(
        [
            snapshot(6, pending=PENDING),
            snapshot(
                7,
                pending=None,
                active_event={"instance_id": 71, "event_id": "example.1"},
            ),
        ],
        [
            outcome(
                "executed",
                "pending_character_interaction_degraded_reject",
                "reject-pending-character-interaction",
            )
        ],
    )
    still_forced = drain_official_pending_interactions_for_construction_read(
        event_after_reply
    )
    require(
        still_forced["status"] == "capability_red"
        and still_forced["construction_read_permitted"] is False,
        "new forced event incorrectly permitted construction read",
    )

    unknown = Service(
        [snapshot(6, pending=PENDING)],
        [RuntimeError("native reply receipt lost")],
    )
    failed = drain_official_pending_interactions_for_construction_read(unknown)
    require(
        failed["status"] == "red_action_state_unknown"
        and failed["construction_read_permitted"] is False,
        "unknown official action state did not stop without read",
    )

    source = inspect.getsource(
        drain_official_pending_interactions_for_construction_read
    )
    tree = ast.parse(source)
    require("service.auto_turn()" in source, "official auto_turn is not used")
    require("_read_step(" not in source, "drain directly issued a private step")
    require(
        not any(
            isinstance(node, ast.Name) and node.id == "ACTION_STEP"
            for node in ast.walk(tree)
        ),
        "drain gained a construction submit path",
    )
    require("reply_pending_character_interaction" not in source,
            "drain bypassed the official strategy")
    print(
        "GREEN bounded official pending query/reply drain; construction read "
        "remains gated; no CK3 launch"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
