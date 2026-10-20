"""Read the actual public producer receipt; no settings call or EXE execution."""
import argparse,datetime,hashlib,json,ntpath
from pathlib import Path
def read(p):
 b=p.read_bytes();return json.loads(b),{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-root',type=Path,required=True);a=p.parse_args()
 root=a.build_root.resolve();assert root==Path('C:/w/e04parenta01/build-a03').resolve()
 report,rpin=read(root/'native-msvc-result.json');settings=report['defender_exclusions']
 assert report.get('build_succeeded') is True and settings['status']=='verified'
 receipt_path=Path(settings['receipt']).resolve();manifest_path=Path(settings['manifest']).resolve()
 assert receipt_path.is_relative_to(root) and manifest_path.is_relative_to(root)
 receipt,pin=read(receipt_path);manifest,mpin=read(manifest_path)
 assert pin['sha256']==settings['receipt_sha256']
 assert receipt['status']=='verified' and receipt['admin_token'] is True and receipt['system_token_sid']=='S-1-5-18'
 assert receipt['files']==manifest['files'] and len(receipt['files'])==1
 item=receipt['files'][0];expected=root/'parent_entry_opportunity_cold.exe'
 assert Path(item['path']).resolve()==expected and item['target']=='parent_entry_opportunity_cold'
 assert expected.stat().st_size==item['size']
 assert ntpath.normcase(str(expected)) in {ntpath.normcase(x) for x in receipt['verified_requested_paths']}
 assert receipt['missing_requested_paths']==[] and receipt['partial_mutation'] is False
 assert receipt['observed_extensions_unchanged'] is True and receipt['observed_processes_unchanged'] is True and receipt['observed_prior_settings_preserved'] is True
 gate={'schema':'xar.parent-entry.cold-EXE-execution-gate.v1','machine_id':'desktop-3fevhd2-1c74096080',
  'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'verified-before-first-project-EXE-execution',
  'producer':rpin,'receipt':pin,'manifest':mpin,'files':receipt['files'],'system_token_sid':'S-1-5-18',
  'game_contact':False,'native_cold_or_real_install_qualification':False}
 out=root/'EXECUTION-GATE.actual.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(gate,f,indent=2);f.write('\n')
 print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
