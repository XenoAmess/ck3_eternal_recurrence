#!/usr/bin/env python3
"""Offline unit tests for the reusable MiniMax localization caller."""

from __future__ import annotations

import codecs
from contextlib import redirect_stderr, redirect_stdout
import http.client
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate_localization_minimax as minimax  # noqa: E402


class ParseLocalizationTests(unittest.TestCase):
    @staticmethod
    def write_fixture(root: Path, payload: str, *, bom: bool = True) -> Path:
        path = root / "fixture_l_english.yml"
        data = payload.encode("utf-8")
        path.write_bytes((codecs.BOM_UTF8 if bom else b"") + data)
        return path

    def test_bom_localization_is_parsed_without_unescaping_values(self):
        payload = (
            "l_english:\n"
            ' first_key:0 "Hello [CHARACTER.GetShortUIName|U]\\nWorld"\n'
            ' second_key:17 "Keep \\\"quoted\\\" text"\n'
            "  # indented comments and blank lines are allowed\n"
            "\n"
        )
        with tempfile.TemporaryDirectory(prefix="minimax-loc-test-") as name:
            path = self.write_fixture(Path(name), payload)
            self.assertEqual(
                {
                    "first_key": "Hello [CHARACTER.GetShortUIName|U]\\nWorld",
                    "second_key": 'Keep \\\"quoted\\\" text',
                },
                minimax.parse_ck3_localization(path),
            )

    def test_missing_bom_and_invalid_utf8_are_rejected_safely(self):
        with tempfile.TemporaryDirectory(prefix="minimax-loc-test-") as name:
            root = Path(name)
            path = self.write_fixture(root, 'l_english:\n key:0 "Value"\n', bom=False)
            with self.assertRaisesRegex(minimax.TranslationError, "lacks UTF-8 BOM"):
                minimax.parse_ck3_localization(path)

            path.write_bytes(codecs.BOM_UTF8 + b"l_english:\n key:0 \"\xff\"\n")
            with self.assertRaisesRegex(minimax.TranslationError, "not valid UTF-8"):
                minimax.parse_ck3_localization(path)

    def test_missing_misordered_and_repeated_headers_are_rejected(self):
        cases = (
            (' key:0 "Value"\n', "entry precedes header"),
            ('# comments only\n', "header missing"),
            (
                'l_english:\nl_french:\n key:0 "Value"\n',
                "multiple localization headers",
            ),
        )
        with tempfile.TemporaryDirectory(prefix="minimax-loc-test-") as name:
            root = Path(name)
            for index, (payload, message) in enumerate(cases):
                path = root / f"fixture_{index}.yml"
                path.write_bytes(codecs.BOM_UTF8 + payload.encode("utf-8"))
                with self.subTest(payload=payload), self.assertRaisesRegex(
                    minimax.TranslationError, message
                ):
                    minimax.parse_ck3_localization(path)

    def test_malformed_nonempty_lines_are_rejected(self):
        malformed_lines = (
            "unexpected text",
            ' key:0 "unterminated',
            ' key:0 "unescaped "quote""',
            '  key:0 "two leading spaces"',
            'key:0 "missing leading space"',
            ' key with spaces:0 "whitespace in key"',
            ' key\twith_tab:0 "tab in key"',
            ' key :0 "trailing whitespace in key"',
            ' key "missing colon and version"',
        )
        with tempfile.TemporaryDirectory(prefix="minimax-loc-test-") as name:
            root = Path(name)
            for index, line in enumerate(malformed_lines):
                path = root / f"malformed_{index}.yml"
                path.write_bytes(
                    codecs.BOM_UTF8 + f"l_english:\n{line}\n".encode("utf-8")
                )
                with self.subTest(line=line), self.assertRaisesRegex(
                    minimax.TranslationError, "malformed localization line"
                ):
                    minimax.parse_ck3_localization(path)

    def test_duplicate_keys_and_empty_entry_set_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="minimax-loc-test-") as name:
            root = Path(name)
            duplicate = root / "duplicate.yml"
            duplicate.write_bytes(
                codecs.BOM_UTF8
                + b'l_english:\n duplicate:0 "One"\n duplicate:0 "Two"\n'
            )
            with self.assertRaisesRegex(minimax.TranslationError, "duplicate localization key"):
                minimax.parse_ck3_localization(duplicate)

            empty = root / "empty.yml"
            empty.write_bytes(codecs.BOM_UTF8 + b"l_english:\n# no entries\n")
            with self.assertRaisesRegex(minimax.TranslationError, "no CK3 localization entries"):
                minimax.parse_ck3_localization(empty)


