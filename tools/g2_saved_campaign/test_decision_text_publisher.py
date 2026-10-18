"""Focused source qualification; the child test has no Game, OBS or window API."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import decision_text_publisher as pub

def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    return pub.pin(path)

def manual(parent=1):
    step='life-advance-one-day'
    return {'origin':'Root finite maintenance notice', 'display_protocol_alias_only':True,
        'actual_auto_turn_call':False,'actual_Service_callback':False,'business_submitted':False,
        'request':{'tool':'root_before_auto_turn_submit','parent_sequence':parent},
        'result':{'is_error':False,'structured_content':{'status':'planned','selected_step':step,
          'plan':{'selected_step':step,'reason':'观察下一日退却进度，不下达新的军令。'}}}}

class PublisherSourceTests(unittest.TestCase):
    def config(self,root):
        feed=root/'responses';feed.mkdir()
        return {'schema':pub.SCHEMA,'machine_id':'explicit-software-qualification-fixture','qualification_only':True,
            'session':str(root),'state_root':str(root/'publisher'),'decision_text_file':str(root/'decision.txt'),
            'current_request_path':str(root/'CURRENT.json'),'feed_root':str(feed),'game':None}

    def test_actual_callback_binds_held_request_game_and_selected_step(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);config=self.config(root)
            config['game']={'pid':31,'creation_date':'fixture-birth'}
            write(root/'CURRENT.json',{'sequence':9,'tool':'ck3_auto_turn'})
            row=manual(9)
            for key in ('origin','display_protocol_alias_only','actual_auto_turn_call','actual_Service_callback','business_submitted'):row.pop(key)
            row.update(source='actual GameplayBridgeService.before_submit callback',game_pid=31,game_creation_date='fixture-birth')
            source=root/'0009-0-plan.json'
            self.assertEqual(pub.validate_observation(row,source,config)['status'],'planned')
            for change in ({'game_pid':32},{'game_creation_date':'other'},{'request':{'tool':'root_before_auto_turn_submit','parent_sequence':8}}):
                with self.assertRaises(ValueError):pub.validate_observation({**row,**change},source,config)
            changed=copy.deepcopy(row);changed['result']['structured_content']['selected_step']='attack'
            with self.assertRaises(ValueError):pub.validate_observation(changed,source,config)
            write(root/'CURRENT.json',{'sequence':10,'tool':'ck3_auto_turn'})
            with self.assertRaises(ValueError):pub.validate_observation(row,source,config)

    def test_manual_alias_cannot_masquerade_as_Service_callback(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);config=self.config(root)
            self.assertEqual(pub.validate_observation(manual(),root/'notice.json',config)['status'],'planned')
            for key in ('actual_auto_turn_call','actual_Service_callback','business_submitted'):
                row=manual();row[key]=True
                with self.assertRaises(ValueError):pub.validate_observation(row,root/'notice.json',config)

    def test_pending_input_not_overwritten_and_source_is_exact(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);config=self.config(root);Path(config['state_root']).mkdir()
            started={**config};one=root/'one.json';two=root/'two.json';write(one,manual());write(two,manual(2))
            pub.enqueue_observation(one,started)
            with self.assertRaisesRegex(RuntimeError,'still pending'):pub.enqueue_observation(two,started)
            prior=pub.read(Path(config['state_root'])/'CURRENT-INPUT.json')
            self.assertEqual(pub.checked(prior['input'])['source_observation'],pub.pin(one))
            self.assertFalse((Path(config['state_root'])/'INPUT-PUBLISH.lock').exists())

    def test_unknown_launch_intent_never_spawns_again(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);config=self.config(root);path=root/'config.json';write(path,config)
            Path(config['state_root']).mkdir();write(Path(config['state_root'])/'LAUNCH-INTENT.json',{'unknown':True})
            with patch.object(pub.subprocess,'Popen',side_effect=AssertionError('No repeat launch')) as spawn:
                with self.assertRaisesRegex(RuntimeError,'outcome unknown'):pub.PublisherOwner(path).start()
                spawn.assert_not_called()

    def test_new_text_source_contains_no_window_creation_or_old_identity(self):
        source=Path(pub.__file__).read_text(encoding='utf-8')
        for forbidden in ('CreateWindow','RegisterClass','overlay_pid','overlay_hwnd','user32','XARG2DecisionOverlay_'):
            self.assertNotIn(forbidden,source)

    @unittest.skipUnless(os.name=='nt' and os.environ.get('XAR_DECISION_TEXT_PORTABLE_ONLY')!='1',
        'Actual independent child qualification is separate from portable CI')
    def test_real_child_publishes_exact_text_and_normal_retained_exit_zero(self):
        with TemporaryDirectory() as temp:
            root=Path(temp).resolve();config=self.config(root);configpath=root/'config.json';write(configpath,config)
            owner=pub.PublisherOwner(configpath);actual=owner.start()
            self.assertEqual(actual,pub.process_identity(owner.process.pid))
            try:
                started=owner.started();binding=owner.seal_binding(root/'ROOT-DECISION-TEXT-PUBLISHER-BINDING.json')
                self.assertEqual(pub.checked(binding)['publisher_started'],started)
                with self.assertRaisesRegex(ValueError,'software fixture'):pub.validate_started(started)
                source=root/'manual.json';write(source,manual())
                ack=pub.wait_text_published(source,started,recording=False)
                text=Path(config['decision_text_file']).read_bytes()
                self.assertEqual(ack['text_sha256'],hashlib.sha256(text).hexdigest())
                self.assertEqual(ack['publisher'],actual)
                self.assertFalse(ack['OBS_draw_ack'])
                self.assertIn('观察下一日退却进度',text.decode())
                self.assertTrue(text.decode().startswith('智能体实时决策\n'))
                self.assertNotIn('罗贝尔',text.decode())
                self.assertNotIn('PID',text.decode())
            finally:
                owner.stop();closed=owner.close()
            self.assertEqual(closed['exit_code'],0)
            self.assertTrue(closed['Popen_original_kernel_handle_retained'])
            self.assertEqual(closed['forced_process_calls'],0)

if __name__=='__main__':unittest.main()
