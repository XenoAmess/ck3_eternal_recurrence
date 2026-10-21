"""Create the independently named postload public source fork; never execute it."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=Path('C:/ck3-e04-resume-20261020-a01')
OLD=BASE/'r08-pointer-live-0030-a01/immutable-a01'
CORE=BASE/'r08-post-window-source-0130-a01/native-postload-a01/candidate-a01'
OUT=ROOT/'candidate'

def pin(path: Path) -> dict[str,object]:
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def write(path: Path,raw: bytes) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)

def main() -> None:
    if datetime.now(timezone.utc)>=datetime(2026,10,21,2,30,tzinfo=timezone.utc):raise ValueError('Expired scope')
    rows=[]
    for name in ('postload_wire.py','postload_models.py','postload_owner_binding.py','parent_postload_contract.py'):
        source=CORE/name;target=OUT/'native-tools'/name
        write(target,source.read_bytes());rows.append({'role':'immutable native typed fork','source':pin(source),'copy':pin(target)})
    for name in ('r04_county_entry_window.py','r04_county_entry.py','r08_writer_common_adapter.py',
                 'ordinary_save_contract.py','r08_writer_one_day.py'):
        source=OLD/'tools/ck3_mod_acceptance_cases'/name;target=OUT/'tools/ck3_mod_acceptance_cases'/name
        write(target,source.read_bytes());rows.append({'role':'unchanged shared same-client collection/cleanup','source':pin(source),'copy':pin(target)})
    maps=[('pointer_read_public_models.py','postload_public_models.py'),
          ('r08_parent_pointer_read_controller.py','r08_parent_postload_controller.py'),
          ('r08_parent_pointer_read_one_day.py','r08_parent_postload_one_day.py')]
    for old,new in maps:
        source=OLD/'revision-a02'/old
        text=source.read_text()
        replacements=[('pointer_read_public_models','postload_public_models'),
            ('r08_parent_pointer_read_controller','r08_parent_postload_controller'),
            ('r08_parent_pointer_read_one_day','r08_parent_postload_one_day'),
            ('parent_pointer_read_contract','parent_postload_contract'),
            ('pointer_read_models','postload_models'),('pointer_read_wire','postload_wire'),
            ('player-parent-pointer-read-once-v1','player-parent-postload-execution-once-v1'),
            ('xar.maintenance.parent_pointer_read.raw.v2','xar.maintenance.parent_postload.raw.v1'),
            ('xar.e04.pointer-read.public-source-bundle.v2','xar.e04.postload.public-source-bundle.v1'),
            ('xar.maintenance.parent_pointer_read.binding.v2','xar.maintenance.parent_postload.binding.v1'),
            ('xar.maintenance.parent_pointer_read.root-scope.v1','xar.maintenance.parent_postload.root-scope.v1'),
            ('r08_parent_pointer_read_one_day','r08_parent_postload_one_day'),
            ('post_parent_pointer_read','parent_postload_execution'),('target_post_read_qualified','target_postload_qualified'),
            ('xar.maintenance.parent_pointer_read.result.v1','xar.maintenance.parent_postload.result.v1'),
            ('r08-pointer','r08-postload'),('R08-PARENT','R08-POSTLOAD'),
            ('PARENT-POINTER-READ','PARENT-POSTLOAD'),('prepare_parent_pointer_read_admission.py','prepare_parent_postload_admission.py'),
            ('--prepare-parent-pointer-read','--prepare-parent-postload'),
            ('consume_parent_pointer_read_actual.py','consume_parent_postload_actual.py'),
            ('--enable-ck3-12004-player-pointer-read','--enable-ck3-12004-parent-postload-once'),
            ('--explicit-player-pointer-readwatch-v1','--explicit-postload-execution-breakpoint-v1'),
            ('readwatch_authorized','postload_execution_authorized')]
        for a,b in replacements:text=text.replace(a,b)
        if new=='postload_public_models.py':
            start=text.index('CORE_NAMES = ');end=text.index('\n\n\n',start)
            text=text[:start]+"CORE_NAMES = frozenset({'postload_wire.py','postload_models.py','postload_owner_binding.py',\n 'parent_postload_contract.py','postload_admission.py','prepare_parent_postload_admission.py',\n 'consume_parent_postload_actual.py'})"+text[end:]
        elif new=='r08_parent_postload_controller.py':
            text=text.replace("binding.expected['watch_address']","binding.expected['post_pc']")
            text=text.replace("saved[5] | 0xb0001","saved[5] | 1")
            text=text.replace("postload_execution_authorized') is True", "postload_execution_authorized') is True")
            text=text.replace("and 0 < (expires-issued).total_seconds() <= 300", "and 0 < (expires-issued).total_seconds() <= 30")
            text=text.replace("qualification: FilePin, observer: FilePin, output: Path)","qualification: FilePin, observer: FilePin, bundle_index: FilePin, output: Path)")
            text=text.replace("'--observer',observer['path'],'--output-root'", "'--observer',observer['path'],'--bundle-index',bundle_index['path'],'--output-root'")
        else:
            start=text.index("    q = read_pin(cfg.qualification_pin)");end=text.index('    return cfg',start)
            text=text[:start]+"    from postload_admission import validate_qualification\n    validate_qualification(read_pin(cfg.qualification_pin),observer=cfg.observer_pin,typed_root=cfg.parent_tools)\n"+text[end:]
            text=text.replace("cfg.qualification_pin,cfg.observer_pin,control)","cfg.qualification_pin,cfg.observer_pin,cfg.bundle_index_pin,control)")
            text=text.replace("'reconstructed_arguments_basis':'preserved post-read registers, not entry atomic raw'", "'reconstructed_arguments_basis':'post-load RCX/R8/R9 and RBP; RDX may be null; no entry atomic or return evidence'")
            text=text.replace("'created':collected.created", "'created':str(collected.created)")
        target=OUT/'tools/ck3_mod_acceptance_cases'/new
        write(target,text.encode());rows.append({'role':'new postload semantic fork of shared lifecycle','source':pin(source),'copy':pin(target)})
    loader=(OLD/'tools/ck3_mod_acceptance_cases/pointer_read_bundle_loader.py').read_text()
    loader=loader.replace("('pointer_read_wire','pointer_read_models','pointer_read_admission_models','pointer_read_owner_binding','parent_pointer_read_contract')",
        "('postload_wire','postload_models','postload_owner_binding','parent_postload_contract','postload_admission')")
    for a,b in [('pointer_read_public_models','postload_public_models'),('r08_parent_pointer_read_controller','r08_parent_postload_controller'),
        ('r08_parent_pointer_read_one_day','r08_parent_postload_one_day'),('pointer_read_bundle_loader','postload_bundle_loader'),
        ('xar.e04.pointer-read.public-source-bundle.v2','xar.e04.postload.public-source-bundle.v1')]:loader=loader.replace(a,b)
    write(OUT/'tools/ck3_mod_acceptance_cases/postload_bundle_loader.py',loader.encode())
    report={'schema':'xar.e04.postload.public-source-inputs.v1','machine_id':'desktop-3fevhd2-1c74096080',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'copies':rows,
        'qualified':False,'native_game_sdk_steam':False,'legacy_Q_reused':False}
    write(ROOT/'SOURCE-INPUTS.actual-a01.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),'sources':len(rows)}))

if __name__=='__main__':main()
