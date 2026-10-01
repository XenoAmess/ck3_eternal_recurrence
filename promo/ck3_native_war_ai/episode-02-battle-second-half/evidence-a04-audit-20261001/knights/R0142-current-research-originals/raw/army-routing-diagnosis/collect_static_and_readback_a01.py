"""Only frozen sources, original files and static EXE reads; no process/game IO."""
from pathlib import Path
import datetime,hashlib,json,collections
import pefile,capstone
OUT=Path(__file__).parent
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
ROOT=Path('C:/w/e2cap1001d')
CTRL=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
EXE=Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')
def ident(p):
 h=hashlib.sha256();size=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
 return {'path':str(p.resolve()),'bytes':size,'sha256':h.hexdigest().upper()}
def write(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def copy(p,sub):
 d=OUT/sub;d.parent.mkdir(parents=True,exist_ok=True)
 with p.open('rb') as inp,d.open('xb') as out:
  for b in iter(lambda:inp.read(1024*1024),b''):out.write(b)
 original=ident(p);result=ident(d);assert original['sha256']==result['sha256'] and original['bytes']==result['bytes']
 return {'original':original,'copy':result,'exact_bytes':True}
bind=json.loads((CTRL/'current-run-bindings.json').read_text('utf-8-sig'))
assert bind['source_commit']=='4ad477ee33e15a93e412f711c7b05b216a2e6651' and bind['native_session_binding']['bridge_pid']==14700
report={'schema':'ck3.R0142.army-in-combat-routing-static-readback/v1','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_run_identity':{k:bind[k] for k in ['source_commit','run_id','native_session_binding','before_date_raw','combat_id','public_unit_id']},'scope':'Frozen source/original files/static EXE only; no native calls, RPM, game API, input, source/Git modification.','exact_copies':[],'native_readbacks':[],'functions':[],'pixel_ID_inference':False,'source_write':False,'game_day_command':False}
report['exact_copies'].append(copy(CTRL/'current-run-bindings.json','exact/current-run-bindings.json'))
for rel in ['ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp','ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json','ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py']:
 report['exact_copies'].append(copy(ROOT/rel,Path('exact/frozen-source')/rel))
for rel in [
 'scoped-ui-research-attempt-01/army-visibility-readonly-diagnostic.json',
 'scoped-ui-research-attempt-01/army-visibility-readonly-diagnostic-window-receipt.json',
 'ck3-output/interactive-requests-responses/before-army-source-snapshot.json',
 'ck3-output/interactive-requests-responses/before-army-open.json',
 'ck3-output/interactive-requests-responses/before-army-readback.json',
 'ck3-output/interactive-requests-responses/army-visibility-diagnostic-readonly.json',
 'ck3-output/interactive-requests-responses/army-visibility-diagnostic-post-readonly.json']:
 p=LIVE/rel
 if not p.exists():continue
 report['exact_copies'].append(copy(p,Path('exact/current-originals')/rel))
 v=json.loads(p.read_text('utf-8-sig'));body=v.get('body')
 if isinstance(body,dict):
  report['native_readbacks'].append({'path':str(p),'result':v.get('result'),'fields':{k:body[k] for k in ['schema','status','accepted','available','window_kind','requested_subject_id','current_subject_id','subject_id_available','native_army_id','owner_character_id','effective_visible','dispatch_invoked','date_raw','paused','played_character_id','native_revision','thread_id','pump_epoch','episode_run_id','queried_snapshot_id','queried_revision','queried_native_revision','queried_connection_generation'] if k in body},'player_armies':body.get('player_armies',[]),'raw_result_receipt':body.get('native_ui_raw_return_receipt')})
  receipt=body.get('native_ui_raw_return_receipt')
  if isinstance(receipt,dict) and Path(receipt['path']).is_file():report['exact_copies'].append(copy(Path(receipt['path']),Path('exact/native-parsed-results')/Path(receipt['path']).name))
 png=LIVE/'scoped-ui-research-attempt-01/army-visibility-readonly-diagnostic-window.png'
 if png.exists() and 'original_diagnostic_PNG' not in report:report['original_diagnostic_PNG']=ident(png)
exeid=ident(EXE);assert exeid['sha256']=='2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
report['executable']=exeid
pe=pefile.PE(str(EXE),fast_load=True);pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']])
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
targets={'SelectUnit':0xA7F050,'RouteSelectedUnitViews':0xA812F0,'OriginalArmyMapClick':0xE7E170,'OriginalCombatMapClick':0xE7CAC0}
for name,rva in targets.items():
 fns=[e.struct for e in pe.DIRECTORY_ENTRY_EXCEPTION if e.struct.BeginAddress<=rva<e.struct.EndAddress];assert len(fns)==1
 fn=fns[0];assert fn.BeginAddress==rva and fn.EndAddress-rva<32768
 raw=pe.get_data(rva,fn.EndAddress-rva)
 binary=OUT/(name+'-original-'+hex(rva)+'.bin')
 with binary.open('xb') as f:f.write(raw)
 ins=[{'rva':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(raw,rva)]
 text=OUT/(name+'-disassembly-a01.txt')
 with text.open('x',encoding='utf-8',newline='\n') as f:
  for i in ins:f.write(i['rva']+': '+i['bytes']+'  '+i['mnemonic']+' '+i['operands']+'\n')
 report['functions'].append({'name':name,'rva_begin':hex(rva),'rva_end':hex(fn.EndAddress),'pdata_unwind_rva':hex(fn.UnwindData),'original_bytes':ident(binary),'disassembly':ident(text),'instructions':ins})
report['script']=ident(Path(__file__))
path=OUT/'static-and-raw-readback-a01.json';write(path,report)
print(json.dumps({'report':ident(path),'readbacks':report['native_readbacks'],'functions':[{'name':r['name'],'begin':r['rva_begin'],'end':r['rva_end'],'bytes':r['original_bytes']['bytes']} for r in report['functions']]},ensure_ascii=False))
