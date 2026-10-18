"""Materialize one previously encoded, SHA-bound segment without re-encoding."""
from pathlib import Path
import argparse
import hashlib
import json
import os

def need(value, message):
    if not value:
        raise ValueError(message)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--partial-output',type=Path,required=True)
    parser.add_argument('--expected-bytes',type=int,required=True)
    parser.add_argument('--expected-sha256',required=True)
    args=parser.parse_args()
    source=args.source.resolve()
    output=args.partial_output.resolve()
    need(source.is_file() and not output.exists(), 'source missing or partial output exists')
    need(args.expected_bytes>0 and len(args.expected_sha256)==64, 'invalid source pin')
    need(source.stat().st_size==args.expected_bytes, 'source length changed')
    output.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256();count=0
    with source.open('rb') as inp, output.open('xb') as out:
        for block in iter(lambda:inp.read(1024*1024),b''):
            out.write(block);digest.update(block);count+=len(block)
        out.flush();os.fsync(out.fileno())
    need(count==args.expected_bytes and digest.hexdigest()==args.expected_sha256.lower(), 'copied segment does not match source pin; partial retained')
    print(json.dumps({'status':'REUSED_EXACT_ENCODED_SEGMENT','source':str(source),'partial_output':str(output),'bytes':count,'sha256':digest.hexdigest(),'reencoded':False}))

if __name__=='__main__':main()
