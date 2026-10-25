"""Exercise the actual finite common-host producer; never starts CK3."""
from __future__ import annotations

import ast
import asyncio
from collections.abc import Callable
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
from typing import TYPE_CHECKING, Protocol, runtime_checkable
import unittest

from ck3_live_run_id import current_machine_id
from ck3_mod_acceptance_background_types import JsonObject, file_pin, json_object, text_field
from ck3_mod_acceptance_build_runtime import EXTRA_CAPABILITIES, HOST_RELATIVE, build_canonical_host_successor, project_host, registration_driver

REPOSITORY = Path(__file__).resolve().parents[1]

if TYPE_CHECKING:
    from mcp.server import MCPServer
    from xar_autoplayer.bridge.driver import GameplayBridgeDriver


@runtime_checkable
class RegistrationProducer(Protocol):
    def __call__(self, case: JsonObject) -> object: ...


@runtime_checkable
class PrisonerServerFactory(Protocol):
    def __call__(self, driver: GameplayBridgeDriver) -> MCPServer: ...


def actual_pin(path: Path) -> JsonObject:
    raw = path.read_bytes()
    return json_object(file_pin({'path': str(path.resolve()), 'bytes': len(raw),
                                 'sha256': hashlib.sha256(raw).hexdigest()}))


def prisoner_banish_wire(can_send: bool) -> dict[str, object]:
    """Authored native DTO: tests transport semantics, never claims a live quote."""
    from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import (
        RELEASE_COST_KEYS_12003, RELEASE_OPTION_KEYS_12003,
    )
    unavailable = {'private_build': True, 'read_only': True, 'advertised': False,
                   'action_surface_present': False, 'status': 'unavailable',
                   'unavailable_reason': 'authored_unrequested_quote'}
    preview: dict[str, object] = {
        'private_build': True, 'read_only': True, 'advertised': False,
        'action_surface_present': False, 'status': 'available',
        'requested_option_mask_bits': 4, 'selected_option_mask_bits': 4,
        'snapshot_id': 'native:1014', 'public_revision': 1014, 'native_revision': 1014,
        'proof_epoch': 2, 'date_raw': 53286360,
        'definition': {'canonical_key': 'release_from_prison_interaction',
                       'deterministic_key_hash': 123, 'runtime_ordinal': 186},
        'payload_shape': 'two_role_selected_release_options',
        'roles': {'actor_character_id': 29829, 'recipient_character_id': 61540},
        'puppet_or_actor_character_id': 29829, 'option_keys': list(RELEASE_OPTION_KEYS_12003),
        'can_send': can_send,
        'costs': {'raw_scale': 100000, 'payer_role': 'actor', 'application_timing': 'on_send',
                  'entries': [{'resource_key': key, 'raw': i * 100001}
                              for i, key in enumerate(RELEASE_COST_KEYS_12003)]},
        'acceptance': ({'kind': 'auto_accept', 'auto_accept': True, 'would_accept_now': True}
                       if can_send else {'kind': 'not_evaluated_unsendable', 'auto_accept': False}),
        'readiness': {key: (can_send if key == 'acceptance_ready' else True) for key in (
            'definition_ready', 'actor_ready', 'recipient_ready', 'finalized_context_ready',
            'can_send_ready', 'costs_ready', 'acceptance_ready', 'same_frame_ready')},
    }
    return {
        'step': 'query-player-prisoner-collection-private-v1', 'accepted': True,
        'status': 'available', 'query_sequence': 1, 'observation_revision': 2,
        'snapshot_revision': 1014, 'private_build': True, 'read_only': True,
        'advertised': False, 'backend_id': 'native-headless',
        'player_prisoner_collection': {
            'schema': 'player-prisoner-collection-private-v1', 'schema_version': 7,
            'snapshot_revision': 1014, 'status': 'available', 'unavailable_reason': None,
            'date_raw': 53286360, 'played_character_id': 29829,
            'played_house_id': None, 'played_dynasty_id': None, 'played_dread_raw': 0,
            'total_count': 1, 'returned_count': 1, 'collection_complete': True,
            'prisoners': [{'source_ordinal': 0, 'prisoner_character_id': 61540,
                'collection_owner_character_id': 29829, 'jailer_character_id': 29829,
                'custody_relation_verified': True, 'house_id': None, 'dynasty_id': None,
                'same_house': False, 'same_dynasty': False, 'is_child_of_played_character': False,
                'primary_title_tier_raw': None, 'native_kinship': deepcopy(unavailable),
                'unconditional_release_preview': deepcopy(unavailable),
                'ransom_quote_preview': deepcopy(unavailable), 'negotiated_release_preview': preview}],
        },
    }


