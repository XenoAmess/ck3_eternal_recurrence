from pathlib import Path
import re, json, hashlib
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
SRC=Path('C:/lr17s1/ck3_autonomous_player/native_bridge/src/bridge.cpp')
text=SRC.read_text(encoding='utf-8-sig')
def ref(p):
 raw=Path(p).read_bytes();return {'path':Path(p).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def mask(match):return ''.join('\n' if c=='\n' else ' ' for c in match.group())
clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',mask,text)
lines=text.splitlines();stack=[];line=1
for c in clean:
 if c=='\n':line+=1
 elif c=='{':stack.append(line)
 elif c=='}':
  if not stack:print('unmatched_close',line);continue
  start=stack.pop()
  if 27484<=line<=27490:
   print('CLOSE',line,'OPEN',start,'CONTEXT', '\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,start-8),min(len(lines),start+2))))
print('REMAIN',stack[-12:])
client=BASE/'live-attempt-017/mcp-client-001'
files=sorted(p for p in client.iterdir() if p.name.startswith(('0015-','0016-','0017-')) or p.name=='server.stderr.log')
print('FILES',json.dumps([ref(p) for p in files],ensure_ascii=False))
for p in files:
 if 'native-01' in p.name:
  v=json.loads(p.read_bytes());print('NATIVE',p.name, 'KEYS',list(v),'STATUS',v.get('status'),'REASON',v.get('reason'))
  s=v.get('snapshot',v.get('snapshot_after',{}));print('FRAME', {k:s.get(k) for k in ['revision','native_revision','date_raw','paused','active_event']})
  if p.name.startswith('0015-'):print('QUERY',json.dumps(v.get('result',v.get('query',{})),ensure_ascii=False)[:1600])
  if p.name.startswith('0017-'):print('HISTORY',json.dumps(s.get('history',[]),ensure_ascii=False)[-2200:])
