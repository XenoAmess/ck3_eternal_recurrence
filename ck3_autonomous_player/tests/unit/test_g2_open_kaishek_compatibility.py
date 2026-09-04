from __future__ import annotations

import copy
import json
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "native_bridge/research/verify_g2_open_kaishek_compatibility.py"
SPEC = importlib.util.spec_from_file_location("g2_open_kaishek_compatibility", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import setup failure
    raise ImportError(f"cannot load compatibility verifier: {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

FIXTURE_PATH = MODULE.FIXTURE_PATH
audit = MODULE.audit
parse_capability_source = MODULE.parse_capability_source
parse_actual_truce_expiry_source = MODULE.parse_actual_truce_expiry_source
parse_postwar_cleanup_expiry_adapter_source = (
    MODULE.parse_postwar_cleanup_expiry_adapter_source
)
parse_ck3_profile_source = MODULE.parse_ck3_profile_source
parse_projects_metrics_source = MODULE.parse_projects_metrics_source
parse_promotion_source_transport = MODULE.parse_promotion_source_transport
parse_war_bound_loss_source = MODULE.parse_war_bound_loss_source


def _configured_checkout() -> Path:
    return Path(
        os.environ.get("XAR_OPEN_KAISHEK_ROOT")
        or os.environ.get("OPEN_KAISHEK_ROOT")
        or r"Z:\workspace\open_kaishek"
    )


class G2OpenKaishekCompatibilityTests(unittest.TestCase):
    def test_root_and_frozen_fixture_are_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = audit(checkout=Path(directory) / "missing")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["status"], "GREEN_STATIC_NO_CHECKOUT")
        self.assertTrue(
            report["checks"]["fixture_root_profile_matches_open_kaishek"]
        )
        self.assertTrue(
            report["checks"]["fixture_root_capability_matches_open_kaishek"]
        )
        self.assertFalse(report["external"]["available"])
        self.assertEqual(report["readiness"]["stage"], "production-live primitive")
        self.assertTrue(report["readiness"]["native_certified"])
        self.assertTrue(report["readiness"]["runtime_certified"])
        self.assertTrue(report["readiness"]["production_live"])

    def test_fixture_identity_sections_cannot_drift(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for section, key in (
            ("root_binding", "profile_id"),
            ("root_binding", "capability_id"),
            ("open_kaishek", "profile_id"),
            ("open_kaishek", "capability_id"),
        ):
            with self.subTest(section=section, key=key):
                mutated = copy.deepcopy(fixture)
                mutated[section][key] = "drifted-g2-identity"
                with tempfile.TemporaryDirectory() as directory:
                    fixture_path = Path(directory) / "fixture.json"
                    fixture_path.write_text(
                        json.dumps(mutated, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with mock.patch.object(MODULE, "FIXTURE_PATH", fixture_path):
                        report = audit(
                            checkout=Path(directory) / "missing"
                        )
                self.assertFalse(report["ok"], report)
                self.assertEqual(report["status"], "RED")
                if section == "root_binding":
                    self.assertFalse(
                        report["checks"][
                            f"root_{key.removesuffix('_id')}_matches_fixture"
                        ]
                    )
                else:
                    self.assertFalse(
                        report["checks"][
                            f"fixture_root_{key.removesuffix('_id')}_matches_open_kaishek"
                        ]
                    )

    def test_available_checkout_matches_when_present(self) -> None:
        checkout = _configured_checkout()
        if not checkout.is_dir():
            self.skipTest("the external open_kaishek checkout is not available")
        report = audit(checkout=checkout, require_checkout=True, require_clean=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["status"], "GREEN_STATIC")
        self.assertTrue(report["checks"]["checkout_head_matches_fixture"])
        self.assertTrue(report["checks"]["checkout_origin_main_matches_fixture"])
        self.assertTrue(report["checks"]["checkout_clean"])

    def test_missing_required_checkout_is_explicitly_red(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            report = audit(checkout=missing, require_checkout=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "RED")
        self.assertFalse(report["checks"]["checkout_available"])

    def test_java_source_extractors_preserve_contract_shape(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        checkout = _configured_checkout()
        if not checkout.is_dir():
            self.skipTest("the external open_kaishek checkout is not available")
        open_data = fixture["open_kaishek"]
        capability = parse_capability_source(
            checkout / open_data["capability_source"]
        )
        build = parse_ck3_profile_source(checkout / open_data["ck3_profile_source"])
        war_loss_expected = fixture["war_bound_loss_candidate"]
        war_loss = parse_war_bound_loss_source(
            checkout / war_loss_expected["source"]
        )
        projects_expected = fixture["projects_metrics_delta"]
        projects = parse_projects_metrics_source(
            checkout / projects_expected["source"]
        )
        promotion_expected = fixture["promotion_source_transport"]
        promotion = parse_promotion_source_transport(
            checkout / promotion_expected["source"]
        )
        expiry_expected = fixture["actual_truce_expiry_candidate"]
        expiry = parse_actual_truce_expiry_source(
            checkout / expiry_expected["source"]
        )
        cleanup_expected = fixture["postwar_cleanup_expiry_adapter"]
        cleanup = parse_postwar_cleanup_expiry_adapter_source(
            checkout / cleanup_expected["source"]
        )
        for key in (
            "profile_id",
            "capability_id",
            "required_fields",
            "invariants",
            "read_only",
            "deterministic",
            "native_certified",
            "runtime_certified",
        ):
            self.assertEqual(capability[key], open_data[key])
        self.assertEqual(
            capability["provider_transition"], fixture["provider_transition"]
        )
        self.assertEqual(build["game_version"], open_data["game_version"])
        self.assertEqual(build["exe_sha256"], open_data["exe_sha256"])
        self.assertEqual(
            war_loss,
            {
                key: value
                for key, value in war_loss_expected.items()
                if key != "source"
            },
        )
        self.assertEqual(
            projects,
            {
                key: value
                for key, value in projects_expected.items()
                if key != "source"
            },
        )
        self.assertEqual(
            promotion,
            {
                key: value
                for key, value in promotion_expected.items()
                if key != "source"
            },
        )
        self.assertEqual(
            expiry,
            {
                key: value
                for key, value in expiry_expected.items()
                if key != "source"
            },
        )
        self.assertEqual(
            cleanup,
            {
                key: value
                for key, value in cleanup_expected.items()
                if key != "source"
            },
        )


if __name__ == "__main__":
    unittest.main()
