"""Verify new nonwar rare-schedule inputs in frozen files; reuse reform proof."""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE=Path(__file__).resolve().parent
MAP=HERE/'religion_reform12002_schedule_abi.json'
HEADER=HERE.parent/'include/xar_bridge/religion_reform12002_schedule.hpp'
SHA='ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
REUSED_SHA='30d1baac976bcb0fd954cc0e53471cb6668b7f600891692480d57a8f2d7dd1f0'
SPANS=[
    ('AI.prepare_clock_result',0x19EA5E0,0x19EA782),
    ('Character.highest_tier',0x28AC6B0,0x28AC73C),
    ('Character.IsIndependentRuler',0x28C0000,0x28C0028),
    ('Character.IsIndependentRuler.reflection',0x28CF2B0,0x28CF2E8),
    ('Character.government_getter',0x28C2E10,0x28C2EFD),
    ('player_instance.special_AI',0x1A32CF0,0x1A32DAE),
]
SLICES=[
    ('CAIManager.vtable_install',0x1A2E28D,0x1A2E2A2),
    ('prepare.master_AI_gate',0x1A304C0,0x1A304D0),
    ('prepare.AI_holder_and_cache',0x1A305AC,0x1A30620),
    ('prepare.candidates_budget_and_selected',0x1A30A53,0x1A30D14),
    ('AI.rare_clock_phase_initialization',0x19E7DC2,0x19E7E83),
    ('AI.rare_clock_reset',0x19E8ADA,0x19E8AFF),
    ('AI.cache_gate_write_sources',0x1A22D30,0x1A22DCE),
    ('AI.state_initialization',0x1ACBBCD,0x1ACBC02),
    ('IsIndependentRuler.registration',0x55A013,0x55A0A4),
    ('NAI.MAX_TICK_STALENESS.name_binding',0x1A3E5B0,0x1A3E5CD),
    ('NAI.RARE_TASK_TICK.array_binding',0x1A3DBC0,0x1A3DBE1),
]
SITES=[
    ('AI_manager_secondary_vtable',0x1A2E297),
    ('master_AI_enabled_gate',0x1A304C3),
    ('AI_holder',0x1A305AC),('active_AI_gate',0x1A305D3),
    ('clock_result_call',0x1A3060E),('cache_output_AI_plus8',0x1A30613),
    ('cache_refresh_call',0x1A3061B),
    ('clear_selection',0x19EA71F),('countdown_begin',0x19EA72A),
    ('countdown_end',0x19EA731),('decrement_countdown',0x19EA740),
    ('overdue_staleness',0x1A30A88),('rare_budget_periods',0x1A30B4D),
    ('budget_index6',0x1A30B86),('selected_lane',0x1A30CDC),
    ('initial_tier_call',0x19E7DC7),('initial_rare_periods',0x19E7E18),
    ('phase_lane_multiplier',0x19E7E64),('phase_actor_ID',0x19E7E69),
    ('phase_modulo',0x19E7E6C),('phase_plus_one',0x19E7E6E),
    ('reset_tier_call',0x19E8AE7),('reset_rare_periods',0x19E8AEF),
    ('reset_countdown',0x19E8AF9),
    ('cache_government_getter',0x1A22D51),('government_flags_word',0x1A22D5C),
    ('government_flags_cache',0x1A22D60),('independent_flag_cache',0x1A22DCB),
    ('AI_initial_active_special',0x1ACBBFB),('player_AI_special',0x1A32D98),
    ('independent_reflection_name',0x55A013),('independent_reflection_binding',0x55A094),
    ('independent_reflection_getter',0x28CF2C2),
    ('MAX_TICK_STALENESS_global',0x1A3E5B3),
    ('MAX_TICK_STALENESS_name',0x1A3E5C1),('RARE_TASK_TICK_global',0x1A3DBC9),
    ('daily_manager_thunk_slot10',0x110CD03),('AI_thunk_slot8',0x9D09F3),
    ('manager_binder_function',0x2988BF7),
    ('daily_pre_stage_slot10',0x2967712),('daily_true_predicate_slot20',0x296771B),
    ('daily_true_path_call',0x2967728),('daily_post_stage_slot18',0x296773B),
    ('true_path_daily_slot8',0x2967912),('daily_date_advance_call',0x29881E7),
    ('game_date_add24',0x22A0E8D),('daily_AI_execute_call',0x2989031),
    ('AI_state_constructor',0x2ADC641),('AI_manager_array_registration',0x2ADBB80),
    ('daily_command_primary_vtable',0x25A9EA3),('daily_command_secondary_vtable',0x25A9EAE),
    ('daily_command_queue_call',0x25A9EC2),('pre_stage_tomorrow_date',0x2988313),
]
BINDINGS={
    'kScheduleHighestTierRva':0x28AC6B0,'kScheduleIndependentRulerRva':0x28C0000,
    'kScheduleRarePeriodsRva':0x5449D90,'kScheduleReformationToggleRva':0x5448579,
    'kScheduleActorIdOffset':0x18,'kScheduleActorTagOffset':0x1C,
    'kScheduleAIActorOffset':0x18,'kScheduleAIExtensionOffset':0x20,
    'kScheduleAIGovernmentFlagsOffset':0x14,'kScheduleAIIndependentFlagsOffset':0x16,
    'kScheduleAIActiveOffset':0x2C,'kScheduleAISpecialOffset':0x2E,
    'kScheduleRareCountdownOffset':0x284,'kScheduleRareSelectedOffset':0x29B,
}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True,type=Path);p.add_argument('--game',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--record',action='store_true')
    a=p.parse_args();data=a.exe.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Exact EXE differs')
    reused=(HERE/'religion_reform12002_willingness_abi.json').read_bytes()
    if hashlib.sha256(reused).hexdigest()!=REUSED_SHA:raise ValueError('Frozen reform ABI differs')
    old=json.loads(reused);pe=PeImage(data);cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    def read(rva,n):off=pe.rva_to_offset(rva);return data[off:off+n]
    day_path=HERE/'religion_reform12002_schedule_day.json'
    day=json.loads(day_path.read_text(encoding='utf8'))
    if day['exe_sha256']!=SHA:raise ValueError('Daily chain exact build differs')
    day_spans=[];day_slices=[]
    for region in day['regions']:
        start=int(region['begin_rva'],0);end=int(region['end_rva_exclusive'],0)
        raw=read(start,end-start)
        if raw.hex()!=region['hex'] or hashlib.sha256(raw).hexdigest()!=region['sha256']:
            raise ValueError(region['name'])
        row=(region['name'],start,end)
        (day_spans if region['kind'].startswith('complete_') else day_slices).append(row)
    all_spans=SPANS+day_spans;all_slices=SLICES+day_slices
    header=HEADER.read_text(encoding='utf-8-sig')
    for name,value in BINDINGS.items():
        m=re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)',header)
        if not m or int(m[1],0)!=value:raise ValueError(name)
    spans=[];dump=[]
    for name,start,end in all_spans+all_slices:
        raw=read(start,end-start)
        spans.append({'name':name,'start_rva':hex(start),'end_exclusive_rva':hex(end),
                      'kind':'complete_function' if (name,start,end) in all_spans else 'slice',
                      'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex(' ')})
        dump.append(f'{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:09X} {i.bytes.hex(" "):36s} {i.mnemonic} {i.op_str}' for i in cs.disasm(raw,start))
    instructions=[]
    for name,rva in SITES:
        i=next(cs.disasm(read(rva,15),rva))
        instructions.append({'name':name,'rva':hex(rva),'bytes':i.bytes.hex(' '),
            'instruction':f'{i.mnemonic} {i.op_str}',
            'rip_targets':[hex(i.address+i.size+o.mem.disp) for o in i.operands if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP],
            'direct_targets':[hex(o.imm) for o in i.operands if o.type==X86_OP_IMM and i.mnemonic in ('call','jmp')]})
    by={x['name']:x for x in instructions}
    for name,target in [('clock_result_call',0x19EA5E0),('cache_refresh_call',0x1A22D30),
        ('initial_tier_call',0x28AC6B0),('reset_tier_call',0x28AC6B0),
        ('cache_government_getter',0x28C2E10),('independent_reflection_getter',0x28C0000),
        ('daily_true_path_call',0x29677E0),('daily_date_advance_call',0x22A0D80),
        ('daily_AI_execute_call',0x1A31EE0),('AI_state_constructor',0x1A2E260),
        ('AI_manager_array_registration',0x880340),('daily_command_queue_call',0x9E16B0)]:
        if by[name]['direct_targets']!=[hex(target)]:raise ValueError(name)
    for name,target in [('AI_manager_secondary_vtable',0x45AC5F8),('master_AI_enabled_gate',0x542FF82),
        ('overdue_staleness',0x5C68758),('rare_budget_periods',0x5449D90),
        ('initial_rare_periods',0x5449D90),('reset_rare_periods',0x5449D90),
        ('independent_reflection_name',0x4761EA8),('independent_reflection_binding',0x28CF2B0),
        ('MAX_TICK_STALENESS_global',0x5C68758),('MAX_TICK_STALENESS_name',0x45ACD70),
        ('RARE_TASK_TICK_global',0x5449D90),('manager_binder_function',0x110CD00),
        ('daily_command_primary_vtable',0x44B5018),('daily_command_secondary_vtable',0x44B50B0)]:
        if by[name]['rip_targets']!=[hex(target)]:raise ValueError(f'{name}: {by[name]} expected {target:#x}')
    for name,text in [('daily_manager_thunk_slot10','jmp qword ptr [rax + 0x10]'),
        ('AI_thunk_slot8','jmp qword ptr [rax + 8]'),
        ('daily_pre_stage_slot10','call qword ptr [rax + 0x10]'),
        ('daily_true_predicate_slot20','call qword ptr [rax + 0x20]'),
        ('daily_post_stage_slot18','call qword ptr [rax + 0x18]'),
        ('true_path_daily_slot8','call qword ptr [rax + 8]'),
        ('game_date_add24','add dword ptr [rsi + 8], 0x18')]:
        if by[name]['instruction']!=text:raise ValueError(name)
    for rva,text in [(0x4761EA8,b'IsIndependentRuler\0'),(0x45ACD70,b'MAX_TICK_STALENESS\0')]:
        if read(rva,len(text))!=text:raise ValueError('Reflection/define name')
    slots=[(0x45AC5F8,8,0x1A304A0),(0x45AC5F8,0x30,0x1A31EE0)]
    slots.extend((int(x['vtable_rva'],0),int(x['slot'],0),int(x['target_rva'],0)) for x in day['vtable_slots'])
    for vt,slot,target in slots:
        if struct.unpack('<Q',read(vt+slot,8))[0]-pe.image_base!=target:raise ValueError('AI manager vtable')
    for vt,col,tag,offset in [(0x45AC5F8,0x4BF0E10,'.?AVCAIManager@@',8),
                             (0x44B50B0,0x4A4CCC8,'.?AVCDailyTickCommand@@',24)]:
        if struct.unpack('<Q',read(vt-8,8))[0]-pe.image_base!=col:raise ValueError('RTTI COL')
        fields=struct.unpack('<6I',read(col,24))
        if fields[1]!=offset or read(fields[3]+16,len(tag)+1)!=tag.encode()+b'\0':raise ValueError('RTTI identity')
    tables=[]
    for rva,target in [(0x19E7E98,0x19E7E18),(0x1A30DF0,0x1A30B4D)]:
        raw=read(rva,9*4);entries=struct.unpack('<9I',raw)
        if entries[3]!=target:raise ValueError('Rare lane index')
        tables.append({'rva':hex(rva),'bytes':raw.hex(' '),'rare_index':3,'rare_target':hex(target)})
    # The old proof binds the actual dispatcher and console to this same bool.
    old_by={x['name']:x for x in old['semantic_instructions']}
    if old_by['AI_toggle_global']['rip_targets']!=['0x5448579'] or old_by['rare_toggle_comparison']['rip_targets']!=['0x5448579']:
        raise ValueError('Reused actual AI toggle differs')
    path=a.game/'common/defines/ai/00_ai.txt';lines=path.read_text(encoding='utf-8-sig').splitlines()
    stock_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if stock_sha!='3af5d4100789bad56570e05c5852f35783605813957de7a5129d23142a116120':raise ValueError('Frozen stock differs')
    stock_dump=['common/defines/ai/00_ai.txt']
    for first,last in [(32,40),(90,98)]:stock_dump.extend(f'{n}: {lines[n-1]}' for n in range(first,last+1))
    result={'schema':'ck3_12002_religion_reform_schedule_v1','executable_sha256':SHA,
        'readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'reused_reform_abi_sha256':REUSED_SHA,'reused_proof_counts':{'functions':7,'slices':4,'anchors':28},
        'native_spans':spans,'semantic_instructions':instructions,'rare_lane_tables':tables,
        'AI_manager_secondary_vtable':{'rva':'0x45ac5f8','base_offset':8,'prepare_slot':'0x8','execute_slot':'0x30'},
        'daily_chain':{'source_sha256':hashlib.sha256(day_path.read_bytes()).hexdigest(),
                       'vtable_slots':day['vtable_slots'],'rtti':day['rtti'],'unknowns':day['unknowns']},
        'source_bindings':{k:hex(v) for k,v in BINDINGS.items()},
        'stock_source':{'path':'common/defines/ai/00_ai.txt','sha256':stock_sha,'ranges':[[32,40],[90,98]]},
        'remaining':['government bit6 exact property name','native general non-unreformed Rite creation','actual paused AI pointer integration and observation','queued reform outcome and independent post-action readback']}
    if a.record:MAP.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    elif json.loads(MAP.read_text(encoding='utf8'))!=result:raise ValueError('Reviewed ABI differs')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    native=a.output_dir/'native-disassembly.txt';native.write_text('\n'.join(dump)+'\n',encoding='utf8')
    stock=a.output_dir/'stock-evidence.txt';stock.write_text('\n'.join(stock_dump)+'\n',encoding='utf8')
    receipt={'status':'GREEN','readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'complete_functions':len(all_spans),'slices':len(all_slices),'semantic_instructions':len(SITES),
        'exact_executable_sha256':SHA,'abi_manifest_sha256':hashlib.sha256(MAP.read_bytes()).hexdigest(),
        'reused_reform_abi_sha256':REUSED_SHA,
        'artifacts':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [native,stock]}}
    (a.output_dir/'abi-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
