from pathlib import Path
import hashlib,json,re,struct,datetime
root=Path('C:/lr21rw1');out=Path(__file__).parent
native=root/'ck3_autonomous_player/native_bridge'
launch=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-022/launch.json');exe=Path(json.loads(launch.read_bytes())['argv'][0])
expected_sha='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
hasher=hashlib.sha256()
with exe.open('rb') as f:
 while True:
  chunk=f.read(1024*1024)
  if not chunk:break
  hasher.update(chunk)
sha=hasher.hexdigest();assert exe.stat().st_size==101040248 and sha==expected_sha
with exe.open('rb') as f:
 dos=f.read(64);assert dos[:2]==b'MZ';peoff=struct.unpack_from('<I',dos,0x3c)[0]
 f.seek(peoff);header=f.read(24);assert header[:4]==b'PE\0\0'
 machine,count=struct.unpack_from('<HH',header,4);size_optional=struct.unpack_from('<H',header,20)[0];assert machine==0x8664
 f.seek(peoff+24+size_optional);sections=[]
 for i in range(count):
  row=f.read(40);name=row[:8].rstrip(b'\0').decode('ascii');virtual_size,rva,raw_size,raw_offset=struct.unpack_from('<IIII',row,8);flags=struct.unpack_from('<I',row,36)[0]
  sections.append({'name':name,'rva':rva,'virtual_size':virtual_size,'raw_size':raw_size,'raw_offset':raw_offset,'flags':flags})
inc=native/'src/normal_exit_map_pins_v1.inc';text=inc.read_text('utf-8-sig')
pins=re.findall(r'\{(0x[0-9A-Fa-f]+),\{([^}]+)\}\}',text);assert len(pins)==4
headers=[native/'include/xar_bridge/zhongguo_scoreboard_state_v1.hpp',native/'include/xar_bridge/zhongguo_scoreboard_action_v1.hpp']
joined='\n'.join(p.read_text('utf-8-sig') for p in headers)
names=['kCrozier12004GuiFindTopLevelWidgetRva','kCrozier12004ShortcutManagerActivateRva','kCrozier12004StrictDescendantRva','kCrozier12004ButtonBaseSlot13Rva']
rows=[]
with exe.open('rb') as f:
 for i,(name,(old_rva,expected_text)) in enumerate(zip(names,pins,strict=True)):
  rva=int(re.search(r'\b'+name+r'\s*=\s*(0x[0-9A-Fa-f]+)',joined).group(1),16)
  expected=bytes(int(s,16) for s in expected_text.split(','));assert len(expected)==32
  section=next(s for s in sections if s['rva']<=rva and rva+32<=s['rva']+s['raw_size']);assert section['name']=='.text' and section['flags']&0x20000000
  offset=section['raw_offset']+rva-section['rva'];f.seek(offset);actual=f.read(32);assert len(actual)==32
  target=out/(f'{i+1:02d}-'+name+'.actual32.bin')
  with target.open('xb') as stream:stream.write(actual)
  rows.append({'symbol':name,'legacy_pin_rva':old_rva,'actual4_header_rva':hex(rva),'file_offset':offset,'section':section['name'],'expected_prefix_hex':expected.hex(),'actual_prefix_hex':actual.hex(),'exact_prefix_equal':actual==expected,'prefix_sha256':hashlib.sha256(actual).hexdigest(),'raw_prefix_path':str(target)})
proof=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-022/mcp-client-001/0007-r22-007-normal-exit-readonly.native-01.json');raw=proof.read_bytes();assert len(raw)==39223 and hashlib.sha256(raw).hexdigest()=='d221adaf0c18896f6d9f53146cf1134d2fba96fc132596ffb9487fee510321e9'
with (out/'ORIGINAL-R22-NORMAL-EXIT-READONLY.native.json').open('xb') as f:f.write(raw)
observation=json.loads(raw)['result']['native_observation']
assert observation['exact_build_verified'] is True and observation['source_abi_pins_verified'] is False and observation['reason']=='exact_gui_code_pins_changed'
assert not any(d['dispatch_invoked'] for d in observation['dispatches'])
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
result={'schema':'lyd.r22.actual4-normal-exit-static-pin-comparison.v1','started_at_utc':start,'ended_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exe':{'path':str(exe),'bytes':exe.stat().st_size,'sha256':sha},'source_refs':[ref(inc)]+[ref(p)for p in headers]+[ref(native/'src/normal_exit_map_v1.cpp'),ref(native/'src/bridge.cpp')],'original_native_receipt':ref(proof),'observed_reason':observation['reason'],'pre_pin_read_environment_admission_missing_SHA_proven':True,'rows':rows,'all_four_exact_32byte_prefixes_equal':all(row['exact_prefix_equal'] for row in rows),'new_pin_or_RVA_mapping_added':False,'native_memory_SDK_process_or_runtime_build_used':False,'runtime_native_exit_credit':None}
with (out/'RESULT.actual.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'rows':rows,'result':ref(out/'RESULT.actual.json')},ensure_ascii=False))
