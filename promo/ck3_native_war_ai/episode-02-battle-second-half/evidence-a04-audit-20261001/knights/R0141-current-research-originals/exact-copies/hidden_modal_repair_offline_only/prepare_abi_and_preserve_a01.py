from pathlib import Path
import datetime, hashlib, difflib, json
OUT=Path(__file__).parent
ROOT=Path('C:/w/e2research1001');OLD=Path('C:/w/e2cap1001c')
def ident(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
abi_rel='ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json'
original=(ROOT/abi_rel).read_bytes();assert original==(OLD/abi_rel).read_bytes()
abi=json.loads(original.decode('utf-8-sig'))
abi['functions']['SetHoveredWidget']['target']=abi['functions']['SetHoveredWidget']['target'].replace('modal_count0','bounded original modal vector: count0 or all effective-hidden; any effective-visible receiver refused')
abi['modal_admission_revision_v2']={
 'trigger':'R0141 actual owner/TLS/GUI binding passed; count-only gate refused navigation. Original parsed unavailable stays RED/no-day.',
 'evidence_level':'exact original EXE bytes + two later readonly PID6320 memory reads; source/offline validation; new live pending',
 'original_exact_EXE_sha256':abi['executable_sha256'],
 'original_shortcut_manager_rva':'0x36E1C40..0x36E1D35',
 'effective_hidden_scan_rva':'0x36E1C70..0x36E1CA6',
 'count_layout':'GUI context signed int32 +0x29C, bounded 0..256; vector data +0x290, pointer stride8; receiver flags +0xD0 bit08 is effective-hidden cache',
 'policy':'all global open/select/hover/fit actions reject any effective-visible receiver; count0 or fully readable all-hidden receivers allowed; no exception by runtime_name and no native descendant allowance',
 'failed_read_policy':'header/negative/excessive count/null vector/null or unreadable entries/unreadable flags/header change => unavailable; GUI context/owner equality and all original main-thread paused/fullID/actor guards preserved',
 'raw_native_diagnostic':'modal_admission object: attempted/header_read/receivers_verified/actual signed count or null/vector address/observed receiver addresses and D0 flags/effective-visible count/reason; existing driver create-only original parsed command_result persists it before validation. No new public MCP parameters or extra gameplay capability.',
 'MCP_normalized_scope':'Optional raw diagnostic remains in original parsed return; no claim that the current Python normalized UI response publishes it.',
 'readonly_current_memory_report':'C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-modal-admission-diagnosis-other-a01/readonly-modal-receivers-a01.json',
 'readonly_current_memory_SHA256':'FDC019E55D420FB7BBCF54B4F76470EABF086B18981B071C668A0A681EAD283F',
 'static_anchors_report_SHA256':'4165872C563931C331CDF2537041D9BA705C690A2226A2E32ED5AC005F0B32FE',
 'temporal_limit':'Later RPM does not reconstruct the failed call execution-time count/vector; the failed native reason had conflated resolver/pointer/read/count branches.',
 'live_claim':False,'human_approval_created':False
}
with (ROOT/abi_rel).open('w',encoding='utf-8',newline='\n') as f:json.dump(abi,f,ensure_ascii=False,indent=2);f.write('\n')
rels=['ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp','ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp','ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',abi_rel]
items=[]
for rel in rels:
    old=OLD/rel;new=ROOT/rel;dest=OUT/'original-fda-exact-copies'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(old.read_bytes())
    assert ident(old)['sha256']==ident(dest)['sha256']
    diff=''.join(difflib.unified_diff(old.read_text('utf-8-sig').splitlines(True),new.read_text('utf-8-sig').splitlines(True),fromfile=str(old),tofile=str(new)))
    diff_path=OUT/'source-deltas'/Path(rel).name;diff_path.parent.mkdir(parents=True,exist_ok=True)
    with diff_path.open('x',encoding='utf-8',newline='\n') as f:f.write(diff)
    items.append({'old':ident(old),'old_copy':ident(dest),'current':ident(new),'diff':ident(diff_path)})
receipt={'schema':'ck3.R0141.ui-hidden-modal-source-intent/v1','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_private_base':'fda53e7b3e83053f235be3d5725a6238b89db9f0','four_changed_sources':items,'no_Git_no_frozen_source_no_live_io':True,'R0141_original_unavailable_preserved':True,'new_live_pending':True}
dest=OUT/'source-change-intent-a01.json'
with dest.open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(ident(dest)))
