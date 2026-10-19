"""Pure AST audit of explicit SDK metadata writes; never runs runtime code."""
from __future__ import annotations
import ast,hashlib,json,re
from pathlib import Path


def audit_current_views_v1(source: str, *, generation: str, existing_basenames=()):
    tree=ast.parse(source);rows=[]
    def expression(node,bindings):
        if isinstance(node,ast.Name):return bindings.get(node.id)
        if isinstance(node,ast.Constant) and isinstance(node.value,str):return node.value
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):
            left,right=expression(node.left,bindings),expression(node.right,bindings)
            if isinstance(left,str) and isinstance(right,str):return left+'/'+right
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('str','Path') and len(node.args)==1:
            return expression(node.args[0],bindings)
        return None
    def walk(node,bindings):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            inner=dict(bindings)
            for child in node.body:walk(child,inner)
            return
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            value=expression(node.value,bindings)
            for target in (node.targets if isinstance(node,ast.Assign) else [node.target]):
                if isinstance(target,ast.Name) and value is not None:bindings[target.id]=value
        if isinstance(node,ast.Call):
            target=None;kind=None;replace=False
            if isinstance(node.func,ast.Name) and node.func.id in ('atomic','write','atomic_payload_v1') and node.args:
                target=expression(node.args[0],bindings);kind=node.func.id
                replace=any(k.arg=='replace' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords)
            elif isinstance(node.func,ast.Attribute) and node.func.attr in ('open','write_bytes','write_text','mkdir'):
                mode=node.args[0].value if node.args and isinstance(node.args[0],ast.Constant) else None
                if node.func.attr!='open' or isinstance(mode,str) and any(flag in mode for flag in ('x','w','a','+')):
                    target=expression(node.func.value,bindings);kind=node.func.attr+(':'+mode if isinstance(mode,str) else '')
                    replace=node.func.attr not in ('open','mkdir') or 'w' in (mode or '') or 'a' in (mode or '') or '+' in (mode or '')
                    if node.func.attr=='mkdir':
                        replace=any(k.arg=='exist_ok' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords)
            if isinstance(target,str) and (target.startswith(('{N}/','{Q}/','{OUTBOX}/','{INBOX}/','{STATE_DIR}/')) or target=='{Q}'):
                basename=target.rsplit('/',1)[-1]
                rows.append({'line':node.lineno,'path_expression':target,'basename':basename,'write':kind,
                    'replace':replace,'already_exists':basename in set(existing_basenames)})
        for child in ast.iter_child_nodes(node):
            if not isinstance(child,(ast.arguments,ast.arg)):walk(child,bindings)
    walk(tree,{name:'{'+name+'}' for name in ('N','Q','INBOX','OUTBOX','STATE_DIR')})
    current=[];bad=[]
    prefixes=('ROOT-AUDIENCE-ACTIVE-SDK-','ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-',
        'ROOT-ACTUAL-SDK-PROCESSES-PINNED-','ROOT-ACTUAL-DRIVER-MODE-')
    for row in rows:
        name=row['basename']
        if name.startswith(prefixes) or re.search(r'(?:P37C\d+[A-Z]?|SDK-C\d+[A-Z]?|p37c\d+[a-z]?-prewar)',name):
            current.append(row)
            markers=re.findall(r'(?:P37(C\d+[A-Z]?)|SDK-(C\d+[A-Z]?)|p37(c\d+[a-z]?)-prewar)',name)
            if any(next(s for s in parts if s).upper()!=generation for parts in markers):
                bad.append({'reason':'foreign generation write target',**row})
            if row['replace']:bad.append({'reason':'current-generation identity must be create-only',**row})
    return {'explicit_writes':rows,'current_identity_writes':current,'violations':bad,
        'existing_create_only_collisions':[r for r in rows if r['already_exists'] and not r['replace']],
        'scope':'explicit statically resolvable path writes only; dynamic generated per-sequence artifacts and imported helper internals remain original contracts'}


def require_unoccupied_current_views_v1(audit):
    if audit['violations'] or any(r['already_exists'] and not r['replace'] for r in audit['current_identity_writes']):
        raise ValueError('SDK current-view outputs require their own generation and unoccupied create-only targets')


def qualify_c8_v1(queue_path,entry_path,owner_path):
    paths=[Path(p) for p in (queue_path,entry_path,owner_path)]
    sources=[];audits=[]
    existing={'ROOT-AUDIENCE-ACTIVE-SDK-C7.json'}
    for path in paths:
        raw=path.read_bytes();sources.append({'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        audits.append(audit_current_views_v1(raw.decode('utf-8-sig'),generation='C8',existing_basenames=existing))
    queue=paths[0].read_text(encoding='utf-8-sig')
    corrected=queue.replace('N/"ROOT-AUDIENCE-ACTIVE-SDK-C7.json"','N/"ROOT-AUDIENCE-ACTIVE-SDK-C8.json"')
    positive=audit_current_views_v1(corrected,generation='C8',existing_basenames=existing)
    require_unoccupied_current_views_v1(positive)
    bad=corrected.replace('N/"ROOT-AUDIENCE-ACTIVE-SDK-C8.json"','N/"ROOT-AUDIENCE-ACTIVE-SDK-C7.json"')
    negative=audit_current_views_v1(bad,generation='C8',existing_basenames=existing)
    assert any(r['reason']=='foreign generation write target' for r in negative['violations'])
    assert any(r['basename']=='ROOT-AUDIENCE-ACTIVE-SDK-C7.json' for r in negative['existing_create_only_collisions'])
    # Presence checks are separate from generation checks: even correct C8
    # create-only output from a failed attempt must first be explicitly retained.
    occupied=audit_current_views_v1(corrected,generation='C8',existing_basenames={'ROOT-AUDIENCE-ACTIVE-SDK-C8.json'})
    assert any(r['basename']=='ROOT-AUDIENCE-ACTIVE-SDK-C8.json' for r in occupied['existing_create_only_collisions'])
    for rejected in (negative,occupied):
        try:require_unoccupied_current_views_v1(rejected)
        except ValueError:pass
        else:raise AssertionError('Foreign or occupied current-view write was not rejected')
    return {'sources':sources,'actual_source_audits':audits,'corrected_queue_audit':positive,
        'negative_old_generation_and_existing_create_only_detected':True,'same_generation_failed_attempt_collision_detected':True,
        'source_writes':0,'actual_Game_MCP_calls':0}


if __name__=='__main__':
    import argparse
    from datetime import datetime,timezone
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('queue','entry','owner','output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();result=qualify_c8_v1(args.queue,args.entry,args.owner)
    result.update(schema='xar.C8-current-view-create-only-source-qualification/v1',
        machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.now(timezone.utc).isoformat())
    with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'PASS','output':str(args.output),'identity_write_counts':[len(a['current_identity_writes']) for a in result['actual_source_audits']]}))
