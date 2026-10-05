"""Explicit actual-save request only. Qualified AST/typed storage parsers, no game calls."""
import argparse,hashlib,json,re,sys
from decimal import Decimal
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EXT=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
sys.path.insert(0,str(HERE/'dependencies'))
from bounded_save_parser import extract_exact_indented_block,parse_block,block_body,one
from save_fields import stored,unquote
def sha(raw):return hashlib.sha256(raw).hexdigest()
def jload(raw):
    def unique(rows):
        d={}
        for key,val in rows:
            if key in d:raise ValueError('Duplicate JSON key '+key)
            d[key]=val
        return d
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=unique)
def ast(raw):return parse_block(block_body(raw))
def scalar(rows,key,required=False):return unquote(one(rows,key,required=required))
def astdigest(rows):return sha(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def exact_number(value):
    if value is None:return None
    if isinstance(value,list):
        if len(value)!=1 or value[0]['key']!='value':raise ValueError('Unsupported numeric/resource structure')
        value=one(value,'value',required=True)
    if not isinstance(value,str):raise ValueError('Unsupported numeric shape')
    return str(Decimal(value))
def main(request_path):
    raw_request=request_path.read_bytes();request=jload(raw_request)
    if set(request)!={'schema','phase','source_binding','actor_id','save','supporting_evidence','political_title_ids','output','watch_character_ids'} or request['schema']!='lyd.r10.actual-checkpoint-readback-request.v1':raise ValueError('Closed actual-save request required')
    aid=request['actor_id']
    if type(aid) is not int or not 0<aid<4294967295:raise ValueError('Actual full actor ID must be explicitly supplied')
    sr=request['save'];save=Path(sr['path']);data=save.read_bytes()
    if len(data)!=sr['bytes'] or sha(data)!=sr['sha256']:raise ValueError('Actual preserved save bytes/SHA mismatch')
    if data.startswith(b'PK'):raise ValueError('Qualified parser expects exact plaintext CK3 save; zipped save needs separate preserved decoding qualification')
    source=request['source_binding']
    if source['head']!='d0f8fa3b9d444828759443aa018bfd7ad31b398d':raise ValueError('This R10 reader request binding differs from current preserved source')
    ref=source['cold_source_inventory'];source_raw=Path(ref['path']).read_bytes()
    if sha(source_raw)!=ref['sha256'] or len(source_raw)!=ref['bytes']:raise ValueError('Actual R10 cold source inventory changed')
    support=[]
    for item in request['supporting_evidence']:
        raw=Path(item['path']).read_bytes()
        if sha(raw)!=item['sha256'] or len(raw)!=item['bytes']:raise ValueError('Supporting evidence exact SHA mismatch')
        support.append(item)
    text=data.decode('utf-8-sig').replace('\r\n','\n')
    out=Path(request['output']).resolve()
    if out.exists() or not out.is_relative_to(EXT) or out==EXT:raise ValueError('New external output directory required')
    out.mkdir(parents=True)
    def emit(name,value):
        with (out/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    def record(section,key,depth,label):
        raw=extract_exact_indented_block(section,str(key),depth)
        with (out/(label+'.excerpt.txt')).open('x',encoding='utf-8',newline='\n') as f:f.write(raw+'\n')
        return ast(raw)
    def section(key,following):
        a=list(re.finditer(r'(?m)^'+re.escape(key)+r'=\{\n',text));b=list(re.finditer(r'(?m)^'+re.escape(following)+r'=\{\n',text))
        if len(a)!=1 or len(b)!=1 or a[0].start()>=b[0].start():raise ValueError('Ambiguous actual save section '+key)
        return text[a[0].start():b[0].start()]
    meta=record(text,'meta_data',0,'metadata');played=record(text,'played_character',0,'played-character')
    if scalar(meta,'version',True)!='1.20.0.3' or scalar(meta,'save_game_version',True)!='17':raise ValueError('Qualified actual save version differs')
    if scalar(played,'character',True)!=str(aid):raise ValueError('Explicit actual actor differs from saved player')
    dates=re.findall(r'(?m)^date=([^\n]+)$',text);current=re.findall(r'(?m)^currently_played_characters=\{([^}]*)\}',text)
    if len(dates)!=1 or len(current)!=1 or str(aid) not in current[0].split() or scalar(meta,'meta_date',True)!=dates[0]:raise ValueError('Actual saved date/current actor inconsistent')
    faith_raw=extract_exact_indented_block(text,'faiths',0);rite_raw=extract_exact_indented_block(text,'rites',0)
    graphs={}
    for name,raw in [('faiths',faith_raw),('rites',rite_raw)]:
        database=one(ast(raw),'database',required=True)
        if not isinstance(database,list):raise ValueError('Missing graph database')
        graph={}
        for row in database:
            if isinstance(row['key'],str) and row['key'].isdigit():
                if row['key'] in graph or not isinstance(row['value'],list):raise ValueError('Duplicate/invalid graph record')
                graph[row['key']]=row['value']
        graphs[name]=graph
    parents={rid:scalar(rows,'faith',True) for rid,rows in graphs['rites'].items()};mains={fid:scalar(rows,'main_rite') for fid,rows in graphs['faiths'].items()}
    living=section('living','dead_unprunable');actor=record(living,aid,0,'actor-'+str(aid));alive=one(actor,'alive_data',required=True);landed=one(actor,'landed_data') or []
    variables,lists,_=stored(alive);rid=scalar(actor,'rite',True)
    if rid not in parents:raise ValueError('Actual actor Rite absent')
    fid=parents[rid]
    if fid not in graphs['faiths']:raise ValueError('Actual actor Faith absent')
    selected_rites={rid,'187'};selected_faiths={fid,'106'}
    for row in variables.values():
        if row['type']=='rite' and row['identity'] is not None:selected_rites.add(row['identity'])
        if row['type']=='faith' and row['identity'] is not None:selected_faiths.add(row['identity'])
    for collection in lists.values():
        for item in collection['items']:
            if item['type']=='rite' and item['identity'] is not None:selected_rites.add(item['identity'])
            if item['type']=='faith' and item['identity'] is not None:selected_faiths.add(item['identity'])
    missing_rites=sorted(selected_rites-set(graphs['rites']));missing_faiths=sorted(selected_faiths-set(graphs['faiths']))
    selected_rites&=set(graphs['rites']);selected_faiths&=set(graphs['faiths'])
    for fid2 in list(selected_faiths):
        if mains[fid2] in graphs['rites']:selected_rites.add(mains[fid2])
    for rid2 in list(selected_rites):
        if parents[rid2] in graphs['faiths']:selected_faiths.add(parents[rid2])
    selected={name:{} for name in ['faiths','rites']}
    headchars=set()
    for name,ids,raw in [('faiths',selected_faiths,faith_raw),('rites',selected_rites,rite_raw)]:
        for ident in sorted(ids,key=int):
            rows=record(raw,ident,2,name[:-1]+'-'+ident);vs,ls,_=stored(rows);inner=one(rows,'data') or []
            tenets=[row for row in rows if row['key'] in ['tenets','tenet','doctrine','doctrines']]+[row for row in inner if row['key'] in ['tenets','tenet','doctrine','doctrines']]
            heads={key:scalar(rows,key) for key in ['head_of_rite','religious_head','religious_head_title']}
            for key in ['head_of_rite','religious_head']:
                ident2=heads[key]
                if ident2 is not None and ident2.isdigit() and 0<int(ident2)<4294967295:headchars.add(int(ident2))
            selected[name][ident]={'entries':rows,'AST_sha256':astdigest(rows),'variables':vs,'lists':ls,'heads':heads,'tenet_doctrine_rows':tenets,'parent_faith':parents.get(ident) if name=='rites' else None,'main_rite':mains.get(ident) if name=='faiths' else None}
    watch=request['watch_character_ids']
    if not isinstance(watch,list) or not all(type(cid) is int and 0<cid<4294967295 for cid in watch):raise ValueError('Explicit actual watch character IDs required')
    rolechars={aid}|headchars|set(watch)
    for name,group in lists.items():
        if name.startswith(('lyd_c2_','lyd_c3_','lyd_i3b_')):
            for item in group['items']:
                ident=item['identity']
                if item['type']=='char' and ident is not None and ident.isdigit() and 0<int(ident)<4294967295:rolechars.add(int(ident))
    if len(rolechars)>256:raise ValueError('Named role character bound exceeds256')
    chars={};role_unavailable=[]
    for cid in sorted(rolechars):
        try:rows=actor if cid==aid else record(living,cid,0,'character-'+str(cid));ca=one(rows,'alive_data',required=True)
        except ValueError as exc:role_unavailable.append({'id':cid,'reason':str(exc)});continue
        vs,ls,_=stored(ca)
        chars[str(cid)]={'rite':scalar(rows,'rite'),'variables':vs,'lists':ls,'protected_top':{key:one(rows,key) for key in ['first_name','birth','culture','traits','skill','dynasty_house','dna','family_data','court_data']},'protected_alive':{key:one(ca,key) for key in ['family_data','court_data','domain','primary_title','laws','government']},'raw_character_AST_sha256':astdigest(rows)}
    def currency(key,leaf):
        return exact_number(one(one(alive,key) or [],leaf))
    wallet={'gold':currency('gold','value'),'piety':currency('piety','currency'),'prestige':currency('prestige','currency')}
    lifestyle=one(alive,'lifestyle_xp') or []
    domain=one(landed,'domain') or [];domainids=[row['value'] for row in domain if row['key'] is None]
    political=request['political_title_ids']
    if len(political)!=7 or len(set(political))!=7 or not all(type(t) is int and t>0 for t in political):raise ValueError('Explicit7 political title IDs required, not inferred from head/claim titles')
    title_section=section('landed_titles','dynasties');titles={}
    for tid in sorted(set(map(int,domainids))|set(political)):
        rows=record(title_section,tid,0,'title-'+str(tid));titles[str(tid)]={'entries':rows,'AST_sha256':astdigest(rows),'holder':scalar(rows,'holder'),'political_guard_member':tid in political,'actual_actor_domain_member':str(tid) in domainids}
    rolevars={key:row for key,row in variables.items() if row['type'] in ['rite','faith','char']}
    roundvars={key:row for key,row in variables.items() if key.startswith(('lyd_c2_','lyd_c3_','lyd_i3b_')) and any(term in key for term in ['active','phase','serial','nonce','quorum','signature','charter','total','yes','vote','ticket','owner','mode','current','faith','rite','main'])}
    cooldown={key:variables.get(key) for key in ['lyd_school_cooldown','lyd_study_cooldown']}
    graph_issues=[{'faith':f,'main_rite':m,'main_parent':parents.get(m)} for f,m in mains.items() if m is None or m not in parents or parents[m]!=f]
    summary={'current_actor_id':aid,'current_rite':rid,'current_faith':fid,'current_HoR':scalar(graphs['rites'][rid],'head_of_rite'),'current_HoF':scalar(graphs['faiths'][fid],'religious_head'),'current_faith_main':mains[fid],'current_faith_main_parent':parents.get(mains[fid]),'wallet':wallet,'stress_saved':exact_number(one(alive,'stress')),'learning_XP_saved':exact_number(one(lifestyle,'learning_lifestyle')),'cooldown':cooldown,'round_variables':roundvars,'stored_typed_roles':rolevars,'actor_domain_ids':domainids,'political7':{str(tid):titles[str(tid)] for tid in political},'actual_saved_native_modifiers':one(alive,'modifier'),'stress_or_XP_expected':None}
    state={'calendar':dates[0],'player':played,'summary':summary,'actor_full_AST':actor,'character_roles':chars,'source_target_related_graphs':selected,'all_faith_mains':mains,'all_rite_parents':parents,'all_graph_link_issues_observed':graph_issues,'typed_reference_absences':{'rites':missing_rites,'faiths':missing_faiths,'character_roles':role_unavailable},'all_actor_LYD_variables':variables,'all_actor_LYD_lists':lists,'actor_protected_landed':landed,'all_selected_domain_titles':titles,'raw_resources':{key:one(alive,key) for key in ['gold','piety','prestige','stress','lifestyle_xp','perk','skill_xp']},'faith_graph_raw_sha256':sha((faith_raw+'\n').encode()),'rite_graph_raw_sha256':sha((rite_raw+'\n').encode()),'whole_world_characters_scanned':False,'whole_world_political_titles_scanned':False,'historical_inactive_role_references_not_assumed_current':True,'missing_saved_numeric_values_are_null_notzero':True}
    emit('STATE.json',state)
    report={'schema':'lyd.r10.actual-checkpoint-bounded-AST-readback.v1','status':'ACTUAL_SAVED_OBSERVATION_NO_AUTOMATIC_BUSINESS_PASS','phase':request['phase'],'source_binding':source,'actual_save':sr,'actual_actor_id':aid,'saved_summary':summary,'request':{'path':str(request_path.resolve()),'bytes':len(raw_request),'sha256':sha(raw_request)},'supporting_exact_evidence':support,'supporting_native_business_semantics_verified':False,'state':{'path':str(out/'STATE.json'),'bytes':(out/'STATE.json').stat().st_size,'sha256':sha((out/'STATE.json').read_bytes())},'business_postconditions':'UNASSESSED_REQUIRES_BEFORE_AFTER_OPERATION_SPECIFIC_EXPECTATIONS','game_pipe_MCP_desktop_bus_Git_main_calls':False}
    emit('REPORT.json',report)
    emit('INDEX.json',{'files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'report':str(out/'REPORT.json'),'sha256':sha((out/'REPORT.json').read_bytes()),'actor_id':aid,'rite':rid,'faith':fid,'head_of_rite':summary['current_HoR'],'wallet':wallet,'stress_saved':summary['stress_saved'],'related_characters':len(chars),'status':report['status']},ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--request',type=Path,required=True);args=ap.parse_args();main(args.request)
