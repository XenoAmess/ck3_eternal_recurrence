from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (  # noqa: E402
    ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
    PROGRESS_WIDGETS,
    QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
    parse_query_promotion_source_progress_v1_step,
    query_promotion_source_progress_v1_step,
)
from zg361_phase2_promotion_source_production_entry import (  # noqa: E402
    B1_AUTHORED_ADVANCE_DAYS,
    KNOWN_TIMELINE_INTERRUPTS,
    MAX_ADVANCE_DAYS,
    POST_PUBLICATION_OBSERVATION_DAYS,
    PromotionProductionEntryError,
    _known_interrupt_checks,
    enter_promotion_source_checkpoint_v1,
)


def _typed(value: bool) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _progress(action: bool, b1: bool, sequence: int) -> dict[str, object]:
    visible = [True, action, b1, False, False]
    return {
        "status": "available",
        "query_sequence": sequence,
        "zhongguo_promotion_source_progress": {
            "widgets": [
                {"stable_identity": name, "effective_visible": _typed(state)}
                for name, state in zip(PROGRESS_WIDGETS, visible, strict=True)
            ]
        },
        "binding": {
            "connection_generation": 7,
            "player_character_id": 29037,
        },
    }


def _character_scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            },
        },
    }


def _boolean_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {"status": "available", "type_key": "boolean"},
    }


def _unavailable_character_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "unavailable",
                "reason": "character_scope_identity_unavailable",
            },
        },
    }


def _opaque_scope(name: str, type_key: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {"status": "available", "type_key": type_key},
    }


def _options(
    count: int, *, native_indices: tuple[int, ...] | None = None
) -> list[dict[str, object]]:
    indices = native_indices or tuple(range(count))
    return [
        {
            "rendered_index": index,
            "native_option_index": indices[index],
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        }
        for index in range(count)
    ]


