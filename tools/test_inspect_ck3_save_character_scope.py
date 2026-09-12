from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inspect_ck3_save_character_scope as scope


MELTED = """SAV0100
meta_data={
\tversion="1.19.0.6"
}
\t20={
\t\tfirst_name="Manager"
\t\talive_data={
\t\t\tvariables={
\t\t\t\tdata={
\t\t\t\t\t{
\t\t\t\t\t\tflag="manager_cycle"
\t\t\t\t\t\tdata={
\t\t\t\t\t\t\ttype=value
\t\t\t\t\t\t\tidentity=1700000
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tlists={
\t\t\t\t\t{
\t\t\t\t\t\tname="subjects"
\t\t\t\t\t\titem={
\t\t\t\t\t\t\ttype=char
\t\t\t\t\t\t\tidentity=30
\t\t\t\t\t\t}
\t\t\t\t\t\titem={
\t\t\t\t\t\t\ttype=char
\t\t\t\t\t\t\tidentity=40
\t\t\t\t\t\t}
\t\t\t\t\t\tduration={
\t\t\t\t\t\t\t2
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\t30={
\t\tfirst_name="Current"
\t\talive_data={
\t\t\tvariables={
\t\t\t\tdata={
\t\t\t\t\t{
\t\t\t\t\t\tflag="case_owner"
\t\t\t\t\t\tdata={
\t\t\t\t\t\t\ttype=char
\t\t\t\t\t\t\tidentity=20
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\t40={
\t\tfirst_name="Foreign"
\t\tdead_data={
\t\t\tvariables={
\t\t\t\tdata={
\t\t\t\t\t{
\t\t\t\t\t\tflag="case_owner"
\t\t\t\t\t\tdata={
\t\t\t\t\t\t\ttype=char
\t\t\t\t\t\t\tidentity=99
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t}
"""


class CharacterScopeTests(unittest.TestCase):
    def test_selected_variables_and_followed_character_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(MELTED, encoding="utf-8")
            report = scope.inspect_melted(
                path,
                root_character_id=20,
                root_variables=["manager_cycle", "missing"],
                list_names=["subjects"],
                referenced_variables=["case_owner", "case_active"],
            )

        self.assertEqual(report["kind"], scope.KIND)
        self.assertEqual(report["game_version"], "1.19.0.6")
        self.assertEqual(report["root"]["variables"]["manager_cycle"]["number"], 17)
        self.assertFalse(report["root"]["variables"]["missing"]["present"])
        self.assertEqual(report["root"]["lists"]["subjects"]["item_count"], 2)
        self.assertEqual(report["unique_referenced_character_count"], 2)
        rows = {row["character_id"]: row for row in report["referenced_characters"]}
        self.assertTrue(rows[30]["alive"])
        self.assertEqual(rows[30]["variables"]["case_owner"]["character_id"], 20)
        self.assertFalse(rows[30]["variables"]["case_active"]["present"])
        self.assertFalse(rows[40]["alive"])
        self.assertEqual(rows[40]["variables"]["case_owner"]["character_id"], 99)

    def test_discovers_all_roots_with_requested_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(MELTED, encoding="utf-8")
            report = scope.inspect_discovery_melted(
                path,
                discovery_variable="manager_cycle",
                root_variables=["missing"],
                list_names=["subjects"],
                referenced_variables=["case_owner"],
            )

        self.assertEqual(report["kind"], scope.DISCOVERY_KIND)
        self.assertEqual(report["root_character_count"], 1)
        self.assertEqual(report["roots"][0]["root_character_id"], 20)
        self.assertEqual(
            report["roots"][0]["variables"]["manager_cycle"]["number"], 17
        )
        self.assertEqual(report["unique_referenced_character_count"], 2)


if __name__ == "__main__":
    unittest.main()
