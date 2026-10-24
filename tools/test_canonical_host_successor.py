"""Exercise the actual finite common-host producer; never starts CK3."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import sys
from typing import Protocol, runtime_checkable
import unittest

from ck3_live_run_id import current_machine_id
from ck3_mod_acceptance_background_types import JsonObject, file_pin, json_object
from ck3_mod_acceptance_build_runtime import EXTRA_CAPABILITIES, HOST_RELATIVE, build_canonical_host_successor, project_host, registration_driver

REPOSITORY = Path(__file__).resolve().parents[1]


@runtime_checkable
class RegistrationProducer(Protocol):
    def __call__(self, case: JsonObject) -> object: ...


def actual_pin(path: Path) -> JsonObject:
    raw = path.read_bytes()
    return json_object(file_pin({'path': str(path.resolve()), 'bytes': len(raw),
                                 'sha256': hashlib.sha256(raw).hexdigest()}))


class CanonicalHostSuccessorTests(unittest.TestCase):
    def test_actual_members_registration_policy_roundtrip_is_default_off_and_preserves_native_flag(self) -> None:
        sys.path.insert(0, str(REPOSITORY / 'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.driver import GameplayBridgeDriver
        tool = 'ck3_query_player_rite_members_v1'
        self.assertEqual(EXTRA_CAPABILITIES[tool], ['XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1'])
        producer: object = registration_driver
        if not isinstance(producer, RegistrationProducer):
            raise ValueError('Existing shared registration producer must be callable')
        for requested in ([], [tool]):
            case = json_object(json.loads(json.dumps({'opt_in_read_only_mcp_tools': requested})))
            driver = producer(case)
            if not isinstance(driver, GameplayBridgeDriver):
                raise ValueError('Registration facade must expose the existing semantic driver boundary')
            self.assertIs(getattr(driver, 'allow_private_player_rite_members_query'), bool(requested))
            async def names() -> set[str]:
                return {row.name for row in await create_server(driver).list_tools()}
            registered = asyncio.run(names())
            self.assertEqual(tool in registered, bool(requested))
            self.assertNotIn('ck3_execute_player_rite_creation_action_v1', registered)

    def test_actual_global_factory_registers_all_four_rite_tools_and_declared_queries(self) -> None:
        sys.path.insert(0, str(REPOSITORY / 'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.driver import GameplayBridgeDriver
        case = json_object(json.loads((REPOSITORY / 'tools/ck3_mod_acceptance_products.json').read_bytes())['products']['dynastic-esotericism']['cases'][0])
        producer: object = registration_driver
        if not isinstance(producer, RegistrationProducer):
            raise ValueError('Existing shared registration producer must be callable')
        driver = producer(case)
        if not isinstance(driver, GameplayBridgeDriver):
            raise ValueError('Registration facade must expose the existing semantic driver boundary')
        async def names() -> set[str]:
            return {row.name for row in await create_server(driver).list_tools()}
        registered = asyncio.run(names())
        required = case['required_mcp_tools']
        if not isinstance(required, list) or any(not isinstance(name, str) for name in required):
            raise ValueError('Required tool array must contain only registered names')
        self.assertTrue(all(name in registered for name in required))

    def inputs(self, root: Path) -> tuple[Path, Path, Path, str]:
        source = root / 'source'
        canonical = source / HOST_RELATIVE
        canonical.parent.mkdir(parents=True)
        actual = (REPOSITORY / HOST_RELATIVE).read_bytes()
        canonical.write_bytes(actual)
        tree = ast.parse(actual.decode('utf-8-sig'))
        binding = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'bind_normal_exit_managed_profile']
        self.assertEqual(1, len(binding))
        # Authored parent isolates the exact existing normal-exit authority. The
        # complete successor bytes come from the actual canonical host above.
        parent_host = root / 'parent-host.py'
        parent_host.write_text(ast.unparse(binding[0]) + '\n', encoding='utf-8')
        machine = current_machine_id()
        self.assertIsInstance(machine, str)
        if not isinstance(machine, str):
            raise ValueError('Actual stable machine identity unavailable')
        pin = actual_pin(parent_host)
        manifest = root / 'parent-manifest.json'
        manifest.write_text(json.dumps({'schema': 'ck3-mod-acceptance-shared-runtime-v1',
            'machine_id': machine, 'host': {'path_key': 'host', 'bytes': pin['bytes'], 'sha256': pin['sha256']}}), encoding='utf-8')
        runtime = root / 'parent-runtime.json'
        runtime.write_text(json.dumps({'schema': 'ck3-mod-acceptance-runtime-v1', 'machine_id': machine,
            'manifest': actual_pin(manifest), 'paths': {'host': str(parent_host)}}), encoding='utf-8')
        return source, runtime, parent_host, machine

    def test_actual_producer_pins_parent_canonical_and_exact_output_then_refuses_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, runtime, _, machine = self.inputs(root)
            output = root / 'successor'
            ref = build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', output, machine)
            payload = json_object(json.loads(Path(ref['path']).read_bytes()))
            self.assertEqual(payload['parent_runtime'], actual_pin(runtime))
            self.assertEqual(payload['canonical_host'], actual_pin(source / HOST_RELATIVE))
            self.assertEqual(payload['projected_host'], actual_pin(output / 'shared-host.py'))
            self.assertEqual((source / HOST_RELATIVE).read_bytes().removeprefix(b'\xef\xbb\xbf'),
                             (output / 'shared-host.py').read_bytes().removeprefix(b'\xef\xbb\xbf'))
            self.assertIs(payload['actual_live_qualified'], False)
            self.assertIs(payload['game_started'], False)
            with self.assertRaises(ValueError):
                build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', output, machine)

    def test_source_metadata_float_and_bool_never_compare_equal_to_actual_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, runtime, parent, _ = self.inputs(root)
            canonical = actual_pin(source / HOST_RELATIVE)
            for count in (True, float((source / HOST_RELATIVE).stat().st_size)):
                with self.subTest(count=count), self.assertRaises(ValueError):
                    project_host(source, parent, runtime, root / 'selected-runtime.json',
                        {HOST_RELATIVE: {'bytes': count, 'sha256': canonical['sha256']}})

    def test_existing_global_registration_projection_survives_canonical_host_successor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, runtime, parent, machine = self.inputs(root)
            parent.write_text(parent.read_text(encoding='utf-8') + '\n'
                'def native_server(args):\n'
                '    clean_imports(args.agent_source_root)\n'
                '    from registration_bootstrap import bind_registration\n'
                '    bind_registration()\n'
                '    from progress_driver import ProgressDailyDriver\n'
                '    from registration_mcp import create_server\n', encoding='utf-8')
            manifest_path = root / 'parent-manifest.json'
            manifest = json_object(json.loads(manifest_path.read_bytes()))
            parent_pin = actual_pin(parent)
            manifest['host'] = {'path_key': 'host', 'bytes': parent_pin['bytes'], 'sha256': parent_pin['sha256']}
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            parent_runtime = json_object(json.loads(runtime.read_bytes()))
            parent_runtime['manifest'] = actual_pin(manifest_path)
            registration = root / 'parent-registration/registration_mcp.py'
            registration.parent.mkdir()
            registration.write_text('def create_server(driver, *, service_override=None):\n'
                '    module = load_module(pin(source), "authored_original_factory")\n'
                '    return module.create_server(driver, service_override=service_override)\n', encoding='utf-8')
            parent_runtime['runtime_environment'] = {'PYTHONPATH': [str(registration.parent)]}
            parent_runtime['allocator_overlay'] = {'registration': actual_pin(registration)}
            factory = source / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
            factory.parent.mkdir(parents=True)
            factory.write_bytes((REPOSITORY / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py').read_bytes())
            runtime.write_text(json.dumps(parent_runtime), encoding='utf-8')
            output = root / 'successor'
            build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', output, machine)
            actual = (output / 'shared-host.py').read_text(encoding='utf-8-sig')
            self.assertIn('selected_r05_registration_factory_v1', actual)
            self.assertIn('class RecordingDriver(ProgressDailyDriver)', actual)
            canonical_server = next(node for node in ast.parse((source / HOST_RELATIVE).read_text(encoding='utf-8-sig')).body
                if isinstance(node, ast.FunctionDef) and node.name == 'native_server')
            projected_server = next(node for node in ast.parse(actual).body
                if isinstance(node, ast.FunctionDef) and node.name == 'native_server')
            canonical_driver = next(node for node in canonical_server.body if isinstance(node, ast.ClassDef) and node.name == 'RecordingDriver')
            projected_driver = next(node for node in projected_server.body if isinstance(node, ast.ClassDef) and node.name == 'RecordingDriver')
            self.assertEqual([ast.dump(node, include_attributes=False) for node in canonical_driver.body],
                             [ast.dump(node, include_attributes=False) for node in projected_driver.body])
            projected_registration = (output / 'registration_mcp.py').read_text(encoding='utf-8-sig')
            self.assertIn('from xar_autoplayer.bridge import mcp_server as module', projected_registration)
            self.assertIn('service_override=service_override', projected_registration)
            canonical_functions = {node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse((source / HOST_RELATIVE).read_text(encoding='utf-8-sig')).body
                if isinstance(node, ast.FunctionDef) and node.name != 'native_server'}
            projected_functions = {node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(actual).body if isinstance(node, ast.FunctionDef) and node.name != 'native_server'}
            self.assertEqual(canonical_functions, projected_functions)

    def test_changed_parent_pin_wrong_machine_and_changed_binding_reach_real_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, runtime, host, machine = self.inputs(root)
            with self.assertRaises(ValueError):
                build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', root / 'wrong-machine', 'wrong-machine')
            host.write_text(host.read_text(encoding='utf-8') + '\n# mutation\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', root / 'changed-parent', machine)
            self.assertFalse((root / 'changed-parent').exists())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, runtime, _, machine = self.inputs(root)
            canonical = source / HOST_RELATIVE
            text = canonical.read_text(encoding='utf-8-sig')
            text = text.replace('def bind_normal_exit_managed_profile(driver, args)',
                                'def bind_normal_exit_managed_profile(driver, changed_args)', 1)
            canonical.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', root / 'changed-authority', machine)
            self.assertFalse((root / 'changed-authority').exists())


if __name__ == '__main__':
    unittest.main()