class _Service:
    def __init__(self) -> None:
        self.stage = "seed"
        self.selected: list[int] = []

    def snapshot(self) -> dict[str, object]:
        date = 53146920
        event = None
        if self.stage == "m146":
            event = {"instance_id": 1460, "option_count": 3}
            date += 330 * 24
        elif self.stage == "m147":
            event = {"instance_id": 1470, "option_count": 3}
            date += 331 * 24
        return {
            "snapshot_id": f"snapshot-{self.stage}",
            "revision": {"seed": 1, "b1": 2, "m146": 3, "m147": 4}[self.stage],
            "native_revision": {"seed": 11, "b1": 12, "m146": 13, "m147": 14}[self.stage],
            "date_raw": date,
            "paused": True,
            "speed": 1,
            "map_ready": True,
            "played_character": {"character_id": 29037},
            "diagnostics": {"connection_generation": 7},
            **({"active_event": event} if event is not None else {}),
        }

    def query_zhongguo_promotion_source_progress_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        del request_nonce, expected_revision
        return _progress(self.stage == "seed", self.stage == "b1", 1 if self.stage == "seed" else 2)

    def activate_zhongguo_review_now_v1(
        self, request_nonce: str, source_progress: dict[str, object], *,
        expected_revision: int,
    ) -> dict[str, object]:
        del request_nonce, source_progress, expected_revision
        self.stage = "b1"
        return {
            "accepted": True,
            "status": "acknowledged_verification_pending",
            "production_capability_advertised": False,
        }

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        del expected_revision
        if step == "resume-map" and self.stage == "b1":
            self.stage = "m146"
        return {"accepted": True, "status": "submitted"}

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        snapshot = self.snapshot()
        key = "zg361pp.146" if self.stage == "m146" else "zg361pp.147"
        return {
            "status": "available",
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": expected_revision,
                "native_revision": snapshot["native_revision"],
                "event_instance_id": event_instance_id,
            },
            "current_event_window_context": {"event_definition_key": key},
        }

    def select_event_option(
        self, option_number: int, *, event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        del event_instance_id, expected_revision
        self.selected.append(option_number)
        self.stage = "m147"
        return {"accepted": True, "status": "submitted"}


def test_query_step_is_fixed_owner_nonce_only() -> None:
    step = query_promotion_source_progress_v1_step(29037, "promo.entry")
    parsed = parse_query_promotion_source_progress_v1_step(step)
    assert parsed is not None
    assert parsed.owner_character_id == 29037
    assert parsed.request_nonce == "promo.entry"


def test_product_path_uses_ack_only_then_independent_b1_and_m147() -> None:
    service = _Service()
    result = enter_promotion_source_checkpoint_v1(
        service, poll_interval_seconds=0
    )
    assert result["result"] == "GREEN"
    assert result["readiness"] == "paused-real-zg361pp.147"
    assert result["action_ack_used_as_state_evidence"] is False
    assert result["review_action_postcondition"]["after_query_sequence"] == 2
    assert result["m146_date_raw"] + 24 == result["target_binding"]["date_raw"]
    assert result["advance_bound"] == {
        "b1_authored_days": B1_AUTHORED_ADVANCE_DAYS,
        "post_publication_observation_days": POST_PUBLICATION_OBSERVATION_DAYS,
        "total_days": MAX_ADVANCE_DAYS,
    }
    assert MAX_ADVANCE_DAYS == 550
    assert service.selected == [1]


def test_product_path_accepts_idempotent_already_running_ack() -> None:
    class _AlreadyRunningService(_Service):
        def __init__(self) -> None:
            super().__init__()
            self.resume_count = 0

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            del expected_revision
            if step == "resume-map" and self.stage == "b1":
                self.resume_count += 1
                if self.resume_count == 2:
                    self.stage = "m146"
                    return {"accepted": True, "status": "already_running"}
            return {"accepted": True, "status": "submitted"}

    service = _AlreadyRunningService()
    result = enter_promotion_source_checkpoint_v1(
        service, poll_interval_seconds=0
    )
    assert result["result"] == "GREEN"
    assert service.resume_count == 2
    assert service.selected == [1]


def test_product_path_retries_same_native_frame_while_saved_scopes_build() -> None:
    class _TransientSavedScopeService(_Service):
        def __init__(self) -> None:
            super().__init__()
            self.query_calls = 0
            self.query_revision = 3

        def snapshot(self) -> dict[str, object]:
            value = super().snapshot()
            if self.stage == "m146":
                value["revision"] = self.query_revision
            return value

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            self.query_calls += 1
            if self.stage == "m146" and self.query_calls == 1:
                assert expected_revision == 3
                self.query_revision = 4
                return {
                    "status": "unavailable",
                    "queried_snapshot_id": "snapshot-m146",
                    "queried_revision": 4,
                    "queried_native_revision": 13,
                    "current_event_window_context": {
                        "status": "unavailable",
                        "current_event_instance_id": event_instance_id,
                        "unavailable_reason": "event_saved_scope_invalid",
                    },
                }
            return super().query_current_event_window_context_v1(
                event_instance_id, expected_revision=expected_revision
            )

    service = _TransientSavedScopeService()
    result = enter_promotion_source_checkpoint_v1(
        service, poll_interval_seconds=0, sleeper=lambda _: None
    )
    assert result["result"] == "GREEN"
    assert service.query_calls == 3
    assert service.selected == [1]


def test_product_path_drains_exact_seed_interrupts_with_bounded_repeat() -> None:
    class _InterruptedService(_Service):
        def snapshot(self) -> dict[str, object]:
            if self.stage not in {
                "pip", "flood_relief", "new_governorship", "forced_retirement", "doppelganger", "china_yearly", "grieving_child", "merchant_dispute", "unpaid_taxes", "emperor_assistance", "scholar", "learned_eunuch", "equitable", "local_defense", "governor_yearly", "pugnacious", "neighbor_governor", "silk_road",
                "arbitrary_tax", "hook_offer", "hook_offer_repeat", "no_secrets", "jingcha",
                "self_review", "secret_discovery", "lover_secret", "sway_misunderstanding",
                "governor_bargain", "succession"
            }:
                return super().snapshot()
            if self.stage == "pip":
                instance_id, option_count, date, revision = 400, 3, 53147040, 30
            elif self.stage == "flood_relief":
                instance_id, option_count, date, revision = 8120, 3, 53147520, 31
            elif self.stage == "new_governorship":
                instance_id, option_count, date, revision = 2, 3, 53147280, 31
            elif self.stage == "forced_retirement":
                instance_id, option_count, date, revision = 630, 1, 53151600, 31
            elif self.stage == "doppelganger":
                instance_id, option_count, date, revision = 9007, 2, 53147520, 31
            elif self.stage == "china_yearly":
                instance_id, option_count, date, revision = 10, 3, 53147520, 31
            elif self.stage == "grieving_child":
                instance_id, option_count, date, revision = 5, 3, 53147520, 31
            elif self.stage == "merchant_dispute":
                instance_id, option_count, date, revision = 15, 3, 53147520, 32
            elif self.stage == "unpaid_taxes":
                instance_id, option_count, date, revision = 20, 2, 53147520, 32
            elif self.stage == "emperor_assistance":
                instance_id, option_count, date, revision = 2200, 2, 53147520, 32
            elif self.stage == "scholar":
                instance_id, option_count, date, revision = 2240, 3, 53147520, 32
            elif self.stage == "learned_eunuch":
                instance_id, option_count, date, revision = 1200, 4, 53147520, 32
            elif self.stage == "equitable":
                instance_id, option_count, date, revision = 8160, 3, 53147520, 32
            elif self.stage == "local_defense":
                instance_id, option_count, date, revision = 8170, 4, 53147520, 32
            elif self.stage == "governor_yearly":
                instance_id, option_count, date, revision = 8060, 4, 53147520, 33
            elif self.stage == "governor_bargain":
                instance_id, option_count, date, revision = 8010, 3, 53147520, 34
            elif self.stage == "pugnacious":
                instance_id, option_count, date, revision = 8110, 4, 53147520, 34
            elif self.stage == "neighbor_governor":
                instance_id, option_count, date, revision = 8100, 3, 53147520, 34
            elif self.stage == "silk_road":
                instance_id, option_count, date, revision = 40, 3, 53147520, 35
            elif self.stage == "arbitrary_tax":
                instance_id, option_count, date, revision = 8130, 4, 53147520, 36
            elif self.stage in {"hook_offer", "hook_offer_repeat"}:
                instance_id, option_count, date, revision = (
                    (381, 2, 53148768, 37)
                    if self.stage == "hook_offer"
                    else (382, 2, 53152896, 40)
                )
            elif self.stage == "no_secrets":
                instance_id, option_count, date, revision = 399, 2, 53148768, 38
            elif self.stage == "jingcha":
                instance_id, option_count, date, revision = 40, 2, 53150880, 39
            elif self.stage == "self_review":
                instance_id, option_count, date, revision = 200, 3, 53152728, 40
            elif self.stage == "secret_discovery":
                instance_id, option_count, date, revision = 342, 1, 53152896, 40
            elif self.stage == "lover_secret":
                instance_id, option_count, date, revision = 346, 1, 53152896, 41
            elif self.stage == "sway_misunderstanding":
                instance_id, option_count, date, revision = 2001, 1, 53153952, 42
            else:
                instance_id, option_count, date, revision = 3060, 3, 53148072, 43
            snapshot_option_count = (
                3
                if self.stage == "doppelganger"
                else 4
                if self.stage in {
                    "china_yearly", "grieving_child", "merchant_dispute", "neighbor_governor",
                    "succession",
                }
                else option_count
            )
            return {
                "snapshot_id": f"snapshot-{self.stage}",
                "revision": revision,
                "native_revision": revision + 100,
                "date_raw": date,
                "paused": True,
                "speed": 1,
                "map_ready": True,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 7},
                "active_event": {
                    "instance_id": instance_id,
                    "option_count": snapshot_option_count,
                },
            }

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            del expected_revision
            if step == "resume-map" and self.stage == "b1":
                self.stage = "pip"
            return {"accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            if self.stage not in {
                "pip", "flood_relief", "new_governorship", "forced_retirement", "doppelganger", "china_yearly", "grieving_child", "merchant_dispute", "unpaid_taxes", "emperor_assistance", "scholar", "learned_eunuch", "equitable", "local_defense", "governor_yearly", "pugnacious", "neighbor_governor", "silk_road",
                "arbitrary_tax", "hook_offer", "hook_offer_repeat", "no_secrets", "jingcha",
                "self_review", "secret_discovery", "lover_secret", "sway_misunderstanding",
                "governor_bargain", "succession"
            }:
                return super().query_current_event_window_context_v1(
                    event_instance_id, expected_revision=expected_revision
                )
            snapshot = self.snapshot()
            if self.stage == "pip":
                key = "zg361b2.40"
                scopes = [
                    _character_scope("zg361_reviewing_superior", 32904),
                    _character_scope("zg361_b2_pip_prompt_owner", 32904),
                    _character_scope("zg361_b2_pip_prompt_subject", 29037),
                    _character_scope("zga_personal_result_target", 29037),
                ]
                option_count = 3
            elif self.stage == "flood_relief":
                key = "ep3_governor_yearly.8120"
                scopes = [_opaque_scope("disaster_county", "landed_title")]
                option_count = 3
            elif self.stage == "new_governorship":
                key = "ep3_admin_events.0002"
                scopes = [
                    _opaque_scope("title", "landed_title"),
                    _character_scope("previous_holder", 28557),
                    _character_scope("new_holder", 29037),
                    _opaque_scope("transfer_type", "flag"),
                    _opaque_scope("nf_gov_type", "government_type"),
                    _opaque_scope("governor_title", "landed_title"),
                    _character_scope("previous_governor", 28557),
                ]
                option_count = 3
            elif self.stage == "forced_retirement":
                key = "ep3_interactions_events.0630"
                scopes = [
                    _character_scope("actor", 32904),
                    _character_scope("recipient", 29037),
                    _unavailable_character_scope("secondary_actor"),
                    _unavailable_character_scope("secondary_recipient"),
                    _unavailable_character_scope("intermediary"),
                    _boolean_scope("hook"),
                    _opaque_scope("force_retirement_treasury_cost", "value"),
                ]
                option_count = 1
            elif self.stage == "doppelganger":
                key = "bp1_yearly.9007"
                scopes = [
                    _character_scope(
                        "bp1_yearly_9007_doppelganger", 16779978
                    ),
                ]
                option_count = 2
            elif self.stage == "china_yearly":
                key = "tgp_china_yearly.0010"
                scopes = [_character_scope("starving_lowborn", 16780149)]
                option_count = 3
            elif self.stage == "grieving_child":
                key = "tgp_china_yearly.0005"
                scopes = [
                    # R56 allocator identities differ from R50 while the
                    # source-defined parent alias and complete shape remain.
                    _character_scope("grieving_child", 16780191),
                    _character_scope("orphan_mother", 16780218),
                    _character_scope("orphan_father", 16780221),
                    _character_scope("parent", 16780221),
                    _character_scope("guardian", 31647),
                    _character_scope("messenger", 31003),
                ]
                option_count = 3
            elif self.stage == "merchant_dispute":
                key = "tgp_china_yearly.0015"
                scopes = [
                    _character_scope("market_vendor", 16780002),
                    _character_scope("traveling_merchant", 16780004),
                ]
                option_count = 3
            elif self.stage == "unpaid_taxes":
                key = "tgp_china_yearly.0020"
                scopes = [
                    _opaque_scope("taxless_county", "landed_title"),
                    _character_scope("tax_official", 29346),
                    _character_scope("tax_liege", 32904),
                ]
                option_count = 2
            elif self.stage == "emperor_assistance":
                key = "ep3_emperor_yearly.2200"
                scopes = [
                    _character_scope("liege", 32904),
                    _opaque_scope("governorship", "landed_title"),
                    _opaque_scope("capital", "landed_title"),
                ]
                option_count = 2
            elif self.stage == "scholar":
                key = "ep3_emperor_yearly.2240"
                scopes = [_character_scope("the_scholar", 56656)]
                option_count = 3
            elif self.stage == "learned_eunuch":
                key = "ep1_flavor.1200"
                scopes = [
                    _opaque_scope("eunuch_target_culture", "culture"),
                    _character_scope("eunuch_target", 16780004),
                ]
                option_count = 4
            elif self.stage == "equitable":
                key = "ep3_governor_yearly.8160"
                scopes = [
                    _opaque_scope("minority_county", "landed_title"),
                    _character_scope("councillor", 31003),
                    _character_scope("culture", 29037),
                    _character_scope("administrator", 16780148),
                ]
                option_count = 3
            elif self.stage == "local_defense":
                key = "ep3_governor_yearly.8170"
                scopes = [
                    _character_scope("governor", 29037),
                    _character_scope("marshal", 29575),
                    _character_scope("raider", 32922),
                    _opaque_scope("raid_county", "landed_title"),
                ]
                option_count = 4
            elif self.stage == "governor_yearly":
                key = "ep3_governor_yearly.8060"
                scopes = []
                option_count = 4
            elif self.stage == "governor_bargain":
                key = "ep3_governor_yearly.8010"
                scopes = [
                    _character_scope("governor", 29347),
                    _character_scope("their_title_receiver", 30938),
                    _opaque_scope("their_title", "landed_title"),
                    _character_scope("title_receiver", 29067),
                    _opaque_scope("title", "landed_title"),
                    _opaque_scope("governor_request", "flag"),
                    _opaque_scope("governor_offer", "flag"),
                ]
                option_count = 3
            elif self.stage == "pugnacious":
                key = "ep3_governor_yearly.8110"
                scopes = [
                    _character_scope("governor_1", 28598),
                    _character_scope("governor_2", 27181),
                ]
                option_count = 4
            elif self.stage == "neighbor_governor":
                key = "ep3_governor_yearly.8100"
                scopes = [
                    _character_scope("governor", 27181),
                    _character_scope("neighboring_promoted_char", 36175),
                    _character_scope("target_family_member", 31647),
                ]
                option_count = 3
            elif self.stage == "silk_road":
                key = "tgp_dynastic_cycle_events.0040"
                scopes = [
                    _opaque_scope("my_situation", "situation"),
                    _opaque_scope("silk_road_situation", "situation"),
                    _opaque_scope(
                        "my_movement", "situation_participant_group"
                    ),
                    _character_scope("steward", 31003),
                ]
                option_count = 3
            elif self.stage == "arbitrary_tax":
                key = "ep3_governor_yearly.8130"
                scopes = []
                option_count = 4
            elif self.stage in {"hook_offer", "hook_offer_repeat"}:
                key = "spymaster_task.0381"
                scopes = [
                    _character_scope("councillor", 27963),
                    _character_scope("councillor_liege", 29037),
                    _character_scope("target_character", 27051),
                    _boolean_scope("having_find_secrets_event"),
                    _character_scope(
                        "character_to_hook",
                        31660 if self.stage == "hook_offer" else 32086,
                    ),
                ]
                option_count = 2
            elif self.stage == "no_secrets":
                key = "spymaster_task.0399"
                scopes = [
                    _character_scope("councillor", 27963),
                    _character_scope("councillor_liege", 29037),
                    _character_scope("target_character", 27051),
                    _boolean_scope("no_secrets_here"),
                ]
                option_count = 2
            elif self.stage == "jingcha":
                key = "zg361.40"
                scopes = []
                option_count = 2
            elif self.stage == "self_review":
                key = "zg361b1.200"
                scopes = [
                    _character_scope("zga_phase2_seed_player", 29037),
                    _character_scope("zg361_b1_ticket_owner", 29628),
                    _opaque_scope("zg361_b1_ticket_cycle", "value"),
                    _opaque_scope("zg361_b1_ticket_case", "value"),
                    _opaque_scope("zg361_b1_ticket_state", "value"),
                    _character_scope("zg361_b1_self_ticket_owner", 29628),
                    _character_scope("zg361_b1_self_ticket_subject", 29037),
                    _opaque_scope("zg361_b1_self_ticket_cycle", "value"),
                    _opaque_scope("zg361_b1_self_ticket_case", "value"),
                    _opaque_scope("zg361_b1_self_ticket_state", "value"),
                ]
                option_count = 3
            elif self.stage == "secret_discovery":
                key = "spymaster_task.0342"
                scopes = [
                    _character_scope("councillor", 27963),
                    _character_scope("councillor_liege", 29037),
                    _character_scope("target_character", 27051),
                    _boolean_scope("having_find_secrets_event"),
                    _character_scope("active_councillor", 27963),
                    _character_scope("secret_holder", 27051),
                    _opaque_scope("secret_to_reveal", "secret"),
                ]
                option_count = 1
            elif self.stage == "lover_secret":
                key = "spymaster_task.0346"
                scopes = [
                    _character_scope("councillor", 27963),
                    _character_scope("councillor_liege", 29037),
                    _character_scope("target_character", 27051),
                    _boolean_scope("having_find_secrets_event"),
                    _character_scope("active_councillor", 27963),
                    _character_scope("secret_holder", 27051),
                    _opaque_scope("secret_to_reveal", "secret"),
                    _character_scope("lover", 45267),
                ]
                option_count = 1
            elif self.stage == "sway_misunderstanding":
                key = "sway_outcome.2001"
                scopes = [
                    _opaque_scope("scheme", "scheme"),
                    _character_scope("owner", 29037),
                    _opaque_scope("artifact", "artifact"),
                    _character_scope("target", 27051),
                ]
                option_count = 1
            else:
                key = "ep3_governor_yearly.3060"
                scopes = [
                    _opaque_scope("title", "landed_title"),
                    _character_scope("previous_holder", 32904),
                    _character_scope("new_holder", 36354),
                    _opaque_scope("transfer_type", "flag"),
                    _opaque_scope("nf_gov_type", "government_type"),
                    _character_scope("emperor", 36354),
                    _character_scope("root_scope", 29037),
                    _opaque_scope("emp_location", "province"),
                ]
                option_count = 3
            return {
                "status": "available",
                "binding": {
                    "snapshot_id": snapshot["snapshot_id"],
                    "revision": expected_revision,
                    "native_revision": snapshot["native_revision"],
                    "event_instance_id": event_instance_id,
                },
                "current_event_window_context": {
                    "schema": "current-event-window-context-v1",
                    "schema_version": 1,
                    "status": "available",
                    "window_match_count": 1,
                    "event_definition_key": key,
                    "current_event_instance_id": event_instance_id,
                    "date_raw": snapshot["date_raw"],
                    "root_scope": _character_scope("root", 29037)["scope"],
                    "saved_scopes": scopes,
                    "options": _options(
                        option_count,
                        native_indices=(
                            (0, 1, 3)
                            if self.stage == "neighbor_governor"
                            else (0, 2)
                            if self.stage == "doppelganger"
                            else (0, 1, 2)
                            if self.stage in {
                                "china_yearly", "grieving_child",
                                "merchant_dispute",
                            }
                            else (1, 2, 3)
                            if self.stage == "succession"
                            else None
                        ),
                    ),
                },
            }

        def select_event_option(
            self, option_number: int, *, event_instance_id: int,
            expected_revision: int,
        ) -> dict[str, object]:
            del expected_revision
            self.selected.append(option_number)
            native_index = (
                3
                if self.stage in {"neighbor_governor", "succession"}
                else 2
                if self.stage == "doppelganger"
                else option_number - 1
            )
            if self.stage == "pip":
                assert option_number == 1
                self.stage = "flood_relief"
            elif self.stage == "flood_relief":
                assert option_number == 3
                self.stage = "new_governorship"
            elif self.stage == "new_governorship":
                assert option_number == 3
                self.stage = "forced_retirement"
            elif self.stage == "forced_retirement":
                assert option_number == 1
                self.stage = "doppelganger"
            elif self.stage == "doppelganger":
                assert option_number == 3
                self.stage = "china_yearly"
            elif self.stage == "china_yearly":
                assert option_number == 3
                self.stage = "grieving_child"
            elif self.stage == "grieving_child":
                assert option_number == 3
                self.stage = "merchant_dispute"
            elif self.stage == "merchant_dispute":
                assert option_number == 3
                self.stage = "unpaid_taxes"
            elif self.stage == "unpaid_taxes":
                assert option_number == 1
                self.stage = "emperor_assistance"
            elif self.stage == "emperor_assistance":
                assert option_number == 2
                self.stage = "scholar"
            elif self.stage == "scholar":
                assert option_number == 3
                self.stage = "learned_eunuch"
            elif self.stage == "learned_eunuch":
                assert option_number == 4
                self.stage = "equitable"
            elif self.stage == "equitable":
                assert option_number == 3
                self.stage = "local_defense"
            elif self.stage == "local_defense":
                assert option_number == 4
                self.stage = "governor_yearly"
            elif self.stage == "governor_yearly":
                assert option_number == 4
                self.stage = "governor_bargain"
            elif self.stage == "governor_bargain":
                assert option_number == 3
                self.stage = "pugnacious"
            elif self.stage == "pugnacious":
                assert option_number == 2
                self.stage = "neighbor_governor"
            elif self.stage == "neighbor_governor":
                assert option_number == 4
                self.stage = "silk_road"
            elif self.stage == "silk_road":
                assert option_number == 3
                self.stage = "arbitrary_tax"
            elif self.stage == "arbitrary_tax":
                assert option_number == 4
                self.stage = "hook_offer"
            elif self.stage == "hook_offer":
                assert option_number == 2
                self.stage = "no_secrets"
            elif self.stage == "no_secrets":
                assert option_number == 2
                self.stage = "jingcha"
            elif self.stage == "jingcha":
                assert option_number == 1
                self.stage = "hook_offer_repeat"
            elif self.stage == "hook_offer_repeat":
                assert option_number == 2
                self.stage = "self_review"
            elif self.stage == "self_review":
                assert option_number == 1
                self.stage = "secret_discovery"
            elif self.stage == "secret_discovery":
                assert option_number == 1
                self.stage = "lover_secret"
            elif self.stage == "lover_secret":
                assert option_number == 1
                self.stage = "sway_misunderstanding"
            elif self.stage == "sway_misunderstanding":
                assert option_number == 1
                self.stage = "succession"
            elif self.stage == "succession":
                assert option_number == 4
                self.stage = "m146"
            else:
                self.stage = "m147"
            return {
                "step": f"select-event-option-{option_number}",
                "accepted": True,
                "status": "submitted",
                "option_number": option_number,
                "option_index": native_index,
                "event_selection": {
                    "postcondition_verified": True,
                    "old_event_instance_id": event_instance_id,
                    "new_event_instance_id": event_instance_id + 1,
                    "selected_option_number": option_number,
                    "selected_native_option_index": native_index,
                },
            }

    service = _InterruptedService()
    result = enter_promotion_source_checkpoint_v1(
        service, poll_interval_seconds=0
    )
    assert result["result"] == "GREEN"
    assert [
        row["event_definition_key"]
        for row in result["timeline_interrupt_drains"]
    ] == [
        "zg361b2.40",
        "ep3_governor_yearly.8120",
        "ep3_admin_events.0002",
        "ep3_interactions_events.0630",
        "bp1_yearly.9007",
        "tgp_china_yearly.0010",
        "tgp_china_yearly.0005",
        "tgp_china_yearly.0015",
        "tgp_china_yearly.0020",
        "ep3_emperor_yearly.2200",
        "ep3_emperor_yearly.2240",
        "ep1_flavor.1200",
        "ep3_governor_yearly.8160",
        "ep3_governor_yearly.8170",
        "ep3_governor_yearly.8060",
        "ep3_governor_yearly.8010",
        "ep3_governor_yearly.8110",
        "ep3_governor_yearly.8100",
        "tgp_dynastic_cycle_events.0040",
        "ep3_governor_yearly.8130",
        "spymaster_task.0381",
        "spymaster_task.0399",
        "zg361.40",
        "spymaster_task.0381",
        "zg361b1.200",
        "spymaster_task.0342",
        "spymaster_task.0346",
        "sway_outcome.2001",
        "ep3_governor_yearly.3060",
    ]
    assert service.selected == [1, 3, 3, 1, 3, 3, 3, 3, 1, 2, 3, 4, 3, 4, 4, 3, 2, 4, 3, 4, 2, 2, 1, 2, 1, 1, 1, 1, 4, 1]


