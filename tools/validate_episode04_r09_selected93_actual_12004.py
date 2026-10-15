"""Read a portable literal R0176 projection; never access raw paths or runtime."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('projection',type=Path)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    if args.projection.stat().st_size>1024*1024:raise ValueError('literal projection exceeds1MiB')
    raw=args.projection.read_bytes()
    sys.path.insert(0,str(args.repo/'ck3_autonomous_player/src'))
    source=Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_r09_selected93_actual_12004.py'
    spec=importlib.util.spec_from_file_location('r09_saved_reader',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    value=module.qualify_r0176_selected93_micro_12004(json.loads(raw))
    print(json.dumps({'projection_bytes':len(raw),'projection_sha256':hashlib.sha256(raw).hexdigest(),
                      'semantic_result':value},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
