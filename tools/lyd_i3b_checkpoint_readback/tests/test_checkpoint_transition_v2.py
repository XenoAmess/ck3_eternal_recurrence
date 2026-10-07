"""Portable inert checkpoint/SDK fixtures; no external attempt or game access."""
from pathlib import Path
from copy import deepcopy
import json,sys,hashlib,unittest,tempfile
from unittest.mock import patch
ROOT=Path(__file__).parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'reader'))
sys.path.insert(0,str(ROOT/'reader/dependencies'))
sys.path.insert(0,str(ROOT/'tests'))
import checkpoint_transition_v2 as transition
import sdk_checkpoint_transition_qualification_v2 as seam
import sdk_checkpoint_qualification as strict
import sdk_artifact_lineage as lineage
import sdk_fixture_builders as f
def descriptor(path):
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
metadata=descriptor(ROOT/'tests/fixtures/readonly23_metadata.json')
codec=descriptor(ROOT/'tests/fixtures/inert_sdk_codec.py')
business=json.loads((ROOT/'reader/dependencies/frozen_business_contract.json').read_bytes())['files']

def basic_provenance(receipt):
    frame=strict.frame_binding(receipt['snapshot_before'])
    return {k:receipt[k] for k in ('session_id','profile_sha256','pipe_name')} | {'game_pid':frame['game_pid'],'connection_generation':frame['connection_generation']}

def fixture():
    """Entire query/state bundle is an inert synthetic fixture; never live credit."""
    before=f.frame();before.update(backend_id='native-headless',local_player_id=1,last_checkpoint_submission=None,native_command_history=[])
    before['diagnostics'].update(pipe_name='synthetic-pipe',bridge_pid=991)
    before['played_character_gold']={'raw':104300000,'scale':100000}
    before['diagnostics']['last_heartbeat']={'main_thread_query_mailbox_v1':{'ready':True,'consecutive_verified':1,'owner_verified_pump_epochs':1,'pump_epochs':1},'monotonic_ms':1,'sequence':1,'snapshot_observer_12002':{'started_ms':1,'completed_ms':1}}
    after=deepcopy(before);after.update(revision=4,native_revision=8,snapshot_id='native:8')
    after['diagnostics']['last_heartbeat']['sequence']=2
    submission={'sequence':1,'requested_save_name':'xar_checkpoint','date_raw':before['date_raw']}
    cpdesc={'status':'saved','path':str(Path(tempfile.gettempdir())/'synthetic-transition/xar_checkpoint.ck3'),'name':'xar_checkpoint.ck3','size':123,'sha256':'4'*64,
        'date_raw':before['date_raw'],'history_index':1,'strategy':'native-autosave-command-v1'}
    result={'step':'save-checkpoint','accepted':True,'status':'submitted','submission':submission,'backend_id':'native-headless',
        'checkpoint':cpdesc,'materialization':{'available':True,'save_dir':str(Path(tempfile.gettempdir())/'synthetic-transition'),'mtime_ns':1}}
    after['last_checkpoint_submission']={**submission,'status':'submitted'}
    after['native_command_history']=[{'index':1,'command':'save-checkpoint','ok':True,'result':deepcopy(result)}]
    def outer(result):
        return {'schema':'ck3.native-profile-receipt.v1','session_id':'synthetic-session','profile_sha256':'3'*64,'pipe_name':'synthetic-pipe',
            'recorded_at_utc':'synthetic-only','receipt_path':'synthetic-only.json','status':'native_confucian_readonly_observed',
            'result':result,'business_effects_verified':False,'full_product_acceptance_credit':False}
    checkpoint=outer(result);checkpoint.update(status='native_gameplay_postcondition_verified',snapshot_before=before,snapshot_after=after,uses_ocr=False,uses_desktop_input=False)
    binding=seam.frame_binding(after);dto2=f.assembly(binding);dto3=f.title(binding);dto3['native_title_holder_full_id']=31254
    g2=outer(seam.sdk.project_native_query(f.envelope('assembly_predicates',binding,dto2),binding,'assembly_predicates'))
    g3=outer(seam.sdk.project_native_query(f.envelope('religious_title',binding,dto3),binding,'religious_title'))
    provenance={'schema':'lyd.actual-sdk-checkpoint-provenance.v2','source_head':'f'*40,'source_export_sha256':'1'*64,'DLL_sha256':'2'*64,
        **basic_provenance(checkpoint),'reader_contract_source_head':seam.CONTRACT_HEAD,'reader_sha256':seam.READER_SHA,
        'sdk_metadata_sha256':metadata['sha256'],'sdk_metadata_artifact':deepcopy(metadata),'sdk_codec_sha256':codec['sha256'],'sdk_codec_artifact':deepcopy(codec),
        'current_business_files':business,'capture_epochs':{'assembly_predicates':42,'religious_title':43}}
    state={'schema':'lyd.i3b.checkpoint-observations.v1','source_head':seam.CONTRACT_HEAD,'checkpoint_sha256':'4'*64,
        'identity':{'actor_id':31254,'faith_id':107,'main_rite_id':169,'pid':991,'session_id':'synthetic-session','revision':8,'checkpoint_id':cpdesc['path']},
        'actual_pass':None,'actual_native_runtime_pass':None,'formal_mandate_credit':None,
        'roster':{'whole_world_living_records_scanned':True,'faith_classification_complete':True,'living_faith_ids':dto2['complete_native_faith_member_ids']},
        'rites':[{'id':169},{'id':170}], 'native_title':None,'result_head_title_reference':None,'native_reference_qualification':{'status':'UNKNOWN'}}
    hashes={k:str(i)*64 for i,k in enumerate(('provenance','checkpoint_receipt','saved_state','G2_receipt','G3_receipt'),1)}
    return {'provenance':provenance,'checkpoint':checkpoint,'state':state,'g2':g2,'g3':g3,'hashes':hashes,'after_binding':binding}

