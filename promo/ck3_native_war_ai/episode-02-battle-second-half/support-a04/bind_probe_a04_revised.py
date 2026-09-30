from pathlib import Path
import json,hashlib
from xar_promo.media import parse_ffprobe_json,write_bound_media_probe
RUN=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
SOURCE=Path('C:/Users/1/ck3-a04-machine-audit-20260930/attempt-02/ffprobe-final.stdout.txt')
identity=json.loads((RUN/'final-artifact.json').read_text(encoding='utf-8'))
probe=parse_ffprobe_json(SOURCE.read_bytes())
target=RUN/'bound-media-probe.json';bound=write_bound_media_probe(target,media_path=Path(identity['path']),probe=probe)
if bound.subject_sha256!=identity['sha256'] or bound.subject_bytes!=identity['bytes']:raise ValueError('independent probe subject differs')
report={'kind':'retained-independent-ffprobe-binding','source_path':str(SOURCE),'source_bytes':SOURCE.stat().st_size,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper(),'bound_probe_path':str(target),'bound_probe_sha256':hashlib.sha256(target.read_bytes()).hexdigest().upper(),'no_second_probe':True,'human_signoff':'not-provided'}
with (RUN/'bound-probe-provenance.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
