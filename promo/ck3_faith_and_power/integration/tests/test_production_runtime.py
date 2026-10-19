"""No-network checks for the official latest-release transport and existing guards."""
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from faith_power_promo import production


class ProductionRuntimeTests(unittest.TestCase):
    def error(self, code, body=b'{"message":"Forbidden"}', remaining=None):
        headers = {} if remaining is None else {"X-RateLimit-Remaining": remaining}
        return HTTPError(production.LATEST, code, "test error", headers, BytesIO(body))

    def test_http_success_keeps_anonymous_transport(self):
        response = BytesIO(b'{"tag_name":"v1"}')
        response.status = 200
        with patch.object(production.urllib.request, "urlopen", return_value=response) as fetch:
            with patch.object(production, "command") as command:
                release, transport = production._official_latest_release("unused", "unit-machine")
        self.assertEqual(release, {"tag_name": "v1"})
        self.assertEqual(transport, {"method": "urllib", "anonymous_http_status": 200})
        self.assertEqual(fetch.call_args.args[0].full_url, production.LATEST)
        command.assert_not_called()

    def test_only_explicit_rate_limits_use_audited_same_endpoint(self):
        cases = [(403, b'{}', "0"),
                 (403, b'{"message":"API rate limit exceeded for test"}', None),
                 (403, b'{"message":"You have exceeded a secondary rate limit."}', None),
                 (429, b'{"message":"Too Many Requests"}', None)]
        for code, body, remaining in cases:
            with self.subTest(code=code, body=body), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                with patch.object(production.urllib.request, "urlopen", side_effect=self.error(code, body, remaining)):
                    with patch.object(production, "command", return_value=SimpleNamespace(returncode=0, stdout='{"tag_name":"v1"}')) as command:
                        release, transport = production._official_latest_release(root, "unit-machine")
                self.assertEqual(release["tag_name"], "v1")
                self.assertEqual(transport["method"], "gh-api")
                self.assertEqual(transport["anonymous_http_status"], code)
                self.assertEqual(command.call_args.args, (["gh", "api", "--hostname", "github.com", "--method", "GET",
                    "--header", "Accept:application/vnd.github+json", "repos/XenoAmess/xar_promo_toolchain/releases/latest"], root, "official-latest-gh-api"))
                diagnostic = json.loads((root / "official-latest-anonymous-rate-limit.json").read_text("utf-8"))
                self.assertEqual(diagnostic["http_status"], code)
                self.assertEqual(diagnostic["machine_id"], "unit-machine")
                self.assertEqual(diagnostic["body"], body.decode())

    def test_non_rate_http_errors_preserve_original_failure(self):
        for code, remaining in ((403, None), (403, "1"), (401, "0"), (404, "0"), (500, "0")):
            with self.subTest(code=code, remaining=remaining):
                error = self.error(code, remaining=remaining)
                with patch.object(production.urllib.request, "urlopen", side_effect=error):
                    with patch.object(production, "command") as command:
                        with self.assertRaises(HTTPError) as caught:
                            production._official_latest_release("unused", "unit-machine")
                self.assertIs(caught.exception, error)
                command.assert_not_called()

    def test_http_json_error_does_not_fallback(self):
        response = BytesIO(b'not JSON')
        response.status = 200
        with patch.object(production.urllib.request, "urlopen", return_value=response):
            with patch.object(production, "command") as command:
                with self.assertRaises(json.JSONDecodeError):
                    production._official_latest_release("unused", "unit-machine")
        command.assert_not_called()

    def test_gh_nonzero_remains_failure_and_keeps_original_http(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            error = self.error(429)
            with patch.object(production.urllib.request, "urlopen", side_effect=error):
                with patch.object(production, "command", return_value=SimpleNamespace(returncode=1, stdout="")):
                    with self.assertRaises(RuntimeError) as caught:
                        production._official_latest_release(root, "unit-machine")
            self.assertIs(caught.exception.__cause__, error)
            self.assertTrue((root / "official-latest-anonymous-rate-limit.json").is_file())

    def test_gh_bad_json_or_nonobject_remains_failure(self):
        for output, exception in (("invalid", json.JSONDecodeError), ("[]", ValueError)):
            with self.subTest(output=output), tempfile.TemporaryDirectory() as name:
                with patch.object(production.urllib.request, "urlopen", side_effect=self.error(429)):
                    with patch.object(production, "command", return_value=SimpleNamespace(returncode=0, stdout=output)):
                        with self.assertRaises(exception):
                            production._official_latest_release(name, "unit-machine")

    def test_fresh_runtime_keeps_installed_release_guards(self):
        wheel = {"name": "tool.whl", "browser_download_url": "https://example.invalid/tool.whl", "digest": "sha256:" + "a" * 64}
        base = {"tag_name": "v1", "draft": False, "prerelease": False, "assets": [wheel]}
        direct = {"url": wheel["browser_download_url"], "archive_info": {"hashes": {"sha256": "a" * 64}}}
        cases = [({**base, "tag_name": "v2"}, direct),
                 ({**base, "assets": [wheel, wheel]}, direct),
                 (base, {**direct, "url": "https://example.invalid/other.whl"}),
                 (base, {**direct, "archive_info": {"hashes": {"sha256": "b" * 64}}})]
        for release, installed in cases:
            with self.subTest(release=release, installed=installed):
                dist = SimpleNamespace(version="1", read_text=lambda _: json.dumps(installed))
                with patch.object(production.subprocess, "check_output", return_value="unit-machine"):
                    with patch.object(production, "_official_latest_release", return_value=(release, {"method": "gh-api", "anonymous_http_status": 403})):
                        with patch.object(production.metadata, "distribution", return_value=dist):
                            with patch.object(production, "command") as command:
                                with self.assertRaises(ValueError):
                                    production.fresh_runtime("unused", {"machine_id": "unit-machine"}, "unused")
                command.assert_not_called()

    def test_fresh_runtime_records_transport_with_original_status(self):
        wheel = {"name": "tool.whl", "browser_download_url": "https://example.invalid/tool.whl", "digest": "sha256:" + "a" * 64}
        release = {"tag_name": "v1", "draft": False, "prerelease": False, "assets": [wheel], "published_at": "unit-time"}
        direct = {"url": wheel["browser_download_url"], "archive_info": {"hashes": {"sha256": "a" * 64}}}
        dist = SimpleNamespace(version="1", read_text=lambda _: json.dumps(direct))
        transport = {"method": "gh-api", "anonymous_http_status": 403}
        with tempfile.TemporaryDirectory() as name:
            with patch.object(production.subprocess, "check_output", return_value="unit-machine"):
                with patch.object(production, "_official_latest_release", return_value=(release, transport)):
                    with patch.object(production.metadata, "distribution", return_value=dist):
                        with patch.object(production, "command", return_value=SimpleNamespace(returncode=0, stdout="unit-version")):
                            with patch.object(production, "bound", side_effect=lambda value: Path(value["path"])):
                                with patch.object(production, "pin", side_effect=lambda path: {"path": str(path)}):
                                    record = production.fresh_runtime("unused", {"machine_id": "unit-machine", "ffmpeg": {"path": "ffmpeg"}, "ffprobe": {"path": "ffprobe"}}, name)
            self.assertEqual(record["release"]["transport"], transport)
            self.assertEqual(json.loads((Path(name) / "fresh-runtime.json").read_text("utf-8"))["release"]["transport"], transport)


if __name__ == "__main__":
    unittest.main()
