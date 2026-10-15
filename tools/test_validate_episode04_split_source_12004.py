from pathlib import Path
import hashlib,importlib.util,json,shutil,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_replay',ROOT/'tools/validate_episode04_split_source_12004.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
INDEX=ROOT/'docs/ck3-native-ai/evidence/episode04-split-source-12004/source-index.json'

class SourceReplayTests(unittest.TestCase):
 def test_complete_portable_bundle_replays(self):
  result=module.validate_source_index(INDEX)
  self.assertEqual(result['status'],'STATIC_SOURCE_CONTRACT_REPLAYED')
  self.assertEqual(result['families'],13)
  self.assertEqual(result['raw_bytes'],8509)
  self.assertIsNone(result['runtime_business_credit'])

 def test_altered_bytes_and_unsafe_paths_fail(self):
  for change in ('raw','instruction','path','build'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary)/'portable';shutil.copytree(INDEX.parent,root)
    index=root/'source-index.json';packet=json.loads(index.read_text(encoding='utf-8'))
    if change=='raw':
     target=root/packet['families'][0]['raw_hex_path'];raw=target.read_text();target.write_text('00'+raw[2:],encoding='ascii')
    if change=='instruction':
     family=packet['families'][0];target=root/family['instructions_path']
     value=json.loads(target.read_text(encoding='utf-8'));value['instructions'][0]['bytes']='000000'
     raw=json.dumps(value).encode();target.write_bytes(raw);family['instructions_sha256']=hashlib.sha256(raw).hexdigest()
    if change=='path':packet['families'][0]['raw_hex_path']='../outside.hex'
    if change=='build':packet['exe_sha256']='0'*64
    index.write_text(json.dumps(packet),encoding='utf-8')
    with self.assertRaises(ValueError):module.validate_source_index(index)

if __name__=='__main__':unittest.main()
