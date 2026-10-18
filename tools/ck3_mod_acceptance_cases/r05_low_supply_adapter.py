"""R05 case data adapter using the one common runtime and saved-game host.

No host/DLL selection and no launch here. The sole mod occupies the generic
common 'product' carrier slot but is explicitly a controlled research fixture.
"""
from pathlib import Path
import importlib.util,json,re,sys

def load(name,path):
    path=Path(path)
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    original=list(sys.path);sys.path.insert(0,str(path.parent))
    try:spec.loader.exec_module(module)
    finally:sys.path[:]=original
    return module

def script_preflight_scope(preflight,package,m,current_machine):
    """Admit the actually covered parser subset; preserve unsupported RED.

    The retained CLI's IR/runtime demo is a separate synthetic fixture. Only
    root_scan and the exact decision corpus are relevant to this initializer.
    """
    source_rows={r['relative_path']:r['sha256'] for r in package['files']}
    m.require(preflight.get('machine_id')==current_machine and
        preflight.get('corpus_sha256')==source_rows and preflight.get('ck3_exe_sha256')==m.EXE_SHA and
        type(preflight.get('open_kaishek_commit')) is str and re.fullmatch(r'[0-9a-fA-F]{40}',preflight['open_kaishek_commit']) is not None and
        preflight.get('profile_version') and preflight.get('actual_command') and
        type(preflight.get('unsupported_semantics')) is list and preflight['unsupported_semantics'],
        'AGENTS deterministic preflight is not bound to the actual fixture corpus/build')
    if preflight.get('status')=='PARSER_SYNTAX_ONLY_EXACT_CORPUS':
        ref=preflight['actual_parse_report'];m.require(m.pin(ref['path'])==ref,'actual parse-only report bytes changed')
        parsed=json.loads(Path(ref['path']).read_bytes())
        decision=next(r for r in package['files'] if r['relative_path'].startswith('common/decisions/'))
        m.require(preflight.get('actual_exit_code')==0 and parsed.get('status')=='PARSED' and
            parsed.get('bytes')==decision['bytes'] and parsed.get('diagnostics')==[] and parsed.get('roundTrip') is True and
            preflight.get('parsed_relative_path')==decision['relative_path'] and
            preflight.get('source_decision_sha256')==decision['sha256'], 'actual exact decision parse-only result differs')
        prior=preflight['prior_unsupported_validation'];m.require(m.pin(prior['path'])==prior,'historical unsupported validator evidence changed')
        prior_result=json.loads(Path(prior['path']).read_bytes());codes=prior_result.get('semanticCodes',[])
        m.require(prior_result.get('status')=='INVALID' and codes and all(c=='UNKNOWN_OPCODE' for c in codes) and
            preflight.get('semantic_validation_current_corpus')=='NOT_RUN_UNSUPPORTED_PROFILE_12004',
            'parse-only receipt must retain unsupported semantics and actual prior RED without reassigning its corpus')
        return 'exact_decision_parser_syntax_only_current_semantics_UNSUPPORTED_native_NOT_QUALIFIED'
    report_ref=preflight['actual_preflight_report'];m.require(m.pin(report_ref['path'])==report_ref,'actual parser report bytes changed')
    report=json.loads(Path(report_ref['path']).read_bytes())
    parser=report.get('root_scan',{}).get('parser',{});validator=report.get('root_scan',{}).get('validator',{})
    decision=next(row for row in package['files'] if row['relative_path'].startswith('common/decisions/'))
    m.require(report.get('schema')=='open_kaishek.preflight.v1' and parser.get('status')=='GREEN' and
        parser.get('diagnostics')==0 and parser.get('files')==1 and parser.get('bytes')==decision['bytes'],
        'actual decision root parser did not pass; no profile/launch preparation')
    if preflight.get('status')=='DETERMINISTIC_SCRIPT_SUBSET_PASSED':
        fingerprint=report.get('build_fingerprint',{})
        m.require(report.get('status')=='GREEN' and validator.get('status')=='GREEN' and
            fingerprint.get('version')=='1.20.0.4' and str(fingerprint.get('exe_sha256','')).lower()==m.EXE_SHA,
            'full offline pass lacks its actual exact4 profile/result')
        return 'covered_offline_subset_passed_not_native_effect_qualified'
    m.require(preflight.get('status')=='PARSER_SYNTAX_PASSED_VALIDATOR_UNSUPPORTED' and
        report.get('status')=='RED' and validator.get('status')=='RED','actual unsupported validator RED missing')
    validation_ref=preflight['actual_validate_report'];m.require(m.pin(validation_ref['path'])==validation_ref,'actual validator report bytes changed')
    validation=json.loads(Path(validation_ref['path']).read_bytes());codes=validation.get('semanticCodes',[])
    m.require(validation.get('status')=='INVALID' and validation.get('syntaxDiagnostics')==0 and
        codes and all(code=='UNKNOWN_OPCODE' for code in codes) and
        validation.get('semanticDiagnostics')==len(codes)==validator.get('diagnostics'),
        'validator failure is not solely an explicitly unsupported opcode surface')
    return 'parser_syntax_only_validator_RED_unsupported_native_semantics_NOT_QUALIFIED'

