"""No-network checks for the official latest-release transport and existing guards."""
from io import BytesIO
import argparse
import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
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


class Fixture403(Exception):
    """Simulated first-wire rejection; no provider connection is performed."""


class FixtureCommunicate:
    mode: str = 'success'
    constructed: int = 0
    wire_entries: int = 0
    saves: int = 0

    def __init__(self, text: str, voice: str, *, rate: str, volume: str, pitch: str,
                 boundary: str = 'SentenceBoundary') -> None:
        type(self).constructed += 1
        if self.mode == 'construct':
            raise RuntimeError('fixture construction failure')
        if boundary != 'SentenceBoundary':
            raise ValueError('Fixture expects explicit sentence mode')

    async def _Communicate__stream(self) -> AsyncIterator[dict[str, object]]:
        type(self).wire_entries += 1
        yield {'type': 'audio', 'data': b'synthetic fixture bytes, not an actual MP3'}
        if self.mode == 'partial':
            raise RuntimeError('actual fixture partial failure')
        if self.mode != 'empty':
            yield {'type': 'SentenceBoundary', 'offset': 0, 'duration': True if self.mode == 'bool' else 20000000,
                   'text': '改字。' if self.mode == 'text' else '第一句。'}
            yield {'type': 'SentenceBoundary', 'offset': 10000000, 'duration': 20000000, 'text': '第二句。'}
        if self.mode == 'retry':
            raise Fixture403('simulated HTTP403 after first partial stream')

    async def stream(self) -> AsyncIterator[dict[str, object]]:
        try:
            async for event in self._Communicate__stream():
                yield event
        except Fixture403:
            # Exact failure shape of 7.3.1: public stream attempts private wire again.
            async for event in self._Communicate__stream():
                yield event

    def save_sync(self, audio_fname: str, metadata_fname: str | None = None) -> None:
        type(self).saves += 1
        if self.mode == 'missing':
            Path(audio_fname).write_bytes(b'fixture output with no stream metadata')
            return
        async def save_fixture() -> None:
            with open(audio_fname, 'wb') as audio:
                if metadata_fname is None:
                    async for event in self.stream():
                        if event['type'] == 'audio':
                            data = event['data']
                            assert isinstance(data, bytes)
                            audio.write(data)
                else:
                    with open(metadata_fname, 'w', encoding='utf-8') as metadata_stream:
                        async for event in self.stream():
                            if event['type'] == 'audio':
                                data = event['data']
                                assert isinstance(data, bytes)
                                audio.write(data)
                            else:
                                json.dump(event, metadata_stream)
                                metadata_stream.write('\n')
        asyncio.run(save_fixture())


