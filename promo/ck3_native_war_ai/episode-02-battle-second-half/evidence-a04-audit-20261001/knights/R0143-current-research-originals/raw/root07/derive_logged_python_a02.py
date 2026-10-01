from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
old=ROOT/'run_logged_python_a01.py'
new=ROOT/'run_logged_python_a02.py'
text=old.read_text(encoding='utf-8').replace("argv = [sys.executable, '-X', 'utf8=0', '-B', str(a.script.resolve()), *a.arguments]", "extra = a.arguments[1:] if a.arguments and a.arguments[0] == '--' else a.arguments\nargv = [sys.executable, '-X', 'utf8=0', '-B', str(a.script.resolve()), *extra]")
with new.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
with (ROOT/'logged-python-a02-derivation.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'original':str(old),'source_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'derived':str(new),'derived_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'fix':'Remove explicit -- separator before forwarding named script arguments. Prior argparse failures happened before any binding or game request.'},f,indent=2)
