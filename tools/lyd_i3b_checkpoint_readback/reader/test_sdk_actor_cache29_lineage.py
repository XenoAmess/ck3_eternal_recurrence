"""Pure source-contract fixtures; these rows are not actual SDK metadata."""
from pathlib import Path
import copy
import json
import unittest

import sdk_artifact_lineage as lineage


class ActorCache29LineageTests(unittest.TestCase):
    def setUp(self):
        reference = json.loads((Path(__file__).parent / 'dependencies/frozen_sdk_g2_g3_metadata.json').read_bytes())
        self.rows = [{'name': name} for name in reference['readonly23_tool_names']]
        self.rows = [copy.deepcopy(reference['G2_G3_tools'].get(row['name'], row)) for row in self.rows]
        self.descriptor = {'sha256': '1' * 64}
        self.cache = copy.deepcopy(reference['G2_G3_tools']['ck3_query_profile_confucian_assembly_predicates_v1'])
        self.cache['name'] = lineage.ACTOR_CACHE_TOOL_NAME
        self.cache['description'] = "Read the actor's complete native cached successor IDs in original order."
        self.cache['inputSchema']['title'] = lineage.ACTOR_CACHE_TOOL_NAME + 'Arguments'
        self.cache['outputSchema']['title'] = lineage.ACTOR_CACHE_TOOL_NAME + 'DictOutput'

    def inventory(self, count):
        result = copy.deepcopy(self.rows)
        if count >= 24:
            result.append({'name': lineage.GRAPH_TOOL_NAME})
        if count >= 28:
            result.extend({'name': name} for name in lineage.GRANT_TOOL_NAMES)
        if count == 29:
            result.append(copy.deepcopy(self.cache))
        return result

    def verify(self, rows):
        return lineage.verify_metadata_artifact(rows, self.descriptor, '1' * 64)

    def test_original_inventories_and_explicit29(self):
        for count in (23, 24, 28, 29):
            with self.subTest(count=count):
                self.assertEqual(self.verify(self.inventory(count))['actual_tool_count'], count)

    def test29_cannot_replace_additional_tool_or_duplicate_name(self):
        for replacement in ('unknown_query', lineage.GRAPH_TOOL_NAME):
            rows = self.inventory(29)
            rows[-1]['name'] = replacement
            with self.subTest(name=replacement), self.assertRaises(ValueError):
                self.verify(rows)

    def test28_cannot_silently_replace_grant_with_cache(self):
        rows = self.inventory(28)
        rows[-1] = self.cache
        with self.assertRaises(ValueError):
            self.verify(rows)

    def test29_requires_closed_revision_schema_and_readonly_annotations(self):
        changes = (
            ('inputSchema', 'additionalProperties', True),
            ('annotations', 'readOnlyHint', False),
            ('annotations', 'destructiveHint', True),
            ('outputSchema', 'additionalProperties', False),
        )
        for section, key, value in changes:
            rows = self.inventory(29)
            rows[-1][section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                self.verify(rows)
        rows = self.inventory(29)
        rows[-1]['inputSchema']['properties']['expected_revision']['exclusiveMinimum'] = -1
        with self.assertRaises(ValueError):
            self.verify(rows)

    def test29_keeps_exact_g2_g3_and_descriptor_binding(self):
        rows = self.inventory(29)
        target = next(row for row in rows if row['name'] == 'ck3_query_profile_confucian_assembly_predicates_v1')
        target['annotations']['readOnlyHint'] = False
        with self.assertRaises(ValueError):
            self.verify(rows)
        with self.assertRaises(ValueError):
            lineage.verify_metadata_artifact(self.inventory(29), self.descriptor, '2' * 64)


if __name__ == '__main__':
    unittest.main()
