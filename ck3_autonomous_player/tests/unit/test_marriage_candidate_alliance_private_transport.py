"""Focused transport contract for the unadvertised five-candidate read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    SCHEMA, STEP, query_first_heir_candidate_alliance_projection_private_v1,
)


IDS = [16778038, 16778252, 16778632, 16778730, 16778737]


def _frame() -> dict[str, object]:
    return {"native_revision": 3, "date_raw": 53350000, "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def _legality() -> dict[str, object]:
    return {"schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
            "status": "available", "native_revision": 3,
            "query_sequence": 7, "observed_first_heir_character_id": 38822,
            "native_legal_candidates": [
                {"played_character_id": 29829,
                 "subject_character_id": 38822,
                 "candidate_character_id": candidate}
                for candidate in IDS]}


def _reply(*, unavailable_index: int | None = None) -> dict[str, object]:
    rows = []
    for index, candidate in enumerate(IDS):
        unavailable = index == unavailable_index
        rows.append({
            "actor_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": candidate,
            "recipient_character_id": candidate,
            "status": "unavailable" if unavailable else "available",
            "failure": "projection_unavailable" if unavailable else "none",
            "projection_failure": "signature_mismatch" if unavailable else "none",
            "outcome_failure": "none",
            "predicted_outcome_if_accepted":
                None if unavailable else "marriage",
            "heir_is_adult": None if unavailable else True,
            "candidate_is_adult": None if unavailable else True,
            "heir_adult_measure_raw": None if unavailable else 16,
            "candidate_adult_measure_raw": None if unavailable else 16,
            "heir_adult_threshold_raw": None if unavailable else 16,
            "candidate_adult_threshold_raw": None if unavailable else 16,
            "grand_wedding_option_selected": None if unavailable else False,
            "heir_native_fertility": None if unavailable else {
                "source": "native_marriage_fertility_input",
                "extension_present": True, "native_gate_evaluated": True,
                "native_gate_allows": True, "effective_raw": 40000,
            },
            "candidate_native_fertility": None if unavailable else {
                "source": "native_marriage_fertility_input",
                "extension_present": True, "native_gate_evaluated": True,
                "native_gate_allows": True, "effective_raw": 65000,
            },
            "generic_costs": None if unavailable else {
                "raw_scale": 100_000, "payer_role": "actor",
                "application_timing": "on_send", "gold_raw": 0,
                "prestige_raw": 250_000 if index == 0 else 0,
                "piety_raw": 0, "renown_raw": 0,
                "influence_raw": 0, "herd_raw": 0,
                "treasury_raw": 0, "treasury_or_gold_raw": 0,
                "merit_raw": 0, "barter_goods_raw": 0,
            },
            "heir_betrothed_character_id": None,
            "heir_primary_spouse_character_id": None,
            "heir_spouse_character_ids": None if unavailable else [],
            "played_house_id": None if unavailable else 100,
            "played_dynasty_id": None if unavailable else 200,
            "heir_house_id": None if unavailable else 100,
            "heir_dynasty_id": None if unavailable else 200,
            "candidate_house_id": None if unavailable else 300 + index,
            "candidate_dynasty_id": None if unavailable else 400 + index,
            "heir_sex_selector_raw": None if unavailable else 0,
            "candidate_sex_selector_raw": None if unavailable else 1,
            "effective_matrilineal_if_accepted": None if unavailable else False,
            "matrilineal_option_selected": None if unavailable else False,
            "possible_alliance_pairs": [] if unavailable else [{
                "first_character_id": 29829,
                "second_character_id": candidate,
                "already_allied": False,
                "both_have_realm_data": True,
                "would_attempt_if_accepted": True,
            }],
        })
    return {"ok": True, "result": {
        "step": STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False,
        "native_revision": 3, "legality_query_sequence": 7,
        "status": "unavailable" if unavailable_index is not None
                  else "available", "rows": rows,
    }}


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, reply: dict[str, object] | None) -> None:
        self.reply = reply

    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> dict[str, object] | None:
        return self.reply


class _Driver:
    def __init__(self, reply: dict[str, object] | None,
                 frames: list[dict[str, object]]) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(reply)
        self.frames = frames

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)


class MarriageCandidateAlliancePrivateTransportTests(unittest.TestCase):
    def test_optional_native_fertility_floor_reaches_real_service_diagnostic(self) -> None:
        """Consume four native wires when supplied; otherwise authored shapes.

        Compiled FIRST sets XAR_FIRST_HEIR_FERTILITY_NATIVE_WIRE_DIR to the
        parent-owned rich-reader/serializer output directory. The old-absent
        case is a compatibility copy, not a new native execution or live
        observation. This method invokes the production rich transport and
        the real Service family-planning entry without submitting a proposal.
        """
        import json
        import os
        import tempfile

        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        raw_field = "native_candidate_fertility_floor_raw"
        comparison_field = "candidate_native_fertility_floor_comparison_v1"
        wire_dir = os.environ.get("XAR_FIRST_HEIR_FERTILITY_NATIVE_WIRE_DIR")
        output_path = os.environ.get("XAR_FIRST_HEIR_FERTILITY_SERVICE_OUTPUT")
        inputs = [
            ("positive", 10000, [15000, 10000, -1, 0, 25000],
             [True, False, False, False, True]),
            ("negative", -2, [-1, -2, -3, 0, 1],
             [True, False, False, True, True]),
            ("unbound", None, [15000, 10000, -1, 0, 25000],
             [None] * 5),
            ("deniedread", None, [15000, 10000, -1, 0, 25000],
             [None] * 5),
        ]
        cases = []
        for name, floor, candidate_raws, expected_passes in inputs:
            if wire_dir:
                reply = json.loads((Path(wire_dir) / f"{name}.json")
                                   .read_text(encoding="utf-8"))
            else:
                reply = _reply()
                for row, raw in zip(reply["result"]["rows"], candidate_raws):
                    row[raw_field] = floor
                    row["candidate_native_fertility"]["effective_raw"] = raw
                    row.update({
                        "requested_matrilineal_option": False,
                        "selected_option_readback": None,
                        "final_legality_sampled": True,
                        "complete_can_send": True,
                        "recipient_ai_accept_raw": 1600000,
                        "recipient_answer_status_raw": 0,
                    })
            self.assertEqual(len(reply["result"]["rows"]), 5)
            for row in reply["result"]["rows"]:
                self.assertIn(raw_field, row)
                self.assertEqual(row[raw_field], floor)
            if floor is not None:
                self.assertEqual([
                    row["candidate_native_fertility"]["effective_raw"]
                    for row in reply["result"]["rows"]], candidate_raws)
            cases.append((name, reply, expected_passes))
        old_absent = deepcopy(cases[0][1])
        for row in old_absent["result"]["rows"]:
            del row[raw_field]
        cases.append(("oldabsent", old_absent, [None] * 5))

        class ServiceDriver(_Driver):
            allow_private_family_marriage_formal_trial = True

            def __init__(self, reply, frame, legality, state_dir):
                super().__init__(reply, [deepcopy(frame), deepcopy(frame)])
                self.legality = legality
                self.state_dir = state_dir
                self.consumed_projection = None

            def query_observed_first_heir_marriage_legality_v1(
                self, *, expected_native_revision,
            ):
                if expected_native_revision != self.legality["native_revision"]:
                    raise AssertionError("Service changed the fixture frame")
                return self.legality

            def query_first_heir_candidate_alliance_projection_private_v1(
                self, *, legality, candidate_character_ids,
            ):
                self.consumed_projection = (
                    query_first_heir_candidate_alliance_projection_private_v1(
                        self, legality=legality,
                        candidate_character_ids=candidate_character_ids))
                return self.consumed_projection

        selected_candidates = []
        service_outputs = []
        for name, native_reply, expected_passes in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                reply = deepcopy(native_reply)
                result = reply["result"]
                native_rows = result["rows"]
                frame = _frame()
                frame.update({
                    "native_revision": result["native_revision"],
                    "active_event": None,
                    "pending_character_interaction": None, "active_wars": [],
                    "episode_run_id": "fertility-floor-offline-compound",
                    "played_character": {
                        "character_id": native_rows[0]["actor_character_id"],
                        "alive": True,
                    },
                    "diagnostics": {"hello": {
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                    }},
                })
                legality = {
                    "schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
                    "status": "available", "native_revision": frame["native_revision"],
                    "query_sequence": result["legality_query_sequence"],
                    "observed_first_heir_character_id": native_rows[0]["heir_character_id"],
                    "exact_ck3_build": CK3_12004.game_version,
                    "exe_sha256": CK3_12004.executable_sha256,
                    "native_legal_candidates": [{
                        "candidate_character_id": row["candidate_character_id"],
                        "played_character_id": row["actor_character_id"],
                        "subject_character_id": row["heir_character_id"],
                        "recipient_matchmaker_character_id": row["recipient_character_id"],
                        "heir_adult_measure_raw": row["heir_adult_measure_raw"],
                        "candidate_adult_measure_raw": row["candidate_adult_measure_raw"],
                        "played_dynasty_id": row["played_dynasty_id"],
                        "heir_dynasty_id": row["heir_dynasty_id"],
                        "candidate_dynasty_id": row["candidate_dynasty_id"],
                        "realm_backed_actor_recipient": True,
                        "complete_can_send": row["complete_can_send"],
                        "recipient_answer_allows_send":
                            row["recipient_answer_status_raw"] in (0, 1),
                        "recipient_answer_status_raw": row["recipient_answer_status_raw"],
                        "recipient_ai_accept_raw": row["recipient_ai_accept_raw"],
                        **({"final_legality_sampled": row["final_legality_sampled"]}
                           if "final_legality_sampled" in row else {}),
                    } for row in native_rows],
                }
                driver = ServiceDriver(reply, frame, legality, Path(temporary))
                planned = GameplayBridgeService(driver)._plan_private_family_opportunity_v1(
                    {"plan": {"selected_step": "life-advance"}}, frame)
                diagnostic = planned["plan"]["family_marriage_private_diagnostic"]
                self.assertEqual(diagnostic["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(len(diagnostic["rows"]), 5)
                selected_candidates.append(
                    planned["plan"]["family_marriage_choice"]["candidate_character_id"])
                service_outputs.append({
                    "case": name,
                    "family_marriage_choice": deepcopy(
                        planned["plan"]["family_marriage_choice"]),
                    "family_marriage_private_diagnostic": deepcopy(diagnostic),
                })
                for index, observed in enumerate(diagnostic["rows"]):
                    original = native_rows[index]
                    comparison = observed[comparison_field]
                    self.assertEqual(observed[raw_field], original.get(raw_field))
                    self.assertEqual(observed["candidate_native_fertility"],
                                     original["candidate_native_fertility"])
                    self.assertEqual(observed["heir_native_fertility"],
                                     original["heir_native_fertility"])
                    self.assertEqual(observed["recipient_ai_accept_raw"],
                                     original["recipient_ai_accept_raw"])
                    self.assertEqual(observed["recipient_answer_status_raw"],
                                     original["recipient_answer_status_raw"])
                    self.assertIs(observed["complete_can_send"],
                                  original["complete_can_send"])
                    if "final_legality_sampled" in original:
                        self.assertIs(driver.legality["native_legal_candidates"][index][
                            "final_legality_sampled"], original["final_legality_sampled"])
                    self.assertEqual(comparison["source"],
                                     "derived_signed_native_fertility_floor_comparison")
                    self.assertIs(comparison["ready"], expected_passes[index] is not None)
                    self.assertIs(comparison["passes"], expected_passes[index])
                    consumed = driver.consumed_projection["rows"][index]
                    if name == "oldabsent":
                        self.assertNotIn(raw_field, consumed)
                    else:
                        self.assertIn(raw_field, consumed)
                request = driver.endpoint.request
                self.assertEqual(request["step"], STEP)
                self.assertEqual([request[f"candidate_id_{index}"] for index in range(5)],
                                 [row["candidate_character_id"] for row in native_rows])
        self.assertEqual(len(set(selected_candidates)), 1)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "schema": "xar.ck3.first-heir-fertility-floor-service-compound.v1",
                "source_mode": ("compiled_native_whole_wire" if wire_dir
                                else "authored_source_shape"),
                "native_wire_directory": wire_dir,
                "production_live": False, "material_result": False,
                "cases": service_outputs,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_paired_native_fertility_is_consumed_by_rich_rows(self) -> None:
        frame = _frame()
        frame["diagnostics"] = {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }}
        legality = _legality()
        legality.update({"exact_ck3_build": CK3_12003.game_version,
                         "exe_sha256": CK3_12003.executable_sha256})
        reply = _reply()
        native_rows = reply["result"]["rows"]
        candidate_inputs = [
            {"source": "native_marriage_fertility_input",
             "extension_present": True, "native_gate_evaluated": True,
             "native_gate_allows": True, "effective_raw": 65000},
            {"source": "native_marriage_fertility_input",
             "extension_present": True, "native_gate_evaluated": True,
             "native_gate_allows": False, "effective_raw": 0},
            {"source": "native_marriage_fertility_input",
             "extension_present": False, "native_gate_evaluated": False,
             "native_gate_allows": None, "effective_raw": 0},
            {"source": "native_marriage_fertility_input",
             "extension_present": True, "native_gate_evaluated": True,
             "native_gate_allows": True, "effective_raw": 0},
            {"source": "native_marriage_fertility_input",
             "extension_present": True, "native_gate_evaluated": True,
             "native_gate_allows": True, "effective_raw": -31},
        ]
        for row, fertility in zip(native_rows, candidate_inputs):
            row["candidate_native_fertility"] = fertility
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [deepcopy(frame), deepcopy(frame)]),
            legality=legality, candidate_character_ids=IDS)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["exact_ck3_build"], CK3_12003.game_version)
        self.assertEqual(result["exe_sha256"], CK3_12003.executable_sha256)
        for index, fertility in enumerate(candidate_inputs):
            with self.subTest(candidate=IDS[index]):
                self.assertEqual(result["rows"][index]["candidate_native_fertility"],
                                 fertility)
                self.assertEqual(result["rows"][index]["heir_native_fertility"],
                                 native_rows[index]["heir_native_fertility"])
                self.assertEqual(result["rows"][index]["heir_native_fertility"][
                    "effective_raw"], 40000)

        partial = _reply(unavailable_index=2)
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(partial, [deepcopy(frame), deepcopy(frame)]),
            legality=legality, candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["heir_native_fertility"])
        self.assertIsNone(result["rows"][2]["candidate_native_fertility"])
        self.assertEqual(result["rows"][0]["candidate_native_fertility"][
            "effective_raw"], 65000)

        missing = _reply()
        del missing["result"]["rows"][0]["candidate_native_fertility"]
        with self.assertRaisesRegex(BridgeUnavailableError, "row identity malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(missing, [deepcopy(frame)]), legality=legality,
                candidate_character_ids=IDS)

        invalid = _reply()
        invalid["result"]["rows"][0]["candidate_native_fertility"].update({
            "native_gate_allows": False, "effective_raw": 1})
        with self.assertRaisesRegex(BridgeUnavailableError,
                                    "native fertility input malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(invalid, [deepcopy(frame)]), legality=legality,
                candidate_character_ids=IDS)

    def test_five_dynamic_legal_ids_are_sent_and_read_without_advertising(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        result = query_first_heir_candidate_alliance_projection_private_v1(
            driver, legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertFalse(result["advertised"])
        self.assertEqual(driver.endpoint.request["step"], STEP)
        self.assertEqual(driver.endpoint.request["candidate_id_4"], IDS[4])
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(result["rows"][0]["predicted_outcome_if_accepted"],
                         "marriage")
        self.assertIs(result["rows"][0]["heir_is_adult"], True)
        self.assertIs(result["rows"][0]["candidate_is_adult"], True)
        self.assertEqual(result["rows"][0]["heir_adult_measure_raw"], 16)
        self.assertIs(result["rows"][0]["grand_wedding_option_selected"], False)
        self.assertEqual(result["rows"][0]["heir_spouse_character_ids"], [])
        self.assertEqual(result["rows"][0]["played_dynasty_id"], 200)
        self.assertEqual(result["rows"][4]["candidate_dynasty_id"], 404)
        self.assertEqual(result["rows"][0]["heir_sex_selector_raw"], 0)
        self.assertIs(result["rows"][0]["effective_matrilineal_if_accepted"],
                      False)
        self.assertEqual(result["rows"][0]["generic_costs"]["prestige_raw"],
                         250_000)
        self.assertEqual(result["rows"][4]["generic_costs"]["prestige_raw"], 0)

    def test_one_unavailable_pair_does_not_become_false_or_success(self) -> None:
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(_reply(unavailable_index=2), [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["matrilineal_option_selected"])
        self.assertIsNone(result["rows"][2]["predicted_outcome_if_accepted"])
        self.assertIsNone(result["rows"][2]["heir_is_adult"])
        self.assertIsNone(result["rows"][2]["heir_adult_measure_raw"])
        self.assertIsNone(result["rows"][2]["heir_spouse_character_ids"])
        self.assertIsNone(result["rows"][2]["candidate_dynasty_id"])
        self.assertIsNone(result["rows"][2]["candidate_sex_selector_raw"])
        self.assertIsNone(result["rows"][2]["effective_matrilineal_if_accepted"])
        self.assertIsNone(result["rows"][2]["generic_costs"])
        self.assertEqual(result["rows"][2]["possible_alliance_pairs"], [])

    def test_same_heir_relationship_is_read_across_five_candidates(self) -> None:
        reply = _reply()
        for row in reply["result"]["rows"]:
            row["heir_primary_spouse_character_id"] = 456
            row["heir_spouse_character_ids"] = [456]
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["rows"][4]["heir_spouse_character_ids"], [456])
        reply["result"]["rows"][4]["heir_spouse_character_ids"] = []
        with self.assertRaisesRegex(BridgeUnavailableError, "relationship malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply["result"]["rows"][4]["heir_primary_spouse_character_id"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "changed between candidates"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)

    def test_unavailable_heir_relationship_stays_unknown(self) -> None:
        reply = _reply(unavailable_index=2)
        row = reply["result"]["rows"][2]
        row["failure"] = "heir_relationship_unavailable"
        row["projection_failure"] = "none"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertIsNone(result["rows"][2]["heir_spouse_character_ids"])
        self.assertEqual(result["status"], "unavailable")

    def test_full_lineage_ids_are_consistent_and_absence_is_explicit(self) -> None:
        reply = _reply()
        reply["result"]["rows"][0]["candidate_house_id"] = None
        reply["result"]["rows"][0]["candidate_dynasty_id"] = None
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertIsNone(result["rows"][0]["candidate_dynasty_id"])
        reply["result"]["rows"][0]["candidate_dynasty_id"] = 400
        with self.assertRaisesRegex(BridgeUnavailableError, "lineage identity malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][3]["heir_dynasty_id"] = 201
        with self.assertRaisesRegex(BridgeUnavailableError, "heir lineage changed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        del reply["result"]["rows"][1]["candidate_house_id"]
        with self.assertRaisesRegex(BridgeUnavailableError, "row identity malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)

    def test_lineage_read_failure_remains_unavailable(self) -> None:
        reply = _reply(unavailable_index=2)
        row = reply["result"]["rows"][2]
        row["failure"] = "lineage_unavailable"
        row["projection_failure"] = "none"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["heir_house_id"])

    def test_sex_selector_is_raw_and_consistent_without_semantic_guess(self) -> None:
        reply = _reply()
        reply["result"]["rows"][3]["heir_sex_selector_raw"] = 1
        with self.assertRaisesRegex(BridgeUnavailableError, "heir sex selector changed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply["result"]["rows"][3]["heir_sex_selector_raw"] = 2
        with self.assertRaisesRegex(BridgeUnavailableError, "sex selector malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)

    def test_effective_lineality_uses_exact_same_selector_branch(self) -> None:
        reply = _reply()
        for row in reply["result"]["rows"]:
            row["heir_sex_selector_raw"] = 1
            row["candidate_sex_selector_raw"] = 1
            row["effective_matrilineal_if_accepted"] = True
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertIs(result["rows"][0]["matrilineal_option_selected"], False)
        self.assertIs(result["rows"][0]["effective_matrilineal_if_accepted"], True)
        reply["result"]["rows"][2]["effective_matrilineal_if_accepted"] = False
        with self.assertRaisesRegex(BridgeUnavailableError, "effective marriage lineality"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)

    def test_outcome_failure_does_not_become_a_marriage(self) -> None:
        reply = _reply(unavailable_index=2)
        row = reply["result"]["rows"][2]
        row["failure"] = "outcome_unavailable"
        row["projection_failure"] = "none"
        row["outcome_failure"] = "runtime_threshold_unavailable"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["predicted_outcome_if_accepted"])

    def test_betrothal_breakdown_distinguishes_shared_minor_heir_from_candidate(self) -> None:
        reply = _reply()
        for row in reply["result"]["rows"]:
            row["heir_is_adult"] = False
            row["heir_adult_measure_raw"] = 15
            row["predicted_outcome_if_accepted"] = "betrothal"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertTrue(all(row["heir_is_adult"] is False for row in result["rows"]))
        self.assertTrue(all(row["candidate_is_adult"] is True for row in result["rows"]))
        reply["result"]["rows"][4]["heir_adult_measure_raw"] = 14
        with self.assertRaisesRegex(BridgeUnavailableError, "adult outcome breakdown"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply["result"]["rows"][4]["heir_adult_measure_raw"] = 15
        reply["result"]["rows"][4]["heir_is_adult"] = True
        with self.assertRaisesRegex(BridgeUnavailableError, "adult outcome breakdown"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["grand_wedding_option_selected"] = True
        reply["result"]["rows"][0]["predicted_outcome_if_accepted"] = "betrothal"
        query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)

    def test_duplicate_or_not_legal_id_never_submits(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        with self.assertRaises(ValueError):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(),
                candidate_character_ids=IDS[:4] + IDS[0:1])
        self.assertIsNone(driver.endpoint.request)
        with self.assertRaises(BridgeUnavailableError):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(),
                candidate_character_ids=IDS[:4] + [999999])
        self.assertIsNone(driver.endpoint.request)

    def test_red_and_frame_drift_are_not_consumed(self) -> None:
        driver = _Driver({"ok": False, "error": "mailbox busy"}, [_frame()])
        with self.assertRaisesRegex(BridgeUnavailableError, "RED: mailbox busy"):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(), candidate_character_ids=IDS)
        changed = deepcopy(_frame())
        changed["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "frame changed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(_reply(), [_frame(), changed]),
                legality=_legality(), candidate_character_ids=IDS)

    def test_native_identity_or_value_mismatch_is_red(self) -> None:
        reply = _reply()
        reply["result"]["rows"][1]["candidate_character_id"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "row identity"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["possible_alliance_pairs"][0][
            "would_attempt_if_accepted"] = False
        with self.assertRaisesRegex(BridgeUnavailableError, "pair malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["predicted_outcome_if_accepted"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "lost native option"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][1]["generic_costs"]["prestige_raw"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "cost vector malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["generic_costs"]["application_timing"] = "on_accept"
        with self.assertRaisesRegex(BridgeUnavailableError, "cost vector malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)


if __name__ == "__main__":
    unittest.main()
