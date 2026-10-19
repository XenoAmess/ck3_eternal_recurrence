"""Same-frame use of existing ordinary DTOs, without query or runtime state."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from test_turn_bundle_v1 import _root, _snapshot
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.campaign_score_cadence_v1 import ordinary_sample_candidate, raw_to_date
from xar_autoplayer.campaign_score_existing_inputs_v1 import project_existing_month_inputs_v1


def cash_inputs():
    retained = json.loads((Path(__file__).parents[1] / "fixtures/construction_cash_current_12004.json").read_text(encoding="utf-8"))
    frame, packet = retained["planning_source_frame"], retained["packet"]
    snapshot = {key: frame[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
    snapshot.update(paused=True, map_ready=True,
        played_character={"character_id": frame["actor_character_id"], "alive": True},
        played_character_gold=deepcopy(packet["current_treasury"]), active_wars=[],
        diagnostics={"bridge_pid": frame["bridge_pid"], "connection_generation": frame["connection_generation"],
                     "hello": {"game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256}})
    return snapshot, frame, packet


def root_inputs():
    snapshot, result = _snapshot(), _root()
    snapshot.update(map_ready=True, episode_run_id="native-12345-existing-input-fixture",
        diagnostics={"bridge_pid": 44, "connection_generation": 3,
                     "hello": {"game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256}})
    result["campaign_root_context"]["provenance"] = {"game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256}
    return snapshot, GameplayBridgeService._observed_planning_source_frame(snapshot), result


class ExistingMonthInputsTests(unittest.TestCase):
    def test_retained_actual_cash_DTO_maps_gross_and_each_actor_cost_once(self):
        snapshot, frame, packet = cash_inputs()
        # Explicit software scope variant: identical actor-global cost in two wars.
        packet["active_war_ids"] = [100, 200]
        for row in packet["military_expenses"].values():
            row["war_ids"] = [100, 200]
        snapshot["active_wars"] = [{"war_id": 100}, {"war_id": 200}]
        original = deepcopy((snapshot, frame, packet))

        result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)

        expected = {"gross_income": "9.93374", "total_expenses": "0.236",
                    "military_current": "0.111", "military_all_raised": "4.101"}
        self.assertEqual({key: row["value"] for key, row in result["raw_metrics"].items()}, expected)
        self.assertTrue(all(row["unit"] == "gold/month" for row in result["raw_metrics"].values()))
        self.assertEqual(result["sources"][0]["binding"], frame)
        self.assertEqual((snapshot, frame, packet), original)

    def test_real_DTO_without_original_planning_frame_stays_unknown(self):
        snapshot, _, packet = cash_inputs()
        result = project_existing_month_inputs_v1(snapshot, cash_packet=packet)
        self.assertEqual(result["input_gaps"]["cash"], "existing_planning_source_frame_missing")
        self.assertTrue(all(row["value"] is None for row in result["raw_metrics"].values()))
        self.assertEqual(result["sources"], [])

    def test_same_day_pre_AUTO_or_reconnected_source_cannot_fill_current_month(self):
        for key, value in (("revision", 635), ("native_revision", 737),
                           ("actor_character_id", 40000), ("bridge_pid", 226541),
                           ("connection_generation", 5), ("episode_run_id", "other-episode")):
            with self.subTest(key=key):
                snapshot, frame, packet = cash_inputs()
                frame[key] = value
                result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
                self.assertIn(key, result["input_gaps"]["cash"])
                self.assertTrue(all(row["value"] is None for row in result["raw_metrics"].values()))
        snapshot, frame, packet = cash_inputs()
        # A newly stamped outside frame cannot fix the original DTO's old revision.
        snapshot["native_revision"] += 1
        frame["native_revision"] += 1
        result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
        self.assertIn("cash", result["input_gaps"])
        self.assertEqual(result["sources"], [])

    def test_unmarked_net_or_wrong_arithmetic_and_per_war_scope_are_not_promoted(self):
        for mutation in ("marker", "net", "scope"):
            with self.subTest(mutation=mutation):
                snapshot, frame, packet = cash_inputs()
                if mutation == "marker":
                    packet.pop("monthly_income_semantics")
                elif mutation == "net":
                    packet["player_monthly_net_income"]["raw"] = packet["player_monthly_gross_income"]["raw"]
                else:
                    packet["military_expenses"]["current"]["source_scope"] = "per_war"
                result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
                self.assertIn("cash", result["input_gaps"])
                self.assertTrue(all(row["value"] is None for row in result["raw_metrics"].values()))

    def test_partial_and_incompatible_rates_keep_unknown_without_filling_zero(self):
        snapshot, frame, packet = cash_inputs()
        for field, flag, reason in (
            ("player_monthly_total_expenses", "monthly_total_expenses_ready", "monthly_total_expenses_unavailable_reason"),
            ("player_monthly_net_income", "monthly_net_income_ready", "monthly_net_income_unavailable_reason")):
            packet[field] = None
            packet["readiness"][flag] = False
            packet[reason] = "reader unavailable"
        result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
        self.assertEqual(result["raw_metrics"]["gross_income"]["value"], "9.93374")
        self.assertIsNone(result["raw_metrics"]["total_expenses"]["value"])
        snapshot, frame, packet = cash_inputs()
        packet["military_expenses"]["current"].update(gold_raw=30000,
            resource_raw_native=[30000] + [0] * 9)
        result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
        self.assertEqual(result["raw_metrics"]["military_current"]["availability"], "unknown")
        self.assertEqual(result["raw_metrics"]["total_expenses"]["value"], "0.236")

    def test_wallet_disagreement_or_missing_build_rejects_cash_without_new_reads(self):
        for mutation in ("wallet", "build"):
            with self.subTest(mutation=mutation):
                snapshot, frame, packet = cash_inputs()
                if mutation == "wallet":
                    snapshot["played_character_gold"]["raw"] += 1
                else:
                    snapshot["diagnostics"]["hello"]["game_version"] = "unknown"
                result = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
                self.assertIn("cash", result["input_gaps"])
                self.assertEqual(result["sources"], [])

    def test_current_root_is_domain_diagnostic_and_never_full_realm_scoring(self):
        snapshot, frame, root = root_inputs()
        result = project_existing_month_inputs_v1(snapshot, campaign_root_result=root, root_source_frame=frame)
        realm = result["realm_diagnostics"]
        self.assertEqual(realm["status"], "available")
        self.assertEqual(realm["domain"]["value"]["size"], 6)
        self.assertEqual(realm["territory"]["directly_held_geographic_county_title_ids"]["value"], [91])
        self.assertFalse(realm["full_realm_scoring_input_available"])
        self.assertNotIn("realm_county_count", result["raw_metrics"])
        root["campaign_root_context"]["date_raw"] -= 24
        stale = project_existing_month_inputs_v1(snapshot, campaign_root_result=root, root_source_frame=frame)
        self.assertEqual(stale["realm_diagnostics"]["status"], "unavailable")

    def test_pure_merge_keeps_founder_and_unobserved_E_M_H_inputs(self):
        snapshot, frame, packet = cash_inputs()
        start = raw_to_date(snapshot["date_raw"])
        candidate = ordinary_sample_candidate(snapshot, start_date=start, machine_id="synthetic",
            observed_at_utc="synthetic", campaign_anchor={"campaign_id": "synthetic",
                "founder_character_id": 31254, "founding_house_id": 174, "founding_dynasty_id": 174})
        before = deepcopy(candidate)
        extra = project_existing_month_inputs_v1(snapshot, cash_packet=packet, cash_source_frame=frame)
        enriched = {**candidate, "raw_metrics": {**candidate["raw_metrics"], **extra["raw_metrics"]},
                    "sources": candidate["sources"] + extra["sources"]}
        self.assertEqual(enriched["campaign_anchor"], before["campaign_anchor"])
        self.assertEqual(enriched["raw_metrics"]["gold"], before["raw_metrics"]["gold"])
        for key in ("due_commitments", "P_quality", "continuation_legal", "backup_heirs", "Q_realm", "K_dynasty"):
            self.assertEqual(enriched["raw_metrics"][key]["availability"], "unknown")
        self.assertEqual(candidate, before)


if __name__ == "__main__":
    unittest.main()
