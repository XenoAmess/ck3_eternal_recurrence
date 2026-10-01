from pathlib import Path
import subprocess,json,sys
root=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001');p=root/'review_C08_after_monitor_a03.py'
assert str(Path(sys.executable).resolve()).lower()=='d:\\workspace\\ck3_eternal_recurrence\\tools\\.venv\\scripts\\python.exe'
argv=[sys.executable,'-X','utf8=0','-B',str(p)]
with (root/'scoped-ui-C08-review-a03-argv.json').open('x',encoding='utf-8')as f:json.dump(argv,f,indent=2)
with (root/'scoped-ui-C08-review-a03-stdout.bin').open('xb')as out,(root/'scoped-ui-C08-review-a03-stderr.bin').open('xb')as err:r=subprocess.run(argv,stdout=out,stderr=err)
with (root/'scoped-ui-C08-review-a03-process.json').open('x',encoding='utf-8')as f:json.dump({'exit_code':r.returncode,'native_requests':0,'screen_actions':0},f)
print(r.returncode)
