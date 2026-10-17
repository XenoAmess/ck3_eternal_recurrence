"""Bounded definition-entry candidates. Native receiver selection stays unknown."""
from __future__ import annotations

IMAGE_BYTES=0x61C5000
SOURCE="native_gui_type635_definition_candidates_12004"
FIELDS={"source","status","unavailable_reason","receiver_type_id",
        "current_variable_table_observed","native_receiver_selected",
        "receiver_variable_index","declared_type_id","stable_double_read","entries"}
ENTRY={"ancestor_depth","entry_type_48","entry_mode_40","entry_flag_4c",
       "direct_value_present","provider_present","provider_vtable_rva",
       "provider_slot2_rva","direct_owner_full_id","direct_owner_identity_verified"}
FRAME={"native_revision","connection_generation","pump_epoch","ticket_sequence",
       "game_pid","thread_id","played_character_full_id","date_raw",
       "owner_thread_verified","frame_stable","gui_owner_stable"}

def integer(x,lo,hi):
    return type(x) is int and lo<=x<=hi

def normalize_receiver_candidates(raw):
    fields=FIELDS | ({"failure_diagnostic"} if type(raw) is dict and "failure_diagnostic" in raw else set())
    if type(raw) is dict and "local_definition_entry_only" in raw:fields=fields|{"local_definition_entry_only"}
    if type(raw) is dict and "definition_chain_prefix_depth8" in raw:fields=fields|{"definition_chain_prefix_depth8"}
    if type(raw) is dict and "definition_frontier_continuation_depth8_12" in raw:fields=fields|{"definition_frontier_continuation_depth8_12"}
    if (type(raw) is not dict or raw.keys()!=fields or raw['source']!=SOURCE
            or type(raw['receiver_type_id']) is not int or raw['receiver_type_id']!=635
            or raw['current_variable_table_observed'] is not False
            or raw['native_receiver_selected'] is not False
            or type(raw['stable_double_read']) is not bool or type(raw['entries']) is not list
            or len(raw['entries'])>8):
        raise ValueError('type635 candidate schema/qualification')
    local=None
    if "local_definition_entry_only" in raw:
        local=normalize_local_definition_entry_only(raw["local_definition_entry_only"])
        if (raw['status']=='available' and local['status']=='available' and
                any(raw[k]!=local[k] for k in ('receiver_variable_index','declared_type_id'))):
            raise ValueError('local prefix declaration differs from full candidate')
    prefix=None
    if "definition_chain_prefix_depth8" in raw:
        prefix=normalize_definition_chain_prefix_depth8(raw["definition_chain_prefix_depth8"])
        failure=raw.get('failure_diagnostic')
        if (raw['status']!='unavailable' or raw['unavailable_reason']!='candidate_parent_depth_exhausted'
                or type(failure) is not dict or failure.get('capture_pass')!=1
                or failure.get('ancestor_depth')!=8 or failure.get('kind')!='parent_depth_exhausted'):
            raise ValueError('definition prefix lacks the original depth8 full failure')
        if prefix['status']=='available':
            if local is None or local['status']!='available':
                raise ValueError('definition prefix lacks independent stable local view')
            if (any(prefix[k]!=local[k] for k in ('receiver_variable_index','declared_type_id'))
                    or prefix['rows'][0]['entries']!=local['entries']
                    or prefix['rows'][0]['raw_definition_entry_count']!=local['raw_definition_entry_count']
                    or prefix['rows'][0]['definition_present']!=local['definition_present']):
                raise ValueError('definition prefix differs from independent local view')
    continuation=None
    if 'definition_frontier_continuation_depth8_12' in raw:
        if prefix is None:
            raise ValueError('frontier continuation lacks its original depth8 prefix')
        continuation=normalize_definition_frontier_continuation_depth8_12(raw['definition_frontier_continuation_depth8_12'])
        if continuation['status']=='available':
            if prefix['status']!='available' or any(continuation[k]!=prefix[k] for k in ('receiver_variable_index','declared_type_id')):
                raise ValueError('frontier continuation crossed its stable prefix/declaration')
    if 'failure_diagnostic' in raw:
        if raw['status']!='unavailable':raise ValueError('failure diagnostic cannot qualify an available candidate')
        normalize_receiver_failure(raw['failure_diagnostic'])
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or raw['entries']
                or raw['receiver_variable_index'] is not None or raw['declared_type_id'] is not None):
            raise ValueError('unavailable candidate must preserve unknown values')
        return {**raw, **({"local_definition_entry_only":local} if local is not None else {}), **({"definition_chain_prefix_depth8":prefix} if prefix is not None else {}), **({"definition_frontier_continuation_depth8_12":continuation} if continuation is not None else {})}
    if (raw['status']!='available' or raw['unavailable_reason'] is not None
            or raw['stable_double_read'] is not True
            or not integer(raw['receiver_variable_index'],0,255)
            or type(raw['declared_type_id']) is not int or raw['declared_type_id']!=635):
        raise ValueError('candidate declaration or double read')
    rows=[];last=-1
    for e in raw['entries']:
        if (type(e) is not dict or e.keys()!=ENTRY
                or not integer(e['ancestor_depth'],last+1,7)
                or type(e['entry_type_48']) is not int or e['entry_type_48']!=635
                or not integer(e['entry_mode_40'],-128,127) or not integer(e['entry_flag_4c'],0,255)
                or any(type(e[k]) is not bool for k in ('direct_value_present','provider_present','direct_owner_identity_verified'))):
            raise ValueError('candidate entry raw type/ordinal')
        last=e['ancestor_depth']
        for key,n in (('provider_vtable_rva',24),('provider_slot2_rva',1)):
            if e[key] is not None and not integer(e[key],1,IMAGE_BYTES-n):
                raise ValueError('provider target outside exact image')
        dynamic=e['entry_mode_40']>=2
        if ((not dynamic or not e['provider_present']) and
                (e['provider_vtable_rva'] is not None or e['provider_slot2_rva'] is not None)):
            raise ValueError('provider RVA on a branch that does not dispatch')
        if e['provider_slot2_rva'] is not None and e['provider_vtable_rva'] is None:
            raise ValueError('provider target lacks image vtable')
        direct=e['entry_mode_40']==1 and e['direct_value_present']
        owner=e['direct_owner_full_id']
        if owner is not None and not integer(owner,-2**31,2**31-1):
            raise ValueError('owner full generation ID')
        if (not direct and (owner is not None or e['direct_owner_identity_verified'])) or (
                e['direct_owner_identity_verified'] and (owner is None or owner==-1)):
            raise ValueError('direct owner source branch/identity')
        rows.append(dict(e))
    if (local is not None and local['status']=='available'
            and [e for e in rows if e['ancestor_depth']==0]!=local['entries']):
        raise ValueError('local prefix depth0 entries differ from full candidate')
    return {**raw,'entries':rows, **({"local_definition_entry_only":local} if local is not None else {})}