def test_product_path_rejects_interrupt_identity_drift_before_action() -> None:
    class _DriftedInterruptedService(_Service):
        def snapshot(self) -> dict[str, object]:
            if self.stage != "pip":
                return super().snapshot()
            return {
                "snapshot_id": "snapshot-pip",
                "revision": 30,
                "native_revision": 130,
                "date_raw": 53147040,
                "paused": True,
                "speed": 1,
                "map_ready": True,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 7},
                "active_event": {"instance_id": 400, "option_count": 3},
            }

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            del expected_revision
            if step == "resume-map" and self.stage == "b1":
                self.stage = "pip"
            return {"accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            snapshot = self.snapshot()
            return {
                "status": "available",
                "binding": {
                    "snapshot_id": snapshot["snapshot_id"],
                    "revision": expected_revision,
                    "native_revision": snapshot["native_revision"],
                    "event_instance_id": event_instance_id,
                },
                "current_event_window_context": {
                    "schema": "current-event-window-context-v1",
                    "schema_version": 1,
                    "status": "available",
                    "window_match_count": 1,
                    "event_definition_key": "zg361b2.40",
                    "current_event_instance_id": event_instance_id,
                    "date_raw": snapshot["date_raw"],
                    "root_scope": _character_scope("root", 29037)["scope"],
                    "saved_scopes": [
                        _character_scope("zg361_reviewing_superior", 99999),
                        _character_scope("zg361_b2_pip_prompt_owner", 32904),
                        _character_scope("zg361_b2_pip_prompt_subject", 29037),
                        _character_scope("zga_personal_result_target", 29037),
                    ],
                    "options": _options(3),
                },
            }

    service = _DriftedInterruptedService()
    with pytest.raises(
        PromotionProductionEntryError,
        match=r"zg361b2\.40.*scope:zg361_reviewing_superior",
    ):
        enter_promotion_source_checkpoint_v1(
            service, poll_interval_seconds=0
        )
    assert service.selected == []


def test_grieving_child_contract_binds_dynamic_parent_relationship() -> None:
    scopes = [
        _character_scope("grieving_child", 16780191),
        _character_scope("orphan_mother", 16780218),
        _character_scope("orphan_father", 16780221),
        _character_scope("parent", 16780221),
        _character_scope("guardian", 31647),
        _character_scope("messenger", 31003),
    ]
    snapshot = {
        "date_raw": 53147520,
        "active_event": {"option_count": 4},
    }
    event = {"event_instance_id": 5}
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "tgp_china_yearly.0005",
        "current_event_instance_id": 5,
        "date_raw": 53147520,
        "root_scope": _character_scope("root", 29037)["scope"],
        "saved_scopes": scopes,
        "options": _options(3, native_indices=(0, 1, 2)),
    }
    contract = KNOWN_TIMELINE_INTERRUPTS["tgp_china_yearly.0005"]
    checks = _known_interrupt_checks(
        snapshot=snapshot,
        event=event,
        context=context,
        event_key="tgp_china_yearly.0005",
        contract=contract,
    )
    assert all(checks.values())

    scopes[3] = _character_scope("parent", 16780299)
    checks = _known_interrupt_checks(
        snapshot=snapshot,
        event=event,
        context=context,
        event_key="tgp_china_yearly.0005",
        contract=contract,
    )
    assert checks["scope:parent:matches_any"] is False


