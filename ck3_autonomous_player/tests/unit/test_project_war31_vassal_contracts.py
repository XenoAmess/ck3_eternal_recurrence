"""Bounded save-level checks for WAR31 direct contract relation evidence."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from project_war31_vassal_contracts import project_holder_contracts  # noqa: E402


def fixture(*, holder_list: str = "9000", liege_id: int = 29829) -> str:
    return (
        "living={\n"
        "\t29829={\n\t\tlanded_data={\n\t\t\tvassal_contracts={\n"
        "\t\t\t\t8383\n\t\t\t}\n\t\t}\n\t}\n"
        "\t33435={\n\t\tlanded_data={\n\t\t\tvassal_contracts={\n"
        f"\t\t\t\t{holder_list}\n\t\t\t}}\n\t\t}}\n\t}}\n"
        "}\n"
        "vassal_contracts={\n\tdatabase={\n"
        "\t\t8383={\n\t\t\tvassal=33435\n"
        f"\t\t\tliege={liege_id}\n\t\t}}\n"
        "\t\t9000={\n\t\t\tvassal=43703\n\t\t\tliege=33435\n\t\t}\n"
        "\t}\n}\n"
    )


class War31ContractProjectionTests(unittest.TestCase):
    def project(self, value: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_bytes(value.encode("ascii"))
            return project_holder_contracts(path, 33435)

    def test_requires_both_contract_database_and_liege_living_list(self) -> None:
        result = self.project(fixture())
        self.assertEqual(result["personal_liege"]["character_id"], 29829)
        self.assertEqual(result["personal_liege"]["contract_id"], 8383)
        self.assertEqual(
            [(row["contract_id"], row["vassal_character_id"])
             for row in result["direct_contract_vassals"]],
            [(9000, 43703)],
        )

    def test_rejects_reference_without_matching_database_edge(self) -> None:
        with self.assertRaisesRegex(ValueError, "differs from database"):
            self.project(fixture(holder_list="9001"))

    def test_rejects_unverified_liege_list(self) -> None:
        with self.assertRaisesRegex(ValueError, "requested living lord"):
            self.project(fixture(liege_id=29097))

    def test_missing_holder_list_cannot_be_mistaken_for_no_vassals(self) -> None:
        missing = fixture().replace(
            "\t33435={\n\t\tlanded_data={\n\t\t\tvassal_contracts={\n"
            "\t\t\t\t9000\n\t\t\t}\n\t\t}\n\t}\n",
            "\t33435={\n\t\tlanded_data={\n\t\t}\n\t}\n",
        )
        with self.assertRaisesRegex(ValueError, "requested living lord"):
            self.project(missing)


if __name__ == "__main__":
    unittest.main()
