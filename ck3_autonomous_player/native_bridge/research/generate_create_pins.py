"""Generate the finite Create callback prefixes from frozen source packets.

No EXE, section cache, process, or native call is accessed by this generator.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-source-root',type=Path,required=True)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'include/xar_bridge/holy_site_creation_create_once12004_pins.hpp')
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    machine=subprocess.check_output([sys.executable,'-B',str(args.repo_source_root/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    specs=[('source/create-callback.json',0x17E9B60),('c0-source/vslot17e9220.json',0x17E9220),
        ('create-once-source-a01/clone.json',0x29A77F0),('create-once-source-a01/queue_submit.json',0x37F06D0),
        ('create-once-source-a01/action_secondary.json',0x29A55B0),('create-once-source-a01/create_site.json',0x29D9790)]
    rows=[];inputs=[]
    for name,rva in specs:
        path=args.evidence_root/name;data=path.read_bytes();packet=json.loads(data);raw=bytes.fromhex(packet['bytes_hex'])
        if (hashlib.sha256(raw).hexdigest()!=packet['bytes_sha256'] or packet['begin_rva']!=rva or
                packet['exe_sha256']!='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518' or len(raw)<32):
            raise ValueError('Frozen exact4 packet identity mismatch: '+str(path))
        rows.append('{0x%X,{%s}},'%(rva,','.join('0x%02X'%x for x in raw[:32])))
        inputs.append({'path':path.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),
            'source_machine_id':packet.get('machine_id','unknown'),'rva':rva,
            'prefix_sha256':hashlib.sha256(raw[:32]).hexdigest()})
    text='// GENERATED FILE: generate_create_pins.py; original callback chain, exact4 only.\n#pragma once\n#include <array>\n#include <cstdint>\nnamespace xar::ck3_12004::religion::holy_site_creation::create_source {\nstruct Pin {std::uintptr_t rva;std::array<unsigned char,32> bytes;};\ninline constexpr std::array<Pin,%d> pins{{\n'%len(rows)+'\n'.join(rows)+'\n}};\n}\n'
    data=text.encode('utf-8')
    if args.check:
        if args.output.read_bytes()!=data:raise ValueError('Generated header differs')
    else:
        with args.output.open('xb') as output:output.write(data)
    result={'machine_id':machine,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'inputs':inputs,'output':args.output.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),
        'check':args.check,'local_exe_or_game_read':False}
    if args.manifest:
        with args.manifest.open('x',encoding='utf-8',newline='\n') as output:json.dump(result,output,indent=2);output.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
