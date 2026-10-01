from pathlib import Path
import json
import knight_saved_pair as pair
out=pair.NEW/'loading-window-observation-a01'
out.mkdir(exist_ok=False)
image=pair.capture_window(out,'current-loading')
rows=(pair.OUTPUT/'mcp-calls.jsonl').read_text(encoding='utf-8').splitlines()
last=[json.loads(r) for r in rows[-3:]]
pair.write(out/'same-owner-last-three-calls.json',last)
print(json.dumps({'image':image,'last_calls':last},ensure_ascii=False))
