import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;p=HERE/'prepare_finalizer.py';raw=p.read_bytes();text=raw.decode('utf-8')
old='" \'actual_personal114_"';new='" \'actual_personal114_instance"'
if text.count(old)!=1:raise ValueError('Need exact personal check selector correction')
text=text.replace(old,new)
lines=text.splitlines(True);matches=[line for line in lines if line.startswith("for old,new in [('0121-'")]
if len(matches)!=1:raise ValueError('Need exact already rebound control mapping line')
text=''.join(line.replace(':replace(old,new)',":replace(old,new) if old in text else changes.append({'control_key_already_rebound_in_new_setup':old})") if line.startswith("for old,new in [('0121-'") else line for line in lines)
text=text.replace("'round11','round12'","'round11','round12'")
with (HERE/'FINALIZER-PREWRITE-FAILURE-002.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'stage':'external finalizer reuse preparation before output','failed_driver':str(HERE/'prepare_finalizer_v2.py'),'error':'Old typed-control keys already removed by replacement of setup block; skip only those already rebound keys','new_save_AST_reads_during_failed_driver':0,'finalizer_or_final_report_written_during_failed_driver':False,'old_packages_modified':False},f,ensure_ascii=False,indent=2);f.write('\n')
exec(compile(text,str(Path(__file__).resolve()),'exec'),{'__file__':str(Path(__file__).resolve()),'__name__':'__main__'})
