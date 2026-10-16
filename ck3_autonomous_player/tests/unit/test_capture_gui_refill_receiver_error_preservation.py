"""A failed MCP call must retain the original text when structured data is absent."""
import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def test_mcp_error_content_survives_capture(tmp_path, monkeypatch):
    marker = 'SYNTHETIC_ORIGINAL_MCP_ERROR_CONTENT_635'
    calls = []

    class FakeDriver:
        def __init__(self, **_kwargs):
            calls.append('driver_created')

        def close(self):
            calls.append('driver_closed')

    class FakeResponse:
        structured_content = None
        is_error = True
        content = [{'type': 'text', 'text': marker}]

    class FakeClient:
        def __init__(self, _server):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def call_tool(self, name, arguments):
            calls.append((name, arguments))
            return FakeResponse()

    def fake_module(name, **members):
        module = types.ModuleType(name)
        module.__dict__.update(members)
        monkeypatch.setitem(sys.modules, name, module)

    fake_module('tools', __path__=[])
    fake_module('tools.ck3_live_run_id', current_machine_id=lambda: 'test-machine')
    fake_module('mcp', Client=FakeClient)
    fake_module('xar_autoplayer', __path__=[])
    fake_module('xar_autoplayer.bridge', __path__=[])
    fake_module('xar_autoplayer.bridge.native_driver', NativeHeadlessGameplayDriver=FakeDriver)
    fake_module('xar_autoplayer.bridge.mcp_server', create_server=lambda _driver: object())

    path = Path(__file__).resolve().parents[2] / 'tools/capture_gui_refill_receiver_candidates_12004.py'
    spec = importlib.util.spec_from_file_location('receiver_capture_error_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / 'failed-response.json'
    args = types.SimpleNamespace(
        repo_root=tmp_path, expected_machine_id='test-machine', pipe_name='fake',
        state_dir=tmp_path / 'state', output=output, expected_game_pid=1,
        expected_connection_generation=1, expected_native_revision=1,
        expected_played_full_id=1, expected_date_raw=1,
    )
    with pytest.raises(ValueError, match='original response retained'):
        asyncio.run(module.capture(args))
    saved = json.loads(output.read_text(encoding='utf-8'))
    assert saved['body'] is None
    assert saved['response_is_error'] is True
    assert saved['error_envelope']['content'][0]['text'] == marker
    assert calls[-1] == 'driver_closed'
