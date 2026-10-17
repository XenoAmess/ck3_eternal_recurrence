"""Render reviewed small prefix inputs without reading CK3 or its section cache."""
from pathlib import Path
import argparse,hashlib,json

def render(manifest:Path)->str:
 value=json.loads(manifest.read_bytes())
 if value['exe_sha256']!='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518':raise ValueError('unsupported source identity')
 rows=value['pins'];seen=set()
 for row in rows:
  raw=bytes.fromhex(row['bytes_hex']);rva=row['rva']
  if not 0<len(raw)<=64 or len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['bytes_sha256'] or rva in seen:raise ValueError('invalid reviewed prefix input')
  seen.add(rva)
 lines=['// GENERATED from source-slot/loaded-code-prefix-pins-a01.json; do not edit.',
  '// Exact CK3 1.20.0.4 frozen cache; runtime comparison is still required.',
  f'constexpr std::array<std::pair<std::uintptr_t,std::string_view>,{len(rows)}> kPins{{{{']
 lines.extend(f' {{0x{row["rva"]:X},"{row["bytes_hex"]}"}}, // {row["label"]}' for row in rows)
 return '\n'.join(lines+['}};'])+'\n'

def main()->int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[3])
 p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
 manifest=a.manifest or a.repo_root/'docs/ck3-native-ai/holy-site-relic-native-actions12004/loaded-code-prefix-pins.json'
 output=a.output or a.repo_root/'ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_action_context_pins.inc'
 data=render(manifest).encode('utf-8')
 if a.check:
  if output.read_bytes()!=data:raise ValueError('generated prefix include differs')
 else:output.write_bytes(data)
 print(json.dumps({'status':'exact' if a.check else 'rendered','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'game_contacted':False}))
 return 0
if __name__=='__main__':raise SystemExit(main())
