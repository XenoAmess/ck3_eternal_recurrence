from pathlib import Path
source=Path(__file__).with_name('review_scoped_ui_C07_reinforcement_a01.py').read_text(encoding='utf-8')
source=source.replace('scoped-ui-C07-independent-review-reinforcement-a01','scoped-ui-C08-independent-review-reinforcement-a02')
source=source.replace('A3A31116C17E6313938677858AD230DD7945C8A8651FF16D475B14A3B1485CE5','169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640')
source=source.replace("'scoped_ui_research_a07.py','run_paused_ui_stage_a06.py','preserve_paused_ui_checkpoint_a05.py','prepare_runtime_binding_and_plan_a07.py'", "'scoped_ui_research_a08.py','run_paused_ui_stage_a07.py','preserve_paused_ui_checkpoint_a06.py','prepare_runtime_binding_and_plan_a08.py'")
source=source.replace("'require','original_gui_owner_identity'", "'require','original_combat_knight_fields','original_gui_owner_identity'")
source=source.replace('C07 exact selected AST pure-mock-no-requests','C08 exact selected AST pure-mock-no-requests')
start=source.index("class Mock:")
extra='''# Each individual getter member has independent presence/type/bounds negatives.
for field in ('combat_knights_read_available','left_knight_count','right_knight_count','left_knight_breakdown','right_knight_breakdown'):
 for variant in ('absent','wrong-type'):
  def getter_bad(field=field,variant=variant):
   body=window()
   if variant=='absent':body.pop(field)
   else:body[field]='true' if field=='combat_knights_read_available' else True if field.endswith('_count') else []
   ns['original_combat_knight_fields'](body)
  case('getter-'+field+'-'+variant,getter_bad,True)
for count in (-1,4097):
 def bounds(count=count):
  body=window();body['right_knight_count']=count;ns['original_combat_knight_fields'](body)
 case('getter-count-bound-'+str(count),bounds,True)
def zero_empty():
 body=window();body.update(left_knight_count=0,right_knight_count=0,left_knight_breakdown='',right_knight_breakdown='')
 assert ns['original_combat_knight_fields'](body)==(0,0,'','')
 ns['verify_window'](body,'combat',16777218,VALUES,CONFIG)
case('getter-zero-count-empty-markup-is-legal',zero_empty)
'''
source=source[:start]+extra+source[start:]
start=source.index("assert inputs==[identity(SOURCE/f)for f in files]")
extra='''# Only the shared getter gate and its call were added to C07; daily/monitor/frames unchanged.
oldtree=ast.parse((SOURCE/'scoped_ui_research_a07.py').read_text(encoding='utf-8'))
oldfuncs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
newfuncs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
same=[]
for name,node in oldfuncs.items():
 if name=='verify_window':continue
 assert ast.dump(node,include_attributes=False)==ast.dump(newfuncs[name],include_attributes=False),name
 same.append(name)
v=copy.deepcopy(newfuncs['verify_window'])
v.body=[n for n in v.body if not(isinstance(n,ast.If)and any(isinstance(x,ast.Name)and x.id=='original_combat_knight_fields'for x in ast.walk(n)))]
assert ast.dump(v,include_attributes=False)==ast.dump(oldfuncs['verify_window'],include_attributes=False)
structural['C07_other_functions_AST_byte_semantics_equal']=same
assert all(c['status']=='PASS'for c in cases),cases
'''
source=source[:start]+extra+source[start:]
source=source.replace('INDEPENDENT_EXACT_C07_AST_MOCK_REVIEW_NOT_LIVE_OR_PIXEL_TRUTH','INDEPENDENT_EXACT_C08_AST_MOCK_REVIEW_NOT_LIVE_OR_PIXEL_TRUTH')
source=source.replace('C07 GUI owner/RNG0/same-frame and day guards pass; missing/invalid getter field false accepts require create-only C08 shared typed getter gate before live','C08 targeted getter regressions and inherited GUI owner/RNG0/same-frame/day/monitor guards PASS; suitable for root-owned live only with new exact source/DLL/eight-test admission and fresh offline/screen prerequisites')
source=source.replace("'live_ready_for_this_C07':False", "'consumer_ready_for_root_owned_live':True,'mechanism_or_pixels_closed':False,'full_DLL_eight_tests_and_fresh_root_admission_still_required':True")
exec(compile(source,str(Path(__file__).resolve()),'exec'))
