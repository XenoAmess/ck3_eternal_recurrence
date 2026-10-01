"""Create a long-path-aware exact archive commit, including preserved ignored process assets."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent

def main():
    spec = importlib.util.spec_from_file_location('_derivatives',ROOT / 'derive_full_panel_owner_proof_a01.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = module.derive('commit_R0140_research_archive_a02.py','commit_R0140_research_archive_a03.py',[
        ("['git',*args]","['git','-c','core.longpaths=true',*args]",1),
        ("set(git('ls-files','--others','--exclude-standard').splitlines()) == set(files)",
         "set(git('ls-files','--others','--exclude-standard').splitlines()).issubset(set(files)) and {path.relative_to(SOURCE).as_posix() for path in (BASE / 'R0140-current-research-originals').rglob('*') if path.is_file()} | {str((BASE / name).relative_to(SOURCE).as_posix()) for name in ('current-native-research-R0140.json','current-native-research-R0140.md')} == set(files)",1),
        ("['git','add','--',str(BASE","['git','-c','core.longpaths=true','add','-f','--',str(BASE",1),
        ("['git','diff','--cached','--check']","['git','-c','core.longpaths=true','diff','--cached','--check']",1),
        ("['git','commit','-m'","['git','-c','core.longpaths=true','commit','-m'",1),
        ("        require(result.returncode == 0,'Private archive commit failed')",
         "        require(result.returncode == 0,'Private archive commit failed')\n        if index == 0:\n            require(set(git('diff','--cached','--name-only').splitlines()) == set(files),'Staged archive differs from exact reviewed 709-file manifest')",1)])
    module.write('R0140-archive-precheck-derivative-a03.json',{
        'predecessor_precheck_result':'REJECTED_BEFORE_ANY_GIT_MUTATION',
        'cause':'Windows Git default long-path limit and ordinary ignore rules must not omit preserved process evidence.',
        'per_command_core_longpaths':True,'global_git_configuration_modified':False,
        'exact_709_file_set_before_and_after_stage_required':True,'create_only_derivative':record})
    print(json.dumps(record))

if __name__ == '__main__':
    main()
