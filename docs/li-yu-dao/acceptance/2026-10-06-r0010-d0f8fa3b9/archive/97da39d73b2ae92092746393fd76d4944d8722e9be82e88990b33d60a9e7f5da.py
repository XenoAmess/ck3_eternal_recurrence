import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;previous=HERE/'prepare_finalizer.py';raw=previous.read_bytes();text=raw.decode('utf-8')
old="replace('actual fourth-open checks','actual fifth-open checks')";new="replace('Actual fourth-open checks','Actual fifth-open checks')"
if text.count(old)!=1:raise ValueError('Need exact single prewrite case anchor correction')
text=text.replace(old,new)
with (HERE/'FINALIZER-PREWRITE-FAILURE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'stage':'external finalizer reuse preparation','error':'Case-sensitive anchor actual vs Actual in error-message text','failed_driver':{'path':str(previous),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'new_save_AST_reads_during_failed_driver':0,'finalizer_or_final_report_written_during_failed_driver':False,'correction':'Capitalized error-message anchor; all evidence and actual AST cache unchanged','old_package_mutations':False},f,ensure_ascii=False,indent=2);f.write('\n')
exec(compile(text,str(Path(__file__).resolve()),'exec'),{'__file__':str(Path(__file__).resolve()),'__name__':'__main__'})
