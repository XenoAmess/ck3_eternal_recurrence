"""Default PLAN. Explicitly verify only bounded package-relative text bytes.

The local manifest is the declared inventory. This verifies file integrity,
not the authenticity of historical review receipts or any external media.
Input failures use explicit exceptions, including under python -O.
"""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath

MAX_FILE_BYTES=1024*1024
MAX_FILES=256
TEXT_SUFFIXES={'.json','.jsonl','.md','.txt','.py','.patch','.ass'}

def verify(root):
    root=root.resolve(strict=True)
    if not root.is_dir():raise ValueError('package root must be a directory')
    manifest=root/'manifest.json'
    if not manifest.is_file() or manifest.is_symlink() or not 0<manifest.stat().st_size<=MAX_FILE_BYTES:
        raise ValueError('bounded local manifest required')
    manifest_bytes=manifest.read_bytes()
    data=json.loads(manifest_bytes)
    if not isinstance(data,dict) or not isinstance(data.get('files'),list) or not 0<len(data['files'])<=MAX_FILES:
        raise ValueError('bounded manifest file inventory required')
    seen=set();total=0
    for item in data['files']:
        if not isinstance(item,dict):raise ValueError('file record must be an object')
        value=item.get('relative')
        if not isinstance(value,str) or not value or ':' in value or '\\' in value:
            raise ValueError('explicit POSIX relative path required')
        relative=PurePosixPath(value)
        if relative.is_absolute() or '..' in relative.parts or value in seen or relative.as_posix()!=value:
            raise ValueError('unique normalized package-relative path required')
        if relative.suffix.lower() not in TEXT_SUFFIXES:
            raise ValueError('only declared text source files permitted')
        size=item.get('bytes');digest=item.get('sha256')
        if type(size) is not int or not 0<=size<=MAX_FILE_BYTES or not isinstance(digest,str) or len(digest)!=64:
            raise ValueError('bounded file size and SHA-256 required')
        try:int(digest,16)
        except ValueError as error:raise ValueError('hex SHA-256 required') from error
        path=root.joinpath(*relative.parts)
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file() or path.stat().st_size!=size:
            raise ValueError('local carried file missing or byte length differs: '+value)
        raw=path.read_bytes()
        if b'\x00' in raw:raise ValueError('NUL bytes are not carried text: '+value)
        raw.decode('utf-8-sig')
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest.lower():
            raise ValueError('exact declared source bytes differ: '+value)
        seen.add(value);total+=size
    return {'status':'PASS_BOUNDED_RELATIVE_TEXT_PACKAGE_EXPLICIT_FAILURES','catalog_files':len(seen),
            'catalog_bytes':total,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
            'external_locator_reads':0,'media_reads':0,'provider_processes_started':0,
            'source_or_media_authenticity_credit':False,'continuous_clean_or_human_film_signoff':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    if not args.verify:
        print(json.dumps({'status':'PLAN_ONLY','file_reads':0,'writes':0,'provider_media_Game_SDK_UI_calls':0,'human_signoff':False}));return 0
    try:result=verify(args.root)
    except (OSError,ValueError,TypeError,KeyError) as error:
        print(json.dumps({'status':'FAIL_BOUNDED_RELATIVE_TEXT_PACKAGE','error':str(error)},ensure_ascii=False));return 2
    print(json.dumps(result,ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
