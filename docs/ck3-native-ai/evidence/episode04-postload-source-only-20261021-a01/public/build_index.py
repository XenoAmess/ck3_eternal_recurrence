"""Finite source bundle/template only. No Q, identity, owner or runtime is invented."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CANDIDATE=ROOT/'candidate'

def pin(path: Path) -> dict[str,object]:
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def main() -> None:
    tools=CANDIDATE/'native-tools';cases=CANDIDATE/'tools/ck3_mod_acceptance_cases'
    names=('postload_wire','postload_models','postload_owner_binding','parent_postload_contract','postload_admission')
    public=('r04_county_entry_window','r04_county_entry','r08_writer_common_adapter','ordinary_save_contract',
        'r08_writer_one_day','postload_public_models','r08_parent_postload_controller','r08_parent_postload_one_day',
        'r10_prepare_adapter','r08_postload_adapter','postload_bundle_loader')
    modules={name:str((tools/(name+'.py')).resolve()) for name in names}
    modules.update({name:str((cases/(name+'.py')).resolve()) for name in public})
    paths=sorted(CANDIDATE.rglob('*.py'))+[cases/'r08_postload.json']
    # These are actual import locations of the unchanged public runtime helpers,
    # not a claim that the complete runtime transitive closure was reassembled.
    base=Path('D:/workspace/ck3_eternal_recurrence')
    paths += [base/'tools/ck3_live_run_id.py',
        base/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py',
        base/'ck3_autonomous_player/src/xar_autoplayer/bridge/exact_one_day_postcondition.py']
    index={'schema':'xar.e04.postload.public-source-bundle.v1','files':[pin(path) for path in paths],'modules':modules}
    target=ROOT/'PUBLIC-SOURCE-INDEX.prepared-a04.json'
    target.write_text(json.dumps(index,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    template={'schema':'xar.e04.postload.source-only-input-template.v1',
        'machine_id':'desktop-3fevhd2-1c74096080','observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'case_inputs':{'r08_parent_postload_one_day':{'bundle_index_pin':pin(target),
            'qualification_pin':None,'observer_pin':None,'root_scope_path':'PENDING_ACTUAL_RUN_SCOPE',
            'actor_id':33388,'expected_start_date_raw':53149056,'parent_tools':str(tools.resolve()),
            'prefix':'r08-postload-PENDING','deadline_utc':'PENDING_NEW_LIVE_PURPOSE',
            'payment_enable_once_authorized':False,'natural_phase_enable_once_authorized':False}},
        'actual_Q_absent_default_refusal':True,'Game_or_Steam_or_observer_execution_admitted':False,
        'complete_runtime_frozen_files_still_required':True,'planner_autoload':False}
    (ROOT/'CASE-INPUTS.source-only-template-a04.json').write_text(json.dumps(template,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index':pin(target),'source_bytes':sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())}))

if __name__=='__main__':main()
