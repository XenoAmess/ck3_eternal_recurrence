from pathlib import Path
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = BASE / 'r10-log-preterminal-cut244-readonly-review-20261006-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))

def dump_new(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert not (OUT / 'INDEX.json').exists()
keywords = re.compile(r'error|invalid|failed|failure|assert|exception|unknown|undefined|not found|wrong scope|null scope|dereference|unrecognized', re.I)
lyd = re.compile(r'(?<![A-Za-z0-9_])lyd[A-Za-z0-9_]*', re.I)
runtime = re.compile(r'(?:(?:invalid|unknown|undefined|wrong|null|failed|failure|error|unrecognized).{0,80}(?:scope|reference|effect|trigger)|(?:scope|reference|effect|trigger).{0,80}(?:invalid|unknown|undefined|wrong|null|failed|failure|error|unrecognized))', re.I)
candidates = []
lyd_signatures = {}
for log in ['error.log', 'debug.log']:
    blocks = load(OUT / ('BLOCKS-' + log + '.json'))['records']
    for block in blocks:
        if block['category'] != 'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC' and keywords.search(block['message']):
            candidates.append({'log': log, 'runtime_keyword_candidate': bool(runtime.search(block['message'])), **block})
        if lyd.search(block['message']) and block['category'] != 'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC':
            row = lyd_signatures.setdefault(block['message'], {'count': 0, 'log': log,
                'first_line': block['first_line'], 'last_line': block['last_line']})
            row['count'] += 1
            row['last_line'] = block['last_line']
dump_new(OUT / 'ALL-SEVERITY-ERROR-KEYWORD-REVIEW-CANDIDATES.json', {
    'method': 'All captured complete blocks, including D/I/no-prefix records, searched for error-oriented terms; candidates are not automatically declared errors',
    'records': candidates})
dump_new(OUT / 'LYD-NON-UNUSED-LOG-SIGNATURES.json', {
    'method': 'Full LYD identifier token matches; these are log references, not automatic evidence of executed business effects or errors',
    'rows': [{'exact_message_clock_stripped': msg, **row} for msg, row in lyd_signatures.items()]})
print(json.dumps({'error_keyword_candidate_count': len(candidates),
                  'candidates': candidates,
                  'lyd_nonunused_signature_count': len(lyd_signatures),
                  'lyd_nonunused_signatures': [{'message': msg, **row} for msg, row in lyd_signatures.items()]}, ensure_ascii=True))
