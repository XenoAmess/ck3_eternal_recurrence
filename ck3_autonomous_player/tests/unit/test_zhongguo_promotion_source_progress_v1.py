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
    PromotionProductionEntryError,
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
    assert service.selected == [1]


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