class PrisonerPreviewEndpoint:
    pipe_name = r'\\.\pipe\authored_prisoner_readonly_contract'

    def __init__(self) -> None:
        self.on_frame: Callable[[dict[str, object]], None] | None = None
        self.requests: list[dict[str, object]] = []
        self.result = prisoner_banish_wire(True)

    def start(self, on_frame: Callable[[dict[str, object]], None],
              on_disconnect: Callable[[], None]) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise ValueError('Actual driver did not bind the authored endpoint')
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        if frame.get('type') == 'ping':
            return
        assert frame['type'] == 'execute_step'
        assert frame['step'] == 'query-player-prisoner-collection-private-v1'
        assert frame['expected_revision'] == 1014
        assert type(frame['release_option_mask_bits']) is int and frame['release_option_mask_bits'] == 4
        self.requests.append(deepcopy(frame))
        self.publish({'type': 'command_result', 'protocol_version': 1,
                      'request_id': frame['request_id'], 'ok': True, 'result': deepcopy(self.result)})

    def close(self) -> None:
        pass


def assert_prisoner_preview_provider_chain(host: Path, declared: list[str],
        server_factory: PrisonerServerFactory | None = None) -> None:
    """Actual host permission -> registered MCP -> real driver/transport; no CK3."""
    sys.path.insert(0, str(REPOSITORY / 'ck3_autonomous_player/src'))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    factory = create_server if server_factory is None else server_factory
    tool = 'ck3_query_player_prisoner_collection_private_v1'
    tree = ast.parse(host.read_text(encoding='utf-8-sig'))
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute)
        and node.targets[0].attr == 'allow_private_prisoner_collection_query'
        and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == 'driver']
    assert len(assignments) == 1
    endpoint = PrisonerPreviewEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1)
    try:
        endpoint.publish({'type': 'hello', 'protocol_version': 1, 'bridge_version': '0.1.0',
            'pid': 7878, 'session_generation': 0, 'game_version': '1.20.0.4',
            'expected_ck3_version': '1.20.0.4',
            'executable_sha256': '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518',
            'capabilities': ['game.state.snapshot', 'game.command.query-player-prisoner-collection-private-v1']})
        endpoint.publish({'type': 'state_snapshot', 'protocol_version': 1,
            'snapshot_id': 'native:1014', 'revision': 1014,
            'state': {'phase': 'map_hud', 'date': 'authored:prisoner-boundary', 'date_raw': 53286360,
                'speed': 1, 'paused': True, 'map_ready': True, 'history': [], 'active_event': None,
                'pending_character_interaction': None, 'played_character': {'character_id': 29829, 'alive': True},
                'one_life_settlement': None, 'active_wars': [], 'player_armies': []}})
        # Run the actual canonical assignment; action permissions stay default off.
        setattr(driver, 'case_declared_read_only_mcp_tools', frozenset(declared))
        statements: list[ast.stmt] = [*assignments]
        exec(compile(ast.Module(body=statements, type_ignores=[]), str(host), 'exec'), {'driver': driver})

        async def exercise() -> None:
            async with Client(factory(driver)) as client:
                tools = {row.name: row for row in (await client.list_tools()).tools}
                assert (tool in tools) is (tool in declared)
                assert 'ck3_release_player_prisoner_private_v1' not in tools
                assert 'ck3_ransom_player_prisoner_private_v1' not in tools
                if tool not in declared:
                    assert endpoint.requests == []
                    return
                annotations = tools[tool].annotations
                assert annotations is not None and annotations.read_only_hint is True
                revision = driver.take_snapshot()['revision']
                assert isinstance(revision, int) and not isinstance(revision, bool)
                arguments: dict[str, object] = {'expected_revision': revision, 'release_option_keys': ['banish']}
                for can_send in (True, False):
                    endpoint.result = prisoner_banish_wire(can_send)
                    called = await client.call_tool(tool, arguments)
                    assert called.is_error is False
                    result = json_object(json.loads(json.dumps(called.structured_content)))
                    collection = json_object(result['player_prisoner_collection'])
                    rows = collection['prisoners']
                    assert isinstance(rows, list) and len(rows) == 1
                    row = json_object(rows[0])
                    preview = json_object(row['negotiated_release_preview'])
                    assert row['prisoner_character_id'] == 61540
                    assert preview['can_send'] is can_send
                    assert preview['selected_option_mask_bits'] == result['queried_release_option_mask_bits'] == 4
                    assert result['queried_release_option_keys'] == ['banish']
                    assert result['exact_ck3_build'] == '1.20.0.4'
                before = len(endpoint.requests)
                invalid_arguments: list[dict[str, object]] = [
                    {}, {'expected_revision': True}, {'expected_revision': float(revision)},
                    {'expected_revision': str(revision)}, {'expected_revision': None},
                    {**arguments, 'ransom_ordinal': True}, {**arguments, 'ransom_ordinal': 64},
                    {**arguments, 'release_option_keys': [True]}, {**arguments, 'release_option_keys': []},
                    {**arguments, 'release_option_keys': ['banish', 'banish']},
                    {**arguments, 'release_option_keys': ['unknown']},
                    {**arguments, 'release_material_target_character_id': True},
                    {**arguments, 'send': True},
                ]
                for invalid in invalid_arguments:
                    rejected = await client.call_tool(tool, invalid)
                    assert rejected.is_error is True, invalid
                    assert len(endpoint.requests) == before, invalid
                for defect in ('missing', 'type', 'mask', 'owner'):
                    endpoint.result = prisoner_banish_wire(True)
                    value = json_object(endpoint.result['player_prisoner_collection'])
                    rows = value['prisoners']
                    assert isinstance(rows, list)
                    row = json_object(rows[0])
                    preview = json_object(row['negotiated_release_preview'])
                    if defect == 'missing':
                        del preview['can_send']
                    elif defect == 'type':
                        preview['can_send'] = 1
                    elif defect == 'mask':
                        preview['selected_option_mask_bits'] = 0
                    else:
                        row['jailer_character_id'] = 29830
                    row['negotiated_release_preview'] = preview
                    value['prisoners'] = [row]
                    endpoint.result['player_prisoner_collection'] = value
                    rejected = await client.call_tool(tool, arguments)
                    assert rejected.is_error is True, defect
        asyncio.run(exercise())
    finally:
        driver.close()


