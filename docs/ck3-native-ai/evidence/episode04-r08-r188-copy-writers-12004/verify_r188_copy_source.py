"""Stdlib replay of held695B source against two saved R188 post-instruction traps."""
from pathlib import Path
from io import BytesIO
from collections import Counter
import argparse,base64,hashlib,json,re,struct,zipfile,zlib
MEMBER='docs/ck3-native-ai/evidence/episode04-r08-r188-copy-writers-12004/postpc-source.actual.json'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(b,row,label):need(len(b)==row['bytes']and sha(b)==row['sha256'],'Pin differs: '+label)
def load(path):
    p=Path(path)
    if p.suffix=='.patch':
        sections=re.split(br'(?m)^diff --git ',p.read_bytes())[1:]
        found=[s for s in sections if ('+++ b/'+MEMBER).encode()in s.splitlines()]
        need(len(found)==1 and b'new file mode 100644'in found[0],'Complete new-file bundle required')
        active=False;out=[]
        for line in found[0].splitlines(keepends=True):
            if line.startswith(b'@@ '):active=True;continue
            if active and line.startswith(b'+'):out.append(line[1:])
        raw=b''.join(out)
    else:raw=p.read_bytes()
    return json.loads(raw)
def decode(row):
    need(row['encoding']=='zlib+base85','Unexpected original encoding');raw=zlib.decompress(base64.b85decode(row['payload']));pin(raw,row,row['id']);return raw
def asm_rows(text,body):
    rows={};cursor=0x28A63E0
    for line in text.splitlines():
        m=re.fullmatch(r'([0-9A-Fa-f]+)\s+((?:[0-9A-Fa-f]{2}\s+)+)([a-z][a-z0-9]*)\s*(.*?)\s*',line)
        need(m is not None,'Saved ASM row shape differs');pc=int(m[1],16);chunk=bytes.fromhex(m[2]);need(pc==cursor and body[pc-0x28A63E0:pc-0x28A63E0+len(chunk)]==chunk,'Complete saved ASM byte coverage differs');rows[pc]=(chunk,m[3],m[4]);cursor+=len(chunk)
    need(cursor==0x28A6697 and len(rows)==147,'Held695B boundary differs');return rows
