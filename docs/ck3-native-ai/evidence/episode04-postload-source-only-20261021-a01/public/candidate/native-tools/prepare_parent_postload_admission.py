"""Create one distinct postload admission; default OFF, no observer or SDK calls."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from postload_admission import (MODE,file_pin,read,verify,need,obj,text,scope_value,
    validate_qualification,validate_index,packet,expected_from_scope,pin)
from postload_wire import wire_json
from postload_models import expected_value
import postload_owner_binding as owner
from parent_postload_contract import PREFIX_SHA,digest

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-parent-postload',action='store_true')
    for key in ('repo','snapshot','cash','root-scope','qualification','observer','bundle-index','output-root'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    need(args.prepare_parent_postload,'default OFF; explicit prepare required')
    root=Path(__file__).resolve().parent
    index_pin=pin(args.bundle_index)
    validate_index(index_pin,self_path=Path(__file__))
    scope_ref=pin(args.root_scope);q_ref=pin(args.qualification)
    scope=scope_value(read(scope_ref))
    q=validate_qualification(read(q_ref),observer=pin(args.observer),typed_root=root)
    need(scope.bundle==index_pin and scope.machine==q.machine,'public source index/machine differs')
    need(scope.raw['qualification_sha256']==q_ref['sha256']
        and scope.raw['observer_sha256']==q.observer['sha256'],'Root scope/Q/executable binding')
    repo=args.repo.resolve()
    sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
    from ck3_live_run_id import current_machine_id
    need(current_machine_id()==scope.machine,'actual current machine differs')
    common=Path(text(scope.raw['common_output'],'same case output'))
    need(pin(args.snapshot)==scope.snapshot and pin(args.cash)==scope.cash,'Root exact owner pair pins')
    snapshot=packet(scope.snapshot,tool='ck3_take_snapshot',common=common,machine=scope.machine)
    cash=packet(scope.cash,tool='ck3_query_war_cash_current_resources_private_v1',common=common,machine=scope.machine)
    from xar_autoplayer.bridge.nonwar_private_build import private_native_build_identity
    from xar_autoplayer.bridge.version_identity import CK3_12004
    need(private_native_build_identity(snapshot)==CK3_12004,'actual 1.20.0.4 native carrier required')
    expected=expected_from_scope(scope,snapshot,cash)
    expected['admission_id']=digest({'expected':expected,'root_scope_sha256':scope_ref['sha256'],
        'snapshot_sha256':scope.snapshot['sha256'],'cash_sha256':scope.cash['sha256']})
    expected_value(wire_json(expected))
    metadata: dict[str,object]={
        'parent_schema':'xar.maintenance.parent_postload.admission.v1','pid':expected['pid'],'tid':0,
        'created':expected['created'],'character':expected['character'],'context':expected['context'],
        'full_id':expected['full_id'],'post_pc':expected['post_pc'],
        'subject_field_address':expected['subject_field_address'],'module_base':scope.module_base,
        'module_size':scope.module_size,'postload_mode_qualified':1,'prefix_sha256':PREFIX_SHA,
        'qualified_exe_sha256':'98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518',
        'game_version':'1.20.0.4','steam_build_id':25734779,
        'controlled_window_id':scope.owner['controlled_window_id'],'payment_epoch':scope.owner['payment_epoch'],
        'connection_generation':scope.owner['connection_generation'],'native_revision':scope.owner['native_revision'],
        'date_raw':expected['date_raw'],'source_cash_sha256':scope.cash['sha256'],
        'admission_id':expected['admission_id'],'foreign_limit':4096,'cancel_event':scope.cancel}
    metadata.update(owner.metadata(scope.owner))
    meta=''.join(key+'='+str(value)+'\n' for key,value in metadata.items()).encode('ascii')
    binding=(json.dumps(wire_json({'schema':'xar.maintenance.parent_postload.binding.v1',
        'machine_id':scope.machine,'expected':expected,'root_scope_sha256':scope_ref['sha256'],
        'qualification_sha256':q_ref['sha256'],'public_bundle_sha256':index_pin['sha256'],
        'meta_sha256':hashlib.sha256(meta).hexdigest(),'prepared_only':True}),
        sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(meta)+len(binding)<=32768 and not args.output_root.exists(),'bounded new admission; no replay')
    args.output_root.mkdir(parents=True)
    for name,payload in [('PARENT-POSTLOAD.meta.txt',meta),('BINDING.prepared.json',binding)]:
        with (args.output_root/name).open('xb') as stream:stream.write(payload)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