def normalize_definition_chain_prefix_depth8(raw):
    fields={'source','scope','status','unavailable_reason','receiver_type_id','depth_limit',
            'walk_complete','current_variable_table_observed','native_receiver_selected',
            'receiver_variable_index','declared_type_id','frontier_depth','frontier_context_present',
            'stable_double_read','rows'}
    if (type(raw) is not dict or raw.keys()!=fields
            or raw['source']!='native_gui_type635_definition_chain_prefix_depth8_12004'
            or raw['scope']!='visited_definition_prefix_depth8'
            or type(raw['receiver_type_id']) is not int or raw['receiver_type_id']!=635
            or type(raw['depth_limit']) is not int or raw['depth_limit']!=8
            or any(raw[k] is not False for k in ('walk_complete','current_variable_table_observed','native_receiver_selected'))
            or type(raw['stable_double_read']) is not bool or type(raw['rows']) is not list):
        raise ValueError('definition chain prefix schema/scope')
    observed=('receiver_variable_index','declared_type_id','frontier_depth','frontier_context_present')
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or raw['rows'] or any(raw[k] is not None for k in observed)):
            raise ValueError('unavailable definition prefix must preserve unknown')
        return dict(raw)
    if (raw['status']!='available' or raw['unavailable_reason'] is not None or not raw['stable_double_read']
            or not integer(raw['receiver_variable_index'],0,255)
            or type(raw['declared_type_id']) is not int or raw['declared_type_id']!=635
            or type(raw['frontier_depth']) is not int or raw['frontier_depth']!=8
            or raw['frontier_context_present'] is not True or len(raw['rows'])!=8):
        raise ValueError('definition prefix boundary/double-read incomplete')
    rows=[];entries=[]
    for depth,row in enumerate(raw['rows']):
        if (type(row) is not dict or row.keys()!={'ancestor_depth','definition_present',
                'raw_definition_entry_count','entries','parent_edge','parent_present'}
                or type(row['ancestor_depth']) is not int or row['ancestor_depth']!=depth
                or type(row['definition_present']) is not bool or row['parent_present'] is not True
                or type(row['entries']) is not list or len(row['entries'])>1
                or type(row['parent_edge']) is not str or row['parent_edge'] not in {'definition_108','context_e8'}):
            raise ValueError('definition prefix row/edge incomplete')
        if not row['definition_present']:
            if (row['raw_definition_entry_count'] is not None or row['entries']
                    or row['parent_edge']!='context_e8' or depth==0):
                raise ValueError('null definition cannot supply a table/definition edge')
        elif (not integer(row['raw_definition_entry_count'],0,256)
                or (row['entries'] and row['raw_definition_entry_count']==0)):
            raise ValueError('definition prefix entry count')
        for entry in row['entries']:
            if type(entry) is not dict or entry.get('ancestor_depth')!=depth:
                raise ValueError('definition prefix entry depth mismatch')
        entries.extend(row['entries']);rows.append(dict(row))
    # Existing production rules check all descriptor fields, widths and branches.
    envelope={k:raw[k] for k in FIELDS if k!='entries'}
    envelope.update(source=SOURCE,entries=entries)
    normalize_receiver_candidates(envelope)
    for row in rows:
        for entry in row['entries']:
            depth=row['ancestor_depth']
            if ((depth==0 and entry['entry_flag_4c']!=0)
                    or (depth>0 and entry['entry_flag_4c']!=0 and 0<=entry['entry_mode_40']<=1)):
                raise ValueError('definition prefix continues beyond a static native stop')
            if depth>0 and entry['entry_flag_4c']==0 and (
                    entry['provider_vtable_rva'] is not None or entry['provider_slot2_rva'] is not None
                    or entry['direct_owner_full_id'] is not None or entry['direct_owner_identity_verified']):
                raise ValueError('filtered parent entry cannot qualify provider/owner observation')
    return {**raw,'rows':rows}

