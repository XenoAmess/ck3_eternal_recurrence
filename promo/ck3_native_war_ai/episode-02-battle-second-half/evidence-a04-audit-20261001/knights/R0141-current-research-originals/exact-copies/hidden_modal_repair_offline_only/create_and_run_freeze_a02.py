from pathlib import Path
import subprocess,sys,json,hashlib,datetime
out=Path(__file__).parent
def ident(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
old=out/'freeze_source_ready_a01.py'
source=old.read_text('utf-8').replace("source-freeze-ui-hidden-modal-a01'","source-freeze-ui-hidden-modal-a02'")
source=source.replace("python_text=python_stderr.read_bytes().decode('utf-8',errors='replace');assert", "python_text=python_stderr.read_bytes().decode('utf-8',errors='replace').replace('\\r\\n','\\n');assert")
assert source!=old.read_text('utf-8')
new=out/'freeze_source_ready_a02.py'
with new.open('x',encoding='utf-8',newline='\n') as f:f.write(source)
failed={'schema':'ck3.source-freeze-helper-firstattempt-red/v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'old_script':ident(old),'status':'freeze receipt writer RED; native/UI actual tests remain PASS','reason':'Writer checked LF-only OK token against actual Windows CRLF unittest stderr. No native/UI source or verification behavior changed. Partial first freeze exact copies preserved. New a02 normalizes CRLF for token checking only.','first_freeze_receipt_exists':(out/'source-freeze-ui-hidden-modal-a01/source-ready-and-test-receipt.json').exists()}
with (out/'freeze-firstattempt-writer-RED.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(failed,f,ensure_ascii=False,indent=2);f.write('\n')
argv=[sys.executable,'-X','utf8','-B',str(new)]
p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
for name,data in [('source-freeze-a02-stdout.bin',p.stdout),('source-freeze-a02-stderr.bin',p.stderr)]:
    with (out/name).open('xb') as f:f.write(data)
result={'argv':argv,'shell':False,'returncode':p.returncode,'stdout':ident(out/'source-freeze-a02-stdout.bin'),'stderr':ident(out/'source-freeze-a02-stderr.bin')}
with (out/'source-freeze-a02-result.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(p.stdout.decode('utf-8',errors='replace'));print(p.stderr.decode('utf-8',errors='replace'))
sys.exit(p.returncode)
