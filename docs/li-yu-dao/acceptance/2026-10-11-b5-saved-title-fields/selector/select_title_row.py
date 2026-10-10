"""One authenticated streaming pass; retain one actual nested Title row only."""
import argparse
import codecs
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
LIMIT = 32768


def bounded_lines(stream, hasher):
    """Yield bounded fragments with line ends; never buffer a world-sized line."""
    decoder = codecs.getincrementaldecoder('utf-8-sig')('strict')
    first = True
    total = 0
    while True:
        chunk = stream.read(65536)
        if not chunk:
            break
        hasher.update(chunk)
        total += len(chunk)
        decoder.decode(chunk, final=False)
        if first:
            if chunk.startswith(b'PK'):
                raise ValueError('Compressed save unsupported; no decoder invoked')
            if chunk.startswith(codecs.BOM_UTF8):
                chunk = chunk[3:]
            first = False
        start = 0
        while start < len(chunk):
            end = chunk.find(b'\n', start)
            if end < 0:
                yield chunk[start:], False
                break
            yield chunk[start:end + 1], True
            start = end + 1
    decoder.decode(b'', final=True)
    yield b'', None  # flush a final unterminated line
    return total


class Selector:
    def __init__(self, title_id, limit=LIMIT):
        self.title_id, self.limit = title_id, limit
        self.outer = self.nested = self.following = self.matches = 0
        self.active = self.closed = False
        self.depth = 0
        self.quoted = self.escaped = False
        self.current = None
        self.row = bytearray()
        self.row_bytes = 0
        self.row_hash = hashlib.sha256()
        self.row_overflow = False
        self.line = bytearray()
        self.line_bytes = 0
        self.line_depth = 0
        self.line_quoted = False

    def retain(self, piece):
        self.row_hash.update(piece)
        self.row_bytes += len(piece)
        if self.row_bytes <= self.limit:
            self.row.extend(piece)
        else:
            self.row.clear()
            self.row_overflow = True

    def feed(self, piece, end):
        if not self.line_bytes:
            self.line_depth, self.line_quoted = self.depth, self.quoted
        self.line_bytes += len(piece)
        if len(self.line) < 128:
            self.line.extend(piece[:128 - len(self.line)])
        if self.current == self.title_id:
            self.retain(piece)
        if self.active:
            for ch in piece:
                if self.quoted:
                    if self.escaped:
                        self.escaped = False
                    elif ch == 92:
                        self.escaped = True
                    elif ch == 34:
                        self.quoted = False
                elif ch == 34:
                    self.quoted = True
                elif ch == 123:
                    self.depth += 1
                elif ch == 125:
                    self.depth -= 1
                    if self.depth < 0:
                        raise ValueError('Title database brace underflow')
        if end is False:
            return
        if not self.line_bytes:
            return
        line = bytes(self.line)
        complete = self.line_bytes == len(line)
        if complete and line == b'landed_titles={\n':
            self.outer += 1
            if self.active or self.nested or self.following:
                raise ValueError('Actual outer Title database boundary differs')
        elif complete and line == b'\tlanded_titles={\n':
            self.nested += 1
            if self.outer != 1 or self.nested != 1 or self.following:
                raise ValueError('Actual nested Title database nonunique/boundary differs')
            self.active, self.depth = True, 1
        elif complete and line == b'dynasties={\n':
            self.following += 1
            if self.active or not self.closed:
                raise ValueError('Actual following section before Title database close')
        elif self.active:
            if self.current is None:
                match = re.fullmatch(rb'([0-9]+)=\{\n', line) if complete else None
                if match:
                    if self.line_depth != 1 or self.line_quoted or self.depth != 2:
                        raise ValueError('Unsupported numeric Title record framing')
                    self.current = int(match[1])
                    if self.current == self.title_id:
                        self.matches += 1
                        if self.matches != 1:
                            raise ValueError('Duplicate selected Title ID')
                        self.retain(line)
                elif self.depth == 0:
                    if not complete or line.strip() != b'}' or self.quoted:
                        raise ValueError('Actual Title database closing frame differs')
                    self.active, self.closed = False, True
                elif not complete or not (line.strip() in (b'', b'}') or line.lstrip().startswith(b'#')):
                    raise ValueError('Unsupported Title record framing')
            elif complete and line in (b'}\n', b'}'):
                if self.line_depth != 2 or self.depth != 1 or self.quoted:
                    raise ValueError('Title record terminator/brace binding differs')
                self.current = None
        self.line.clear()
        self.line_bytes = 0

    def finish(self):
        if (self.outer, self.nested, self.following, self.matches) != (1, 1, 1, 1):
            raise ValueError('Exactly one actual nested database and selected Title required')
        if self.active or not self.closed or self.current is not None:
            raise ValueError('Truncated actual Title database/record')


