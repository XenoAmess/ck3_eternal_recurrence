from __future__ import annotations

import copy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.epidemic_recovery_formal_observer import (
    capture_epidemic_recovery_before_option,
    observe_epidemic_recovery_after_option,
)


def _snapshot(*, after: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": "native:238" if after else "native:237",
        "revision": 239 if after else 238,
        "native_revision": 238 if after else 237,
        "date_raw": 53376672,
        "episode_run_id": "native-36403-episode",
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 36403, "alive": True},
        "active_event": None if after else {"instance_id": 24},
    }


def _candidate() -> dict[str, object]:
    return {
        "snapshot_id": "native:237",
        "revision": 238,
        "selected_step": "select-event-option-3",
        "plan": {
            "phase": "active_event_registry_choice",
            "active_event": {"instance_id": 24},
            "event_decision": {
                "status": "recommended",
                "event_definition_key": "epidemic_events.0110",
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        },
    }


class _Service:
    def __init__(self) -> None:
        self.frame = _snapshot()
        self.before_rows = [
            {"landed_title_id": 524, "minor_present": False, "tiny_present": False},
            {"landed_title_id": 525, "minor_present": False, "tiny_present": False},
        ]
        self.after_rows = {
            524: {"landed_title_id": 524, "minor_present": True, "tiny_present": False},
            525: {"landed_title_id": 525, "minor_present": True, "tiny_present": False},
        }
        self.queries: list[tuple[int, int, int | None]] = []

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def query_player_epidemic_recovery_private_v1(
        self, *, expected_revision: int, requested_title_id: int = 0,
        expected_event_instance_id: int | None = None,
    ) -> dict[str, object]:
        self.queries.append((expected_revision, requested_title_id, expected_event_instance_id))
        assert expected_revision == self.frame["revision"]
        if requested_title_id:
            rows = [self.after_rows[requested_title_id]]
        else:
            assert expected_event_instance_id == 24
            rows = self.before_rows
        return {"player_epidemic_recovery": {
            "status": "available", "counties": copy.deepcopy(rows),
        }}

    def query_campaign_root_context_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        assert expected_revision == self.frame["revision"]
        return {
            "queried_snapshot_id": self.frame["snapshot_id"],
            "queried_revision": self.frame["revision"],
            "queried_native_revision": self.frame["native_revision"],
            "campaign_root_context": {
                "player_character_id": 36403,
                "player_legitimacy_v1": {
                    "status": "available",
                    "value": {
                        "raw": 26_300_000 if self.frame["active_event"] is None
                        else 28_300_000,
                        "scale": 100_000,
                    },
                    "unavailable_reason": None,
                },
            },
        }


def test_exact_option_c_freezes_titles_before_clear_and_reads_same_date() -> None:
    service = _Service()
    captured = capture_epidemic_recovery_before_option(service, _candidate())
    assert captured is not None
    assert [row["landed_title_id"] for row in captured["before_counties"]] == [524, 525]
    assert captured["before_legitimacy"]["raw"] == 28_300_000
    service.frame = _snapshot(after=True)
    observed = observe_epidemic_recovery_after_option(
        service, captured, service.snapshot()
    )
    assert observed["status"] == "verified_new_modifier_presence"
    assert [row["status"] for row in observed["counties"]] == [
        "new_modifier_presence", "new_modifier_presence",
    ]
    assert observed["legitimacy"]["delta_raw"] == -2_000_000
    assert observed["date_advanced"] is False
    assert service.queries == [(238, 0, 24), (239, 524, None), (239, 525, None)]


def test_unknown_option_is_not_queried_and_preexisting_modifier_is_partial() -> None:
    service = _Service()
    candidate = _candidate()
    candidate["plan"]["event_decision"]["event_definition_key"] = "other.0110"
    assert capture_epidemic_recovery_before_option(service, candidate) is None
    assert service.queries == []
    service.before_rows[0]["minor_present"] = True
    captured = capture_epidemic_recovery_before_option(service, _candidate())
    assert captured is not None
    service.frame = _snapshot(after=True)
    observed = observe_epidemic_recovery_after_option(
        service, captured, service.snapshot()
    )
    assert observed["status"] == "partial_or_unverified"
    assert observed["counties"][0]["status"] == "preexisting_presence_ambiguous"


def test_cross_date_and_unavailable_target_list_do_not_claim_near_pair() -> None:
    service = _Service()
    captured = capture_epidemic_recovery_before_option(service, _candidate())
    assert captured is not None
    service.frame = _snapshot(after=True)
    service.frame["date_raw"] += 24
    with pytest.raises(BridgeUnavailableError, match="same-day"):
        observe_epidemic_recovery_after_option(service, captured, service.snapshot())

    service = _Service()
    service.before_rows = []
    with pytest.raises(BridgeUnavailableError, match="empty"):
        capture_epidemic_recovery_before_option(service, _candidate())