def normalize_definition_frontier_continuation_depth8_12(raw):
    fields={'source','scope','status','unavailable_reason','receiver_type_id','start_depth','depth_limit',
            'current_variable_table_observed','native_receiver_selected','provider_invoked',
            'receiver_variable_index','declared_type_id','stop_depth','stop_reason','next_context_present',
            'stable_double_read','rows'}
    if type(raw) is dict and 'failure_diagnostic' in raw:fields=fields|{'failure_diagnostic'}
    if type(raw) is dict and 'static_direct_owner_switch_12004' in raw:fields=fields|{'static_direct_owner_switch_12004'}
    if (type(raw) is not dict or raw.keys()!=fields
            or raw['source']!='native_gui_type635_frontier_continuation_depth8_12_12004'
            or raw['scope']!='definition_frontier_depth8_through11'
            or type(raw['receiver_type_id']) is not int or raw['receiver_type_id']!=635
            or type(raw['start_depth']) is not int or raw['start_depth']!=8
            or type(raw['depth_limit']) is not int or raw['depth_limit']!=12
            or any(raw[k] is not False for k in ('current_variable_table_observed','native_receiver_selected','provider_invoked'))
            or type(raw['stable_double_read']) is not bool or type(raw['rows']) is not list or len(raw['rows'])>4):
        raise ValueError('frontier continuation schema/scope')
    if 'static_direct_owner_switch_12004' in raw and raw['status']!='available':
        raise ValueError('static owner switch requires an independently available source continuation')
    if 'failure_diagnostic' in raw:
        if raw['status']!='unavailable':raise ValueError('available continuation cannot contain a failed capture')
        normalize_receiver_failure(raw['failure_diagnostic'],max_depth=12)
    observed=('receiver_variable_index','declared_type_id','stop_depth','stop_reason','next_context_present')
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or raw['rows'] or any(raw[k] is not None for k in observed)):
            raise ValueError('unavailable continuation must preserve unknown')
        return dict(raw)
    if (raw['status']!='available' or raw['unavailable_reason'] is not None or not raw['stable_double_read']
            or not integer(raw['receiver_variable_index'],0,255)
            or type(raw['declared_type_id']) is not int or raw['declared_type_id']!=635
            or not integer(raw['stop_depth'],8,12)
            or type(raw['stop_reason']) is not str
            or raw['stop_reason'] not in {'null_end','cycle','static_direct_terminal','depth_limit'}):
        raise ValueError('frontier continuation boundary/double-read')
    rows=[];entries=[]
    for ordinal,row in enumerate(raw['rows']):
        depth=8+ordinal
        if (type(row) is not dict or row.keys()!={'ancestor_depth','definition_present',
                'raw_definition_entry_count','first_match_entry_index','entries','parent_edge','parent_present'}
                or type(row['ancestor_depth']) is not int or row['ancestor_depth']!=depth
                or type(row['definition_present']) is not bool
                or type(row['entries']) is not list or len(row['entries'])>1
                or type(row['parent_edge']) is not str
                or row['parent_edge'] not in {'definition_108','context_e8','not_read_native_static_stop'}
                or (row['parent_present'] is not None and type(row['parent_present']) is not bool)):
            raise ValueError('frontier continuation row/depth/edge')
        if not row['definition_present']:
            if row['raw_definition_entry_count'] is not None or row['entries'] or row['parent_edge']!='context_e8':
                raise ValueError('null continuation definition cannot supply a table/definition edge')
        elif (not integer(row['raw_definition_entry_count'],0,256)
                or (row['entries'] and row['raw_definition_entry_count']==0)):
            raise ValueError('frontier continuation definition count')
        if row['entries']:
            if not integer(row['first_match_entry_index'],0,row['raw_definition_entry_count']-1):
                raise ValueError('continuation first match index outside its definition table')
        elif row['first_match_entry_index'] is not None:
            raise ValueError('continuation no-match cannot claim a matching entry index')
        if row['parent_edge']=='definition_108' and row['parent_present'] is not True:
            raise ValueError('definition parent edge must have an actual nonnull parent')
        terminal=False
        for entry in row['entries']:
            if type(entry) is not dict or entry.get('ancestor_depth')!=depth:
                raise ValueError('frontier continuation entry depth')
            # Reuse production descriptor width/RVA/owner rules with an internal
            # ordinal rebasing only. This does not claim a native receiver.
            entries.append({**entry,'ancestor_depth':ordinal})
            if entry.get('entry_flag_4c')==0 and any(entry.get(k) is not None for k in
                    ('provider_vtable_rva','provider_slot2_rva','direct_owner_full_id')):
                raise ValueError('filtered continuation parent cannot supply provider/owner')
            if entry.get('entry_flag_4c')==0 and entry.get('direct_owner_identity_verified') is not False:
                raise ValueError('filtered continuation parent cannot verify owner')
            terminal=integer(entry.get('entry_mode_40'),0,1) and integer(entry.get('entry_flag_4c'),1,255)
        last=ordinal==len(raw['rows'])-1
        if terminal:
            if (not last or raw['stop_reason']!='static_direct_terminal'
                    or row['parent_edge']!='not_read_native_static_stop' or row['parent_present'] is not None):
                raise ValueError('continuation reads beyond a native static direct stop')
        elif row['parent_edge']=='not_read_native_static_stop' or row['parent_present'] is None:
            raise ValueError('continuation fabricates a static parent stop')
        if not last and row['parent_present'] is not True:
            raise ValueError('continuation continues beyond null/end')
        rows.append(dict(row))
    envelope={k:raw[k] for k in FIELDS if k!='entries'}
    envelope.update(source=SOURCE,entries=entries)
    normalize_receiver_candidates(envelope)
    reason=raw['stop_reason'];count=len(rows)
    if reason=='depth_limit':
        valid=count==4 and raw['stop_depth']==12 and raw['next_context_present'] is True and rows[-1]['parent_present'] is True
    elif reason=='null_end':
        valid=count>=1 and raw['stop_depth']==8+count and raw['next_context_present'] is False and rows[-1]['parent_present'] is False
    elif reason=='cycle':
        valid=count<=3 and raw['stop_depth']==8+count and raw['next_context_present'] is True and (not rows or rows[-1]['parent_present'] is True)
    else:
        valid=count>=1 and raw['stop_depth']==7+count and raw['next_context_present'] is None and rows[-1]['parent_edge']=='not_read_native_static_stop'
    if not valid:raise ValueError('continuation stop reason contradicts rows/frontier')
    extra={}
    if 'static_direct_owner_switch_12004' in raw:
        extra['static_direct_owner_switch_12004']=normalize_static_direct_owner_switch(raw['static_direct_owner_switch_12004'],rows)
    return {**raw,'rows':rows,**extra}

