#!/usr/bin/env python3
"""Purpose-split contracts for incidental manager-cycle event drains."""

from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


def _scope(
    name: str,
    type_key: str,
    character_id: int | None = None,
    *,
    unavailable_character: bool = False,
) -> dict[str, object]:
    if character_id is not None:
        typed_identity: dict[str, object] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    else:
        typed_identity = {
            "status": "unavailable",
            "reason": (
                "character_scope_identity_unavailable"
                if unavailable_character
                else "generic_scope_payload_identity_not_closed"
            ),
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": typed_identity,
        },
    }


def _context(
    *,
    event_key: str,
    instance_id: int,
    date_raw: int,
    player: int,
    scopes: list[dict[str, object]],
    native_option_indices: tuple[int, ...],
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": event_key,
        "current_event_instance_id": instance_id,
        "date_raw": date_raw,
        "root_scope": _scope("root", "character", player)["scope"],
        "saved_scopes": scopes,
        "options": [
            {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for rendered, native in enumerate(native_option_indices)
        ],
    }


def _manager_contract(event_key: str, *, player: int) -> dict[str, object]:
    contract = production._manager_recovery_contract(
        production.KNOWN_TIMELINE_INTERRUPTS[event_key],
        player=player,
        event_key=event_key,
    )
    return production._timeline_contract_for_window(
        contract,
        starting_date=53147016,
    )


def _extract_block(source: str, header: str) -> str:
    header_index = source.index(header)
    open_index = source.index("{", header_index + len(header))
    depth = 0
    for index in range(open_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[header_index:index + 1]
    raise AssertionError(f"unterminated source block: {header}")


def _human_tribute_scopes() -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 34077),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", 54393),
        _scope("intermediary", "character", unavailable_character=True),
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 34077),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("concubine_character", "character", 54393),
        _scope("human_tribute", "character", 54393),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
    ]


