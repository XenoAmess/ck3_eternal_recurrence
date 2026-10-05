import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'r10-actual-sixth-open-join-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
p=HERE/'inspect_new.py'
with p.open('xb') as f:f.write((SOURCE/p.name).read_bytes())
with (HERE/'TOOL-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.seventh-external-tool-parameter-reuse.v1','records':[{'source':pin(SOURCE/name),'new':pin(HERE/name)} for name in ['prepare_request.py','collect_controls.py','inspect_new.py']],'parameter_mapping_driver':pin(HERE/'prepare_tools.py'),'preparation_failure':'Empty replacement mapping matched empty regex while copying inspector; prepare_request and collector had already been created. Copied inspector bytes directly without rerunning writer.','new_save_AST_parse_attempts_before_this_resume':0,'old_save_reparsed':False,'old_package_writes':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'inspector':pin(p),'preparation_failure_actual_AST_reads':0},ensure_ascii=False))
