from pathlib import Path
import re,json
ROOT=Path('C:/lr17s1/ck3_autonomous_player/native_bridge')
src=ROOT/'src/bridge.cpp';text=src.read_text(encoding='utf-8-sig');lines=text.splitlines()
for i,s in enumerate(lines,1):
 if 'native_step_dispatched' in s:print('DISPATCH',i,s)
cache=Path('C:/lr17b1/CMakeCache.txt').read_text(encoding='utf-8-sig')
flags={k:v for line in cache.splitlines() if (m:=re.fullmatch(r'(XAR_CK3_[A-Z0-9_]+):BOOL=(ON|OFF)',line)) for k,v in [m.groups()]}
macros={k for k,v in flags.items() if v=='ON'}|{'_WIN32','_WIN64','_MSC_VER','NDEBUG'}
active=[];stack=[];unsupported=[]
def evaluate(expr):
 expr=re.sub(r'defined\s*\(\s*(\w+)\s*\)',lambda m:'1' if m[1] in macros else '0',expr)
 expr=re.sub(r'defined\s+(\w+)',lambda m:'1' if m[1] in macros else '0',expr)
 expr=expr.replace('&&',' and ').replace('||',' or ');expr=re.sub(r'!(?!=)',' not ',expr)
 if re.search(r'[^\s\d()andort!=<>+*\-/]',expr):unsupported.append(expr);return False
 try:return bool(eval(expr,{'__builtins__':{}},{}))
 except Exception:unsupported.append(expr);return False
for line in lines:
 stripped=line.strip()
 m=re.match(r'#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)',stripped)
 if m:
  kind,expr=m.groups();outer=all(s['active'] for s in stack[:-1]) if stack else True
  if kind in ['if','ifdef','ifndef']:
   parent=all(s['active'] for s in stack);answer=evaluate(expr) if kind=='if' else (expr.strip() in macros)==(kind=='ifdef')
   stack.append({'active':parent and answer,'seen':answer,'parent':parent})
  elif kind=='elif':
   s=stack[-1];answer=evaluate(expr);s['active']=s['parent'] and not s['seen'] and answer;s['seen']|=answer
  elif kind=='else':
   s=stack[-1];s['active']=s['parent'] and not s['seen'];s['seen']=True
  else:stack.pop()
  active.append('')
 else:active.append(line if all(s['active'] for s in stack) else '')
clean='\n'.join(active)
def mask(m):return ''.join('\n' if c=='\n' else ' ' for c in m.group())
clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\\n])\'',mask,clean)
nest=[];line=1;unmatched=[]
for c in clean:
 if c=='\n':line+=1
 elif c=='{':nest.append(line)
 elif c=='}':
  if not nest:unmatched.append(line);continue
  start=nest.pop()
  if 27484<=line<=27490:
   print('CLOSE',line,'OPEN',start,'CONTEXT','\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,start-6),min(len(lines),start+2))))
print('PREPROCESS',json.dumps({'flags_on':sorted(macros-{'_WIN32','_WIN64','_MSC_VER','NDEBUG'}),'unsupported':unsupported,'unmatched':unmatched,'remaining':nest}))
for p in (ROOT/'src').glob('*.cpp'):
 if p.name=='bridge.cpp':continue
 found=[]
 for i,s in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
  if 'SubmitCommandCopyCompat' in s:found.append([i,s])
 if found:print('COMPAT',p.as_posix(),json.dumps(found))
