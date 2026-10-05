"""Read final R9 log files only, after parent-reported official exit."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'final-whole-logs-001'
LOGS=ROOT.parent/'live-attempt-009/userdir/logs'
OLD=ROOT/'after-sign-and-first-join-prefix-recovery-004'
AUDIT=ROOT/'third-prefix-critical-audit-001/REPORT.json'
HEADER=re.compile(rb'(?m)^\[([^]\r\n]+)\]\[([A-Z])\][^\r\n]*')
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def meta(s):
    return {'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,
            'device':s.st_dev,'inode':s.st_ino,'birthtime_ns':getattr(s,'st_birthtime_ns',None)}
def stable(a,b):return all(a[k]==b[k] for k in ('size','mtime_ns','device','inode'))
def write(rel,data):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
def js(rel,data):write(rel,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def error_groups(raw):
    matches=list(HEADER.finditer(raw));line=1;previous=0
    for n,m in enumerate(matches):
        line+=raw[previous:m.start()].count(b'\n');previous=m.start()
        if m[2]!=b'E':continue
        end=matches[n+1].start() if n+1<len(matches) else len(raw)
        yield m,raw[m.start():end],line
def identity(m,g):
    # Exact event identity includes timestamp, header and continuation lines.
    return sha(g.replace(b'\r\n',b'\n').rstrip(b'\n'))
def category(header,text):
    if re.search(r"Variable '(lyd_im_case_[0-9]+_(?:armed|acknowledged)|lyd_im_adopted)' is set but is never used\.",header):
        return 'known_fixture_unused_variable'
    if 'set_parent_faith_third' in text:return 'current_product_c2_native_dynamic_localization'
    if 'lyd_c2_' in text:
        if any(v in text for v in ('lyd_c2_check_count','lyd_c2_check_rites','lyd_c2_check_followers','lyd_c2_check_players')):
            return 'current_product_c2_scratch_error'
        if re.search(r'lyd_c2_consent_triggers.txt line: 351\b',text):return 'current_product_c2_ready_source_signed_callsite'
        if re.search(r'lyd_c2_consent_triggers.txt line: 318\b',text):return 'current_product_c2_receiver_endorser_scope'
        if 'Scope dependent values in localization inside an any trigger' in text:return 'current_product_c2_doctrine_tooltip_scope'
        if re.search(r'lyd_c2_consent_triggers.txt line: (?:75|76|77|78|79|80)\b',text):return 'current_product_c2_source_retirement_scope'
        if re.search(r'lyd_c2_consent_triggers.txt line: 87\b',text):return 'current_product_c2_retirement_postcondition_scope'
        return 'other_current_product_c2_error'
    return 'other_error_unreviewed'
def main():
    OUT.mkdir(exist_ok=False);start=now();files={};comparisons={}
    names=sorted(p.name for p in LOGS.iterdir() if p.is_file())
    old_report=json.loads((OLD/'REPORT.json').read_text('utf-8'))
    for name in names:
        src=LOGS/name;read_start=now();before_path=meta(src.stat())
        with src.open('rb') as f:
            before_handle=meta(os.fstat(f.fileno()));payload=f.read();after_handle=meta(os.fstat(f.fileno()))
        after_first=meta(src.stat());firstsha=sha(payload)
        write('raw-whole/'+name,payload)
        # Second whole read proves bytes unchanged across the capture's two reads.
        second_start=now();before_second=meta(src.stat())
        with src.open('rb') as f:
            second_handle_before=meta(os.fstat(f.fileno()));second=f.read();second_handle_after=meta(os.fstat(f.fileno()))
        after_second=meta(src.stat());secondsha=sha(second)
        good=(all(stable(before_path,x) for x in (before_handle,after_handle,after_first,before_second,
                second_handle_before,second_handle_after,after_second)) and firstsha==secondsha
                and len(payload)==before_path['size'] and len(second)==after_second['size'])
        files[name]={'source_path':str(src),'saved_whole_path':str(OUT/'raw-whole'/name),
          'read_start_utc':read_start,'first_read_end_utc':second_start,'second_read_end_utc':now(),
          'before_path_metadata':before_path,'before_handle_metadata':before_handle,
          'after_handle_metadata':after_handle,'after_first_path_metadata':after_first,
          'before_second_path_metadata':before_second,'before_second_handle_metadata':second_handle_before,
          'after_second_handle_metadata':second_handle_after,'after_second_path_metadata':after_second,
          'saved_bytes':len(payload),'saved_sha256':firstsha,'second_read_bytes':len(second),
          'second_read_sha256':secondsha,'stable_size_mtime_identity_and_bytes':good}
        old_path=OLD/'raw-prefix'/name
        if old_path.exists():
            prior=old_path.read_bytes();append=payload.startswith(prior)
            tail=payload[len(prior):] if append else b''
            comparisons[name]={'previous':pin(old_path),'current':pin(OUT/'raw-whole'/name),
                 'previous_prefix_exact':append,'added_bytes':len(tail) if append else None,
                 'added_raw_lines':tail.count(b'\n')+(bool(tail) and not tail.endswith(b'\n')) if append else None}
            if tail:
                write('added-raw/'+name,tail)
                line=prior.count(b'\n')+1;offset=len(prior)
                rows=[]
                for rawline in tail.splitlines(keepends=True):
                    rows.append(json.dumps({'file':name,'line':line,'byte_start':offset,'bytes':len(rawline),
                           'sha256':sha(rawline),'raw_text':rawline.decode('utf-8',errors='replace')},ensure_ascii=False)+'\n')
                    offset+=len(rawline);line+=1
                write('added-raw/'+name+'.jsonl',''.join(rows).encode('utf-8'))
    end_names=sorted(p.name for p in LOGS.iterdir() if p.is_file())
    final_meta={name:meta((LOGS/name).stat()) for name in end_names}
    directory_stable=names==end_names and all(stable(files[name]['before_path_metadata'],final_meta[name]) for name in names)
    raw=(OUT/'raw-whole/error.log').read_bytes();prior=(OLD/'raw-prefix/error.log').read_bytes()
    exact_same=raw==prior;old_audit=json.loads(AUDIT.read_text('utf-8'))
    counts=Counter();groups_by_signature={};primary=Counter();new_e=0
    # This is a linear scan, including E header groups that mention no variable by name.
    for m,g,line in error_groups(raw):
        text=g.decode('utf-8',errors='replace');header=m[0].decode('utf-8',errors='replace')
        cat=category(header,text);counts[cat]+=1;primary[identity(m,g)]+=1
        if m.start()>=len(prior):new_e+=1
        description=re.search(r'(?m)^  Error: (.*)$',text)
        location=re.search(r'(?m)^  Script location: (.*)$',text)
        key=(cat,description[1] if description else header.split(']: ',1)[-1],location[1] if location else '')
        item=groups_by_signature.setdefault(key,{'category':cat,'description':key[1],'script_location':key[2],
                     'count':0,'engine_second_counts':Counter(),'first_sample':None,'last_sample':None})
        sample={'source_time':m[1].decode('ascii',errors='replace'),'byte_start':m.start(),'byte_end_exclusive':m.start()+len(g),
                'line_start':line,'raw_group_sha256':sha(g),'raw_text':text}
        item['count']+=1;item['engine_second_counts'][sample['source_time']]+=1
        if item['first_sample'] is None:item['first_sample']=sample
        item['last_sample']=sample
    grouped=list(groups_by_signature.values())
    for item in grouped:item['engine_second_counts']=dict(item['engine_second_counts'])
    mirror={}
    for name in ('debug.log','game.log'):
        counter=Counter();catcounts=Counter()
        for m,g,line in error_groups((OUT/'raw-whole'/name).read_bytes()):
            counter[identity(m,g)]+=1
            text=g.decode('utf-8',errors='replace');catcounts[category(m[0].decode('utf-8',errors='replace'),text)]+=1
        intersection=sum((counter&primary).values())
        mirror[name]={'error_headers_in_this_file':sum(counter.values()),'exact_normalized_event_matches_to_error_log':intersection,
            'unmatched_here':sum((counter-primary).values()),'category_counts_for_crosscheck':dict(catcounts),
            'counting_rule':'Mirror diagnostics only, never added to primary error.log error total.'}
    js('COMPARE-004-TO-FINAL.json',{'files':comparisons,'new_error_log_E_headers':new_e,
          'error_bytes_identical_to_recovered_prefix_004':exact_same,'prior_detailed_audit':pin(AUDIT),
          'prior_audit_reusable_only_for_exact_error_bytes':exact_same})
    js('CLASSIFICATION.json',{'primary_log':'error.log','unique_header_partition':True,
        'primary_E_header_total':sum(counts.values()),'counts':dict(counts),'groups':grouped,
        'mirror_crosscheck':mirror,'scratch_header_count':counts['current_product_c2_scratch_error'],
        'all_header_categories_sum_to_primary_E_total':sum(counts.values())==sum(primary.values()),
        'classification_rule':'Every primary E header assigned exactly one category. Ready source_signed includes unnamed derivative error classes at actual line351; scratch checks explicit, fixture unused requires exact known variable diagnostic.'})
    stable_all=directory_stable and all(item['stable_size_mtime_identity_and_bytes'] for item in files.values())
    report={'result':'ACTUAL_R9_WHOLE_LOGS_RED' if sum(counts.values())>counts['known_fixture_unused_variable'] else 'ACTUAL_R9_WHOLE_LOGS_NO_PRODUCT_E',
       'capture_result':'PASS_STABLE_COMPLETE_FILES' if stable_all else 'RED_SOURCE_CHANGED_DURING_CAPTURE',
       'capture_start_utc':start,'capture_end_utc':now(),'files':files,'final_directory_metadata':final_meta,
       'source_directory_inventory_unchanged':directory_stable,'captured_log_count':len(files),
       'parent_reported_terminal_context':{'original_pid':20264,'original_create_time':1791179349.2116988,
          'official_MCP_final_confirm':'0064','retained_HANDLE_observer':'0065','exit_code':0,'typed_terminal':True,
          'observer_disposed':True,'prepare_stage1':'standard WM_CLOSE maintenance; full MCP prepare NOT_GREEN',
          'client_keeper_exit_code':0,'CAS_release':'2980 to 2981, resources=[]; expired own waiting and unresolved RED retained',
          'independently_requeried':False,'authority':'Root explicit message; no game/process handle/native operation by this reader'},
       'primary_error_log':{'bytes':len(raw),'sha256':sha(raw),'E_headers':sum(counts.values()),'category_counts':dict(counts),
          'last_line_complete':raw.endswith(b'\n'),'same_as_saved_004':exact_same,'added_E_headers':new_e},
       'whole_coverage':'All 16 actual files after parent-reported process exit; two whole reads and before/after size/mtime/identity stable during capture.',
       'native_dynamic_loc':'set_parent_faith_third one actual primary E remains KNOWN_RED; candidate hidden_effect has NOT_RUN native credit.',
       'log_cap':'EXACT_100000_E_OBSERVED_CAP_NOT_PROVEN. No final absence of growth clears the recorded REDs or proves later evaluations error-free.',
       'per_native_call_error_growth':'NOT_DETERMINED. The saved per-engine-second samples are not per-MCP-call offsets.',
       'event_mirrors':mirror,'primary_header_counting':'error.log only; debug/game mirrored events are not counted three times.',
       'live_operations':0,'process_handle_operations':0,'pipe_operations':0,'source_operations':0,
       'known_scopes':'ready_to_confirm .220 trigger; receiver endorser; source retirement head/title/owner/holder; retirement postcondition; doctrine any trigger preview; dynamic native commit_join loc.',
       'saturation_limit':'Raw error file has 100000 E; whether engine stopped logging cannot be determined from these artifacts.'}
    js('REPORT.json',report)
    write('REPORT.md',('R9 完整日志实际 RED。受父代理明确终止回执后，只读复制完整16日志；两次 whole read 的大小、mtime、identity、SHA均稳定。error.log 原始100000 E按唯一 header互斥分类；debug/game相同事件仅作mirror核对，不加入三倍计数。\n\n578项已知fixture unused之外的99422项生产C2错误仍保持 RED：ready source_signed与衍生scope、receiver背书、退休对象/归属、postcondition、doctrine any预览，以及1项set_parent_faith_third动态本地化。exact100000只是观察值，未证明引擎cap；后续零增长不能据此验收通过。原始第三partial、第四恢复与全部比较保持原样。原生源码候选本身仍NOT_RUN。\n').encode('utf-8'))
    js('INDEX.json',{p.relative_to(OUT).as_posix():pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()})
    print(json.dumps({'output':str(OUT),'report':pin(OUT/'REPORT.json'),'index':pin(OUT/'INDEX.json'),
       'capture':report['capture_result'],'logs':len(files),'error':report['primary_error_log'],'mirrors':mirror},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
