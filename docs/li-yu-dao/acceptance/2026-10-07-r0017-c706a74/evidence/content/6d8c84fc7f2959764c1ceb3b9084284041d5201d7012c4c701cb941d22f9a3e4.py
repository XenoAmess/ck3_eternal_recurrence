import contextlib,io
with contextlib.redirect_stdout(io.StringIO()):
 import read_static_route_v2 as m
nest=[];line=1;parents={14198,14775,18013,20143,22858,24196,26568};rows=[]
for c in m.clean:
 if c=='\n':line+=1
 elif c=='{':
  if nest and nest[-1] in parents and not '{};' in m.lines[line-1]:
   context=[f'{j+1}: {m.active[j].strip()}' for j in range(max(0,line-7),line) if m.active[j].strip()]
   rows.append((line,nest[-1],context[-4:]))
  nest.append(line)
 elif c=='}' and nest:nest.pop()
for line,parent,context in rows:
 if parent in {14198,14775,18013}:print('CHILD',line,'PARENT',parent,' || '.join(context))
print('OTHER_COUNTS',[(parent,len([r for r in rows if r[1]==parent])) for parent in [20143,22858,24196,26568]])
