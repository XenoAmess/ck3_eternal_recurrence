"""Project exact new current-input literals from explicit saved responses.

No query, SDK, native binary, save, video, latest-file search or qualification.
Driver JSON references are followed only inside the supplied scene root.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json
from pathlib import Path

TARGETS={
    'county_entry_inputs_v1':'county_current_inputs',
    'multiplier_floor_inputs_v1':'county_loaded_floors',
    'refill_permission_switch_v1':'refill_administrative_switch',
    'current_raw_context_v1':'paused_current_raw_cash_context',
    'callback_binding_source_12004':'military_callback_source',
    'standard_click_binding_12004':'military_widget_callback_slots',
}
IDENTITIES=('army_id','native_carmy_id','army_regiment_id','persistent_regiment_id','persistent_full_id',
            'regiment_id','character_id','played_character_id','widget_id','name','path','vtable_rva')
FRAME=('snapshot_id','revision','native_revision','date_raw','episode_run_id','bridge_pid','connection_generation',
       'queried_snapshot_id','queried_revision','queried_native_revision','queried_date_raw',
       'queried_connection_generation','queried_episode_run_id','query_sequence','army_strengths_profile','army_strengths_query_scope')


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def pointer_token(value):return str(value).replace('~','~0').replace('/','~1')


def read_json(path,scene,expected=None):
    path=path.resolve();require(scene in path.parents,'explicit input lies outside scene root')
    require(not path.is_symlink() and path.suffix=='.json','only regular saved JSON input allowed')
    require(path.stat().st_size<=128*1024**2,'saved JSON exceeds finite read bound')
    raw=path.read_bytes()
    if expected:require(len(raw)==expected['bytes'] and sha(raw)==expected['sha256'],'exact saved Driver JSON reference changed')
    return json.loads(raw),{'path':path.relative_to(scene).as_posix(),'bytes':len(raw),'sha256':sha(raw),'availability':'source-machine external original; not copied into compact record'}


def collect(value,source,base_pointer=''):
    rows=[]
    def walk(item,pointer,ancestors):
        if isinstance(item,dict):
            identity={key:item[key] for key in IDENTITIES if key in item and not isinstance(item[key],(dict,list))}
            context=ancestors+([{'pointer':pointer,'identity':identity}] if identity else [])
            for key,child in item.items():
                child_pointer=pointer+'/'+pointer_token(key)
                if key in TARGETS:
                    rows.append({'kind':TARGETS[key],'source':source,'json_pointer':child_pointer,
                                 'identity_ancestors':context,'literal':child})
                if isinstance(child,(dict,list)):walk(child,child_pointer,context)
        elif isinstance(item,list):
            for i,child in enumerate(item):walk(child,pointer+'/'+str(i),ancestors)
    walk(value,base_pointer,[])
    return rows


def intern_observations(rows):
    """Deduplicate metadata and equal values, retaining every literal pointer."""
    tables={'originals':[],'identity_contexts':[],'literal_values':[]};indices={k:{} for k in tables}
    def add(table,value):
        key=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        if key not in indices[table]:
            indices[table][key]=len(tables[table]);tables[table].append(value)
        return indices[table][key]
    compact=[]
    for row in rows:
        compact.append({'kind':row['kind'],'source_id':add('originals',row['source']),
            'json_pointer':row['json_pointer'],'identity_context_id':add('identity_contexts',row['identity_ancestors']),
            'literal_id':add('literal_values',row['literal'])})
    return tables,compact


def extract(scene,responses,machine_id,runtime_proof=None):
    sources=[];observations=[];seen_raw=set()
    for kind,path in responses:
        envelope,pin=read_json(path,scene)
        require(envelope.get('machine_id')==machine_id,'saved response machine ID differs')
        body=envelope.get('body');require(isinstance(body,dict),'saved response has no literal body')
        # Driver evidence belongs to the saved response envelope. Never walk
        # SDK text/structured duplicates to rediscover the same source.
        evidence=envelope.get('army_history_evidence')
        references=[('/army_history_evidence',evidence)] if isinstance(evidence,dict) and isinstance(evidence.get('raw_result_reference'),dict) else []
        record={'kind':kind,'response':pin,'machine_id':envelope['machine_id'],'is_error':envelope.get('is_error'),
                'request':envelope.get('request'),'body_frame':{k:body[k] for k in FRAME if k in body},
                'body_state':{k:body[k] for k in ('accepted','status','step','root_available','truncated','scope','callback_method_name_available','click_action_available') if k in body},
                'driver_evidence':[]}
        if kind in ('cash','cash_observer_enable'):
            record['cash_body_literal']=body
        if references:
            for pointer,evidence in references:
                ref=evidence['raw_result_reference'];raw_path=Path(ref['path'])
                require(ref.get('kind')=='complete-driver-army-query-result-json-v1','unexpected Driver evidence kind')
                raw,pin_raw=read_json(raw_path,scene,ref)
                relative_evidence=dict(evidence);relative_ref=dict(ref)
                relative_ref['path']=pin_raw['path'];relative_evidence['raw_result_reference']=relative_ref
                record['driver_evidence'].append({'response_pointer':pointer,'literal_metadata':relative_evidence,'sourcepath_form':'relative to original scene root; original SHA binds untouched response','raw_original':pin_raw,
                    'raw_frame':{k:raw[k] for k in FRAME if k in raw}})
                signature=(pin_raw['sha256'],pin_raw['bytes'])
                if signature not in seen_raw:
                    observations.extend(collect(raw,pin_raw));seen_raw.add(signature)
        # The response is the source for cash/tree. Strength uses the exact
        # Driver original to avoid duplicate filtered/body representations.
        if kind!='strengths' or not references:observations.extend(collect(body,pin,'/body'))
        sources.append(record)
    proof=None
    if runtime_proof is not None:
        literal,pin=read_json(runtime_proof,scene)
        require(literal.get('machine_id')==machine_id,'runtime proof machine differs')
        proof={'source':pin,'literal':literal}
    counts={name:sum(row['kind']==name for row in observations) for name in TARGETS.values()}
    tables,compact=intern_observations(observations)
    return {'schema':'episode04.a07.current-literal-compact.v1','machine_id':machine_id,
        'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_proof':proof,
        'sources':sources,'literal_tables':tables,'observations':compact,
        'projection_counts':counts,
        'scope':'saved current-value literals and provenance only; no consumer requalification or causal result',
        'causal_business_PASS':False,'new_query_or_action':False,'new_live_evidence_by_extractor':False,
        'save_video_native_binary_read':False,'missing_target_fields_are_not_zero_filled':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene',type=Path,required=True);parser.add_argument('--machine-id',required=True)
    for name in ('strengths','cash','military-tree'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cash-observer-enable',type=Path)
    parser.add_argument('--runtime-proof',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'append-only compact target already exists')
    responses=[('strengths',args.strengths),('cash',args.cash),('military_tree',args.military_tree)]
    if args.cash_observer_enable:responses.append(('cash_observer_enable',args.cash_observer_enable))
    value=extract(args.scene.resolve(),responses,args.machine_id,args.runtime_proof)
    raw=(json.dumps(value,separators=(',',':'),ensure_ascii=False)+'\n').encode()
    require(len(raw)<=384*1024,'literal projection exceeds compact lane bound; retain originals and report before reducing scope')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as stream:stream.write(raw)
    print(json.dumps({'bytes':len(raw),'sha256':sha(raw),'projection_counts':value['projection_counts'],'causal_business_PASS':False}))


if __name__=='__main__':main()
