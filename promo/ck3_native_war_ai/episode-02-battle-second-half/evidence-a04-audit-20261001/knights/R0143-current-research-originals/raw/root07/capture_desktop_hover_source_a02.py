"""Capture actual desktop and a measured review preview; no input or game mutation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import importlib.util
import pyautogui
import win32gui
import win32process

ROOT=Path(__file__).resolve().parent
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not (args.label and all(c.isalnum() or c in '-_' for c in args.label)):raise RuntimeError('Invalid exclusive label')
    spec=importlib.util.spec_from_file_location('_hover_source',ROOT/'scoped_ui_research_a09.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    cfg=m.read(ROOT/'current-run-bindings.json')
    live,output,evidence,transport,steps=m.bind(cfg)
    date=cfg['before_date_raw'] if not (evidence/'one-day-finished.json').exists() else cfg['after_date_raw']
    snap,sr,values=m.snapshot(output,transport,steps,args.label+'-desktop-source',date)
    hwnd=win32gui.GetForegroundWindow();pid=win32process.GetWindowThreadProcessId(hwnd)[1]
    m.require(pid==cfg['native_session_binding']['bridge_pid'],'Foreground is not current admitted game')
    size=list(pyautogui.size());image=pyautogui.screenshot();m.require(list(image.size)==size,'Desktop dimensions changed')
    dst=evidence/(args.label+'-desktop-original.png');m.require(not dst.exists(),'Original image exists');image.save(dst)
    preview=image.copy();preview.thumbnail((1280,1280))
    view=evidence/(args.label+'-review-preview.png');m.require(not view.exists(),'Preview exists');preview.save(view)
    post,pr,pv=m.snapshot(output,transport,steps,args.label+'-desktop-post',date);m.require(values==pv,'Paused native source changed around pixels')
    record={'at_utc':datetime.now(timezone.utc).isoformat(),'current_paused_source':values,'snapshot':sr,'post_snapshot':pr,
        'foreground_hwnd':hwnd,'foreground_pid':pid,'desktop_size':size,'original_image_size':list(image.size),
        'original':ident(dst),'review_preview':ident(view),'preview_image_content_rect':{'left':0,'top':0,'width':preview.width,'height':preview.height},
        'preview_purpose':'Measured readonly inspection aid; original remains the capture evidence and coordinate source',
        'input_mouse_keyboard':False,'original_pixels_actually_reviewed':False}
    path=evidence/(args.label+'-desktop-source.json');m.write(path,record)
    print(json.dumps({'receipt':ident(path),'original':ident(dst),'review_preview':ident(view),'rect':record['preview_image_content_rect'],'foreground_hwnd':hwnd}))
if __name__=='__main__':main()
