"""Version admission fixtures; they carry no native or business acceptance."""
from __future__ import annotations

import copy
import unittest
import test_confucian_readonly_private_v1 as base
import test_confucian_challenger_graph_v1 as challenger
from xar_autoplayer.bridge import confucian_readonly_private_v1 as query
from xar_autoplayer.bridge import confucian_challenger_graph_v1 as graph
from xar_autoplayer.bridge import ingame_decisions_open_contract as opening


def upgraded(raw):
    raw = copy.deepcopy(raw)
    raw['game_version'] = query.CK3_12004.game_version
    raw['executable_sha256'] = query.CK3_12004.executable_sha256
    if 'backend_id' in raw:
        raw['backend_id'] = raw['backend_id'].replace('1.20.0.3', '1.20.0.4')
    if 'qualification' in raw:
        for key in raw['qualification']:
            if key.endswith('_index_sha256'):
                raw['qualification'][key] = query.ACTUAL4_ABI_INDEX_SHA256
    for key in ('confucian_assembly_predicates', 'confucian_religious_title', 'confucian_challenger_graph'):
        if key in raw:
            raw[key] = upgraded(raw[key])
    return raw


def upgraded_frame():
    value = base.frame()
    value['diagnostics']['hello'].update(
        game_adapter_id='ck3-1.20.0.4-msvc-x64',
        expected_ck3_version=query.CK3_12004.game_version,
        expected_ck3_sha256=query.CK3_12004.executable_sha256)
    return value


class Actual4PrivateContractTests(unittest.TestCase):
    def test_all_three_domains_correlate_image_backend_payload_and_static_map(self):
        before = upgraded_frame()
        binding = query.query_binding(before, 3)
        self.assertEqual(set(binding), set(query.query_binding(base.frame(), 3)))
        cases = [('assembly_predicates', base.envelope('assembly_predicates', binding)),
                 ('religious_title', base.envelope('religious_title', binding)),
                 ('challenger_graph', challenger.envelope(binding))]
        for operation, raw in cases:
            project = (lambda value, build: graph.project_native_graph_query(value, binding, challenger.FAITHS, build)) if operation == 'challenger_graph' else (
                lambda value, build: query.project_native_query(value, binding, operation, build))
            for build, value in ((query.CK3_12003, raw), (query.CK3_12004, upgraded(raw))):
                with self.subTest(operation=operation, build=build.game_version):
                    result = project(value, build)
                    self.assertFalse(result['business_postcondition_verified'])
                    self.assertFalse(result['full_product_acceptance_credit'])
            actual = upgraded(raw)
            nested = query.OPERATIONS[operation][3]
            mutations = [lambda v: v.update(executable_sha256=query.CK3_12003.executable_sha256),
                         lambda v: v.update(backend_id=raw['backend_id']),
                         lambda v: v[nested].update(executable_sha256=query.CK3_12003.executable_sha256),
                         lambda v: v.update(snapshot_revision=8)]
            if operation != 'assembly_predicates':
                mutations.append(lambda v: v[nested]['qualification'].update(title_properties_index_sha256='0'*64))
            else:
                mutations.append(lambda v: v[nested]['members'][0].update(adult=False))
            for mutate in mutations:
                changed = copy.deepcopy(actual)
                mutate(changed)
                with self.subTest(operation=operation, mutation=mutate), self.assertRaises(ValueError):
                    project(changed, query.CK3_12004)
            with self.assertRaises(ValueError):
                project(actual, query.CK3_12003)

    def test_hello_frame_and_decision_identity_stay_exact(self):
        before = upgraded_frame()
        binding = query.query_binding(before, 3)
        self.assertTrue(query.same_query_frame(before, copy.deepcopy(before), binding))
        self.assertFalse(query.same_query_frame(before, base.frame(), binding))
        self.assertEqual(opening.opening_binding(before), opening.opening_binding(base.frame()))
        for key, value in (('game_adapter_id', 'ck3-1.20.0.3-msvc-x64'),
                           ('expected_ck3_sha256', query.CK3_12003.executable_sha256)):
            changed = copy.deepcopy(before)
            changed['diagnostics']['hello'][key] = value
            with self.assertRaises(ValueError):
                query.query_binding(changed, 3)
            with self.assertRaises(ValueError):
                opening.opening_binding(changed)
        with self.assertRaises(ValueError):
            opening.result_build({'game_version':'1.20.0.4', 'executable_sha256':query.CK3_12003.executable_sha256})


if __name__ == '__main__':
    unittest.main()
