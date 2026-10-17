"""Exercise the actual candidate launch preflight without importing desktop code."""
from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

CANDIDATE = Path(__file__).resolve().parents[2] / 'src/xar_autoplayer/runtime.py'

class AgentError(RuntimeError):
    pass

class ReachedExistingVerification(RuntimeError):
    pass

def load_actual_launch_preflight():
    source = CANDIDATE.read_text(encoding='utf-8')
    parsed = ast.parse(source, filename=str(CANDIDATE))
    names = {'NativeBridgeLaunchConfig', '_require_runtime_dependency_profile_bridge', 'launch'}
    selected = [node for node in parsed.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
    if len(selected) != len(names):
        raise AssertionError('Candidate launch and guard definitions not found')
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *selected], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {'Mapping':Mapping, 'Path':Path, 'dataclass':dataclass, 'AgentError':AgentError,
        'json':json, 'math':__import__('math'), 'time':__import__('time')}
    exec(compile(module, str(CANDIDATE), 'exec'), namespace)
    return namespace

class RuntimeNativeOnlyLaunchGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manifest_path = Path(self.temp.name) / 'environment.json'
        self.spec = SimpleNamespace(manifest_path=self.manifest_path)
        self.ns = load_actual_launch_preflight()
        self.verify = Mock(side_effect=ReachedExistingVerification)
        self.ns['verify_profile'] = self.verify
        self.ns['validate_native_bridge_launch_config'] = lambda config: config
        self.ns['native_bridge_launch_config_from_environment'] = lambda: None

    def write_manifest(self, profile):
        runtime = {} if profile is None else {'runtime_dependency_profile':profile}
        self.manifest_path.write_text(json.dumps({'agent_runtime':runtime}),encoding='utf-8')

    def config(self, mode):
        return self.ns['NativeBridgeLaunchConfig'](mode, r'\\.\pipe\unit', Path('bridge.dll'), Path('injector.exe'))

    def test_native_only_rejects_absent_actual_bridge_before_verification(self):
        self.write_manifest('native-only')
        with self.assertRaisesRegex(AgentError, 'actual native-headless bridge'):
            self.ns['launch'](self.spec)
        self.verify.assert_not_called()

    def test_environment_string_cannot_override_actual_hybrid_config(self):
        self.write_manifest('native-only')
        with patch.dict(os.environ, {'XAR_CK3_BRIDGE_MODE':'native-headless'}):
            with self.assertRaisesRegex(AgentError, 'actual native-headless bridge'):
                self.ns['launch'](self.spec, native_bridge=self.config('hybrid-fallback'))
        self.verify.assert_not_called()

    def test_native_only_actual_native_config_reaches_existing_verifier(self):
        self.write_manifest('native-only')
        with patch.dict(os.environ, {'XAR_CK3_BRIDGE_MODE':'disabled'}):
            with self.assertRaises(ReachedExistingVerification):
                self.ns['launch'](self.spec, native_bridge=self.config('native-headless'))
        self.verify.assert_called_once_with(self.spec, xar_enabled='xar_on')

    def test_full_profile_retains_existing_verification_without_bridge(self):
        self.write_manifest('full')
        with self.assertRaises(ReachedExistingVerification):
            self.ns['launch'](self.spec)
        self.verify.assert_called_once_with(self.spec, xar_enabled='xar_on')

    def test_legacy_manifest_retains_existing_verification_without_bridge(self):
        self.write_manifest(None)
        with self.assertRaises(ReachedExistingVerification):
            self.ns['launch'](self.spec)
        self.verify.assert_called_once_with(self.spec, xar_enabled='xar_on')

    def test_fixture_skip_does_not_allow_native_only_hybrid_launch(self):
        self.write_manifest('native-only')
        with self.assertRaisesRegex(AgentError, 'actual native-headless bridge'):
            self.ns['launch'](self.spec, native_bridge=self.config('hybrid-fallback'), verify_prepared_profile=False)
        self.verify.assert_not_called()

if __name__ == '__main__':
    unittest.main()