class CandidateExtractionTests(unittest.TestCase):
    KEYS = ("first", "second")

    def test_single_exact_candidate_is_returned_in_source_key_order(self):
        candidate = minimax.extract_candidate(
            '{"second":"Deux","first":"Un"}', self.KEYS
        )
        self.assertEqual(["first", "second"], list(candidate))
        self.assertEqual({"first": "Un", "second": "Deux"}, candidate)

    def test_prose_markdown_and_repeated_json_are_rejected(self):
        invalid = (
            'Here is the result: {"first":"Uno","second":"Dos"}',
            '```json\n{"first":"Uno","second":"Dos"}\n```',
            '{"first":"Uno","second":"Dos"}\n'
            '{"first":"Uno","second":"Dos"}',
            '{"first":"Uno","second":"Dos"}\ntrailing text',
        )
        for content in invalid:
            with self.subTest(content=content), self.assertRaisesRegex(
                minimax.TranslationError, "not one strict JSON object"
            ):
                minimax.extract_candidate(content, self.KEYS)

    def test_duplicate_json_keys_are_rejected_even_when_values_match(self):
        for content in (
            '{"first":"Uno","first":"Uno","second":"Dos"}',
            '{"first":"Uno","second":"Dos","second":"Dos"}',
        ):
            with self.subTest(content=content), self.assertRaisesRegex(
                minimax.TranslationError, "response JSON contains duplicate key"
            ):
                minimax.extract_candidate(content, self.KEYS)

    def test_wrong_key_set_non_string_values_and_non_objects_are_rejected(self):
        cases = (
            ('{"first":"Uno"}', "response key set differs"),
            (
                '{"first":"Uno","second":"Dos","extra":"Tres"}',
                "response key set differs",
            ),
            ('{"first":"Uno","second":2}', "non-string translation value"),
            ('["Uno", "Dos"]', "response JSON is not an object"),
            ("not JSON", "not one strict JSON object"),
            ("   ", "response content is empty or not text"),
        )
        for content, message in cases:
            with self.subTest(content=content), self.assertRaisesRegex(
                minimax.TranslationError, message
            ):
                minimax.extract_candidate(content, self.KEYS)

        with self.assertRaisesRegex(
            minimax.TranslationError, "response content is empty or not text"
        ):
            minimax.extract_candidate(None, self.KEYS)  # type: ignore[arg-type]


