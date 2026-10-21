from __future__ import annotations
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
N = ROOT.parent
W = Path('C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree')
BASE = 'f7afb648f330d3a0d9d15861db0e68215b764f05'
ACTUAL_BASE = '992ca426939c19dcb62375344fc4a230e86a38f1'
PLAN = N/'EXACT-PUBLICATION-COPYPLAN.prepared-a03.json'
PLAN_SHA = '47393081bbe0b3adb08076f8df7552baf32ee204daa00550172d382614e50a2f'
R13 = Path('C:/ck3-e04-resume-20261020-a01/r13-r176-continuous-review-0230-a01')
ADJ = R13/'ROOT-R0176-R13-FORMAL-ADJUDICATION.actual-a01.json'
ADJ_SHA = 'cbfcdfdffb377a3aec38ee256ec88b0b122eb28a7e78c6203f6dc7630fcb9d03'
PROJECTION = N/'ROOT-POSTLOAD-SOURCE-ONLY-ADOPTION.actual-a01.json'
PROJECTION_SHA = '5fad2634e14c9eccb505628449a93cd1223b42d2f85a19a6bfb728ba26441cb3'
ARCHIVE = 'promo/ck3_native_war_ai/episode-04-march-logistics/review02/r0176-r13-positive-review-a01'
ROOT_REL = ARCHIVE+'/'+ADJ.name
PROJECTION_REL = 'docs/ck3-native-ai/evidence/episode04-postload-source-only-20261021-a01/provenance/'+PROJECTION.name
TOPIC = 'docs/ck3-native-ai/episode04-r13-locked-reroute-r0176-12004.md'
LEDGER = 'promo/ck3_native_war_ai/episode-04-march-logistics/review02/r0175-r12-positive-review-a01/formal-dynamic-theme-ledger.json'
OVERVIEWS = ['docs/ck3-native-ai/episode04-gameplay-agent-use-12004.md',
             'docs/ck3-native-ai/episode04-current-execution-map-12004.md',
             'docs/handover/2026-10-20-war-episode04-vacation-handover.md']
Data = dict[str, object]

def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)

def mapping(value: object) -> Data:
    need(isinstance(value,dict),'Expected JSON object')
    result: Data = {}
    if isinstance(value,dict):
        for key,item in value.items():
            need(isinstance(key,str),'JSON key must be text')
            if isinstance(key,str):
                result[key]=item
    return result

def objects(value: object) -> list[Data]:
    need(isinstance(value,list),'Expected object list')
    return [mapping(item) for item in value] if isinstance(value,list) else []

def decoded(body: bytes) -> Data:
    value: object=json.loads(body)
    return mapping(value)

def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()

def wire(body: bytes) -> Data:
    return dict(bytes=len(body),sha256=digest(body))

