"""Preserve failed archive precheck and correct path normalization and argv size."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent

def main():
    spec = importlib.util.spec_from_file_location('_derivatives',ROOT / 'derive_full_panel_owner_proof_a01.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = module.derive('commit_R0140_research_archive_a01.py','commit_R0140_research_archive_a02.py',[
        ("        require(allowed and identity(path) == pin,'Archive path or bytes changed: ' + relative)",
         "        actual = identity(path)\n        require(allowed and actual['bytes'] == pin['bytes'] and actual['sha256'] == pin['sha256'],'Archive path or bytes changed: ' + relative)",1),
        ("(['git','add','--',*files],['git','diff','--cached','--check'],",
         "(['git','add','--',str(BASE / 'R0140-current-research-originals'),str(BASE / 'current-native-research-R0140.json'),str(BASE / 'current-native-research-R0140.md')],['git','diff','--cached','--check'],",1)])
    module.write('R0140-archive-precheck-derivative-a02.json',{
        'predecessor_precheck_result':'REJECTED_BEFORE_ANY_GIT_MUTATION',
        'cause':'Literal path strings used forward/backward slash variants; actual pins must compare resolved path plus exact bytes/SHA.',
        'create_only_derivative':record,'no_research_status_changed':True})
    print(json.dumps(record))

if __name__ == '__main__':
    main()
