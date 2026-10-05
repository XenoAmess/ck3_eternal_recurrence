import hashlib
import json
from pathlib import Path

root=Path(r'C:\workspace\ck3_eternal_recurrence')
out=Path(__file__).parent/'source-evidence-001'
out.mkdir(exist_ok=False)
requests=[(root/'tools/ck3_native_profile_mcp.py',[(1,40),(150,162),(526,586),(730,760)]),
          (root/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',[(2622,2653),(6345,6357),(6430,6460),(6480,6530),(9625,9683)]),
          (Path(r'C:\workspace\ck3_lyd_runtime_20261004\lyd-r9-official-mcp-consumer21-20261005-001\review-package-001\persistent_native_mcp_queue_21.py'),[(1,50),(174,180),(194,231)])]
manifest=[]
for i,(src,ranges) in enumerate(requests):
    data=src.read_bytes()
    dst=out/f'{i:02d}-{src.name}'
    dst.write_bytes(data)
    lines=data.decode('utf-8-sig').splitlines()
    fragments=[]
    for first,last in ranges:
        fragments += [f'{line+1}: {lines[line]}' for line in range(first-1,min(last,len(lines)))]
    excerpt='\n'.join(fragments)+'\n'
    (out/f'{i:02d}-{src.name}.excerpt.txt').write_text(excerpt,encoding='utf-8')
    manifest.append({'source':str(src),'copy':str(dst),'sha256':hashlib.sha256(data).hexdigest(),'ranges':ranges})
    print('SOURCE',src)
    print(excerpt)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