def encoded(row: Data) -> bytes:
    return (json.dumps(row,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def git_read(relative: str, commit: str = BASE) -> bytes:
    argv=['git','--no-optional-locks','--no-lazy-fetch','-c','gc.auto=0',
          '-c','maintenance.auto=false','show',commit+':'+relative]
    done: subprocess.CompletedProcess[bytes]=subprocess.run(argv,cwd=W,capture_output=True,
        timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    need(done.returncode==0,'Exact local Git object unavailable: '+relative)
    return done.stdout

def block(name: str, relative: str) -> str:
    source=(ROOT/name).read_text(encoding='utf-8')
    prefix='../../' if relative.startswith('docs/') else ''
    topic='episode04-r13-locked-reroute-r0176-12004.md'
    projection='evidence/episode04-postload-source-only-20261021-a01/provenance/'+PROJECTION.name
    rule='episode04-r08-player-parent-opportunity-input-contract-12004.md'
    if relative.startswith('docs/handover/'):
        topic='../ck3-native-ai/'+topic
        projection='../ck3-native-ai/'+projection
        rule='../ck3-native-ai/'+rule
    source=source.replace('@R13_ROOT@',prefix+ROOT_REL).replace('@R13_TOPIC@',topic).replace('@SOURCE_ONLY@',projection).replace('@PARENT_RULE@',rule)
    need('@R13_' not in source and '@SOURCE_' not in source and '@PARENT_' not in source,'Unresolved document link')
    return source

def ledger_after(before: bytes, decision: Data) -> bytes:
    row=decoded(before)
    need(type(row.get('accepted_count')) is int and row['accepted_count']==7,'Expected exact current7 ledger')
    need(row.get('machine_id')==decision.get('machine_id'),'Machine differs')
    prior=decoded(before)
    themes=objects(row.get('themes'))
    r13=[item for item in themes if item.get('theme')=='R13']
    need(len(r13)==1 and r13[0].get('status')=='pending_accepted_original_M_source_shot','R13 no longer pending')
    r13[0]['status']='accepted_original_M_positive_source_shot'
    r13[0]['accepted_shots']=[dict(run='R0176',span_seconds_half_open=[0,30],
        span_frames_half_open=[0,900],source_fps=30,source_time_base='1/1000',
        last_selected_PTS_ms=29967,Root_decision_repository_relative_path=ROOT_REL,
        native_army_id=18,native_actor_id=31254,native_lock_progress=95108,
        native_lock_cutoff=50000,native_old_front=8653,native_new_target=8645,
        native_final_alternate_arrival_confirmed=True,alternate_endpoint_within_selected_clip=False,
        visible_suffix_change_seconds_open_closed=[4,10],
        visible_front_direction_change_seconds_open_closed=[10,20],
        exact_native_event_encoded_PTS=None,AI_all_contact_sheets=57,AI_actual_valid_cells=900,
        Root_contact_sheets_actually_viewed=[0,7,18,37,56],Root_valid_contact_cells_actually_viewed=68,
        human_1x=False,human_signoff=False)]
    accepted=[item['theme'] for item in themes if item.get('status')=='accepted_original_M_positive_source_shot']
    pending=[item['theme'] for item in themes if item.get('status')=='pending_accepted_original_M_source_shot']
    need(accepted==['R03','R04','R06','R07','R09','R11','R12','R13'],'Unexpected accepted themes')
    need(pending==['R05','R08','R10'],'Unexpected remaining themes')
    root_pin=dict(repository_relative_path=ROOT_REL,bytes=4850,sha256=ADJ_SHA)
    row.update(observed_at_utc=decision['observed_at_utc'],themes=themes,accepted_count=8,
        percentage=8/11*100,current_Root_decision=root_pin,full_R13_variant_film_qualified=False,
        R13_alternate_endpoint_in_selected_clip=False,historical_R0176_cleanup_accepted=False)
    history=objects(row.get('history'))
    history.append(dict(observed_at_utc=decision['observed_at_utc'],accepted_count=8,
        accepted_themes=accepted,previous_ledger_sha256=digest(before),Root_decision=root_pin))
    row['history']=history
    decisions=objects(row.get('Root_decisions'))
    need(not any(item.get('sha256')==ADJ_SHA for item in decisions),'R13 already counted')
    row['Root_decisions']=decisions+[root_pin]
    limits=row.get('explicit_limits')
    need(isinstance(limits,list) and len(limits)>=4,'Existing limits differ')
    if isinstance(limits,list):
        old_words=[limits[2],limits[3]]
        limits[2]='The R0175/R12 source gives no R13 credit; R13 is credited only by separately adjudicated R0176 [0,30). No finished chapter/full film/human1x/signoff/OneDrive credit.'
        limits[3]='This derived ledger update performs no media copy/hash/decode/render. Separate R0176 one-pass900-frame extraction and Root independent raw hash are bound by its receipt; retained full-raw QA reused.'
        limits.append('R0176/R13 only original-M three-state [0,30)/900 frames; alternate endpoint outside45s raw, exact native event encodedPTS null, no all-variants/wholecase/historical-cleanup/human1x/final-film credit.')
        row['scope_wording_history']=[dict(observed_at_utc=decision['observed_at_utc'],
            previous_ledger_sha256=digest(before),old_R12_scoped_limit_wording=old_words)]
    row['R13_evidence_retention']=decision['retention']
    need(row['unchanged_counters']==prior['unchanged_counters'],'Other counters changed')
    need(row['evidence_retention']==prior['evidence_retention'],'Old protection automatically renewed')
    need([item for item in themes if item.get('theme')!='R13']==
         [item for item in objects(prior['themes']) if item.get('theme')!='R13'],'Other theme modified')
    need(history[:-1]==objects(prior['history']),'Old signing history changed')
    body=encoded(row)
    need(decoded(body)==row,'Ledger serialization differs')
    return body

def main() -> None:
    need(digest(PLAN.read_bytes())==PLAN_SHA,'Frozen publisher plan changed')
    need(digest(ADJ.read_bytes())==ADJ_SHA,'Root R13 decision changed')
    need(digest(PROJECTION.read_bytes())==PROJECTION_SHA,'Root source-only projection changed')
    decision=decoded(ADJ.read_bytes())
    need(decision.get('decision')=='ACCEPT_R13_LIMITED_FORMAL_THREE_STATE_SHOT','Unexpected adjudication')
    plan=decoded(PLAN.read_bytes())
    items=objects(plan.get('items'))
    before: dict[str,bytes]={TOPIC:git_read(TOPIC),LEDGER:git_read(LEDGER)}
    base_refs: list[Data]=[dict(target=relative,source_kind='exact_fixed_Git_object',
        git_commit=BASE,**wire(body)) for relative,body in before.items()]
    for relative in OVERVIEWS:
        matches=[item for item in items if item.get('target')==relative]
        need(len(matches)==1,'Publisher target not unique')
        item=matches[0]
        source=item.get('source')
        need(isinstance(source,str),'Publisher source path missing')
        if not isinstance(source,str):
            raise ValueError('Source must be string')
        body=Path(source).read_bytes()
        need(len(body)==item.get('bytes') and digest(body)==item.get('sha256'),'Expected firstbatch source changed')
        before[relative]=body
        base_refs.append(dict(target=relative,source_kind='expected_firstbatch_source_row',
            source=source,publisher_plan_sha256=PLAN_SHA,**wire(body)))
    for relative,body in before.items():
        need(git_read(relative,ACTUAL_BASE)==body,'Actual firstbatch preimage differs: '+relative)
    after: dict[str,bytes]={LEDGER:ledger_after(before[LEDGER],decision)}
    after[TOPIC]=before[TOPIC]+('\n'+block('R13-APPEND.source.md',TOPIC)).encode('utf-8')
    for relative in OVERVIEWS:
        old=before[relative]
        first,tail=old.split(b'\n',1)
        after[relative]=first+b'\n\n'+block('SNAPSHOT.source.md',relative).encode('utf-8')+b'\n'+tail
        need(after[relative].endswith(tail),'Prior snapshot bytes not preserved')
        need(b'01:17' in old and b'01:17' in after[relative],'Expected01:17 snapshot missing')
    need(after[TOPIC].startswith(before[TOPIC]),'Old R0176 topic changed')
    patch=''.join(''.join(difflib.unified_diff(before[relative].decode('utf-8').splitlines(True),
        body.decode('utf-8').splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
        for relative,body in after.items()).encode('utf-8')
    current=sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())
    need(current+sum(len(body) for body in after.values())+len(patch)+16384<=262144,'Candidate peak exceeds256KiB')
    candidate_refs: list[Data]=[]
    for relative,body in after.items():
        path=ROOT/'candidates'/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:
            stream.write(body)
        candidate_refs.append(dict(target=relative,source=str(path),**wire(body)))
    with (ROOT/'media-ledger.patch').open('xb') as stream:
        stream.write(patch)
    manifest=dict(schema='xar.E04.R13.formal8.expected-preimage-candidates.v1',
        machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        actual_base_commit=ACTUAL_BASE,expected_preimage_after_firstbatch=False,
        all_five_actual_firstbatch_preimages_byte_equal=True,prior_fixed_Git_commit=BASE,
        publisher_plan=dict(path=str(PLAN),**wire(PLAN.read_bytes())),expected_preimages=base_refs,
        candidates=candidate_refs,Root_R13_decision=dict(path=str(ADJ),**wire(ADJ.read_bytes())),
        Root_source_only_projection=dict(path=str(PROJECTION),repository_relative_path=PROJECTION_REL,**wire(PROJECTION.read_bytes())),
        patch=dict(path=str(ROOT/'media-ledger.patch'),**wire(patch)),
        apply_rule='All five actual992ca preimages verified byte-exact. Publisher must preserve these preimages at apply; concurrent mismatch stops for adaptation, no upstream overwrite.',
        checks=dict(five_candidates=True,prior_snapshot_bytes_preserved=True,other_themes_and_counters_preserved=True,
            no_old_retention_renewal=True,accepted=8,total=11,pending=['R05','R08','R10'],Root_human1x=False),
        Git_mutations=0,raw_body_reads_or_new_media=0,old_closed_roots_written=False)
    with (ROOT/'CANDIDATE-MANIFEST.actual-a01.json').open('xb') as stream:
        stream.write(encoded(manifest))
    print(json.dumps(dict(manifest=wire((ROOT/'CANDIDATE-MANIFEST.actual-a01.json').read_bytes()),
        candidate_bytes=sum(len(body) for body in after.values()),patch_bytes=len(patch),
        aggregate=sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file()),
        actual_base_commit=ACTUAL_BASE,all_five_preimages_byte_equal=True)))

if __name__=='__main__':
    main()
