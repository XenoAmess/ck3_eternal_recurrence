"""Read-only exact-build declaration-input extraction; never opens a process."""
from pathlib import Path
import argparse
import hashlib
import json

SHA = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'
DEFAULT_EXE = Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, default=DEFAULT_EXE)
    p.add_argument('--rva', type=lambda s: int(s, 0), required=True)
    p.add_argument('--size', type=lambda s: int(s, 0), required=True)
    p.add_argument('--qwords', action='store_true', help='Read file-backed uint64 values instead of decoding instructions')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('wrong exact-build executable')
    image = pefile.PE(data=raw, fast_load=True)
    offset = image.get_offset_from_rva(args.rva)
    block = raw[offset:offset+args.size]
    lines = [f'EXE_SHA256={SHA} RVA={args.rva:#x} SIZE={args.size:#x} BLOCK_SHA256={hashlib.sha256(block).hexdigest()}']
    if args.size <= 0 or len(block) != args.size:
        raise ValueError('requested block is not completely file-backed')
    if args.qwords:
        if args.size % 8:
            raise ValueError('--qwords requires a multiple-of-eight size')
        for pos in range(0, args.size, 8):
            value = int.from_bytes(block[pos:pos+8], 'little')
            lines.append(f'{args.rva+pos:09X}  value={value:#x} relative_to_image_base={value-image.OPTIONAL_HEADER.ImageBase:#x}')
    else:
        for ins in Cs(CS_ARCH_X86, CS_MODE_64).disasm(block, image.OPTIONAL_HEADER.ImageBase+args.rva):
            lines.append(f'{ins.address-image.OPTIONAL_HEADER.ImageBase:09X}  {ins.bytes.hex(" "):<32} {ins.mnemonic:<8} {ins.op_str}')
    body = '\n'.join(lines)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8',newline='\n') as out:
            out.write(body)
    else:
        print(body,end='')


if __name__ == '__main__':
    main()
