from pathlib import Path
import json,hashlib,collections,sys
BASE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
PAIR=LIVE/'scoped-ui-research-attempt-01'
OUT=BASE/'R0142-four-save-endpoint-audit-reinforcement-a01'
def ident(p):
 p=Path(p).resolve();b=p.read_bytes();return{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ident(p)
def main():
 OUT.mkdir(exist_ok=False);sys.stdout.reconfigure(encoding='utf-8')
 parsed=LIVE/'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json'
 raw=read(parsed);body=raw['body'];mon=body['scoped_variable_monitor'];rows=mon['records']
 inspect={'monitor_original':ident(parsed),'result':raw['result'],'accepted':body['accepted'],'status':body['status'],'schema':mon['schema_version'],'failure_flags':mon['failure_flags'],'truncated':mon['truncated'],'detours_uninstalled':mon['detours_uninstalled'],'record_count':len(rows),'boundary_counts':dict(collections.Counter(r['boundary']for r in rows)),'thread_counts':dict(collections.Counter(r['thread_id']for r in rows)),'date_counts':dict(collections.Counter(r['date_raw']for r in rows)),'character_counts':dict(collections.Counter(r['character_id']for r in rows)),'first':rows[0],'last':rows[-1],'partial_actual_write_records':[r for r in rows if r['boundary'].startswith('variable_write')],'partial_house_records':[r for r in rows if r['boundary'].startswith('house_predicate')],'strict_monitor_verifier_applicable':False,'reason':'Original accepted=false/statusfailed/flags8/truncatedtrue; no complete-monitor inference.'}
 ids=save(OUT/'monitor-original-schema-inspection.json',inspect)
 shapes=[]
 for label in ['before-pre-ui-checkpoint','before','after-pre-ui-checkpoint','after']:
  p=PAIR/(label+'-saved-pair.json');pair=read(p);snapshot=read(pair['snapshot']['response']['path']);receipt=read(pair['save']['response']['path'])
  shapes.append({'label':label,'pair':ident(p),'keys':list(pair),'source_values':pair['source_values'],'snapshot_body_keys':list(snapshot['body']),'snapshot_driver_state':snapshot.get('driver_state'),'save_driver_state':receipt.get('driver_state')})
 save(OUT/'four-pair-input-shapes.json',shapes)
 print(json.dumps({'monitor':ids,'shape_receipt':ident(OUT/'four-pair-input-shapes.json'),'actual_partial_monitor_counts':inspect['boundary_counts']},ensure_ascii=False))
if __name__=='__main__':main()
