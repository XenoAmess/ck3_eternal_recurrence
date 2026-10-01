from pathlib import Path
import json
ROOT=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02/research-pair-attempt-02')
data=json.loads((ROOT/'after-pair.json').read_text(encoding='utf-8'))
body=data.get('trace_finish_body')
print(json.dumps({'trace_error':data.get('trace_error'),'top_keys':list(body or {}),'values':data['values']},ensure_ascii=False))
def walk(v,path='root'):
    if isinstance(v,dict):
        if 'records' in v and isinstance(v['records'],list):
            print(json.dumps({'path':path,'scalar_fields':{k:x for k,x in v.items() if isinstance(x,(bool,str,int,float)) or x is None},
                              'record_count':len(v['records']),
                              'record_summaries':[{k:x for k,x in r.items() if isinstance(x,(bool,str,int,float)) or x is None} for r in v['records']]},ensure_ascii=False))
        for k,x in v.items():walk(x,path+'.'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):walk(x,path+'.'+str(i))
walk(body)