def convert(d):
    return seam.convert(d['provenance'],d['checkpoint'],d['state'],d['g2'],d['g3'],immutable_business_files=business,artifact_hashes=d['hashes'])

actual=fixture()['checkpoint']

class TransitionTests(unittest.TestCase):
    def reject_checkpoint_mutation(self, mutate):
        cp=deepcopy(actual);mutate(cp)
        with self.assertRaises(strict.QualificationError):transition.bind_checkpoint_transition(cp,basic_provenance(actual))
    def test_synthetic_exact_transition_retains_both_frames(self):
        original=json.dumps(actual,sort_keys=True)
        binding,result=transition.bind_checkpoint_transition(actual,basic_provenance(actual))
        self.assertEqual(binding['revision'],4);self.assertEqual(binding['native_revision'],8)
        self.assertEqual(result['before_binding']['native_revision'],7)
        self.assertEqual(result['snapshot_before_original'],actual['snapshot_before'])
        self.assertEqual(result['snapshot_after_original'],actual['snapshot_after'])
        self.assertEqual(json.dumps(actual,sort_keys=True),original)
        self.assertFalse(result['raw_snapshot_rewritten']);self.assertIsNone(result['actual_pass']);self.assertIsNone(result['formal_mandate_credit'])
    def test_old_strict_gate_rejects_same_checkpoint_transition(self):
        d=fixture();cp=deepcopy(actual)
        provenance=deepcopy(d['provenance']);provenance.pop('sdk_metadata_artifact');provenance.pop('sdk_codec_artifact');provenance['sdk_metadata_sha256']=strict.SDK_METADATA_SHA;provenance['sdk_codec_sha256']=strict.SDK_CODEC_SHA;provenance['schema']='lyd.actual-sdk-checkpoint-provenance.v1';provenance.update(basic_provenance(cp))
        g2=deepcopy(d['g2']);g3=deepcopy(d['g3'])
        for r in (g2,g3):
            for key in ('session_id','profile_sha256','pipe_name'):r[key]=cp[key]
        with self.assertRaisesRegex(strict.QualificationError,'checkpoint crossed native/public snapshot frame') as caught:
            strict.convert(provenance,cp,d['state'],g2,g3,immutable_business_files=business,artifact_hashes=d['hashes'])
    def test_date_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('date_raw',53144713))
    def test_actor_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['played_character'].__setitem__('character_id',65865))
    def test_connection_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['diagnostics'].__setitem__('connection_generation',3))
    def test_pid_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['diagnostics']['hello'].__setitem__('pid',15137))
    def test_profile_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp.__setitem__('profile_sha256','f'*64))
    def test_wallet_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['played_character_gold'].__setitem__('raw',104300001))
    def test_event_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('active_event',{'instance_id':1}))
    def test_pause_drift_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('paused',False))
    def test_multiple_commands_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['native_command_history'].append(deepcopy(cp['snapshot_after']['native_command_history'][0])))
    def test_wrong_appended_result_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['native_command_history'][0]['result']['checkpoint'].__setitem__('sha256','f'*64))
    def test_unknown_business_key_drift_rejected(self):
        def mutate(cp):cp['snapshot_before']['future_observed_field']=1;cp['snapshot_after']['future_observed_field']=2
        self.reject_checkpoint_mutation(mutate)
    def test_added_snapshot_key_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('unknown_new_field',None))
    def test_nonwhitelisted_diagnostic_change_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1'].__setitem__('ready',not cp['snapshot_after']['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['ready']))
    def test_revision_jump_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('revision',5))
    def test_snapshot_alias_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after'].__setitem__('snapshot_id','synthetic:2'))
    def test_last_submission_mismatch_rejected(self):self.reject_checkpoint_mutation(lambda cp:cp['snapshot_after']['last_checkpoint_submission'].__setitem__('sequence',2))
    def test_next_save_sequence_and_history_prefix_required(self):
        d=fixture();cp=d['checkpoint'];old_command=deepcopy(cp['snapshot_after']['native_command_history'][0])
        cp['snapshot_before']['native_command_history']=[deepcopy(old_command)]
        cp['snapshot_before']['last_checkpoint_submission']=deepcopy(cp['snapshot_after']['last_checkpoint_submission'])
        cp['result']['submission']['sequence']=2;cp['result']['checkpoint']['history_index']=2
        cp['snapshot_after']['last_checkpoint_submission']={**cp['result']['submission'],'status':'submitted'}
        cp['snapshot_after']['native_command_history']=[old_command,{'index':2,'command':'save-checkpoint','ok':True,'result':deepcopy(cp['result'])}]
        self.assertEqual(transition.bind_checkpoint_transition(cp,d['provenance'])[1]['submission_sequence'],2)
        cp['snapshot_after']['native_command_history'][0]['ok']=False
        with self.assertRaises(strict.QualificationError):transition.bind_checkpoint_transition(cp,d['provenance'])
    def test_full_synthetic_seam_joins_only_after_and_preserves_credit_boundary(self):
        d=fixture();before=json.dumps(d,sort_keys=True);out=convert(d)
        self.assertEqual(out['schema'],'lyd.sdk-checkpoint-qualified-native.v2')
        self.assertEqual(out['G2_status'],'BOUND_COMPLETE_NATIVE_OBSERVATION')
        self.assertEqual(out['runtime_binding']['queried_revision'],4);self.assertEqual(out['runtime_binding']['queried_native_revision'],8)
        self.assertEqual(out['native_predicates']['identity']['revision'],8)
        self.assertIsNone(out['actual_pass']);self.assertIsNone(out['formal_mandate_credit']);self.assertFalse(out['business_postcondition_verified'])
        self.assertEqual(json.dumps(d,sort_keys=True),before)
    def test_G2_query_bound_to_before_is_rejected(self):
        d=fixture();binding=seam.frame_binding(d['checkpoint']['snapshot_before'])
        d['g2']['result']=seam.sdk.project_native_query(f.envelope('assembly_predicates',binding),binding,'assembly_predicates')
        with self.assertRaises(seam.QualificationError):convert(d)
    def test_G3_query_bound_to_before_is_rejected(self):
        d=fixture();binding=seam.frame_binding(d['checkpoint']['snapshot_before'])
        d['g3']['result']=seam.sdk.project_native_query(f.envelope('religious_title',binding),binding,'religious_title')
        with self.assertRaises(seam.QualificationError):convert(d)
    def test_saved_state_native_before_revision_is_rejected(self):
        d=fixture();d['state']['identity']['revision']=7
        with self.assertRaises(seam.QualificationError):convert(d)
    def test_actual_metadata_and_frozen_contract_metadata_are_distinct(self):
        d=fixture();out=convert(d)
        self.assertEqual(out['runtime_binding']['sdk_metadata_sha256'],metadata['sha256'])
        self.assertEqual(out['runtime_binding']['sdk_metadata_contract_sha256'],seam.SDK_METADATA_SHA)
        self.assertNotEqual(metadata['sha256'],seam.SDK_METADATA_SHA)
        d['provenance']['sdk_metadata_artifact']['sha256']=seam.SDK_METADATA_SHA
        with self.assertRaises(seam.QualificationError):convert(d)

