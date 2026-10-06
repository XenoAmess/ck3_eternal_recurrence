"""Verify only the relative small-file package; excludes external media."""
from pathlib import Path
import hashlib,json
def main():
 root=Path(__file__).resolve().parent
 data=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
 for item in data['files']:
  relative=Path(item['relative']);assert not relative.is_absolute() and '..' not in relative.parts
  p=root/relative;assert p.is_file() and p.suffix.lower() not in {'.mp4','.mkv','.mov','.png','.wav','.mp3','.pcm'}
  b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],str(p)
 print(json.dumps({'state':'SMALL_RELATIVE_PACKAGE_PASS','files':len(data['files']),'external_media_reads':0,'processes_started':0,'human_signoff':False}))
 return 0
if __name__=='__main__':raise SystemExit(main())
