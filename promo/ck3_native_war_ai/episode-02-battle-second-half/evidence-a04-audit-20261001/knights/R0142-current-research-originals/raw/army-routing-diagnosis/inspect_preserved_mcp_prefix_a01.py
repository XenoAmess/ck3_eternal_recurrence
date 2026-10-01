from pathlib import Path
import json
p=Path(__file__).parent/'mcp-calls-bounded-prefix-through-routing-query-a01.jsonl'
for n,line in enumerate(p.read_bytes().splitlines(),1):
 v=json.loads(line)
 tool=v.get('tool','')
 if 'select_army' in tool or 'query_ingame_ui' in tool or 'open_combat' in tool:
  body=v.get('body')
  print(json.dumps({'line':n,'tool':tool,'arguments':v.get('arguments'),'at':v.get('at'),'keys':list(v),'body_type':type(body).__name__,'body_keys':list(body) if isinstance(body,dict) else None,'body_head':str(body)[:450]},ensure_ascii=False))
