"""One new d26/d27 saved-state pair; no recorder or historical film approval."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

FROZEN=Path('C:\\Users\\1\\ck3-a04-mechanism-evidence-20261001\\reinforcement-attempt-12-R0129-native-center-diagnostic\\source')
SOURCE=FROZEN/'promo/ck3_native_war_ai/episode-02-battle-second-half'
sys.path.insert(0,str(SOURCE))
import remaining_live_step as step
import pursuit_live_step as transport
NEW=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
OUTPUT=NEW/'ck3-output'
def require(ok,reason):
    if not ok:
        raise RuntimeError(reason)
def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
def identity(path):
    path=Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper()}
def preserved_save(body,label,evidence):
    checkpoint=body.get('checkpoint') or {}
    require(body.get('accepted') is True and checkpoint.get('status')=='saved','Native save refused')
    original=Path(checkpoint['path'])
    source=identity(original)
    require(source['bytes']==checkpoint['size'] and source['sha256']==checkpoint['sha256'].upper(),'Save bytes differ from native receipt')
    target=evidence/(label+'-immutable.ck3')
    require(not target.exists(),'Immutable save already exists')
    shutil.copyfile(original,target)
    require(identity(target)['sha256']==source['sha256'],'Preserved bytes changed')
    return identity(target)
def capture_window(evidence,label):
    import psutil
    import win32gui
    import win32process
    sys.path.insert(0,'D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927/wgc-lib')
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
    games=[p for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower()=='ck3.exe']
    require(len(games)==1 and str(NEW/'ck3-state/profile').replace('\\','/').lower() in ' '.join(games[0].info['cmdline']).replace('\\','/').lower(),
            'WGC target is not this isolated CK3 process')
    pid=games[0].pid
    windows=[]
    def enum(hwnd,_):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1]==pid:
            rect=win32gui.GetWindowRect(hwnd)
            if rect[2]-rect[0]>500 and rect[3]-rect[1]>300:
                windows.append(hwnd)
    win32gui.EnumWindows(enum,None)
    require(len(windows)==1,'CK3 visible window identity ambiguous')
    hwnd=windows[0]
    path=evidence/(label+'-window.png')
    events=[]
    capture=WindowsCapture(cursor_capture=False,draw_border=None,window_hwnd=hwnd)
    @capture.event
    def on_frame_arrived(frame:Frame,control:InternalCaptureControl):
        if not path.exists():
            frame.save_as_image(str(path))
            events.append({'at_utc':datetime.now(timezone.utc).isoformat(),'width':frame.width,'height':frame.height})
        control.stop()
    @capture.event
    def on_closed():
        pass
    control=capture.start_free_threaded()
    deadline=time.monotonic()+8
    while time.monotonic()<deadline and not path.exists() and not control.is_finished():
        time.sleep(.1)
    control.stop()
    if control.is_finished():
        control.wait()
    require(path.is_file(),'No CK3 original window frame')
    row={'kind':'original WGC HWND frame, not desktop composite','pid':pid,'creation_time':games[0].create_time(),'hwnd':hwnd,
         'title':win32gui.GetWindowText(hwnd),'rect':win32gui.GetWindowRect(hwnd),'events':events,'image':identity(path),
         'visual_review':'pending root original-pixel inspection','mouse_inputs':0}
    write(evidence/(label+'-window-receipt.json'),row)
    return row
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['before','advance','finish'],required=True)
    args=parser.parse_args()
    evidence=NEW/'evidence'
    evidence.mkdir(exist_ok=True)
    require(identity(SOURCE/'remaining_live_step.py')['sha256']=='393818F52C2E76C8AFC083F4FB3CD3BF6CF08C11C2784E37D80C2AADEF78B52B','Frozen controller changed')
    if args.mode=='before':
        binding=step.bind_session(OUTPUT,'e2-05-d26')
        before,br=transport.call(OUTPUT,'e2-05-d26-pre-advance-snapshot','ck3_take_snapshot',{},120)
        ok,values=step.snapshot_case(before,53146848,require_combat=True)
        require(ok,'New source paused actor/date/War4/Army18 frame not confirmed')
        control,cr=transport.call(OUTPUT,'e2-05-d26-native-control','ck3_query_battle_control_snapshot_v1',
                                  {'subject_army_id':18,'expected_revision':values['revision']},120)
        cok,cvalues=step.battle_control_case(control,values,53146848)
        require(cok,'New source combat/control revision not confirmed')
        image=capture_window(evidence,'d26-before')
        saved,sr=transport.call(OUTPUT,'e2-05-d26-before-save','ck3_save_checkpoint',{'expected_revision':values['revision']},120)
        require(saved.get('checkpoint',{}).get('date_raw')==53146848,'Saved source date changed')
        immutable=preserved_save(saved,'d26',evidence)
        after_save,ar=transport.call(OUTPUT,'d26-after-save-snapshot','ck3_take_snapshot',{},120)
        ok,av=step.snapshot_case(after_save,53146848,require_combat=True)
        require(ok and av['revision']>values['revision'],'Post-save paused source invalid')
        write(evidence/'before-pair.json',{'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_binding':binding,'snapshot':br,
              'native_control':cr,'control_values':cvalues,'image':image,'save':sr,'immutable':immutable,'after_save_snapshot':ar,
              'after_save_values':av,'episode_run_id':saved['checkpoint']['episode_run_id'],
              'scope':'saved-state sampling with original HWND evidence; no gameplay recorder or clean-span certification'})
        print(json.dumps({'result':'BEFORE_SAVED_WAITING_VISUAL_REVIEW','evidence':str(evidence),'values':av},ensure_ascii=False))
    elif args.mode=='advance':
        prior=json.loads((evidence/'before-pair.json').read_text(encoding='utf-8'))
        require((evidence/'d26-window-visual-review.json').is_file(),'Root review of actual d26 window frame required')
        review=json.loads((evidence/'d26-window-visual-review.json').read_text(encoding='utf-8'))
        require(review.get('actual_paused_d26_ui_observed') is True and review['image']==identity(evidence/'d26-before-window.png'),
                'D26 visual review does not bind original bytes')
        require(not (evidence/'one-day-intent.json').exists(),'Day advance already attempted; never resubmit')
        before,br=transport.call(OUTPUT,'d26-before-one-day-snapshot','ck3_take_snapshot',{},120)
        ok,values=step.snapshot_case(before,53146848,require_combat=True)
        require(ok and values==prior['after_save_values'],'Paused source changed after immutable preservation')
        token=6100103
        begun,bgr=step.private_call(OUTPUT,'knight-new-trace-begin',{'action':'private_phase_trace',
                     'step':'experimental-combat-phase-event-trace-begin-v1','expected_revision':values['revision'],
                     'combat_id':16777218,'managed_daily_sequence_token':token,'checkpoint_sequence':1},120)
        require(begun.get('accepted') is True and begun.get('combat_id')==16777218 and begun.get('managed_daily_sequence_token')==token,
                'Private trace begin not bound; no day advance')
        write(evidence/'one-day-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'source_values':values,'token':token,
                     'trace_begin':bgr,'at_most_one_day':True,'recorder_requested':False,'scope':'native saved-state pair; not film advance certification'})
        advanced,adr=transport.call(OUTPUT,'knight-new-one-day','ck3_execute_step',{'step':'life-advance','expected_revision':values['revision']},150)
        require(advanced.get('ending_date_raw')==53146872 and type(advanced.get('revision')) is int,'Single submitted day result ambiguous; do not retry')
        trace_error=None
        ended=None
        er=None
        try:
            ended,er=step.private_call(OUTPUT,'knight-new-trace-finish',{'action':'private_phase_trace',
                    'step':'experimental-combat-phase-event-trace-finish-v1','expected_revision':advanced['revision'],
                    'combat_id':16777218,'managed_daily_sequence_token':token},120)
        except (OSError,RuntimeError,TimeoutError,ValueError) as error:
            trace_error=repr(error)
        post,psr=transport.call(OUTPUT,'new-d27-snapshot','ck3_take_snapshot',{},120)
        ok,pv=step.snapshot_case(post,53146872,require_combat=False)
        require(ok,'Actual paused d27 source invalid; preserve attempt')
        control,cr=transport.call(OUTPUT,'new-d27-native-control','ck3_query_battle_control_snapshot_v1',
                                 {'subject_army_id':18,'expected_revision':pv['revision']},120)
        image=capture_window(evidence,'d27-after')
        saved,sr=transport.call(OUTPUT,'new-d27-save','ck3_save_checkpoint',{'expected_revision':pv['revision']},120)
        require(saved.get('checkpoint',{}).get('date_raw')==53146872,'Saved after date changed')
        immutable=preserved_save(saved,'d27',evidence)
        write(evidence/'after-pair.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'one_day':adr,'trace_finish':er,
                   'trace_finish_body':ended,'trace_error':trace_error,'snapshot':psr,'values':pv,'control':cr,
                   'image':image,'save':sr,'immutable':immutable,'episode_run_id':saved['checkpoint']['episode_run_id'],
                   'target_status':'pending strict saved-state reader','film_clean_span':False})
        print(json.dumps({'result':'AFTER_SAVED_PENDING_STRICT_READER','values':pv,'trace_error':trace_error},ensure_ascii=False))
    else:
        target=OUTPUT/'interactive-requests/root-finish.json'
        pending=target.with_suffix('.json.pending')
        require(not target.exists() and not pending.exists(),'Finish already submitted')
        write(pending,{'action':'finish'})
        os.rename(pending,target)
        print(json.dumps({'finish_submitted':str(target),'cleanup_pending':True}))
if __name__=='__main__':
    main()