def scan(stream, title_id):
    sha = hashlib.sha256()
    selector = Selector(title_id)
    size = 0
    # Source read() accounting is separate from retained row size.
    class Counted:
        def read(self, n):
            nonlocal size
            value = stream.read(n)
            size += len(value)
            return value
    for piece, end in bounded_lines(Counted(), sha):
        selector.feed(piece, end)
    selector.finish()
    return selector, size, sha.hexdigest()


def render(selector, source, parser_namespace):
    result = {
        'schema': 'lyd.single-saved-title-stream-observation.v1',
        'status': 'UNQUALIFIED_SELECTED_ROW', 'source': source,
        'title_id': selector.title_id, 'section': 'landed_titles.landed_titles',
        'row_bytes': selector.row_bytes, 'row_sha256': selector.row_hash.hexdigest(),
        'full_save_authenticated': True, 'source_stream_passes': 1,
        'native_title_binding': None, 'saved_title_field_qualification': None,
        'B5_pass': False, 'business_pass': False,
        'input_role': 'R26 protection-RED world; field research only, never seed',
    }
    if selector.row_overflow:
        result['status'] = 'ROW_RETENTION_LIMIT_EXCEEDED'
    else:
        raw = selector.row.decode('utf-8', errors='strict')
        entries = parser_namespace['parse_block'](parser_namespace['block_body'](raw))
        result['entries'] = entries
        result['ast_sha256'] = hashlib.sha256(json.dumps(entries, ensure_ascii=False,
            sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(encoded) > LIMIT:
        result.pop('entries', None)
        result['status'] = 'AST_OUTPUT_LIMIT_EXCEEDED'
        encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(encoded) > LIMIT:
        raise ValueError('Summary exceeds output bound')
    return encoded


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--save', required=True, type=Path)
    ap.add_argument('--bytes', required=True, type=int)
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--title-id', required=True, type=int)
    ap.add_argument('--parser', required=True, type=Path)
    ap.add_argument('--parser-bytes', required=True, type=int)
    ap.add_argument('--parser-sha256', required=True)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    if args.output.exists() or args.save.resolve() == args.output.resolve():
        raise ValueError('Fresh distinct output required')
    parser_source = args.parser.read_bytes()
    if (len(parser_source), hashlib.sha256(parser_source).hexdigest()) != (args.parser_bytes, args.parser_sha256):
        raise ValueError('Original parser exact ref differs')
    namespace = {'__name__': 'authenticated_bounded_save_parser'}
    exec(compile(parser_source, str(args.parser), 'exec'), namespace)
    with args.save.open('rb') as stream:
        selected, size, sha = scan(stream, args.title_id)
    if (size, sha) != (args.bytes, args.sha256):
        raise ValueError('Original checkpoint exact bytes/SHA differs; no output written')
    source = {'path': str(args.save), 'bytes': size, 'sha256': sha,
              'parser': {'path': str(args.parser), 'bytes': args.parser_bytes,
                         'sha256': args.parser_sha256}}
    encoded = render(selected, source, namespace)
    with args.output.open('xb') as stream:
        stream.write(encoded)
    print(json.dumps({'path': str(args.output), 'bytes': len(encoded),
                      'sha256': hashlib.sha256(encoded).hexdigest(),
                      'business_pass': False}))


if __name__ == '__main__':
    main()
