"""Offline migration replay of reviewed DTOs; these are not new live packets."""

from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import test_ck3_12002_python_transport as core
import test_event_feature_contracts_12002 as event_features
import test_player_faction_alerts_v1_bridge as factions
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003


def patch_identity(value, *, field=None):
    """Mirror the .3 adapter's outward identity/schema translation only."""
    if isinstance(value, dict):
        return {key: patch_identity(item, field=key) for key, item in value.items()}
    if isinstance(value, list):
        return [patch_identity(item) for item in value]
    if isinstance(value, str):
        if value == CK3_12002.executable_sha256:
            return CK3_12003.executable_sha256
        if field == "schema" and value.startswith("ck3_12002_"):
            return "ck3_12003_" + value[len("ck3_12002_"):]
        return value.replace("1.20.0.2", "1.20.0.3")
    return value


def first_actor(value):
    if isinstance(value, dict):
        actor = value.get("played_character_id", value.get("player_character_id"))
        if type(actor) is int and actor >= 0:
            return actor
        for item in value.values():
            found = first_actor(item)
            if found is not None:
                return found
    return None


class ReplayDriver:
    def __init__(self, packet):
        self.packet = patch_identity(packet)
        result = self.packet["result"]
        self.snapshot = {
            "snapshot_id": "patch-migration-replay", "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": first_actor(result), "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {"expected_ck3_version": CK3_12003.game_version,
                                       "expected_ck3_sha256": CK3_12003.executable_sha256}},
        }
        self.endpoint = self
        self.state = NativeProtocolState("offline-patch-migration-replay")
        self.sent = []

    def __getattr__(self, name):
        if name.startswith("allow_private_"):
            return True
        raise AttributeError(name)

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.state.ingest(packet)


class PatchTransportTests(unittest.TestCase):
    def test_core_campaign_and_event_feature_queries_preserve_reviewed_values(self):
        frame = patch_identity(core._baseline_campaign())
        self.assertEqual(core.normalize_campaign_root_context_v1(
            frame, expected_date_raw=frame["date_raw"], expected_snapshot_revision=17,
        ), frame)
        for factory, normalize in (
            (event_features._event_frame, event_features._event),
            (event_features._pending_frame, event_features._pending),
            (event_features._feature_frame, event_features._features),
        ):
            with self.subTest(factory=factory.__name__):
                source = patch_identity(factory())
                self.assertEqual(normalize(source), source)
        mixed = patch_identity(event_features._feature_frame())
        mixed["build"]["exe_sha256"] = CK3_12002.executable_sha256
        with self.assertRaises(ValueError):
            event_features._features(mixed)

    def test_existing_prewar_entry_and_claim_terms_keep_reviewed_addresses(self):
        prewar = core.prewar_fixture._payload()
        prewar["provenance"].update(game_version=CK3_12003.game_version,
            executable_sha256=CK3_12003.executable_sha256, unit_storage_slot_rva="0x5D1E380")
        result = core.normalize_prewar_primary_scope(prewar,
            expected_declaration_id=prewar["declaration_id"],
            expected_actor_character_id=prewar["actor_character_id"])
        self.assertFalse(result["readiness"]["war_entry_forecast_inputs_ready"])
        entry = core.entry_fixture._payload()
        entry["provenance"] = {
            "game_version": CK3_12003.game_version, "executable_sha256": CK3_12003.executable_sha256,
            "assessment_rva": "0x1A23240", "network_collector_rva": "0x1A24010",
            "power_leaf": "CCharacter+0x1C0->+0x308", "fixed_point_scale": 100000,
        }
        self.assertEqual(core.normalize_war_entry_assessments(entry)["assessments"], entry["assessments"])
        terms = core.terms_fixture._available_terms()
        terms["provenance"].update(game_version=CK3_12003.game_version,
            executable_sha256=CK3_12003.executable_sha256,
            native_reader="CWar+0x270/+0x290;0x2B9ECD0",
            claim_script_sha256="887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4")
        self.assertEqual(core.normalize_war_termination_terms(terms), terms)
        recorded = json.loads((PROJECT / "tests/fixtures/war_termination_options_12002_replay.json").read_text())
        actual = core.normalize_war_termination_options(recorded["war_termination_options"], source_build=CK3_12003)
        self.assertEqual(actual["options"]["white_peace"]["recipient_response"]["status"], "unavailable")

    def test_faction_dto_accepts_selected_patch_identity(self):
        frame = factions._partial_frame()
        frame["provenance"] = {"game_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
            "backend_id": CK3_12003.backend_id("player-faction-alerts-v1")}
        actual = normalize_player_faction_alerts_v1(frame,
            expected_date_raw=frame["date_raw"], expected_snapshot_revision=frame["snapshot_revision"],
            expected_game_version=CK3_12003.game_version,
            expected_executable_sha256=CK3_12003.executable_sha256)
        self.assertEqual(actual["provenance"], frame["provenance"])
        self.assertFalse(actual["readiness"]["alert_ready"])

    def test_existing_private_read_queries_preserve_patch_labels_and_source_values(self):
        cases = (
            ("player_religion_context", "mailbox/current-zero.json"),
            ("player_religion_doctrines", "mailbox/current-scopes.json"),
            ("player_religion_doctrine_catalogue", "named-loaded-catalogue.json"),
            ("player_religion_draft_groups", "visible-multi-slots.json"),
            ("player_religion_draft_doctrine_choices", "visible-four-slots.json"),
            ("player_religion_draft_tenet_choices", "native-current-draft.json"),
            ("player_religion_draft_resource_costs", "native-current-draft.json"),
            ("player_religion_reform_context", "absent-window.json"),
            ("player_religion_ai_reform_inputs", "multiple-controllers.json"),
            ("player_rite_governance", "distinct-zero.json"),
            ("player_rite_members", "current-members.json"),
        )
        for domain, name in cases:
            with self.subTest(domain=domain):
                path = PROJECT / "native_bridge/research/fixtures" / f"ck3_12002_{domain}" / name
                driver = ReplayDriver(json.loads(path.read_text(encoding="utf-8")))
                module = importlib.import_module(f"xar_autoplayer.bridge.{domain}_private_transport")
                query = getattr(module, f"query_{domain}_private_v1")
                actual = query(driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1)
                native = driver.packet["result"][domain]
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(len(driver.sent), 1)

    def test_sway_completion_and_crown_law_query_bind_patch_frame(self):
        import test_ck3_12002_sway_completion_wire as sway
        import test_ck3_12002_realm_law_formal_wire as law
        driver = sway.CompletionPacketDriver(patch_identity(sway.load_fixture("current-wire.json")))
        driver.snapshot = patch_identity(driver.snapshot)
        result = sway.query(driver)
        self.assertEqual(result["exact_ck3_build"], CK3_12003.game_version)
        snapshot = patch_identity(law.query_frame())
        result = law.query_realm_law_crown_action_private_v1(
            law.LawDriver(patch_identity(law.wire("query")), snapshot),
            expected_revision=snapshot["revision"], timeout_seconds=1)
        self.assertEqual(result["exact_ck3_build"], CK3_12003.game_version)


if __name__ == "__main__":
    unittest.main()
