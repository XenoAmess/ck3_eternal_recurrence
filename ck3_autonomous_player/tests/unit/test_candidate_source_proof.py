from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.candidate_source_proof import (
    CANDIDATE_SOURCE_PROOF_POLICY,
    CandidateSourceProofError,
    candidate_source_sequence_preimage,
    candidate_source_sequence_sha256,
    normalize_candidate_source_proof,
)


class CandidateSourceProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "role": "commander",
                "source_army_id": 16777217,
                "source_regiment_id": None,
                "character_id": 16777218,
            },
            {
                "role": "knight",
                "source_army_id": 16777217,
                "source_regiment_id": 16777217,
                "character_id": 16777218,
            },
        ]
        self.proof = {
            "policy": CANDIDATE_SOURCE_PROOF_POLICY,
            "source_vector_equivalence": True,
            "sequence_sha256": (
                "BED2F60F06753A1E834BAEED9D1926E4B574DD833E74E39B997CFB1EC4CDCF8B"
            ),
            "ordered_sources": copy.deepcopy(self.rows),
        }

    def test_native_compact_preimage_and_available_golden_digest_are_exact(self) -> None:
        expected = (
            '{"policy":"ccombat_side_commanders_then_knights_native_source_'
            'equivalence_v1","side_index":0,"ordered_sources":['
            '{"role":"commander","source_army_id":16777217,'
            '"source_regiment_id":null,"character_id":16777218},'
            '{"role":"knight","source_army_id":16777217,'
            '"source_regiment_id":16777217,"character_id":16777218}]}'
        ).encode("utf-8")
        self.assertEqual(candidate_source_sequence_preimage(0, self.rows), expected)
        self.assertEqual(
            candidate_source_sequence_sha256(0, self.rows),
            self.proof["sequence_sha256"],
        )
        self.assertEqual(
            normalize_candidate_source_proof(self.proof, side_index=0),
            self.proof,
        )

    def test_defender_native_golden_digest_is_exact(self) -> None:
        rows = [
            {
                "role": "knight",
                "source_army_id": 16777218,
                "source_regiment_id": 16777219,
                "character_id": 16777219,
            }
        ]
        self.assertEqual(
            candidate_source_sequence_sha256(1, rows),
            "DC94F02BFE75DB393A6E90847C27D39FE980948E4A2BABDE8CAC61E29C9E145F",
        )

    def test_schema_policy_equivalence_and_digest_are_fail_closed(self) -> None:
        mutations = []
        extra = copy.deepcopy(self.proof)
        extra["extra"] = None
        mutations.append(extra)
        missing = copy.deepcopy(self.proof)
        missing.pop("ordered_sources")
        mutations.append(missing)
        policy = copy.deepcopy(self.proof)
        policy["policy"] = "drift"
        mutations.append(policy)
        equivalence = copy.deepcopy(self.proof)
        equivalence["source_vector_equivalence"] = False
        mutations.append(equivalence)
        lowercase_digest = copy.deepcopy(self.proof)
        lowercase_digest["sequence_sha256"] = str(
            lowercase_digest["sequence_sha256"]
        ).lower()
        mutations.append(lowercase_digest)
        wrong_side = copy.deepcopy(self.proof)
        mutations.append(wrong_side)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(
                CandidateSourceProofError
            ):
                normalize_candidate_source_proof(
                    mutation, side_index=1 if mutation is wrong_side else 0
                )

    def test_row_roles_ids_and_native_commander_then_knight_order_are_strict(self) -> None:
        cases: list[list[dict[str, object]]] = []
        commander_regiment = copy.deepcopy(self.rows)
        commander_regiment[0]["source_regiment_id"] = 7
        cases.append(commander_regiment)
        knight_null_regiment = copy.deepcopy(self.rows)
        knight_null_regiment[1]["source_regiment_id"] = None
        cases.append(knight_null_regiment)
        bool_id = copy.deepcopy(self.rows)
        bool_id[1]["character_id"] = True
        cases.append(bool_id)
        knight_then_commander = list(reversed(copy.deepcopy(self.rows)))
        cases.append(knight_then_commander)
        extra_key = copy.deepcopy(self.rows)
        extra_key[0]["extra"] = 1
        cases.append(extra_key)
        for index, rows in enumerate(cases):
            proof = {
                "policy": CANDIDATE_SOURCE_PROOF_POLICY,
                "source_vector_equivalence": True,
                "sequence_sha256": self.proof["sequence_sha256"],
                "ordered_sources": rows,
            }
            with self.subTest(index=index), self.assertRaises(
                CandidateSourceProofError
            ):
                normalize_candidate_source_proof(proof, side_index=0)


if __name__ == "__main__":
    unittest.main()
