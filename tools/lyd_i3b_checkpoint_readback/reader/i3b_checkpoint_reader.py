"""I3b checkpoint observation adapter. No game, provider, registry, or mutation.

Lossless block and stored-value bodies are exact copies of sealed primitives.
Raw save observations and separately qualified native predicates stay distinct.
The checked-in pending request cannot open a save. Actual acceptance stays null.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent / 'dependencies'))
from bounded_save_parser import parse_block, block_body, one
from save_fields import stored, unquote

HEAD = '632f0a57a07aa6299052004589ed6f7632e7d8f7'
MAX_ID = 4294967295
REQUEST_KEYS = {'schema','mode','source_head','stage','identity','save','expected','native_predicates','native_reference_binding','native_title_binding','baseline','output'}
IDENTITY_KEYS = {'actor_id','faith_id','main_rite_id','pid','session_id','revision','checkpoint_id'}
STAGES = {'proposal','ballot','signed_precommit','success_postcommit','partial_postcommit'}

class ReadbackError(ValueError):
    pass

def require(value, message):
    if not value:
        raise ReadbackError(message)

def unique_json(path):
    def pairs(rows):
        out = {}
        for key, value in rows:
            require(key not in out, 'duplicate JSON key ' + key)
            out[key] = value
        return out
    def constant(token):
        raise ReadbackError('nonfinite JSON constant ' + token)
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,parse_constant=constant)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def ast_sha(entries):
    return digest(json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode('utf-8'))

def valid_id(value, label):
    require(type(value) is int and 0 < value < MAX_ID, 'invalid ' + label)
    return value

def scalar_id(value, label, absent=False, allow_zero=False):
    if value is None and absent:
        return None
    require(isinstance(value, str) and re.fullmatch(r'[0-9]+', value), 'non-ID ' + label)
    if allow_zero and value == '0':
        return 0
    return valid_id(int(value), label)

def native_link_id(value,label):
    # Explicit CK3 missing-head sentinel stays null; never becomes an ID.
    if value in (None,'0',str(MAX_ID)):
        return None
    return scalar_id(value,label)

def var_ref(variables, name, kind, required=True):
    row = variables.get(name)
    if row is None and not required:
        return None
    require(row is not None and row.get('type') == kind, 'missing or wrong typed ' + name)
    return scalar_id(row.get('identity'), name)

def number(variables, name, required=True):
    row = variables.get(name)
    if row is None and not required:
        return None
    require(row is not None and row.get('type') == 'value' and 'number' in row, 'missing numeric ' + name)
    value = Decimal(row['number'])
    require(value == value.to_integral_value(), 'nonintegral ' + name)
    return int(value)

def list_refs(lists, name, kind):
    require(name in lists, 'missing captured list ' + name)
    result = []
    for row in lists[name]['items']:
        require(row['type'] == kind, 'wrong list item type ' + name)
        result.append(scalar_id(row['identity'], name))
    require(len(result) == len(set(result)), 'duplicate captured reference ' + name)
    return result

def title_type_binding(request):
    binding=request['native_reference_binding']
    if binding is None:
        return None
    require(set(binding)=={'schema','source_head','evidence_sha256','title_type'},'closed reference binding')
    require(binding['schema']=='lyd.saved-native-reference-binding.v1' and binding['source_head']==HEAD,'reference binding source')
    require(isinstance(binding['evidence_sha256'],str) and re.fullmatch('[0-9a-f]{64}',binding['evidence_sha256']),'reference binding evidence')
    require(isinstance(binding['title_type'],str) and binding['title_type'] not in ('char','faith','rite','value','boolean') and binding['title_type'],'unknown native title type')
    return binding['title_type']

def title_list_refs(lists, name, title_type):
    require(name in lists,'missing title list')
    if title_type is not None:
        return list_refs(lists,name,title_type)
    # Discovery only: retain IDs but do not classify this representation as
    # native Title until an independent actual typed-row binding is supplied.
    refs=[]
    for row in lists[name]['items']:
        require(isinstance(row.get('type'),str) and row['type'] not in ('char','faith','rite','value','boolean'),'contradictory unqualified Title reference')
        refs.append(scalar_id(row['identity'],name))
    require(len(refs)==len(set(refs)),'duplicate title list reference')
    return refs

def section(text, key, following):
    starts = list(re.finditer(r'^' + re.escape(key) + r'=\{\n', text, re.M))
    ends = list(re.finditer(r'^' + re.escape(following) + r'=\{\n', text, re.M))
    require(len(starts) == len(ends) == 1 and starts[0].end() < ends[0].start(), 'nonunique section ' + key)
    return text[starts[0].end():ends[0].start()]

def records(span, label):
    """Consume each depth-0 numeric record once; never build the world AST.

    Same exact indentation framing as the sealed actual reader. Unsupported
    framing fails, rather than silently omitting a living or title record.
    """
    lines = span.splitlines(keepends=True)
    current, body, seen = None, [], set()
    for line in lines:
        if current is None:
            m = re.fullmatch(r'([0-9]+)=\{\n', line)
            if m:
                current = scalar_id(m.group(1), label, allow_zero=(label == 'landed title'))
                require(current not in seen, 'duplicate record ' + label)
                seen.add(current)
                body = [line]
            else:
                require(line.strip() in ('','}') or line.lstrip().startswith('#'), 'unsupported record framing ' + label)
        else:
            body.append(line)
            if line == '}\n' or line == '}':
                raw = ''.join(body)
                entries = parse_block(block_body(raw))
                yield current, entries
                current, body = None, []
    require(current is None, 'truncated record ' + label)

def title_database_records(text):
    """Actual CK3 wraps its numeric database in landed_titles.landed_titles."""
    matches = list(re.finditer(r'^\tlanded_titles=\{\n', text, re.M))
    if not matches:
        yield from records(section(text, 'landed_titles', 'dynasties'), 'landed title')
        return
    require(len(matches) == 1, 'nonunique actual nested landed_titles database')
    outer = list(re.finditer(r'^landed_titles=\{\n', text, re.M))
    following = list(re.finditer(r'^dynasties=\{\n', text, re.M))
    require(len(outer) == len(following) == 1 and outer[0].end() < matches[0].start() < following[0].start(), 'actual landed_titles database boundary')
    start = matches[0].end() - 2
    depth, quoted, escaped = 0, False, False
    for pos in range(start, following[0].start()):
        ch = text[pos]
        if quoted:
            if escaped: escaped = False
            elif ch == '\\': escaped = True
            elif ch == '"': quoted = False
        elif ch == '"': quoted = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                yield from records(text[matches[0].end():pos], 'landed title')
                return
    raise ReadbackError('truncated actual landed_titles database')

def exact_root_block(text, key):
    # Matches multiline/inline roots. Quoted braces are handled by the tokenizer.
    matches = list(re.finditer(r'^' + re.escape(key) + r'=\{', text, re.M))
    require(len(matches) == 1, 'nonunique root block ' + key)
    start = matches[0].end() - 1
    depth, quoted, escaped = 0, False, False
    for pos in range(start, len(text)):
        ch = text[pos]
        if quoted:
            if escaped: escaped = False
            elif ch == '\\': escaped = True
            elif ch == '"': quoted = False
        elif ch == '"': quoted = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return parse_block(text[start:pos+1])
    raise ReadbackError('truncated root ' + key)

def graph(text, root, parent_key):
    entries = exact_root_block(text, root)
    db = one(entries, 'database', required=True)
    require(isinstance(db,list), 'nonblock graph database')
    result = {}
    for row in db:
        gid = scalar_id(row['key'], root, allow_zero=True)
        require(gid not in result and isinstance(row['value'],list), 'duplicate or scalar graph')
        e = row['value']; variables, lists, _ = stored(e)
        heads = {k: one(e,k) for k in ('head_of_rite','religious_head','religious_head_title')}
        tenets = [r for r in e if r['key'] in ('tenets','tenet','doctrine','doctrines')]
        nested = one(e, 'data')
        if isinstance(nested,list):
            tenets += [r for r in nested if r['key'] in ('tenets','tenet','doctrine','doctrines')]
        result[gid] = {'id':gid,'entries':e,'AST_sha256':ast_sha(e),'variables':variables,'lists':lists,
                       'heads':heads,'tenet_doctrine_rows':tenets,parent_key:one(e,parent_key)}
    return result

def saved_character_is_alive(cid, entries):
    """CK3 living section can retain explicit dead_data records until pruning."""
    alive = one(entries, 'alive_data')
    dead = one(entries, 'dead_data')
    require((alive is None) != (dead is None), 'ambiguous saved character lifecycle ' + str(cid))
    require(isinstance(alive if alive is not None else dead, list), 'bad saved character lifecycle ' + str(cid))
    if dead is not None:
        require(isinstance(one(dead, 'date', required=True), str), 'dead character date absent ' + str(cid))
    return alive is not None

def raw_character(cid, entries):
    require(saved_character_is_alive(cid, entries), "explicit dead record is not a living character " + str(cid))
    alive = one(entries,'alive_data',required=True)
    require(isinstance(alive,list), 'bad alive_data')
    variables, lists, _ = stored(alive)
    rite = scalar_id(one(entries,'rite'), 'character rite', absent=True, allow_zero=True)
    return {'character_id':cid,'rite_id':rite,'entries':entries,'AST_sha256':ast_sha(entries),
            'variables':variables,'lists':lists,'alive_data':alive,'landed_data':one(entries,'landed_data'),
            'native_eligibility':None}

def title_row(tid, entries):
    variables, lists, _ = stored(entries)
    return {'title_id':tid,'holder':native_link_id(one(entries,'holder'),'title holder'),
            'entries':entries,'AST_sha256':ast_sha(entries),'variables':variables,'lists':lists,'qualification':None}

def path_value(entries, path):
    require(isinstance(path,list) and path and all(isinstance(k,str) and k for k in path), 'invalid qualified field path')
    value = entries
    for key in path:
        require(isinstance(value,list), 'qualified field parent is not a block')
        value = one(value,key,required=True)
    return value

def qualify_native_title(row, binding):
    if binding is None:
        return {'status':'UNKNOWN','law':None,'properties':None,'reason':'native serialization not yet source-qualified'}
    require(set(binding) == {'schema','source_head','evidence_sha256','law','properties'}, 'closed title binding keys')
    require(binding['schema'] == 'lyd.native-title.saved-field-binding.v1' and binding['source_head'] == HEAD, 'title binding source')
    require(isinstance(binding['evidence_sha256'],str) and re.fullmatch('[0-9a-f]{64}',binding['evidence_sha256']), 'title binding evidence')
    law = binding['law']
    require(set(law) == {'path','shape'}, 'law binding keys')
    actual_law = path_value(row['entries'],law['path'])
    if law['shape'] == 'bare_scalar_list':
        require(isinstance(actual_law,list) and all(r['key'] is None and isinstance(r['value'],str) for r in actual_law), 'unsupported law shape')
        laws = [unquote(r['value']) for r in actual_law]
    elif law['shape'] == 'scalar':
        require(isinstance(actual_law,str), 'unsupported scalar law')
        laws = [unquote(actual_law)]
    else:
        raise ReadbackError('unsupported law binding shape')
    names = {'destroy_if_invalid_heir','no_automatic_claims','definitive_form','always_follows_primary_heir'}
    require(set(binding['properties']) == names, 'incomplete native title properties')
    properties = {}
    for name, spec in binding['properties'].items():
        require(set(spec) == {'path','true_token','false_token'} and isinstance(spec['true_token'],str) and isinstance(spec['false_token'],str) and spec['true_token'] != spec['false_token'], 'property token binding')
        raw = path_value(row['entries'],spec['path'])
        require(isinstance(raw,str) and raw in (spec['true_token'],spec['false_token']), 'unknown property saved token')
        properties[name] = {'raw':raw,'value':raw == spec['true_token'],'path':spec['path']}
    return {'status':'QUALIFIED_OBSERVATION','law':laws,'properties':properties,'binding':binding,
            'law_matches_factory_contract':'temporal_head_of_faith_succession_law' in laws,
            'properties_match_factory_contract':all(r['value'] for r in properties.values())}

def validate_request(request, before_open=False):
    require(set(request) == REQUEST_KEYS, 'closed request keys')
    require(request['schema'] == 'lyd.i3b.checkpoint-reader-request.v1' and request['source_head'] == HEAD, 'source/schema mismatch')
    require(request['mode'] in ('synthetic_fixture','future_actual') and request['stage'] in STAGES, 'mode/stage')
    require(set(request['identity']) == IDENTITY_KEYS, 'closed identity keys')
    for key in ('actor_id','faith_id','main_rite_id'):
        valid_id(request['identity'][key], key)
    expected = request['expected']
    require(set(expected) == {'serial','nonce','phase'}, 'closed expected round keys')
    require(all(type(expected[k]) is int and expected[k] > 0 for k in ('serial','nonce')), 'pending or invalid round')
    phase = expected['phase']
    require(type(phase) is int and phase in (1,2), 'invalid phase')
    require(phase == (1 if request['stage'] == 'proposal' else 2), 'stage phase mismatch')
    if request['mode'] == 'future_actual':
        identity=request['identity']
        require(type(identity['pid']) is int and identity['pid'] > 0, 'pending PID')
        require(type(identity['revision']) is int and identity['revision'] >= 0, 'pending revision')
        require(all(isinstance(identity[k],str) and identity[k] for k in ('session_id','checkpoint_id')), 'pending actual session/checkpoint')
    if before_open:
        save = request['save']
        require(set(save) == {'path','bytes','sha256'}, 'closed save descriptor')
        require(isinstance(save['path'],str) and save['path'] and type(save['bytes']) is int and save['bytes'] > 0 and isinstance(save['sha256'],str) and re.fullmatch('[0-9a-f]{64}',save['sha256']), 'pending save descriptor')

def add_check(checks, name, matches, observed=None, expected=None):
    checks.append({'name':name,'matches':bool(matches),'observed':observed,'expected':expected})

def replace_no_head(value):
    if isinstance(value,list):
        return [{'key':r['key'],'value':replace_no_head(r['value'])} for r in value]
    return 'doctrine_temporal_head' if value=='doctrine_no_head' else value

def doctrine_present(rows, token):
    def walk(value):
        if isinstance(value,list):
            return any(walk(r['value']) for r in value)
        return unquote(value)==token
    return walk(rows)

def predicate_rows(request, state, checks):
    witness = request['native_predicates']
    if witness is None:
        state['native_predicate_qualification']={'status':'UNKNOWN','reason':'is_adult/is_imprisoned/incapable/effective learning/is_ai require fresh independent native readback'}
        return {}
    keys={'schema','source_head','checkpoint_sha256','identity','complete_current_faith_roster','human_character_ids','characters','rite_counties','evidence_sha256'}
    require(set(witness)==keys and witness['schema']=='lyd.i3b.native-predicates.v1' and witness['source_head']==HEAD,'closed predicate witness')
    require(witness['identity']==request['identity'] and witness['checkpoint_sha256']==state['checkpoint_sha256'],'stale predicate witness binding')
    require(isinstance(witness['evidence_sha256'],str) and re.fullmatch('[0-9a-f]{64}',witness['evidence_sha256']),'predicate evidence hash')
    require(witness['complete_current_faith_roster'] is True,'incomplete native roster')
    human_ids=witness['human_character_ids']
    require(isinstance(human_ids,list) and len(human_ids)==len(set(human_ids)) and all(type(i)is int and 0<i<MAX_ID for i in human_ids),'human witness ids')
    rows={}
    for row in witness['characters']:
        require(set(row)=={'character_id','alive','adult','imprisoned','incapable','learning','is_ai'},'closed native character predicates')
        cid=valid_id(row['character_id'],'native character')
        require(cid not in rows and all(type(row[k])is bool for k in ('alive','adult','imprisoned','incapable','is_ai')) and type(row['learning'])is int and row['learning']>=0,'bad native predicate row')
        require(row['alive'] is True,'native roster includes nonliving')
        rows[cid]=row
    add_check(checks,'native_witness_full_living_faith_roster',set(rows)==set(state['roster']['living_faith_ids']),sorted(rows),state['roster']['living_faith_ids'])
    actual_humans=sorted(i for i,r in rows.items() if not r['is_ai'])
    add_check(checks,'native_human_roster_exact',actual_humans==sorted(human_ids),actual_humans,sorted(human_ids))
    # Save player topology is an independent observation, never silently is_ai.
    add_check(checks,'saved_current_humans_match_native',actual_humans==state['roster']['saved_current_human_faith_ids'],actual_humans,state['roster']['saved_current_human_faith_ids'])
    counties=witness['rite_counties']
    require(isinstance(counties,dict) and all(re.fullmatch('[0-9]+',k) and type(v)is int and v>=0 for k,v in counties.items()),'county witness')
    state['native_predicate_qualification']={'status':'SYNTHETIC_BOUND_OBSERVATION' if request['mode']=='synthetic_fixture' else 'CALLER_SUPPLIED_NOT_NATIVE_AUTHENTICATED',
        'witness':witness,'authority':'input contract only; hash syntax is not a native receipt authenticity proof'}
    for row in state['roster']['members']:
        cid=row['character_id'];native=rows.get(cid)
        row['native_eligibility']=native
        if native is None: continue
        qualifies=native['alive'] and native['adult'] and not native['imprisoned'] and not native['incapable'] and native['learning']>=15
        add_check(checks,f'member_{cid}_elector_matches_native',row['was_elector']==int(qualifies),row['was_elector'],int(qualifies))
        add_check(checks,f'member_{cid}_human_matches_native',row['was_player']==int(not native['is_ai']),row['was_player'],int(not native['is_ai']))
    for row in state['schools']:
        observed=counties.get(str(row['rite_id']))
        add_check(checks,f'rite_{row["rite_id"]}_native_counties',observed is not None and observed==row['counties'],observed,row['counties'])
        if row['delegate_id'] is not None:
            native=rows.get(row['delegate_id'])
            eligible=native is not None and native['alive'] and native['adult'] and not native['imprisoned'] and not native['incapable'] and native['learning']>=15
            add_check(checks,f'rite_{row["rite_id"]}_delegate_native_qualified',eligible)
    return rows

def observe_text(text, request, checkpoint_sha256):
    validate_request(request)
    text=text.replace('\r\n','\n')
    actor_id,faith_id,main_id=(request['identity'][k] for k in ('actor_id','faith_id','main_rite_id'))
    baseline_graphs=request['baseline']['graphs']
    require(set(baseline_graphs)=={'faiths','rites'},'complete selected baseline graphs required')
    require({str(faith_id),'104','106'} <= set(baseline_graphs['faiths']) and {str(main_id),'159','187'} <= set(baseline_graphs['rites']),'mandatory 0240 current/old/receiving graph baseline coverage')
    baseline_rite_ids=request['baseline']['actual_faith_rite_ids']
    require(isinstance(baseline_rite_ids,list) and baseline_rite_ids and len(baseline_rite_ids)==len(set(baseline_rite_ids)) and all(type(i)is int and 0<i<MAX_ID for i in baseline_rite_ids),'baseline actual Faith Rite set')
    require({str(i) for i in baseline_rite_ids} <= set(baseline_graphs['rites']),'complete captured-Rite tenet baseline')
    faiths=graph(text,'faiths','main_rite');rites=graph(text,'rites','faith')
    require(faith_id in faiths and main_id in rites,'missing actual graph')
    parents={i:scalar_id(r['faith'],'rite parent',absent=True,allow_zero=True) for i,r in rites.items()}
    actual_rites=sorted(i for i,f in parents.items() if f==faith_id)
    all_living={}
    living_count=0
    living_section_count=0
    excluded_explicit_dead=[]
    unclassified=[]
    # Scan every numeric record; explicit saved dead records are not living members.
    for cid,entries in records(section(text,'living','dead_unprunable'),'living character'):
        living_section_count+=1
        if not saved_character_is_alive(cid, entries):
            excluded_explicit_dead.append({'character_id':cid,'AST_sha256':ast_sha(entries),'dead_data':one(entries,'dead_data')})
            continue
        living_count+=1
        character=raw_character(cid,entries)
        if character['rite_id'] is None or character['rite_id'] not in parents or parents[character['rite_id']] is None:
            unclassified.append(cid)
        if cid==actor_id or parents.get(character['rite_id'])==faith_id:
            all_living[cid]=character
    require(actor_id in all_living,'actor not alive')
    actor=all_living[actor_id];variables=actor['variables'];lists=actor['lists']
    stage=request['stage'];post=stage in ('success_postcommit','partial_postcommit')
    captured_members=[] if post else list_refs(lists,'lyd_i3b_members','char')
    captured_rites=[] if post else list_refs(lists,'lyd_i3b_rites','rite')
    title_type=title_type_binding(request)
    political_ids=request['baseline']['political_title_ids']
    require(isinstance(political_ids,list) and len(political_ids)==len(set(political_ids)) and all(type(i)is int and 0<i<MAX_ID for i in political_ids),'political ids')
    current_humans=[]
    for row in exact_root_block(text,'currently_played_characters'):
        require(row['key'] is None,'unsupported saved human roster')
        current_humans.append(scalar_id(row['value'],'saved current human'))
    require(len(current_humans)==len(set(current_humans)),'duplicate saved current human')
    faith_living_ids=sorted(i for i,c in all_living.items() if parents.get(c['rite_id'])==faith_id)
    saved_human_faith_ids=sorted(set(current_humans)&set(faith_living_ids))
    state={'schema':'lyd.i3b.checkpoint-observations.v1','source_head':HEAD,'mode':request['mode'],'stage':stage,
           'identity':request['identity'],'checkpoint_sha256':checkpoint_sha256,'actual_pass':None,'actual_native_runtime_pass':None,
           'round':{},'actor':actor,'faith':faiths[faith_id],'rites':[rites[i] for i in actual_rites],
           'roster':{'whole_world_living_records_scanned':True,'living_records_scanned':living_count,'living_section_numeric_records_scanned':living_section_count,'excluded_explicit_dead_records':excluded_explicit_dead,'faith_classification_complete':not unclassified,'unclassified_living_ids':unclassified,'living_faith_ids':faith_living_ids,
                     'captured_member_ids':captured_members,'saved_current_human_ids':current_humans,'saved_current_human_faith_ids':saved_human_faith_ids,'members':[]},
           'schools':[],'native_title':None,'protected_titles':[],'native_predicate_qualification':None,'checks':[]}
    checks=state['checks']
    state['native_reference_qualification']={'status':'UNKNOWN' if title_type is None else 'QUALIFIED_OBSERVATION','binding':request['native_reference_binding']}
    add_check(checks,'all_living_faith_classification_complete',not unclassified,unclassified,[])
    add_check(checks,'actual_Faith_Rite_registry_set_protected',set(actual_rites)==set(baseline_rite_ids),actual_rites,baseline_rite_ids)
    if stage=='success_postcommit':
        for rid in actual_rites:
            rows=rites[rid]['tenet_doctrine_rows']
            add_check(checks,f'all_actual_rite_{rid}_native_temporal_doctrine',doctrine_present(rows,'doctrine_temporal_head') and not doctrine_present(rows,'doctrine_no_head'))
    serial_name='lyd_i3b_result_serial' if post else 'lyd_i3b_serial'
    nonce_name='lyd_i3b_result_nonce' if post else 'lyd_i3b_nonce'
    serial,nonce=number(variables,serial_name),number(variables,nonce_name)
    state['round']={'serial':serial,'nonce':nonce,'phase':None if post else number(variables,'lyd_i3b_phase'),
                    'result_code':number(variables,'lyd_i3b_result_code') if post else None}
    add_check(checks,'exact_current_serial',serial==request['expected']['serial'],serial,request['expected']['serial'])
    add_check(checks,'exact_current_nonce',nonce==request['expected']['nonce'],nonce,request['expected']['nonce'])
    add_check(checks,'actor_current_main',actor['rite_id']==main_id,actor['rite_id'],main_id)
    add_check(checks,'faith_current_main',scalar_id(faiths[faith_id]['main_rite'],'Faith main')==main_id)
    add_check(checks,'actual_main_parent',parents[main_id]==faith_id)
    add_check(checks,'captured_faith',var_ref(variables,'lyd_i3b_faith','faith')==faith_id)
    add_check(checks,'captured_main',var_ref(variables,'lyd_i3b_main','rite')==main_id)
    add_check(checks,'detached_actual_native_hor',native_link_id(rites[main_id]['heads']['head_of_rite'],'native HoR')==actor_id)
    state['protected_graphs']=[]
    for kind,current in (('faiths',faiths),('rites',rites)):
        for gid_string,baseline in baseline_graphs[kind].items():
            gid=int(gid_string)
            require(gid in current,'protected graph missing')
            row=current[gid]
            captured=(kind=='faiths' and gid==faith_id) or (kind=='rites' and gid in actual_rites)
            if captured:
                expected_rows=replace_no_head(baseline['tenet_doctrine_rows']) if stage=='success_postcommit' else baseline['tenet_doctrine_rows']
                if stage!='partial_postcommit':
                    add_check(checks,f'{kind}_{gid}_complete_tenet_status_projection',row['tenet_doctrine_rows']==expected_rows,row['tenet_doctrine_rows'],expected_rows)
                if post and stage=='success_postcommit':
                    add_check(checks,f'{kind}_{gid}_native_temporal_doctrine',doctrine_present(row['tenet_doctrine_rows'],'doctrine_temporal_head') and not doctrine_present(row['tenet_doctrine_rows'],'doctrine_no_head'))
            else:
                add_check(checks,f'{kind}_{gid}_full_AST_protected',row['AST_sha256']==baseline['AST_sha256'])
                state['protected_graphs'].append({'kind':kind,'id':gid,'entries':row['entries'],'AST_sha256':row['AST_sha256'],'baseline_AST_sha256':baseline['AST_sha256']})
    if not post:
        add_check(checks,'active',number(variables,'lyd_i3b_active')==1)
        add_check(checks,'phase',state['round']['phase']==request['expected']['phase'])
        add_check(checks,'captured_rites_exact',set(captured_rites)==set(actual_rites),captured_rites,actual_rites)
        add_check(checks,'captured_living_members_exact',set(captured_members)==set(faith_living_ids),captured_members,faith_living_ids)
        add_check(checks,'captured_political_titles_exact',set(title_list_refs(lists,'lyd_i3b_political_titles',title_type))==set(political_ids))
        add_check(checks,'detached_authority_mode',number(variables,'lyd_i3b_authority_mode')==1)
        add_check(checks,'required_actual_native_hor',var_ref(variables,'lyd_i3b_required_native_hor','char')==actor_id)
        for cid in captured_members:
            if cid not in all_living:
                add_check(checks,f'member_{cid}_living_current_faith',False)
                continue
            row=all_living[cid];v=row['variables']
            row.update({'member_rite_id':var_ref(v,'lyd_i3b_member_rite','rite'),'member_owner_id':var_ref(v,'lyd_i3b_member_owner','char'),
                        'member_serial':number(v,'lyd_i3b_member_serial'),'was_elector':number(v,'lyd_i3b_was_elector'),
                        'was_player':number(v,'lyd_i3b_was_player'),'player_yes':number(v,'lyd_i3b_player_yes'),'vote':number(v,'lyd_i3b_vote')})
            require(row['was_elector'] in (0,1) and row['was_player'] in (0,1) and row['player_yes'] in (0,1) and row['vote'] in (-1,0,1),'invalid ballot flag value')
            add_check(checks,f'member_{cid}_same_rite',row['rite_id']==row['member_rite_id'])
            add_check(checks,f'member_{cid}_exact_owner_serial',row['member_owner_id']==actor_id and row['member_serial']==serial)
            add_check(checks,f'member_{cid}_saved_human_stamp',row['was_player']==int(cid in current_humans))
            if row['was_elector']==0:
                add_check(checks,f'member_{cid}_nonelector_no_ballot',row['vote']==-1)
            if request['expected']['phase']==1:
                add_check(checks,f'member_{cid}_proposal_no_ballot_or_consent',row['vote']==-1 and row['player_yes']==0)
            if stage=='signed_precommit' and row['was_player']==1:
                add_check(checks,f'member_{cid}_separate_412_consent',row['player_yes']==1)
            state['roster']['members'].append(row)
        for rid in captured_rites:
            require(rid in rites,'captured rite not found')
            v=rites[rid]['variables']
            school={'rite_id':rid,'owner_id':var_ref(v,'lyd_i3b_owner','char'),'serial':number(v,'lyd_i3b_serial'),
                    'members_total':number(v,'lyd_i3b_members_total'),'total':number(v,'lyd_i3b_total'),'yes':number(v,'lyd_i3b_yes'),
                    'signed':number(v,'lyd_i3b_signed'),'dormant':number(v,'lyd_i3b_dormant'),'counties':number(v,'lyd_i3b_counties'),
                    'delegate_id':var_ref(v,'lyd_i3b_delegate','char',required=False)}
            require(school['dormant'] in (0,1) and school['signed'] in (0,1) and all(school[k]>=0 for k in ('members_total','total','yes','counties')),'invalid school counters')
            members=[c for c in state['roster']['members'] if c['rite_id']==rid]
            electors=[c for c in members if c['was_elector']==1]
            yes=sum(c['vote']==1 for c in electors)
            school.update({'counted_members_total':len(members),'counted_total':len(electors),'counted_yes':yes,'quorum_numerator':3*yes-2*len(electors)})
            add_check(checks,f'rite_{rid}_exact_owner_serial',school['owner_id']==actor_id and school['serial']==serial)
            add_check(checks,f'rite_{rid}_counters_match_full_roster',school['members_total']==len(members) and school['total']==len(electors) and school['yes']==yes)
            add_check(checks,f'rite_{rid}_dormancy_exact',school['dormant']==int(school['counties']==0 and len(members)==0))
            if school['dormant']==0:
                add_check(checks,f'rite_{rid}_positive_elector_count',len(electors)>0)
                if request['expected']['phase']==2:
                    add_check(checks,f'rite_{rid}_actual_representative',school['delegate_id'] in {c['character_id'] for c in electors})
                if stage=='signed_precommit':
                    add_check(checks,f'rite_{rid}_independent_two_thirds',len(electors)>0 and 3*yes>=2*len(electors))
                    add_check(checks,f'rite_{rid}_representative_signature',school['signed']==1)
            else:
                add_check(checks,f'rite_{rid}_dormant_no_signature_or_delegate',school['signed']==0 and school['yes']==0 and school['delegate_id'] is None)
            if request['expected']['phase']==1:
                add_check(checks,f'rite_{rid}_proposal_no_yes_or_signature',school['yes']==0 and school['signed']==0)
            elif school['signed']==1:
                add_check(checks,f'rite_{rid}_signature_requires_quorum_and_representative',len(electors)>0 and 3*yes>=2*len(electors) and school['delegate_id'] in {c['character_id'] for c in electors})
            state['schools'].append(school)
        predicate_rows(request,state,checks)
    else:
        cleanup_names={'lyd_i3b_active','lyd_i3b_phase','lyd_i3b_authority_mode','lyd_i3b_required_native_hor'}
        add_check(checks,'round_cleanup',not (set(variables)&cleanup_names) and not(set(lists)&{'lyd_i3b_rites','lyd_i3b_members','lyd_i3b_political_titles'}))
        add_check(checks,'result_same_native_hor',var_ref(variables,'lyd_i3b_result_native_hor','char')==actor_id and number(variables,'lyd_i3b_result_authority_mode')==1)
        state['native_predicate_qualification']={'status':'NOT_APPLICABLE_POST_CLEANUP','reason':'must separately retain signed_precommit readback; cleanup removes votes'}
    result_title_ref=variables.get('lyd_i3b_result_head_title') if post else None
    discovered=None
    if result_title_ref is not None:
        if title_type is not None:
            discovered=var_ref(variables,'lyd_i3b_result_head_title',title_type)
        else:
            require(isinstance(result_title_ref.get('type'),str) and result_title_ref['type'] not in ('char','faith','rite','value','boolean'),'contradictory result Title reference')
            discovered=scalar_id(result_title_ref['identity'],'unqualified result Title reference')
    state['result_head_title_reference']=result_title_ref
    observed_head=native_link_id(faiths[faith_id]['heads']['religious_head_title'],'actual Faith native title') if post else None
    titles={}
    for tid,entries in title_database_records(text):
        if tid in set(political_ids) or tid==discovered or tid==observed_head:
            titles[tid]=title_row(tid,entries)
    baseline_titles=request['baseline']['political_titles']
    require(set(baseline_titles)=={str(i) for i in political_ids},'complete political baseline required')
    for tid in political_ids:
        require(tid in titles,'missing protected title')
        row=titles[tid];baseline=baseline_titles[str(tid)]
        row.update({'baseline_AST_sha256':baseline['AST_sha256'],'baseline_holder':baseline['holder']})
        add_check(checks,f'political_{tid}_holder',row['holder']==actor_id and row['holder']==baseline['holder'])
        add_check(checks,f'political_{tid}_full_AST_protected',row['AST_sha256']==baseline['AST_sha256'])
        state['protected_titles'].append(row)
    if post:
        state['faith_native_head_title_id']=observed_head
        if request['stage']=='success_postcommit':
            add_check(checks,'actual_result_success_code',state['round']['result_code']==1)
            add_check(checks,'actual_discovered_title_exists',discovered is not None and discovered in titles)
            add_check(checks,'faith_and_receipt_actual_title_agree',discovered is not None and observed_head==discovered)
            add_check(checks,'actual_faith_religious_head_actor',native_link_id(faiths[faith_id]['heads']['religious_head'],'Faith native religious head')==actor_id)
            add_check(checks,'actual_recognized_leader',var_ref(faiths[faith_id]['variables'],'lyd_c3_recognized_leader','char',required=False)==actor_id)
            add_check(checks,'actual_office_faith',var_ref(variables,'lyd_c3_office_faith','faith',required=False)==faith_id)
            if discovered is not None and discovered in titles:
                row=titles[discovered];state['native_title']=row
                add_check(checks,'new_title_not_political',discovered not in political_ids)
                add_check(checks,'actual_title_holder',row['holder']==actor_id)
                add_check(checks,'actual_title_owned_marker',number(row['variables'],'lyd_c2_owned_head_title')==1)
                add_check(checks,'actual_title_owner_faith',var_ref(row['variables'],'lyd_c2_owner_faith','faith')==faith_id)
                row['qualification']=qualify_native_title(row,request['native_title_binding'])
                if row['qualification']['status']!='UNKNOWN':
                    add_check(checks,'actual_title_succession_law',row['qualification']['law_matches_factory_contract'])
                    add_check(checks,'actual_title_four_properties',row['qualification']['properties_match_factory_contract'])
        else:
            add_check(checks,'partial_result_code',state['round']['result_code'] in (2,3,4,5,6,7))
            # A partial factory title may exist without success receipt. Preserve
            # raw Faith graph and observed ID; never invent result_head_title.
            state['partial_actual_title_observation']={'faith_title_id':observed_head,'success_receipt_title_id':discovered,'actual_pass':None}
            state['partial_native_title']=titles.get(observed_head)
    else:
        state['native_title_qualification']={'status':'NOT_APPLICABLE_PRECOMMIT'}
    state['observation_checks_match']=all(r['matches'] for r in checks)
    unknown = state['native_reference_qualification']['status']=='UNKNOWN' or (not post and state['native_predicate_qualification']['status']=='UNKNOWN') or (stage=='success_postcommit' and (state['native_title'] is None or state['native_title']['qualification']['status']=='UNKNOWN'))
    state['assessment']='OBSERVED_CONTRACT_MISMATCH' if not state['observation_checks_match'] else 'INCOMPLETE_NATIVE_QUALIFICATION' if unknown else 'OBSERVED_CONTRACT_MATCH'
    if request['mode']=='future_actual' and state['assessment']=='OBSERVED_CONTRACT_MATCH':
        state['assessment']='OBSERVED_FIELDS_MATCH_NATIVE_AUTHENTICATION_PENDING'
    state['formal_mandate_credit']=None
    state['formal_event_context_qualification']={'status':'UNKNOWN','actor':None,'serial':None,'nonce':None,'phase':None,'native_revision':None,
      'reason':'checkpoint consistency does not prove callbacks used formal ballot events or current event scope; retain independently bound 410/411/412/413/430 receipts'}
    state['signed_precommit_required_for_postcommit']=post
    return state

def read_checkpoint(request):
    # Every pending identity/round/save value is rejected before file access.
    validate_request(request,before_open=True)
    path=Path(request['save']['path'])
    data=path.read_bytes()
    require(len(data)==request['save']['bytes'] and digest(data)==request['save']['sha256'],'checkpoint bytes/hash mismatch')
    require(not data.startswith(b'PK'),'compressed save not accepted; no automatic external decoder')
    text=data.decode('utf-8-sig',errors='strict')
    return observe_text(text,request,digest(data))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True,type=Path)
    args=parser.parse_args(argv)
    request=unique_json(args.request)
    state=read_checkpoint(request)
    output=Path(request['output'])
    require(not output.exists(),'output already exists')
    output.mkdir(parents=True,exist_ok=False)
    (output/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'REPORT.json').write_text(json.dumps({'schema':'lyd.i3b.checkpoint-reader-report.v1','request_sha256':digest(args.request.read_bytes()),'state_sha256':digest((output/'STATE.json').read_bytes()),'assessment':state['assessment'],'actual_pass':None,'formal_mandate_credit':None},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(output),'assessment':state['assessment'],'actual_pass':None}))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
