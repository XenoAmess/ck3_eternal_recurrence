"""First common allocation after a closed legacy managed-session bootstrap.

This admits resource closure, not old profile-MCP typed-exit or business credit.
The public allocator still enforces empty shared history and a single machine chain.
"""
from datetime import datetime
from pathlib import Path
import json,subprocess

SCHEMA='ck3-mod-acceptance-first-managed-bootstrap-v2'
MODE='first-machine-legacy-managed-session-closure'
def require(ok,message):
    if not ok:raise ValueError(message)

def validate_originals(values,binding,history,events,tasks,previous_release):
    from ck3_mod_acceptance_allocate import native_cleanup_closed
    context,boot,release=(values[k] for k in ('allocation_context','bootstrap_result','screen_release'))
    identity=context['identity'];session=boot['session'];shutdown=session['shutdown'];keeper=boot['screen_lease']
    require(identity in history and identity['machine_id']==binding['machine_id']==context['machine_id']==boot['machine_id']==session['machine_id'],
        'legacy managed identity absent/crossed actual canonical machine history')
    require(context['run_id']==identity['run_id'] and identity['mod_key']=='vanilla','legacy managed run identity differs')
    require(datetime.fromisoformat(identity['allocated_at_utc'])<datetime.fromisoformat(session['started_at'])<datetime.fromisoformat(session['finished_at']),
        'legacy managed original time ordering differs')
    require(session['exit_reason']=='process_exit' and type(session['process_exit_code']) is int and session['process_exit_code']==0 and
        session['ok'] is True and session['error'] is None and type(session['pid']) is int and session['pid']>0 and
        session['pid']==shutdown['ck3_pid'] and shutdown['ck3_exit_code']==0 and
        native_cleanup_closed({'session':{'report':session}}),'legacy managed original Popen/job/tree/control cleanup not closed0')
    require(boot['sdk_error'] is None and boot['sdk_thread_exited'] is True and boot['supervisor_error'] is None and
        keeper['thread_exited'] is True and keeper['failure'] is None,'legacy managed SDK/supervisor/keeper not closed')
    require(release['machine_id']==binding['machine_id'] and release['run_id']==identity['run_id'] and release['exit_code']==0 and
        release['task_done_resources_empty'] is True and release['normal_exit_zero'] is True and release['game_exit_code']==0,
        'legacy managed actual release does not bind this normal0 scene')
    packet=json.loads(release['stdout']);task=packet['task']
    require(task['task_id']==keeper['task_id'] and task['resources']==[] and task['state'] in ('done','waiting') and
        task['last_sequence']>keeper['last_sequence'],'legacy managed released task mismatch')
    matched=[t for t in tasks if t.get('task_id')==task['task_id']]
    require(len(matched)==1 and matched[0]['last_sequence']==task['last_sequence'] and matched[0]['resources']==[] and
        matched[0]['state'] in ('done','waiting'),'fresh actual bus task differs from original release')
    before=[e for e in events if e.get('task_id')==task['task_id'] and e.get('sequence')==keeper['last_sequence']]
    after=[e for e in events if e.get('task_id')==task['task_id'] and e.get('sequence')==task['last_sequence']]
    require(len(before)==len(after)==1 and before[0]['resources']==['ck3-screen:acquired'] and
        after[0]['resources']==[] and after[0]['state'] in ('done','waiting'),'durable managed screen ownership/release chain missing')
    closed=datetime.fromisoformat(task['updated_at_utc'])
    require(all(datetime.fromisoformat(row['allocated_at_utc'])<=closed for row in history),
        'later canonical identity exists; use its actual closure')
    return {'mode':MODE,'legacy_run_id':identity['run_id'],'legacy_task':task['task_id'],
        'legacy_managed_original_process_exit_zero':True,'legacy_shared_runtime_qualified':False,
        'old_profile_typed_normal0_claimed':False,'business_pass':False,'fresh_release_task':matched[0],
        'release_event':after[0],'machine':binding}

def validate_bootstrap(bundle,selection,binding,bus_events,bus_packet,previous_release):
    from ck3_mod_acceptance_allocate import pin,check_pin,read_json,machine_id_history
    require(bundle.get('schema')==SCHEMA and bundle.get('machine')==binding,'managed bootstrap schema/machine differs')
    require(bundle['runtime_config']==pin(selection.runtime_path) and bundle['runtime_manifest']==pin(selection.manifest_path) and
        Path(bundle['repo_root']).resolve()==selection.locations['repo_root'].resolve(),'managed bootstrap common runtime differs')
    archive=Path(bundle['legacy_archive_index']['path']).resolve();check_pin(archive,bundle['legacy_archive_index'])
    require(archive.is_relative_to(selection.locations['repo_root'].resolve()),'managed legacy archive must be tracked in checkout')
    subprocess.run(['git','ls-files','--error-unmatch','--',str(archive)],cwd=selection.locations['repo_root'],capture_output=True,check=True)
    index=read_json(archive);archived={r['source']['path'].replace('\\','/').lower():r['source'] for r in index['evidence_entries']}
    refs=bundle['legacy_managed_closure'];require(set(refs)=={'allocation_context','bootstrap_result','screen_release'},'managed original reference set differs')
    require(Path(previous_release).resolve()==Path(refs['screen_release']['path']).resolve(),'previous-release must name actual managed release')
    values={}
    for key,ref in refs.items():
        check_pin(Path(ref['path']),ref)
        require(archived.get(ref['path'].replace('\\','/').lower())==ref,'managed original not preserved in tracked index')
        values[key]=read_json(Path(ref['path']))
    require(values['screen_release']['bootstrap_result']==refs['bootstrap_result'],
        'managed release does not pin the exact original bootstrap result')
    history,history_files=machine_id_history(binding)
    result=validate_originals(values,binding,history,bus_events,bus_packet['tasks'],previous_release)
    return {**result,'archive_index':bundle['legacy_archive_index'],'original_evidence':refs,
        'canonical_id_history':history_files,'bootstrap':pin(Path(bundle['_bundle_path']))}
