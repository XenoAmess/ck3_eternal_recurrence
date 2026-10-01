from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
import knight_research_pair_a02 as pair
EVIDENCE=pair.NEW/'research-pair-attempt-02'
image=pair.identity(EVIDENCE/'d26-before-window.png')
row={'at_utc':datetime.now(timezone.utc).isoformat(),'reviewer':'root direct inspection of exact original WGC frame',
     'image':image,'actual_paused_d26_ui_observed':True,'actual_ui_date':'1066.12.29','source_day_index':26,
     'observation':'Original HUD visibly shows 暂停 and 公元1066年12月29日; map/battle badge present.',
     'character_UI_observed':False,'full_battle_panel_observed':False,'scope':'research native day/selector/final-lifecycle verification',
     'human_video_signoff':False,'film_clean_span':False}
pair.write(EVIDENCE/'d26-window-visual-review.json',row)
args=[sys.executable,'-X','utf8',str(Path(__file__).with_name('knight_research_pair_a02.py')),'--mode','advance']
with (Path(__file__).parent/'research-advance-stdout.txt').open('x',encoding='utf-8') as out, \
     (Path(__file__).parent/'research-advance-stderr.txt').open('x',encoding='utf-8') as err:
    result=subprocess.run(args,stdout=out,stderr=err)
pair.write(Path(__file__).parent/'research-advance-process.json',{'argv':args,'returncode':result.returncode,
      'stdout':pair.identity(Path(__file__).parent/'research-advance-stdout.txt'),
      'stderr':pair.identity(Path(__file__).parent/'research-advance-stderr.txt')})
print((Path(__file__).parent/'research-advance-stdout.txt').read_text(encoding='utf-8'))
print((Path(__file__).parent/'research-advance-stderr.txt').read_text(encoding='utf-8'))
raise SystemExit(result.returncode)
