from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'root-attempt-01'
task=json.loads(Path('D:/workspace/.codex-task-bus/tasks/war-e2-six-gap-screen-20261001-a01.json').read_text(encoding='utf-8'))
if task['resources']!=['ck3-screen:acquired']:raise RuntimeError('Missing screen lease')
for name in ['prepare_ui_capture_a01.py','run_ui_sdk_a01.py','capture_steam_library_change_a01.py']:
    text=(OLD/name).read_text(encoding='utf-8')
    text=text.replace('six-gap-ui-live-20261001-a01','six-gap-ui-live-20261001-a02').replace('six-gap-ui-preflight-20261001-a01','six-gap-ui-preflight-20261001-a02')
    text=text.replace("'3355'",repr(str(task['last_sequence'])))
    text=text.replace('ck3-six-gap-ui-20261001-a01','ck3-six-gap-ui-20261001-a02').replace('six-gap-ui-20261001-a01-root','six-gap-ui-20261001-a02-root')
    if name=='capture_steam_library_change_a01.py':text=text.replace('steam://nav/games/details/1158310','steam://nav/games/details/1086940')
    if name=='prepare_ui_capture_a01.py':
        text=text.replace('Current CK3 library body states','Current BG3 library body states').replace('changed BG3 library to CK3','changed CK3 library to BG3')
        text=text.replace("'steam://nav/games/details/1158310'","'steam://nav/games/details/1086940'")
        text=text.replace("ROOT/'offline-recovery-a01/probe-1/steam-moved.png'","ROOT.parent/'root-attempt-01/wgc-steam-library-change-a01/frame-03.png'")
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('Prepared new retry helpers; previous failed attempt preserved.')