def normalize_local_definition_entry_only(raw):
    fields={"source","scope","status","unavailable_reason","receiver_type_id","ancestor_depth",
            "current_variable_table_observed","native_receiver_selected","receiver_variable_index",
            "declared_type_id","raw_definition_entry_count","local_definition_active_raw",
            "definition_present","local_entry_present","stable_double_read","entries"}
    if type(raw) is dict and "failure_diagnostic" in raw:fields=fields|{"failure_diagnostic"}
    if (type(raw) is not dict or raw.keys()!=fields
            or raw['source']!='native_gui_type635_local_definition_entry_only_12004'
            or raw['scope']!='local_definition_entry_only'
            or type(raw['receiver_type_id']) is not int or raw['receiver_type_id']!=635
            or type(raw['ancestor_depth']) is not int or raw['ancestor_depth']!=0
            or raw['current_variable_table_observed'] is not False or raw['native_receiver_selected'] is not False
            or type(raw['stable_double_read']) is not bool or type(raw['entries']) is not list or len(raw['entries'])>1):
        raise ValueError('local definition prefix schema/scope')
    if 'failure_diagnostic' in raw:
        if raw['status']!='unavailable':raise ValueError('local failure diagnostic cannot qualify available prefix')
        normalize_receiver_failure(raw['failure_diagnostic'])
    observed=('receiver_variable_index','declared_type_id','raw_definition_entry_count',
              'local_definition_active_raw','definition_present','local_entry_present')
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or raw['entries'] or any(raw[k] is not None for k in observed)):
            raise ValueError('unavailable local prefix must preserve unknown values')
        return dict(raw)
    if (raw['status']!='available' or raw['unavailable_reason'] is not None or not raw['stable_double_read']
            or not integer(raw['receiver_variable_index'],0,255)
            or type(raw['declared_type_id']) is not int or raw['declared_type_id']!=635
            or not integer(raw['raw_definition_entry_count'],0,256)
            or not integer(raw['local_definition_active_raw'],1,255)
            or raw['definition_present'] is not True or type(raw['local_entry_present']) is not bool
            or raw['local_entry_present'] is not bool(raw['entries'])
            or (raw['entries'] and raw['raw_definition_entry_count']==0)):
        raise ValueError('local prefix declaration/lookup/double-read is incomplete')
    # Reuse the production entry width/RVA/direct-owner rules; this synthetic
    # envelope is internal normalization only, never a native-selection claim.
    old={k:raw[k] for k in FIELDS}
    old['source']=SOURCE
    entries=normalize_receiver_candidates(old)['entries']
    if any(e['ancestor_depth']!=0 for e in entries):raise ValueError('local prefix entry is not depth0')
    return {**raw,'entries':entries}