def prepare_case(context):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_prepare import materialize_product_profile,finish_product_profile,write_json,pin,checked_copy
    from xar_autoplayer.bridge import r05_low_supply_fixture as m
    inputs=context['case_inputs'];output=Path(context['output']);seed=context['saved_campaign']
    # Reuse the existing pure-vanilla checkpoint reader as a library, never its
    # historical bootstrap run path. This binds the exact original Save packet.
    repo=Path(context['shared_source_root'])
    bootstrap=load('r05_checkpoint_source_library',repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py')
    for field in ('normal_checkpoint_receipt','normal_checkpoint_build_receipt','open_kaishek_preflight'):
        row=inputs[field]
        m.require(pin(row['path'])==row,field+' exact pin changed')
    qualified=bootstrap.checkpoint_source(Path(seed['save']),Path(inputs['normal_checkpoint_receipt']['path']),
        Path(inputs['normal_checkpoint_build_receipt']['path']),bootstrap.game_target('1.20.0.4'),seed['player_id'])
    m.require(qualified is not None and qualified['actor_id']==seed['player_id'] and
        qualified['date_raw']==seed['date_raw'] and qualified['save']['bytes']==seed['bytes'] and
        qualified['save']['sha256']==seed['sha256'].lower(),'normal checkpoint actor/date/exact save does not match common startup')
    current_machine=current_machine_id()
    fixture=output/'generated-r05-fixture'
    package=m.generate_fixture(fixture,province_id=inputs['province_id'],machine_id=current_machine,
        fraction=inputs.get('supply_loss_fraction','0.999'),decision_key=inputs.get('decision_key','xar_r05_initialize_low_supply'))
    preflight=json.loads(Path(inputs['open_kaishek_preflight']['path']).read_bytes())
    for field in ('actual_preflight_report','actual_validate_report','actual_parse_report','prior_unsupported_validation'):
        if field in preflight:
            ref=preflight[field];path=Path(ref['path'])
            if not path.is_absolute():path=Path(inputs['open_kaishek_preflight']['path']).parent/path
            preflight[field]={**ref,'path':str(path.resolve())}
    offline_scope=script_preflight_scope(preflight,package,m,current_machine)
    profile=materialize_product_profile(context,fixture,inputs['plain_configuration'])
    mounted=m.common_mount_receipt(profile['profile'])
    finished=finish_product_profile(context,profile,provenance={
        'kind':'controlled-mechanism-research-fixture-in-common-content-carrier','research_fixture_mounted':True,
        'fixture_manifest':m.pin(fixture/'fixture-manifest.json'),'normal_checkpoint_library_result':qualified,
        'source_build_machine_id':json.loads(Path(inputs['normal_checkpoint_build_receipt']['path']).read_bytes()).get('machine_id','unknown'),
        'open_kaishek_preflight':inputs['open_kaishek_preflight'],
        'offline_qualification_scope':offline_scope,'native_script_effect_qualified':False,
        'natural_low_stock_proven':False,'starvation_casualty_proven':False})
    root_contract=output/'r05-root-prepared.json'
    write_json(root_contract,{'schema':'xar.r05-common-runtime-prepared.v1','machine_id':current_machine,
        'profile_dir':profile['profile'],'game':{'sha256':m.EXE_SHA},'r05_low_supply_fixture':mounted,
        'runtime_manifest':context['runtime_manifest'],'source_checkpoint':qualified,
        'research_fixture_mounted':True,'not_a_vanilla_or_product_business_run':True})
    initial=output/'initial-plan.json';write_json(initial,{'steps':[]})
    return {'machine_id':current_machine,'startup':{'mode':'saved_campaign','state_dir':profile['state_dir'],
            'saved_campaign':{**seed,'product_inventory':profile['product_inventory']['path']}},
        'initial_plan':pin(initial),'profile_preparation':finished,'files':profile['files'],
        'root_prepared':pin(root_contract),'research_fixture_mounted':True,
        'offline_qualification_scope':offline_scope,'native_script_effect_qualified':False,
        'runtime_status':'NOT_RUN','business_contract_applicable':True,'business_pass':False,'R05_pass':False}

class CommonRelay:
    """Adapt the existing held host's control queue; no second SDK client."""
    def __init__(self,context,client,machine):
        self.RUN=Path(context['run_dir']);self.CONTEXT={'machine_id':machine};self.client=client
    def snapshot(self,identifier):
        return self.client.snapshot()
    def request(self,identifier,tool,arguments):
        rows=self.client.execute_plan([{'id':identifier,'tool':tool,'args':arguments,'fresh_revision':False}],identifier)
        if len(rows)!=1 or rows[0].get('ok') is not True or rows[0].get('error'):
            raise RuntimeError('actual common control failed; inspect same request, never replay')
        return {'body':rows[0]['result']}

def run_case(context,client):
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge import r05_low_supply_fixture as m
    machine=current_machine_id();inputs=context['case_inputs'];client.retain_process()
    f=client.snapshot();process=client._process
    m.require(process and process['pid']==f['diagnostics']['bridge_pid'],'actual held OS/native process differs')
    prepared_path=Path(client.selection.prepared['preparation']['root_prepared']['path'])
    prepared=json.loads(prepared_path.read_bytes());m.require(m.pin(prepared_path)==client.selection.prepared['preparation']['root_prepared'],'prepared contract changed')
    actor=context['saved_campaign']['player_id'];province=inputs['province_id']
    candidates=[row for row in f.get('player_armies',[]) if row.get('owner_character_id')==actor and row.get('current_province_id')==province]
    m.require(len(candidates)==1,'current typed owner/location does not resolve exactly one Army')
    army_id=candidates[0]['army_id']
    relay=CommonRelay(context,client,machine)
    m.require_capabilities(relay.request('r05-locate-capabilities','ck3_get_capabilities',{})['body'])
    strength=relay.request('r05-locate-strengths','ck3_query_army_strengths',
        {'army_ids':[army_id],'expected_revision':f['revision'],'profile':'observed_history_full_v1'})['body']
    rows=[row for row in strength.get('army_strengths',[]) if row.get('army_id')==army_id]
    m.require(len(rows)==1,'current selected Strength identity missing/ambiguous')
    carmy_id=rows[0].get('native_carmy_id')
    m.integer(army_id,'current public Army ID',0);m.integer(carmy_id,'current CArmy ID',0)
    m.target_witness(f,strength,actor_id=actor,army_id=army_id,carmy_id=carmy_id,province_id=province)
    for key,actual in (('army_id',army_id),('carmy_id',carmy_id)):
        m.require(inputs.get(key) is None or inputs[key]==actual,'optional expected '+key+' differs from current typed identity')
    binding={'machine_id':machine,'run_dir':context['run_dir'],'actor_id':context['saved_campaign']['player_id'],
        'pid':process['pid'],'process_creation_unix_seconds':process['create_time'],
        'episode':f['episode_run_id'],'generation':f['diagnostics']['connection_generation']}
    runner=load('r05_common_once_runner',Path(context['repo_root'])/'tools/run_r05_low_supply_initializer_once.py')
    package=m.validate_fixture(prepared['r05_low_supply_fixture']['manifest']['path'])
    result=runner.initialize_once(relay,m,binding=binding,prepared=prepared,package=package,
        army_id=army_id,carmy_id=carmy_id,prefix='r05-controlled-init-once',
        claims_dir=Path(context['state_dir'])/'r05-initializer-claims',current_machine=machine)
    client.checkpoint('r05-controlled-initializer-outcome',result)
    return {'machine_id':machine,'controlled_initializer_qualified':result['assessment']['status']=='prepared_low_stock',
        'assessment':result['assessment'],'business_pass':False,'R05_pass':False,'natural_days_advanced':0}

def verify_case(context):
    path=Path(context['output'])/'r05-controlled-initializer-outcome.json'
    if not path.is_file():
        return {'machine_id':'unknown','case_acceptance_pass':False,'R05_pass':False,'reason':'actual independent typed initialization evidence absent'}
    result=json.loads(path.read_bytes());a=result.get('assessment',{});ack=result.get('confirm_ack',{})
    physical=a.get('status')=='prepared_low_stock' and a.get('physical_soldiers_unchanged') is True
    gui=ack.get('postcondition_verified') is True and ack.get('status')=='observed_decision_detail_closed'
    return {'machine_id':result.get('machine_id','unknown'),'case_contract_qualified':physical,
        'gui_contract_qualified':gui,'case_acceptance_pass':False,
        'scope':'controlled initial supply only','R05_pass':False,'natural_update_observed':False,
        'starvation_casualty_proven':False}
