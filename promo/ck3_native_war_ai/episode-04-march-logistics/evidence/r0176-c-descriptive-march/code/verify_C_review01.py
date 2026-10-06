"""Default PLAN; --verify replays only declared relative JSON/text evidence."""
import argparse,importlib.util,json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--package',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    if not args.verify:
        print(json.dumps({'status':'PLAN_ONLY','read_evidence':False,'write_or_machine_actions':False,
                          'C_terminal':None,'winner':None,'controlled_comparison_eligibility':'NOT_GRANTED'})); return 0
    try:
        spec=importlib.util.spec_from_file_location('review01_core',Path(__file__).with_name('review01_core.py'))
        core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
        manifest,objects,cache=core.read_manifest(args.package)
        actual=core.derive(args.package,objects,cache)
        core.need(actual==objects['C-review01-values.json'],'derived Review01 must equal saved values')
        core.need(actual['normalized_C_result']==objects['normalized_C_result.json'],
                  'standalone downstream normalized result equals source-derived projection')
        print(json.dumps({'status':'PASS_C_REVIEW01_TEXT_SOURCES','source_artifacts':len(cache),
                         'C_status':actual['status'],'C_terminal':None if actual['terminal'] is None else actual['terminal']['status'],
                         'sampling_deviation_count':len(actual['sampling_deviations']),
                         'controlled_comparison_eligibility':'NOT_GRANTED','winner':None,
                         'raw_save_Game_SDK_UI_bus_Git_or_network_actions':0},indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
        print(json.dumps({'status':'FAIL_C_REVIEW01_TEXT_SOURCES','error':str(exc)},indent=2)); return 2

if __name__=='__main__': raise SystemExit(main())