class ManagerRecoveryInterruptTests(unittest.TestCase):
    def test_cold_import_preserves_existing_canonical_contract_identity(
        self,
    ) -> None:
        from xar_autoplayer import vanilla_events
        from xar_autoplayer.vanilla_events import records_embedded

        event_key = "stress_threshold.1721"
        package_before = vanilla_events.VANILLA_EVENT_TIMELINE_CONTRACTS[
            event_key
        ]
        leaf_before = records_embedded.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[
            event_key
        ]
        module_name = "_xar_production_entry_cold_import_regression"
        spec = importlib.util.spec_from_file_location(
            module_name, Path(production.__file__)
        )
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        cold_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = cold_module
        try:
            spec.loader.exec_module(cold_module)
        finally:
            sys.modules.pop(module_name, None)

        self.assertIs(
            vanilla_events.VANILLA_EVENT_TIMELINE_CONTRACTS[event_key],
            package_before,
        )
        self.assertIs(
            records_embedded.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key],
            leaf_before,
        )
        self.assertIs(cold_module.KNOWN_TIMELINE_INTERRUPTS[event_key], leaf_before)

    def test_reload_refreshes_nested_shared_vanilla_contract(self) -> None:
        source = f"""
import importlib
from pathlib import Path
import sys

root = Path({str(ROOT)!r})
sys.path.insert(0, str(root / "tools"))
sys.path.insert(0, str(root / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production
import zg361_phase2_promotion_career_hc_contracts as career_hc
from xar_autoplayer.vanilla_events import records_embedded, records_tgp_dynastic_cycle

event_key = "stress_threshold.1721"
before = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
product_event_key = "zg361ch.950"
product_before = production.KNOWN_TIMELINE_INTERRUPTS[product_event_key]
reloaded = importlib.reload(production)
canonical = records_embedded.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key]
product_canonical = career_hc.CAREER_HC_TIMELINE_CONTRACTS[product_event_key]
if reloaded is not production:
    raise SystemExit("production module identity changed")
if production.KNOWN_TIMELINE_INTERRUPTS[event_key] is not canonical:
    raise SystemExit("production contract is not the canonical leaf contract")
if canonical is before:
    raise SystemExit("reload retained the stale canonical contract")
if production.KNOWN_TIMELINE_INTERRUPTS[product_event_key] is not product_canonical:
    raise SystemExit("production contract is not the refreshed career/HC leaf")
if product_canonical is product_before:
    raise SystemExit("reload retained the stale career/HC contract")
if product_canonical.get("occurrence_policy") != (
    "repeatable-within-product-observation-window"
):
    raise SystemExit("career/HC portfolio did not retain repeatable policy")
no_confidant = canonical["scope_variants"][0]
if no_confidant["selected_option_number"] != 11:
    raise SystemExit("wrong no-confidant authored option")
if no_confidant["selected_native_option_index"] != 10:
    raise SystemExit("wrong no-confidant native option")

# A live process may reload from an older module generation that predates the
# initialization sentinel. Its existing contract mapping is the durable reload
# signal in that deployment case.
new_event_key = "tgp_dynastic_cycle_events.0001"
production.KNOWN_TIMELINE_INTERRUPTS.pop(new_event_key, None)
records_tgp_dynastic_cycle.VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS.pop(
    new_event_key, None
)
del production._PRODUCTION_ENTRY_INITIALIZED
reloaded = importlib.reload(production)
if new_event_key not in reloaded.KNOWN_TIMELINE_INTERRUPTS:
    raise SystemExit("legacy-generation reload did not refresh new records")
"""
        command = [sys.executable]
        if not __debug__:
            command.append("-O")
        command.extend(("-c", source))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=(
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ),
        )

    def test_central_summary_allows_two_observed_cycle_terminals(self) -> None:
        event_key = "zg361p2c.2"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53199480,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract["option_count"], 1)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 2)

        completed = [
            {"event_definition_key": event_key, "date_raw": 53201136},
            {"event_definition_key": event_key, "date_raw": 53217456},
        ]
        max_occurrences = int(contract["max_occurrences"])

        def next_occurrence_allowed(rows: list[dict[str, object]]) -> bool:
            occurrence_count = sum(
                row.get("event_definition_key") == event_key for row in rows
            )
            return occurrence_count < max_occurrences

        self.assertTrue(next_occurrence_allowed([]))
        self.assertTrue(next_occurrence_allowed(completed[:1]))
        self.assertFalse(next_occurrence_allowed(completed))

    def test_career_hc_portfolio_repeats_with_exact_safe_route(self) -> None:
        event_key = "zg361ch.950"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53447000,
            absolute_end_date=53490000,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(contract["option_count"], 4)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        for instance_id, date_raw, subject_id in (
            (682, 53447664, 36160),
            (876, 53488512, 36160),
        ):
            context = _context(
                event_key=event_key,
                instance_id=instance_id,
                date_raw=date_raw,
                player=32904,
                scopes=[
                    _scope("zg361_ch_d_event_owner", "character", 32904),
                    _scope(
                        "zg361_ch_d_event_subject", "character", subject_id,
                    ),
                    _scope("zg361_ch_d_event_cycle", "value"),
                    _scope("zg361_ch_d_event_case", "value"),
                ],
                native_option_indices=(0, 1, 2, 3),
            )
            checks = production._known_interrupt_checks(
                snapshot={
                    "date_raw": date_raw,
                    "active_event": {"option_count": 4},
                },
                event={"event_instance_id": instance_id},
                context=context,
                event_key=event_key,
                contract=contract,
            )
            self.assertTrue(all(checks.values()), checks)

    def test_value_track_card_repeats_with_exact_safe_route(self) -> None:
        event_key = "zg361.30"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53447000,
            absolute_end_date=53490000,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(contract["option_count"], 2)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        for instance_id, date_raw in (
            (681, 53447664),
            (875, 53488512),
        ):
            context = _context(
                event_key=event_key,
                instance_id=instance_id,
                date_raw=date_raw,
                player=32904,
                scopes=[
                    _scope("zg361_n_dog", "value"),
                    _scope("zg361_n_rabbit", "value"),
                ],
                native_option_indices=(0, 1),
            )
            checks = production._known_interrupt_checks(
                snapshot={
                    "date_raw": date_raw,
                    "active_event": {"option_count": 2},
                },
                event={"event_instance_id": instance_id},
                context=context,
                event_key=event_key,
                contract=contract,
            )
            self.assertTrue(all(checks.values()), checks)

    def test_late_pause_target_enables_pp_and_three_cycle_workforce_routes(
        self,
    ) -> None:
        pp = production._resolve_timeline_interrupt_contract(
            "zg361pp.147",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(pp)
        assert pp is not None
        self.assertEqual(pp["selected_native_option_index"], 0)

        workforce = production._resolve_timeline_interrupt_contract(
            "zg361we.355",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(workforce)
        assert workforce is not None
        self.assertEqual(workforce["option_count"], 3)
        self.assertEqual(workforce["selected_native_option_index"], 0)
        self.assertEqual(workforce["max_occurrences"], 3)
        self.assertEqual(
            workforce["workforce_three_cycle_route"],
            "prefer-non-debt-with-authored-fallback",
        )

        handoff_timeout = production._resolve_timeline_interrupt_contract(
            "zg361we.264",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(handoff_timeout)
        assert handoff_timeout is not None
        fallback_projection = production._option_contract_for_context(
            [{"native_option_index": 2}], handoff_timeout,
        )
        self.assertEqual(fallback_projection["option_count"], 1)
        self.assertEqual(fallback_projection["selected_option_number"], 3)
        self.assertEqual(fallback_projection["selected_native_option_index"], 2)

        fraud_audit = production._resolve_timeline_interrupt_contract(
            "zg361we.265",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(fraud_audit)
        assert fraud_audit is not None
        debt_projection = production._option_contract_for_context(
            [{"native_option_index": 2}], fraud_audit,
        )
        self.assertEqual(debt_projection["option_count"], 1)
        self.assertEqual(debt_projection["selected_option_number"], 3)
        self.assertEqual(debt_projection["selected_native_option_index"], 2)

        annual_summary = production._resolve_timeline_interrupt_contract(
            "zg361.1",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(annual_summary)
        assert annual_summary is not None
        self.assertEqual(annual_summary["option_count"], 1)
        self.assertEqual(annual_summary["selected_native_option_index"], 0)
        self.assertEqual(annual_summary["character_scopes"], {})
        self.assertEqual(annual_summary["scope_types"], {})
        self.assertNotIn("saved_scope_name_sets", annual_summary)
        self.assertEqual(
            annual_summary["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        elimination = production._resolve_timeline_interrupt_contract(
            "zg361.5",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(elimination)
        assert elimination is not None
        self.assertEqual(elimination["option_count"], 3)
        self.assertEqual(elimination["selected_native_option_index"], 2)
        self.assertEqual(elimination["character_scopes"], {})
        self.assertEqual(elimination["scope_types"], {})
        self.assertNotIn("saved_scope_name_sets", elimination)
        self.assertEqual(
            elimination["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        project_cycle = production._resolve_timeline_interrupt_contract(
            "zg361cp.31",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(project_cycle)
        assert project_cycle is not None
        self.assertEqual(project_cycle["option_count"], 3)
        self.assertEqual(project_cycle["selected_native_option_index"], 0)
        self.assertEqual(
            project_cycle["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", project_cycle)

        career_digest = production._resolve_timeline_interrupt_contract(
            "zg361cl.390",
            player=32904,
            starting_date=53313360,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(career_digest)
        assert career_digest is not None
        self.assertEqual(career_digest["option_count"], 1)
        self.assertEqual(career_digest["selected_native_option_index"], 0)
        self.assertEqual(
            career_digest["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("saved_scope_name_sets", career_digest)

        handoff = production._resolve_timeline_interrupt_contract(
            "zg361we.5264",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(handoff)
        assert handoff is not None
        owner_projection = production._option_contract_for_context(
            [
                {"native_option_index": 2},
                {"native_option_index": 3},
            ],
            handoff,
        )
        self.assertEqual(owner_projection["option_count"], 2)
        self.assertEqual(owner_projection["selected_option_number"], 3)
        self.assertEqual(owner_projection["selected_native_option_index"], 2)

    def test_pause_target_occurrence_counts_only_prior_target_drains(self) -> None:
        drains = [
            {"event_definition_key": "zg361we.355"},
            {"event_definition_key": "zg361we.356"},
            {"event_definition_key": "zg361pp.147"},
            {"event_definition_key": "zg361we.356"},
        ]
        self.assertEqual(
            production._pause_target_occurrence_index(
                "zg361we.356",
                pause_on_event_definition_key="zg361we.356",
                timeline_interrupt_drains=drains,
            ),
            3,
        )
        self.assertIsNone(
            production._pause_target_occurrence_index(
                "zg361we.355",
                pause_on_event_definition_key="zg361we.356",
                timeline_interrupt_drains=drains,
            )
        )

    def test_hot_recovery_retains_prior_target_drains(self) -> None:
        initial = {
            "map_ready": True,
            "revision": 2072,
            "native_revision": 2071,
            "snapshot_id": "native:2071",
            "date_raw": 53268288,
            "paused": True,
            "played_character": {"character_id": 32904},
            "diagnostics": {
                "connection_generation": 1,
                "bridge_pid": 69176,
            },
        }
        target_binding = {
            "event_instance_id": 531,
            "revision": 2072,
        }
        retained_drains = [
            {"event_definition_key": "zg361cl.390", "result": "GREEN"},
            {"event_definition_key": "zg361we.356", "result": "GREEN"},
            {"event_definition_key": "zg361we.356", "result": "GREEN"},
        ]
        evidence: dict[str, object] = {
            "timeline_interrupt_drains": copy.deepcopy(retained_drains),
        }
        service = type("Service", (), {"snapshot": lambda self: initial})()

        with (
            mock.patch.object(
                production,
                "_binding",
                return_value=(initial, target_binding),
            ),
            mock.patch.object(
                production,
                "_event_definition",
                return_value=("zg361we.356", {"status": "available"}),
            ),
        ):
            result = production.enter_promotion_source_checkpoint_v1(
                service,
                pause_on_event_definition_key="zg361we.356",
                pause_on_event_occurrence=3,
                evidence_out=evidence,
            )

        self.assertIs(result, evidence)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["target_occurrence_index"], 3)
        self.assertEqual(result["timeline_interrupt_drains"], retained_drains)
        self.assertEqual(result["retained_timeline_interrupt_drain_count"], 3)

    def test_clean_boundary_recovery_keeps_known_vanilla_contract(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            "tribute_mission.1002",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=True,
        )

        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertTrue(contract["manager_recovery_only"])
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["saved_scope_count"], 14)

        pp_fallback = production._resolve_timeline_interrupt_contract(
            "zg361pp.146",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=True,
        )
        self.assertIsNotNone(pp_fallback)
        assert pp_fallback is not None
        self.assertEqual(pp_fallback["selected_native_option_index"], 0)

        known_pp = production._resolve_timeline_interrupt_contract(
            "zg361pp.149",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=True,
        )
        self.assertIsNotNone(known_pp)
        assert known_pp is not None
        self.assertTrue(known_pp["manager_recovery_only"])
        self.assertNotIn("saved_scope_name_sets", known_pp)
        self.assertEqual(known_pp["option_count"], 3)
        self.assertEqual(known_pp["selected_native_option_index"], 0)
        two_option_projection = production._option_contract_for_context(
            [
                {"native_option_index": 0},
                {"native_option_index": 1},
            ],
            known_pp,
        )
        self.assertEqual(two_option_projection["option_count"], 2)
        self.assertEqual(
            two_option_projection["native_option_indices"], (0, 1)
        )
        route_c_only_projection = production._option_contract_for_context(
            [{"native_option_index": 2}],
            known_pp,
        )
        self.assertEqual(route_c_only_projection["option_count"], 1)
        self.assertEqual(
            route_c_only_projection["native_option_indices"], (2,)
        )
        self.assertEqual(
            route_c_only_projection["snapshot_option_counts"], (1, 3)
        )
        self.assertEqual(
            production._snapshot_option_counts(route_c_only_projection),
            (1, 3),
        )
        self.assertEqual(route_c_only_projection["selected_option_number"], 3)
        self.assertEqual(
            route_c_only_projection["selected_native_option_index"], 2
        )
        route_c_context = _context(
            event_key="zg361pp.179",
            instance_id=295,
            date_raw=53147016,
            player=32904,
            scopes=[],
            native_option_indices=(2,),
        )
        route_c_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53147016,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 295},
            context=route_c_context,
            event_key="zg361pp.179",
            contract=known_pp,
        )
        self.assertTrue(all(route_c_checks.values()), route_c_checks)
        reordered_projection = production._option_contract_for_context(
            [
                {"native_option_index": 2},
                {"native_option_index": 0},
            ],
            known_pp,
        )
        self.assertEqual(reordered_projection["option_count"], 3)
        self.assertEqual(
            reordered_projection["native_option_indices"], (0, 1, 2)
        )

        credit_project = production._resolve_timeline_interrupt_contract(
            "zg361cp.30",
            player=32904,
            starting_date=53246664,
            stop_at_clean_review_boundary=True,
        )
        self.assertIsNotNone(credit_project)
        assert credit_project is not None
        self.assertTrue(credit_project["manager_recovery_only"])
        self.assertEqual(credit_project["character_scopes"], {})
        self.assertEqual(credit_project["scope_types"], {})
        self.assertNotIn("saved_scope_name_sets", credit_project)
        self.assertEqual(credit_project["option_count"], 3)
        self.assertEqual(credit_project["selected_option_number"], 1)
        self.assertEqual(credit_project["selected_native_option_index"], 0)

        self.assertIsNone(
            production._resolve_timeline_interrupt_contract(
                "unreviewed_vanilla.1",
                player=32904,
                starting_date=53147016,
                stop_at_clean_review_boundary=True,
            )
        )

    def test_random_bad_nickname_uses_only_visible_authored_option(self) -> None:
        event_key = "lifestyle_nicknames.1000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=24,
            date_raw=53158896,
            player=32904,
            scopes=[
                _scope("possible_conqueror", "character", 32904),
                _scope("toggle_null_result", "boolean"),
                _scope("nickname_root_scope", "character", 32904),
                _scope("had_nick_the_mad", "boolean"),
                _scope("nickname_getter", "character", 32904),
                _scope("informer", "character", 28314),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158896,
                "active_event": {"option_count": 6},
            },
            event={"event_instance_id": 24},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["character_scopes"],
            {
                "possible_conqueror": 32904,
                "nickname_root_scope": 32904,
                "nickname_getter": 32904,
            },
        )
        self.assertEqual(contract["snapshot_option_count"], 6)
        self.assertEqual(contract["native_option_indices"], (1,))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158896,
                "active_event": {"option_count": 6},
            },
            event={"event_instance_id": 24},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:informer:type"])
        self.assertFalse(drift_checks["scope:informer:unique_third_party"])
        self.assertFalse(drift_checks["saved_scope_names_exact"])
        self.assertFalse(drift_checks["saved_scope_count"])

    def test_murder_secret_discovery_binds_exclusive_scheme_projection(self) -> None:
        event_key = "spymaster_task.0344"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=385,
            date_raw=53269008,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 27275),
                _scope("artifact", "artifact"),
                _scope("target", "character", 29628),
                _scope("councillor_liege", "character", 32904),
                _scope("target_character", "character", 29628),
                _scope("councillor", "character", 27275),
                _scope("active_councillor", "character", 27275),
                _scope("secret_holder", "character", 28903),
                _scope("secret_to_reveal", "secret"),
                _scope("murder_target", "character", 31013),
            ],
            native_option_indices=(1,),
        )
        snapshot = {
            "date_raw": 53269008,
            "active_event": {"option_count": 2},
        }
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 385},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["saved_scope_counts"], (10, 11))
        self.assertEqual(contract["snapshot_option_count"], 2)
        current_projection = production._option_contract_for_context(
            context["options"], contract
        )
        self.assertEqual(current_projection["selected_option_number"], 2)
        self.assertEqual(current_projection["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        no_scheme = copy.deepcopy(context)
        no_scheme["saved_scopes"] = no_scheme["saved_scopes"][1:]
        no_scheme["options"] = _context(
            event_key=event_key,
            instance_id=385,
            date_raw=53269008,
            player=32904,
            scopes=[],
            native_option_indices=(0,),
        )["options"]
        no_scheme_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 385},
            context=no_scheme,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(no_scheme_checks.values()), no_scheme_checks)
        plain_projection = production._option_contract_for_context(
            no_scheme["options"], contract
        )
        self.assertEqual(plain_projection["selected_option_number"], 1)
        self.assertEqual(plain_projection["selected_native_option_index"], 0)

        same_murderer_and_victim = copy.deepcopy(context)
        same_murderer_and_victim["saved_scopes"][-1] = _scope(
            "murder_target", "character", 28903
        )
        drift_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 385},
            context=same_murderer_and_victim,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:murder_target:differs_from"]
        )

    def test_lover_secret_discovery_accepts_complete_task_frame(self) -> None:
        event_key = "spymaster_task.0346"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=410,
            date_raw=53298480,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 30434),
                _scope("artifact", "artifact"),
                _scope("target", "character", 31130),
                _scope("councillor_liege", "character", 32904),
                _scope("target_character", "character", 31130),
                _scope("councillor", "character", 30434),
                _scope("active_councillor", "character", 30434),
                _scope("secret_holder", "character", 33951),
                _scope("secret_to_reveal", "secret"),
                _scope("lover", "character", 48808),
            ],
            native_option_indices=(0,),
        )
        snapshot = {
            "date_raw": 53298480,
            "active_event": {"option_count": 1},
        }
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 410},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["saved_scope_count"], 11)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        legacy_context = _context(
            event_key=event_key,
            instance_id=62,
            date_raw=53152920,
            player=32904,
            scopes=[
                _scope("councillor", "character", 27963),
                _scope("councillor_liege", "character", 32904),
                _scope("target_character", "character", 27051),
                _scope("active_councillor", "character", 27963),
                _scope("secret_holder", "character", 27051),
                _scope("secret_to_reveal", "secret"),
                _scope("lover", "character", 45267),
                _scope("having_find_secrets_event", "boolean"),
            ],
            native_option_indices=(0,),
        )
        legacy_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53152920,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 62},
            context=legacy_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(legacy_checks.values()), legacy_checks)

        mixed_context = copy.deepcopy(context)
        mixed_context["saved_scopes"].append(
            _scope("having_find_secrets_event", "boolean")
        )
        mixed_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 410},
            context=mixed_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(mixed_checks["saved_scope_names_exact"])
        self.assertFalse(mixed_checks["saved_scope_count"])

    def test_fallback_secret_discovery_is_repeatable_per_task_outcome(self) -> None:
        event_key = "spymaster_task.0359"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=371,
            date_raw=53254608,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 27275),
                _scope("artifact", "artifact"),
                _scope("target", "character", 29628),
                _scope("councillor_liege", "character", 32904),
                _scope("target_character", "character", 29628),
                _scope("councillor", "character", 27275),
                _scope("active_councillor", "character", 27275),
                _scope("secret_holder", "character", 29628),
                _scope("secret_to_reveal", "secret"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53254608,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 371},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"], {"councillor_liege": 32904})
        self.assertEqual(contract["saved_scope_count"], 10)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        first_repeat = copy.deepcopy(context)
        first_repeat["current_event_instance_id"] = 91
        first_repeat["date_raw"] = 53178192
        first_repeat_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53178192,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 91},
            context=first_repeat,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(first_repeat_checks.values()), first_repeat_checks)

        second = copy.deepcopy(context)
        second["current_event_instance_id"] = 92
        second["date_raw"] = 53178912
        second["saved_scopes"][8] = _scope(
            "secret_holder", "character", 28677,
        )
        second_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53178912,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 92},
            context=second,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(second_checks.values()), second_checks)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][5] = _scope(
            "target_character", "character", 29503,
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53254608,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 371},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:target:matches_any"])
        self.assertFalse(drift_checks["scope:target_character:matches_any"])

    def test_nonfounder_culture_notification_selects_other_acknowledgement(
        self,
    ) -> None:
        event_key = "culture_notification.1111"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148048,
            player=32904,
            scopes=[
                _scope("founder", "character", 35761),
                _scope("parent_culture_1", "culture"),
                _scope("new_culture", "culture"),
                _scope("parent_1", "culture"),
                _scope("ethos", "flag"),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148048,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["scope_types"]["founder"], "character")
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148048,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_chancellor_truce_cancel_binds_only_authored_route(self) -> None:
        event_key = "chancellor_task.1102"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53151120,
            player=32904,
            scopes=[
                _scope("councillor", "character", 28761),
                _scope("councillor_liege", "character", 32904),
                _scope("target", "character", 30921),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53151120,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["councillor_liege"], 32904)
        self.assertEqual(contract["scope_types"]["councillor"], "character")
        self.assertEqual(contract["scope_types"]["target"], "character")
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2]["scope"]["type_key"] = "landed_title"
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53151120,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:target:type"])

    def test_celestial_study_uses_friendship_progress_route(self) -> None:
        event_key = "tgp_movement_events.0070"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53150712,
            player=32904,
            scopes=[
                _scope("my_movement", "situation_participant_group"),
                _scope("councillor", "character", 29889),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["scope_types"]["my_movement"],
            "situation_participant_group",
        )
        self.assertEqual(contract["scope_types"]["councillor"], "character")
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["options"][2]["native_option_index"] = 3
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_family_subsidy_uses_terminal_hidden_option_route(self) -> None:
        event_key = "tgp_movement_events.0080"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=206,
            date_raw=53205336,
            player=32904,
            scopes=[
                _scope("root_scope", "character", 32904),
                _scope("my_movement", "situation_participant_group"),
                _scope("family_member", "character", 31137),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 206},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["root_scope"], 32904)
        self.assertEqual(
            contract["scope_types"]["my_movement"],
            "situation_participant_group",
        )
        self.assertEqual(contract["scope_types"]["family_member"], "character")
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (1, 2, 3))
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "family_member", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 206},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:family_member:unique_third_party"])

    def test_shinto_visitor_uses_deterministic_welcome_route(self) -> None:
        event_key = "tgp_movement_events.0150"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53150712,
            player=32904,
            scopes=[
                _scope("other_ruler", "character", 29646),
                _scope("monk", "character", 16783528),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["saved_scope_count"], 2)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_ep1_language_quarrel_binds_r289_frame_and_positive_route(self) -> None:
        event_key = "ep1_flavor.0021"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=205,
            date_raw=53215344,
            player=32904,
            scopes=[
                _scope("rival_realm", "landed_title"),
                _scope("rival_monarch", "character", 36310),
                _scope("nitpicker", "character", 37929),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53215344,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 205},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["saved_scope_count"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "nitpicker", "character", 36310
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53215344,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 205},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:rival_monarch:differs_from"])
        self.assertFalse(drift_checks["scope:nitpicker:differs_from"])

    def test_ck3_11906_ep1_language_route_b_avoids_duel_and_modifier(self) -> None:
        event_source = (
            ROOT
            / "Crusader Kings III"
            / "game"
            / "events"
            / "dlc"
            / "ep1"
            / "ep1_flavor_events.txt"
        )
        if not event_source.is_file():
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")
        self.assertEqual(
            hashlib.sha256(event_source.read_bytes()).hexdigest().upper(),
            "CC4CD67B77F9FA7B83E3B7A5534045F0DBFC1E724C53182E19ED7884BAD10924",
        )
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "ep1_flavor.0021 =",
        )
        self.assertEqual(
            re.findall(
                r"(?m)^\t\tname = (ep1_flavor\.0021\.[abc])$",
                event_block,
            ),
            [
                "ep1_flavor.0021.a",
                "ep1_flavor.0021.b",
                "ep1_flavor.0021.c",
            ],
        )
        route_b_start = event_block.index("\toption =", event_block.index("\toption =") + 1)
        route_b = _extract_block(event_block[route_b_start:], "\toption =")
        self.assertIn("progress_towards_friend_effect", route_b)
        self.assertIn("minor_cultural_acceptance_gain", route_b)
        self.assertNotIn("\t\tduel =", route_b)
        self.assertNotIn("add_character_modifier", route_b)
        self.assertNotIn("trigger_event", route_b)

    def test_military_aid_letter_acknowledges_exact_governor_pair(self) -> None:
        event_key = "tgp_interaction_event.0015"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53156904,
            player=32904,
            scopes=[
                _scope("actor", "character", 30987),
                _scope("recipient", "character", 32904),
                _scope("secondary_actor", "character", unavailable_character=True),
                _scope("secondary_recipient", "character", 28664),
                _scope("intermediary", "character", unavailable_character=True),
                _scope("governor_at_war", "character", 32904),
                _scope("governor_joining", "character", 28664),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156904,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["recipient"], 32904)
        self.assertEqual(contract["character_scopes"]["governor_at_war"], 32904)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][-1] = _scope(
            "governor_joining", "character", 28665
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156904,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:governor_joining:matches_any"]
        )

    def test_boiling_anger_response_uses_only_visible_stress_relief(self) -> None:
        event_key = "stress_threshold.2202"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148288,
            player=32904,
            scopes=[
                _scope("stress_character", "character", 26849),
                _scope("character_to_yell_at", "character", 32904),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148288,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["character_scopes"]["character_to_yell_at"],
            32904,
        )
        self.assertEqual(contract["scope_types"]["stress_character"], "character")
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148288,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_impostor_break_prefers_confider_over_starvation_or_stress(self) -> None:
        event_key = "stress_threshold.1721"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=627,
            date_raw=53387208,
            player=32904,
            scopes=[
                _scope("stress_character", "character", 32904),
                _scope("deceased_character", "character", 16843923),
                _scope("confidant", "character", 32797),
            ],
            native_option_indices=(7, 9, 12),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53387208,
                "active_event": {"option_count": 14},
            },
            event={"event_instance_id": 627},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 10)
        self.assertEqual(contract["selected_native_option_index"], 9)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        no_confidant = _context(
            event_key=event_key,
            instance_id=849,
            date_raw=53470848,
            player=32904,
            scopes=[
                _scope("stress_character", "character", 32904),
                _scope("deceased_character", "character", 32797),
            ],
            native_option_indices=(7, 10, 12),
        )
        current_contract = production._timeline_contract_for_window(
            production._manager_recovery_contract(
                production.KNOWN_TIMELINE_INTERRUPTS[event_key],
                player=32904,
                event_key=event_key,
            ),
            starting_date=53391336,
        )
        no_confidant_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53470848,
                "active_event": {"option_count": 14},
            },
            event={"event_instance_id": 849},
            context=no_confidant,
            event_key=event_key,
            contract=current_contract,
        )
        self.assertTrue(all(no_confidant_checks.values()), no_confidant_checks)
        no_confidant_effective = production._option_contract_for_context(
            no_confidant["options"],
            production._scope_contract_for_context(
                no_confidant["saved_scopes"], current_contract
            ),
        )
        self.assertEqual(no_confidant_effective["selected_option_number"], 11)
        self.assertEqual(
            no_confidant_effective["selected_native_option_index"], 10
        )

        class Service:
            def snapshot(self) -> dict[str, object]:
                return {
                    "snapshot_id": "native:2446",
                    "revision": 2447,
                    "native_revision": 2446,
                    "date_raw": 53470848,
                    "map_ready": True,
                    "paused": True,
                    "played_character": {"character_id": 32904},
                    "diagnostics": {"connection_generation": 1},
                    "active_event": {
                        "instance_id": 849,
                        "option_count": 14,
                    },
                }

            def select_event_option(
                self,
                option_number: int,
                *,
                event_instance_id: int,
                expected_revision: int,
            ) -> dict[str, object]:
                self.submission = (
                    option_number,
                    event_instance_id,
                    expected_revision,
                )
                return {
                    "accepted": True,
                    "status": "submitted",
                    "option_number": option_number,
                    "option_index": 10,
                    "event_selection": {
                        "postcondition_verified": True,
                        "old_event_instance_id": event_instance_id,
                        "new_event_instance_id": None,
                        "selected_option_number": option_number,
                        "selected_native_option_index": 10,
                    },
                }

        service = Service()
        drain = production._drain_known_timeline_interrupt(
            service,
            snapshot={
                "date_raw": 53470848,
                "active_event": {"option_count": 14},
            },
            event={"event_instance_id": 849},
            query={"current_event_window_context": no_confidant},
            event_key=event_key,
            contract=current_contract,
            player=32904,
            connection_generation=1,
        )
        self.assertEqual(service.submission, (11, 849, 2447))
        self.assertTrue(all(drain["selection_checks"].values()))

        same_people = copy.deepcopy(context)
        same_people["saved_scopes"][2] = _scope(
            "confidant", "character", 16843923
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53387208,
                "active_event": {"option_count": 14},
            },
            event={"event_instance_id": 627},
            context=same_people,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:confidant:differs_from"])

    def test_dynasty_birth_notice_only_acknowledges_bound_family(self) -> None:
        event_key = "birth.1010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53154408,
            player=32904,
            scopes=[
                _scope("child", "character", 16790642),
                _scope("father", "character", 36354),
                _scope("real_father", "character", 36354),
                _scope("mother", "character", 35997),
                _scope("is_bastard", "boolean"),
                _scope("is_child_of_concubine", "boolean"),
                _scope("matrilineal", "boolean"),
                _scope("spouse_of_mother", "character", 36354),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53154408,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        repeated_context = copy.deepcopy(context)
        repeated_context["current_event_instance_id"] = 397
        repeated_context["date_raw"] = 53286168
        repeated_context["saved_scopes"][0] = _scope(
            "child", "character", 73331
        )
        repeated_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53286168,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 397},
            context=repeated_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(repeated_checks.values()), repeated_checks)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "real_father", "character", 36355
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53154408,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:real_father:matches_any"])

    def test_dynasty_birth_notice_accepts_bound_unmarried_secret_frame(self) -> None:
        event_key = "birth.1010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=209,
            date_raw=53213208,
            player=32904,
            scopes=[
                _scope("child", "character", 16842384),
                _scope(
                    "father",
                    "character",
                    unavailable_character=True,
                ),
                _scope("real_father", "character", 36350),
                _scope("mother", "character", 37337),
                _scope("is_bastard", "boolean"),
                _scope("is_child_of_concubine", "boolean"),
                _scope("matrilineal", "boolean"),
                _scope("new_secret", "secret"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53213208,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 209},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        variant = contract["scope_variants"][0]
        self.assertEqual(variant["unavailable_character_scopes"], ("father",))
        self.assertEqual(variant["scope_types"]["new_secret"], "secret")

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][1] = _scope("father", "character", 36350)
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53213208,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 209},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:father:unavailable_character"])

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][-1] = _scope("new_secret", "flag")
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53213208,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 209},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:new_secret:type"])

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"].pop()
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53213208,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 209},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"].append(
            _scope("spouse_of_mother", "character", 36350)
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53213208,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 209},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])

    def test_epidemic_notice_avoids_physician_followup_chain(self) -> None:
        event_key = "epidemic_events.1100"
        contract = _manager_contract(event_key, player=32904)
        for native_indices in ((0, 1), (0, 2)):
            with self.subTest(native_indices=native_indices):
                context = _context(
                    event_key=event_key,
                    instance_id=14,
                    date_raw=53148360,
                    player=32904,
                    scopes=[
                        _scope("epidemic", "epidemic"),
                        _scope("province", "province"),
                        _scope("infected_county", "landed_title"),
                    ],
                    native_option_indices=native_indices,
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53148360,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 14},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        repeat = copy.deepcopy(context)
        repeat["current_event_instance_id"] = 386
        repeat["date_raw"] = 53270136
        repeat["options"] = _context(
            event_key=event_key,
            instance_id=386,
            date_raw=53270136,
            player=32904,
            scopes=[],
            native_option_indices=(0, 1),
        )["options"]
        repeat_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53270136,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 386},
            context=repeat,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(repeat_checks.values()), repeat_checks)

        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148360,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("province", "province"),
                _scope("infected_county", "landed_title"),
            ],
            native_option_indices=(0, 2),
        )
        drifted = copy.deepcopy(context)
        drifted["options"][1]["native_option_index"] = 3
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148360,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_epidemic_scapegoat_response_slows_witch_trials(self) -> None:
        event_key = "epidemic_events.1060"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=212,
            date_raw=53225568,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("story_scope", "story"),
            ],
            native_option_indices=(1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225568,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 212},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope("story_scope", "situation")
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225568,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 212},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:story_scope:type"])

    def test_liberty_ultimatum_refuses_realm_law_mutation(self) -> None:
        event_key = "faction_demand.0101"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=408,
            date_raw=53297760,
            player=32904,
            scopes=[
                _scope("faction", "faction"),
                _scope("faction_leader", "character", 28671),
                _scope("faction_target", "character", 32904),
            ],
            native_option_indices=(0, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53297760,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 408},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        counter_offer_visible = copy.deepcopy(context)
        counter_offer_visible["options"] = _context(
            event_key=event_key,
            instance_id=408,
            date_raw=53297760,
            player=32904,
            scopes=[],
            native_option_indices=(0, 1, 2),
        )["options"]
        variant_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53297760,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 408},
            context=counter_offer_visible,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(variant_checks.values()), variant_checks)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][0] = _scope("faction", "character", 28671)
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53297760,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 408},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:faction:type"])

    def test_populist_ultimatum_refuses_immediate_title_transfer(self) -> None:
        event_key = "faction_demand.1001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=214,
            date_raw=53229048,
            player=32904,
            scopes=[
                _scope("faction", "faction"),
                _scope("peasant_county", "landed_title"),
                _scope("faction_target", "character", 32904),
                _scope("target_title", "landed_title"),
                _scope("peasant_leader", "character", 16820110),
            ],
            native_option_indices=(2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229048,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 214},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        repeated_context = copy.deepcopy(context)
        repeated_context["current_event_instance_id"] = 413
        repeated_context["date_raw"] = 53308056
        repeated_context["saved_scopes"][4] = _scope(
            "peasant_leader", "character", 73620
        )
        repeated_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53308056,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 413},
            context=repeated_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(repeated_checks.values()), repeated_checks)

        conversion_visible = copy.deepcopy(context)
        conversion_visible["current_event_instance_id"] = 232
        conversion_visible["date_raw"] = 53237880
        conversion_visible["options"] = _context(
            event_key=event_key,
            instance_id=232,
            date_raw=53237880,
            player=32904,
            scopes=[],
            native_option_indices=(0, 2, 3),
        )["options"]
        conversion_visible_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53237880,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 232},
            context=conversion_visible,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(
            all(conversion_visible_checks.values()), conversion_visible_checks
        )

        new_leader_context = copy.deepcopy(context)
        new_leader_context["current_event_instance_id"] = 223
        new_leader_context["date_raw"] = 53239560
        new_leader_context["saved_scopes"].append(
            _scope("new_title", "landed_title")
        )
        new_leader_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239560,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 223},
            context=new_leader_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(new_leader_checks.values()), new_leader_checks)

        invalid_new_title = copy.deepcopy(new_leader_context)
        invalid_new_title["saved_scopes"][-1] = _scope(
            "new_title", "character", 70343
        )
        invalid_new_title_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239560,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 223},
            context=invalid_new_title,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            invalid_new_title_checks["scope:new_title:optional_type"]
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][4] = _scope(
            "peasant_leader", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229048,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 214},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:peasant_leader:unique_third_party"]
        )

    def test_auto_accepted_pardon_uses_only_acknowledgement(self) -> None:
        event_key = "char_interaction.0240"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=616,
            date_raw=53366952,
            player=32904,
            scopes=[
                _scope("actor", "character", 29747),
                _scope("recipient", "character", 32904),
                _scope(
                    "secondary_actor", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "secondary_recipient", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "intermediary", "character",
                    unavailable_character=True,
                ),
                _scope("hook", "boolean"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53366952,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 616},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

    def test_vassal_contract_lowering_uses_only_acknowledgement(self) -> None:
        event_key = "char_interaction.0251"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=613,
            date_raw=53363856,
            player=32904,
            scopes=[
                _scope("actor", "character", 30075),
                _scope("recipient", "character", 32904),
                _scope(
                    "secondary_actor", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "secondary_recipient", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "intermediary", "character",
                    unavailable_character=True,
                ),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53363856,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 613},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        player_actor = copy.deepcopy(context)
        player_actor["saved_scopes"][0] = _scope(
            "actor", "character", 32904
        )
        drift = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53363856,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 613},
            context=player_actor,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift["scope:actor:unique_third_party"])

    def test_avalanche_followup_pays_aid_without_province_penalty(self) -> None:
        event_key = "travel_danger_events.3002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=621,
            date_raw=53373936,
            player=32904,
            scopes=[
                _scope("travel_plan", "travel_plan"),
                _scope("travel_leader", "character", 68875),
                _scope("avalanche_traveler", "character", 32602),
                _scope("avalanche_location", "province"),
                _scope("news_bearer", "character", 30987),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53373936,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 621},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

    def test_ceased_tributary_notification_uses_inert_acknowledgement(self) -> None:
        event_key = "char_interaction.0370"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=215,
            date_raw=53229720,
            player=32904,
            scopes=[
                _scope("actor", "character", 35923),
                _scope("recipient", "character", 32904),
                _scope(
                    "secondary_actor", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "secondary_recipient", "character",
                    unavailable_character=True,
                ),
                _scope(
                    "intermediary", "character",
                    unavailable_character=True,
                ),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229720,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 215},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "secondary_actor", "character", 36354
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229720,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 215},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:secondary_actor:unavailable_character"]
        )

    def test_epidemic_alms_proposal_avoids_disease_roll(self) -> None:
        event_key = "physician_epidemic_events.1040"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=222,
            date_raw=53237808,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("physician", "character", 49718),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53237808,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 222},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "physician", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53237808,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 222},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:physician:unique_third_party"])

    def test_herbalist_accusation_avoids_imprisonment(self) -> None:
        event_key = "epidemic_events.5007"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=387,
            date_raw=53270256,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("herbalist", "character", 49718),
                _scope("accuser", "character", 16834604),
            ],
            native_option_indices=(1, 2),
        )
        snapshot = {
            "date_raw": 53270256,
            "active_event": {"option_count": 3},
        }
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 387},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        root_has_related_trait = copy.deepcopy(context)
        root_has_related_trait["options"] = _context(
            event_key=event_key,
            instance_id=387,
            date_raw=53270256,
            player=32904,
            scopes=[],
            native_option_indices=(0, 1, 2),
        )["options"]
        trait_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 387},
            context=root_has_related_trait,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(trait_checks.values()), trait_checks)

        same_participant = copy.deepcopy(context)
        same_participant["saved_scopes"][3] = _scope(
            "accuser", "character", 49718
        )
        drift_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event={"event_instance_id": 387},
            context=same_participant,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:accuser:differs_from"])

    def test_herbal_sachet_offer_buys_nothing(self) -> None:
        event_key = "epidemic_events.5009"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=231,
            date_raw=53254032,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("merchant", "character", 63643),
                _scope("flower_species", "flag"),
                _scope("owner", "character", 63643),
                _scope("creator", "character", 63643),
                _scope("random_quality_bonus", "value"),
                _scope("quality", "value"),
                _scope("wealth", "value"),
                _scope("location", "province"),
                _scope("newly_created_artifact", "artifact"),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53254032,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 231},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][5] = _scope(
            "creator", "character", 63644
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53254032,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 231},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:creator:matches_any"])

    def test_language_learning_response_avoids_rival_progress(self) -> None:
        event_key = "learn_language_outcome.1001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=232,
            date_raw=53257296,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 62813),
                _scope("artifact", "artifact"),
                _scope("target", "character", 32904),
                _scope("scheme_successful", "boolean"),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53257296,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 232},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][1] = _scope(
            "owner", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53257296,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 232},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:owner:unique_third_party"])

    def test_hostile_scheme_discovery_binds_dynamic_court_parties(self) -> None:
        event_key = "hostile_scheme_discovery.2001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=207,
            date_raw=53216088,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 29583),
                _scope("artifact", "artifact"),
                _scope("target", "character", 37960),
                _scope("spymaster", "character", 30434),
                _scope("discovery_chance", "value"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53216088,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 207},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        owner_is_player = copy.deepcopy(context)
        owner_is_player["saved_scopes"][1] = _scope(
            "owner", "character", 32904
        )
        owner_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53216088,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 207},
            context=owner_is_player,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(owner_checks["scope:owner:unique_third_party"])

        merged_parties = copy.deepcopy(context)
        merged_parties["saved_scopes"][4] = _scope(
            "spymaster", "character", 37960
        )
        merged_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53216088,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 207},
            context=merged_parties,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(merged_checks["scope:spymaster:differs_from"])

    def test_eunuch_story_opener_avoids_court_position_mutation(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.1001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=209,
            date_raw=53219664,
            player=32904,
            scopes=[
                _scope("eunuch", "character", 31801),
                _scope("origin", "landed_title"),
                _scope("story", "story"),
                _scope("liege", "character", 32904),
                _scope("candidate", "character", 31801),
                _scope("modifier_type", "flag"),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219664,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 209},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        mismatched_candidate = copy.deepcopy(context)
        mismatched_candidate["saved_scopes"][4] = _scope(
            "candidate", "character", 31802
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219664,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 209},
            context=mismatched_candidate,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:candidate:matches_any"])

    def test_eunuch_secret_proposal_avoids_revealing_secret(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2051"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=211,
            date_raw=53223312,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("secret", "secret"),
                _scope("secret_owner", "character", 31671),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["saved_scope_counts"], (6, 7, 8, 9, 10))
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        switched_contract = _manager_contract(event_key, player=40000)
        self.assertEqual(
            switched_contract["optional_unique_character_scope_excludes"],
            {"secret_target": (40000,), "rival": (40000,)},
        )

        targeted_secret = copy.deepcopy(context)
        targeted_secret["saved_scopes"].append(
            _scope("secret_target", "character", 62189)
        )
        targeted_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=targeted_secret,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(targeted_checks.values()), targeted_checks)

        all_optionals = copy.deepcopy(context)
        all_optionals["saved_scopes"].extend(
            [
                _scope("protege", "character", 33001),
                _scope("student", "character", 33002),
                _scope("rival", "character", 16834604),
                _scope("secret_target", "character", 62189),
            ]
        )
        all_optional_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=all_optionals,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(all_optional_checks.values()), all_optional_checks)

        eunuch_rival = copy.deepcopy(all_optionals)
        eunuch_rival["saved_scopes"][8] = _scope(
            "rival", "character", 31801
        )
        rival_drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=eunuch_rival,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            rival_drift_checks["scope:rival:optional_differs_from"]
        )

        player_target = copy.deepcopy(targeted_secret)
        player_target["saved_scopes"][6] = _scope(
            "secret_target", "character", 32904
        )
        target_drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=player_target,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            target_drift_checks[
                "scope:secret_target:optional_unique_third_party"
            ]
        )

        shared_identity = copy.deepcopy(context)
        shared_identity["saved_scopes"][5] = _scope(
            "secret_owner", "character", 31801
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223312,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 211},
            context=shared_identity,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:secret_owner:differs_from"])

    def test_eunuch_boon_proposal_avoids_external_boon_mutation(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2050"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=374,
            date_raw=53255856,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("student", "character", 33596937),
                _scope("rival", "character", 16834604),
                _scope("boon_faction", "faction"),
                _scope("boon_victim", "character", 16843415),
                _scope("eunuch_boon", "flag"),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53255856,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 374},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 32)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        no_target_branch = copy.deepcopy(context)
        no_target_branch["saved_scopes"] = [
            scope
            for scope in no_target_branch["saved_scopes"]
            if scope["name"] not in {"boon_faction", "boon_victim"}
        ]
        no_target_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53255856,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 374},
            context=no_target_branch,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(no_target_checks.values()), no_target_checks)

        candidacy_branch = copy.deepcopy(no_target_branch)
        candidacy_branch["saved_scopes"].extend(
            [
                _scope("boon_title", "landed_title"),
                _scope("boon_victim", "character", 16843415),
                _scope("boon_target", "character", 36354),
            ]
        )
        candidacy_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53255856,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 374},
            context=candidacy_branch,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(candidacy_checks.values()), candidacy_checks)

        player_eunuch = copy.deepcopy(context)
        player_eunuch["saved_scopes"][2] = _scope(
            "eunuch", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53255856,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 374},
            context=player_eunuch,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:eunuch:unique_third_party"])

    def test_eunuch_scheme_proposal_preserves_hidden_scheme(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2052"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=229,
            date_raw=53236512,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("rival", "character", 16844822),
                _scope("scheme", "scheme"),
                _scope("scheme_owner", "character", 29573),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["saved_scope_counts"], (6, 7, 8, 9, 10))
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        repeat = copy.deepcopy(context)
        repeat["current_event_instance_id"] = 388
        repeat["date_raw"] = 53270760
        repeat["saved_scopes"].extend(
            [
                _scope("student", "character", 33596937),
                _scope("scheme_target", "character", 32364),
            ]
        )
        repeat_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53270760,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 388},
            context=repeat,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(repeat_checks.values()), repeat_checks)

        target_without_rival = copy.deepcopy(context)
        target_without_rival["saved_scopes"] = [
            row
            for row in target_without_rival["saved_scopes"]
            if row["name"] != "rival"
        ]
        target_without_rival["saved_scopes"].append(
            _scope("scheme_target", "character", 32364)
        )
        target_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=target_without_rival,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(target_checks.values()), target_checks)

        neither_optional = copy.deepcopy(target_without_rival)
        neither_optional["saved_scopes"] = [
            row
            for row in neither_optional["saved_scopes"]
            if row["name"] != "scheme_target"
        ]
        neither_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=neither_optional,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(neither_checks.values()), neither_checks)

        both_optional = copy.deepcopy(context)
        both_optional["saved_scopes"].append(
            _scope("scheme_target", "character", 32364)
        )
        both_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=both_optional,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(both_checks.values()), both_checks)

        eunuch_target = copy.deepcopy(target_without_rival)
        eunuch_target["saved_scopes"][6] = _scope(
            "scheme_target", "character", 31801
        )
        target_drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=eunuch_target,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            target_drift_checks[
                "scope:scheme_target:optional_differs_from"
            ]
        )

        player_target = copy.deepcopy(target_without_rival)
        player_target["saved_scopes"][6] = _scope(
            "scheme_target", "character", 32904
        )
        player_target_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=player_target,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            player_target_checks[
                "scope:scheme_target:optional_unique_third_party"
            ]
        )

        owner_is_eunuch = copy.deepcopy(context)
        owner_is_eunuch["saved_scopes"][6] = _scope(
            "scheme_owner", "character", 31801
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53236512,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 229},
            context=owner_is_eunuch,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:eunuch:differs_from"])
        self.assertFalse(drift_checks["scope:scheme_owner:differs_from"])

    def test_eunuch_court_position_demand_refuses_assignment(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2060"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=346,
            date_raw=53225016,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("candidate", "character", 31801),
                _scope("liege", "character", 32904),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225016,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 346},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)

        all_optionals = copy.deepcopy(context)
        all_optionals["saved_scopes"].extend(
            [
                _scope("protege", "character", 33001),
                _scope("student", "character", 33002),
                _scope("rival", "character", 33003),
                _scope("old_holder", "character", 33004),
            ]
        )
        optional_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225016,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 346},
            context=all_optionals,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(optional_checks.values()), optional_checks)

        wrong_candidate = copy.deepcopy(context)
        wrong_candidate["saved_scopes"][4] = _scope(
            "candidate", "character", 31802
        )
        candidate_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225016,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 346},
            context=wrong_candidate,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(candidate_checks["scope:candidate:matches_any"])

        unknown_scope = copy.deepcopy(context)
        unknown_scope["saved_scopes"].append(_scope("mystery", "flag"))
        unknown_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225016,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 346},
            context=unknown_scope,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(unknown_checks["saved_scope_names_exact"])

    def test_eunuch_family_position_demand_refuses_assignment(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2061"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=363,
            date_raw=53239872,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("student", "character", 33596937),
                _scope("rival", "character", 16834604),
                _scope("positioner", "character", 31440),
                _scope("candidate", "character", 31440),
                _scope("liege", "character", 32904),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239872,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 363},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        all_optionals = copy.deepcopy(context)
        all_optionals["saved_scopes"].extend(
            [
                _scope("protege", "character", 33001),
                _scope("old_holder", "character", 33002),
            ]
        )
        optional_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239872,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 363},
            context=all_optionals,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(optional_checks.values()), optional_checks)

        wrong_candidate = copy.deepcopy(context)
        wrong_candidate["saved_scopes"][7] = _scope(
            "candidate", "character", 31441
        )
        candidate_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239872,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 363},
            context=wrong_candidate,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(candidate_checks["scope:candidate:matches_any"])

        old_holder_is_candidate = copy.deepcopy(all_optionals)
        old_holder_is_candidate["saved_scopes"][10] = _scope(
            "old_holder", "character", 31440
        )
        holder_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239872,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 363},
            context=old_holder_is_candidate,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            holder_checks["scope:old_holder:optional_differs_from"]
        )

    def test_eunuch_council_demand_preserves_council_roster(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2040"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=378,
            date_raw=53258328,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("student", "character", 33596937),
                _scope("rival", "character", 16834604),
                _scope("petition_liege", "character", 32904),
                _scope("petition_vassal", "character", 31801),
                _scope("second_party", "character", 29346),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53258328,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 378},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        empty_seat = copy.deepcopy(context)
        empty_seat["saved_scopes"] = [
            scope
            for scope in empty_seat["saved_scopes"]
            if scope["name"] != "second_party"
        ]
        empty_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53258328,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 378},
            context=empty_seat,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(empty_checks.values()), empty_checks)

        alias_drift = copy.deepcopy(context)
        alias_drift["saved_scopes"][7] = _scope(
            "petition_vassal", "character", 31802
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53258328,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 378},
            context=alias_drift,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:eunuch:matches_any"])
        self.assertFalse(drift_checks["scope:petition_vassal:matches_any"])

    def test_eunuch_family_council_petition_preserves_council_roster(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2041"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=233,
            date_raw=53239224,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("rival", "character", 16844822),
                _scope("petition_liege", "character", 32904),
                _scope("councillor", "character", 35159),
                _scope("petition_vassal", "character", 35159),
                _scope("second_party", "character", 29346),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239224,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 233},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        repeated_context = copy.deepcopy(context)
        repeated_context["current_event_instance_id"] = 393
        repeated_context["date_raw"] = 53277192
        repeated_context["saved_scopes"].insert(
            4, _scope("student", "character", 33596937)
        )
        repeated_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53277192,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 393},
            context=repeated_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(repeated_checks.values()), repeated_checks)
        self.assertEqual(contract["saved_scope_counts"], (7, 8, 9, 10, 11))
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)

        alias_drift = copy.deepcopy(context)
        alias_drift["saved_scopes"][7] = _scope(
            "petition_vassal", "character", 35160
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53239224,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 233},
            context=alias_drift,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:councillor:matches_any"])
        self.assertFalse(drift_checks["scope:petition_vassal:matches_any"])

    def test_eunuch_governorship_request_preserves_title_roster(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.2021"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=216,
            date_raw=53227128,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("governor", "character", 31440),
                _scope("title", "landed_title"),
                _scope("title_heir", "character", 30938),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53227128,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 216},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        reused_heir = copy.deepcopy(context)
        reused_heir["saved_scopes"][6] = _scope(
            "title_heir", "character", 31440
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53227128,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 216},
            context=reused_heir,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:title_heir:differs_from"])

    def test_eunuch_student_story_node_acknowledges_immediate_setup(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.3001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=236,
            date_raw=53243184,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("rival", "character", 16844822),
                _scope("origin_liege", "character", 31801),
                _scope("origin", "landed_title"),
                _scope("student", "character", 69909),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243184,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 236},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 8)

        neighboring_origin = copy.deepcopy(context)
        neighboring_origin["saved_scopes"][5] = _scope(
            "origin_liege", "character", 30921
        )
        neighboring_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243184,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 236},
            context=neighboring_origin,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(neighboring_checks.values()), neighboring_checks)

        existing_student = copy.deepcopy(context)
        existing_student["saved_scopes"] = [
            row
            for row in existing_student["saved_scopes"]
            if row["name"] not in ("origin_liege", "origin")
        ]
        existing_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243184,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 236},
            context=existing_student,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(existing_checks.values()), existing_checks)

        half_origin = copy.deepcopy(context)
        half_origin["saved_scopes"] = [
            row for row in half_origin["saved_scopes"] if row["name"] != "origin"
        ]
        half_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243184,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 236},
            context=half_origin,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(half_checks["saved_scope_names_exact"])

    def test_eunuch_rival_opener_only_acknowledges_immediate_result(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.3010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=218,
            date_raw=53229168,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("origin_liege", "character", 32904),
                _scope("origin", "landed_title"),
                _scope("rival", "character", 16844822),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229168,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 218},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 4)

        dynamic_origin_liege = copy.deepcopy(context)
        dynamic_origin_liege["saved_scopes"][4] = _scope(
            "origin_liege", "character", 32922
        )
        dynamic_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229168,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 218},
            context=dynamic_origin_liege,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(dynamic_checks.values()), dynamic_checks)

        retained_story_roles = copy.deepcopy(dynamic_origin_liege)
        retained_story_roles["saved_scopes"].extend(
            [
                _scope("protege", "character", 33001),
                _scope("student", "character", 33002),
            ]
        )
        retained_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229168,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 218},
            context=retained_story_roles,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(retained_checks.values()), retained_checks)

        same_rival = copy.deepcopy(context)
        same_rival["saved_scopes"][6] = _scope(
            "rival", "character", 31801
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229168,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 218},
            context=same_rival,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:rival:differs_from"])

    def test_eunuch_family_dispute_avoids_story_downgrade(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.5010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=364,
            date_raw=53243880,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("rival", "character", 31137),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243880,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 364},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 4)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        retained_story_roles = copy.deepcopy(context)
        retained_story_roles["saved_scopes"].extend(
            [
                _scope("protege", "character", 33001),
                _scope("student", "character", 33596937),
            ]
        )
        retained_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243880,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 364},
            context=retained_story_roles,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(retained_checks.values()), retained_checks)

        player_rival = copy.deepcopy(context)
        player_rival["saved_scopes"][4] = _scope(
            "rival", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53243880,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 364},
            context=player_rival,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:rival:unique_third_party"])

    def test_eunuch_spouse_accusation_avoids_double_imprisonment(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.4000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=223,
            date_raw=53232552,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("rival", "character", 16844822),
                _scope("spouse", "character", 32797),
                _scope("cuckolder", "character", 30581),
            ],
            native_option_indices=(0, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53232552,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 223},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 4)

        retained_student = copy.deepcopy(context)
        retained_student["current_event_instance_id"] = 425
        retained_student["date_raw"] = 53325480
        retained_student["saved_scopes"].insert(
            4, _scope("student", "character", 33596937)
        )
        retained_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53325480,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 425},
            context=retained_student,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(retained_checks.values()), retained_checks)

        same_accused_party = copy.deepcopy(context)
        same_accused_party["saved_scopes"][6] = _scope(
            "cuckolder", "character", 32797
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53232552,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 223},
            context=same_accused_party,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:spouse:differs_from"])
        self.assertFalse(drift_checks["scope:cuckolder:differs_from"])

        visible_option_drift = copy.deepcopy(context)
        visible_option_drift["options"][1]["native_option_index"] = 1
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53232552,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 223},
            context=visible_option_drift,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_eunuch_seduction_plot_avoids_duel_and_triple_imprisonment(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.4010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=368,
            date_raw=53247768,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("student", "character", 33596937),
                _scope("rival", "character", 16834604),
                _scope("spouse", "character", 32797),
                _scope("seducer", "character", 31440),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53247768,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 368},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 16)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        generated_branch = copy.deepcopy(context)
        generated_branch["saved_scopes"].extend(
            [
                _scope("had_sex_root_character", "character", 31440),
                _scope("had_sex_with_effect_partner", "character", 32797),
                _scope("new_memory", "character_memory"),
                _scope("secret", "secret"),
            ]
        )
        generated_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53247768,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 368},
            context=generated_branch,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(generated_checks.values()), generated_checks)

        had_sex_alias_drift = copy.deepcopy(generated_branch)
        had_sex_alias_drift["saved_scopes"][8] = _scope(
            "had_sex_root_character", "character", 31441
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53247768,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 368},
            context=had_sex_alias_drift,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks[
                "scope:had_sex_root_character:optional_matches_any"
            ]
        )

    def test_eunuch_puppet_heir_binds_distinct_current_heir(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.5020"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=366,
            date_raw=53246016,
            player=32904,
            scopes=[
                _scope("story", "story"),
                _scope("emperor", "character", 32904),
                _scope("eunuch", "character", 31801),
                _scope("admin_title", "landed_title"),
                _scope("student", "character", 33596937),
                _scope("rival", "character", 16844822),
                _scope("current_heir", "character", 36354),
                _scope("puppet", "character", 37810),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53246016,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 366},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 4)

        no_story_roles = copy.deepcopy(context)
        no_story_roles["saved_scopes"] = [
            scope
            for scope in no_story_roles["saved_scopes"]
            if scope["name"] not in {"student", "rival"}
        ]
        no_roles_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53246016,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 366},
            context=no_story_roles,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(no_roles_checks.values()), no_roles_checks)

        current_heir_reused = copy.deepcopy(context)
        current_heir_reused["saved_scopes"][7] = _scope(
            "puppet", "character", 36354
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53246016,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 366},
            context=current_heir_reused,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:current_heir:differs_from"])
        self.assertFalse(drift_checks["scope:puppet:differs_from"])

    def test_concubine_tribute_declines_person_without_court_mutation(self) -> None:
        event_key = "tribute_mission.1002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150160,
            player=32904,
            scopes=_human_tribute_scopes(),
            native_option_indices=(0, 1, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150160,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150160,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])
        self.assertFalse(drift_checks["saved_scope_count"])

    def test_eunuch_tribute_declines_person_without_court_mutation(self) -> None:
        event_key = "tribute_mission.1002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=225,
            date_raw=53231832,
            player=32904,
            scopes=[
                _scope("actor", "character", 34162),
                _scope("recipient", "character", 32904),
                _scope(
                    "secondary_actor",
                    "character",
                    unavailable_character=True,
                ),
                _scope("secondary_recipient", "character", 35197),
                _scope(
                    "intermediary",
                    "character",
                    unavailable_character=True,
                ),
                _scope("tribute_mission_target", "character", 32904),
                _scope("tributary_scope", "character", 34162),
                _scope("overlord_scope", "character", 32904),
                _scope("receiving_character", "character", 32904),
                _scope("opinion_of_tributary", "value"),
                _scope("eunuch_character", "character", 35197),
                _scope("human_tribute", "character", 35197),
                _scope("tribute_reward_type_treasury", "value"),
                _scope("saved_innovation", "culture_innovation"),
            ],
            native_option_indices=(0, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53231832,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 225},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        wrong_branch_options = copy.deepcopy(context)
        wrong_branch_options["options"] = [
            {**row, "native_option_index": native}
            for row, native in zip(
                wrong_branch_options["options"],
                (0, 1, 3),
            )
        ]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53231832,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 225},
            context=wrong_branch_options,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_tribute_reward_uses_no_player_resource_cost_route(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=15,
            date_raw=53150184,
            player=32904,
            scopes=[
                *_human_tribute_scopes(),
                _scope("rejected_concubine", "flag"),
                _scope("decided_on_treasury_reward", "flag"),
            ],
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150184,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 6)
        self.assertEqual(contract["selected_native_option_index"], 5)

        compact = copy.deepcopy(context)
        compact["saved_scopes"] = [
            row
            for row in compact["saved_scopes"]
            if row["name"] not in {"concubine_character", "rejected_concubine"}
        ]
        compact_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150400,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context={**compact, "date_raw": 53150400},
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(compact_checks.values()), compact_checks)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150184,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])

    def test_seduce_outcome_binds_the_complete_mandatory_notification(self) -> None:
        event_key = "seduce_outcome.4900"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53199480,
        )
        contexts = (
            _context(
                event_key=event_key,
                instance_id=208,
                date_raw=53215752,
                player=32904,
                scopes=[
                    _scope("scheme", "scheme"),
                    _scope("owner", "character", 30320),
                    _scope("artifact", "artifact"),
                    _scope("target", "character", 37337),
                    _scope("ignore_cheating_error_check", "boolean"),
                    _scope("discovery_chance", "value"),
                    _scope("scheme_discovered", "boolean"),
                    _scope("target_liege", "character", 32904),
                ],
                native_option_indices=(0,),
            ),
            _context(
                event_key=event_key,
                instance_id=342,
                date_raw=53217600,
                player=32904,
                scopes=[
                    _scope("scheme", "scheme"),
                    _scope("owner", "character", 28443),
                    _scope("artifact", "artifact"),
                    _scope("target", "character", 34991),
                    _scope("ignore_cheating_error_check", "boolean"),
                    _scope("discovery_chance", "value"),
                    _scope("scheme_discovered", "boolean"),
                    _scope("target_liege", "character", 32904),
                ],
                native_option_indices=(0,),
            ),
        )
        for context in contexts:
            with self.subTest(instance_id=context["current_event_instance_id"]):
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": context["date_raw"],
                        "active_event": {"option_count": 1},
                    },
                    event={
                        "event_instance_id": context[
                            "current_event_instance_id"
                        ]
                    },
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)

        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["character_scopes"], {"target_liege": 32904}
        )

        drifted = copy.deepcopy(contexts[1])
        drifted["saved_scopes"][7] = _scope(
            "target_liege", "character", 30320
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53215752,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 208},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:target_liege"])

        drifted = copy.deepcopy(contexts[1])
        drifted["saved_scopes"][3] = _scope(
            "target", "character", 28443
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53217600,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 342},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:owner:differs_from"])

    def test_seduce_discovery_binds_liege_and_complete_scope_stack(self) -> None:
        event_key = "seduce_outcome.3901"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53199480,
        )
        context = _context(
            event_key=event_key,
            instance_id=401,
            date_raw=53248656,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 31496),
                _scope("artifact", "artifact"),
                _scope("target", "character", 37337),
                _scope("ignore_cheating_error_check", "boolean"),
                _scope("scheme_successful", "boolean"),
                _scope("discovery_chance", "value"),
                _scope("scheme_discovered", "boolean"),
                _scope("target_liege", "character", 32904),
                _scope("capital", "landed_title"),
                _scope(
                    "dummy_servant_gender",
                    "character",
                    unavailable_character=True,
                ),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53248656,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 401},
            context=context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"], {"target_liege": 32904})
        self.assertEqual(contract["saved_scope_count"], 11)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][10] = _scope(
            "dummy_servant_gender", "character", 31496
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53248656,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 401},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:dummy_servant_gender:unavailable_character"]
        )


if __name__ == "__main__":
    unittest.main()
