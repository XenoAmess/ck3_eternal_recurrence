from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'current-run-bindings.json').read_text(encoding='utf-8'))
live=Path(cfg['live_root'])
evidence=live/'scoped-ui-research-attempt-01'
day=json.loads((evidence/'one-day-finished.json').read_text(encoding='utf-8'))
result={'day_values':day['post_day_values'],'trace_error':day.get('trace_error'),'trace_body_present':day['trace_finish_body'] is not None}
if day['trace_finish_body'] is not None:
    body=day['trace_finish_body'];result['trace_accepted']=body.get('accepted');result['trace_keys']=list(body)
    managed=body.get('managed_trace',{})
    result['trace_checkpoint']=managed.get('managed_checkpoint')
    result['trace_summary']={k:v for k,v in managed.get('trace',{}).items() if not isinstance(v,(dict,list))}
monitor=json.loads((evidence/'variable-monitor-finish.json').read_text(encoding='utf-8'))
p=monitor['scoped_variable_monitor']
result['monitor']={'accepted':monitor['native_envelope'].get('accepted'),'status':monitor['native_envelope'].get('status'),'failure_flags':p['failure_flags'],'truncated':p['truncated'],'uninstalled':p['detours_uninstalled'],'record_count':len(p['records']),'records':[{'sequence':r['sequence'],'boundary':r['boundary'],'character_id':r.get('character_id'),'flags':r.get('failure_flags'),'read':r.get('value',{}).get('read'),'dead':r.get('dead')} for r in p['records']]}
result['original_parsed_diagnostics']=[]
for path in live.rglob('native-trace-*.json'):
    frame=json.loads(path.read_text(encoding='utf-8'))['original_parsed_command_result']
    if 'trace_publish_diagnostic' in frame:
        result['original_parsed_diagnostics'].append({'path':str(path),'diagnostic':frame['trace_publish_diagnostic']})
print(json.dumps(result))
