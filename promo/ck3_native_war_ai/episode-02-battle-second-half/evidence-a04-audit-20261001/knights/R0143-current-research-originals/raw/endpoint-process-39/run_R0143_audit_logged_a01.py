from pathlib import Path
import hashlib,json,subprocess,sys,datetime
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
def pin(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def write(p,v):
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 sys.stdout.reconfigure(encoding='utf-8');script=B/sys.argv[1];name=sys.argv[2]
 argv=[sys.executable,'-X','utf8=0','-B',str(script)]
 intent=B/(name+'-intent.json');write(intent,{'argv':argv,'reader':pin(script),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'no_game_source_git_screen':True})
 stdout=B/(name+'.stdout.bin');stderr=B/(name+'.stderr.bin')
 with stdout.open('xb')as o,stderr.open('xb')as e:r=subprocess.run(argv,stdout=o,stderr=e,check=False)
 result={'argv':argv,'exit_code':r.returncode,'stdout':pin(stdout),'stderr':pin(stderr),'intent':pin(intent)}
 write(B/(name+'-process.json'),result);print(json.dumps(result,ensure_ascii=False));return r.returncode
if __name__=='__main__':raise SystemExit(main())
