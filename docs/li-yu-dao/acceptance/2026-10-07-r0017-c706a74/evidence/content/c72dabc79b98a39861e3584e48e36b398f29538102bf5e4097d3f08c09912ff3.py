"""Author one brace relocation; model literal active source without C++ compilation."""
from pathlib import Path
import difflib, hashlib, json, re, subprocess
OUT=Path(__file__).resolve().parent
SOURCE=Path('C:/lr17s1/ck3_autonomous_player/native_bridge/src/bridge.cpp')
REL='ck3_autonomous_player/native_bridge/src/bridge.cpp'
HEAD='c706a74f9d00dd842b7edce8901fb3417344fd9c'
CACHE=Path('C:/lr17b1/CMakeCache.txt')
HEADER=SOURCE.parents[1]/'include/xar_bridge/h2743_stock_private_query_v1.hpp'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def ref(path):
 path=Path(path).resolve();raw=path.read_bytes();return {'path':path.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def put(name,value):
 path=OUT/name;raw=value.encode('utf-8') if isinstance(value,str) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with path.open('xb') as f:f.write(raw)
 return ref(path)
def active_source(text,enabled):
 macros={k:1 for k in enabled};macros.update(_WIN32=1,_WIN64=1,_MSC_VER=1)
 # Included production header supplies this exact default numeric macro.
 macros.setdefault('XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1',0)
 lines=text.splitlines();result=['']*len(lines);stack=[];i=0
 def evaluate(expr):
  expr=re.sub(r'defined\s*\(\s*(\w+)\s*\)',lambda m:str(int(m[1] in macros)),expr)
  expr=re.sub(r'defined\s+(\w+)',lambda m:str(int(m[1] in macros)),expr)
  expr=re.sub(r'\b[A-Za-z_]\w*\b',lambda m:str(macros.get(m[0],0)),expr)
  expr=expr.replace('&&',' and ').replace('||',' or ');expr=re.sub(r'!(?!=)',' not ',expr)
  need(not re.search(r'[^\s\d()andort!=<>+*\-/]',expr),'Unresolved preprocessor expression: '+expr)
  return bool(eval(expr,{'__builtins__':{}},{}))
 while i<len(lines):
  start=i;line=lines[i]
  while line.rstrip().endswith('\\'):
   line=line.rstrip()[:-1]+' '+lines[i+1].lstrip();i+=1
  m=re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif|define|undef)\b(.*)',line)
  if m:
   kind,expr=m.groups();parent=all(s['active'] for s in stack)
   if kind in ['if','ifdef','ifndef']:
    value=evaluate(expr) if kind=='if' else (expr.strip() in macros)==(kind=='ifdef')
    stack.append({'active':parent and value,'seen':value,'parent':parent})
   elif kind=='elif':
    s=stack[-1];value=evaluate(expr);s['active']=s['parent'] and not s['seen'] and value;s['seen']|=value
   elif kind=='else':
    s=stack[-1];s['active']=s['parent'] and not s['seen'];s['seen']=True
   elif kind=='endif':stack.pop()
   elif parent:
    fields=expr.strip().split(None,1)
    if fields and re.fullmatch(r'\w+',fields[0]):
     if kind=='undef':macros.pop(fields[0],None)
     elif len(fields)==1:macros[fields[0]]=1
     elif re.fullmatch(r'\d+',fields[1]):macros[fields[0]]=int(fields[1])
  elif parent:
   for j in range(start,i+1):result[j]=lines[j]
  i+=1
 need(not stack,'Unclosed preprocessor condition')
 return '\n'.join(result)
def brace_graph(text):
 def mask(m):return ''.join('\n' if c=='\n' else ' ' for c in m[0])
 text=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\\n])\'',mask,text)
 nest=[];parent={};closing={};line=1
 for c in text:
  if c=='\n':line+=1
  elif c=='{':parent[line]=nest[-1] if nest else None;nest.append(line)
  elif c=='}':
   need(bool(nest),'Unmatched source brace at '+str(line));closing[nest.pop()]=line
 need(not nest,'Unclosed source braces')
 return parent,closing
