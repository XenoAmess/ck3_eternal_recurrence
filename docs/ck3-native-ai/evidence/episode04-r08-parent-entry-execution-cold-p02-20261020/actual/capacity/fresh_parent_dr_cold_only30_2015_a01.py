"""Cold-only phase guard; completed source/build/SYSTEM permissions remain closed."""
import argparse,sys,os,json
from pathlib import Path
from datetime import datetime
sys.path.insert(0,'C:/ck3-e04-resume-20261020-a01/r08-1615-a01/capacity')
from packet_1615_common import pin,exact,snapshot,balances,volumes,budget,now,put,M
S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p02').resolve()
B=Path('C:/w/e04parentdr02').resolve();BC=B/'build-a01';BOOT=B/'capacity';CTRL=B/'control-metadata-a01'
def measure(root):
    rows=[];stack=[root] if root.exists() else []
    while stack:
        with os.scandir(stack.pop()) as es:
            for e in es:
                st=e.stat(follow_symlinks=False);assert not getattr(st,'st_file_attributes',0)&0x400
                if e.is_dir(follow_symlinks=False):stack.append(Path(e.path))
                else:
                    assert e.is_file(follow_symlinks=False)
                    rows.append({'path':str(Path(e.path).resolve()),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'dev':st.st_dev,'ino':st.st_ino})
                assert len(rows)<100000
    return rows
def same(ref):
    got=pin(ref['path']);assert got['bytes']==ref['bytes'] and got['sha256']==ref['sha256']
    return got
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cap',required=True);ap.add_argument('--cap-sha256',required=True);ap.add_argument('--phase',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    cp=pin(a.cap);assert cp['sha256']==a.cap_sha256;c=exact(cp)
    assert c['machine_id']==M and c['admitted'] is True and c['budget_status']=='GREEN'
    assert Path(cp['path']).is_relative_to(BOOT),'Future actual admission must be in new admitted bootstrap, never expired N'
    assert c['aggregate_ceiling_bytes']==67108864
    assert c['component_ceiling_bytes']=={'source':2097152,'build':31457280,'protocol':33554432}
    assert Path(c['component_roots']['source']).resolve()==S and Path(c['component_roots']['build']).resolve()==B
    assert Path(c['build_root']).resolve()==BC,'True producer root is new build child, aggregate build remains top'
    assert a.phase=='cold-selected-suite' and set(c['allowed_phase_argv'])=={'cold-selected-suite'}
    assert c['stage_financial_future_bytes']==31457280
    assert not c.get('source_freeze_execution_admitted') and not c.get('build_execution_admitted') and not c.get('SYSTEM_registration_execution_admitted')
    same(c['stage_closure_census']);same(c['stage_financial_transition'])
    base=['source-copy','MSVC-build-and-ordinary-SYSTEM','exact-SYSTEM-receipt']
    if a.phase in base and a.phase!='source-copy':assert c.get('build_execution_admitted') is True
    if a.phase=='MSVC-build-and-ordinary-SYSTEM':assert c.get('SYSTEM_registration_execution_admitted') is True
    if a.phase not in base:
        assert c.get('EXE_execution_admitted') is True and c.get('cold_execution_admitted') is True
        assert c.get('selected_project_EXEs') and c.get('Root_actual_SYSTEM_review')
        for ref in c['selected_project_EXEs']:same(ref)
        same(c['Root_actual_SYSTEM_review'])
    plan=exact(c['producer_plan']);same(plan['installed_policy'])
    assert plan['entry_dependencies'] and plan['source_copy']
    for ref in plan['entry_dependencies']:same(ref)
    for ref in plan['source_copy']:same(ref)
    source_rows=measure(S);build_rows=measure(B)
    source_bytes=sum(x['bytes'] for x in source_rows);build_bytes=sum(x['bytes'] for x in build_rows)
    assert source_bytes<=2097152 and build_bytes<=31457280
    if a.phase=='source-copy':
        assert not S.exists() and not BC.exists(),'Both new frozen-source and true CMake build child must be absent'
        assert c['source_freeze_execution_admitted'] is True
        assert c['bootstrap_metadata_total_ceiling_bytes']==262144
        limits=c['bootstrap_subroots']
        assert Path(limits['capacity']['root']).resolve()==BOOT and limits['capacity']['ceiling_bytes']==65536
        assert Path(limits['control_metadata']['root']).resolve()==CTRL and limits['control_metadata']['ceiling_bytes']==196608
        assert all(Path(x['path']).is_relative_to(BOOT) or Path(x['path']).is_relative_to(CTRL) for x in build_rows),'Top root before sourcecopy contains only exact capacity/control metadata bootstrap'
        assert build_bytes<=262144
        assert sum(x['bytes'] for x in build_rows if Path(x['path']).is_relative_to(BOOT))<=65536
        assert sum(x['bytes'] for x in build_rows if Path(x['path']).is_relative_to(CTRL))<=196608
        expected={str(Path(ref['path']).resolve()):same(ref) for ref in c['bootstrap_files']}
        expected[cp['path']]=cp
        assert set(x['path'] for x in build_rows)==set(expected),'Only admitted exact bootstrap leaves'
        for ref in expected.values():same(ref)
        for directory,dirs,_ in os.walk(B):
            for name in dirs:
                p=Path(directory)/name
                assert p==BOOT or p==CTRL or p.is_relative_to(BOOT) or p.is_relative_to(CTRL),'No unadmitted top-level directory or old build payload'
    else:assert S.is_dir(),'Later phases require genuine frozen source'
    l,ident,lp=snapshot();active=balances(l);claim=next(x for x in l['claims'] if x['task_id']==c['task_id'])
    assert claim['state']=='active' and claim['reserved_future_bytes_by_volume']=={'C:/':31457280,'D:/':0} and claim.get('phase')=='cold-only-source-build-SYSTEM-closed'
    t=datetime.fromisoformat(now());deadline=datetime.fromisoformat(c['hard_deadline_utc'].replace('Z','+00:00'))
    assert datetime.fromisoformat('2026-10-20T19:20:00+00:00')<=t<deadline<=datetime.fromisoformat('2026-10-20T20:15:00+00:00')
    v=volumes();b=budget(v,active);assert min(b[k] for k in ('C_quota_margin_bytes','C_floor_margin_bytes','D_floor_margin_bytes'))>=0
    result={'schema':'xar.e04.parent-dr-native64-2015-phase-fresh.v1','machine_id':M,'observed_at_utc':now(),'capacity':cp,'phase':a.phase,'admitted':True,'budget_status':'GREEN','aggregate_source_root':str(S),'aggregate_build_root':str(B),'true_producer_build_child':str(BC),'source_complete_logical_bytes':source_bytes,'build_complete_logical_bytes':build_bytes,'metadata_scans_complete':True,'historical_protocol_absolute_ceiling_bytes':33554432,'new_protocol_future_bytes':0,'cold_top_future_bytes':31457280,'protected_private_enumeration_not_claimed':True,'ledger':lp,'all_active_claims':active,'fresh_volumes':v,'budget':b,'observation_not_continuous_peak_proof':True}
    if a.output=='-':
        result['precheck_storage']='Original stdout memory; later persistence is explicitly post-observation, not an earlier durable intent'
        print(json.dumps(result));return
    out=Path(a.output).resolve();assert out.is_relative_to(B) and out.parent.is_dir() and not out.exists()
    assert a.phase!='source-copy','First fresh stays stdout memory; preserve exact bootstrap leaves until source-freezer wait'
    print(json.dumps({'receipt':put(out,result),'budget':b}))
if __name__=='__main__':main()
