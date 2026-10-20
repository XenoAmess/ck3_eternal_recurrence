"""Metadata-only scene component measurement. Fixed hardcaps; no SDK or screen."""
from packet_1615_common import *
sys.path.insert(0,'C:/ck3-e04-resume-20261020-a01/capacity')
from monitor_r220_components import allocated

def measure(cap):
    scene=Path(cap['scene_root']).resolve()
    assert scene==S.resolve()
    roots={k:[Path(x).resolve() for x in [cap['component_roots'][k],*cap.get('component_additional_roots',{}).get(k,[])]] for k in ['profile','driver']}
    roots['raw']=[scene/'raw-a01']
    groups={k:{'logical_bytes':0,'allocated_unique_bytes':0,'files':0,'ceiling_bytes':cap['component_ceiling_bytes'][k]} for k in ['profile','driver','raw','other']}
    seen=set();errors=[];stack=[scene];start=time.monotonic();count=0
    while stack:
        directory=stack.pop()
        try:
            with os.scandir(directory) as entries:
                for e in entries:
                    count+=1
                    assert count<100000 and time.monotonic()-start<120
                    path=Path(e.path)
                    try:
                        st=path.stat(follow_symlinks=False)
                        assert not getattr(st,'st_file_attributes',0)&0x400,'Reparse entry not admitted'
                        if e.is_dir(follow_symlinks=False):stack.append(path);continue
                        assert e.is_file(follow_symlinks=False) and st.st_ino!=0
                        key=next((k for k,rr in roots.items() if any(path.is_relative_to(r) for r in rr)),'other')
                        group=groups[key];group['logical_bytes']+=st.st_size;group['files']+=1
                        identity=(st.st_dev,st.st_ino)
                        if identity not in seen:
                            size,error=allocated(path)
                            assert size is not None and error is None,repr(error)
                            group['allocated_unique_bytes']+=size;seen.add(identity)
                    except (OSError,AssertionError) as ex:errors.append({'path':str(path),'error':repr(ex)})
        except (OSError,AssertionError) as ex:
            errors.append({'path':str(directory),'error':repr(ex)})
            if count>=100000 or time.monotonic()-start>=120:break
    return {'machine_id':M,'observed_at_utc':now(),'scene_root':str(scene),'components':groups,
        'metadata_coverage_complete':not errors,'errors':errors[:20],'errors_count':len(errors),
        'elapsed_seconds':round(time.monotonic()-start,3),'logical_total_bytes':sum(x['logical_bytes'] for x in groups.values()),
        'allocated_unique_total_bytes':sum(x['allocated_unique_bytes'] for x in groups.values()),
        'live_measurement_not_atomic_snapshot':True,'payload_body_bytes_read':0,'SDK_game_screen_actions':0}
