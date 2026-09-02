from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_raiktor_war_bound_private_capture_v1.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "raiktor_war_bound_private_capture_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("war_bound_capture_runner", RUNNER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RaiktorWarBoundCaptureRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner_source = RUNNER.read_text(encoding="utf-8")

    def test_manifest_persists_distinct_300_second_readiness(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        attempt = manifest["attempt_contract"]
        readiness = manifest["readiness_contract"]
        self.assertTrue(attempt["fresh_attempt_required"])
        self.assertFalse(attempt["reuse_previous_attempt"])
        self.assertEqual(readiness["main_menu_timeout_seconds"], 300)
        self.assertEqual(
            readiness["main_menu_stage_capture_seconds"],
            [60, 120, 180, 240, 300],
        )
        self.assertEqual(readiness["capture_process_timeout_ms"], 1200000)
        self.assertEqual(readiness["private_attach_timeout_seconds"], 30)
        self.assertEqual(manifest["capture_product"]["timeout_max_ms"], 1200000)
        self.assertEqual(
            manifest["capture_product"]["executable_sha256"],
            MODULE.EXPECTED_CAPTURE_EXE_SHA256,
        )
        self.assertIn("MainMenuReadinessTimeout", readiness["typed_terminals"])
        self.assertIn("AttachTargetIdentityMismatch", readiness["typed_terminals"])
        self.assertIn("PrivateAttachReadinessTimeout", readiness["typed_terminals"])
        self.assertIn("LegalConsentNotAuthorized", readiness["typed_terminals"])
        self.assertIn("LegalConsentMarkerNotPersisted", readiness["typed_terminals"])
        self.assertIn("starts one CK3 normally", manifest["live_command"])
        legal = manifest["legal_consent_contract"]
        self.assertTrue(legal["allow_exact_semantic_modal_acceptance"])
        self.assertFalse(legal["accepted_marker_present"])
        self.assertEqual(
            legal["source_profile_relative_path"],
            "account/PDX/SDK/ck3/account.json",
        )
        self.assertIn("telemetry", legal["explicitly_not_authorized"])

    def test_readiness_cli_must_match_manifest(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        args = SimpleNamespace(
            main_menu_timeout_seconds=300,
            ui_timeout_seconds=520,
            capture_timeout_ms=1200000,
        )
        observed = MODULE.validate_readiness_contract(manifest, args)
        self.assertEqual(observed["main_menu_timeout_seconds"], 300)
        args.main_menu_timeout_seconds = 299
        with self.assertRaisesRegex(RuntimeError, "does not match manifest"):
            MODULE.validate_readiness_contract(manifest, args)

    def test_fresh_attempt_rejects_prior_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            attempt = Path(temporary) / "attempt"
            MODULE.require_fresh_attempt_directory(attempt)
            attempt.mkdir()
            MODULE.require_fresh_attempt_directory(attempt)
            (attempt / "prior-report.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.TypedTerminalError, "artifact directory is not absent or empty"
            ):
                MODULE.require_fresh_attempt_directory(attempt)

    def test_empty_capture_is_a_typed_report_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "capture.json"
            path.write_bytes(b"")
            capture, error = MODULE.load_capture_artifact(path)
        self.assertIsNone(capture)
        self.assertEqual(error, "capture artifact is empty")

    def test_valid_capture_object_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "capture.json"
            path.write_text('{"result":"RED"}\n', encoding="utf-8")
            capture, error = MODULE.load_capture_artifact(path)
        self.assertEqual(capture, {"result": "RED"})
        self.assertIsNone(error)

    def test_attach_ready_requires_exact_pid_build_and_breakpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "attach-ready.json"
            path.write_text(json.dumps({
                "schema": "raiktor-war-bound-private-attach-ready-v1",
                "attach_mode": True,
                "pid": 4242,
                "exe_sha256": MODULE.EXPECTED_CK3_SHA256,
                "image_base": "0x140000000",
                "observation_stop_rva": "0x2E7F951",
                "breakpoint_installed": True,
            }), encoding="utf-8")
            ready = MODULE.load_attach_ready(path, 4242)
            self.assertEqual(ready["pid"], 4242)
            self.assertIn("sha256", ready)
            with self.assertRaises(MODULE.TypedTerminalError) as caught:
                MODULE.load_attach_ready(path, 4243)
        self.assertEqual(caught.exception.terminal, "PrivateAttachReadinessInvalid")

    def test_runner_waits_for_main_menu_before_private_attach(self) -> None:
        normal_start = self.runner_source.index("ck3_process = subprocess.Popen")
        main_menu = self.runner_source.index("wait_for_main_menu_readiness(", normal_start)
        attach = self.runner_source.index("capture_process = subprocess.Popen", main_menu)
        lobby = self.runner_source.index(
            "navigate_lobby_with_authorized_legal(", attach
        )
        self.assertLess(normal_start, main_menu)
        self.assertLess(main_menu, attach)
        self.assertLess(attach, lobby)
        self.assertNotIn('"-debug_mode"', self.runner_source)
        self.assertIn("validate_running_ck3(ck3_pid, args.ck3_exe)", self.runner_source)

    def test_legal_modal_allowlist_accepts_agreements_and_captures_version(self) -> None:
        agreement = MODULE.classify_authorized_legal_modal([
            "Paradox Interactive - User Agreement",
            "Last update January 21, 2026",
            "好的",
        ])
        self.assertIsNotNone(agreement)
        assert agreement is not None
        self.assertEqual(
            agreement["title"], "Paradox Interactive - User Agreement"
        )
        self.assertEqual(
            agreement["version"], "Last update January 21, 2026"
        )
        self.assertIsNotNone(MODULE.classify_authorized_legal_modal([
            "Paradox Interactive 最终用户许可协议", "版本 4.0", "我同意"
        ]))
        self.assertIsNotNone(MODULE.classify_authorized_legal_modal([
            "Paradox Interactive Terms of Use", "Effective 2026-08-01", "Accept"
        ]))

    def test_legal_modal_denylist_prevents_optional_consent_click(self) -> None:
        with self.assertRaises(MODULE.TypedTerminalError) as privacy:
            MODULE.classify_authorized_legal_modal([
                "Paradox Interactive Privacy Policy", "Accept"
            ])
        self.assertEqual(privacy.exception.terminal, "LegalConsentNotAuthorized")
        with self.assertRaises(MODULE.TypedTerminalError) as caught:
            MODULE.classify_authorized_legal_modal([
                "Paradox Interactive User Agreement",
                "I also agree to personalized advertising and data sharing",
                "Accept",
            ])
        self.assertEqual(caught.exception.terminal, "LegalConsentNotAuthorized")

    def test_legal_modal_requires_version_before_any_click(self) -> None:
        class ForbiddenAcceptance:
            FULL_SCREEN_REGION = (0, 0, 1, 1)

            @staticmethod
            def find_ocr_text(*_args, **_kwargs):
                raise AssertionError("missing version must stop before button lookup")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "userdir"
            ui_dir = root / "ui"
            userdir.mkdir()
            with self.assertRaises(MODULE.TypedTerminalError) as raised:
                MODULE.accept_authorized_legal_modal(
                    ForbiddenAcceptance(),
                    object(),
                    userdir,
                    ui_dir,
                    object(),
                    ["Paradox Interactive User Agreement", "Accept"],
                    1,
                    [],
                )
        self.assertEqual(raised.exception.terminal, "LegalConsentVersionMissing")

    def test_shared_classifier_preserves_chinese_policy_terms(self) -> None:
        allowed = MODULE.classify_authorized_legal_modal(
            ["Paradox Interactive 最终用户许可协议", "版本 4.0", "我同意"]
        )
        self.assertIsNotNone(allowed)
        with self.assertRaises(MODULE.TypedTerminalError) as denied:
            MODULE.classify_authorized_legal_modal(
                ["Paradox Interactive 遥测与数据共享政策", "接受"]
            )
        self.assertEqual(denied.exception.terminal, "LegalConsentNotAuthorized")

    def test_new_accepted_marker_must_be_allowlisted(self) -> None:
        before = {
            "markers": ["eula-2016-11-08", "Terms-of-use-2019-04-05"]
        }
        after = {
            "markers": [
                "eula-2016-11-08",
                "Terms-of-use-2019-04-05",
                "user-agreement-2026-01-21",
            ]
        }
        new_markers = MODULE.newly_persisted_legal_markers(before, after)
        self.assertEqual(new_markers, ["user-agreement-2026-01-21"])
        self.assertTrue(MODULE._authorized_legal_marker(new_markers[0]))
        self.assertFalse(MODULE._authorized_legal_marker("privacy-policy-2026-01-21"))

    def test_authorized_handler_clicks_once_and_records_isolated_marker(self) -> None:
        class FakeImage:
            def __init__(self, payload: bytes) -> None:
                self.payload = payload

            def save(self, path: Path) -> None:
                path.write_bytes(self.payload)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "userdir"
            ui_dir = root / "ui"
            account = userdir / MODULE.LEGAL_CONSENT_PROFILE_SUFFIX
            account.parent.mkdir(parents=True)
            ui_dir.mkdir()
            account.write_text(json.dumps({
                "viewedLegalDocuments": {
                    "online": ["Terms-of-use-2019-04-05"],
                    "localOnly": ["eula-2016-11-08"],
                }
            }), encoding="utf-8")

            class FakeAcceptance:
                FULL_SCREEN_REGION = (0, 0, 1, 1)

                def __init__(self) -> None:
                    self.clicks = 0

                def find_ocr_text(self, _image, label, _region, contains=False):
                    del contains
                    return (50, 50) if label == "好的" else None

                def deliberate_click(self, _point, _label) -> None:
                    self.clicks += 1
                    account.write_text(json.dumps({
                        "viewedLegalDocuments": {
                            "online": [
                                "Terms-of-use-2019-04-05",
                                "user-agreement-2026-01-21",
                            ],
                            "localOnly": ["eula-2016-11-08"],
                        }
                    }), encoding="utf-8")

                def focus_ck3(self) -> None:
                    return None

                def ocr_results(self, _image, _region):
                    return [("公爵罗贝尔", 0, (0, 0), 0)]

            class FakeGrab:
                @staticmethod
                def grab():
                    return FakeImage(b"after")

            acceptance = FakeAcceptance()
            stages: list[dict[str, object]] = []
            evidence = MODULE.accept_authorized_legal_modal(
                acceptance,
                FakeGrab,
                userdir,
                ui_dir,
                FakeImage(b"before"),
                [
                    "Paradox Interactive - User Agreement",
                    "Last update January 21, 2026",
                    "好的",
                ],
                1,
                stages,
            )
        self.assertEqual(acceptance.clicks, 1)
        self.assertEqual(evidence["button_label"], "好的")
        self.assertEqual(
            evidence["new_accepted_markers"],
            ["user-agreement-2026-01-21"],
        )
        self.assertNotEqual(
            evidence["marker_sha256_before"], evidence["marker_sha256_after"]
        )
        self.assertEqual(
            [stage["stage"] for stage in stages],
            ["legal_consent_before", "legal_consent_after"],
        )


if __name__ == "__main__":
    unittest.main()
