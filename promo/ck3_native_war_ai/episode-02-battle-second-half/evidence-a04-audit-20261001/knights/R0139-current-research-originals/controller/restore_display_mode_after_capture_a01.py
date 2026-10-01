from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,time,psutil,win32api,win32con,pyautogui
from PIL import ImageGrab
parser=argparse.ArgumentParser();parser.add_argument('--screen-task-id',required=True);parser.add_argument('--expected-sequence',type=int,required=True);args=parser.parse_args()
r=Path(__file__).resolve().parent;out=r/'display-restore-original-a01';out.mkdir(exist_ok=False)
def now():return datetime.now(timezone.utc).isoformat()
def fields(m):return {k:getattr(m,k) for k in ['PelsWidth','PelsHeight','BitsPerPel','DisplayFrequency','DisplayOrientation','Position_x','Position_y','DisplayFlags']}
def write(name,value):
    with (out/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
owners=[]
for p in Path('D:/workspace/.codex-task-bus/tasks').glob('*.json'):
    row=json.loads(p.read_text(encoding='utf-8'))
    if 'ck3-screen:acquired' in row.get('resources',[]):owners.append(row)
assert len(owners)==1 and owners[0]['task_id']==args.screen_task_id and owners[0]['last_sequence']==args.expected_sequence
age=(datetime.now(timezone.utc)-datetime.fromisoformat(owners[0]['updated_at_utc'])).total_seconds();assert 0<=age<=600
busy=[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower() in ('ck3.exe','ffmpeg.exe','obs64.exe')];assert not busy
original=json.loads((r.parent/'root-attempt-01/display-align-2560-a01/preflight.json').read_text(encoding='utf-8'))
device=original['device'];current=win32api.EnumDisplaySettings(device,win32con.ENUM_CURRENT_SETTINGS)
assert (current.PelsWidth,current.PelsHeight,current.BitsPerPel,current.DisplayFrequency)==(2560,1440,32,60) and list(pyautogui.size())==[2560,1440]
target=None
for i in range(1000):
    try:m=win32api.EnumDisplaySettings(device,i)
    except Exception:break
    if (m.PelsWidth,m.PelsHeight,m.BitsPerPel,m.DisplayFrequency,m.DisplayOrientation,m.Position_x,m.Position_y)==(1024,768,32,60,0,0,0):target=m;break
assert target is not None
write('preflight.json',{'at':now(),'screen_owner':owners[0],'busy_inventory':busy,'original_alignment_receipt_sha256':hashlib.sha256((r.parent/'root-attempt-01/display-align-2560-a01/preflight.json').read_bytes()).hexdigest().upper(),'before_mode':fields(current),'restore_target':fields(target),'registry_update_requested':False})
test=win32api.ChangeDisplaySettingsEx(device,target,win32con.CDS_TEST);write('test.json',{'at':now(),'return_code':test});assert test==0
result=win32api.ChangeDisplaySettingsEx(device,target,0);write('apply.json',{'at':now(),'return_code':result,'registry_update_requested':False});assert result==0
time.sleep(3);actual=win32api.EnumDisplaySettings(device,win32con.ENUM_CURRENT_SETTINGS);size=list(pyautogui.size());im=ImageGrab.grab(all_screens=False);p=out/'original-desktop-after-restore.png';im.save(p)
verified=(actual.PelsWidth,actual.PelsHeight,actual.BitsPerPel,actual.DisplayFrequency)==(1024,768,32,60) and size==list(im.size)==[1024,768]
receipt={'at':now(),'actual_mode':fields(actual),'desktop_size':size,'original_image_size':list(im.size),'verified':verified,'screenshot':{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()},'steam_online_switch':False,'input_mouse_or_keyboard':False}
write('readback.json',receipt);print(json.dumps(receipt));assert verified
