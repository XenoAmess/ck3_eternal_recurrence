from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_scoreboard_state_contract import (  # noqa: E402
    native_frame,
    typed,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_contract import (  # noqa: E402
    ACTION_KEYS,
    ScoreboardActionRejected,
    acknowledged_zhongguo_scoreboard_action_v1,
    build_zhongguo_scoreboard_action_v1_request,
    normalize_zhongguo_scoreboard_action_v1_ack,
    plan_zhongguo_scoreboard_action_v1,
    verify_zhongguo_scoreboard_action_v1_postcondition,
)


PUBLIC_REVISION = 19
NATIVE_REVISION = 77
CONNECTION_GENERATION = 3
PLAYER = 101
PROVIDER_SESSION = "0123456789ABCDEF0123456789ABCDEF"
TREE_FINGERPRINT = "A" * 64
SEMANTIC_FINGERPRINT = "B" * 64
SCHEMA = PROJECT_ROOT / "schemas/zhongguo-scoreboard-action-v1.schema.json"
ABI = (
    PROJECT_ROOT
    / "native_bridge/research/zhongguo_scoreboard_action_v1_abi.json"
)
SOURCE_FIXTURE = (
    PROJECT_ROOT
    / "native_bridge/research/fixtures/zhongguo_scoreboard_action_v1_source_contract.json"
)
MOD_ROOT = PROJECT_ROOT.parent / "mod_zhongguo_style"

ENTRY = {
    "managed": "zg361_scoreboard_entry_managed",
    "received": "zg361_scoreboard_entry_received",
    "system": "zg361_scoreboard_entry_system",
}
TAB = {
    "managed": "zg361_scoreboard_tab_managed",
    "received": "zg361_scoreboard_tab_received",
    "system": "zg361_scoreboard_tab_system",
}
PAGE = {
    "managed": "zg361_scoreboard_page_managed",
    "received": "zg361_scoreboard_page_received",
    "system": "zg361_scoreboard_page_system",
}


def _widget(frame: dict[str, object], identity: str) -> dict[str, object]:
    widgets = frame["widgets"]
    assert isinstance(widgets, list)
    return next(item for item in widgets if item["stable_identity"] == identity)


def _set_visible(frame: dict[str, object], identity: str, visible: bool) -> None:
    row = _widget(frame, identity)
    row["local_visible"] = typed(visible)
    row["effective_visible"] = typed(visible)


def _frame(*, open_tab: str | None, entry_tab: str = "received") -> dict[str, object]:
    frame = native_frame()
    frame["request_nonce"] = "scoreboard.source"
    widgets = frame["widgets"]
    assert isinstance(widgets, list)
    for index, row in enumerate(widgets, start=1):
        row["instance_pointer"] = typed(f"0x{0x14000000 + index * 0x100:X}")
        row["vtable_pointer"] = typed("0x14506020")
        row["exists"] = typed(True)
        row["enabled"] = typed(True)
        if row["stable_identity"] not in {
            "zg361_open_scoreboard",
            "zg361_scoreboard_window",
        }:
            _set_visible(frame, row["stable_identity"], False)
    if open_tab is None:
        _set_visible(frame, ENTRY[entry_tab], True)
    else:
        _set_visible(frame, "zg361_scoreboard_modal", True)
        _set_visible(frame, "zg361_scoreboard_panel", True)
        _set_visible(frame, "zg361_scoreboard_header_close", True)
        for tab in TAB:
            _set_visible(frame, TAB[tab], True)
        _set_visible(frame, PAGE[open_tab], True)
    return frame


def _request(
    frame: dict[str, object],
    *,
    action: str,
    target_identity: str,
):
    window = _widget(frame, "zg361_scoreboard_window")
    target = _widget(frame, target_identity)
    return build_zhongguo_scoreboard_action_v1_request(
        request_nonce=f"scoreboard.action.{action}",
        action=action,
        expected_revision=PUBLIC_REVISION,
        expected_native_revision=NATIVE_REVISION,
        expected_connection_generation=CONNECTION_GENERATION,
        expected_player_character_id=PLAYER,
        expected_provider_session_id=frame["provider_session_id"],
        expected_observation_sequence=frame["observation_sequence"],
        expected_observed_state_revision=frame["observed_state_revision"],
        expected_tree_fingerprint_v1=frame["tree_fingerprint_v1"],
        expected_semantic_fingerprint_v1=frame["semantic_fingerprint_v1"],
        expected_window_instance_pointer=window["instance_pointer"]["value"],
        expected_target_instance_pointer=target["instance_pointer"]["value"],
        expected_target_vtable_pointer=target["vtable_pointer"]["value"],
    )


def _plan(frame: dict[str, object], *, action: str, target_identity: str):
    request = _request(frame, action=action, target_identity=target_identity)
    plan = plan_zhongguo_scoreboard_action_v1(
        request,
        source_state=frame,
        observed_revision=PUBLIC_REVISION,
        observed_connection_generation=CONNECTION_GENERATION,
    )
    return request, plan


def _post(
    source: dict[str, object],
    *,
    active_tab: str | None,
) -> dict[str, object]:
    frame = copy.deepcopy(source)
    frame["request_nonce"] = "scoreboard.post-query"
    frame["snapshot_revision"] = NATIVE_REVISION
    frame["observation_sequence"] = source["observation_sequence"] + 1
    frame["observed_state_revision"] = source["observed_state_revision"] + 1
    frame["semantic_fingerprint_v1"] = "C" * 64
    _set_visible(frame, "zg361_scoreboard_modal", active_tab is not None)
    _set_visible(frame, "zg361_scoreboard_panel", active_tab is not None)
    _set_visible(frame, "zg361_scoreboard_header_close", active_tab is not None)
    for tab in PAGE:
        _set_visible(frame, PAGE[tab], tab == active_tab)
    return frame


class ZhongguoScoreboardActionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)

    def test_primitive_actions_are_allowlisted_and_ack_never_claims_postcondition(self) -> None:
        cases = (
            ("open", None, "received", ENTRY["received"], "received"),
            ("switch-managed", "received", "received", TAB["managed"], "managed"),
            ("switch-received", "managed", "received", TAB["received"], "received"),
            ("switch-system", "managed", "received", TAB["system"], "system"),
            ("close", "received", "received", "zg361_scoreboard_header_close", None),
        )
        self.assertEqual({row[0] for row in cases} | {"reopen"}, ACTION_KEYS)
        for action, open_tab, entry_tab, target, expected_tab in cases:
            with self.subTest(action=action):
                frame = _frame(open_tab=open_tab, entry_tab=entry_tab)
                if action == "switch-managed":
                    frame["acl"]["managed"]["surface_available"] = True
                    frame["acl"]["managed"][
                        "current_player_can_assess_others"
                    ] = True
                request, plan = _plan(frame, action=action, target_identity=target)
                ack = acknowledged_zhongguo_scoreboard_action_v1(plan)
                normalized = normalize_zhongguo_scoreboard_action_v1_ack(
                    ack, expected_request=request
                )
                Draft202012Validator(self.schema).validate(normalized)
                self.assertFalse(normalized["postcondition_verified"])
                self.assertEqual(normalized["target"]["stable_identity"], target)
                self.assertEqual(
                    normalized["expected_postcondition"]["active_tab"],
                    expected_tab,
                )
                post = _post(frame, active_tab=expected_tab)
                proof = verify_zhongguo_scoreboard_action_v1_postcondition(
                    normalized,
                    post_state=post,
                    observed_revision=PUBLIC_REVISION,
                    observed_connection_generation=CONNECTION_GENERATION,
                )
                self.assertTrue(proof["postcondition_verified"])
                self.assertEqual(proof["active_tab"], expected_tab)

        reopen_frame = _frame(open_tab=None, entry_tab="system")
        reopen_request = _request(
            reopen_frame,
            action="reopen",
            target_identity=ENTRY["system"],
        )
        with self.assertRaisesRegex(
            ScoreboardActionRejected,
            "reopen_requires_two_phase_sequence",
        ):
            plan_zhongguo_scoreboard_action_v1(
                reopen_request,
                source_state=reopen_frame,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )

    def test_request_has_no_widget_name_coordinate_or_character_scope_escape_hatch(self) -> None:
        frame = _frame(open_tab=None)
        request = _request(
            frame, action="open", target_identity=ENTRY["received"]
        )
        self.assertEqual(
            set(request.__dataclass_fields__),
            {
                "request_nonce",
                "action",
                "expected_revision",
                "expected_native_revision",
                "expected_connection_generation",
                "expected_player_character_id",
                "expected_provider_session_id",
                "expected_observation_sequence",
                "expected_observed_state_revision",
                "expected_tree_fingerprint_v1",
                "expected_semantic_fingerprint_v1",
                "expected_window_instance_pointer",
                "expected_target_instance_pointer",
                "expected_target_vtable_pointer",
            },
        )
        for bad in ("bad/widget", "", "a" * 65):
            with self.assertRaises(ValueError):
                build_zhongguo_scoreboard_action_v1_request(
                    request_nonce=bad,
                    action="open",
                    expected_revision=1,
                    expected_native_revision=1,
                    expected_connection_generation=1,
                    expected_player_character_id=1,
                    expected_provider_session_id=PROVIDER_SESSION,
                    expected_observation_sequence=1,
                    expected_observed_state_revision=1,
                    expected_tree_fingerprint_v1=TREE_FINGERPRINT,
                    expected_semantic_fingerprint_v1=SEMANTIC_FINGERPRINT,
                    expected_window_instance_pointer="0x1",
                    expected_target_instance_pointer="0x2",
                    expected_target_vtable_pointer="0x3",
                )
        with self.assertRaises(ValueError):
            build_zhongguo_scoreboard_action_v1_request(
                request_nonce="ok",
                action="click-arbitrary-widget",
                expected_revision=1,
                expected_native_revision=1,
                expected_connection_generation=1,
                expected_player_character_id=1,
                expected_provider_session_id=PROVIDER_SESSION,
                expected_observation_sequence=1,
                expected_observed_state_revision=1,
                expected_tree_fingerprint_v1=TREE_FINGERPRINT,
                expected_semantic_fingerprint_v1=SEMANTIC_FINGERPRINT,
                expected_window_instance_pointer="0x1",
                expected_target_instance_pointer="0x2",
                expected_target_vtable_pointer="0x3",
            )

    def test_stale_or_rebound_request_fails_before_dispatch(self) -> None:
        frame = _frame(open_tab=None)
        request = _request(
            frame, action="open", target_identity=ENTRY["received"]
        )
        cases = (
            ("revision_mismatch", {"observed_revision": PUBLIC_REVISION + 1}),
            (
                "connection_generation_mismatch",
                {"observed_connection_generation": CONNECTION_GENERATION + 1},
            ),
        )
        for reason, override in cases:
            with self.subTest(reason=reason):
                kwargs = {
                    "source_state": copy.deepcopy(frame),
                    "observed_revision": PUBLIC_REVISION,
                    "observed_connection_generation": CONNECTION_GENERATION,
                    **override,
                }
                with self.assertRaisesRegex(ScoreboardActionRejected, reason):
                    plan_zhongguo_scoreboard_action_v1(request, **kwargs)
        rebound = copy.deepcopy(frame)
        rebound["player_character_id"] = 202
        with self.assertRaisesRegex(
            ScoreboardActionRejected, "player_binding_mismatch"
        ):
            plan_zhongguo_scoreboard_action_v1(
                request,
                source_state=rebound,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )

    def test_non_player_missing_hidden_disabled_and_unfrozen_enabled_fail_closed(self) -> None:
        base = _frame(open_tab=None)
        request = _request(
            base, action="open", target_identity=ENTRY["received"]
        )
        mutations = []
        non_player = copy.deepcopy(base)
        non_player["readiness"]["player_binding_ready"] = False
        mutations.append(("player_or_same_frame_not_ready", non_player))
        missing = copy.deepcopy(base)
        _widget(missing, ENTRY["received"])["exists"] = typed(False)
        mutations.append(("target_not_instantiated", missing))
        hidden = copy.deepcopy(base)
        _set_visible(hidden, ENTRY["received"], False)
        mutations.append(("entry_target_not_unique", hidden))
        disabled = copy.deepcopy(base)
        _widget(disabled, ENTRY["received"])["enabled"] = typed(False)
        mutations.append(("target_disabled", disabled))
        unavailable_enabled = copy.deepcopy(base)
        _widget(unavailable_enabled, ENTRY["received"])["enabled"] = {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "enabled_state_abi_not_frozen",
        }
        mutations.append(("target_enabled_unavailable", unavailable_enabled))
        for reason, frame in mutations:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ScoreboardActionRejected, reason):
                    plan_zhongguo_scoreboard_action_v1(
                        request,
                        source_state=frame,
                        observed_revision=PUBLIC_REVISION,
                        observed_connection_generation=CONNECTION_GENERATION,
                    )

    def test_acl_and_exact_instance_identity_are_enforced(self) -> None:
        frame = _frame(open_tab="received")
        managed = _request(
            frame,
            action="switch-managed",
            target_identity=TAB["managed"],
        )
        with self.assertRaisesRegex(ScoreboardActionRejected, "managed_acl_denied"):
            plan_zhongguo_scoreboard_action_v1(
                managed,
                source_state=frame,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )
        frame["acl"]["managed"]["surface_available"] = True
        frame["acl"]["managed"]["current_player_can_assess_others"] = True
        rebound = copy.deepcopy(frame)
        _widget(rebound, TAB["managed"])["instance_pointer"] = typed("0xDEADBEEF")
        with self.assertRaisesRegex(
            ScoreboardActionRejected, "target_instance_mismatch"
        ):
            plan_zhongguo_scoreboard_action_v1(
                managed,
                source_state=rebound,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )

    def test_ack_is_not_a_postcondition_and_stale_post_query_is_rejected(self) -> None:
        frame = _frame(open_tab=None)
        request, plan = _plan(
            frame, action="open", target_identity=ENTRY["received"]
        )
        ack = normalize_zhongguo_scoreboard_action_v1_ack(
            acknowledged_zhongguo_scoreboard_action_v1(plan),
            expected_request=request,
        )
        post = _post(frame, active_tab="received")
        for reason, revision, native_revision, nonce in (
            ("post_revision_mismatch", PUBLIC_REVISION + 1, NATIVE_REVISION, "post"),
            ("post_native_revision_mismatch", PUBLIC_REVISION, NATIVE_REVISION + 1, "post"),
            (
                "post_query_nonce_not_independent",
                PUBLIC_REVISION,
                NATIVE_REVISION,
                request.request_nonce,
            ),
        ):
            with self.subTest(reason=reason):
                candidate = copy.deepcopy(post)
                candidate["snapshot_revision"] = native_revision
                candidate["request_nonce"] = nonce
                with self.assertRaisesRegex(ScoreboardActionRejected, reason):
                    verify_zhongguo_scoreboard_action_v1_postcondition(
                        ack,
                        post_state=candidate,
                        observed_revision=revision,
                        observed_connection_generation=CONNECTION_GENERATION,
                    )
        missing_nonce = copy.deepcopy(post)
        missing_nonce.pop("request_nonce")
        with self.assertRaisesRegex(
            ScoreboardActionRejected, "post_query_nonce_unavailable"
        ):
            verify_zhongguo_scoreboard_action_v1_postcondition(
                ack,
                post_state=missing_nonce,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )
        with self.assertRaisesRegex(
            ScoreboardActionRejected, "ack_binding_unavailable"
        ):
            verify_zhongguo_scoreboard_action_v1_postcondition(
                {},
                post_state=post,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )

    def test_schema_and_normalizer_reject_ack_expansion_or_false_success(self) -> None:
        frame = _frame(open_tab=None)
        request, plan = _plan(
            frame, action="open", target_identity=ENTRY["received"]
        )
        ack = acknowledged_zhongguo_scoreboard_action_v1(plan)
        expanded = copy.deepcopy(ack)
        expanded["screen_x"] = 1
        with self.assertRaises(ValueError):
            normalize_zhongguo_scoreboard_action_v1_ack(
                expanded, expected_request=request
            )
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(expanded)
        false_success = copy.deepcopy(ack)
        false_success["postcondition_verified"] = True
        with self.assertRaises(ValueError):
            normalize_zhongguo_scoreboard_action_v1_ack(
                false_success, expected_request=request
            )
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(false_success)

    def test_source_contract_freezes_names_and_keeps_live_blockers_explicit(self) -> None:
        abi = json.loads(ABI.read_text(encoding="utf-8"))
        fixture = json.loads(SOURCE_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(set(abi["actions"]), ACTION_KEYS)
        self.assertEqual(set(fixture["actions"]), ACTION_KEYS)
        self.assertEqual(abi["ack"]["postcondition_verified"], False)
        self.assertEqual(
            fixture["production_executor"],
            "exact_dispatch_ack_verification_pending",
        )
        self.assertEqual(
            fixture["shared_transport"], "wired_ack_or_typed_unavailable"
        )
        self.assertNotIn(
            "effective_enabled_semantics", abi["exact_build_blockers"]
        )
        self.assertEqual(
            abi["enabled_abi"]["effective_disabled_mask"], "0x02"
        )
        self.assertEqual(
            abi["disproven_dispatch_candidates"][0]["rva"],
            "0x36C6A90",
        )
        gui = (MOD_ROOT / "gui/zg361_scoreboard.gui").read_text(
            encoding="utf-8-sig"
        )
        for identity in (*TAB.values(), *PAGE.values()):
            self.assertEqual(gui.count(f'name = "{identity}"'), 1, identity)
        native = (
            PROJECT_ROOT
            / "native_bridge/src/zhongguo_scoreboard_action_v1.cpp"
        ).read_text(encoding="utf-8")
        self.assertNotIn("SendInput", native)
        self.assertNotIn("screen_x", native)
        self.assertNotIn("0x36C6A90", native)


if __name__ == "__main__":
    unittest.main()