def test_unavailable_progress_reports_native_reason_and_widgets() -> None:
    class _UnavailableService(_Service):
        def query_zhongguo_promotion_source_progress_v1(
            self, request_nonce: str, *, expected_revision: int
        ) -> dict[str, object]:
            del request_nonce, expected_revision
            return {
                "status": "unavailable",
                "zhongguo_promotion_source_progress": {
                    "unavailable_reason": "widget_not_instantiated",
                    "widgets": [
                        {
                            "runtime_name": name,
                            "exists": _typed(index == 0),
                        }
                        for index, name in enumerate(PROGRESS_WIDGETS)
                    ],
                },
            }

    with pytest.raises(
        PromotionProductionEntryError,
        match=(
            "reason='widget_not_instantiated'.*"
            "zg361_promotion_source_review_now_action"
        ),
    ):
        enter_promotion_source_checkpoint_v1(
            _UnavailableService(), poll_interval_seconds=0
        )


def test_source_contract_and_product_share_exact_entry() -> None:
    decision = (ROOT / "mod_zhongguo_style/common/decisions/zg361_decisions.txt").read_text(encoding="utf-8-sig")
    triggers = (ROOT / "mod_zhongguo_style/common/scripted_triggers/zg361_triggers.txt").read_text(encoding="utf-8-sig")
    gui = (ROOT / "mod_zhongguo_style/common/scripted_guis/zg361_promotion_source_progress_guis.txt").read_text(encoding="utf-8-sig")
    native = (ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/zhongguo_promotion_source_progress_v1.hpp").read_text(encoding="utf-8-sig")
    runner = (ROOT / "tools/run_zhongguo_acceptance.py").read_text(encoding="utf-8-sig")
    assert decision.count("zg361_review_now_business_valid_trigger = yes") == 2
    assert "zg361_review_now_business_valid_trigger = {" in triggers
    assert "add_prestige = -150" in gui
    assert "add_character_flag = zg361_review_now_pending" in gui
    assert "production_live_ready = false" in native
    assert QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY in native
    assert ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY in native
    assert "enter_promotion_source_checkpoint_v1(" in runner
    assert "03_promotion_source_production_entry.json" in runner


def test_package_adds_no_scripted_effect_monolith() -> None:
    added = ROOT / "mod_zhongguo_style/common/scripted_effects/zg361_promotion_source_progress_effects.txt"
    assert not added.exists()