class ProtectedTokenTests(unittest.TestCase):
    SOURCE = {
        "event": (
            "Visit https://example.test/docs?q=1 <b>{name}</b> ${count} {{state}} "
            "[CHARACTER.GetShortUIName|U] $trait_impotent$ @warning_icon! "
            "#P good#! §Rred§! %1$s\\n\\\"quoted\\\""
        ),
        "brand": "Ox Here meets Ox Here",
    }

    def test_broad_ck3_and_generic_placeholder_multiset_is_accepted(self):
        candidate = {
            "event": (
                "#P bon#! §Rrouge§! %1$s @warning_icon! $trait_impotent$ "
                "[CHARACTER.GetShortUIName|U] {{state}} ${count} <b>{name}</b> "
                "https://example.test/docs?q=1\\n\\\"citation\\\""
            ),
            "brand": "Ox Here rencontre Ox Here",
        }
        minimax.assert_protected_tokens(self.SOURCE, candidate, ("Ox Here",))

    def test_any_automatic_placeholder_drift_is_rejected(self):
        baseline = {
            "event": self.SOURCE["event"],
            "brand": "Ox Here rencontre Ox Here",
        }
        replacements = (
            ("https://example.test/docs?q=1", "https://other.test/"),
            ("<b>", "<strong>"),
            ("{name}", "{nom}"),
            ("${count}", "${nombre}"),
            ("{{state}}", "{{etat}}"),
            ("[CHARACTER.GetShortUIName|U]", "[CHARACTER.GetName]"),
            ("$trait_impotent$", "$trait_lustful$"),
            ("@warning_icon!", "@gold_icon!"),
            ("#P", "#N"),
            ("§R", "§G"),
            ("%1$s", "%2$s"),
            ("\\n", " "),
            ('\\"', "'"),
        )
        for old, new in replacements:
            candidate = dict(baseline)
            candidate["event"] = candidate["event"].replace(old, new, 1)
            with self.subTest(old=old), self.assertRaisesRegex(
                minimax.TranslationError, "protected-token mismatch"
            ):
                minimax.assert_protected_tokens(self.SOURCE, candidate, ("Ox Here",))

    def test_explicit_protected_token_count_is_enforced(self):
        candidate = {"event": self.SOURCE["event"], "brand": "Ox Here arrives"}
        with self.assertRaisesRegex(minimax.TranslationError, "explicit token 'Ox Here'"):
            minimax.assert_protected_tokens(self.SOURCE, candidate, ("Ox Here",))

    def test_balanced_icu_plural_and_select_blocks_are_verbatim_tokens(self):
        plural = "{count, plural, =0 {none} one {one ox} other {{count} oxen}}"
        select = "{gender, select, male {He arrived} female {She arrived} other {They arrived}}"
        source = {"icu": f"Result: {plural}; {select}"}
        self.assertEqual((plural, select), minimax.find_icu_blocks(source["icu"]))
        minimax.assert_protected_tokens(source, dict(source))

        candidate = {
            "icu": source["icu"].replace("one {one ox}", "one {un bœuf}")
        }
        with self.assertRaisesRegex(minimax.TranslationError, "protected-token mismatch"):
            minimax.assert_protected_tokens(source, candidate)


class TargetParsingTests(unittest.TestCase):
    def test_valid_target_is_normalized(self):
        self.assertEqual(
            ("simp_chinese2", "Simplified Chinese"),
            minimax.parse_target("simp_chinese2=  Simplified Chinese  "),
        )

    def test_malformed_targets_are_rejected(self):
        for value in (
            "french",
            "=French",
            "French=French",
            "fr-FR=French",
            "french=   ",
            " french=French",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                minimax.argparse.ArgumentTypeError, "target must be key=Display Name"
            ):
                minimax.parse_target(value)


