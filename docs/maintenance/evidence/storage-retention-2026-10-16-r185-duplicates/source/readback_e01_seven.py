"""Independent bounded readback of the seven exact retired paths and keeper."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
out=Path(__file__).parent
spec=importlib.util.spec_from_file_location('p',out/'plan_e01_exact_duplicates.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
rp=out/'E01-SEVEN.result.actual-a01.json'
assert p.sha(rp)=='a5efe843b63d02438f594e2ec616e3865e515f068207d28fbd73aed6a8bd4e4c'
r=json.loads(rp.read_text(encoding='utf-8'))
rows=[json.loads(x) for x in (out/'E01-SEVEN.files.actual-a01.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(rows)==7 and all(x['status']=='deleted_unavailable' and not Path(x['path']).exists() for x in rows)
assert len({tuple(x['file_id']) for x in rows})==7
keep=r['retained_replica'];kp=p.base.checked(keep['path'],[p.ROOT]);h=p.lib.open_handle(kp,0x80000000|0x80,1)
try: assert p.lib.get_info(h,kp)==keep['info']
finally:p.k.CloseHandle(h)
report={'schema':'xar.r185-e01-seven-independent-readback.v1','machine_id':p.M,'at_utc':datetime.now(timezone.utc).isoformat(),'policy_version':'1.0.0','actual_result_sha256':p.sha(rp),'seven_paths_absent_now':True,'unique_deleted_file_ids':7,'keeper_current_file_id':keep['info']['id'],'keeper_current_identity_metadata_unchanged':True,'keeper_sha256_from_same_handle_execution':keep['sha256'],'keeper_content_rehashed_by_this_readback':False,'fresh_D_free_bytes':shutil.disk_usage('D:/').free,'actual_D_allocation_credit_bytes':r['actual_D_single_link_allocation_bytes'],'actual_C_credit_bytes':0,'volume_free_delta_not_assumed_exclusive':True,'new_deletions':0,'screen_SDK_TaskBus_main_repo_actions':0,'automatic_gc_implemented':False}
pin=p.write(out/'E01-SEVEN.independent-readback.actual-a01.json',report)
print(json.dumps({'readback':pin,'D_free_bytes':report['fresh_D_free_bytes'],'total_output_bytes':sum(f.stat().st_size for f in out.rglob('*') if f.is_file())}))
