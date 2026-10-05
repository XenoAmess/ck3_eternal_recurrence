"""Ordinary offline source assembly of the exact reviewed a06 continuation.

The 37.6 MiB stock Python/pywin32 payload remains an approved external input.
This tool performs no ACL, elevation, TaskScheduler or Defender operation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

OLD_SHA='3a65d3186ddbee3eb9d7ff3882d7ec58ece4362a0da84fb7fa925a4921bd7ef4'
NEW_SHA='4054437f4a6e18b8feeeab8d2ac91698e82b5006d0b5e49fb1b15afda22ca49e'
IDENTITY='83b30886-8dbc-4c9c-8177-d575be46a925'
OWNER='S-1-5-21-4063940640-1897558599-686929869-1001'
VARIANT_SHA='1da88287ae4fc9f78aecc8388d0a7bb2af53142ed2595bec5945d849979cfc9d'
ENTRY_SHA='d9ae23c50c3b9eda75a699aec85deb64bc27201e05f691559570b3f899d1ee84'

def sha(data):return hashlib.sha256(data).hexdigest()
def raw(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
def pin(path,root):
    data=path.read_bytes();return {'path':path.relative_to(root).as_posix(),'size':len(data),'sha256':sha(data)}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-a05-package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=Path(__file__).parent
    # Import only the checked-in reader, never code from the external payload.
    sys.path.insert(0,str(source))
    from native_safety import NativeSafety
    from installer_core import load_bundle
    safety=NativeSafety(OWNER,r'C:\Program Files\XAR CK3 Project EXE Broker\private-frozen',r'C:\Program Files\XAR CK3 Project EXE Broker\receipts')
    baseline,frozen=load_bundle(args.approved_a05_package,OLD_SHA,safety)
    if baseline['installation_id']!=IDENTITY or len(frozen)!=734:raise ValueError('exact a05 baseline required')
    old={row['path']:data for row,data in frozen}
    variant=(source/'vendor-shims/stock-VARIANT-class.py').read_bytes()
    entry=(source/'frozen-source/resume_project_exe_broker.py').read_bytes()
    if sha(variant)!=VARIANT_SHA or sha(entry)!=ENTRY_SHA:raise ValueError('approved finite producer source pin changed')
    args.output.mkdir(exist_ok=False)
    package=args.output/'package';package.mkdir(exist_ok=False)
    new=dict(old)
    new['deps/win32com/client/__init__.py']=old['deps/win32com/client/__init__.py']+b'\r\n'+variant+b'\r\n'
    if sha(new['deps/win32com/client/__init__.py'])!='e9edd437147e3b2908b86be9cc79a67d229ef65ed6032e91dab950ba90b5410a':
        raise ValueError('stock VARIANT append did not reproduce approved shim')
    seal=json.loads(new['runtime-seal.json'])
    seal['files']=[{'path':row['path'],'size':len(new[row['path']]),'sha256':sha(new[row['path']])} for row in seal['files']]
    new['runtime-seal.json']=raw(seal)
    policy=json.loads(new['policy.json']);policy['runtime_manifest_sha256']=sha(new['runtime-seal.json'])
    new['policy.json']=raw(policy)
    installation=json.loads(new['installation-manifest.json'])
    for key,relative in [('policy','policy.json'),('runtime_seal','runtime-seal.json')]:
        installation[key].update(size=len(new[relative]),sha256=sha(new[relative]))
    new['installation-manifest.json']=raw(installation)
    bundle=dict(baseline)
    bundle['files']=[{'path':row['path'],'size':len(new[row['path']]),'sha256':sha(new[row['path']])} for row in baseline['files']]
    bundle_raw=raw(bundle)
    if sha(bundle_raw)!=NEW_SHA:raise ValueError('new bundle differs from reviewed a06')
    for relative,data in new.items():
        path=package/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    (package/'bundle-manifest.json').write_bytes(bundle_raw)
    old_bundle_raw=(args.approved_a05_package/'bundle-manifest.json').read_bytes()
    if sha(old_bundle_raw)!=OLD_SHA:raise ValueError('baseline manifest changed')
    (args.output/'expected-old-bundle-manifest.json').write_bytes(old_bundle_raw)
    (args.output/'resume_project_exe_broker.py').write_bytes(entry)
    (args.output/'stock-VARIANT-class.py').write_bytes(variant)
    after={row['path']:row for row in bundle['files']}
    changes=[{'path':row['path'],'before':row,'after':after[row['path']]} for row in baseline['files'] if row!=after[row['path']]]
    for change in changes:
        path=args.output/'expected-old-leaves'/change['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(old[change['path']])
    authority={'schema':'xar.project-exe-broker.resume-authority.v1','installation_id':IDENTITY,'owner_sid':OWNER,
      'old_bundle_sha256':OLD_SHA,'new_bundle_sha256':NEW_SHA,
      'old_partial_receipt_sha256':'89952704c6ead5e2b323e8cde424a87b6e89169cf96c95ecbd6a387bdafb02dc',
      'changed_leaves':changes,'new_paths':[],'task_continuation':'missing-folder-create-or-exact-empty-folder-create-only',
      'source_entry':{'path':'resume_project_exe_broker.py','size':len(entry),'sha256':ENTRY_SHA}}
    authority_raw=raw(authority)
    if sha(authority_raw)!='4a1aac6e92801a75ae275cafe83aba7e666d93e24ce0ef3647e1e7dd308eef63':raise ValueError('authority reproducibility mismatch')
    (args.output/'resume-authority.json').write_bytes(authority_raw)
    files=[pin(path,args.output) for path in sorted(args.output.rglob('*')) if path.is_file()]
    if len(files)!=743:raise ValueError('unexpected source capsule path set')
    inventory_raw=raw({'schema':'xar.project-exe-broker.resume-source-inventory.v1','installation_id':IDENTITY,'files':files})
    if sha(inventory_raw)!='7577eb373feb532122b429b8be09dac28e519615fc23c48128abc1f0aa0fafb9':raise ValueError('complete source inventory mismatch')
    (args.output/'resume-source-inventory.json').write_bytes(inventory_raw)
    print(json.dumps({'status':'assembled_exact_reviewed_source_only','output':str(args.output),'installed_paths':734,
      'source_files':744,'bundle_sha256':NEW_SHA,'authority_sha256':sha(authority_raw),'inventory_sha256':sha(inventory_raw),
      'settings_changed':False,'installed':False},indent=2))
if __name__=='__main__':main()
