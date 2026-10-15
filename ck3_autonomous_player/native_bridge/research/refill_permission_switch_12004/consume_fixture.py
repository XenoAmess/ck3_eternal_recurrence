from pathlib import Path
import argparse,copy,datetime as dt,hashlib,importlib,json,sys,types
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--candidate-src',type=Path)
parser.add_argument('--native-output-root',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
root=args.output_dir;root.mkdir(parents=True,exist_ok=False)
repo=args.repo/'ck3_autonomous_player/src/xar_autoplayer'
candidate=(args.candidate_src/'xar_autoplayer') if args.candidate_src else repo
for name,paths in [('xar_autoplayer',[candidate,repo]),('xar_autoplayer.bridge',[candidate/'bridge',repo/'bridge'])]:
    package=types.ModuleType(name);package.__path__=[str(p) for p in paths];sys.modules[name]=package
normalize=importlib.import_module('xar_autoplayer.bridge.army_scoped_ordered_refill_contract').normalize_scoped_ordered_refill_inputs_v1
strict=importlib.import_module('xar_autoplayer.bridge.army_refill_permission_switch_12004').normalize_refill_permission_switch_12004
physical=importlib.import_module('xar_autoplayer.bridge.army_observed_core_validation_12004')._physical
native_root=args.native_output_root
raw=(native_root/'native-packets.actual.ndjson').read_bytes()
run=json.loads((native_root/'RUN.actual.json').read_text());assert run['exit_code']==0 and hashlib.sha256(raw).hexdigest()==run['raw_sha256']
rows=[json.loads(line) for line in raw.decode().splitlines()]
accepted=[];normalized={}
for row in rows:
    assert row['synthetic'] is True and row['CK3_runtime_observed'] is False
    if row['producer']=='ReadOrderedRefillPersistent12003':
        p=row['persistent']
        envelope={'source':'native_scoped_observed_prepared_ordered_refill','status':'partial',
          'unavailable_reason':'synthetic_without_arrg_resolver','subject_army_id':1,'subject_carmy_id':2,
          'native_persistent_occurrence_count':1,'native_army_refresh_occurrence_count':1,
          'persistent_occurrences':[{'stored_index':0,'persistent_regiment_id':p['persistent_regiment_id']}],
          'army_refresh_occurrence_indices':[0],'persistent_regiments':[p]}
        result=normalize(envelope);physical(p,p['persistent_regiment_id'],'native_fixture')
        normalized[row['case']]=result
        assert result['persistent_regiments'][0]==p
        accepted.append({'case':row['case'],'ordinary_normalizer':True,'natural_core_physical_validator':True,
          'chunks':len(p['chunks']),'switch_present':'refill_permission_switch_v1' in p['chunks'][0]})
    else:
        assert strict(row['switch'])==row['switch']
        accepted.append({'case':row['case'],'strict_nested_normalizer':True})
by_case={r['case']:r for r in rows}
title=by_case['title_holder_not_player']['persistent']['chunks'][0]['refill_permission_switch_v1']
direct=by_case['direct_nonzero']['persistent']['chunks'][0]['refill_permission_switch_v1']
assert title['enabled'] is False and title['resolved_character_full_id']!=direct['resolved_character_full_id']
assert direct['enabled'] is True and direct['raw_byte_4a9']==2
rejects=[]
for label,mutate in [
 ('player_substitution',lambda d:d.update(resolved_character_full_id=direct['resolved_character_full_id'])),
 ('disabled_became_true',lambda d:d.update(enabled=True)),
 ('drop_source_witness',lambda d:d.pop('selected_character_raw_full_id')),
 ('wrong_full_generation',lambda d:d.update(resolved_character_full_id=d['selected_character_raw_full_id']+0x1000000)),
 ('borrow_title_for_direct',lambda d:d.update(resolved_title_full_id=0x31000001)),
 ('unavailable_grants_false',lambda d:d.update(status='unavailable',unavailable_reason='missing'))]:
    value=copy.deepcopy(title if label!='borrow_title_for_direct' else direct);mutate(value)
    try:strict(value)
    except ValueError as error:rejects.append({'case':label,'reason':str(error),'derived_negative_only':True})
    else:raise AssertionError(label)
assert len(accepted)==12 and len(rejects)==6
record={'machine_id':run['machine_id'],'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'status':'PASS','source':'unchanged native producer+serializer NDJSON, not hand-authored successful packets',
 'raw_path':str(native_root/'native-packets.actual.ndjson'),'raw_sha256':run['raw_sha256'],
 'accepted':accepted,'rejected':rejects,'CK3_runtime_observed':False,
 'actual_ADD_observed':False,'permission_result_qualified':False}
(root/'NATIVE-STRICT-CONSUMER.actual.json').write_text(json.dumps(record,indent=2)+'\n')
(root/'CONSUMED-NATIVE-SYNTHETIC.actual.json').write_text(json.dumps(normalized,indent=2)+'\n')
print(json.dumps({'status':'PASS','native_cases':len(accepted),'derived_rejections':len(rejects),'actual_ADD_observed':False}))