class RequestContractTests(unittest.TestCase):
    def test_request_uses_official_m3_body_and_validates_envelope(self):
        source = {"line": "Ox Here [CHARACTER.GetName]"}
        translated = {"line": "Ox Here [CHARACTER.GetName] est arrivé"}
        envelope = {
            "base_resp": {"status_code": 0},
            "input_sensitive": False,
            "output_sensitive": False,
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps(translated, ensure_ascii=False)},
                }
            ],
        }
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(envelope, ensure_ascii=False).encode("utf-8")

        with mock.patch.object(minimax.request, "urlopen", return_value=response) as urlopen:
            result = minimax.request_candidate(
                "french",
                "French",
                "minimal prompt",
                source,
                "test-only-api-key",
                4321,
                ("Ox Here",),
            )

        self.assertEqual(("french", translated), result)
        urlopen.assert_called_once()
        req = urlopen.call_args.args[0]
        self.assertEqual(180, urlopen.call_args.kwargs["timeout"])
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual("MiniMax-M3", body["model"])
        self.assertEqual(4321, body["max_completion_tokens"])
        self.assertEqual({"type": "disabled"}, body["thinking"])
        self.assertNotIn("max_tokens", body)
        self.assertNotIn("response_format", body)
        self.assertEqual(
            {"model", "max_completion_tokens", "temperature", "thinking", "messages"},
            set(body),
        )

    def test_transport_read_failures_retry_then_raise_controlled_error(self):
        failures = (
            (http.client.IncompleteRead(b"partial", 20), "IncompleteRead"),
            (OSError("fixture transport failure"), "OSError"),
        )
        for exception, diagnostic in failures:
            with (
                self.subTest(exception=type(exception).__name__),
                mock.patch.object(
                    minimax.request, "urlopen", side_effect=exception
                ) as urlopen,
                mock.patch.object(minimax.time, "sleep") as sleep,
                self.assertRaises(minimax.TranslationError) as raised,
            ):
                minimax.request_candidate(
                    "french",
                    "French",
                    "minimal prompt",
                    {"line": "Source"},
                    "test-only-api-key",
                    4321,
                )
            self.assertIn(diagnostic, str(raised.exception))
            self.assertEqual(2, urlopen.call_count)
            sleep.assert_called_once_with(2)

    def test_translation_validation_diagnostic_survives_bounded_retries(self):
        envelope = {
            "base_resp": {"status_code": 0},
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": '{"wrong":"translation"}'},
                }
            ],
        }
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(envelope).encode("utf-8")
        with (
            mock.patch.object(minimax.request, "urlopen", return_value=response) as urlopen,
            mock.patch.object(minimax.time, "sleep") as sleep,
            self.assertRaises(minimax.TranslationError) as raised,
        ):
            minimax.request_candidate(
                "french",
                "French",
                "minimal prompt",
                {"line": "Source"},
                "test-only-api-key",
                4321,
            )
        message = str(raised.exception)
        self.assertIn("response key set differs", message)
        self.assertIn("missing=['line']", message)
        self.assertIn("extra=['wrong']", message)
        self.assertEqual(2, urlopen.call_count)
        sleep.assert_called_once_with(2)

    def test_main_keeps_successful_target_json_when_another_target_fails(self):
        with tempfile.TemporaryDirectory(prefix="minimax-main-test-") as name:
            source_path = Path(name) / "source_l_english.yml"
            source_path.write_bytes(
                codecs.BOM_UTF8
                + b'l_english:\n brand:0 "Ox Here"\n ignored:0 "Not selected"\n'
            )
            calls: list[tuple[object, ...]] = []

            def fake_request(*args):
                calls.append(args)
                target_key = args[0]
                if target_key == "german":
                    raise minimax.TranslationError("fixture failure")
                return target_key, {"brand": "Ox Here FR"}

            stdout = io.StringIO()
            stderr = io.StringIO()
            argv = [
                "--source",
                str(source_path),
                "--source-language",
                "English",
                "--target",
                "french=French",
                "--target",
                "german=German",
                "--context",
                "fixture",
                "--key",
                "brand",
                "--protect",
                "Ox Here",
                "--workers",
                "1",
            ]
            with (
                mock.patch.dict(os.environ, {minimax.API_KEY_ENV: "configured-for-test"}),
                mock.patch.object(minimax, "request_candidate", side_effect=fake_request),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                status = minimax.main(argv)

        self.assertEqual(1, status)
        self.assertEqual({"french": {"brand": "Ox Here FR"}}, json.loads(stdout.getvalue()))
        self.assertIn("MINIMAX TARGET FAILED [german]", stderr.getvalue())
        self.assertEqual(2, len(calls))
        for call in calls:
            self.assertEqual({"brand": "Ox Here"}, call[3])
            self.assertEqual(("Ox Here",), call[6])
            self.assertIn('"brand"', call[2])
            self.assertNotIn('"ignored"', call[2])


if __name__ == "__main__":
    unittest.main()
