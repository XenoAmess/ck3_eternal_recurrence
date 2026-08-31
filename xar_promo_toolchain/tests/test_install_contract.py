from __future__ import annotations

import argparse
import json
import sys
import tomllib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
SCHEMA_ROOT = SOURCE_ROOT / "xar_promo" / "schemas"
CONTRACT_PATH = SCHEMA_ROOT / "install-contract-v1.json"
EXPECTED_COMMANDS = (
    "init",
    "start-run",
    "validate",
    "preserve",
    "signoff",
    "plan",
    "build",
    "audit",
    "review",
    "export",
)
EXPECTED_RESOURCES = (
    "xar_promo/schemas/install-contract-v1.json",
    "xar_promo/schemas/promo-project-config-v1.schema.json",
    "xar_promo/schemas/promo-run-manifest-v1.schema.json",
)


class InstallContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            cls.pyproject = tomllib.load(handle)

        sys.path.insert(0, str(SOURCE_ROOT))
        try:
            from xar_promo import __version__
            from xar_promo.cli import build_parser

            cls.runtime_version = __version__
            cls.parser = build_parser()
        finally:
            sys.path.pop(0)

    def test_contract_is_versioned_json_with_required_sections(self) -> None:
        self.assertEqual("xar-promo-install-contract-v1", self.contract["schema"])
        self.assertEqual(1, self.contract["schema_version"])
        self.assertTrue(
            {
                "package",
                "compatibility",
                "entry_points",
                "requirements",
                "acquisition",
                "extras",
                "artifacts",
                "verification",
                "side_effect_boundaries",
            }.issubset(self.contract)
        )

    def test_package_metadata_and_entry_points_match_pyproject_and_runtime(self) -> None:
        project = self.pyproject["project"]
        package = self.contract["package"]
        self.assertEqual(project["name"], package["distribution_name"])
        self.assertEqual(project["version"], package["version"])
        self.assertEqual(project["requires-python"], package["python_requires"])
        self.assertEqual(project["license"], package["license"])
        self.assertEqual(self.runtime_version, package["version"])
        self.assertEqual(
            self.pyproject["build-system"]["build-backend"],
            package["build_backend"],
        )
        self.assertEqual(
            self.pyproject["build-system"]["requires"],
            self.contract["requirements"]["build_dependencies"],
        )
        self.assertEqual(
            project["dependencies"],
            self.contract["requirements"]["core_python_dependencies"],
        )
        console = self.contract["entry_points"]["console"]
        self.assertEqual("xar-promo", console["name"])
        self.assertEqual(project["scripts"][console["name"]], console["target"])
        self.assertEqual(
            ["python", "-m", "xar_promo"],
            self.contract["entry_points"]["module"]["argv"],
        )

    def test_optional_extras_match_pyproject_exactly(self) -> None:
        declared = self.pyproject["project"]["optional-dependencies"]
        contracted = {
            name: row["requirements"]
            for name, row in self.contract["extras"].items()
        }
        self.assertEqual(declared, contracted)
        self.assertEqual({"tts", "visual", "render"}, set(contracted))
        external = self.contract["requirements"]["external_executables"]
        self.assertEqual({"ffmpeg", "ffprobe"}, {row["name"] for row in external})
        self.assertTrue(all(row["installed_by_pip"] is False for row in external))

    def test_cross_platform_compatibility_boundary_is_explicit(self) -> None:
        compatibility = self.contract["compatibility"]
        self.assertEqual(["windows", "linux", "macos"], compatibility["supported_os"])
        self.assertEqual("py3-none-any", compatibility["core_wheel_tag"])
        self.assertIs(compatibility["core_architecture_independent"], True)
        constraints = " ".join(compatibility["target_specific_components"])
        self.assertIn("optional dependencies", constraints)
        self.assertIn("ffmpeg", constraints)
        self.assertIn("CPU architecture", constraints)
        installation = (PROJECT_ROOT / "docs" / "installation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Windows, Linux, and macOS", installation)
        self.assertIn("tagged `py3-none-any`", installation)
        self.assertIn("The declared extras are", installation)

    def test_exact_ten_cli_commands_are_exposed_and_verified(self) -> None:
        subparser_action = next(
            action
            for action in self.parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertEqual(set(EXPECTED_COMMANDS), set(subparser_action.choices))
        verification = self.contract["verification"]
        self.assertEqual(list(EXPECTED_COMMANDS), verification["expected_subcommands"])
        help_rows = {
            tuple(row["argv"]): row
            for row in verification["commands"]
            if row["id"].startswith("help-")
        }
        self.assertEqual(
            {("xar-promo", command, "--help") for command in EXPECTED_COMMANDS},
            set(help_rows),
        )
        self.assertTrue(all(row["expected_exit_code"] == 0 for row in help_rows.values()))
        self.assertTrue(all(row["project_writes"] is False for row in help_rows.values()))

    def test_version_schema_and_help_verification_is_read_only_and_offline(self) -> None:
        verification = self.contract["verification"]
        rows = {row["id"]: row for row in verification["commands"]}
        self.assertEqual(len(rows), len(verification["commands"]))
        self.assertEqual(
            {"console-version", "module-version", "installed-schema-resources"},
            {name for name in rows if not name.startswith("help-")},
        )
        self.assertEqual(["xar-promo", "--version"], rows["console-version"]["argv"])
        self.assertEqual(
            ["python", "-m", "xar_promo", "--version"],
            rows["module-version"]["argv"],
        )
        self.assertTrue(all(row["expected_exit_code"] == 0 for row in rows.values()))
        self.assertTrue(all(row["project_writes"] is False for row in rows.values()))
        boundary = self.contract["side_effect_boundaries"]["verification"]
        self.assertIs(boundary["project_writes"], False)
        self.assertIs(boundary["network"], False)
        self.assertIs(boundary["media_processes"], False)

    def test_contract_and_native_schemas_are_wheel_package_data(self) -> None:
        resources = self.contract["artifacts"]["installed_resources"]
        self.assertEqual(list(EXPECTED_RESOURCES), resources)
        for resource in resources:
            package_name, relative_name = resource.split("/", 1)
            self.assertEqual("xar_promo", package_name)
            path = SOURCE_ROOT / package_name / Path(relative_name)
            self.assertTrue(path.is_file(), resource)
            json.loads(path.read_text(encoding="utf-8"))

        package_data = self.pyproject["tool"]["setuptools"]["package-data"]
        self.assertIn("schemas/*.json", package_data["xar_promo"])
        manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("graft src", manifest.splitlines())

    def test_distribution_artifact_names_follow_metadata(self) -> None:
        package = self.contract["package"]
        normalized = package["distribution_name"].replace("-", "_")
        version = package["version"]
        artifacts = self.contract["artifacts"]
        self.assertEqual(
            f"{normalized}-{version}-py3-none-any.whl",
            artifacts["wheel"]["filename"],
        )
        self.assertEqual(
            f"{normalized}-{version}.tar.gz",
            artifacts["sdist"]["filename"],
        )
        self.assertTrue(artifacts["wheel"]["installable"])
        self.assertTrue(artifacts["sdist"]["installable"])
        self.assertTrue((PROJECT_ROOT / "docs" / "installation.md").is_file())

    def test_distribution_source_and_integrity_boundary_is_explicit(self) -> None:
        acquisition = self.contract["acquisition"]
        self.assertIs(acquisition["public_index_published"], False)
        self.assertIn("trusted", acquisition["preferred_install_source"])
        integrity = acquisition["integrity"]
        self.assertEqual("SHA-256", integrity["algorithm"])
        self.assertIn("independently", integrity["expected_digest_provenance"])
        self.assertIs(integrity["expected_digest_must_be_external_to_artifact"], True)
        installation = (PROJECT_ROOT / "docs" / "installation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("not published to PyPI or another public Python index", installation)
        self.assertIn("Get-FileHash -Algorithm SHA256", installation)
        self.assertIn("sha256sum", installation)
        self.assertIn("shasum -a 256", installation)
        self.assertIn("--no-index", installation)
        self.assertIn("Upgrading pip is optional", installation)
        self.assertIn("py -3 -c", installation)


if __name__ == "__main__":
    unittest.main()
