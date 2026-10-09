"""Original independent QOL cells; launch, identity and cleanup stay shared."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

from ck3_mod_acceptance_prepare import materialize_fixture_profile, pin, write_json
from .xqol_scope import parse_song_scope

QR = {'begin':'ZQR120QUAL: SCOPE BEGIN actual_song_actor_D0',
      'pass':'ZQR120QUAL: TEST PASS actual_song_actor_D0',
      'end':'ZQR120QUAL: SCOPE END actual_song_actor_D0',
      'fail':'ZQR120QUAL: TEST FAIL actual_song_actor_D0'}


def require(value, message):
    if not value: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def base(context):
    return Path(__file__).parent / context['case_contract']['data_directory']


def validate_contract(context):
    c=context['case_contract']
    require(c['schema']=='ck3-xqol-original-followup-case-v1' and c['case']==context['case'],
            'Original independent QOL case differs')
    require(context['case_spec']['budgets']==c['original_budgets'], 'Original QOL wall-clock bounds changed')
    for relative, expected in c['support_files'].items():
        path=Path(__file__).parent / relative
        actual=pin(path)
        require(all(actual[k]==expected[k] for k in ('bytes','sha256')), 'Original case support changed: '+relative)


def observe(raw, required, forbidden, complete=True):
    require(len(raw)<=64*1024*1024, 'Original bounded debug log exceeded')
    text=raw.decode('utf-8-sig',errors='replace')
    counts={'required':{m:text.count(m) for m in required},
            'forbidden':{m:text.count(m) for m in forbidden}}
    require(all(v==0 for v in counts['forbidden'].values()) and
            all(v<=1 for v in counts['required'].values()), 'Original FAIL/duplicate observed; never replay')
    if complete: require(all(v==1 for v in counts['required'].values()), 'Original required marker missing')
    return counts


def song_scope(raw):
    proof=parse_song_scope(raw, {'scope_name':'xqol_startup_actor','markers':QR})
    require(proof is not None, 'Original actual Song scope proof missing')
    return proof


def admit_startup_event(context, snapshot, event_context):
    """Original QR scope-bound first intro, without large raw hex transport."""
    path=Path(context['state_dir'])/'profile/logs/debug.log'
    proof=song_scope(path.read_bytes())
    actor=snapshot.get('played_character',{})
    require(actor.get('source')=='native' and actor.get('alive') is True and
            actor.get('character_id')==proof['runtime_character_id'], 'Original Song intro actor differs')
    event=snapshot.get('active_event',{})
    require(event.get('source')=='native' and type(event.get('instance_id')) is int and
            event['instance_id']==1 and event.get('option_count')==1, 'Original sole first intro changed')
    options=event.get('options',[])
    require(len(options)==1 and options[0].get('enabled') is True and
            options[0].get('option_number')==1 and options[0].get('index')==0, 'Original intro option unavailable')
    typed=event_context.get('current_event_window_context',{})
    identity=typed.get('root_scope',{}).get('typed_identity',{})
    require(event_context.get('status')=='available' and event_context.get('current_event_window_context_ready') is True and
            typed.get('schema')=='current-event-window-context-v1' and typed.get('schema_version')==1 and
            typed.get('status')=='available' and typed.get('window_match_count')==1 and
            typed.get('current_event_instance_id')==1 and typed.get('snapshot_revision')==snapshot['native_revision'] and
            typed.get('date_raw')==snapshot['date_raw'] and identity.get('status')=='available' and
            identity.get('kind')=='character' and identity.get('character_id')==actor['character_id'],
            'Original typed intro owner/revision/date differs')
    options=typed.get('options',[])
    require(len(options)==1 and all(options[0].get(k)==v for k,v in
        {'rendered_index':0,'native_option_index':0,'shown':True,'enabled':True,'fallback':False,'cancel':False}.items()),
        'Original typed sole intro option differs')
    compact={k:v for k,v in proof.items() if k!='raw_scope_block_hex'}
    compact['source_debug_log']=str(path)
    return {'event_instance_id':1,'option_number':1,'proof':compact,'business_pass':False}


def stock_reward_projection(stock_raw, wrapper_raw):
    """Select the stock filename, retaining every original reward effect body."""
    from xqol_vanilla_contract import block
    text=stock_raw.decode('utf-8-sig');wrapped=wrapper_raw.decode('utf-8-sig')
    projected=text;definitions=[]
    keys=('conversion_tenet_acts_of_the_apostles_effect','conversion_tenet_mendicant_preachers_effect')
    for key in keys:
        original=block(text,key);observed=block(wrapped,key)
        body=original[original.index('{')+1:-1]
        require(observed.count(body)==1, 'Original stock reward body differs: '+key)
        require(projected.count(original)==1, 'Original stock reward definition ambiguous: '+key)
        projected=projected.replace(original,observed,1)
        definitions.append({'effect':key,'original_reward_body_byte_exact':True,
                            'stock_block_sha256':hashlib.sha256(original.encode('utf-8')).hexdigest()})
    inverse=projected
    for key in keys:inverse=inverse.replace(block(wrapped,key),block(text,key),1)
    require(inverse==text, 'Original stock file inverse projection differs')
    prefix=b'\xef\xbb\xbf' if stock_raw.startswith(b'\xef\xbb\xbf') else b''
    return prefix+projected.encode('utf-8'), {'definitions':definitions,'all_other_definitions_byte_exact':True,
        'inverse_entire_stock_file_byte_exact':True,'actual_loaded_callback_still_required':True}


def prepare_case(context, song=True):
    validate_contract(context)
    c=context['case_contract']; source=base(context); output=Path(context['output'])
    fixture=output/'original-case-fixture'; fixture.mkdir()
    changes=[]
    for relative in c['fixture_files']:
        original=(source/'fixture'/relative).read_bytes()
        raw=original
        if relative=='common/scripted_effects/zqp_reward_observer_wrappers.txt':
            expected=c['vanilla_reward_source'];path=Path(context['game_dir'])/'game'/expected['relative']
            actual=pin(path)
            require(all(actual[k]==expected[k] for k in ('bytes','sha256')), 'Reviewed stock reward source changed')
            stock_raw=path.read_bytes()
            require(len(stock_raw)==expected['bytes'] and hashlib.sha256(stock_raw).hexdigest()==expected['sha256'],
                    'Reviewed stock reward source changed during read')
            raw,projection=stock_reward_projection(stock_raw,original)
            changes.append({'source_wrapper':relative,'materialized_relative':expected['relative'],
                            'actual_stock_source':actual,'projection':projection})
            relative=expected['relative']
        if relative=='descriptor.mod':
            raw=re.sub(rb'(?m)^(supported_version\s*=\s*")1\.20\.0\.3(")',
                       lambda m:m[1]+context['shared_game']['version'].encode('ascii')+m[2],raw)
        target=fixture/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        if relative=='descriptor.mod' and raw!=original:changes.append({'path':relative,'kind':'fixture_descriptor_current_shared_version_only',
                                        'original_sha256':hashlib.sha256(original).hexdigest(),'current':pin(target)})
    profile=materialize_fixture_profile(context,fixture,context['case_inputs']['product_dir'],
                                         context['case_inputs']['plain_configuration'])
    actual={k.removeprefix('mod-content/product/'):v for k,v in profile['files'].items() if k.startswith('mod-content/product/')}
    expected=context['case_inputs']['formal_product_files']
    require(len(actual)==len(expected)==27 and set(actual)==set(expected) and
            all(all(actual[k][f]==expected[k][f] for f in ('bytes','sha256')) for k in expected),
            'Existing exact formal27 required; no release builder is run')
    startup={'mode':'fixture','state_dir':profile['state_dir'],'fixture_start_policy':profile['fixture_start_policy']}
    if (source/'frontend-rules-plan.json').is_file():
        rules=output/'frontend-rules-plan.json';shutil.copyfile(source/'frontend-rules-plan.json',rules)
        startup['frontend_rules_plan']=pin(rules)
    if song:
        handler=pin(Path(__file__));handler['function']='admit_startup_event'
        dependencies=[pin(p) for p in (Path(__file__).with_name('xqol_scope.py'),
            Path(__file__).parent.parent/'ck3_mod_acceptance_prepare.py',Path(__file__).with_name('__init__.py'))]
        hook=output/'frontend-fixture-startup-case-contract.json'
        write_json(hook,{'schema':'ck3-frontend-fixture-startup-case-contract-v1','state_dir':context['state_dir'],
                         'handler':handler,'dependencies':dependencies})
        startup['startup_case_contract']=pin(hook)
    steps, metadata=bind_plan(context)
    for step in steps:
        if step.get('kind')=='advance_day' and step.get('expect',{}).get('one_life_identity_claimed') is False:
            step['expect'].pop('one_life_identity_claimed')
            metadata.append({'step':step['id'],'kind':'legacy_no_one_life_claim_proved_by_full_native_campaign_frames'})
        if step.get('tool'):step['fresh_revision']=True
    initial=output/'initial-plan.json'
    write_json(initial,{'steps':[{'id':'qolf-anchor','tool':'ck3_take_snapshot',
        'args':{'include_native_command_history':False},'fresh_revision':True}]+steps})
    return {'startup':startup,'initial_plan':pin(initial),'profile':profile,'fixture_metadata_changes':changes,
            'initial_plan_original_business':True,'original_plan_metadata_projection':metadata,
            'formal_product_unchanged':True,'original_case':c['case'],'runtime_status':'NOT_RUN','business_pass':False}


def at(value, path):
    for part in path.split('.'):
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def check_expected(value, expected, results):
    for key,wanted in expected.items():
        if isinstance(wanted,dict) and set(wanted)=={'$ref'}:
            reference=wanted['$ref'];require(reference.startswith('results.'),'Unknown original reference domain')
            wanted=at(results,reference[8:])
        actual=at(value,key)
        require(type(actual) is type(wanted) and actual==wanted, 'Original expected value differs: '+key)


def bind_plan(context):
    c=context['case_contract'];plan=read(base(context)/'original-plan.json');changes=[]
    def visit(value):
        if isinstance(value,dict):
            if set(value)=={'$ref'} and value['$ref'].startswith('results.qol-startup-scope-actor-binding.'):
                old=value['$ref'];tail=old.rsplit('.',1)[1]
                paths={'runtime_character_id':'played_character.character_id','bridge_pid':'diagnostics.bridge_pid',
                       'connection_generation':'diagnostics.connection_generation','date_raw':'date_raw'}
                new='results.qolf-anchor.'+paths[tail];changes.append({'from':old,'to':new})
                return {'$ref':new}
            return {k:visit(v) for k,v in value.items()}
        if isinstance(value,list):return [visit(v) for v in value]
        return value
    steps=visit(copy.deepcopy(plan['steps']))
    for step in steps:
        expected=step.get('expect',{})
        if expected.get('provenance.game_version')=='1.20.0.3':
            expected['provenance.game_version']=context['shared_game']['version']
            changes.append({'step':step['id'],'kind':'one_shared_runtime_version_provenance'})
        if step.get('tool')=='ck3_query_engine_log_literals_v1':
            for key in list(expected):
                match=re.fullmatch(r'matches\.(\d+)\.literal',key)
                if match and expected[key]!=step['args']['literals'][int(match[1])]:
                    old=expected[key];expected[key]=step['args']['literals'][int(match[1])]
                    changes.append({'step':step['id'],'field':key,'from':old,'to':expected[key],'kind':'stale_ordinary_async_label_only'})
    return steps,changes


def run_plan(context,client):
    c=context['case_contract'];steps,changes=bind_plan(context)
    require(len(steps)==c['original_step_count'], 'Original step count changed')
    report=client.read_report()
    def actual(identifier):
        found=[r for r in report.get('steps',[]) if r.get('id')==identifier]
        require(len(found)==1 and found[0].get('finished_at'), 'Original initial step absent/duplicate/unfinished: '+identifier)
        return found[0]
    anchor=actual('qolf-anchor')
    require(anchor.get('ok') is True and not anchor.get('error'), 'Original anchor unavailable')
    frame=client.validate_frame(anchor['result']);results={'qolf-anchor':frame};rows=[];days=0
    if c.get('song_scope_required'):
        require(frame['played_character']['character_id']==song_scope(client.log_bytes())['runtime_character_id'],
                'Original framed Song differs from actual full native player')
    for step in steps:
        identifier=step['id']
        row=actual(identifier)
        require(row.get('ok') is True or step.get('continue_on_error') is True, 'Original case step failed')
        if step.get('kind')=='advance_day':
            require(step.get('days')==1 and days<c['maximum_natural_days'], 'Original one-day cap changed')
            days+=1
            expected=copy.deepcopy(step.get('expect',{}))
            # The current shared full-frame native_campaign contract proves this
            # legacy metadata claim, without inventing a returned raw field.
            if expected.get('one_life_identity_claimed') is False:
                expected.pop('one_life_identity_claimed')
                require(row['result']['before']['episode_projection']==row['result']['after']['episode_projection']=='native_campaign',
                        'Original no-one-life identity boundary changed')
            check_expected(row['result'],expected,results)
            before=client.validate_frame(row['result']['before'])
            after=client.validate_frame(row['result']['after'])
            elapsed=row['result'].get('elapsed_hours')
            require(type(elapsed) is int and 24<=elapsed<48 and after['date_raw']-before['date_raw']==elapsed,
                    'Original complete natural day interval differs')
        else:
            check_expected(row['result'],step.get('expected',{}),results)
        if row.get('ok') is True:
            check_expected(row['result'],{} if step.get('kind')=='advance_day' else step.get('expect',{}),results)
        results[identifier]=row.get('result');rows.append({'original_id':identifier,'actual_row':row})
        observe(client.log_bytes(),c['required_markers'],c['forbidden_markers'],False)
    final=client.snapshot()
    require(final['played_character']['character_id']==frame['played_character']['character_id'] and
            0<=final['date_raw']-frame['date_raw']<24*(c['maximum_natural_days']+1), 'Original actor/date cap changed')
    return {'rows':rows,'before':frame,'after':final,'natural_days':days,'metadata_rebindings':changes}


def preserve_result(context,client,result,gui=True):
    c=context['case_contract'];raw=client.log_bytes();counts=observe(raw,c['required_markers'],c['forbidden_markers'])
    debug=Path(context['output'])/'original-debug.raw'
    with debug.open('xb') as stream:stream.write(raw)
    errors=client.log_bytes('error.log');error=Path(context['output'])/'original-error.raw'
    with error.open('xb') as stream:stream.write(errors)
    names=[Path(p).name for p in c['fixture_files'] if p!='descriptor.mod']
    names+=['xqol_events.txt','xqol_effects.txt','xqol_prison_payment_effects.txt','xqol_conversion_effects.txt']
    affected=[line for line in errors.decode('utf-8-sig',errors='replace').splitlines() if any(n in line for n in names)]
    require(not affected, 'Actual fixture/product error-log entries require classification: '+str(affected[:8]))
    result.update(run_id=context['run_id'],case=context['case'],debug_original=pin(debug),error_original=pin(error),
        counts=counts,error_classification={'fixture_or_product_entries':affected,'all_other_errors_preserved':True},
        case_contract_qualified=True,gui_contract_qualified=gui,business_contract_applicable=False,business_pass=False,
        product_release_pass=False,coverage=c['acceptance_scope'])
    if c.get('song_scope_required'):result['actual_song_scope']=song_scope(raw)
    client.checkpoint('qol-original-followup-result',result)
    return result


def verify_case(context):
    validate_contract(context)
    path=Path(context['output'])/'qol-original-followup-result.json'
    if not path.is_file():return {'case_contract_qualified':False,'gui_contract_qualified':False,'business_pass':False,'status':'NOT_RUN'}
    result=read(path);c=context['case_contract']
    require(result['run_id']==context['run_id'] and result['case']==context['case'],'Original case result crossed run')
    for key in ('debug_original','error_original'):
        require(pin(result[key]['path'])==result[key], 'Original evidence changed: '+key)
    require(observe(Path(result['debug_original']['path']).read_bytes(),c['required_markers'],c['forbidden_markers'])==result['counts'],
            'Original marker observation changed')
    for row in result.get('gui_evidence',[]):require(pin(row['path'])==row,'Original GUI evidence changed')
    return {**result,'business_contract_applicable':False,'business_pass':False,'product_release_pass':False}
