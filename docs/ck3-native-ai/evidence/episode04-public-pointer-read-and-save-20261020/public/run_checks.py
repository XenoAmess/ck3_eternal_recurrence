"""Source-only checks with original Popen receipts and immutable source pins."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import check_owner as owner

A = Path(__file__).resolve().parent
ROOT = A/'checks-final'
PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
LIB = Path('C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib')
D = Path('D:/workspace/ck3_eternal_recurrence')
SOURCES = [A/'tools/ck3_mod_acceptance_cases'/name for name in
    ('pointer_read_public_models.py','r08_parent_pointer_read_controller.py','r08_parent_pointer_read_one_day.py','pointer_read_bundle_loader.py','ordinary_save_contract.py','r10_prepare_adapter.py')]
SOURCES += [A/'parent-tools'/name for name in ('pointer_read_wire.py','pointer_read_models.py','pointer_read_owner_binding.py',
    'pointer_read_admission_models.py','parent_pointer_read_contract.py','prepare_parent_pointer_read_admission.py',
    'consume_parent_pointer_read_actual.py','cold_runner_models.py','run_parent_pointer_read_cold.py')]


def pins() -> list[owner.Json]:
    return [{'path':str(path),'bytes':path.stat().st_size,'sha256':owner.sha(path.read_bytes())} for path in SOURCES]


def all_pins() -> list[owner.Json]:
    paths = [*(A/'parent-tools').glob('*'),*(A/'tools/ck3_mod_acceptance_cases').glob('*.py'),
             A/'test_public_pointer_v2.py',Path(__file__).resolve()]
    return [{'path':str(path),'bytes':path.stat().st_size,'sha256':owner.sha(path.read_bytes())}
            for path in sorted(paths) if path.is_file()]


def command(label: str, argv: list[str], environment: dict[str,str]) -> int:
    owner.need(owner.census(A) < 1200000,'Author budget before check')
    records = owner.Recorder(ROOT,'desktop-3fevhd2-1c74096080')
    before = pins()
    tracked_before = all_pins()
    source_table = records.put(label+'.SOURCE-PINS.actual.json',{'files':tracked_before})
    process: subprocess.Popen[bytes] = subprocess.Popen(argv,cwd=A,env=environment,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)

    def created(birth: str) -> None:
        records.put(label+'.CREATED.actual.json',{'argv':argv,'pid':process.pid,'creation_filetime_decimal':birth,
            'source_before':before,'Game_SDK_Steam_VM_Git':False})

    result = owner.own_wait(process,None,owner.creation_filetime,created)
    for name,data in (('stdout',result.stdout),('stderr',result.stderr)):
        owner.need(len(data) <= 65536 and owner.census(A)+len(data) <= 1310720,'Bounded source check log')
        with (ROOT/(label+'.'+name+'.log')).open('xb') as stream:
            stream.write(data)
    records.put(label+'.ORIGINAL-WAIT.actual.json',{'argv':argv,'pid':result.pid,'creation_filetime_decimal':result.created,
        'returncode':result.code,'actual_original_popen_wait':True,'diagnostics':list(result.errors),
        'source_before':before,'source_after':pins(),'sources_unchanged':before==pins(),
        'all_actual_dependency_source_pins':{'path':str(source_table.path),'bytes':source_table.size,'sha256':source_table.sha256},
        'all_dependency_before_after_equal':tracked_before==all_pins(),
        'stdout_bytes':len(result.stdout),'stdout_sha256':owner.sha(result.stdout),
        'stderr_bytes':len(result.stderr),'stderr_sha256':owner.sha(result.stderr),'Game_SDK_Steam_VM_Git':False})
    print(label,result.code,result.stdout.decode(errors='replace'),result.stderr.decode(errors='replace'),flush=True)
    return result.code


def main() -> int:
    suffix = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv)>2 else 'static'
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=os.pathsep.join((str(LIB),str(A/'tools'),str(A/'parent-tools'),'C:/ck3-e04-resume-20261020-a01/r08-production-runtime-source-2130-a01/source-candidate-a01/tools',str(D/'tools'),str(D/'ck3_autonomous_player/src'))),
        MYPYPATH=os.pathsep.join((str(A/'tools'),str(A/'parent-tools'),'C:/ck3-e04-resume-20261020-a01/r08-production-runtime-source-2130-a01/source-candidate-a01/tools',str(D/'tools'),str(D/'ck3_autonomous_player/src'))))
    if mode == 'tests':
        return command('focused-'+suffix,[str(PYTHON),'-B','-m','unittest','-v','test_public_pointer_v2'],environment)
    return command('static-'+suffix,[str(PYTHON),'-B','-m','mypy','--no-incremental','--cache-dir','nul',
        '--config-file',str(A/'mypy.ini'),'--namespace-packages','--explicit-package-bases','--follow-imports=skip',
        '--ignore-missing-imports','--disallow-any-generics','--disallow-untyped-defs','--warn-return-any',
        *[str(path) for path in SOURCES]],environment)


if __name__ == '__main__':
    raise SystemExit(main())
