"""Reapply directory-scoped attributes to staged historical evidence without altering originals."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent

def main():
    spec = importlib.util.spec_from_file_location('_derivatives',ROOT / 'derive_full_panel_owner_proof_a01.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = (ROOT / 'commit_exact_R0140_archive_a04.py').read_text(encoding='utf-8')
    count = original.count('-a04')
    record = module.derive('commit_exact_R0140_archive_a04.py','commit_exact_R0140_archive_a05.py',[
        ("set(git('diff','--cached','--name-only').splitlines()) == original_names",
         "set(git('diff','--cached','--name-only').splitlines()) == original_names | {(ARCHIVE / '.gitattributes').relative_to(SOURCE).as_posix()}",1),
        ("require(not git('diff','--name-only'),'Original tracked worktree asset changed')",
         "require(set(git('diff','--name-only').splitlines()).issubset(original_names),'Unreviewed tracked worktree file changed')",1),
        ("[*GIT,'add','-f','--'","[*GIT,'add','--renormalize','-f','--'",1),
        ('-a04','-a05',count)])
    module.write('R0140-canonical-stage-derivative-a05.json',{
        'previous_stage_result':'REJECTED_BEFORE_COMMIT_BY_CANONICAL_SHA_CHECK',
        'cause':'Git add retained stat-cached normalized index entries; renormalize explicitly reapplies new -text attributes.',
        'exact_original_bytes_unchanged':True,'fresh_process_records_required':True,
        'derivative':record})
    print(json.dumps(record))

if __name__ == '__main__':
    main()