def main():
 raw=SOURCE.read_bytes();need(ref(SOURCE)['sha256']=='666a2d3673abfe443f5fba152ec0fc51b11fb8a0b217891b9db069a712e98adf','Frozen source changed')
 blob=subprocess.run(['git','-C','C:/workspace/ck3_eternal_recurrence','show',HEAD+':'+REL],capture_output=True)
 need(blob.returncode==0 and blob.stdout==raw,'Actual clean c706 blob must equal frozen compiled export')
 text=raw.decode('utf-8')
 before='          }\n          }\n        } else if (\n            step == xar::ck3_11906::\n                        kZhongguoAiOwnedCaseSnapshotV1Step) {'
 after='          }\n        } else if (\n            step == xar::ck3_11906::\n                        kZhongguoAiOwnedCaseSnapshotV1Step) {'
 need(text.count(before)==1,'Exact original premature closure marker required')
 candidate=text.replace(before,after,1)
 before2='        } else {\n          native_step_dispatched = false;\n        }\n        if (!native_step_dispatched) {\n          native_step_dispatched = true;\n        if (step == xar::ck3_11906::kLoadedFeatureManifestV1Step) {'
 after2=before2.replace('        }\n        if (!native_step_dispatched)', '        }\n        }\n        if (!native_step_dispatched)',1)
 need(candidate.count(before2)==1,'Exact segment boundary marker required')
 candidate=candidate.replace(before2,after2,1)
 flags={m[1]:m[2] for line in CACHE.read_text(encoding='utf-8-sig').splitlines() if (m:=re.fullmatch(r'(XAR_CK3_[A-Z0-9_]+):BOOL=(ON|OFF)',line))}
 actual={k for k,v in flags.items() if v=='ON'};need(len(actual)==12,'Actual 12 ON cache required')
 need('#define XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 0' in HEADER.read_text(encoding='utf-8'),'Actual numeric macro header default required')
 modes={'actual12':actual,'default_private_off':set(),'all_declared_private_on':set(flags)}
 checks=[];mappings=[]
 for name,enabled in modes.items():
  original_parent,original_close=brace_graph(active_source(text,enabled));fixed_parent,fixed_close=brace_graph(active_source(candidate,enabled))
  cases=[('original_premature_outer_closure_reproduced',original_close[20143]==22728),
         ('original_ai_handler_binds_to_outer_dispatch',original_parent[22730]==14775),
         ('candidate_ai_handler_in_segment3',fixed_parent[22729]==20143),
         ('candidate_false_fallback_in_segment3',fixed_parent[22854]==20143),
         ('candidate_segment3_closes_after_false_fallback',fixed_close[20143]==22857),
         ('later_segment_boundaries_unchanged',all(fixed_parent[n]==original_parent[n] for n in [22858,24196,26568])),
         ('event_tail_fallback_unchanged',fixed_parent[27484]==original_parent[27484]==26568)]
  if name!='default_private_off':cases.append(('normal_exit_keeps_first_segment_route',original_parent[17082]==fixed_parent[17082]==14775))
  for label,ok in cases:need(ok,name+': '+label);checks.append({'mode':name,'check':label,'passed':ok})
  mappings.append({'mode':name,'enabled_count':len(enabled),'original_segment3_close_line':original_close[20143],'original_ai_parent':original_parent[22730],
                   'candidate_segment3_close_line':fixed_close[20143],'candidate_ai_parent':fixed_parent[22729],
                   'candidate_false_fallback_parent':fixed_parent[22854],'event_tail_call_parent':fixed_parent[27484]})
 patch=''.join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile='a/'+REL,tofile='b/'+REL))
 patch_ref=put('CANDIDATE.incremental.patch',patch)
 candidate_ref=put('bridge.cpp.candidate',candidate)
 base=OUT/'apply-check-base';target=base/REL;target.parent.mkdir(parents=True);target.write_bytes(raw)
 checked=subprocess.run(['git','apply','--check',patch_ref['path']],cwd=base,capture_output=True)
 put('GIT-APPLY-CHECK.stdout',checked.stdout.decode('utf-8',errors='replace'));put('GIT-APPLY-CHECK.stderr',checked.stderr.decode('utf-8',errors='replace'))
 need(checked.returncode==0,'Exact isolated apply check failed')
 focused=put('OFFLINE-BRACE-MODEL.actual.json',{'status':'PASS_SOURCE_MODEL_ONLY','checks':checks,'passed':len(checks),'mappings':mappings,'actual_flags_on':sorted(actual),'actual_flag_census':flags,'C++_compiled':False,'native_builds':0})
 client=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/mcp-client-001')
 refs=[ref(p) for p in sorted(client.iterdir()) if p.name.startswith(('0015-','0016-','0017-')) and ('.native-01.json' in p.name or '.sdk-result.json' in p.name)]
 index=put('INDEX.json',{'status':'SOURCE_ONLY_BRACE_RELOCATION_CANDIDATE_AFTER_GENUINE_CLOSE_REQUIRED','source_revision':HEAD,'target':REL,'before':ref(SOURCE),'after':candidate_ref,
                       'patch':patch_ref,'source_model':focused,'actual_cache':ref(CACHE),'included_numeric_macro_default':ref(HEADER),'original_receipts':refs,
                       'apply_check':{'exit_code':checked.returncode,'workdir':base.as_posix()},'normal_exit_route_affected':False,
                       'deferred_event_submission':False,'deferred_state_basis':'Unmatched legacy step enters segment3 and sets handled true; malformed closure prevents reset false. All later segments and the sole SubmitSelectEventOption tail call are skipped. incoming frame is loop-local; no event command/mailbox request is retained by this path.',
                       'native_event_dispatch_trace_available':False,'runtime_pending_pointer_observed':None,'future_fixed_runtime':None,'main_writes':0,'native_builds':0,'SDK_calls':0,'game_calls':0,'bus_calls':0})
 print(json.dumps({'INDEX':index,'patch':patch_ref,'focused':focused,'source_model_checks_passed':len(checks),'apply_check_exit_code':checked.returncode,'main_changed':False}))
if __name__=='__main__':main()
