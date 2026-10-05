import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;p=HERE/'prepare_finalizer.py';raw=p.read_bytes();text=raw.decode('utf-8')
old='" \'actual_personal114_"';new='" \'actual_personal114_instance"'
if text.count(old)!=1:raise ValueError('Need exact check-line selector correction')
text=text.replace(old,new)
with (HERE/'FINALIZER-PREWRITE-FAILURE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'failed_driver':{'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'stage':'external finalizer reuse preparation before output','error':'Personal check prefix also matched the facts row; tightened to exact instance check prefix','new_save_AST_reads_during_failed_driver':0,'finalizer_or_final_report_written_during_failed_driver':False,'following_missing_finalizer_command_also_no_AST_or_output':True,'old_packages_modified':False},f,ensure_ascii=False,indent=2);f.write('\n')
exec(compile(text,str(Path(__file__).resolve()),'exec'),{'__file__':str(Path(__file__).resolve()),'__name__':'__main__'})
