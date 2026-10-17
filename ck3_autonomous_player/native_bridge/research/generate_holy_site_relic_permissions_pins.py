"""Render entry-prefix pins from an explicitly reviewed exact-build manifest."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-pins',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 source=json.loads(a.source_pins.read_text(encoding='utf-8'))
 if source['exe_sha256'].lower()!='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518':
  raise ValueError('source pins are not the reviewed exact4 executable')
 pins=source['pins']
 rows=['// GENERATED from exact-build source-prefix-pins-a01.json; do not edit.\n',
       'constexpr std::array<std::pair<std::uintptr_t,std::string_view>,'+str(len(pins))+'> kPins{{\n']
 for pin in pins:
  raw=bytes.fromhex(pin['prefix_hex'])
  if len(raw)!=32 or hashlib.sha256(raw).hexdigest()!=pin['prefix_sha256']:
   raise ValueError('prefix bytes or SHA changed')
  rows.append(' {0x'+format(pin['entry_rva'],'X')+',"'+raw.hex()+'"},\n')
 rows.append('}};\n')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(''.join(rows),encoding='utf-8',newline='\n')

if __name__=='__main__':main()
