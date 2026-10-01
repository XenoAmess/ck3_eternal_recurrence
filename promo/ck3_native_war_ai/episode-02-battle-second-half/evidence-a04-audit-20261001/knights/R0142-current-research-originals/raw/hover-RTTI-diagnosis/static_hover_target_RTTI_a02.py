"""Only exact EXE/frozen source/original returned file bytes. No process IO."""
from pathlib import Path
import datetime,hashlib,json,struct
import pefile

OUT=Path(__file__).parent
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
ROOT=Path('C:/w/e2cap1001d')
EXE=Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')
def ident(p):
 raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest().upper()}
def copy(p,rel):
 dst=OUT/'exact-a02'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(p.read_bytes())
 a,b=ident(p),ident(dst);assert (a['bytes'],a['sha256'])==(b['bytes'],b['sha256'])
 return {'original':a,'copy':b,'exact_bytes':True}
copies=[]
for rel in ['ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp','ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp','ck3_autonomous_player/native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp','ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json']:
 copies.append(copy(ROOT/rel,Path('frozen-source')/rel))
p=LIVE/'ck3-output/interactive-requests-responses/before-left-knights-tooltip-native-hover.json'
copies.append(copy(p,Path('current-return')/p.name))
value=json.loads(p.read_text('utf-8-sig'));body=value['body']
assert body['unavailable_reason']=='current_combat_knight_text_target_unverified'
assert body['dispatch_invoked'] is False and body['current_subject_id']==16777218
assert body['date_raw']==53146848 and body['paused'] is True and body['thread_id']==7144
raw=Path(body['native_ui_raw_return_receipt']['path'])
assert ident(raw)['sha256']==body['native_ui_raw_return_receipt']['sha256'].upper()
copies.append(copy(raw,Path('original-parsed-result')/raw.name))
exeid=ident(EXE);assert exeid['sha256']=='2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
pe=pefile.PE(str(EXE),fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
reads=[]
def read(rva,size,label):
 assert 0<=rva and rva+size<=pe.OPTIONAL_HEADER.SizeOfImage and 0<size<=2048
 raw=pe.get_data(rva,size);assert len(raw)==size
 reads.append({'label':label,'rva':hex(rva),'bytes':size,'raw_hex':raw.hex()})
 return raw
def type_name(rva,label):
 return read(rva+16,160,label).split(b'\0',1)[0].decode('ascii')
targets=[w for w in body['tree']['widgets'] if w['runtime_name']=='left_knights']
assert len(targets)==1
target=targets[0];vtable=target['vtable_rva']
colva=struct.unpack('<Q',read(vtable-8,8,'current-vtable-COL-pointer-original-EXE'))[0]
colrva=colva-base
signature,offset,cd,td,chd,selfrva=struct.unpack('<6I',read(colrva,24,'original-RTTI-COL'))
assert signature==1 and selfrva==colrva
expected=0x5020010
hier_signature,attributes,count,array=struct.unpack('<4I',read(chd,16,'original-RTTI-CHD'))
assert 0<count<=32
baservas=struct.unpack('<'+'I'*count,read(array,count*4,'original-RTTI-base-class-array'))
bases=[]
for index,rva in enumerate(baservas):
 fields=struct.unpack('<7I',read(rva,28,'base-class-descriptor'+str(index)))
 bases.append({'descriptor_rva':hex(rva),'type_descriptor_rva':hex(fields[0]),'name':type_name(fields[0],'base-class-name'+str(index)),'raw_descriptor_fields':fields})
report={
 'schema':'ck3.R0142.native-hover-target-static-RTTI/v1',
 'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Frozen source and exact original EXE plus original returned JSON only. No live process read, native call, input, source or Git edit.',
 'original_EXE':exeid,'image_base_original':hex(base),'exact_copies':copies,
 'actual_native_failure':{k:body[k] for k in ['window_kind','current_subject_id','effective_visible','date_raw','paused','thread_id','pump_epoch','gui_context_address','gui_owner_address','dispatch_invoked','unavailable_reason','episode_run_id','queried_revision','queried_native_revision']},
 'actual_returned_widget':target,'original_target_RTTI':{'vtable_rva':hex(vtable),'COL_rva':hex(colrva),'COL_fields':{'signature':signature,'offset':offset,'constructor_displacement':cd,'type_descriptor_rva':hex(td),'hierarchy_rva':hex(chd),'self_rva':hex(selfrva)},'type_name':type_name(td,'actual-type-name'),'base_classes':bases},
 'source_required_RTTI':{'type_descriptor_rva':hex(expected),'name':type_name(expected,'source-required-type-name'),'matches_actual_exact_type':td==expected,'is_actual_base_class':any(b['type_descriptor_rva']==hex(expected) for b in bases)},
 'source_target_gate':'ingame_ui_navigation_v1.cpp235-240 requires TypedObject exact COL.type_descriptor==0x5020010; cpp594-597 also requires target+D8 equals original GuiContext.',
 'provider_gap':'Existing named-window GUI census serializes child_path/runtime_name/vtable_rva/visible/enabled but no raw target address, RTTI type descriptor or target+D8. Existing native UI result exposes global context/owner only, no target context. A current RPM could distinguish target-type vs target-context failure; static exact-type mismatch itself is independently checkable without RPM.',
 'failure_time_target_context_proven':False,'static_reads':reads,'script':ident(Path(__file__)),
}
report['diagnosis']='EXACT_TYPE_GATE_REJECTS_VALID_DERIVED_WIDGET' if td!=expected and report['source_required_RTTI']['is_actual_base_class'] else 'EXACT_TYPE_MATCH_OR_OTHER_RTTI_TO_REVIEW'
out=OUT/'native-hover-static-RTTI-diagnosis-a02.json'
with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':ident(out),'diagnosis':report['diagnosis'],'actual_RTTI':report['original_target_RTTI'],'expected_RTTI':report['source_required_RTTI']},ensure_ascii=False))
