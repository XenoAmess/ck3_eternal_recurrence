"""Offline scoped parsing checks for the WAR31 save material reader."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from project_war31_save_material import project_melted  # noqa: E402


def save_text(*, holder: int = 33435, piety: str = "-1.25",
              title_key: str = "c_foggia", repeat_title: bool = False) -> str:
    title = f"\t\t2128={{\n\t\t\tkey=\"{title_key}\"\n\t\t\tde_facto_liege=2141\n\t\t\tholder={holder}\n\t\t}}\n"
    return (
        "SAV0100\nmeta_data={\n\tversion=\"1.19.0.6\"\n\tmeta_date=1068.3.4\n}\n"
        "date=1068.3.4\nlanded_titles={\n\tlanded_titles={\n"
        + title + (title if repeat_title else "")
        + "\t\t2141={\n\t\t\tkey=\"d_apulia\"\n\t\t\tholder=29829\n\t\t}\n"
        + "\t\t2129={\n\t\t\tkey=\"b_lucera\"\n\t\t\tde_facto_liege=2128\n\t\t\tholder=33435\n\t\t}\n"
        + "\t}\n}\nliving={\n"
        + "\t29829={\n\t\tfirst_name=\"Robert\"\n\t\talive_data={\n"
          "\t\t\tgold={\n\t\t\t\tvalue=10.12345\n\t\t\t}\n"
          f"\t\t\tpiety={{\n\t\t\t\tcurrency={piety}\n\t\t\t}}\n"
          "\t\t\tprestige={\n\t\t\t\tcurrency=0\n\t\t\t}\n\t\t}\n\t}\n"
        + "\t30097={\n\t\tfirst_name=\"Landolf\"\n\t\talive_data={\n"
          "\t\t\tgold={\n\t\t\t\tvalue=20\n\t\t\t}\n"
          "\t\t\tpiety={\n\t\t\t\tcurrency=30\n\t\t\t}\n"
          "\t\t\tprestige={\n\t\t\t\tcurrency=40\n\t\t\t}\n\t\t}\n\t}\n}\n"
    )


class War31SaveMaterialTests(unittest.TestCase):
    def parse(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_bytes(text.encode("utf-8"))
            return project_melted(path)

    def test_scopes_title_and_signed_resources_without_inventing_truce(self) -> None:
        value = self.parse(save_text())
        self.assertEqual(value["target_title"]["holder_character_id"], 33435)
        self.assertEqual(value["target_title"]["de_facto_liege_title_holder_character_id"], 29829)
        self.assertEqual(value["target_title"]["direct_de_facto_child_titles"][0]["title_id"], 2129)
        self.assertEqual(value["characters"]["29829"]["resources"]["gold"]["raw"], 1_012_345)
        self.assertEqual(value["characters"]["29829"]["resources"]["piety"]["raw"], -125_000)
        self.assertEqual(value["characters"]["29829"]["resources"]["prestige"]["raw"], 0)
        self.assertEqual(value["holder_personal_vassals"]["status"], "unavailable")
        self.assertEqual(value["persisted_truce"]["status"], "unavailable")

    def test_rejects_duplicate_target_title(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate title ID"):
            self.parse(save_text(repeat_title=True))

    def test_rejects_overprecise_currency(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a save decimal"):
            self.parse(save_text(piety="1.234567"))

    def test_rejects_missing_target_holder(self) -> None:
        with self.assertRaisesRegex(ValueError, "target title holder absent"):
            self.parse(save_text().replace("\t\t\tholder=33435\n", "", 1))

    def test_rejects_wrong_game_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "version differs"):
            self.parse(save_text().replace("1.19.0.6", "1.19.0.7"))


if __name__ == "__main__":
    unittest.main()