def normalize_receiver_failure(raw,*,max_depth=8):
    fields={'stage','kind','capture_pass','read_ordinal','ancestor_depth','raw_declaration_count',
            'raw_index_count','raw_definition_entry_count','context_present','definition_present',
            'local_definition_active_raw'}
    if type(raw) is not dict or raw.keys()!=fields:
        raise ValueError('receiver failure diagnostic schema')
    # This is one failed capture's progress, not a stable receiver observation.
    for key in ('stage','kind'):
        if type(raw[key]) is not str or not raw[key] or len(raw[key])>64 or not all(
                c.isascii() and (c.islower() or c.isdigit() or c=='_') for c in raw[key]):
            raise ValueError('receiver failure diagnostic label')
    if not integer(raw['capture_pass'],1,2) or not integer(raw['read_ordinal'],0,4097):
        raise ValueError('receiver failed-capture pass/read ordinal')
    if raw['ancestor_depth'] is not None and not integer(raw['ancestor_depth'],0,max_depth):
        raise ValueError('receiver failure depth')
    for key in ('raw_declaration_count','raw_index_count','raw_definition_entry_count'):
        if raw[key] is not None and not integer(raw[key],-2**31,2**31-1):
            raise ValueError('receiver failure raw count')
    for key in ('context_present','definition_present'):
        if raw[key] is not None and type(raw[key]) is not bool:
            raise ValueError('receiver failure presence')
    if raw['local_definition_active_raw'] is not None and not integer(raw['local_definition_active_raw'],0,255):
        raise ValueError('receiver failure local active byte')
    return dict(raw)

