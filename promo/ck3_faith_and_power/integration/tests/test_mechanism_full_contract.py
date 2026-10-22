"""Exercise the actual formal consumer, with source files but no media process."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from faith_power_promo import full_episode as common
from faith_power_promo.formal_episode import FormalInputs
from faith_power_promo.mechanism_contract import MODE, parse_mechanism_full
from test_value_v3_formal import small_metadata_fixture


class MechanismFullContractTests(unittest.TestCase):
    def fixture(self, directory: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path]:
        document, _media = small_metadata_fixture(directory)
        voices = common.read(document['voice_authoring_catalog']['path'])
        evidence = common.read(document['cue_evidence_catalog']['path'])
        source = directory / 'source.json'
        source.write_text('{"rule": "fixed source"}', encoding='utf-8')
        ref = {'file': common.pin(source), 'json_pointer': '/rule',
               'equals': 'fixed source'}
        document.update(scope='episode02-formal-review', review_content_kind=MODE,
                        pending_result_slots={}, result_voice_batches=[], excluded_cues=[])
        voices['new_live_result_voice_slots'] = {}
        for row in document['cues']:
            row.update(content_class='rule', live_result_asserted=False)
        for row in evidence['claims']:
            row.pop('kind', None)
            row.update(claim_kind='source-rule', live_result_asserted=False,
                       source_refs=[deepcopy(ref)])
        return document, voices, evidence, source

    def consume(self, document: dict[str, object], voices: dict[str, object], evidence: dict[str, object]) -> dict[str, object]:
        for key, value in [('voice_authoring_catalog', voices),
                           ('cue_evidence_catalog', evidence)]:
            path = Path(document[key]['path'])
            path.write_text(json.dumps(value), encoding='utf-8')
            document[key] = common.pin(path)
        return FormalInputs(document, common, metadata_only=True).inspect()

    def test_actual_formal_consumer_accepts_explicit_full_mechanism(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            result = self.consume(document, voices, evidence)
            self.assertEqual(result['pending_result_slots'], {})
            self.assertEqual(result['scope'], 'episode02-formal-review')
            self.assertFalse(result['ready_to_build'])
            self.assertFalse(result['fullrender_admitted'])
            self.assertTrue(result['metadata_only'])
            self.assertTrue(all('formal visual parts unbound' in gap
                                for gap in result['gaps']))

    def test_old_full_mode_still_requires_its_live_slots(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            del document['review_content_kind']
            with self.assertRaisesRegex(ValueError, 'preserve every pending'):
                self.consume(document, voices, evidence)

    def test_full_mode_cannot_impersonate_a_segment(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            document['scope'] = 'episode02-review-segment'
            with self.assertRaisesRegex(ValueError, 'full episode02 scope'):
                self.consume(document, voices, evidence)

    def test_live_claim_or_cue_cannot_use_the_exception(self) -> None:
        for target in ('cue', 'claim'):
            for value in (True, 0, None):
                with self.subTest(target=target, value=value), tempfile.TemporaryDirectory() as name:
                    document, voices, evidence, _ = self.fixture(Path(name))
                    row = document['cues'][0] if target == 'cue' else evidence['claims'][0]
                    row['live_result_asserted'] = value
                    with self.assertRaisesRegex(ValueError, 'explicitly deny live'):
                        self.consume(document, voices, evidence)

    def test_missing_flag_and_unknown_classification_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            del document['cues'][0]['live_result_asserted']
            with self.assertRaisesRegex(ValueError, 'explicitly deny live'):
                self.consume(document, voices, evidence)
        for field, bad in [('content_class', 'gameplay'), ('claim_kind', 'observed-live-result')]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as name:
                document, voices, evidence, _ = self.fixture(Path(name))
                row = document['cues'][0] if field == 'content_class' else evidence['claims'][0]
                row[field] = bad
                with self.assertRaisesRegex(ValueError, 'unknown'):
                    self.consume(document, voices, evidence)

    def test_empty_containers_are_required_not_missing_or_null(self) -> None:
        for owner_name, key in [('document', 'pending_result_slots'),
                                ('document', 'result_voice_batches'),
                                ('voices', 'new_live_result_voice_slots')]:
            for mutation in ('missing', 'null', 'wrong_type'):
                with self.subTest(owner=owner_name, key=key, mutation=mutation), tempfile.TemporaryDirectory() as name:
                    document, voices, evidence, _ = self.fixture(Path(name))
                    owner = document if owner_name == 'document' else voices
                    if mutation == 'missing':
                        del owner[key]
                    else:
                        owner[key] = None if mutation == 'null' else 'empty'
                    with self.assertRaises(ValueError):
                        self.consume(document, voices, evidence)

    def test_real_live_slot_is_not_erased(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            voices['new_live_result_voice_slots'] = {'actual-result': None}
            with self.assertRaisesRegex(ValueError, 'cannot erase or invent'):
                self.consume(document, voices, evidence)

    def test_every_claim_needs_a_narrow_bound_source(self) -> None:
        for refs in ([], None, [{'file': {'path': 'missing', 'bytes': 0, 'sha256': '0'*64}}]):
            with self.subTest(refs=refs), tempfile.TemporaryDirectory() as name:
                document, voices, evidence, _ = self.fixture(Path(name))
                evidence['claims'][0]['source_refs'] = refs
                with self.assertRaises(ValueError):
                    self.consume(document, voices, evidence)

    def test_source_identity_and_line_numbers_reject_bool_or_float(self) -> None:
        for value in (True, 1.0):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as name:
                document, voices, evidence, _ = self.fixture(Path(name))
                evidence['claims'][0]['source_refs'][0]['file']['bytes'] = value
                with self.assertRaisesRegex(ValueError, 'exact integer'):
                    self.consume(document, voices, evidence)
            with self.subTest(line=value), tempfile.TemporaryDirectory() as name:
                document, voices, evidence, _ = self.fixture(Path(name))
                ref = evidence['claims'][0]['source_refs'][0]
                del ref['json_pointer']
                ref.update(first_line=value, last_line=1)
                with self.assertRaisesRegex(ValueError, 'exact integer'):
                    self.consume(document, voices, evidence)

    def test_classification_does_not_bypass_actual_source_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, source = self.fixture(Path(name))
            source.write_text('{"rule": "other source"}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'input bytes changed|input size differs'):
                self.consume(document, voices, evidence)

    def test_classification_does_not_bypass_actual_pointer_value(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            evidence['claims'][0]['source_refs'][0]['equals'] = 'invented result'
            with self.assertRaisesRegex(ValueError, 'Source pointer value differs'):
                self.consume(document, voices, evidence)

    def test_json_roundtrip_preserves_the_internal_tuples(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = self.fixture(Path(name))
            expected = parse_mechanism_full(document, voices, evidence)
            actual = parse_mechanism_full(*(json.loads(json.dumps(value))
                                           for value in (document, voices, evidence)))
            self.assertEqual(expected, actual)
            self.assertIsNotNone(actual)

    def test_public_json_entry_rejects_nonobject_roots(self) -> None:
        for document in ([], None, 1, True):
            with self.subTest(document=document), self.assertRaisesRegex(ValueError, 'JSON object'):
                parse_mechanism_full(document, {}, {})
        for voices, evidence in ((None, {}), ({}, [])):
            with self.subTest(voices=voices, evidence=evidence), self.assertRaisesRegex(ValueError, 'JSON object'):
                parse_mechanism_full({'review_content_kind': MODE}, voices, evidence)


if __name__ == '__main__':
    unittest.main()
