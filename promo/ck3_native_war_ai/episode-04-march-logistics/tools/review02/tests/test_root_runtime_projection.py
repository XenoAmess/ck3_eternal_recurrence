"""New metadata projection cases only; no prior matrix, filesystem or SDK."""
import unittest
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import importlib.util
import sys
REVIEW02 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REVIEW02))
import root_runtime_projection as p

class RootShape(unittest.TestCase):
    def fixture(self):
        root=Path(__file__).resolve().parent
        # Synthetic identities; source declarations deliberately differ from
        # native-build provenance to cover a Python-only runtime revision.
        proof={'schema':'xar.e04.robert-identity-source-chain.actual.v1','machine_id':'synthetic',
            'run_id':'synthetic--vanilla--R0999','source_head':'a'*40,'native_build_source_head':'b'*40,
            'pid':7,'process_creation_filetime_100ns':134365824001234567,'connection_generation':2,
            'actual_runtime_character_full_id':9,'episode_run_id':'synthetic-episode',
            'recorded_at_utc':'2026-10-17T01:00:00+00:00'}
        prepared={'machine_id':'synthetic','target_build':{'version':'1.20.0.4'},'bridge_dll':{'sha256':'c'*64}}
        context={'machine_id':'synthetic','source_head':'a'*40,'identity':{'machine_id':'synthetic','run_id':proof['run_id'],'mod_key':'vanilla'}}
        ref={'path':str(root/'synthetic-not-read-proof.json'),'bytes':7,'sha256':'d'*64}
        plan={'status':'frozen','frozen_at_utc':'2026-10-15T23:00:00+00:00','build':{'source_head':'a'*40,'native_dll_sha256':'c'*64}}
        return proof,prepared,context,ref,root,plan
    def test_existing_runtime_shape_uses_real_process_start_and_keeps_native_build_independent(self):
        proof,prepared,context,ref,root,plan=self.fixture()
        actual=p.project(proof,prepared,context,ref,root,plan=plan)
        self.assertEqual(actual['started_at_utc'],'2026-10-16T00:00:00.1234567+00:00')
        self.assertNotEqual(actual['started_at_utc'],proof['recorded_at_utc'])
        self.assertEqual(actual['source_proof']['path'],'synthetic-not-read-proof.json')
        comparison=REVIEW02/'comparison/r10_compare.py'
        spec=importlib.util.spec_from_file_location('actual_R10_schema_for_new_projection',comparison)
        consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
        consumer.schema_check(actual,'runtime')
    def test_late_recording_cannot_repair_pre_freeze_process_and_unknowns_are_not_filled(self):
        proof,prepared,context,ref,root,plan=self.fixture();plan['frozen_at_utc']='2026-10-16T00:00:01+00:00'
        with self.assertRaisesRegex(ValueError,'actually started before'):p.project(proof,prepared,context,ref,root,plan=plan)
        for wrong in (None,True,0,-1):
            changed=deepcopy(proof);changed['process_creation_filetime_100ns']=wrong
            with self.assertRaises(ValueError):p.project(changed,prepared,context,ref,root)
        changed=deepcopy(context);changed['identity']['run_id']='synthetic-other'
        with self.assertRaisesRegex(ValueError,'source/run'):p.project(proof,prepared,changed,ref,root)
        outside={**ref,'path':str(root.parent/'outside-not-read.json')}
        with self.assertRaisesRegex(ValueError,'inside explicit'):p.project(proof,prepared,context,outside,root)
if __name__=='__main__':unittest.main()