def assert_prisoner_preview_runtime_consumers(runtime_path: Path, argv: list[str]) -> None:
    runtime = json_object(json.loads(runtime_path.read_bytes()))
    paths = json_object(runtime['paths'])
    source = Path(text_field(paths, 'source_root'))
    index = json_object(json.loads(Path(text_field(paths, 'source_index')).read_bytes()))
    files = json_object(index['files'])
    for name in ('mcp_server.py', 'native_driver.py', 'player_prisoner_collection_private_transport.py',
                 'prisoner_release_preview_contract_12003.py', 'prisoner_negotiated_preview_contract_12003.py',
                 'prisoner_selected_quote_source_contract_12004.py'):
        relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/' + name
        pin = actual_pin(source / relative)
        assert files[relative] == {'bytes': pin['bytes'], 'sha256': pin['sha256']}
        assert (source / relative).read_bytes() == (REPOSITORY / relative).read_bytes()
    declared = [argv[i + 1] for i, argument in enumerate(argv) if argument == '--case-read-only-mcp-tool']
    assert Path(argv[argv.index('--agent-source-root') + 1]).resolve() == source.resolve()
    environment = json_object(runtime['runtime_environment'])
    imports = environment['PYTHONPATH']
    assert isinstance(imports, list) and isinstance(imports[0], str)
    assert Path(imports[0]).resolve() == (source / 'ck3_autonomous_player/src').resolve()
    # Execute the exact files emitted by Java. The existing driver imports this
    # transport at call time; all dependency bytes above retain their source pins.
    bridge = source / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
    loaded = {
        'xar_autoplayer.bridge._java_produced_prisoner_factory': bridge / 'mcp_server.py',
        'xar_autoplayer.bridge.player_prisoner_collection_private_transport':
            bridge / 'player_prisoner_collection_private_transport.py',
    }
    previous = {name: sys.modules.get(name) for name in loaded}
    try:
        for name, path in loaded.items():
            specification = importlib.util.spec_from_file_location(name, path)
            assert specification is not None and specification.loader is not None
            module = importlib.util.module_from_spec(specification)
            sys.modules[name] = module
            specification.loader.exec_module(module)
            location = module.__file__
            assert isinstance(location, str) and Path(location).resolve() == path.resolve()
        candidate: object = getattr(sys.modules['xar_autoplayer.bridge._java_produced_prisoner_factory'],
                                    'create_server', None)
        assert isinstance(candidate, PrisonerServerFactory)
        assert_prisoner_preview_provider_chain(Path(text_field(paths, 'host')), declared, candidate)
    finally:
        for name, original in previous.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class CanonicalHostSuccessorTests(unittest.TestCase):
    def test_prisoner_modified_production_scope_passes_strict_types(self) -> None:
        factory = REPOSITORY / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
        tree = ast.parse(factory.read_text(encoding='utf-8-sig'))
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                     and node.name == 'ck3_query_player_prisoner_collection_private_v1']
        self.assertEqual(len(functions), 1)
        function = deepcopy(functions[0])
        function.decorator_list = []
        prelude = '''from typing import Annotated, Protocol
from pydantic import Field
from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import RELEASE_OPTION_KEYS_12003
class Driver(Protocol):
    case_declared_read_only_mcp_tools: frozenset[str]
    allow_private_prisoner_collection_query: bool
    def query_player_prisoner_collection_private_v1(self, *, expected_revision: int,
            ransom_ordinal: int = 0, release_option_keys: list[str] | None = None,
            release_material_target_character_id: int | None = None) -> dict[str, object]: ...
driver: Driver
'''
        host = ast.parse((REPOSITORY / HOST_RELATIVE).read_text(encoding='utf-8-sig'))
        assignments = [node for node in ast.walk(host) if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr == 'allow_private_prisoner_collection_query'
            and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == 'driver']
        self.assertEqual(len(assignments), 1)
        declarations: list[ast.stmt] = []
        for relative, names in (
            ('tools/ck3_mod_acceptance.py', {'CASE_READ_ONLY_MCP_TOOLS'}),
            ('tools/ck3_mod_acceptance_build_runtime.py', {'EXTRA_CAPABILITIES', 'REGISTRATION_READ_ONLY_FLAGS'}),
        ):
            module = ast.parse((REPOSITORY / relative).read_text(encoding='utf-8-sig'))
            selected = [node for node in module.body if isinstance(node, ast.AnnAssign)
                        and isinstance(node.target, ast.Name) and node.target.id in names]
            self.assertEqual(len(selected), len(names))
            declarations.extend(selected)
        module = ast.Module(body=[*declarations, *assignments, function], type_ignores=[])
        with tempfile.TemporaryDirectory(prefix='prisoner-readonly-strict-') as directory:
            root = Path(directory)
            source = root / 'actual_modified_scope.py'
            source.write_text(prelude + ast.unparse(module) + '\n', encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', '-m', 'mypy', '--strict',
                '--follow-imports=skip', '--no-incremental', '--cache-dir', str(root / 'cache'),
                str(source)], capture_output=True, text=True, encoding='utf-8', timeout=120,
                env={**os.environ, 'MYPYPATH': str(REPOSITORY / 'ck3_autonomous_player/src')})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prisoner_readonly_host_factory_transport_is_default_off_and_keeps_banish_gate(self) -> None:
        for declared in ([], ['ck3_query_player_prisoner_collection_private_v1']):
            with self.subTest(declared=declared):
                assert_prisoner_preview_provider_chain(REPOSITORY / HOST_RELATIVE, declared)

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

            # Consume the actual first producer's bytes as the next parent. The
            # old import provider intentionally stays on PYTHONPATH: the pinned
            # loader must select its own exact overlay rather than that legacy file.
            manifest['host'] = {'path_key': 'host', **{key: actual_pin(output / 'shared-host.py')[key]
                                                      for key in ('bytes', 'sha256')}}
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            parent_runtime['manifest'] = actual_pin(manifest_path)
            parent_runtime['paths'] = {'host': str(output / 'shared-host.py')}
            parent_runtime['allocator_overlay'] = {'registration': actual_pin(output / 'registration_mcp.py')}
            runtime.write_text(json.dumps(parent_runtime), encoding='utf-8')
            second = root / 'second-successor'
            ref = build_canonical_host_successor(runtime, source, root / 'second-runtime.json', second, machine)
            second_receipt = json_object(json.loads(Path(ref['path']).read_bytes()))
            projection = json_object(second_receipt['registration_projection'])
            self.assertEqual(projection['parent'], actual_pin(output / 'registration_mcp.py'))
            self.assertEqual((second / 'registration_mcp.py').read_bytes(),
                             (output / 'registration_mcp.py').read_bytes())
            self.assertIn(str(second / 'registration_mcp.py').replace('\\', '\\\\'),
                          (second / 'shared-host.py').read_text(encoding='utf-8-sig'))
            registration_path = output / 'registration_mcp.py'
            registration_bytes = registration_path.read_bytes()
            original_registration_pin = actual_pin(registration_path)
            for defect in ('incomplete', 'wrong-pin', 'missing-overlay', 'wrong-factory', 'lost-service'):
                with self.subTest(defect=defect):
                    registration_path.write_bytes(registration_bytes)
                    changed = actual
                    bad_runtime = deepcopy(parent_runtime)
                    if defect == 'incomplete':
                        changed = changed.replace('bind_registration()', 'bind_registration(1)', 1)
                    elif defect == 'wrong-pin':
                        changed = changed.replace(str(actual_pin(output / 'registration_mcp.py')['sha256']), '0' * 64, 1)
                    elif defect == 'missing-overlay':
                        bad_runtime['allocator_overlay'] = {}
                    else:
                        registration_text = registration_bytes.decode('utf-8-sig')
                        if defect == 'wrong-factory':
                            registration_text = registration_text.replace('from xar_autoplayer.bridge import mcp_server as module',
                                                                         'from unknown import mcp_server as module', 1)
                        else:
                            registration_text = registration_text.replace('service_override=service_override',
                                                                         'service_override=None', 1)
                        registration_path.write_text(registration_text, encoding='utf-8-sig')
                        changed_pin = actual_pin(registration_path)
                        changed = changed.replace(str(original_registration_pin['sha256']), str(changed_pin['sha256']), 1)
                        changed = changed.replace("'bytes': " + str(original_registration_pin['bytes']),
                                                  "'bytes': " + str(changed_pin['bytes']), 1)
                        bad_runtime['allocator_overlay'] = {'registration': changed_pin}
                    (output / 'shared-host.py').write_text(changed, encoding='utf-8-sig')
                    changed_host = actual_pin(output / 'shared-host.py')
                    manifest['host'] = {'path_key': 'host', 'bytes': changed_host['bytes'], 'sha256': changed_host['sha256']}
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                    bad_runtime['manifest'] = actual_pin(manifest_path)
                    runtime.write_text(json.dumps(bad_runtime), encoding='utf-8')
                    rejected = root / ('rejected-' + defect)
                    with self.assertRaises(ValueError):
                        build_canonical_host_successor(runtime, source, root / 'bad-runtime.json', rejected, machine)
                    self.assertFalse(rejected.exists())

    def test_projected_builder_and_local_service_require_the_selected_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
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
            host_pin = actual_pin(parent)
            manifest['host'] = {'path_key': 'host', 'bytes': host_pin['bytes'], 'sha256': host_pin['sha256']}
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            base = json_object(json.loads(runtime.read_bytes()))
            base['manifest'] = actual_pin(manifest_path)
            registration = root / 'registration/registration_mcp.py'
            registration.parent.mkdir()
            base['runtime_environment'] = {'PYTHONPATH': [str(registration.parent)]}
            factory = source / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
            factory.parent.mkdir(parents=True)
            factory.write_bytes((REPOSITORY / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py').read_bytes())
            # Reduced from the retained parent: real local service + Protocol
            # alias + builder call, without copying unrelated registered tools.
            provider = '''def create_server(driver, *, profile_dir=None, before_auto_turn_submit=None):
    from xar_autoplayer.bridge.service import GameplayBridgeService
    service = GameplayBridgeService(driver)
    from xar_autoplayer.bridge import mcp_server as module
    from typing import Protocol, runtime_checkable
    @runtime_checkable
    class Builder(Protocol):
        def create_server(self, driver, *, service_override, profile_dir, before_auto_turn_submit): ...
    builder: Builder = module
    server = builder.create_server(driver, service_override=service, profile_dir=profile_dir,
                                   before_auto_turn_submit=before_auto_turn_submit)
    return server
'''
            for shape in ('annotated', 'assigned', 'wrong-builder', 'duplicate-builder'):
                with self.subTest(shape=shape):
                    selected = provider
                    if shape == 'assigned':
                        selected = selected.replace('builder: Builder = module', 'builder = module')
                    elif shape == 'wrong-builder':
                        selected = selected.replace('builder: Builder = module', 'builder: Builder = unknown_module')
                    elif shape == 'duplicate-builder':
                        selected = selected.replace('builder: Builder = module', 'builder: Builder = module\n    builder = module')
                    registration.write_text(selected, encoding='utf-8')
                    base['allocator_overlay'] = {'registration': actual_pin(registration)}
                    runtime.write_text(json.dumps(base), encoding='utf-8')
                    output = root / shape
                    if shape in ('annotated', 'assigned'):
                        build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', output, machine)
                        emitted = (output / 'registration_mcp.py').read_text(encoding='utf-8-sig')
                        self.assertEqual(ast.dump(ast.parse(selected)), ast.dump(ast.parse(emitted)))
                    else:
                        with self.assertRaisesRegex(ValueError, 'builder must bind uniquely'):
                            build_canonical_host_successor(runtime, source, root / 'selected-runtime.json', output, machine)
                        self.assertFalse(output.exists())

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
