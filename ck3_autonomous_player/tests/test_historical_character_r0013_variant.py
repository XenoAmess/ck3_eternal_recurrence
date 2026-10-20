from __future__ import annotations

import copy
import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'src'
sys.path.insert(0, str(SOURCE))


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError('Expected a string-keyed object')
    return {key: item for key, item in value.items()}


def sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError('Expected an array')
    return list(value)


POLICY = importlib.import_module('xar_autoplayer.vanilla_events.policy')
REGISTRY = importlib.import_module('xar_autoplayer.vanilla_events.registry')
RECORDS = importlib.import_module('xar_autoplayer.vanilla_events.records_vanilla_shards')
KEY = 'historical_char_creation_events.1'


class HistoricalCharacterVariantTests(unittest.TestCase):
    def context(self) -> dict[str, object]:
        value: object = json.loads((HERE / 'fixtures/historical_character_r0013_context.json').read_text(encoding='utf-8'))
        return mapping(mapping(value)['event_context'])

    def recommend(self, context: dict[str, object], actor: object = 15893) -> dict[str, object]:
        return mapping(POLICY.recommend_registered_vanilla_event_option_v1(context,
            played_character_id=actor, snapshot_option_count=3, ck3_build='1.20.0.4'))

    def test_actual_nine_scope_context_reuses_C_not_first_display(self) -> None:
        context = self.context()
        result = self.recommend(context)
        self.assertEqual(result.get('status'), 'recommended', result)
        self.assertEqual(result.get('selected_native_option_index'), 2, result)
        self.assertEqual(result.get('selected_option_number'), 3, result)
        # Recommendation only; this consumer never sends a native choice.
        self.assertEqual(mapping(context['root_scope'])['typed_identity'],
                         {'status': 'available', 'kind': 'character', 'character_id': 15893})
        self.assertEqual(mapping(sequence(context['options'])[0])['native_option_index'], 0)

    def test_legacy_eight_scope_contract_and_119_record_remain(self) -> None:
        original = mapping(RECORDS.VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS[KEY])
        self.assertNotIn('scope_variants', original)
        self.assertEqual(original['saved_scope_count'], 8)
        self.assertEqual(original['selected_native_option_index'], 2)
        old = mapping(REGISTRY.query_vanilla_event_knowledge_v1(KEY, '1.19.0.6'))
        self.assertEqual(mapping(old['contract'])['saved_scope_count'], 8)
        context = self.context()
        rows = [mapping(row) for row in sequence(context['saved_scopes'])]
        major = copy.deepcopy(next(row for row in rows if row['name'] == 'inspiration_owner'))
        major['name'] = 'major'
        context['saved_scopes'] = [row for row in rows
            if row['name'] not in {'inspiration_owner', 'new_inspiration'}] + [major]
        self.assertEqual(self.recommend(context).get('status'), 'recommended')

    def test_extra_missing_or_duplicate_scope_is_not_recognized(self) -> None:
        for mutation in ('extra', 'missing', 'duplicate'):
            with self.subTest(mutation=mutation):
                context = self.context()
                rows = sequence(context['saved_scopes'])
                if mutation == 'extra':
                    extra = copy.deepcopy(mapping(rows[0])); extra['name'] = 'unreviewed'
                    rows.append(extra)
                elif mutation == 'missing':
                    rows.pop()
                else:
                    rows.append(copy.deepcopy(rows[0]))
                context['saved_scopes'] = rows
                self.assertEqual(self.recommend(context).get('status'), 'blocked')

    def test_bool_actor_and_changed_root_or_scope_type_are_blocked(self) -> None:
        self.assertEqual(self.recommend(self.context(), True).get('status'), 'blocked')
        context = self.context()
        root = mapping(context['root_scope']); identity = mapping(root['typed_identity'])
        identity['character_id'] = 41436; root['typed_identity'] = identity; context['root_scope'] = root
        self.assertEqual(self.recommend(context).get('status'), 'blocked')
        context = self.context(); rows = [mapping(row) for row in sequence(context['saved_scopes'])]
        row = next(row for row in rows if row['name'] == 'new_inspiration')
        scope = mapping(row['scope']); scope['type_key'] = 'character'; row['scope'] = scope
        context['saved_scopes'] = rows
        self.assertEqual(self.recommend(context).get('status'), 'blocked')

    def test_C_disabled_or_display_order_drift_does_not_fall_back_to_A(self) -> None:
        for mutation in ('disabled', 'order'):
            with self.subTest(mutation=mutation):
                context = self.context(); options = [mapping(row) for row in sequence(context['options'])]
                if mutation == 'disabled':
                    options[2]['enabled'] = False
                else:
                    options[0], options[2] = options[2], options[0]
                    for index, row in enumerate(options):
                        row['rendered_index'] = index
                context['options'] = options
                self.assertEqual(self.recommend(context).get('status'), 'blocked')

    def test_modified_definition_analysis_hash_is_rejected(self) -> None:
        knowledge = mapping(REGISTRY.query_vanilla_event_knowledge_v1(KEY, '1.20.0.4'))
        analysis = mapping(knowledge['analysis']); hashes = mapping(analysis['source_sha256'])
        hashes['events/historical_character_events.txt'] = '0' * 64
        analysis['source_sha256'] = hashes; knowledge['analysis'] = analysis
        with patch.object(POLICY, 'query_vanilla_event_knowledge_v1', return_value=knowledge):
            result = self.recommend(self.context())
        self.assertEqual(result.get('status'), 'blocked')
        self.assertEqual(result.get('unavailable_reason'), 'historical_character_exact_source_or_index_drift')

    def test_modified_source_index_definition_or_caller_hash_is_rejected(self) -> None:
        for target in ('definition', 'caller'):
            with self.subTest(target=target):
                indexed = mapping(POLICY.query_vanilla_event_source_v1(KEY, build='1.20.0.4'))
                source = mapping(indexed['source'])
                if target == 'definition':
                    definition = mapping(source['definition']); definition['file_sha256'] = '0' * 64
                    source['definition'] = definition
                else:
                    callers = [mapping(row) for row in sequence(source['caller_candidates'])]
                    callers[0]['file_sha256'] = '0' * 64; source['caller_candidates'] = callers
                indexed['source'] = source
                with patch.object(POLICY, 'query_vanilla_event_source_v1', return_value=indexed):
                    self.assertEqual(self.recommend(self.context()).get('status'), 'blocked')


if __name__ == '__main__':
    unittest.main(verbosity=2)
