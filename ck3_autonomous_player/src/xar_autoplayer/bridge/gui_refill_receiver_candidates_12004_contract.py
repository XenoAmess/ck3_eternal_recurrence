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
    if (type(raw) is not dict or raw.keys()!=FIELDS or raw['source']!=SOURCE
            or type(raw['receiver_type_id']) is not int or raw['receiver_type_id']!=635
            or raw['current_variable_table_observed'] is not False
            or raw['native_receiver_selected'] is not False
            or type(raw['stable_double_read']) is not bool or type(raw['entries']) is not list
            or len(raw['entries'])>8):
        raise ValueError('type635 candidate schema/qualification')
    if raw['status']=='unavailable':
        if (type(raw['unavailable_reason']) is not str or not raw['unavailable_reason']
                or raw['stable_double_read'] or raw['entries']
                or raw['receiver_variable_index'] is not None or raw['declared_type_id'] is not None):
            raise ValueError('unavailable candidate must preserve unknown values')
        return dict(raw)
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
    return {**raw,'entries':rows}

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
