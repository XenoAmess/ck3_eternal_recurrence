"""Original QOL UI25 business controller using the one shared case client."""
from pathlib import Path
import ctypes,hashlib,json,subprocess,sys,time
REPO=PY=COORD=None
DECISIONS=('xqol_enable_auto_appointment_decision','xqol_disable_auto_appointment_decision','xqol_mass_conversion_decision')
TOOLS={'snapshot':'ck3_take_snapshot','campaign-root':'ck3_query_campaign_root_context_v1',
       'title-holder':'ck3_query_title_holder_v1','open-decisions':'ck3_open_ingame_decisions_v1',
       'center-title':'ck3_center_map_on_landed_title_v1','title-own-laws':'ck3_query_title_own_laws_v1',
       'query-decision':'ck3_query_ingame_decision_item_v1','select-decision':'ck3_select_ingame_decision_item_v1',
       'event-context':'ck3_query_current_event_window_context_v1','event-option':'ck3_select_event_option'}
STAGES=['civic-candidates','military-candidates','million-off','million-on','million-restored','civic-appointment','military-appointment','guards','slider-anchor']
STAGES += ['cancel-'+str(p) for p in (0,1,49,50,51,99,100)]
STAGES += ['save-'+str(p) for p in (100,99,51,50,49,1,0)]
STAGES += ['restore-anchor','map-clean']

def require(value,message):
    if not value: raise RuntimeError(message)

def _operator_reviewer(client):
    reviewer=getattr(client,'operator_reviewer','/root')
    require(type(reviewer) is str and reviewer.strip(),'Actual operator reviewer missing')
    return reviewer

def read(path): return json.loads(Path(path).read_bytes())

