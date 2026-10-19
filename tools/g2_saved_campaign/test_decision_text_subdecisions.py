"""Actual paired source contract on local metadata; no publisher/Game process."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import decision_text_publisher as pub
from decision_text_view import AudienceState
from migrate_p51_subdecisions import transform_feed


class SubdecisionSourceTests(unittest.TestCase):
    def test_two_actual_callbacks_keep_distinct_sources_and_reject_same_decision(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root / 'p37-responses').mkdir(); (root / 'publisher').mkdir()
            config = {'game': {'pid': 31, 'creation_date': 'explicit-fixture-birth'},
                      'current_request_path': str(root / 'CURRENT.json')}
            config_path = root / 'config.json'; config_path.write_text(json.dumps(config))
            (root / 'CURRENT.json').write_text(json.dumps({'sequence': 143, 'tool': 'ck3_auto_turn'}))
            started = {'session': str(root), 'state_root': str(root / 'publisher'),
                       'configuration': pub.pin(config_path)}
            view = AudienceState(); publications = []

            def observed_ack(path, reference, **kwargs):
                source = pub.enqueue_observation(path, started)
                row = pub.read(path); pub.validate_observation(row, path, config)
                view.consume(row)
                # The existing pending-input guard requires the preceding real
                # ACK path. This fixture stands in for that independent child.
                pub.atomic(pub.ack_path(started, source), {'fixture_only': True}, new=True)
                publications.append(source)
                return {'source_observation': source, 'OBS_draw_ack': False}

            def callback(step):
                actual = {'selected_step': step, 'snapshot_id': 'native:58', 'revision': 22,
                          'plan': {'selected_step': step}}
                row = {'source': 'actual GameplayBridgeService.before_submit callback',
                       'game_pid': 31, 'game_creation_date': 'explicit-fixture-birth',
                       'request': {'tool': 'root_before_auto_turn_submit', 'parent_sequence': 143},
                       'result': {'is_error': False, 'structured_content': {'status': 'planned', **actual}}}
                return actual, row

            with patch.object(pub, 'validate_started', return_value=started), patch.object(pub, 'wait_text_published', side_effect=observed_ack):
                one, row_one = callback('ordinary-sway-opportunity-v1')
                first = pub.publish_callback_observation(row_one, {}, actual_observation=one)
                original = Path(first['source_observation']['path']).read_bytes()
                two, row_two = callback('life-advance')
                second = pub.publish_callback_observation(row_two, {}, actual_observation=two)
                self.assertEqual((first['callback_index'], second['callback_index']), (1, 2))
                self.assertEqual(Path(second['source_observation']['path']).name, '0143-0002-0-plan.json')
                self.assertNotEqual(first['source_observation']['sha256'], second['source_observation']['sha256'])
                self.assertIn('推进时间', view.render())
                self.assertEqual(view.last_key, (143, 0))  # Existing stage ordering retained.
                with self.assertRaisesRegex(FileExistsError, 'exact decision'):
                    pub.publish_callback_observation(row_one, {}, actual_observation=one)
                self.assertEqual(Path(first['source_observation']['path']).read_bytes(), original)
                self.assertEqual(len(publications), 2)
                changed = pub.read(second['source_observation']['path'])
                changed['request']['callback_index'] = 1
                with self.assertRaises(ValueError):
                    pub.validate_observation(changed, second['source_observation']['path'], config)
                (root / 'p37-responses/0143-1-result.json').write_text('{}')
                three, row_three = callback('query-campaign-root-context-v1')
                with self.assertRaisesRegex(FileExistsError, 'already has a result'):
                    pub.publish_callback_observation(row_three, {}, actual_observation=three)
                self.assertEqual(len(publications), 2)

    def test_transform_keeps_real_callback_source_and_existing_scope(self):
        source = '''def publish_before_submit(observation):
    row={'source':'actual GameplayBridgeService.before_submit callback'}
    payload=json.dumps(row).encode()
    output=N/'old.json'
    if output.exists(): raise FileExistsError('this decision was already published; no action replay')
    return None
'''
        result = transform_feed(source)
        self.assertIn('actual_observation=observation', result)
        self.assertIn('actual GameplayBridgeService.before_submit callback', result)
        self.assertNotIn('display_protocol_alias_only', result)
        self.assertNotIn('output.exists()', result)


if __name__ == '__main__':
    unittest.main()
