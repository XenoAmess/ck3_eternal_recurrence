"""Portable R22 JSON regressions; no SDK, process, save body or live credit."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.dont_write_bytecode = True
P = Path(__file__).parents[1]
sys.path.insert(0, str(P / 'reader'))
sys.path.insert(0, str(P / 'reader/dependencies'))
sys.path.insert(0, str(P / 'tests'))
import checkpoint_transition_v2 as transition
import sdk_artifact_lineage as lineage
import sdk_checkpoint_qualification as strict
import test_checkpoint_transition_v2 as existing

OBSERVATIONS = json.loads(
    (P / 'tests/fixtures/r22_checkpoint_observation_metadata.json').read_bytes()
)


def observed_trait_checkpoint():
    """Use existing inert command/provenance and actual compact actor/frame rows."""
    cp = existing.fixture()['checkpoint']
    for side in ('snapshot_before', 'snapshot_after'):
        observed = deepcopy(OBSERVATIONS[side])
        cp[side].update(observed)
        membership = observed['played_character']['event_trait_membership']
        cp[side]['diagnostics']['hello'].update(
            expected_ck3_version=membership['game_version'],
            expected_ck3_sha256=membership['executable_sha256'].upper(),
            game_adapter_id='ck3-' + membership['game_version'] + '-msvc-x64',
        )
    assert cp['result']['checkpoint']['date_raw'] == cp['snapshot_after']['date_raw']
    return cp


class CheckpointTraitFrameTests(unittest.TestCase):
    def test_actual_trait_revision_transition_preserves_original_business_rows(self):
        cp = observed_trait_checkpoint()
        original = deepcopy(cp)
        before_actor = cp['snapshot_before']['played_character']
        after_actor = cp['snapshot_after']['played_character']
        self.assertNotEqual(before_actor, after_actor)  # Original whole-row check was RED.
        binding, proof = transition.bind_checkpoint_transition(
            cp, existing.basic_provenance(cp)
        )
        self.assertEqual(binding['native_revision'], 2)
        self.assertEqual(proof['before_binding']['native_revision'], 1)
        self.assertEqual(proof['snapshot_before_original'], original['snapshot_before'])
        self.assertEqual(proof['snapshot_after_original'], original['snapshot_after'])
        self.assertEqual(cp, original)
        self.assertFalse(proof['raw_snapshot_rewritten'])
        self.assertIsNone(proof['actual_pass'])
        self.assertIsNone(proof['formal_mandate_credit'])

    def test_membership_revision_requires_its_own_exact_frame(self):
        for side, wrong in [('snapshot_before', 2), ('snapshot_after', 1),
                            ('snapshot_before', None), ('snapshot_before', True)]:
            with self.subTest(side=side, wrong=wrong):
                cp = observed_trait_checkpoint()
                cp[side]['played_character']['event_trait_membership']['snapshot_revision'] = wrong
                with self.assertRaises(strict.QualificationError):
                    transition.bind_checkpoint_transition(cp, existing.basic_provenance(cp))

    def test_actual_trait_and_actor_business_changes_stay_rejected(self):
        def trait(cp):
            cp['snapshot_after']['played_character']['event_trait_membership']['traits']['lifestyle_poet'] = True

        def actor(cp):
            cp['snapshot_after']['played_character']['character_id'] = 65865

        def stress(cp):
            cp['snapshot_after']['played_character']['stress_points'] = 1

        for mutate in (trait, actor, stress):
            with self.subTest(mutation=mutate.__name__):
                cp = observed_trait_checkpoint()
                mutate(cp)
                with self.assertRaises(strict.QualificationError):
                    transition.bind_checkpoint_transition(cp, existing.basic_provenance(cp))

    def test_trait_date_actor_schema_and_unavailable_rows_are_not_discarded(self):
        for key, wrong in [('date_raw', 53144713), ('played_character_id', 65865),
                           ('schema', 'invented-membership'), ('status', 'unavailable')]:
            with self.subTest(key=key):
                cp = observed_trait_checkpoint()
                cp['snapshot_after']['played_character']['event_trait_membership'][key] = wrong
                with self.assertRaises(strict.QualificationError):
                    transition.bind_checkpoint_transition(cp, existing.basic_provenance(cp))


class MetadataFactoryTests(unittest.TestCase):
    def metadata(self, count=28):
        rows = json.loads((P / 'tests/fixtures/readonly23_metadata.json').read_bytes())
        additional = deepcopy(OBSERVATIONS['additional_challenger_and_grant_tools'])
        return rows + additional[:count - 23]

    def verify(self, rows, declared_sha=None):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'metadata.json'
            raw = json.dumps(rows, ensure_ascii=False).encode()
            path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            descriptor = {'path':str(path), 'bytes':len(raw), 'sha256':digest}
            return lineage.verify_metadata_artifact(
                rows, descriptor, digest if declared_sha is None else declared_sha
            )

    def test_exact_readonly23_challenger24_and_actual_grant28_sets(self):
        for count in (23, 24, 28):
            with self.subTest(count=count):
                result = self.verify(self.metadata(count))
                self.assertEqual(result['actual_tool_count'], count)
                self.assertTrue(result['G2_G3_tools_exact'])
                self.assertIsNone(result['actual_acceptance_credit'])

    def test_unknown_duplicate_or_missing_grant_tools_are_rejected(self):
        rows = self.metadata()
        unknown = deepcopy(rows)
        unknown[-1]['name'] = 'invented_grant_tool'
        duplicate = deepcopy(rows)
        duplicate[-1]['name'] = duplicate[-2]['name']
        for changed in (unknown, duplicate, rows[:-1]):
            with self.subTest(names=[row['name'] for row in changed[-5:]]):
                with self.assertRaises(ValueError):
                    self.verify(changed)

    def test_grant28_preserves_exact_G2_schema_check(self):
        rows = self.metadata()
        g2 = next(row for row in rows
                  if row['name'] == 'ck3_query_profile_confucian_assembly_predicates_v1')
        g2['inputSchema']['additionalProperties'] = True
        with self.assertRaisesRegex(ValueError, 'Tool metadata differs'):
            self.verify(rows)

    def test_grant28_declared_metadata_sha_must_still_match(self):
        with self.assertRaisesRegex(ValueError, 'descriptor SHA differs'):
            self.verify(self.metadata(), '0' * 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)
