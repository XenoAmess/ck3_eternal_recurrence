"""ROOT-only official SDK list_tools against exact frozen four-root export; no game callbacks."""
from pathlib import Path, PurePosixPath
import argparse, asyncio, hashlib, importlib.metadata, json, os, re, stat, sys
sys.dont_write_bytecode=True
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
ARCHIVE_ROOTS=('mod_li_yu_dao','ck3_autonomous_player','tools','ck3_workshop_mcp/src')
TOOLS=('ck3_query_native_profile_v1','ck3_attach_profile_bridge_v1','ck3_resume_profile_bridge_v1','ck3_take_profile_native_snapshot_v1','ck3_query_profile_character_interaction_ordinary_v1','ck3_initiate_profile_character_interaction_ordinary_v1','ck3_observe_profile_normal_exit_v1','ck3_query_normal_exit_context_v1','ck3_request_normal_exit_v1','ck3_query_profile_current_actor_stress_adjustment_v1','ck3_query_profile_event_window_v1','ck3_query_profile_pending_interaction_v1','ck3_reply_profile_pending_interaction_v1','ck3_set_profile_simulation_v1','ck3_pause_profile_simulation_v1','ck3_select_profile_event_option_v1','ck3_save_profile_checkpoint_v1','ck3_query_profile_decision_item_v1','ck3_open_profile_decisions_v1','ck3_select_profile_decision_item_v1','ck3_confirm_profile_decision_outcome_v1')
def strip_extended_path(value):
    raw=str(value);prefix=chr(92)*2+'?'+chr(92)
    if raw.startswith(prefix):
        tail=raw[len(prefix):]
        raw=chr(92)*2+tail[4:] if tail[:4].upper()=='UNC'+chr(92) else tail
    elif raw.startswith('//?/'):
        tail=raw[4:];raw='//'+tail[4:] if tail[:4].upper()=='UNC/' else tail
    return raw

def long_path(value):
    raw=strip_extended_path(value)
    p=Path(raw)
    if not p.is_absolute():raise ValueError('Explicit absolute path required')
    raw=str(p.absolute())
    if os.name=='nt':
        raw=chr(92)*2+'?'+chr(92)+'UNC'+chr(92)+raw[2:] if raw.startswith(chr(92)*2) else chr(92)*2+'?'+chr(92)+raw
    return Path(raw)

def no_links(value):
    p=Path(strip_extended_path(value))
    for part in (p.absolute(),*p.absolute().parents):
        q=long_path(part)
        if not q.exists() and not q.is_symlink():continue
        info=q.lstat()
        if q.is_symlink() or q.is_junction() or getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('Symlink/junction/reparse refused: '+str(part))

def path_identity(value):
    p=Path(strip_extended_path(value))
    if not p.is_absolute() or '..' in p.parts or any(c in str(p) for c in (chr(0),chr(10),chr(13),chr(34))):
        raise ValueError('Explicit absolute path without traversal required')
    no_links(p)
    return Path(strip_extended_path(long_path(p).resolve()))

def read_bytes(value):
    p=path_identity(value)
    return long_path(p).read_bytes()

def need(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def exact(obj,fields,label):need(type(obj)is dict and set(obj)==set(fields),label+' closed fields differ');return obj
def jread(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def source_path(name):
    need(type(name)is str,'normalized source path required')
    p=PurePosixPath(name);need(name==p.as_posix() and not p.is_absolute() and '..'not in p.parts and '\\'not in name and ':'not in name,'source path escapes')
    return name
def four_roots(paths):
    roots=set()
    for path in paths:
        path=source_path(path);matches=[r for r in ARCHIVE_ROOTS if path.startswith(r+'/')]
        need(len(matches)==1,'actual source outside exact four archive roots');roots.add(matches[0])
    need(roots==set(ARCHIVE_ROOTS),'actual fourth workshop src root absent')
def ref(p):
    b=read_bytes(p);return {'path':path_identity(p).as_posix(),'bytes':len(b),'sha256':digest(b)}
def read_ref(value):
    exact(value,{'path','bytes','sha256'},'actual export reference')
    need(type(value['path'])is str and Path(value['path']).is_absolute() and type(value['bytes'])is int and value['bytes']>=0 and type(value['sha256'])is str and re.fullmatch('[0-9a-f]{64}',value['sha256']),'actual export ref stamp differs')
    p=path_identity(value['path']);need(not p.is_relative_to(path_identity('C:/workspace/ck3_eternal_recurrence')),'main tree is not frozen export')
    raw=read_bytes(p);need(len(raw)==value['bytes'] and digest(raw)==value['sha256'],'actual export ref changed');return raw
