"""Verify the small package or rebuild retired SDK bytes to a new derived file."""
import argparse,gzip,hashlib,json,pathlib,sys
BASE=pathlib.Path(__file__).resolve().parent
def serialize_response(raw):
    return (json.dumps(json.loads(raw),ensure_ascii=False)+'\n').encode('utf-8')
def new_output(output,derived_root,responses_root,old_path):
    target=pathlib.Path(output).resolve();derived=pathlib.Path(derived_root).resolve();responses=pathlib.Path(responses_root).resolve()
    receipt=pathlib.Path(str(target)+'.rebuild-receipt.json')
    if not target.is_relative_to(derived) or target.is_relative_to(responses.parent):raise ValueError('Output must be in a separate new derived root')
    if target.name.lower()=='mcp-calls.jsonl' or target==pathlib.Path(old_path).resolve():raise ValueError('Do not recreate or impersonate the retired original path/name')
    if target.exists() or receipt.exists():raise FileExistsError('Never overwrite output or rebuild receipt')
    return target,receipt
def verify_package(manifest):
    for entry in manifest['assets']:
        raw=(BASE/entry['file']).read_bytes()
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Canonical package pin mismatch: '+entry['file'])
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-package-only',action='store_true');parser.add_argument('--run',choices=['r0162','r0164'])
    parser.add_argument('--responses-root',type=pathlib.Path);parser.add_argument('--derived-root',type=pathlib.Path);parser.add_argument('--output',type=pathlib.Path)
    args=parser.parse_args();manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));verify_package(manifest)
    if args.verify_package_only:print(json.dumps({'canonical_assets_verified':len(manifest['assets'])}));return
    if not all([args.run,args.responses_root,args.derived_root,args.output]):parser.error('Provide --run, --responses-root, --derived-root and --output')
    run=manifest['runs'][args.run];responses=args.responses_root.resolve(strict=True);target,receipt=new_output(args.output,args.derived_root,responses,run['original_path'])
    target.parent.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256();written=lines=0;status='FAILED_PARTIAL_DERIVED_OUTPUT';error=None
    try:
        with target.open('xb') as output,gzip.open(BASE/run['ordered_index'],'rt',encoding='utf-8') as index:
            for text in index:
                row=json.loads(text);relative=pathlib.PurePosixPath(row['response_relative_path'].replace('\\','/'))
                if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='responses':raise ValueError('Unsafe indexed response path')
                source=responses.joinpath(*relative.parts[1:]).resolve(strict=True)
                if not source.is_relative_to(responses):raise ValueError('Response path escaped supplied root')
                raw=source.read_bytes()
                if len(raw)!=row['response_bytes'] or hashlib.sha256(raw).hexdigest()!=row['response_sha256']:raise ValueError('Retained response changed: '+str(source))
                encoded=serialize_response(raw)
                if len(encoded)!=row['original_line_bytes']:raise ValueError('Rebuilt line size mismatch')
                output.write(encoded);digest.update(encoded);written+=len(encoded);lines+=1
            output.flush()
        if written!=run['original_bytes'] or lines!=run['line_count'] or digest.hexdigest()!=run['original_sha256']:raise ValueError('Aggregate original byte/SHA/count mismatch')
        status='VERIFIED_DERIVED_REBUILD'
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    result={'status':status,'error':error,'run':args.run,'new_derived_output':str(target),'output_bytes':written,'output_sha256':digest.hexdigest(),'line_count':lines,'original_physical_path_available':False,'recreated_file_is_derived_not_original_physical_evidence':True,'original_path':run['original_path']}
    with receipt.open('x',encoding='utf-8',newline='\n') as output:json.dump(result,output,ensure_ascii=False,indent=2);output.write('\n')
    print(json.dumps(result,ensure_ascii=False))
    if error:raise SystemExit(1)
if __name__=='__main__':main()
