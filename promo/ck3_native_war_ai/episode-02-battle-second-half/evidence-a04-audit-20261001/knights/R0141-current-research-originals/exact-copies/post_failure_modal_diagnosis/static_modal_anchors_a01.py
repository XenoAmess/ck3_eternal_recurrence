from pathlib import Path
import json, hashlib, datetime
import pefile, capstone
OUT=Path(__file__).parent
EXE=Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')
EXPECTED='2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
def identity(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest().upper()}
exe_ident=identity(EXE);assert exe_ident['sha256']==EXPECTED
pe=pefile.PE(str(EXE),fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']])
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
targets={'DefaultOnCharacterClick':0xA04530,'NativeShortcutManagerActivate':0x36E1C40,'StrictDescendant':0x369E620,'DeliverGuiEvent':0x36CB4A0}
report={'schema':'ck3.R0141.modal-static-anchors/v1','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_private_commit':'fda53e7b3e83053f235be3d5725a6238b89db9f0','evidence_level':'exact-build-static-original-bytes; no native invocation','executable':exe_ident,'functions':[],'sources':[],'human_signoff':False,'live_capture':False}
for name,rva in targets.items():
    fns=[e.struct for e in pe.DIRECTORY_ENTRY_EXCEPTION if e.struct.BeginAddress<=rva<e.struct.EndAddress]
    assert len(fns)==1
    fn=fns[0];assert fn.BeginAddress==rva
    size=fn.EndAddress-rva;assert 0<size<16384
    raw=pe.get_data(rva,size);assert len(raw)==size
    binary=OUT/(name+'-original-rva-'+hex(rva)+'.bin')
    with binary.open('xb') as f:f.write(raw)
    instructions=[{'rva':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(raw,rva)]
    text=OUT/(name+'-disassembly-a01.txt')
    with text.open('x',encoding='utf-8',newline='\n') as f:
        for i in instructions:f.write(i['rva']+': '+i['bytes']+'  '+i['mnemonic']+' '+i['operands']+'\n')
    report['functions'].append({'name':name,'rva_begin':hex(rva),'rva_end':hex(fn.EndAddress),'pdata_original_unwind_rva':hex(fn.UnwindData),'raw':identity(binary),'disassembly':identity(text),'instructions':instructions})
source_root=Path('C:/w/e2cap1001c')
for rel in [
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1_serializer.cpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1.cpp',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_scoreboard_state_contract.py',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py',
 'ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json',
 'docs/ck3-native-ai/zhongguo-scoreboard-state-v1.md']:
    source=source_root/rel;dest=OUT/'frozen-source-exact-copies'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
    source_id=identity(source);copy_id=identity(dest);assert source_id['sha256']==copy_id['sha256']
    report['sources'].append({'original':source_id,'copy':copy_id,'same_bytes':True})
report['script']=identity(Path(__file__))
dest=OUT/'static-modal-anchors-a01.json'
with dest.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':identity(dest),'functions':[{'name':f['name'],'begin':f['rva_begin'],'end':f['rva_end'],'bytes':f['raw']['bytes']} for f in report['functions']]},ensure_ascii=False))
