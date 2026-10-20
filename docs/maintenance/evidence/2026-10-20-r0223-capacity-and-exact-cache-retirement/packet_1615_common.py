"""Current16:15 purpose; old packet sources remain immutable read-only inputs."""
import sys
from pathlib import Path
sys.path.insert(0,'C:/ck3-e04-resume-20261020-a01/r06-resume-a02/capacity')
from capacity_common import *
OLDROOT=ROOT
ROOT=Path('C:/ck3-e04-resume-20261020-a01/r08-1615-a01')
B=ROOT/'capacity'
S=ROOT.parent/'r08-scene-a02'
T='e04-capacity-r08-1615-20261020-a01'
DEADLINE='2026-10-20T16:15:00Z'

def shared_measure(excludes=()):
    started=time.monotonic();stack=[ROOT];total=files=0
    assert not excludes
    while stack:
        directory=stack.pop()
        with os.scandir(directory) as entries:
            for e in entries:
                p=Path(e.path);s=p.stat(follow_symlinks=False)
                assert not getattr(s,'st_file_attributes',0)&0x400,'Shared reparse requires review'
                if e.is_dir(follow_symlinks=False):stack.append(p)
                else:
                    assert e.is_file(follow_symlinks=False);total+=s.st_size;files+=1
                assert files<100000 and time.monotonic()-started<60
    assert total<=16*Mi,'New M2 shared16MiB exceeded'
    return {'machine_id':M,'observed_at_utc':now(),'aggregate_root':str(ROOT),'excludes':[],'logical_bytes':total,'files':files,'ceiling_bytes':16*Mi,'payload_body_bytes_read':0,'metadata_scan_complete':True}
