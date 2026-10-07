import read_static_route_v2 as model
nest=[];line=1;parents={14775,18013,20143,22858,24196,26568};rows=[]
for c in model.clean:
 if c=='\n':line+=1
 elif c=='{':
  if nest and nest[-1] in parents:
   rows.append((line,nest[-1],'\n'.join(f'{j+1}: {model.lines[j]}' for j in range(max(0,line-7),line))))
  nest.append(line)
 elif c=='}' and nest:nest.pop()
for line,parent,context in rows:print('CHILD',line,'PARENT',parent,'CONTEXT',context)
