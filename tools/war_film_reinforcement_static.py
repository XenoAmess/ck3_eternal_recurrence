"""Read-only exact-build reinforcement research; never opens a game process."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'


def default_exe():
    for root in (ROOT, Path('D:/workspace/ck3_eternal_recurrence')):
        candidate = root / 'Crusader Kings III/binaries/ck3.exe'
        if candidate.is_file():
            return candidate
    for candidate in (Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe'),
                      Path('D:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe')):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError('Pass --exe for the frozen CK3 1.19.0.6 executable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--rva', type=lambda v: int(v, 0))
    parser.add_argument('--size', type=lambda v: int(v, 0), default=0x200)
    parser.add_argument('--literal')
    parser.add_argument('--refs', type=lambda v: int(v, 0), nargs='+', help='Locate common RIP-relative MOV/LEA consumers of exact RVAs')
    parser.add_argument('--strings', nargs='+', help='Locate common RIP references to exact null-terminated UTF-8 literals in one scan')
    parser.add_argument('--calls', type=lambda v: int(v, 0), help='Locate E8 direct calls; containing-function decode required')
    parser.add_argument('--output', type=Path, help='Exclusive-create text output; never overwrite an old attempt')
    args = parser.parse_args()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = args.output.open('x', encoding='utf-8', newline='\n')
    exe = args.exe or default_exe()
    raw = exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f'Executable build mismatch: {digest}')
    if args.refs or args.strings or args.calls is not None:
        import pefile
        from capstone import Cs, CS_ARCH_X86, CS_MODE_64
        from bisect import bisect_right
        pe = pefile.PE(data=raw, fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']])
        functions = sorted((e.struct.BeginAddress, e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
        starts = [p[0] for p in functions]
        targets = {v: hex(v) for v in args.refs or []}
        for name in args.strings or []:
            start = 0
            while (start := raw.find(name.encode()+b'\0', start)) >= 0:
                targets[pe.get_rva_from_offset(start)] = name
                start += 1
        if args.calls is not None:
            targets[args.calls] = hex(args.calls)
        encoding = rb'\xe8.{4}' if args.calls is not None else rb'[\x40-\x4f]?[\x8b\x8d\x89\x3b\x39\x03\x2b\x63][\x05\x0d\x15\x1d\x25\x2d\x35\x3d].{4}'
        pattern = re.compile(b'(?=('+encoding+b'))', re.DOTALL)
        dis = Cs(CS_ARCH_X86, CS_MODE_64)
        boundaries = {}
        rows = []
        for section in pe.sections:
            if not section.IMAGE_SCN_MEM_EXECUTE:
                continue
            code = section.get_data()
            for m in pattern.finditer(code):
                rva = section.VirtualAddress + m.start()
                encoded = m[1]
                target = rva + len(encoded) + struct.unpack('<i', encoded[-4:])[0]
                if target not in targets:
                    continue
                instruction = next(dis.disasm(encoded, pe.OPTIONAL_HEADER.ImageBase+rva), None)
                if instruction is None or instruction.size != len(encoded):
                    continue
                i = bisect_right(starts, rva)-1
                func = functions[i] if i >= 0 and rva < functions[i][1] else None
                if func:
                    if func not in boundaries:
                        off = pe.get_offset_from_rva(func[0])
                        boundaries[func] = {ins.address-pe.OPTIONAL_HEADER.ImageBase for ins in dis.disasm(raw[off:off+func[1]-func[0]], pe.OPTIONAL_HEADER.ImageBase+func[0])}
                    if rva not in boundaries[func]:
                        continue
                rows.append({'rva': hex(rva), 'target_rva': hex(target), 'target_label':targets[target], 'bytes': encoded.hex(),
                             'instruction': instruction.mnemonic+' '+instruction.op_str,
                             'function': [hex(v) for v in func] if func else None})
        print(json.dumps({'exe':str(exe),'exe_sha256':digest,'scan_boundary':'common RIP-relative integer MOV/LEA/CMP/ADD/SUB encodings; candidates require containing-function disassembly before interpretation','references':rows}, indent=2))
    elif args.literal:
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/native_bridge/research'))
        from find_string_xrefs import inspect
        print(json.dumps(inspect(exe, args.literal), ensure_ascii=False, indent=2))
    elif args.rva is not None:
        import pefile
        from capstone import Cs, CS_ARCH_X86, CS_MODE_64
        pe = pefile.PE(data=raw, fast_load=True)
        start = pe.get_offset_from_rva(args.rva)
        print(f'EXE_SHA256={digest} RVA={args.rva:#x} size={args.size:#x}')
        for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(raw[start:start+args.size], pe.OPTIONAL_HEADER.ImageBase+args.rva):
            print(f'{i.address-pe.OPTIONAL_HEADER.ImageBase:09X}  {i.bytes.hex(" "):<32} {i.mnemonic:<8} {i.op_str}')
    else:
        print(json.dumps({'exe': str(exe), 'sha256': digest, 'bytes': len(raw), 'python': sys.executable,
                          'dependencies': {name: importlib.metadata.version(name) for name in ('pefile', 'capstone')}}, indent=2))


if __name__ == '__main__':
    main()
