from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ck3_live_run_id
from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import ck3_mod_acceptance_prepare as shared_prepare


def write_json(path: Path, value: object) -> FilePin:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    return adapter._sr_pin(path)


class SavedClient:
    def __init__(self, context: JsonObject, response: JsonObject) -> None:
        self.context = context
        self.response = response
        self.snapshot_calls = 0
        self.checkpoint_calls = 0
        self.process: JsonObject = {'pid': 202, 'create_time': 2.0, 'retained_synchronize_query_handle_acquired': True}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> JsonObject:
        if not require_event_free or allow_actor_change:
            raise AssertionError('Cold readback cannot admit an actor transition or active event')
        self.snapshot_calls += 1
        return {'episode_projection': 'native_campaign', 'paused': True, 'date_raw': 51394920,
                'played_character': {'character_id': 1128}, 'active_event': None}

    def retain_process(self) -> JsonObject:
        return self.process

    def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90) -> JsonObject:
        self.checkpoint_calls += 1
        if (name != 'saved-readback-exact-cold-checkpoint' or reserve != 90
                or request.get('no_calendar_advance_or_initialization') is not True):
            raise AssertionError('Shared root checkpoint must preserve original normal-close reserve')
        return self.response

    def checkpoint(self, name: str, value: JsonObject) -> object:
        output = Path(str(self.context['output'])) / (name + '.json')
        if output.exists():
            raise AssertionError('Case result cannot replay')
        return write_json(output, value)


class SavedReadbackTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1] / 'test-work'
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='saved-readback-', dir=root)
        self.root = Path(self.temp.name).resolve()
        self.allowed_root = root.resolve()
        self.assertTrue(self.root.is_relative_to(self.allowed_root))
        config_path = Path(adapter.__file__).with_name('superman_qiang_natural_cold_reload.json')
        self.config = json_object(json.loads(config_path.read_text(encoding='utf-8')))
        self.mode = json_object(self.config['saved_readback'])
        self.typed_mode = adapter.SavedReadbackMode.from_validated_json(self.mode)
        self.machine = ck3_live_run_id.current_machine_id()
        self.source_run = self.machine + '--superman-qiang--R9001'
        self.cold_run = self.machine + '--superman-qiang--R9002'
        self.product = self.root / 'product'
        (self.product / 'common/scripted_effects').mkdir(parents=True)
        (self.product / 'descriptor.mod').write_text('name="original product"\nsupported_version="1.20.*"\n', encoding='utf-8')
        for index in range(34):
            (self.product / f'common/scripted_effects/p{index:02}.txt').write_text(f'effect_{index} = {{ }}\n', encoding='utf-8')
        product_rows = {path.relative_to(self.product).as_posix(): adapter._sr_pin(path)
                        for path in self.product.rglob('*') if path.is_file()}
        projection = write_json(self.root / 'projection.json', {'file_count': 35, 'files': product_rows})
        self.passive = self.root / 'fixture'
        for raw in adapter._sr_list(self.mode['passive_fixture_files'], 'files'):
            name = adapter._sr_text(raw, 'file')
            path = self.passive / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('name="passive fixture"\n' if name == 'descriptor.mod' else '# passive source\n', encoding='utf-8')
        blocked = self.passive / 'common/on_action/sxanf_on_actions.txt'
        blocked.parent.mkdir(parents=True)
        blocked.write_text('on_game_start_after_lobby = { effect = { } }\n', encoding='utf-8')
        plain: dict[str, object] = {}
        for name in shared_prepare.CONFIG_NAMES:
            path = self.root / 'plain' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# actual plain config test input\n', encoding='utf-8')
            plain[name] = adapter._sr_pin(path)
        self.characters: JsonObject = {}
        names = [adapter._sr_text(item, 'reference') for item in adapter._sr_list(self.mode['reference_names'], 'references')]
        for index, name in enumerate(names):
            eligible = index < 8
            partner_id = 1000 + (index + 1 if index % 2 == 0 else index - 1)
            self.characters[name] = {'character_id': 1000 + index, 'alive': index != 11,
                'experience': {'state': 'missing'} if index == 11 else {'state': 'value', 'value': 2 if eligible else 0},
                'month': {'state': 'value', 'value': 12805} if eligible else {'state': 'missing'},
                'partners': {'state': 'value', 'value': [partner_id]} if eligible else {'state': 'missing'}}
        source_save = self.root / 'source-final.ck3'
        source_save.write_bytes(b'actual-source-checkpoint-test-bytes')
        self.source_pin = adapter._sr_pin(source_save)
        self.source_readback = write_json(self.root / 'source-decoder.json', {'original_decoder_facts': self.characters})
        self.origin_path = self.root / 'origin.json'
        self.origin: JsonObject = json_object({'schema': 'ck3-mod-acceptance-saved-readback-origin-v1',
            'machine_id': self.machine, 'run_id': self.source_run, 'reviewer': '/root', 'process_id': 101,
            'checkpoint': self.source_pin, 'readback': self.source_readback, 'player_id': 1128,
            'date_raw': 51394920, 'characters': self.characters})
        origin_pin = write_json(self.origin_path, self.origin)
        self.prepare_context: JsonObject = json_object({'repo_root': str(Path(shared_prepare.__file__).parent.parent),
            'output': str(self.root / 'prepared'), 'state_dir': str(self.root / 'state'),
            'run_id': None, 'product': 'superman-qiang', 'case': 'natural-cold-reload',
            'case_contract': self.config, 'case_inputs': {'product_dir': str(self.product),
                'product_projection': projection, 'passive_fixture_dir': str(self.passive),
                'plain_configuration': plain, 'saved_readback_origin': origin_pin}})

    def tearDown(self) -> None:
        self.assertTrue(self.root.is_relative_to(self.allowed_root))
        self.temp.cleanup()

    def prepare(self) -> JsonObject:
        with patch.object(shared_prepare, '_engine', return_value=(object(), {'exact_test_engine': True})):
            prepared = adapter.prepare_case(self.prepare_context)
        self.assertEqual(json_object(prepared['startup'])['mode'], 'saved_campaign')
        self.assertEqual(json_object(prepared['initial_plan'])['bytes'], len(b'{\n  "steps": []\n}\n'))
        return prepared

    def runtime_context(self) -> JsonObject:
        return json_object({**self.prepare_context, 'run_id': self.cold_run,
                            'output': str(self.root / 'run/case-output')})

    def response(self, context: JsonObject) -> JsonObject:
        cold_save = self.root / 'cold-observed.ck3'
        cold_save.write_bytes(b'new-cold-serialization-test-bytes')
        cold_pin = adapter._sr_pin(cold_save)
        decoded = write_json(self.root / 'cold-decoder.json', {'independent_decoder_facts': self.characters})
        saved = write_json(self.root / 'cold-save-response.json', {'status': 'saved', 'episode_projection': 'native_campaign',
            'date_raw': 51394920, 'path': cold_pin['path'], 'size': cold_pin['bytes'], 'sha256': cold_pin['sha256']})
        process = write_json(self.root / 'cold-process.json', {'run_id': self.cold_run, 'machine_id': self.machine,
            'pid': 202, 'create_time': 2.0, 'birth_filetime': '134372463956405830'})
        return json_object({'run_id': context['run_id'], 'reviewer': '/root',
            'assertions': {name: True for name in adapter.SAVED_READBACK_REQUIREMENTS},
            'evidence': [self.source_pin, self.source_readback, cold_pin, decoded, saved, process],
            'saved_readback': {'source_checkpoint': self.source_pin, 'source_readback': self.source_readback,
                'cold_checkpoint': cold_pin, 'cold_readback': decoded, 'cold_checkpoint_response': saved,
                'process_evidence': process, 'process_id': 202, 'player_id': 1128, 'date_raw': 51394920,
                'characters': copy.deepcopy(self.characters)}})

    def test_prepare_run_verify_real_producer_consumer_roundtrip(self) -> None:
        self.prepare()
        context = self.runtime_context()
        response = json_object(json.loads(json.dumps(self.response(context))))
        client = SavedClient(context, response)
        facts = adapter.run_case(context, client)
        result = adapter.verify_case(context)
        self.assertEqual(result['root_response'], facts['root_response'])
        self.assertEqual((client.snapshot_calls, client.checkpoint_calls), (2, 1))
        self.assertIs(result['case_contract_qualified'], True)
        self.assertIs(result['business_pass'], False)
        self.assertIs(result['product_release_pass'], False)

    def test_typed_origin_and_twelve_character_codecs_roundtrip(self) -> None:
        mode = adapter.SavedReadbackMode.from_validated_json(json.loads(json.dumps(self.typed_mode.to_json())))
        self.assertEqual(mode, self.typed_mode)
        origin = adapter.SavedReadbackOrigin.from_validated_json(self.origin, mode, self.cold_run)
        encoded = json.loads(json.dumps(origin.to_json()))
        self.assertEqual(adapter.SavedReadbackOrigin.from_validated_json(encoded, mode, self.cold_run), origin)
        self.assertEqual(origin.characters.records['sxanf_ref_spouse_a'].partners, adapter.PartnerValues((1001,)))
        self.assertEqual(origin.characters.records['sxanf_ref_dead_b'].experience, adapter.MissingValue())

    def test_typed_root_response_codec_roundtrip_before_consumer(self) -> None:
        context = self.runtime_context()
        original = self.response(context)
        response = adapter.SavedRootResponse.from_validated_json(original, self.typed_mode)
        serialized = json.loads(json.dumps(response.to_json()))
        self.assertEqual(adapter.SavedRootResponse.from_validated_json(serialized, self.typed_mode), response)
        self.assertEqual(response.readback.characters.records['sxanf_ref_spouse_a'].character_id, 1000)

    def test_scalar_and_list_union_codecs_preserve_distinct_json_states(self) -> None:
        scalars: tuple[adapter.ScalarState, ...] = (
            adapter.MissingValue(), adapter.NullValue(), adapter.IntegerValue(0), adapter.IntegerValue(2))
        partners: tuple[adapter.PartnerState, ...] = (
            adapter.MissingValue(), adapter.NullValue(), adapter.PartnerValues(()), adapter.PartnerValues((1000, 1001)))
        for scalar in scalars:
            restored = adapter._sr_scalar_from_validated_json(json.loads(json.dumps(scalar.to_json())), 'scalar')
            self.assertEqual(restored, scalar)
        for partner in partners:
            restored_partners = adapter._sr_partners_from_validated_json(json.loads(json.dumps(partner.to_json())), 'partners')
            self.assertEqual(restored_partners, partner)
            if isinstance(restored_partners, adapter.PartnerValues):
                self.assertIsInstance(restored_partners.value, tuple)

    def test_typed_process_identity_codec_keeps_full_uint64_string(self) -> None:
        retained = adapter.RetainedProcess.from_validated_json(SavedClient({}, {}).process)
        self.assertEqual(adapter.RetainedProcess.from_validated_json(json.loads(json.dumps(retained.to_json()))), retained)
        raw = {'run_id': self.cold_run, 'machine_id': self.machine, 'pid': 202, 'create_time': 2.0,
               'birth_filetime': '134372463956405830'}
        identity = adapter.ColdProcessEvidence.from_validated_json(raw)
        self.assertEqual(identity.birth_filetime, raw['birth_filetime'])
        self.assertEqual(adapter.ColdProcessEvidence.from_validated_json(json.loads(json.dumps(identity.to_json()))), identity)
        for value in (True, 2.0):
            with self.subTest(pid=value), self.assertRaises(ValueError):
                adapter.RetainedProcess.from_validated_json({**retained.to_json(), 'pid': value})
        for creation in (True, float('nan'), float('inf'), None):
            with self.subTest(creation=creation), self.assertRaises(ValueError):
                adapter.RetainedProcess.from_validated_json({**retained.to_json(), 'create_time': creation})

    def test_typed_origin_rejects_unknown_missing_and_wrong_fields(self) -> None:
        for field, value in (('process_id', True), ('player_id', 1128.0), ('date_raw', True),
                             ('run_id', self.cold_run), ('run_id', self.machine + '--li-yu-dao--R9001'),
                             ('run_id', self.machine + '--superman-qiang--R09001'),
                             ('machine_id', 'different-machine'), ('reviewer', '/other')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                adapter.SavedReadbackOrigin.from_validated_json({**self.origin, field: value}, self.typed_mode, self.cold_run)
        for raw in ({key: value for key, value in self.origin.items() if key != 'checkpoint'}, {**self.origin, 'extra': 1}):
            with self.assertRaises(ValueError):
                adapter.SavedReadbackOrigin.from_validated_json(raw, self.typed_mode, self.cold_run)

    def test_real_profile_excludes_registrar_and_has_complete_inventory(self) -> None:
        prepared = self.prepare()
        seed = json_object(json_object(prepared['startup'])['saved_campaign'])
        inventory = json_object(json.loads(Path(str(seed['product_inventory'])).read_text(encoding='utf-8')))
        self.assertEqual(inventory['enabled_mods'], ['mod/product.mod', 'mod/passive-saved-dependencies.mod'])
        rows = adapter._sr_list(inventory['product_files'], 'inventory')
        self.assertEqual(len(rows), 43)  # 35 product + outer, 6 passive + outer.
        for raw in rows:
            row = adapter._sr_checked(raw)
            self.assertNotIn('common/on_action/', row['path'].replace('\\', '/'))
        self.assertFalse((self.root / 'state/native-session').exists())
        self.assertFalse((self.root / 'state/profile/save games').exists())

    def test_unknown_mode_never_falls_back_to_fixture(self) -> None:
        json_object(self.prepare_context['case_contract'])['saved_readback'] = {'mode': 'unknown'}
        self.prepare_context['case_contract'] = {**self.config, 'saved_readback': {'mode': 'unknown'}}
        with self.assertRaises(ValueError):
            adapter.prepare_case(self.prepare_context)

    def test_existing_fixture_branches_keep_their_original_dispatch(self) -> None:
        context: JsonObject = {'case_contract': {'acceptance_scope': 'original-fixture'}}
        client = SavedClient(context, {})
        expected: JsonObject = {'original_fixture': True, 'business_pass': False}
        with patch.object(adapter, '_prepare_fixture_case', return_value=expected) as prepare:
            self.assertEqual(adapter.prepare_case(context), expected)
            prepare.assert_called_once_with(context)
        with patch.object(adapter, '_run_fixture_case', return_value=expected) as run:
            self.assertEqual(adapter.run_case(context, client), expected)
            run.assert_called_once_with(context, client)
        with patch.object(adapter, '_verify_fixture_case', return_value=expected) as verify:
            self.assertEqual(adapter.verify_case(context), expected)
            verify.assert_called_once_with(context)

    def test_source_requires_exact_twelve_and_nonbool_ids(self) -> None:
        for bad in (True, 1000.0, 2**32):
            with self.subTest(bad=bad):
                rows = copy.deepcopy(self.characters)
                row = json_object(rows['sxanf_ref_spouse_a'])
                row['character_id'] = bad
                rows['sxanf_ref_spouse_a'] = row
                with self.assertRaises(ValueError):
                    adapter._sr_characters(rows, self.typed_mode)
        rows = copy.deepcopy(self.characters)
        del rows['sxanf_ref_dead_b']
        with self.assertRaises(ValueError):
            adapter._sr_characters(rows, self.typed_mode)

    def test_value_states_and_partner_duplicates_are_strict(self) -> None:
        for name, field, value in (
            ('sxanf_ref_spouse_a', 'experience', {'state': 'value', 'value': True}),
            ('sxanf_ref_spouse_a', 'month', {'state': 'value', 'value': 12805.0}),
            ('sxanf_ref_spouse_a', 'partners', {'state': 'value', 'value': [1001, 1001]}),
            ('sxanf_ref_spouse_a', 'partners', {'state': 'value', 'value': [True]}),
            ('sxanf_ref_minor_a', 'month', {'state': 'missing', 'value': None}),
        ):
            with self.subTest(field=field, value=value):
                rows = copy.deepcopy(self.characters)
                row = json_object(rows[name]); row[field] = json_object(value); rows[name] = row
                with self.assertRaises(ValueError):
                    adapter._sr_characters(rows, self.typed_mode)

    def test_dead_missing_experience_is_not_initialized_to_zero(self) -> None:
        normalized = adapter._sr_characters(self.characters, self.typed_mode)
        self.assertEqual(normalized.records['sxanf_ref_dead_b'].experience, adapter.MissingValue())
        rows = copy.deepcopy(self.characters)
        dead = json_object(rows['sxanf_ref_dead_b'])
        dead['experience'] = {'state': 'value', 'value': 0}
        rows['sxanf_ref_dead_b'] = dead
        with self.assertRaises(ValueError):
            adapter._sr_characters(rows, self.typed_mode)

    def test_projection_mismatch_rejected_before_profile_materialization(self) -> None:
        (self.product / 'common/scripted_effects/p00.txt').write_text('changed = yes\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'changed'):
            adapter.prepare_case(self.prepare_context)
        self.assertFalse((self.root / 'state').exists())

    def test_unknown_character_field_and_missing_artifact_cannot_qualify(self) -> None:
        rows = copy.deepcopy(self.characters)
        row = json_object(rows['sxanf_ref_spouse_a']); row['extra'] = 1; rows['sxanf_ref_spouse_a'] = row
        with self.assertRaises(ValueError):
            adapter._sr_characters(rows, self.typed_mode)
        self.prepare()
        context = self.runtime_context()
        response = self.response(context)
        evidence = adapter._sr_list(response['evidence'], 'evidence')
        response['evidence'] = json_object({'rows': evidence[:-1]})['rows']
        with self.assertRaisesRegex(ValueError, 'evidence list'):
            adapter.run_case(context, SavedClient(context, response))

    def test_cold_response_missing_wrong_fields_or_assertion_type_rejected(self) -> None:
        self.prepare()
        context = self.runtime_context()
        original = self.response(context)
        for bad_kind in ('missing', 'unknown', 'bool_assertion', 'old_pid', 'bool_player', 'float_date'):
            with self.subTest(kind=bad_kind):
                response = copy.deepcopy(original)
                data = json_object(response['saved_readback'])
                if bad_kind == 'missing':
                    del data['cold_readback']
                elif bad_kind == 'unknown':
                    data['extra'] = 1
                elif bad_kind == 'bool_assertion':
                    assertions = json_object(response['assertions']); assertions[adapter.SAVED_READBACK_REQUIREMENTS[0]] = 1
                    response['assertions'] = assertions
                elif bad_kind == 'old_pid':
                    data['process_id'] = 101
                elif bad_kind == 'bool_player':
                    data['player_id'] = True
                else:
                    data['date_raw'] = 51394920.0
                response['saved_readback'] = data
                compiled = adapter._sr_compiled(context)[0]
                with self.assertRaises(ValueError):
                    adapter._sr_response(response, context, compiled, adapter.RetainedProcess.from_validated_json(SavedClient(context, response).process))

    def test_missing_null_empty_are_preserved_across_real_result_verifier(self) -> None:
        self.prepare()
        context = self.runtime_context()
        response = self.response(context)
        data = json_object(response['saved_readback'])
        rows = json_object(data['characters'])
        minor = json_object(rows['sxanf_ref_minor_a'])
        minor['partners'] = {'state': 'value', 'value': []}
        rows['sxanf_ref_minor_a'] = minor; data['characters'] = rows; response['saved_readback'] = data
        with self.assertRaisesRegex(ValueError, 'changed'):
            adapter.run_case(context, SavedClient(context, response))
        self.assertFalse((Path(str(context['output'])) / 'generic-product-case-result.json').exists())

    def test_explicit_null_and_empty_roundtrip_without_initialization(self) -> None:
        row = json_object(self.characters['sxanf_ref_minor_b'])
        row['month'] = {'state': 'null'}
        row['partners'] = {'state': 'value', 'value': []}
        self.characters['sxanf_ref_minor_b'] = row
        self.source_readback = write_json(self.root / 'source-decoder.json', {'original_decoder_facts': self.characters})
        self.origin['characters'] = copy.deepcopy(self.characters)
        self.origin['readback'] = json_object(self.source_readback)
        inputs = json_object(self.prepare_context['case_inputs'])
        inputs['saved_readback_origin'] = json_object(write_json(self.origin_path, self.origin))
        self.prepare_context['case_inputs'] = inputs
        self.prepare()
        context = self.runtime_context()
        adapter.run_case(context, SavedClient(context, self.response(context)))
        facts = adapter.verify_case(context)
        data = json_object(json_object(facts['root_response'])['saved_readback'])
        observed = json_object(json_object(data['characters'])['sxanf_ref_minor_b'])
        self.assertEqual(observed['month'], {'state': 'null'})
        self.assertEqual(observed['partners'], {'state': 'value', 'value': []})

    def test_save_ack_is_not_a_saved_checkpoint(self) -> None:
        self.prepare()
        context = self.runtime_context()
        response = self.response(context)
        data = json_object(response['saved_readback'])
        actual = json_object(json.loads((self.root / 'cold-save-response.json').read_text(encoding='utf-8')))
        actual['status'] = 'queued'
        replacement = write_json(self.root / 'cold-save-response.json', actual)
        data['cold_checkpoint_response'] = json_object(replacement)
        response['saved_readback'] = data
        evidence = adapter._sr_list(response['evidence'], 'evidence')
        evidence[4] = replacement
        response['evidence'] = json_object({'evidence': evidence})['evidence']
        with self.assertRaisesRegex(ValueError, 'actual native cold SAVE|Actual native cold SAVE'):
            adapter.run_case(context, SavedClient(context, response))

    def test_after_run_tampered_evidence_or_source_refuses_verify(self) -> None:
        self.prepare()
        context = self.runtime_context()
        response = self.response(context)
        adapter.run_case(context, SavedClient(context, response))
        (self.root / 'cold-decoder.json').write_text('{"changed":true}\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'changed'):
            adapter.verify_case(context)

    def test_uint64_birth_filetime_rejects_number_and_rounding(self) -> None:
        self.prepare()
        context = self.runtime_context()
        response = self.response(context)
        data = json_object(response['saved_readback'])
        identity = {'run_id': self.cold_run, 'machine_id': self.machine, 'pid': 202,
                    'create_time': 2.0, 'birth_filetime': 134372463956405830}
        current = write_json(self.root / 'wrong-process.json', identity)
        data['process_evidence'] = json_object(current)
        evidence = adapter._sr_list(response['evidence'], 'evidence'); evidence.append(current)
        response['evidence'] = json_object({'items': evidence})['items']; response['saved_readback'] = data
        with self.assertRaisesRegex(ValueError, 'canonical string'):
            adapter.run_case(context, SavedClient(context, response))

    def test_fixture_registrar_is_rejected_before_any_profile_write(self) -> None:
        config = copy.deepcopy(self.config)
        mode = json_object(config['saved_readback'])
        files = adapter._sr_list(mode['passive_fixture_files'], 'files')
        files.append('common/on_action/sxanf_on_actions.txt')
        mode['passive_fixture_files'] = json_object({'files': files})['files']; config['saved_readback'] = mode
        self.prepare_context['case_contract'] = config
        with self.assertRaises(ValueError):
            adapter.prepare_case(self.prepare_context)
        self.assertFalse((self.root / 'state').exists())


if __name__ == '__main__':
    unittest.main()
