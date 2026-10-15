from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent

def need(ok,why):
    if not ok: raise ValueError(why)

def load_source_delta(episode_root=None):
    # No SDK/native imports, external dynamic source, provider or writes.
    episode=Path(episode_root).resolve() if episode_root else HERE.parents[1]
    data=json.loads((HERE/'claim-shot-agent-map.json').read_text(encoding='utf-8'))
    sources=json.loads((HERE/'source-index.json').read_text(encoding='utf-8'))
    original=episode/'production/final-BC-a06/narration/six-chapter-final-BC-Chinese-a06.md'
    raw=original.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==data['metadata']['original69_model']['sha256'],'canonical69 SHA differs')
    ids=set(re.findall(r'^\[(C\d\d-\d\d)\] ',raw.decode('utf-8-sig'),flags=re.MULTILINE))
    need(len(ids)==69,'existing69 model differs')
    prior_path=episode/'review02/story-a02/claim-shot-agent-map.json'
    prior_raw=prior_path.read_bytes()
    need(hashlib.sha256(prior_raw).hexdigest()==data['metadata']['frozen_a02_map']['sha256'],'frozen a02 SHA differs')
    prior=json.loads(prior_raw)
    covered={row['paragraph_id'] for row in prior['paragraphs']}
    selected=[row['paragraph_id'] for row in data['paragraphs']]
    need(len(selected)==len(set(selected))==13,'delta13 ID set differs')
    need(set(selected)<=ids and not set(selected)&covered,'not original uncovered paragraphs')
    need(data['metadata']['research_credit_added']==0 and data['metadata']['winner'] is None,'credit/winner invented')
    for row in data['paragraphs']:
        need(row['actual_shot_ids']==[] and not row['tts_generated'],'source-only row promoted')
        need(all(sid in sources['source_ids'] for sid in row['source_ids']),'source ID absent')
    for c in data['demonstration_cards']:
        need(c['actual_footage'] is None and not c['live_positive_claim_allowed'],'card promoted to live')
    return data,sources

def claims_by_source_id(source_id,episode_root=None):
    data,sources=load_source_delta(episode_root)
    need(source_id in sources['source_ids'],'unknown source ID')
    return {'source':sources['source_ids'][source_id],
            'paragraphs':[r for r in data['paragraphs'] if source_id in r['source_ids']],
            'cards':[c for c in data['demonstration_cards'] if source_id in c['source_ids']]}

def check_arithmetic_examples():
    # Exact small, nonnegative, no-overflow hypothetical examples only.
    need(199*5000//100000==9 and 199*1000//100000==1 and 199*6000//100000==11,'separate integer budgets')
    F=5000*33339//100000
    need(F==1666 and 3001*F//100000==49 and 100*33339//100000==33,'layered county terms')
    need(3001*5000*33339//100000**2==50,'flattened contrast')
    need([19*5000//100000,20*5000//100000]==[0,1],'small eligible integer budgets')
    need(100-min(100,120)==0 and 100-min(100,40)==60,'saved residual')
    need(5900+50+50==6000 and max(0,0-100000)==0,'aggregate/floor illustrative arithmetic')
    return 'six bounded arithmetic checks PASS; no CK3 simulation or observed result'

def main():
    parser=argparse.ArgumentParser(description='Read-only source delta for existing Episode04 paragraph model.')
    parser.add_argument('--episode-root',type=Path)
    parser.add_argument('--source-id')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.source_id:
        out=claims_by_source_id(args.source_id,args.episode_root)
    else:
        data,sources=load_source_delta(args.episode_root)
        out={'paragraphs':len(data['paragraphs']),'cards':len(data['demonstration_cards']),'source_ids':list(sources['source_ids']),
             'status':'PASS','research_credit_added':0,'live_positive':False,'arithmetic':check_arithmetic_examples()}
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
