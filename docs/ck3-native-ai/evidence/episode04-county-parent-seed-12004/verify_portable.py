"""Validate frozen source bytes and saved disassembly; no EXE or live access."""
from pathlib import Path
import hashlib
import json
import re
import tarfile

def require(value, reason):
    if not value:
        raise ValueError(reason)

def main():
    root = Path(__file__).resolve().parent
    index = json.loads((root / 'PORTABLE-INDEX.json').read_bytes())
    archive = root / index['archive']['path']
    raw = archive.read_bytes()
    require(len(raw) == 15948, 'archive size')
    require(hashlib.sha256(raw).hexdigest() == '4141147cd0f193b0833c933d1fe7b6fb3222d9c8a6b1b2b7967101dfa9723d87', 'archive SHA')
    with tarfile.open(archive) as source:
        members = source.getmembers()
        require(all(m.isfile() and '/' not in m.name and '\\' not in m.name for m in members), 'regular flat members')
        require([{'name': m.name, 'bytes': m.size} for m in members] == index['archive']['members'], 'member inventory')
        def read(name):
            stream = source.extractfile(name)
            require(stream is not None, name)
            return stream.read()
        for name in ['README.md', 'SOURCE-INDEX.actual-a01.json']:
            require((root / name).read_bytes() == read(name), 'exact copy ' + name)
        original = json.loads(read('SOURCE-INDEX.actual-a01.json'))
        for key in ['body', 'asm', 'raw_window']:
            item = original[key]
            data = read(item['member'])
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], key)
        body = read('source-28BFC50.bin')
        require(read('source-28BFC50.prefix240.bin')[:118] == body, 'reachable body prefix')
        rows = []
        for line in read('source-28BFC50.asm').decode('utf-8-sig').splitlines():
            m = re.match(r'^([0-9A-F]{8})\s+((?:[0-9a-f]{2}\s+)+)([a-z][a-z0-9]*)\s*(.*)$', line)
            if m:
                rows.append((int(m[1], 16), bytes.fromhex(m[2]), m[3], m[4]))
        require(len(rows) == 31 and b''.join(r[1] for r in rows) == body, 'saved ASM bytes')
        position = 0x28BFC50
        starts = {r[0] for r in rows}
        for address, data, mnemonic, operands in rows:
            require(address == position, 'contiguous saved ASM')
            position += len(data)
            require(mnemonic != 'call', 'no CALL in saved ASM')
            if mnemonic.startswith('j'):
                require(int(operands, 16) in starts, 'internal jump target')
        require(position == 0x28BFCC6, 'reachable end')
        require([r[0] for r in rows if r[2] == 'ret'] == [0x28BFC80, 0x28BFCC5], 'two RETs')
    print(json.dumps({'status': 'PASS', 'members': len(members), 'body_bytes': 118,
        'saved_asm_rows': 31, 'machine_id_of_source': index['machine_id'],
        'new_disassembly_or_native_execution': False, 'runtime_or_physical_credit': False}))

if __name__ == '__main__':
    main()
