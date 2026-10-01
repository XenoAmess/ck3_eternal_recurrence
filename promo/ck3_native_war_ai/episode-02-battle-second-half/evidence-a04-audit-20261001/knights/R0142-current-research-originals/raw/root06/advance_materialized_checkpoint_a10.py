"""Arm against the actual current save submission, then submit exactly one day."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_current_checkpoint_advance',ROOT/'scoped_ui_research_a08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bindings=ROOT/'current-run-bindings.json';config=m.read(bindings)
live,output,evidence,transport,steps=m.bind(config)
m.require(not (evidence/'one-day-intent.json').exists(),'A game-day intent already exists; never repeat a submitted day')
m.require((evidence/'variable-monitor-begin.json').is_file() and not (evidence/'variable-monitor-finish-intent.json').exists(),'Independent observer must remain armed')
review=m.read(evidence/'before-ui-root-review.json');m.require(review['original_pixels_actually_reviewed'] is True,'Root original inspection required')
for image in review['reviewed_images']:m.require(m.identity(image['path'])==image,'Reviewed original bytes changed')
pair_path=evidence/'before-saved-pair.json';pair=m.read(pair_path)
save=pair['save_body'];submission=save['submission'];checkpoint=save['checkpoint']
sequence=submission['sequence']
m.require(type(sequence) is int and sequence>0 and save['accepted'] is True and checkpoint['status']=='saved' and save['materialization']['available'] is True,'No actual materialized checkpoint submission')
m.require(submission['date_raw']==checkpoint['date_raw']==config['before_date_raw'] and checkpoint['episode_run_id']==config['native_session_binding']['episode_run_id'],'Checkpoint is not this actual paused source')
m.require(m.identity(pair['immutable']['path'])==pair['immutable'],'Immutable before save changed')
m.require(m.identity(checkpoint['path'])['sha256']==pair['immutable']['sha256'],'Current checkpoint bytes do not match immutable before save')
prior_path=output/'interactive-requests-responses/scoped-chain-begin.json'
prior=m.read(prior_path)
m.require(prior['result']=='RED' and 'current materialized checkpoint and idle session' in str(prior.get('error')),'Previous admission outcome differs; independently diagnose')
prior_request=m.read(output/'interactive-requests/scoped-chain-begin.json')
m.require(prior_request['checkpoint_sequence']!=sequence,'Previous admission was not an obsolete sequence')
start,sr,values=m.snapshot(output,transport,steps,'scoped-a09-day-source',config['before_date_raw'])
m.require(all(values[key]==value for key,value in pair['source_values'].items() if key!='revision') and values['revision']==prior_request['expected_revision'],'Current native source/session changed after save, or provider revision differs from actual rejected request')
token=config['managed_daily_sequence_token']
parameters={'action':'private_phase_trace','step':'experimental-combat-phase-event-trace-begin-v1',
    'expected_revision':values['revision'],'combat_id':config['combat_id'],'managed_daily_sequence_token':token,
    'checkpoint_sequence':sequence,'capture_runtime_scoped_chain':True,'scoped_character_id':config['victim_id'],
    'scoped_related_character_id':config['killer_id'],'scoped_event_load_index':config['event_load_index']}
m.write(evidence/'actual-checkpoint-trace-readmission-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),
    'consumer':m.identity(Path(__file__)),'prior_rejected_admission':m.identity(prior_path),
    'actual_saved_pair':m.identity(pair_path),'actual_checkpoint_sequence':sequence,'parameters':parameters,
    'prior_GAME_DAY_was_not_submitted':True,'old_rejected_attempt_kept_RED':True})
begun,br=steps.private_call(output,'scoped-a09-chain-begin',parameters,120)
m.require(begun.get('accepted') is True and begun.get('managed_daily_sequence_token')==token,'Actual checkpoint trace admission refused; no game day')
m.write(evidence/'one-day-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'source_values':values,
    'source_snapshot':sr,'token':token,'trace_begin':br,'trace_begin_body':begun,'actual_checkpoint_sequence':sequence,
    'advance_consumer':m.identity(Path(__file__)),'at_most_one_day':True})
changed,dr=transport.call(output,'scoped-a09-one-day','ck3_execute_step',{'step':'life-advance','expected_revision':values['revision']},150)
m.require(changed.get('ending_date_raw')==config['after_date_raw'],'Single submitted day ambiguous; no retry')
end,er,ev=m.snapshot(output,transport,steps,'scoped-a09-post-day-snapshot-only',config['after_date_raw'])
finished,tr=steps.private_call(output,'scoped-a09-chain-finish-once',{'action':'private_phase_trace',
    'step':'experimental-combat-phase-event-trace-finish-v1','expected_revision':ev['revision'],
    'combat_id':config['combat_id'],'managed_daily_sequence_token':token},120)
m.write(evidence/'one-day-finished.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'one_day':dr,'one_day_body':changed,
    'post_day_snapshot':er,'post_day_values':ev,'trace_finish':tr,'trace_finish_body':finished,
    'source_binding':m.identity(bindings),'advance_consumer':m.identity(Path(__file__)),
    'complete_causal_chain':'pending independent raw records/save verification'})
print(json.dumps({'result':'ONE_ORIGINAL_DAY_AND_TRACE_FINISH_RETURNED_PENDING_VERIFICATION','actual_checkpoint_sequence':sequence,'values':ev}))