def verify(path):
    b=load(path);orig={r['id']:decode(r)for r in b['originals']};need(len(orig)==len(b['originals']),'Duplicate original ID')
    proj=json.loads(orig['WRITERS.actual.json']);admission=json.loads(orig['ADMISSION.actual.json']);day=json.loads(orig['NATURAL-DAY.actual.json']);final=json.loads(orig['ROOT-FINALIZE.actual.json']);started=json.loads(orig['OBSERVER-STARTED.actual.json']);ready=json.loads(orig['writer.ready.json'])
    raw_lines=[(i,json.loads(line))for i,line in enumerate(orig['writer.raw.ndjson'].splitlines(),1)if line.strip()];raw_by_line=dict(raw_lines);start=raw_lines[0][1];terminal=raw_lines[-1][1]
    need(sha(orig['WRITERS.actual.json'])=='05575043e9ca43c0469bbbfe9d3ec74e902daf62d6778e4ce010fd1db754262d' and sha(orig['writer.raw.ndjson'])=='d20028e2596ea585939c033cde5ace26f804e51c7bcb8b0ccec11d06478f9a0b','Root-specified actual inputs differ')
    need(proj['evidence_machine_id']==start['machine_id']==admission['machine_id']==day['machine_id']==b['machine_id'],'Machine differs')
    ident=proj['Root_binding'];need(start['pid']==ident['pid']==12060 and start['created']==ident['created']==134366470385086412 and start['full_id']==ident['full_id']==31254,'Process/actor identity differs')
    need(start['admission_generation']==ident['admission_generation']==1 and start['admission_episode']==ident['admission_episode']=='native-31254-0a8ceff1be59','Episode/generation differs')
    meta=dict(line.split('=',1)for line in orig['CURRENT-RAW-ADMISSION.meta.txt'].decode().splitlines()if line)
    image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518';need(meta['qualified_exe_sha256']==b['image']['sha256']==image,'Admitted exact image differs')
    need(meta['game_version']=='1.20.0.4'and meta['steam_build_id']=='25734779','Build differs')
    with zipfile.ZipFile(BytesIO(orig['known-caller-originals.zip']))as z:
        need(z.testzip()is None,'Held archive CRC');source={n:z.read(n)for n in z.namelist()}
    need(set(source)==set(b['held_members']),'Held member set differs')
    for name,row in b['held_members'].items():pin(source[name],row,name)
    receipt=json.loads(source['original-source-receipt.json']);f=receipt['function'];body=source['caller.bin']
    need(len(body)==695 and sha(body)==f['sha256']=='ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede'and bytes.fromhex(f['hex'])==body,'Held source raw differs')
    need(f['begin_rva']==0x28A63E0 and f['end_exclusive']==0x28A6697 and f['flags']==2 and f['chained_runtime_function']is None,'Original .pdata extent differs')
    need(receipt['machine_id']==b['machine_id']and receipt['qualified_EXE_SHA_reused_not_rehashed']==image,'Held source identity differs')
    pdata=[]
    for row in receipt['read_ledger']:
        if row['kind']=='metadata'and row['bytes']==12:
            chunk=bytes.fromhex(row['hex']);need(sha(chunk)==row['sha256'],'Original metadata row differs');v=struct.unpack('<III',chunk)
            if v[0]<=0x28A6454<v[1]:pdata.append(v)
    need(pdata==[(f['begin_rva'],f['end_exclusive'],f['unwind_rva'])],'Containing retained .pdata row differs')
    rows=asm_rows(source['caller.asm'].decode(),body)
    need([pc for pc,(_,mn,_)in rows.items()if mn=='ret']==[0x28A6696],'Ordinary RET differs')
    prologue=bytes.fromhex('48895c2410488974241848897c2420554154415541564157488d6c24b04881ec50010000');need(body.startswith(prologue),'Return-slot frame source differs')
    need(len(proj['qualified_writers'])==2 and proj['unknown_traps']==[] and proj['slot_trap_count']==proj['qualified_slot_count']==2,'Strict projection scope differs')
    specs=[(0,0x2C0,0x28A6450,'498b4118',0x18,0x28A6454,'498981c0020000',0x28A645B,469493),(1,0x2C8,0x28A645B,'498b4120',0x20,0x28A645F,'498981c8020000',0x28A6466,0)]
    for p,(slot,offset,load_pc,load_hex,source_offset,store_pc,store_hex,post,value),join in zip(proj['qualified_writers'],specs,b['source_joins'],strict=True):
        r=raw_by_line[p['raw_line']];need(r['kind']=='raw_field_write_trap'and r['slot']==p['slot']==slot and r['offset']==p['offset']==offset,'Actual source row differs')
        for key in ('thread_id','event_ordinal','slot_hit_ordinal','qpc','address','character','context','full_id','RIP_after','RIP_after_rva','registers','DR6','before_raw','before_basis','after_raw','same_value_write'):need(r[key]==p[key],'Raw/projection differs: '+key)
        need(p['physical_write_qualified']is True and p['source_status']=='unknown'and p['writer_instruction_start']is None and p['known_copy_caller_v1']is None,'Original projection was rewritten')
        need(rows[load_pc][0].hex()==load_hex and rows[store_pc][0].hex()==store_hex and store_pc+len(rows[store_pc][0])==post and post in rows,'Actual post-PC not a saved store end')
        regs=p['registers'];need(p['RIP_after_rva']==post and p['RIP_after']==start['module_base']+post,'RIP ASLR binding differs')
        need(regs['r9']==p['context']==ident['context']and p['address']==regs['r9']+offset,'Effective write address differs')
        need(regs['rsi']==p['character']==ident['character'] and regs['rax']==p['after_raw']==value and p['same_value_write']is True,'Actual value/source receiver differs')
        candidate=regs['rbp']+0x78;need(candidate==regs['rsp']+0x178==join['candidate_return_slot_address'],'Source-derived return-slot frame differs')
        need(join['store_rva']==store_pc and join['post_rva']==post and join['source_field_offset']==source_offset,'Saved source join differs')
        need(join['candidate_return_value']is None and join['incoming_caller_rva']is None and join['actual_write_date_raw']is None,'Missing runtime memory/date invented')
    counts=Counter(r['kind']for _,r in raw_lines);need(counts['raw_field_write_trap']==2 and counts['arm']==108 and counts['restore']==107 and counts['thread_exited']==1,'Actual retained counts differ')
    need(ready=={'ready':True,'armed_thread_count':108},'Actual ready differs')
    need(terminal['reason']=='timeout'and terminal['restored']and terminal['detached']and terminal['cleanup_complete']and not terminal['pending_event']and not terminal['full_window_all_writes_covered'],'Timeout/cleanup boundary changed')
    need(proj['cleanup_proved']and not proj['full_window_all_writes_covered']and proj['missing_or_unproved_live_restores']==[],'Strict cleanup scope changed')
    need(final['result']['wait']['exit_code']==1 and final['result']['wait']['exact_exit_code_observed']and not final['observer_killed'],'Actual exit result changed')
    g=day['exact_original_g12'];need(g['generation']==12 and g['starting_date_raw']==53149056 and g['target_date_raw']==g['last_observed_date_raw']==53149080 and g['completed_daily_ticks']==1 and g['overshoot_days']==0 and g['pause_observed'],'Separate exact day changed')
    need(all(p['actual_writer_game_date']is None for p in proj['qualified_writers']),'Trap date invented')
    observer=orig['cold_observer.d05.cpp'];need(hashlib.sha1(b'blob '+str(len(observer)).encode()+b'\0'+observer).hexdigest()==b['observer_source_git_blob'],'Held observer Git blob differs')
    need(b'x.capture_copy_caller=argc==15'in observer and b'--capture-known-copy-caller'in observer,'Optional source interface differs')
    need(len(started['argv'])==14 and '--capture-known-copy-caller'not in started['argv'],'Actual selected argv differs')
    need(b['caller_boundary']['actual_binary_feature_support_verified']is False and b['business']['military_c_d_producer']is None and b['business']['paid_military_amount_raw']is None and b['business']['cadence']is None,'Unknown scope elevated')
    return dict(status='PASS',scope='existing actual post-PC to held exact source join; not full-window or military attribution',machine_id=b['machine_id'],originals_verified=len(orig),held_body_bytes=695,held_instruction_rows=147,source_matches=2,raw_data_events=2,source_acquisition_EXE_bytes=0,ready_threads=108,restored_readbacks=107,timeout_exit_code=1,cleanup_complete=True,full_window_all_writes_covered=False,incoming_caller_rva=None,actual_trap_game_date=None,paid_military_amount_raw=None,cadence=None,live_execution_performed=False,semantic_correctness_verified=False)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('postpc-source.actual.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle)
    if a.extract_originals:
        need(not a.extract_originals.exists(),'Exclusive extraction root required');a.extract_originals.mkdir(parents=True,exist_ok=False)
        for row in load(a.bundle)['originals']:
            need(re.fullmatch(r'[A-Za-z0-9_.-]+',row['id'])is not None,'Unsafe original name')
            with(a.extract_originals/row['id']).open('xb')as f:f.write(decode(row))
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
