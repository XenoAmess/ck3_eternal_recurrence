from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
HEAD='f960a1b4b46efa5359e403c9d308b2a808a2f7d0'
JOB=118689639628
assert datetime.now(timezone.utc)<datetime(2026,10,20,14,45,tzinfo=timezone.utc)
assert not (ROOT/'FAILED-STEP-EXCERPT.actual.log').exists(),'one read only'
argv=['gh','api','--allow-escape-sequences','--method','GET',f'repos/XenoAmess/ck3_eternal_recurrence/actions/jobs/{JOB}/logs']
r=subprocess.run(argv,cwd='D:/workspace/ck3_eternal_recurrence',capture_output=True,timeout=45)
assert r.returncode==0,r.stderr[:2000]
raw=r.stdout
text=raw.decode('utf8',errors='replace')
lines=text.splitlines(keepends=True)
starts=[i for i,x in enumerate(lines) if '##[group]Run python -B -X utf8 tools/test_r08_writer_one_day.py' in x]
assert len(starts)==1,(len(starts),len(raw),text[:300])
start=starts[0]
end=next((i for i in range(start+1,len(lines)) if '##[group]' in lines[i]),len(lines))
part=''.join(lines[start:end]).encode('utf8')
assert len(part)<=48*1024,len(part)
(ROOT/'FAILED-STEP-EXCERPT.actual.log').write_bytes(part)
def sha(b):return hashlib.sha256(b).hexdigest()
value=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
    exact_head=HEAD,run_id=39440759734,job_id=JOB,original_argv=argv,original_process_returncode=r.returncode,
    original_job_log_response_bytes=len(raw),original_job_log_response_sha256=sha(raw),
    retained_excerpt=dict(path=str(ROOT/'FAILED-STEP-EXCERPT.actual.log'),bytes=len(part),sha256=sha(part),
        source_line_start_1based=start+1,source_line_end_exclusive_1based=end+1),
    excerpt_role='Original contiguous failed-step log byte content decoded UTF8/reencoded; full response only hashed in memory',
    worktree_changes=False,CI_rerun=False,SDK_game_tool_download=False)
(ROOT/'LOG-READ.actual.json').write_bytes((json.dumps(value,indent=2)+'\n').encode('utf8'))
print(json.dumps(value));print(part.decode('utf8'))