def normalize_receiver_frame(raw):
    if type(raw) is not dict or raw.keys()!=FRAME:
        raise ValueError('receiver exact frame schema')
    for k in ('native_revision','connection_generation','pump_epoch','ticket_sequence'):
        if not integer(raw[k],1,2**64-1):raise ValueError('receiver frame epoch: '+k)
    for k in ('game_pid','thread_id'):
        if not integer(raw[k],1,2**32-1):raise ValueError('receiver frame process/thread')
    if not integer(raw['played_character_full_id'],-2**31,2**31-1) or raw['played_character_full_id']==-1 or not integer(raw['date_raw'],-2**31,2**31-1):
        raise ValueError('receiver frame Character/date')
    if any(raw[k] is not True for k in ('owner_thread_verified','frame_stable','gui_owner_stable')):
        raise ValueError('receiver frame owner/world binding unverified')
    return dict(raw)

def bind_receiver_frame(raw,before,after):
    frame=normalize_receiver_frame(raw)
    if type(before) is not dict or type(after) is not dict:
        raise ValueError('receiver frame needs current before/after snapshots')
    for s in (before,after):
        d=s.get('diagnostics') or {};h=d.get('hello') or {}
        if (s.get('paused') is not True or s.get('map_ready') is not True
                or s.get('native_revision')!=frame['native_revision']
                or s.get('date_raw')!=frame['date_raw']
                or (s.get('played_character') or {}).get('character_id')!=frame['played_character_full_id']
                or d.get('bridge_pid')!=frame['game_pid']
                or d.get('connection_generation')!=frame['connection_generation']
                or h.get('expected_ck3_version')!='1.20.0.4'
                or str(h.get('expected_ck3_sha256','')).lower()!='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'):
            raise ValueError('receiver leaf crossed exact native frame')
    keys=('snapshot_id','revision','native_revision','episode_run_id')
    if any(before.get(k) is None or before.get(k)!=after.get(k) for k in keys) or not before.get('episode_run_id'):
        raise ValueError('receiver public frame/episode changed')
    return {k:before[k] for k in keys}

def normalize_static_direct_owner_switch(raw,rows):
    fields={'source','scope','status','unavailable_reason','current_variable_table_observed',
            'native_receiver_selected','provider_invoked','ancestor_depth','owner_full_id',
            'military_component_present','raw_byte_4a9','enabled','value_basis','stable_double_read'}
    if (type(raw) is not dict or raw.keys()!=fields
            or raw['source']!='native_gui_type635_static_direct_owner_switch_12004'
            or raw['scope']!='static_direct_source_candidate'
            or any(raw[k] is not False for k in ('current_variable_table_observed','native_receiver_selected','provider_invoked'))
            or type(raw['stable_double_read']) is not bool):
        raise ValueError('static owner switch source/scope')
    observed=('ancestor_depth','owner_full_id','military_component_present','raw_byte_4a9','enabled','value_basis')
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or any(raw[k] is not None for k in observed)):
            raise ValueError('unavailable static switch must preserve unknown')
        return dict(raw)
    if (raw['status']!='available' or raw['unavailable_reason'] is not None or not raw['stable_double_read']
            or not integer(raw['ancestor_depth'],8,11)
            or not integer(raw['owner_full_id'],-2**31,2**31-1) or raw['owner_full_id']==-1
            or type(raw['military_component_present']) is not bool or type(raw['enabled']) is not bool):
        raise ValueError('static switch availability/identity')
    matching=[e for row in rows if row['ancestor_depth']==raw['ancestor_depth'] for e in row['entries']
              if e['entry_mode_40']==1 and e['entry_flag_4c']!=0 and e['direct_value_present']
              and e['direct_owner_identity_verified'] and e['direct_owner_full_id']==raw['owner_full_id']]
    if len(matching)!=1:raise ValueError('static switch lacks its verified source owner')
    if raw['military_component_present']:
        if (not integer(raw['raw_byte_4a9'],0,255) or raw['value_basis']!='raw_military_byte'
                or raw['enabled'] is not (raw['raw_byte_4a9']!=0)):
            raise ValueError('static switch raw byte/derived value')
    elif (raw['raw_byte_4a9'] is not None or raw['enabled'] is not False
            or raw['value_basis']!='native_null_military_zero'):
        raise ValueError('static switch native null component branch')
    return dict(raw)
