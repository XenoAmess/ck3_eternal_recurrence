from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source=Path(__file__).parent/'ck3_mod_acceptance_cases/faith_e01_saved_startup.py'
spec=importlib.util.spec_from_file_location('faith_e01_saved_startup_proof_test',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SavedPreparationProofTests(unittest.TestCase):
    def packets(self,state,event_id=913):
        expected={'event_definition_key':module.EVENT_KEY,'event_instance_id':event_id,
            'actor_character_id':88001,'root_character_id':88001,'date_raw':51394920,'native_option_indices':[0,1]}
        snapshot={'played_character':{'character_id':88001},'date_raw':51394920,'active_event':{'instance_id':event_id}}
        packet={'current_event_window_context':{'event_definition_key':module.EVENT_KEY,
            'current_event_instance_id':event_id,'root_scope':{'typed_identity':{'character_id':88001}}}}
        return {'state_dir':str(state),'expected':expected},snapshot,packet

    def sources(self,state):
        rows={}
        for index,relative in enumerate(module.SOURCE_FILES):
            path=state/'profile/mod-content/product'/relative;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('owned synthetic source '+str(index)).encode())
            rows[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        return rows

    def test_consumes_actual_bound_new_process_instance_without_assuming_old_one(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);rows=self.sources(state)
            args=self.packets(state,event_id=913)
            with patch.object(module,'SOURCE_FILES',rows):result=module.qualify_prepare_event_from_save(*args)
            self.assertEqual(result['event_instance_id'],913)
            self.assertFalse(result['business_pass'])
            self.assertFalse(result['proof']['preparation_or_selection_performed'])

    def test_unbound_instance_or_wrong_actual_actor_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);rows=self.sources(state)
            for fault in ('unbound','actor'):
                context,snapshot,packet=self.packets(state)
                if fault=='unbound':context['expected']['event_instance_id']=None
                else:snapshot['played_character']['character_id']=34014
                with self.subTest(fault=fault),patch.object(module,'SOURCE_FILES',rows),self.assertRaises(ValueError):
                    module.qualify_prepare_event_from_save(context,snapshot,packet)

    def test_added_startup_registrar_or_changed_event_bytes_rejects(self):
        for fault in ('registrar','changed_event'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
                state=Path(directory);rows=self.sources(state);product=state/'profile/mod-content/product'
                if fault=='registrar':
                    path=product/'common/on_action/start.txt';path.parent.mkdir(parents=True)
                    path.write_text('on_game_start_after_lobby = {}')
                else:(product/'events/xar_faith_h01_prepare_events.txt').write_bytes(b'changed')
                with patch.object(module,'SOURCE_FILES',rows),self.assertRaises(ValueError):
                    module.qualify_prepare_event_from_save(*self.packets(state))


if __name__=='__main__':unittest.main()