def pin(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def read_last_line(path):return json.loads(Path(path).read_text(encoding='utf-8').splitlines()[-1])

class Controller:
    def __init__(self,context,client,*,prior_final6=None):
            global REPO,PY,COORD
            from types import SimpleNamespace
            self.context=context;self.client=client;self.operator_reviewer=_operator_reviewer(client)
            REPO=Path(context['repo_root']);PY=client.selection.locations['python'];COORD=REPO/'tools/desktop_coordinate_map.py'
            self.a=SimpleNamespace(keeper_root=client.keeper)
            self.out=client.output/'ui25';require(not self.out.exists(),'UI25 output already consumed; never replay')
            self.out.mkdir();(self.out/'requests').mkdir()
            self.live=client.live;self.caller=client.output;self.frozen=client.frozen
            self.pending=read(self.caller/'root-same-live-required-ui-awaiting.json')
            require(self.pending['run_id']==self.frozen['run_id'],'Actual UI scene changed')
            require((self.caller/'actual-original-readonly9-results.json').is_file(),'Original readonly9 not complete')
            if prior_final6 is None:
                require((self.caller/'actual-original-final6-results.json').is_file(),'Original final6 not complete')
            else:
                require(context['case_contract'].get('acceptance_scope')=='original_song_ui_tail','External prior final6 is only valid for the explicit UI-tail case')
                require(pin(prior_final6['path'])==prior_final6,'Original frozen prior final6 changed')
                prior=read(prior_final6['path'])
                require(prior.get('original23_verified') is True and prior.get('product_pass') is False and len(prior.get('rows',[]))==6 and all(r.get('ok') is True and not r.get('error') and r.get('finished_at') for r in prior['rows']),'Original frozen prior final6 is incomplete')
                write(self.out/'prior-final6-external-reference.json',{'source':prior_final6,'current_scene_did_not_execute_final6':True,'source_case_is_not_rewritten':True})
            self.pid=self.pending['pid'];self.ctime=self.pending['create_time'];self.deadline=self.pending['original_hold_deadline']
            self.seq=0;self.stage=0;self.records={};self.gaps=[];self.hwnd=None;self.frame_id=None;self.latest=None
            import psutil,pyautogui
            self.psutil=psutil;self.gui=pyautogui
            sys.path.insert(0,str(REPO/'tools'));import desktop_coordinate_map
            self.coords=desktop_coordinate_map
            self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            self.kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];self.kernel.OpenProcess.restype=ctypes.c_void_p
            self.kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];self.kernel.WaitForSingleObject.restype=ctypes.c_uint32
            self.kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            self.handle=self.kernel.OpenProcess(0x100000|0x1000,False,self.pid)
            require(self.handle,'Cannot retain actual current UI process handle')
            write(self.out/'actual-controller-start.json',{'run_id':self.frozen['run_id'],'pending':pin(self.caller/'root-same-live-required-ui-awaiting.json'),'deadline':self.deadline,'shared_host':client.selection.manifest['host'],'operator_reviewer':self.operator_reviewer,'root_review_required':True})
    def remaining(self):return self.deadline-time.time()
    def current(self):
            r=self.client.guard()
            require(r.get('hold_until_utc_estimated')==self.deadline,'Original hold deadline changed')
            return r
    def guard(self):
            require(self.remaining()>90,'Original normal Quit reserve reached; stop new business input')
            require(self.kernel.WaitForSingleObject(self.handle,0)==258,'Original process ended')
            p=self.psutil.Process(self.pid)
            require(p.name().lower()=='ck3.exe' and abs(p.create_time()-self.ctime)<.001,'Actual CK3 identity changed')
            lease=read_last_line(self.a.keeper_root/'journal.jsonl')
            require(lease.get('result')=='OWNED_CAS' and lease['lease']['task_id']==self.frozen['screen_task'] and not (self.a.keeper_root/'report.json').exists(),'Original keeper no longer owns screen')
            state=self.coords.foreground_state()
            require(state['foreground_pid']==self.pid and state['focus_hwnd']>0,'Current CK3 foreground/focus unavailable')
            if self.hwnd is None:self.hwnd=state['foreground_hwnd']
            require(state['foreground_hwnd']==self.hwnd,'Actual HWND changed')
            return state
    def check_frame(self,frame):
            self.client.validate_frame(frame,require_event_free=False,require_paused=False)
            d=frame['diagnostics'];actor=frame['played_character']
            identity=(d.get('bridge_pid'),d.get('pipe_name'),d.get('connection_generation'),actor.get('character_id'))
            require(identity[0]==self.pid and all(v is not None for v in identity),'Actual native UI identity missing')
            if self.frame_id is None:self.frame_id=identity
            require(identity==self.frame_id,'Same-live actor/pipe/generation changed')
            return frame
    def call(self,name,argv):
            self.guard()
            with (self.out/(name+'.stdout.log')).open('xb') as out,(self.out/(name+'.stderr.log')).open('xb') as err:
                p=subprocess.run([str(PY),'-B','-X','utf8',*map(str,argv)],cwd=REPO,stdout=out,stderr=err,
                     timeout=max(1,min(300,self.remaining()-90)))
            write(self.out/(name+'.exit.json'),{'argv':list(map(str,argv)),'exit_code':p.returncode})
            require(p.returncode==0,name+' failed; no replay')
            if name!='request-original-normal-quit':self.guard()
    def typed(self,action,args,prefix):
            require(action in TOOLS,'Typed action is not an existing QOL capability')
            params={}
            if action=='snapshot':params={'include_native_command_history':False}
            elif action=='title-holder':
                require(type(args.get('title_id')) is int and args['title_id']>0,'Actual numeric title ID required');params={'title_id':args['title_id']}
            elif action=='center-title':
                require(type(args.get('title_key')) is str and args['title_key'] and args['title_key'].isascii(),'Actual ASCII title key required');params={'title_key':args['title_key']}
            elif action=='title-own-laws':
                require(type(args.get('title_id')) is int and 0<=args['title_id']<2**32-1,'Actual full uint32 title ID required');params={'title_id':args['title_id']}
            elif action in ('query-decision','select-decision'):
                require(args.get('decision_key') in DECISIONS,'Actual QOL decision key required');params={'decision_key':args['decision_key']}
            elif action in ('event-context','event-option'):
                require(type(args.get('event_instance_id')) is int and args['event_instance_id']>0,'Actual event instance ID required')
                params={'event_instance_id':args['event_instance_id']}
                if action=='event-option':
                    require(type(args.get('option_number')) is int and args['option_number']>0 and args.get('root_confirmed_option_enabled') is True,'Root must review the actual enabled authored option')
                    params['option_number']=args['option_number']
            identifier='qol-same-live-'+prefix
            row=self.client.execute_plan([{'id':identifier,'tool':TOOLS[action],'args':params,'fresh_revision':True}],identifier)[0]
            write(self.out/(prefix+'.actual-result.json'),row)
            if action=='snapshot':self.check_frame(row['result'])
            if isinstance(row.get('after_snapshot'),dict):self.check_frame(row['after_snapshot'])
            if action=='title-holder':
                holder=row['result'].get('title_holder') if isinstance(row['result'],dict) else None
                require(isinstance(holder,dict),'Actual normalized title_holder payload missing')
                return holder
            return row['result']
    def capture(self,name):
            before=self.guard();image=self.gui.screenshot();require(image.size==tuple(self.gui.size()),'PNG/current desktop size differs')
            path=self.out/(name+'.png');require(not path.exists(),'Capture name consumed');image.save(path)
            after=self.guard();require(before['foreground_hwnd']==after['foreground_hwnd'],'Window changed during capture')
            meta={**pin(path),'size':list(image.size),'pid':self.pid,'create_time':self.ctime,'focus':after,'captured_at_unix':time.time(),'operator_reviewer':self.operator_reviewer,'root_review_required':True}
            write(path.with_suffix('.image.json'),meta);self.latest=meta;return meta
    def publish(self):
            scene=self.capture('scene-'+str(self.seq).zfill(4))
            write(self.out/('await-'+str(self.seq).zfill(4)+'.json'),{'sequence':self.seq,'run_id':self.live.name,'operator_reviewer':self.operator_reviewer,
              'stage':STAGES[self.stage] if self.stage<len(STAGES) else 'all-records-present',
              'original_png':scene,'deadline':self.deadline,'remaining_seconds':self.remaining(),'request_path':str(self.out/'requests'/('request-'+str(self.seq).zfill(4)+'.json')),
              'actions':['click','move','drag','scroll','typed','record','gap','finish'],'no_business_result_from_input_ACK':True})
            print('QOL_SAME_LIVE_SCENE '+str(self.out/('await-'+str(self.seq).zfill(4)+'.json')),flush=True)
    def source_guard(self,req):
            require(req.get('reviewer')==self.operator_reviewer and req.get('run_id')==self.live.name and req.get('sequence')==self.seq,'Request is not current operator custody')
            require(req.get('source')=={k:self.latest[k] for k in ('path','bytes','sha256')},'Root review must bind the latest original PNG')
            require(pin(self.latest['path'])==req['source'],'Root reviewed PNG changed')
            self.guard()
    def mouse(self,req,prefix):
            preview=req.get('preview');point=req.get('point')
            require(isinstance(preview,list) and len(preview)==4 and isinstance(point,list) and len(point)==2,'Explicit actual preview rectangle and point required')
            if req['action'] in ('drag','scroll'):
                self.pointer_continuation(req,prefix,preview,point)
                self.typed('snapshot',{},prefix+'-independent-native-after');return
            argv=[COORD,'--source-image',self.latest['path'],'--preview-left',preview[0],'--preview-top',preview[1],
                 '--preview-width',preview[2],'--preview-height',preview[3],'--observed-x',point[0],'--observed-y',point[1],
                 '--'+req['action'],'--receipt',self.out/(prefix+'-after.png')]
            if req['action']=='move':
                region=req.get('reviewed_region');require(isinstance(region,list) and len(region)==4,'Hover requires explicit root reviewed region')
                argv+=['--reviewed-left',region[0],'--reviewed-top',region[1],'--reviewed-width',region[2],'--reviewed-height',region[3],'--expected-foreground-hwnd',self.hwnd]
            else:argv+=['--button',req.get('button','left'),'--expected-foreground-hwnd',self.hwnd,'--max-source-age-seconds','60']
            self.call(prefix,argv);time.sleep(.5);self.guard()
            self.typed('snapshot',{},prefix+'-independent-native-after')
    def pointer_continuation(self,req,prefix,preview,point):
            # Same repository mapper for both axes and reviewed bounds; no handwritten scale.
            size=tuple(self.gui.size());require(size==tuple(self.latest['size']),'Source PNG/live dimensions differ')
            region=req.get('reviewed_region');require(isinstance(region,list) and len(region)==4,'Drag/wheel requires current root reviewed rectangle')
            make=lambda observed:self.coords.Mapping(tuple(preview),tuple(observed),size,size,
                self.coords.map_point(preview_bounds=tuple(preview),observed_point=tuple(observed),target_size=size))
            start=make(point);self.coords.validate_reviewed_region(start,tuple(region))
            end=None
            if req['action']=='drag':
                target=req.get('end_point');require(isinstance(target,list) and len(target)==2,'Actual reviewed drag endpoint required')
                end=make(target);self.coords.validate_reviewed_region(end,tuple(region))
            else:require(type(req.get('wheel_steps')) is int and 0<abs(req['wheel_steps'])<=10,'Actual bounded wheel direction/count required')
            receipt=self.out/(prefix+'-after.png');self.coords.validate_receipt_path(receipt,sidecar=True)
            before=self.guard()
            move=self.coords.move_pointer(mapping=start,reviewed_bounds=tuple(region),source_image=Path(self.latest['path']),
                receipt_path=self.out/(prefix+'-mapped-start.png'),desktop=self.gui,expected_foreground_hwnd=self.hwnd)
            require(not move['failures'],'Mapped start pointer did not read back')
            self.guard()
            try:
                if end:self.gui.dragTo(*end.screen_point,duration=.35,button='left')
                else:self.gui.scroll(req['wheel_steps'])
            finally:
                if end and self.coords.mouse_button_state()['left']:self.gui.mouseUp(button='left')
            after=self.guard();image=self.gui.screenshot();image.save(receipt)
            require(image.size==size==tuple(self.gui.size()),'Desktop dimensions changed during input')
            require(all(before[k]==after[k] for k in ('foreground_hwnd','foreground_pid','focus_hwnd')),'Focus changed during input')
            require(not any(self.coords.mouse_button_state().values()),'Mouse button remained pressed')
            if end:require(tuple(self.gui.position())==end.screen_point,'Drag endpoint readback differs')
            write(receipt.with_name(receipt.name+'.json'),{'action':req['action'],'source':{k:self.latest[k] for k in ('path','bytes','sha256')},
                'preview':preview,'observed_start':point,'mapped_start':list(start.screen_point),
                'observed_end':req.get('end_point'),'mapped_end':list(end.screen_point) if end else None,
                'wheel_steps':req.get('wheel_steps'),'receipt':pin(receipt),'before_focus':before,'after_focus':after,
                'value_truth':'ROOT_MUST_READ_THE_NEW_ORIGINAL_PERCENT_OR_CANDIDATE_LIST','input_ACK_is_not_business_PASS':True})
    def record(self,req,prefix):
            stage=STAGES[self.stage];o=req.get('observation',{})
            require(req.get('stage')==stage and isinstance(o,dict),'Only the current actual business checkpoint may be recorded')
            evidence=req.get('evidence',[]);require(evidence and all(pin(r['path'])==r for r in evidence),'Preserved original root evidence required')
            require(any(r['path']==self.latest['path'] for r in evidence),'Current original PNG must be part of actual review')
            require(o.get('direct_original_review') is True,'Root must directly inspect the original business PNG')
            if stage in ('civic-candidates','military-candidates'):
                kind='civic' if stage.startswith('civic') else 'military';key='d_zhexi' if kind=='civic' else 'e_minister_grand_marshal'
                law='celestial_appointment_succession_law' if kind=='civic' else 'celestial_grand_marshal_appointment_succession_law'
                require(o.get('title_key')==key and o.get('law')==law and o.get('title_id',0)>0,'Actual requested title/law binding missing')
                require(o.get('full_candidates_reviewed') is True and isinstance(o.get('candidates'),list) and o['candidates'],'Actual complete native candidate list required')
                require(o.get('eligibility_and_score_breakdown_reviewed') is True,'Full qualification/score review required')
                o['native_title_holder_readback']=self.typed('title-holder',{'title_id':o['title_id']},prefix+'-holder')
                require(o['native_title_holder_readback'].get('available') is True,'Actual native title holder readback unavailable')
            elif stage.startswith('million-'):
                require(o.get('candidate_character_id')==self.frame_id[3] and o.get('independent_human_candidate') is True,'Original independent player must be a natural native candidate')
                require(o.get('complete_same_title_candidate_row') is True and type(o.get('score')) in (int,float),'Actual complete score breakdown required')
                if stage=='million-off':require(type(o.get('original_switch_enabled')) is bool,'Original appointment switch must be recorded')
                else:
                    base=self.records['million-off']['observation'];require(o.get('title_id')==base.get('title_id'),'Million check crossed title')
                    expected=base['score']-1000000 if stage=='million-on' else base['score']
                    require(o['score']==expected,'Actual million penalty/restoration is not exact')
                require(o.get('auto_appointment_enabled')==(stage=='million-on'),'Actual decision switch state differs')
                if stage=='million-restored':
                    require(o.get('original_switch_restored') is True and o.get('final_switch_enabled')==base['original_switch_enabled'],'Original appointment switch not restored after off-score readback')
            elif stage in ('civic-appointment','military-appointment'):
                kind=stage.split('-')[0];base=self.records[kind+'-candidates']['observation']
                require(o.get('title_id')==base['title_id'] and o.get('chosen_character_id') in [x.get('character_id') for x in base['candidates'] if x.get('eligible') is True and x.get('is_ai') is True],'Chosen AI must come from the actual eligible native list')
                require(o.get('actual_successor_character_id')==o['chosen_character_id'] and o.get('native_appointment_confirmed') is True,'Actual native appointment/successor readback missing')
                o['native_title_holder_readback']=self.typed('title-holder',{'title_id':o['title_id']},prefix+'-holder')
                if 'actual_holder_character_id' in o:require(o['native_title_holder_readback'].get('holder_character_id')==o['actual_holder_character_id'],'Holder UI/native readbacks differ')
            elif stage=='guards':
                require(o.get('mod_created_guard_actual') is True and o.get('external_protection_original_clear_actual') is True,'Both actual guard paths require evidence')
            elif stage=='slider-anchor':require(type(o.get('persisted_anchor')) is int and 0<=o['persisted_anchor']<=100,'Actual persistent anchor must be read')
            elif stage.startswith('cancel-'):
                p=int(stage.split('-')[1]);require(o.get('draft_value')==p and o.get('cancel_option_executed') is True and o.get('reopened_persisted_value')==self.records['slider-anchor']['observation']['persisted_anchor'],'Actual boundary draft/cancel/reopen values differ')
            elif stage.startswith('save-') or stage=='restore-anchor':
                p=int(stage.split('-')[1]) if stage.startswith('save-') else self.records['slider-anchor']['observation']['persisted_anchor']
                require(o.get('draft_value')==p and o.get('save_option_executed') is True and o.get('reopened_persisted_value')==p,'Actual boundary save/reopen differs')
                require(o.get('pending_naturally_completed') is True and o.get('summary_count')==1 and o.get('event_windows_cleared') is True,'Actual natural pending/one summary/clean window closure missing')
                require(o.get('no_script_pending_clear_or_setfaith') is True,'Natural chain may not be replaced by script clears')
            elif stage=='map-clean':
                frame=self.typed('snapshot',{},prefix+'-map');require(frame.get('active_event') is None,'Actual map still has an event')
                require(o.get('all_panels_physically_closed') is True and o.get('current_map_chrome_reviewed') is True,'Actual map must be reviewed after physical panel closure')
            row={'stage':stage,'observation':o,'evidence':evidence,'operator_reviewer':self.operator_reviewer,'root_review_request':pin(self.out/'requests'/('request-'+str(self.seq).zfill(4)+'.json')),'status':'ROOT_ORIGINAL_REVIEW_RECORDED_NO_PRODUCT_PASS_INFERRED'}
            write(self.out/(prefix+'.review.json'),row);self.records[stage]=row;self.stage+=1
    def finish(self,reason):
            result={'run_id':self.frozen['run_id'],'records':self.records,'gaps':self.gaps,'remaining_stages':STAGES[self.stage:],'reason':reason,
                'status':'ACTUAL_ROOT_REVIEWS_RECORDED' if self.stage==len(STAGES) and not self.gaps else 'INCOMPLETE_GAPS_PRESERVED',
                'gui_contract_qualified':self.stage==len(STAGES) and not self.gaps,'product_release_pass':False,'deadline_unchanged':self.deadline}
            write(self.out/'actual-same-live-records.json',result)
            return result
    def run(self):
            try:
                self.typed('snapshot',{},'initial-current-native-frame');self.publish()
                while self.remaining()>95:
                    request=self.out/'requests'/('request-'+str(self.seq).zfill(4)+'.json')
                    if not request.is_file():self.guard();time.sleep(.25);continue
                    req=read(request);self.source_guard(req);action=req.get('action');prefix='action-'+str(self.seq).zfill(4)
                    if action in ('click','move','drag','scroll'):self.mouse(req,prefix)
                    elif action=='typed':
                        self.typed(req['typed_action'],req.get('arguments',{}),prefix)
                        if req['typed_action']!='snapshot':self.typed('snapshot',{},prefix+'-independent-native-after')
                    elif action=='record':self.record(req,prefix)
                    elif action=='gap':
                        require(req.get('stage')==STAGES[self.stage] and req.get('reason'),'Explicit current-stage gap required')
                        self.gaps.append({'stage':STAGES[self.stage],'reason':req['reason'],'request':pin(request),'original_png':self.latest});self.stage+=1
                    elif action=='finish':return self.finish(req.get('reason','Root requested preserved normal closure'))
                    else:raise RuntimeError('Unsupported request action; no speculative input')
                    write(self.out/(prefix+'.complete.json'),{'request':pin(request),'stage_index':self.stage,'input_ACK_is_not_business_pass':True})
                    self.seq+=1;self.publish()
                return self.finish('Original normal Quit reserve reached; remaining business stages preserved as GAP')
            except BaseException as error:
                write(self.out/'controller-error-preserved.json',{'error':type(error).__name__+': '+str(error),'records':self.records,'gaps':self.gaps,'deadline_unchanged':self.deadline,'no_replay':True})
                raise
            finally:
                if self.handle:self.kernel.CloseHandle(self.handle)
            return 1