class SameStreamProducerTests(unittest.TestCase):
    def execute(self, root: Path, *, enabled: bool = True, mode: str = 'success',
                mutate: Callable[[dict[str, object], dict[str, object]], None] | None = None,
                decode_failure: bool = False, preexisting: bool = False) -> dict[str, object]:
        from xar_promo.tts.provider import ProviderIdentity, TtsRequest
        from xar_promo.tts.cache import tts_fingerprint
        from xar_promo.project import load_document
        from faith_power_promo.narration_alignment import checked_file_pin
        FixtureCommunicate.mode = mode
        FixtureCommunicate.constructed = FixtureCommunicate.wire_entries = FixtureCommunicate.saves = 0
        output = root / 'attempt'
        output.mkdir()
        if preexisting:
            (output / 'cue01.mp3').write_bytes(b'preexisting must not be overwritten')
        for name in ('fresh-runtime.json', 'storage-admission.json', 'provider-installation.json', 'ffmpeg.exe', 'ffprobe.exe'):
            (root / name).write_text('{}', encoding='utf-8')
        for name in ('fresh-runtime.json', 'storage-admission.json'):
            (output / name).write_text('{}', encoding='utf-8')
        cue = {'id': 'cue01', 'zh': '第一句。第二句。', 'en': 'First. Second.', 'live_result_asserted': False,
               'subtitle_units': [{'id': 'a', 'zh': '第一句。', 'en': 'First. '}, {'id': 'b', 'zh': '第二句。', 'en': 'Second.'}]}
        script: dict[str, object] = {'cues': [cue]}
        identity = ProviderIdentity('edge-tts', '7.3.1')
        defaults = {'voice': 'zh-CN-XiaoxiaoNeural', 'rate': '+0%', 'volume': '+0%', 'pitch': '+0Hz'}
        recipe: dict[str, object] = {'provider_identity_for_frozen_fingerprints': asdict(identity),
            'request_defaults': defaults, 'entries': [{'cue_id': 'cue01',
                'tts_fingerprint': tts_fingerprint(TtsRequest('第一句。第二句。', **defaults), identity)}],
            'sentence_boundary_limits': {'max_audio_bytes': 4096, 'max_metadata_bytes': 4096, 'max_events': 8}}
        if mutate is not None:
            mutate(script, recipe)
        script_path, recipe_path = root / 'script.json', root / 'recipe.json'
        script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')
        recipe_path.write_text(json.dumps(recipe, ensure_ascii=False), encoding='utf-8')
        runtime = {'tts_runtime_receipt': checked_file_pin(root / 'provider-installation.json'),
                   'ffmpeg': checked_file_pin(root / 'ffmpeg.exe'), 'ffprobe': checked_file_pin(root / 'ffprobe.exe'),
                   'boundary_communicate_source': checked_file_pin(Path(__file__))}
        module = ModuleType('edge_tts')
        module.__file__ = __file__
        setattr(module, 'Communicate', FixtureCommunicate)
        args = argparse.Namespace(script=script_path, recipe=recipe_path, peak_bytes=33554432)
        def external_command(argv: object, directory: object, label: str) -> SimpleNamespace:
            if decode_failure and label.endswith('-strict-audio-decode'):
                raise RuntimeError('fixture strict decode exit nonzero')
            return SimpleNamespace(stdout='{"format":{"duration":"2.5"}}', returncode=0)
        original_version = production.metadata.version
        def version(name: str) -> str:
            return '7.3.1' if name == 'edge-tts' else original_version(name)
        # Only external observation/process/provider runtime seams are fixtures.
        # Real official provider, native project, artifact preservation, producer,
        # persisted parser/alignment and shared subtitle consumer all execute.
        with patch.dict(sys.modules, {'edge_tts': module}), patch.object(production.metadata, 'version', side_effect=version):
            with patch.object(production, 'open_attempt', return_value=(runtime, {'machine_id': 'fixture-machine'}, output)):
                with patch.object(production, 'command', side_effect=external_command), patch.object(production, 'admission', return_value={'fixture': True}):
                    summary = production.run_synthesize(args, sentence_boundaries=enabled)
        self.assertEqual(summary['failed'], 0 if mode == 'success' and not decode_failure and not preexisting else 1)
        measured: object = json.loads(Path(summary['measured_narration']['path']).read_text('utf-8'))
        assert isinstance(measured, dict)
        loaded = load_document(output / 'native-run' / 'run-manifest.json', check_files=True)
        assert loaded.run is not None
        identifiers = {artifact.artifact_id for artifact in loaded.run.artifacts}
        self.assertIn('request.cue01', identifiers)
        self.assertIn('narration-measurement-v1', identifiers)
        if enabled:
            self.assertIn('boundaries.cue01', identifiers)
            self.assertIn('boundary-producer-source-v1', identifiers)
            self.assertIn('boundary-runtime-source-v1', identifiers)
            if (output / 'cue01.stream.jsonl').is_file():
                self.assertIn('boundary-stream.cue01', identifiers)
        return measured

    def test_actual_producer_provider_preservation_json_and_subtitle_consumer(self) -> None:
        from faith_power_promo.full_episode import subtitle_groups
        from faith_power_promo.narration_alignment import parse_boundary_record
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            measured = self.execute(root)
            cues = measured['cues']
            assert isinstance(cues, list) and len(cues) == 1
            row = cues[0]
            envelope = parse_boundary_record(json.loads(Path(row['provider_boundaries']['path']).read_text('utf-8')))
            self.assertEqual(envelope['request'], row['request'])
            self.assertEqual(envelope['audio'], row['audio'])
            self.assertEqual(envelope['actual_wire_calls'], 1)
            self.assertNotIn('provider_request', row)
            groups = subtitle_groups(json.loads(json.dumps({'zh': '第一句。第二句。', 'en': 'First. Second.', **row})))
            self.assertEqual([item['end_seconds'] for item in groups], [1.0, 2.5])
            self.assertEqual((FixtureCommunicate.constructed, FixtureCommunicate.saves, FixtureCommunicate.wire_entries), (1, 1, 1))

    def test_default_contract_unchanged_and_no_metadata_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            measured = self.execute(Path(directory), enabled=False)
            cues = measured['cues']
            assert isinstance(cues, list)
            self.assertNotIn('provider_boundaries', cues[0])
            self.assertNotIn('subtitle_groups', cues[0])
            self.assertEqual((FixtureCommunicate.constructed, FixtureCommunicate.saves, FixtureCommunicate.wire_entries), (1, 1, 1))

    def test_real_failure_paths_no_replay_and_partial_preserved(self) -> None:
        for mode in ('retry', 'partial', 'empty', 'bool', 'text'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                measured = self.execute(Path(directory), mode=mode)
                self.assertEqual(measured['cues'], [])
                failures = measured['failures']
                assert isinstance(failures, list) and len(failures) == 1
                self.assertEqual(FixtureCommunicate.constructed, 1)
                self.assertEqual(FixtureCommunicate.wire_entries, 1)
                self.assertIsNotNone(failures[0]['partial_audio'])
                envelope = json.loads(Path(failures[0]['provider_boundaries']['path']).read_text('utf-8'))
                if mode == 'retry':
                    self.assertEqual(envelope['actual_wire_calls'], 2)
                    self.assertIn('replay refused', envelope['stream_error'])
                if mode == 'text':
                    self.assertEqual(envelope['status'], 'complete')  # Stream complete; alignment failed.
                else:
                    self.assertFalse(envelope['stream_complete'])

    def test_strict_decode_failure_is_preserved_without_second_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            measured = self.execute(Path(directory), decode_failure=True)
            self.assertEqual(measured['cues'], [])
            self.assertEqual(FixtureCommunicate.constructed, 1)

    def test_existing_output_and_missing_metadata_constructor_failure_remain_distinct(self) -> None:
        for mode in ('construct', 'missing', 'success'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                measured = self.execute(root, mode=mode, preexisting=mode == 'success')
                self.assertEqual(measured['cues'], [])
                envelope = json.loads((root / 'attempt' / 'cue01.boundaries.json').read_text('utf-8'))
                self.assertEqual(envelope['actual_wire_calls'], 0)
                self.assertIsNone(envelope['raw_metadata'])
                self.assertIsNone(envelope['audio']) if mode == 'construct' else self.assertIsNotNone(envelope['audio'])
                if mode == 'success':
                    self.assertEqual((root / 'attempt' / 'cue01.mp3').read_bytes(), b'preexisting must not be overwritten')

    def test_invalid_units_limits_and_caps_execute_actual_shared_guards(self) -> None:
        def bad_units(script: dict[str, object], recipe: dict[str, object]) -> None:
            script['cues'] = [{'id': 'cue01', 'zh': '第一句。第二句。', 'en': 'First. Second.', 'live_result_asserted': False}]
        def bad_limits(script: dict[str, object], recipe: dict[str, object]) -> None:
            recipe['sentence_boundary_limits'] = {'max_audio_bytes': True, 'max_metadata_bytes': 4096, 'max_events': 8}
        for mutate in (bad_units, bad_limits):
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                self.execute(Path(directory), mutate=mutate)
            self.assertEqual(FixtureCommunicate.constructed, 0)
        def audio_cap(script: dict[str, object], recipe: dict[str, object]) -> None:
            recipe['sentence_boundary_limits'] = {'max_audio_bytes': 1, 'max_metadata_bytes': 4096, 'max_events': 8}
        with tempfile.TemporaryDirectory() as directory:
            measured = self.execute(Path(directory), mode='cap', mutate=audio_cap)
            self.assertEqual(measured['cues'], [])
            self.assertEqual(FixtureCommunicate.wire_entries, 1)
        for key in ('max_metadata_bytes', 'max_events'):
            def metadata_cap(script: dict[str, object], recipe: dict[str, object]) -> None:
                limits = {'max_audio_bytes': 4096, 'max_metadata_bytes': 4096, 'max_events': 8}
                limits[key] = 1
                recipe['sentence_boundary_limits'] = limits
            with self.subTest(cap=key), tempfile.TemporaryDirectory() as directory:
                measured = self.execute(Path(directory), mode='cap', mutate=metadata_cap)
                self.assertEqual(measured['cues'], [])
                self.assertEqual(FixtureCommunicate.wire_entries, 1)

    def test_cli_optin_reaches_the_existing_producer(self) -> None:
        base = ['synthesize', '--repo', 'r', '--script', 's', '--runtime', 'u', '--reservation', 'a',
                '--package-root', 'p', '--output', 'o', '--reservation-task', 'task', '--peak-bytes', '1024', '--recipe', 'v']
        for enabled in (False, True):
            with self.subTest(enabled=enabled), patch.object(production, 'run_synthesize', return_value={'failed': 0}) as producer:
                with patch('builtins.print'):
                    self.assertEqual(production.main(base + (['--sentence-boundaries'] if enabled else [])), 0)
                self.assertIs(producer.call_args.kwargs['sentence_boundaries'], enabled)


if __name__ == "__main__":
    unittest.main()
