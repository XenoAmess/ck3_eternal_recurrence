"""Configure the actual reader recipe without invoking a native compiler."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest


NATIVE = Path(__file__).resolve().parents[1] / "native_bridge"
RECIPE = NATIVE / "cmake/religion_shared_readers_12004.cmake"
# Literal functions from the failed sparse LYD link, not speculative providers.
FAILED_FUNCTION_OWNERS = {
    "ReadActorReformAIContext12002": "religion_reform12002_ai_context.cpp",
    "ReadReformScheduleInputs12002": "religion_reform12002_schedule.cpp",
    "ReadPlayedRiteGovernance12002": "religion_rite_governance12002_context.cpp",
    "ReadPlayedOrganizationMembers12002": "religion_rite_governance12002_organization_members.cpp",
    "ReadPlayedReligionContext12002": "ck3_12002_religion_context.cpp",
    "ReadPlayedTenetKnowledgeCatalogue12003": "ck3_12003_player_tenet_knowledge_catalogue.cpp",
    "ReadPlayedTenetRows12002": "religion_doctrine12002_tenet_rows.cpp",
    "ReadPlayedTargetRiteTenetComparison12003": "ck3_12003_target_rite_tenet_comparison.cpp",
    "ReadPlayedDoctrineKnowledge12002": "religion_doctrine12002_choices.cpp",
    "ReadPlayedDoctrineKnowledgeByKey12002": "religion_doctrine12002_choices.cpp",
    "ReadPlayedCurrentDoctrines12002": "religion_doctrine12002_query.cpp",
    "ReadPlayedReformQuery12002": "religion_reform12002_query_runtime.cpp",
    "ReadCurrentDraftTenetSources12002": "religion_reform12002_tenet_sources.cpp",
    "ReadCurrentDraftFullDoctrineChoices12002": "religion_reform12002_fullchoices.cpp",
    "ReadCurrentDraftGroupModel12002": "religion_reform12002_group_model.cpp",
}
TRANSITIVE_READERS = {
    "ReadPlayedRiteModel12002": "religion_reform12002_rite.cpp",
    "ReadFaithMainRiteUnreformed12002": "religion_reform12002_willingness.cpp",
    "ReadCurrentRiteCreationWindow12002": "religion_reform12002_window.cpp",
    "ReadCurrentRiteCreationCosts12002": "religion_reform12002_costs.cpp",
    "ReadCurrentDraftEligibility12002": "religion_reform12002_eligibility.cpp",
    "ReadCurrentDraftChoices12002": "religion_reform12002_choices.cpp",
    "ObserveCurrentDraftDoctrineSelection12002": "religion_doctrine12002_selection.cpp",
    "ReadCurrentDraftCreationTerms12003": "religion_reform12003_creation_terms.cpp",
    "ReadPlayedStateRite12002": "religion_rite_governance12002_state_rite.cpp",
    "ReadPlayedRiteHeads12002": "religion_rite_governance12002_head.cpp",
    "ReadPlayedOrganizationCounts12002": "religion_rite_governance12002_organization.cpp",
    "CopyDoctrineDefinition12002": "religion_doctrine12002_intrinsic.cpp",
    "ReadPlayedTenetParameters12002": "religion_doctrine12002_tenet.cpp",
    "ReadPlayedRiteDoctrines12002": "religion_doctrine12002_rite.cpp",
    "BindFaithMainRiteUnreformedImage12002": "religion_reform12002_willingness.cpp",
}


class ReligionReaderCmakeTests(unittest.TestCase):
    def configure_sources(self, existing):
        cmake = os.environ.get("XAR_TEST_CMAKE") or shutil.which("cmake")
        if cmake is None:
            self.fail("CMake is required for this source contract test")
        recipe = RECIPE.read_text(encoding="utf-8-sig")
        readers = re.findall(r"^  ([\w]+\.cpp)\)?$", recipe, re.MULTILINE)
        with tempfile.TemporaryDirectory(prefix="lyd-religion-cmake-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            for name in ["placeholder.cpp", *readers]:
                (root / "src" / name).write_text("", encoding="utf-8")
            # LANGUAGES NONE and inert rule declarations permit generation of
            # target SOURCES without compiler discovery or any build command.
            initial = []
            for index, name in enumerate(existing):
                initial.append((root / "src" / name).as_posix()
                               if index % 2 else "src/" + name)
            quoted = "\n".join('  "' + value + '"' for value in initial)
            (root / "CMakeLists.txt").write_text(
                "cmake_minimum_required(VERSION 3.20)\n"
                "project(ReaderClosure NONE)\n"
                'set(CMAKE_CXX_COMPILE_OBJECT "cmake -E true")\n'
                'set(CMAKE_CXX_ARCHIVE_CREATE "cmake -E true")\n'
                'set(CMAKE_CXX_ARCHIVE_FINISH "cmake -E true")\n'
                "add_library(xar_ck3_12002_runtime STATIC src/placeholder.cpp\n"
                + quoted + ")\n"
                "set_target_properties(xar_ck3_12002_runtime PROPERTIES LINKER_LANGUAGE CXX)\n"
                + 'include("' + RECIPE.as_posix() + '")\n'
                + 'include("' + RECIPE.as_posix() + '")\n'
                + "get_target_property(actual xar_ck3_12002_runtime SOURCES)\n"
                + 'file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/sources.txt" "${actual}")\n',
                encoding="utf-8",
            )
            command = [cmake, "-S", str(root), "-B", str(root / "configure"), "-G", "Ninja"]
            if os.environ.get("XAR_TEST_NINJA"):
                command.append("-DCMAKE_MAKE_PROGRAM=" + os.environ["XAR_TEST_NINJA"])
            result = subprocess.run(
                command,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            values = (root / "configure/sources.txt").read_text(encoding="utf-8").split(";")
            return [Path(value).name for value in values], readers

    def test_sparse_lyd_link_has_failed_and_transitive_software_owners(self):
        actual, _ = self.configure_sources([])
        for function, owner in (FAILED_FUNCTION_OWNERS | TRANSITIVE_READERS).items():
            with self.subTest(function=function):
                self.assertIn(owner, actual)
                body = (NATIVE / "src" / owner).read_text(encoding="utf-8-sig")
                self.assertRegex(body, r"\b" + function + r"\s*\(")
        self.assertFalse(any("mailbox" in source for source in actual))

    def test_existing_absolute_and_relative_sources_are_not_added_twice(self):
        recipe = RECIPE.read_text(encoding="utf-8-sig")
        readers = re.findall(r"^  ([\w]+\.cpp)\)?$", recipe, re.MULTILINE)
        actual, _ = self.configure_sources(readers)
        for owner in readers:
            self.assertEqual(actual.count(owner), 1, owner)


if __name__ == "__main__":
    unittest.main()
