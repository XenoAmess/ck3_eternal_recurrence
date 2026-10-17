"""Verify only the small R194 normal-close append; never reopen the business ZIP."""
from pathlib import Path
import argparse,hashlib,json,zipfile
def need(v,s):
 if not v:raise ValueError(s)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);a=p.parse_args();need(a.archive.stat().st_size<=64*1024,'Small close append only')
 with zipfile.ZipFile(a.archive) as z:
  m=json.loads(z.read('MANIFEST.json'));need(set(z.namelist())=={'MANIFEST.json',*m['members']},'Exact close append members');d={}
  for name,pin in m['members'].items():
   b=z.read(name);need(len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256'],'Exact original changed '+name);d[name]=json.loads(b)
 s=d['NORMAL-SAVE.actual.json'];b=d['BOOTSTRAP-OBSERVED.actual.json'];r=d['SCREEN-RELEASE.actual.json'];summary=d['CLOSE-SUMMARY.actual.json']
 need(all(v['machine_id']==m['machine_id'] and v['run_id']==m['run_id'] for v in (s,b,r)),'Close actual run binding')
 need(s['source_head']==m['source_head'] and s['pid']==30444 and s['actor_id']==31254 and s['date_raw']==53146632,'Actual normal save identity')
 need(s['checkpoint']['bytes']==71305582 and s['checkpoint']['sha256']=='d2fcb1237dda1ac0a6e0639738e2098a744e68ff9edd92fe084f22fd322be74d','Actual new terminal checkpoint reference')
 need(s['checkpoint']['sha256']!=summary['preserved_common_S0_sha256'],'New terminal checkpoint must not replace common S0')
 need(b['normal_exit_zero'] is True and b['session_exit_reason']=='process_exit' and r['normal_exit_zero'] is True and r['game_exit_code']==0 and r['exit_code']==0 and r['task_done_resources_empty'] is True,'Actual exit0/resource release')
 need(r['normal_save']['sha256']==m['members']['NORMAL-SAVE.actual.json']['sha256'] and r['bootstrap_observation']['sha256']==m['members']['BOOTSTRAP-OBSERVED.actual.json']['sha256'],'Close exact provenance links')
 need(s['recording_scope']['status']=='NORMAL_TREE_EMPTY' and s['recording_scope']['film_result']==summary['business_controller_result'],'Actual recorder and prior business result link')
 need(summary['media_payload_not_read_or_qualified'] is True and summary['dynamic_completed']==0 and summary['ABC_completed']==0 and summary['business_card_count_decision_pending'] is True,'No invented media/count qualification')
 print(json.dumps({'status':'R194_SMALL_NORMAL_CLOSE_APPEND_PASS','normal_exit0':True,'screen_resources_empty':True,'preserved_common_S0_not_replaced':True,'business_archive_reopened':False,'full_Driver_save_video_reads':0,'SDK_game_actions':0,'counter_or_dynamic_signoff_changed':False}))
if __name__=='__main__':main()
