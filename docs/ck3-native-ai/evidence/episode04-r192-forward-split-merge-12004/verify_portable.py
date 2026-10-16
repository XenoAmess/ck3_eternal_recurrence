"""Portable byte/contract verification; optional exact-source production replay."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,zipfile
def need(v,s):
    if not v:raise RuntimeError(s)
def module(p,n):
    spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def wire(value):
    return json.loads(json.dumps(value,ensure_ascii=False))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--repo',type=Path);a=p.parse_args()
    with zipfile.ZipFile(a.archive) as z:
        manifest=json.loads(z.read('MANIFEST.json'))
        need(set(z.namelist())=={'MANIFEST.json',*manifest['members']},'Archive member set changed')
        data={}
        for name,pin in manifest['members'].items():
            b=z.read(name);need(len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256'],'Archive exact bytes changed '+name);data[name]=b
    split=json.loads(data['analysis/SPLIT-ANALYSIS.actual.json']);merge=json.loads(data['analysis/MERGE-ANALYSIS.actual.json'])
    f0=json.loads(data['original/F0-baseline.actual.json'])['packet'];f1=json.loads(data['original/F1-post-split-observation.actual.json'])['packet'];f2=json.loads(data['analysis/POSTMERGE-PACKET.actual.json'])['packet']
    need(split['split_assertion_recomputed']['accepted'] is True and split['strict_unrelated_gate_pass'] is False,'Original strict split RED changed')
    need(merge['merge_DATA_roles']['accepted'] is True and merge['global_physical_identity_keysets_equal'] is True,'Recorded physical qualification differs')
    need([v['current_max'] for v in merge['global_physical_and_cached_F0_F1_F2']]==[[1935,1935]]*3,'Physical totals changed')
    need([v['cached_current_max'] for v in merge['global_physical_and_cached_F0_F1_F2']]==[[1945,1945],[1944,1944],[1945,1945]],'Cache totals changed')
    need(merge['R09_full_card_closed'] is False and merge['merge_was_outside_original_film'] is True,'Card/media limitation changed')
    replay=False
    if a.repo:
        for rel,pin in manifest['production_sources'].items():
            b=(a.repo/rel).read_bytes();need(hashlib.sha256(b).hexdigest()==pin['sha256'],'Exact production source differs '+rel)
        root=a.repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge'
        relay=module(root/'root_relay.py','portable_r192_relay_pure');c=module(root/'army_split_transfer_assertions_12004.py','portable_r192_consumer')
        expected=c.assert_fresh_split_transfer_12004(f0['frame'],f1['frame'],source_army_id=93,pre_strengths=f0['query'],post_strengths=f1['query'],pre_commander=f0['commanders']['93'],post_commanders={int(k):v for k,v in f1['commanders'].items()})
        need(wire(expected)==split['split_assertion_recomputed'],'Production split replay differs')
        old={r['army_id']:r for r in f1['query']['army_strengths']};new={r['army_id']:r for r in f2['query']['army_strengths']}
        need(wire(relay.compare_data_roles(c,[old[93],old[16777378]],[new[93]]))==merge['merge_DATA_roles'],'Production merge DATA/role replay differs')
        need(wire(relay.compare_merge_supply(f1,f2,[93,16777378]))==merge['merge_supply'],'Production merge stock replay differs')
        replay=True
    print(json.dumps({'status':'PORTABLE_EXACT_SMALL_ORIGINALS_AND_RECORDED_QUALIFICATIONS_VERIFIED','members':len(data),'production_replayed':replay,'big_raw_or_save_or_video_body_reads':0,'SDK_calls':0,'R09_full_card_closed':False}))
if __name__=='__main__':main()
