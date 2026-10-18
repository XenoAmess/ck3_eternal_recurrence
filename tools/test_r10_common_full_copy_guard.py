"""One production guard branch compound; no SDK or payload fixtures."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
import argparse, importlib.util, json, sys, tempfile

MIB=1024*1024
class OwnedFile:
 def is_file(self):return True
 def resolve(self):return 'same-owned-file'
 def stat(self):return SimpleNamespace(st_size=self.bytes)
class OwnedRoot:
 def __init__(self,file):self.file=file
 def exists(self):return True
 def rglob(self,pattern):return [self.file]
class OriginalClient:
 def __init__(self):self.calls=[]
 def guard(self,*,reserve):self.calls.append(reserve)
 def remaining(self):return 7200

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-repo',type=Path,required=True);p.add_argument('--stage-root',type=Path)
 a=p.parse_args();repo=a.source_repo.resolve();root=(a.stage_root or repo).resolve()
 sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
 name='ck3_mod_acceptance_cases.r10_common_arm_guard_subject'
 spec=importlib.util.spec_from_file_location(name,root/'tools/ck3_mod_acceptance_cases/r10_common_arm.py')
 mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
 io=mod.CommonArmIO.__new__(mod.CommonArmIO)
 io.deadline=datetime.now(timezone.utc)+timedelta(hours=1)
 io.capacity={'admitted':True};io.capacity_ref={'opaque':'original-cap-ref'}
 io.client=OriginalClient();file=OwnedFile();file.bytes=100*MIB
 # Both owned roots intentionally expose the same file. Original identity-based
 # deduplication remains active, so this is 100 MiB, not 200 MiB.
 io.run=OwnedRoot(file);io.native_session=OwnedRoot(file)
 io.packet_limit=16*MIB;io.runtime_total_budget_bytes=192*MIB
 with patch.object(mod,'small_json',return_value=io.capacity):
  try:io.guard()
  except ValueError as e:
   assert 'original wire, three full results' in str(e)
  else:raise AssertionError('Old 48MiB accounting admits 100+48<=192; real 96MiB copy reserve must reject 100+96>192')
  file.bytes=96*MIB;io.guard()  # exact capacity boundary, including dedup
  io.packet_limit=32*MIB;file.bytes=48*MIB;io.guard() # 48+144==192
  file.bytes=48*MIB+1
  try:io.guard()
  except ValueError as e:assert 'original wire, three full results' in str(e)
  else:raise AssertionError('32MiB admitted packet must also reserve actual32MiB wire and three32MiB bodies')
 assert io.client.calls==[180]*4
 print(json.dumps({'test':'test_real_full_copy_guard_rejects_old_underestimate_preserves_boundary_and_dedup','passed':1,
  'packet16_reserve_bytes':96*MIB,'packet32_reserve_bytes':144*MIB,'SDK_or_game':False,'main_written':False}))
if __name__=='__main__':main()