class ArtifactLineageTests(unittest.TestCase):
    def codec_source(self, raw):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        path=Path(td.name)/'actual_codec.py';path.write_bytes(raw)
        return descriptor(path)
    def metadata_source(self, rows):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        path=Path(td.name)/'factory_metadata.json';path.write_text(json.dumps(rows),encoding='utf-8')
        return descriptor(path)
    def test_actual_full_codec_sha_and_frozen_contract_sha_remain_distinct(self):
        out=convert(fixture());binding=out['runtime_binding']
        self.assertEqual(binding['sdk_codec_sha256'],codec['sha256'])
        self.assertNotEqual(binding['sdk_codec_sha256'],binding['sdk_codec_contract_sha256'])
        self.assertEqual(binding['sdk_codec_contract_sha256'],seam.SDK_CODEC_SHA)
        self.assertEqual(len(binding['sdk_codec_DTO_AST']['pure_DTO_AST_matches']),12)
        self.assertTrue(binding['sdk_codec_DTO_AST']['all_12_match'])
        self.assertFalse(binding['sdk_codec_DTO_AST']['source_executed'])
    def test_changed_DTO_signature_rejected(self):
        raw=Path(codec['path']).read_bytes().replace(b'def project_native_query(raw,binding,operation,expected_build=None):',b'def project_native_query(raw,binding,operation,expected_build=None,faith_full_ids=None):')
        desc=self.codec_source(raw)
        with self.assertRaisesRegex(ValueError,'project_native_query'):
            lineage.verify_codec_artifact(desc,desc['sha256'])
    def test_changed_DTO_body_or_added_branch_rejected(self):
        raw=Path(codec['path']).read_bytes().replace(b"if operation not in OPERATIONS:raise ValueError",b"if operation=='challenger_graph':return None\n    if operation not in OPERATIONS:raise ValueError")
        desc=self.codec_source(raw)
        with self.assertRaisesRegex(ValueError,'project_native_query'):
            lineage.verify_codec_artifact(desc,desc['sha256'])
    def test_duplicate_or_missing_pure_DTO_function_rejected(self):
        raw=Path(codec['path']).read_bytes()
        for changed in (raw+b'\n\ndef integer(value, low, high, label):\n    return value\n',raw.replace(b'def integer(',b'def renamed_integer(')):
            desc=self.codec_source(changed)
            with self.assertRaises(ValueError):lineage.verify_codec_artifact(desc,desc['sha256'])
    def test_codec_declared_SHA_or_artifact_bytes_mismatch_rejected(self):
        with self.assertRaises(ValueError):lineage.verify_codec_artifact(codec,seam.SDK_CODEC_SHA)
        wrong=deepcopy(codec);wrong['sha256']='0'*64
        with self.assertRaises(ValueError):lineage.verify_codec_artifact(wrong,wrong['sha256'])
    def test_codec_source_is_parsed_without_executing_top_level_code(self):
        desc=self.codec_source(Path(codec['path']).read_bytes()+b'\nraise RuntimeError("MUST_NOT_EXECUTE")\n')
        result=lineage.verify_codec_artifact(desc,desc['sha256'])
        self.assertTrue(result['all_12_match']);self.assertFalse(result['source_executed'])
    def test_codec_AST_uses_the_exact_verified_buffer(self):
        raw=Path(codec['path']).read_bytes();desc=self.codec_source(raw);path=Path(desc['path'])
        original=Path.read_bytes
        def change_after_read(p):
            data=original(p)
            if p==path:p.write_bytes(b'raise RuntimeError("changed after verified read")')
            return data
        with patch.object(Path,'read_bytes',change_after_read):result=lineage.verify_codec_artifact(desc,desc['sha256'])
        self.assertEqual(result['actual_sha256'],hashlib.sha256(raw).hexdigest());self.assertTrue(result['all_12_match'])
    def test_current24_metadata_records_actual_count_and_SHA(self):
        d=fixture();rows=json.loads(Path(metadata['path']).read_bytes());graph=deepcopy(rows[-1]);graph['name']=lineage.GRAPH_TOOL_NAME;rows.append(graph)
        desc=self.metadata_source(rows);d['provenance']['sdk_metadata_artifact']=desc;d['provenance']['sdk_metadata_sha256']=desc['sha256']
        out=convert(d);self.assertEqual(out['runtime_binding']['sdk_metadata_tool_count'],24)
        self.assertEqual(out['runtime_binding']['sdk_metadata_sha256'],desc['sha256'])
        self.assertNotEqual(desc['sha256'],seam.READONLY23_METADATA_REFERENCE_SHA)
        self.assertIsNone(out['actual_pass']);self.assertIsNone(out['formal_mandate_credit'])
    def test_changed_G2_G3_Tool_schema_rejected(self):
        d=fixture();rows=json.loads(Path(metadata['path']).read_bytes())
        row=next(row for row in rows if row['name']=='ck3_query_profile_confucian_assembly_predicates_v1')
        row['inputSchema']['properties']['expected_revision']['exclusiveMinimum']=1
        desc=self.metadata_source(rows);d['provenance']['sdk_metadata_artifact']=desc;d['provenance']['sdk_metadata_sha256']=desc['sha256']
        with self.assertRaisesRegex(seam.QualificationError,'Tool metadata differs'):convert(d)
    def test_unrecognized_metadata_tool_set_or_duplicate_name_rejected(self):
        original=json.loads(Path(metadata['path']).read_bytes())
        rows=deepcopy(original);rows[-1]['name']='invented_extra_tool';desc=self.metadata_source(rows)
        with self.assertRaises(ValueError):lineage.verify_metadata_artifact(rows,desc,desc['sha256'])
        rows=deepcopy(original);rows[-1]['name']=rows[0]['name'];desc=self.metadata_source(rows)
        with self.assertRaisesRegex(ValueError,'duplicate'):lineage.verify_metadata_artifact(rows,desc,desc['sha256'])
    def test_bound_codec_artifact_cannot_claim_frozen_SHA_as_actual(self):
        d=fixture();d['provenance']['sdk_codec_sha256']=seam.SDK_CODEC_SHA
        with self.assertRaises(seam.QualificationError):convert(d)

if __name__=='__main__':unittest.main(verbosity=2)
