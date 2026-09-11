from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inspect_ck3_save_player_topology as topology


MELTED = """SAV0100
meta_data={
\tversion="1.19.0.6"
\tmeta_player_tier=3
\tmeta_main_portrait={
\t\tid=20
\t}
\tmeta_number_of_players=1
}
\t\t100={
\t\t\tkey="d_manager"
\t\t\tholder=20
\t\t}
\t\t101={
\t\t\tkey="k_owner"
\t\t\tholder=10
\t\t}
\t20={
\t\tfirst_name="Manager"
\t\talive_data={ }
\t\tlanded_data={
\t\t\tgovernment="celestial_government"
\t\t}
\t}
\t10={
\t\tfirst_name="Owner"
\t\talive_data={ }
\t\tlanded_data={
\t\t\tgovernment="celestial_government"
\t\t}
\t}
\t\t200={
\t\t\tvassal=20
\t\t\tliege=10
\t\t\tcontract_group="celestial_vassal"
\t\t}
played_character={
\tcharacter=20
\tplayer=1
}
currently_played_characters={
\t20
}
"""


class SaveTopologyTests(unittest.TestCase):
    def test_single_player_manager_topology(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(MELTED, encoding="utf-8")
            report = topology.inspect_melted(path)

        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["offline_single_player_ready"])
        self.assertEqual(report["celestial_manager_candidate_count"], 1)
        self.assertEqual(
            report["player_manager_candidates"],
            [
                {
                    "contract_id": 200,
                    "player_manager_character_id": 20,
                    "immediate_liege_character_id": 10,
                    "player_primary_title_tier": 3,
                    "player_primary_title_key": "d_manager",
                    "player_government": "celestial_government",
                    "liege_primary_title_tier": 4,
                    "liege_primary_title_key": "k_owner",
                    "liege_government": "celestial_government",
                    "direct_landed_vassal_count": 0,
                }
            ],
        )

    def test_multiplayer_shape_is_not_single_player_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(
                MELTED.replace("meta_number_of_players=1", "meta_number_of_players=5")
                + "played_character={\n\tcharacter=30\n\tplayer=2\n}\n",
                encoding="utf-8",
            )
            report = topology.inspect_melted(path)

        self.assertFalse(report["offline_single_player_ready"])
        self.assertEqual(len(report["played_character_records"]), 2)


if __name__ == "__main__":
    unittest.main()
