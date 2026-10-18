"""Check the sealed portable source archive; no game, compiler, or local paths."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile
def main():
 root=Path(__file__).resolve().parent
 raw=(root/'portable-source-a01.zip').read_bytes()
 if len(raw)!=160776 or hashlib.sha256(raw).hexdigest()!='9039dc26cda8a6f280b28d84d7f97b9c569d097191af0bd398a4c6dfd7a712dd':
  raise ValueError('portable archive drift')
 source=(root/'SOURCE.final.json').read_bytes()
 if hashlib.sha256(source).hexdigest()!='83b7c34ad6838f48a9557d63c49af96bd43b32d05bb434bc1b197a9c344f8133':
  raise ValueError('source manifest drift')
 manifest=json.loads(source)
 with zipfile.ZipFile(root/'portable-source-a01.zip') as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts for n in names):
   raise ValueError('nonportable archive names')
  if z.read('SOURCE.final.json')!=source:raise ValueError('archive source manifest drift')
  for row in manifest['files']:
   b=z.read(row['path'])
   if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:
    raise ValueError('source member drift: '+row['path'])
 print(json.dumps({'status':'PASS','source_files':len(manifest['files']), 'candidate_targets':len(manifest['copy_plan']), 'runtime_or_build':False,'live_qualification':False}))
if __name__=='__main__':main()
