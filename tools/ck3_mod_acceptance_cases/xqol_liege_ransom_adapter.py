"""Only the missing original L2.4 liege/shared-wallet branches; common runtime."""
from pathlib import Path
import copy
import shutil
from . import xqol_followup_common as common
from ck3_mod_acceptance_prepare import pin
from xqol_vanilla_contract import block

def validate_contract(context):
    common.validate_contract(context)
    for relative, expected in context['case_contract']['current_stock_sources'].items():
        actual=pin(Path(context['game_dir'])/'game'/relative)
        common.require(all(actual[k]==expected[k] for k in ('bytes','sha256')),
                       'Reviewed current .4 stock ransom source changed: '+relative)

def prepare_case(context):
    validate_contract(context)
    c=context['case_contract']; source=common.base(context)
    relative=c['stock_ransom_projection']['relative']
    authored=c['stock_ransom_projection']['authored_wrapper']
    stock_path=Path(context['game_dir'])/'game'/relative
    stock_raw=stock_path.read_bytes(); text=stock_raw.decode('utf-8-sig')
    wrapper_raw=(source/'fixture'/authored).read_bytes()
    wrapper=block(wrapper_raw.decode('utf-8-sig'),'ransom_interaction_effect')
    original=block(text,'ransom_interaction_effect'); body=original[original.index('{')+1:-1]
    common.require(wrapper.count(body)==1 and text.count(original)==1,
                   'Original stock ransom body not byte exact')
    projected=text.replace(original,wrapper,1)
    common.require(projected.replace(wrapper,original,1)==text,
                   'Entire stock ransom inverse projection changed')
    projected_raw=(b'\xef\xbb\xbf' if stock_raw.startswith(b'\xef\xbb\xbf') else b'')+projected.encode('utf-8')
    # Render a create-only input projection, then reuse common prepare unchanged.
    rendered=Path(context['output'])/'stock-ransom-input-projection'; rendered.mkdir()
    for name in ('original-plan.json','frontend-rules-plan.json'):
        shutil.copyfile(source/name,rendered/name)
    for name in c['fixture_files']:
        destination=rendered/'fixture'/(relative if name==authored else name)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(projected_raw if name==authored else (source/'fixture'/name).read_bytes())
    derived=copy.deepcopy(context)
    derived['case_contract']['data_directory']=str(rendered.resolve())
    derived['case_contract']['fixture_files']=[relative if x==authored else x for x in c['fixture_files']]
    prepared=common.prepare_case(derived)
    prepared['fixture_metadata_changes'].append({'kind':'current_stock_ransom_observer_only_projection',
        'actual_stock_source':pin(stock_path),'authored_wrapper':pin(source/'fixture'/authored),
        'projected_stock_file':pin(rendered/'fixture'/relative),
        'original_effect_body_byte_exact':True,'inverse_entire_stock_file_byte_exact':True,
        'all_other_stock_definitions_byte_exact':True,'actual_stock_callback_still_required':True})
    return prepared

def run_case(context,client):
    validate_contract(context)
    result=common.run_plan(context,client)
    result['coverage_exclusions']=['R46 self-payer replay','UI','PAM reward assertions','whole product release']
    classified=copy.deepcopy(context)
    projection=context['case_contract']['stock_ransom_projection']
    classified['case_contract']['fixture_files']=[projection['relative'] if x==projection['authored_wrapper'] else x
        for x in context['case_contract']['fixture_files']]
    return common.preserve_result(classified,client,result)

def verify_case(context):
    validate_contract(context)
    return common.verify_case(context)
