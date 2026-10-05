import hashlib
import json
from pathlib import Path

sdk=Path(r'C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages')
out=Path(__file__).parent/'sdk-source-evidence-001'
out.mkdir(exist_ok=False)
specs=[('mcp/client/stdio.py',[(141,157),(218,225)]),('mcp/client/session.py',[(539,546),(1050,1061)]),('mcp/server/stdio.py',[(199,205)]),('mcp/server/mcpserver/utilities/func_metadata.py',[(119,165),(420,470)]),('anyio/_backends/_asyncio.py',[(1140,1153)]),('anyio/streams/text.py',[(50,65)])]
manifest=[]
for i,(relative,ranges) in enumerate(specs):
    src=sdk/relative
    data=src.read_bytes()
    target=out/f'{i:02d}-{src.name}'
    target.write_bytes(data)
    lines=data.decode('utf-8-sig').splitlines()
    text='\n'.join(f'{n+1}: {lines[n]}' for first,last in ranges for n in range(first-1,min(last,len(lines))))+'\n'
    (out/f'{i:02d}-{src.name}.excerpt.txt').write_text(text,encoding='utf-8')
    manifest.append({'source':str(src),'copy':str(target),'sha256':hashlib.sha256(data).hexdigest(),'ranges':ranges})
    if 'func_metadata' in relative:
        print(text)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
