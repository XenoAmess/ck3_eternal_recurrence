from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
COMMIT='18b1944d1784d3e4ec57189c016335ef135b9b34'
TREE='77f74591f299874efcd20c2672f143c362e54caa'
REQUIRED={'.github/workflows/li-yu-dao-static.yml','.github/workflows/static-ci.yml'}

def record(p):
 data=p.read_bytes()
 return {'path':p.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def write_new(name,obj):
 with (ROOT/name).open('x',encoding='utf-8',newline='\n') as out:
  json.dump(obj,out,ensure_ascii=False,indent=2)
  out.write('\n')

def main():
 reports=sorted((ROOT/'observations').glob('*/report.json'))
 if not reports: raise RuntimeError('no observation')
 terminal=json.loads(reports[-1].read_text(encoding='utf-8'))
 if not terminal['all_terminal']: raise RuntimeError('CI is still pending; no terminal closure allowed')
 if terminal['commit']!=COMMIT or terminal['lyd_tree']!=TREE: raise RuntimeError('exact source identity mismatch')
 if set(r['path'] for r in terminal['runs'])!=REQUIRED: raise RuntimeError('required workflows mismatch')
 for reportpath in reports:
  index=json.loads((reportpath.parent/'index.json').read_text(encoding='utf-8'))
  for entry in index['files']:
   actual=record(reportpath.parent/entry['path'])
   if actual['bytes']!=entry['bytes'] or actual['sha256']!=entry['sha256']: raise RuntimeError('observation bytes changed')
 for run in terminal['runs']:
  if run['head_sha']!=COMMIT or run['status']!='completed': raise RuntimeError('run not exact terminal')
  rawjobs=json.loads((reports[-1].parent/f"jobs-{run['id']}.raw.json").read_bytes())['jobs']
  if not rawjobs: raise RuntimeError('no actual jobs')
  for job in rawjobs:
   if job['head_sha']!=COMMIT or job['status']!='completed': raise RuntimeError('job not exact terminal')
 status='OFFICIAL_L0_SUCCESS' if terminal['all_success'] else 'OFFICIAL_L0_TERMINAL_NON_SUCCESS'
 receipt={'schema':'ck3.lyd.exact18b1944d-ci-closed.v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'commit':COMMIT,'lyd_tree':TREE,'status':status,'terminal_observation':record(reports[-1]),'runs':terminal['runs'],'history':[{'report':record(p),'status':json.loads(p.read_text(encoding='utf-8'))['status']} for p in reports],'all_observation_hashes_verified':True,'all_success':terminal['all_success'],'live_acceptance':'NOT_COVERED','github_triggered':False,'workflow_retried':False,'tracked_written':False,'game_called':False,'screen_used':False,'finalization_network_calls':0}
 write_new('FINAL-CI-RECEIPT.json',receipt)
 with (ROOT/'README.md').open('x',encoding='utf-8',newline='\n') as out:
  out.write('# 18b1944d 官方静态 CI 终态回执\n\n')
  out.write(f'精确提交 `{COMMIT}`，礼与道产品树 `{TREE}`。最终状态 `{status}`。\n\n')
  for run in terminal['runs']:
   out.write(f"- [{run['workflow_name']}]({run['url']})：`{run['status']} / {run['conclusion']}`，actual head `{run['head_sha']}`。\n")
   for job in run['jobs']:
    out.write(f"  - [{job['name']} job {job['id']}]({job['html_url']})：`{job['status']} / {job['conclusion']}`，完成于 `{job['completed_at']}`。\n")
  out.write('\n首次 pending 和随后每次观察均在 observations 独立目录保留，不覆盖旧结论。每次包括 GitHub 官方 API run/jobs 的精确原始 JSON、GET/HTTP状态/响应头/时间/bytes/SHA-256 收据、辅助脚本和 exact-commit workflow/tree git 对象回执。最终关闭前重新校验所有观察索引及终态原始 jobs。\n\n')
  out.write('[最终机器回执](FINAL-CI-RECEIPT.json)记录精确观察路径、哈希及所有jobs。只读查询没有手工触发、重试CI、checkout、写tracked、调用游戏或占用屏幕；CI终态只证明官方L0静态检查，不证明R5实机通过。\n')
 write_new('index.json',{'schema':'ck3.lyd.exact18b1944d-ci-final-index.v1','files':[record(p) for p in sorted(ROOT.rglob('*')) if p.is_file()],'self_boundary':'index excludes itself'})
 print(json.dumps({'status':status,'runs':terminal['runs'],'receipt':record(ROOT/'FINAL-CI-RECEIPT.json'),'index':record(ROOT/'index.json')},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
