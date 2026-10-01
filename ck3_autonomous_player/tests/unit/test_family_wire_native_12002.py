"""Actual new FAMILY provider and production serializer through Python parsers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = ROOT / "native_bridge" / "research" / "fixtures"

from test_nonwar_private_python_12002 import FixtureDriver, frame
from xar_autoplayer.bridge.nonwar_private_build import private_native_provenance
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    query_first_heir_candidate_alliance_projection_private_v1,
)
from xar_autoplayer.bridge.marriage_matchmaking_private_transport import (
    PRIVATE_RANKED_MARRIAGE_STEP_V1, query_ranked_marriage_private_v1,
)
from xar_autoplayer.bridge.player_child_marriage_value_private_transport import (
    query_player_child_marriage_value_private_v1,
)
from xar_autoplayer.player_child_matrilineal_formal_consumer import _positive_value
from xar_autoplayer.family_marriage_formal_consumer import rank_first_heir_marriage_candidates


def actual_wire(name: str) -> dict[str, object]:
    data = (FIXTURES / (name + ".json")).read_bytes()
    provenance = json.loads((FIXTURES / (name + ".provenance.json")).read_text(encoding="utf-8"))
    ranked = provenance.get("schema") == "xar.offline.native-family-ranked-wire.v1"
    expected_sha = (provenance["files"][0]["sha256"] if ranked
                    else provenance["fixture_sha256"])
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise AssertionError("actual native producer fixture changed")
    if provenance["local_ck3_contacted" if ranked else "local_ck3_accessed"] is not False:
        raise AssertionError("wire fixture is not isolated offline native evidence")
    return json.loads(data)


def caller_legality(native: dict[str, object], snapshot: dict[str, object],
                    *, child: bool) -> dict[str, object]:
    """Supply the parser's caller context, derived from actual returned roles.

    This context is not a second native subject/enumeration observation.
    The native output payload itself is passed through without reconstruction.
    """
    rows = native["rows"]
    first = rows[0]
    return {
        "schema": ("xar.ck3.player-child-marriage-subject.v1" if child else
                   "xar.ck3.observed-first-heir-marriage-legality.v1"),
        **private_native_provenance(snapshot), "status": "available",
        "read_only": True, "advertised": False, "player_child_verified": True,
        "played_character_id": first["actor_character_id"],
        "subject_character_id": first["heir_character_id"],
        "observed_first_heir_character_id": first["heir_character_id"],
        "native_revision": native["native_revision"],
        "query_sequence": native["legality_query_sequence"],
        "house_id": first["heir_house_id"], "dynasty_id": first["heir_dynasty_id"],
        "native_legal_candidates": [{
            "played_character_id": row["actor_character_id"],
            "subject_character_id": row["heir_character_id"],
            "candidate_character_id": row["candidate_character_id"],
            "recipient_matchmaker_character_id": row["recipient_character_id"],
            "recipient_ai_accept_raw": row["recipient_ai_accept_raw"],
            "candidate_dynasty_id": row["candidate_dynasty_id"],
            "candidate_adult_measure_raw": row["candidate_adult_measure_raw"],
            "heir_adult_measure_raw": row["heir_adult_measure_raw"],
        } for row in rows],
    }


class FamilyWireNative12002Tests(unittest.TestCase):
    def test_actual_ranked38_preserves_native_tie_order_score_and_full_pair_roles(self):
        observed = actual_wire("ck3_12002_ranked38_wire")
        snapshot = frame(actor=observed["subject_character_id"],
                         revision=observed["native_revision"], date_raw=observed["date_raw"])
        # The raw actual C++ observation is untouched; only the transport's
        # existing outer result envelope is supplied by the isolated endpoint.
        native = {"step": PRIVATE_RANKED_MARRIAGE_STEP_V1, "accepted": True,
                  "status": "available", "query_sequence": 7,
                  "ranked_marriage_observation": observed}
        driver = FixtureDriver(snapshot, native)
        result = query_ranked_marriage_private_v1(
            driver, expected_native_revision=observed["native_revision"])
        self.assertEqual(result["status"], "available")
        rows = result["observation"]["candidates"]
        self.assertEqual(rows, observed["candidates"])
        self.assertEqual([row["rank"] for row in rows], [1, 2, 3])
        self.assertEqual([row["native_candidate_score"] for row in rows], [200, 200, 99])
        self.assertEqual([row["candidate_character_id"] for row in rows],
                         [50331652, 50331650, 50331651])
        self.assertEqual(rows[0]["pair_roles"]["intermediary_character_id"], 4294967295)
        self.assertEqual(rows[1]["predicted_outcome"], "betrothal")
        self.assertEqual(result["exact_ck3_build"], "1.20.0.2")
        self.assertEqual(observed["proof_epoch"], 9)
        self.assertEqual([request["step"] for request in driver.requests],
                         [PRIVATE_RANKED_MARRIAGE_STEP_V1])
        self.assertFalse(getattr(driver, "allow_private_family_marriage_formal_trial", False))

    def test_actual_five_candidate_rich_value_enters_formal_readback_without_native_rank(self):
        wire = actual_wire("ck3_12002_rich48_five_wire")
        native = wire["result"]
        rows = native["rows"]
        snapshot = frame(actor=rows[0]["actor_character_id"],
                         revision=native["native_revision"], date_raw=53220000)
        legality = caller_legality(native, snapshot, child=False)
        driver = FixtureDriver(snapshot, native)
        candidates = [row["candidate_character_id"] for row in rows]
        result = query_first_heir_candidate_alliance_projection_private_v1(
            driver, legality=legality, candidate_character_ids=candidates)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["rows"], rows)
        self.assertEqual(len(set(candidates)), 5)
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(result["exact_ck3_build"], "1.20.0.2")
        for row in result["rows"]:
            self.assertEqual(len(row["possible_alliance_pairs"]), 3)
            self.assertIsNone(row["candidate_dynasty_id"])
            self.assertEqual(row["generic_costs"]["gold_raw"], -20000)
            self.assertIs(row["heir_is_adult"], True)
            self.assertEqual(row["heir_adult_threshold_raw"], 16)
            self.assertNotIn("rank", row)
        # Actual valid readback may yield no eligible pair under current quality policy.
        self.assertEqual(rank_first_heir_marriage_candidates(legality, result), [])
        self.assertEqual([request["step"] for request in driver.requests], [native["step"]])
        self.assertFalse(getattr(driver, "allow_private_family_marriage_formal_trial", False))

    def test_actual_child_value_accepts_legitimate_absent_dynasty_and_zero_fertility(self):
        wire = actual_wire("ck3_12002_child_value_wire")
        native = wire["result"]
        row = native["rows"][0]
        snapshot = frame(actor=row["actor_character_id"],
                         revision=native["native_revision"], date_raw=53220000)
        legality = caller_legality(native, snapshot, child=True)
        driver = FixtureDriver(snapshot, native)
        driver.allow_private_player_child_marriage_subject_query = True
        result = query_player_child_marriage_value_private_v1(
            driver, legality=legality, candidate_character_id=row["candidate_character_id"],
            request_matrilineal_option=True)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["row"], row)
        self.assertIsNone(result["row"]["candidate_dynasty_id"])
        self.assertIsNone(result["row"]["heir_native_fertility"]["native_gate_allows"])
        self.assertEqual(result["row"]["candidate_native_fertility"]["effective_raw"], 0)
        self.assertEqual(result["row"]["generic_costs"]["gold_raw"], -20000)
        self.assertIs(result["row"]["complete_can_send"], True)
        self.assertIs(result["row"]["effective_matrilineal_if_accepted"], True)
        # Available observed value can be outside the existing narrow policy.
        self.assertFalse(_positive_value(legality, result))
        self.assertEqual([request["step"] for request in driver.requests], [native["step"]])
        self.assertFalse(getattr(driver, "allow_private_player_child_matrilineal_action", False))


if __name__ == "__main__":
    unittest.main()
