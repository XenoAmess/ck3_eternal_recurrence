"""Generate only an external controlled R05 mod; never starts or connects CK3."""
from pathlib import Path
import argparse,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--province-id',required=True,type=int)
    p.add_argument('--supply-loss-fraction',default='0.999')
    p.add_argument('--decision-key',default='xar_r05_initialize_low_supply')
    p.add_argument('--repo-root',type=Path,default=ROOT,help='dependency checkout; default is this integrated repository')
    a=p.parse_args()
    repo=a.repo_root.resolve()
    sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
    from ck3_live_run_id import current_machine_id
    module_path=ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py'
    spec=importlib.util.spec_from_file_location('xar_autoplayer.bridge.r05_low_supply_fixture',module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if a.output.resolve().is_relative_to(repo):
        p.error('fixture output must be outside repository')
    result=module.generate_fixture(a.output,province_id=a.province_id,machine_id=current_machine_id(),
        fraction=a.supply_loss_fraction,decision_key=a.decision_key)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
