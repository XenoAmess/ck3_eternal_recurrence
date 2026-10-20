"""Finite C23 preparation. Initial quote is RAM-only; no Game or Task run."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path('Z:/ck3_mod_rewrite')
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
P = N/'p51-fresh1066-v20261019-prepare01'
T = N/'robert30-v20261019-campaign01/runtime'
O = P/'c23-source23-native30-cold100'
B = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01')
M = 'xenoamess-full-tower-eb9d2c1186'
TOOLS = REPO/'tools/g2_saved_campaign'


def ref(path, size, digest):
    return {'path': str(path), 'bytes': size, 'sha256': digest}


ANCHOR = ref(REPO/'_runtime/source24-integration16/SOURCE24-CANONICAL-ANCHOR.json',6269,'fb4f7ef4933d7e86f82b81e0824332a92f49ae5562c8337460b87efb8031a8f8')
FREEZE = ref(T/'ROOT-FINAL-SDK-FREEZE-P37C23.json',461440,'a45c3948085ae56bb66665e17dd5888cc88ce37d7449a27736cd81362df15338')
BASE_FREEZE = ref(T/'ROOT-FINAL-SDK-FREEZE-P37C22.json',449181,'07fe7edd6bf76cf7a3c2c438de9d13178ced61c00f1d701b748745f4bc33e443')
BASE_NATIVE = ref(T/'ROOT-NATIVE29-NATIVE-PIN-C16.json',4546,'8ace8deb48058b1043374ee49b4be3249359f75123cf236907e43067bbfc1e5b')
EXPORT_CARD = ref(B/'SOURCE24-COMBINED21MiB-NATIVE30-EXACT-EXPORTER-ADMITTED01.json',12850,'d292e9efc7c28f20190b7d3d9b74fbb330bc87f7f154b49c9756193c708cc23f')
FRONTIER = ref(P/'c22-source22-warm99/C22-WARM-ABORT-CLOSED99.json',9089,'312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce')
LEGACY = ref(P/'c22-source22-warm99/post-close/STORAGE-ADMISSION-before-C22.json',29740,'60d4c4be84314f5c953c29fffa51e0d22857b1f7d211e5bae956c11835de3822')
INPUT = ref(B/'CURRENT-FULL-HOLDS-CANONICAL-INPUT-ACCOUNT63-SOURCE24-FINAL02.json',5959,'02566da0804e2a7745c6ae8f08a13771499aecb1bf7a9beaed35ecf6e08456fe')
POLICY = ref(REPO/'docs/storage-retention-policy.json',4022,'ca60e36bef8e59ffafa939689a6ba4106420f20b7c2db19a1199d6408b3131e5')
PREPARE_CARD = ref(B/'C23-SOURCE24-NATIVE30-PHASEA-EXACT-COLD-PREPARE-ADMITTED02.json',20287,'9c422fa87618182f5650a2afcf1c453a79054a9babe7d9977763a3aba45f5040')
PRODUCERS = {
    'controls': ref(TOOLS/'prepare_c23_full_enabled_cold_controls_v1.py',29500,'423706af13d8565332b8ed6e50e5d29b107666e54aac607d2e44afba70b8e0d9'),
    'display': ref(TOOLS/'prepare_c23_display_capture_amendment_v1.py',7983,'7a1d787116f08b2a51bc4c16d158f8c08ec7f4f7f7f9276c4a80ef173a76a5b4'),
    'feeder': ref(TOOLS/'prepare_c23_cold_feeder_v1.py',25270,'dc73df297ec1337af76b7a79fe2f8da3e18955260a7eb1b9a35253bebcd1e146'),
    'canonical': ref(TOOLS/'storage_canonical_compat_v1.py',12424,'53d7f02c05ebe39885de54e6b36e4e16abd2bacda5f1f32415c6075b4fadc552'),
    'native': ref(REPO/'_runtime/prepare_c23_native_binding100.py',7355,'5a1fbdbeeffe09cf916c3d299971357a267215eee64e649c05f98ea50633941e'),
}


def require(ok, why):
    if not ok:
        raise ValueError('C23 finite prepare denied: '+why)


def raw_checked(row, limit=2097152):
    require(isinstance(row,dict) and type(row.get('path')) is str
            and Path(row['path']).is_absolute() and type(row.get('bytes')) is int
            and 0 < row['bytes'] <= limit, 'bounded exact reference required')
    with Path(row['path']).open('rb') as stream:
        raw = stream.read(limit+1)
    require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row.get('sha256'),
            'frozen metadata/source identity differs: '+row['path'])
    return raw


def document(row):
    value = json.loads(raw_checked(row))
    require(isinstance(value,dict), 'JSON object required')
    return value


def load(kind):
    row = PRODUCERS[kind]
    raw = raw_checked(row,131072)
    name = '_C23_frozen_prepare_'+kind
    spec = importlib.util.spec_from_file_location(name,row['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw,row['path'],'exec'),module.__dict__)
    return module


def utc():
    return datetime.now(timezone.utc).isoformat()


def source_graphs(*, include_feeder=True):
    freeze, anchor = document(FREEZE), document(ANCHOR)
    require(freeze.get('machine_id') == anchor.get('machine_id') == M
            and freeze.get('business_source_commit') == anchor.get('commit')
            == '6b55531b1d3a44ee73ab13ea40132556030f682e', 'actual Source24 authority required')
    controls, control_report = load('controls').build_sources(
        native_transition_inputs={'base_freeze_ref':BASE_FREEZE,'base_native_ref':BASE_NATIVE,
                                  'capacity_ref':EXPORT_CARD,'machine_id':M},
        business_anchor_ref=ANCHOR,frontier_ref=FRONTIER,full_timing=True)
    display, review_raw, display_report = load('display').plan(
        T,T,P/'c23-display-source100',generation='C23',machine_id=M)
    feeder, feeder_report = load('feeder').build_sources() if include_feeder else ({},{})
    require(len(controls) == len(display) == 18 and len(feeder) == (3 if include_feeder else 0),
            'complete independently reviewed source graphs required')
    require(sum(map(len,controls.values())) == 518277
            and sum(map(len,display.values())) == 278733
            and sum(map(len,feeder.values())) == (79153 if include_feeder else 0),
            'final logical source totals differ')
    require(len(review_raw) == 16330 and hashlib.sha256(review_raw).hexdigest()
            == '85afefbcd5f1898300cd6a3c2a1d26a168acbc4ed65760dce8a3ee2246ff7d6e',
            'independent display source review differs')
    require(not(set(controls)&set(display) or set(controls)&set(feeder) or set(display)&set(feeder)),
            'generated graphs must have no overlapping targets')
    return controls,display,feeder,review_raw,(control_report,display_report,feeder_report)


def storage_bytes():
    producer = load('canonical')
    raw = producer.compose_canonical_storage_v1(raw_checked(LEGACY),raw_checked(INPUT),
        legacy_pin=LEGACY,coordinator_pin=INPUT,policy_raw=raw_checked(POLICY),now_utc=utc())
    require(len(raw) == 26981 and hashlib.sha256(raw).hexdigest()
            == 'ddf5efc4436b9ef1a45dd3e83eaa871bc008d7bdef04cdf43aba59d37b8ec1cc',
            'Root final full-holds canonical bytes differ')
    return raw


def quote():
    controls,display,feeder,review_raw,reports = source_graphs()
    canonical = storage_bytes()
    compat = load('canonical')
    binding = compat.storage_binding_v1(canonical,canonical_path=str(O/'STORAGE-CANONICAL-FULL-C23.json'))
    review = json.loads(canonical)['review_at_utc']
    compatibility = compat.validate_new_bundle_v1(canonical,
        canonical_path=str(O/'STORAGE-CANONICAL-FULL-C23.json'),profile_storage=binding,
        job_storage=binding,launch_review=review,keeper_review=review)
    names = [str(T/name) for graph in (controls,display,feeder) for name in graph]
    require(all(not Path(name).exists() for name in names), 'source installation is create-only, no retry')
    return {'machine_id':M,'observed_at_utc':utc(),'status':'RAM_QUOTE_NO_OUTPUTS_CREATED',
            'source_control_bytes':sum(map(len,controls.values())),
            'source_display_bytes':sum(map(len,display.values())),
            'source_feeder_bytes':sum(map(len,feeder.values())),
            'display_review_bytes':len(review_raw),'full_storage_bytes':len(canonical),
            'future_profile_job_binding_fixture':compatibility,
            'new_source_files':len(names),'all_source_targets_absent':True,
            'runtime_component_upper':2727936,'Game_Task_OBS_RPC_calls':0,
            'business_anchor':ANCHOR,'sdk_freeze':FREEZE,'full_holds_input':INPUT,
            'source_producers':PRODUCERS}


def pinned(path):
    path = Path(path)
    raw = path.read_bytes()
    return ref(path,len(raw),hashlib.sha256(raw).hexdigest())


def new_file(path, raw):
    path = Path(path)
    require(path.resolve().is_relative_to(T) or path.resolve().is_relative_to(O)
            or path.resolve().is_relative_to(P/'c23-display-source100'), 'finite output root')
    require(type(raw) is bytes, 'exact bytes required')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        __import__('os').fsync(stream.fileno())
    result = pinned(path)
    require(result['bytes'] == len(raw) and result['sha256'] == hashlib.sha256(raw).hexdigest(),
            'new file readback differs; do not retry')
    return result


def new_json(path, value):
    return new_file(path,json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8'))


def prepare_card():
    card = document(PREPARE_CARD)
    require(card.get('status') == 'ADMITTED' and card.get('machine_id') == M
            and card.get('source24_commit') == '6b55531b1d3a44ee73ab13ea40132556030f682e',
            'exact phaseA authority required')
    deadline = datetime.fromisoformat(card['review_at_utc'].replace('Z','+00:00'))
    require(deadline.tzinfo is not None and datetime.now(timezone.utc) < deadline,
            'phaseA review expired')
    require(T in map(Path,card['approved_output_roots'])
            and O in map(Path,card['approved_output_roots']), 'phaseA exact roots required')
    disk = __import__('shutil').disk_usage(T)
    full = json.loads(storage_bytes())
    require(disk.free > card['disk_reserve_bytes']
            and disk.free > full['disk_reserve_bytes']
            and disk.used + full['retained_other_reservations'] <= full['effective_project_quota'],
            'original supervisor full-schema capacity predicate failed')
    return card


def install_sources():
    card = prepare_card()
    controls,display,_,review_raw,_ = source_graphs(include_feeder=False)
    expected = {str(Path(row['path']).resolve()):row for row in card['source_singlecopy_targets']}
    values = {T/name:raw for graph in (controls,display) for name,raw in graph.items()}
    require(len(expected) == len(values) == 36, 'phaseA has exactly 36 control/display targets')
    for path,raw in values.items():
        row = expected.get(str(path.resolve()))
        require(row is not None and row['bytes'] == len(raw)
                and row['sha256'] == hashlib.sha256(raw).hexdigest(), 'card source pin differs')
    native_raw,native_report = load('native').compose(capacity_ref=PREPARE_CARD,observed_at_utc=utc())
    values[T/'ROOT-NATIVE30-NATIVE-PIN-C23.json'] = native_raw
    values[P/'c23-display-source100/REVIEW.json'] = review_raw
    values[O/'prepare-cold100.py'] = Path(__file__).read_bytes()
    output = O/'CONTROL-SOURCES-PREPARED-C23.json'
    require(all(not path.exists() for path in (*values,output)), 'create-only phaseA source installation; no retry')
    pins = [new_file(path,raw) for path,raw in values.items()]
    return new_json(output,{'machine_id':M,'observed_at_utc':utc(),'status':'SOURCE_AND_COMPILED_SESSION_PREPARED_NOT_RUNTIME',
        'capacity':PREPARE_CARD,'sources':pins,'source_control_bytes':518277,
        'source_display_bytes':278733,'display_review_bytes':16330,
        'native_session':native_report,'feeder_sources_installed':False,
        'Game_Task_OBS_RPC_calls':0,'unknown_on_partial_failure_no_retry':True})


def adopt_canonical():
    card = prepare_card()
    row = card['canonical']
    immutable, archive, current = map(Path,(row['immutable_target'],row['legacy_archive'],row['CAS_target']))
    require(immutable == O/'STORAGE-CANONICAL-FULL-C23.json'
            and archive == O/'post-close/STORAGE-ADMISSION-before-C23.json'
            and current == T/'STORAGE-ADMISSION.json', 'exact canonical paths required')
    raw = storage_bytes()
    old = raw_checked(row['legacy_actual_current'],32768)
    oldstat = current.stat()
    output = O/'STORAGE-CANONICAL-ADOPTED-C23.json'
    temporary = T/'STORAGE-ADMISSION-C23.pending.json'
    require(all(not path.exists() for path in (immutable,archive,output,temporary)),
            'canonical adoption is create-only and cannot be retried')
    immutable_ref = new_file(immutable,raw)
    archive_ref = new_file(archive,old)
    new_file(temporary,raw)
    live = current.stat()
    require((live.st_dev,live.st_ino,live.st_mtime_ns,live.st_size)
            == (oldstat.st_dev,oldstat.st_ino,oldstat.st_mtime_ns,oldstat.st_size)
            and current.read_bytes() == old,'canonical FileID/raw CAS differs; stop without replace')
    __import__('os').replace(temporary,current)
    current_ref = pinned(current)
    require(current_ref['bytes'] == immutable_ref['bytes'] and current_ref['sha256'] == immutable_ref['sha256'],
            'canonical readback differs; preserve unknown, no retry')
    return new_json(output,{'machine_id':M,'observed_at_utc':utc(),'status':'FULL_CANONICAL_ADOPTED_NO_RUNTIME',
        'capacity':PREPARE_CARD,'coordinator':INPUT,'immutable_fullview':immutable_ref,
        'original_current_file_id':oldstat.st_ino,'old_raw_archive':archive_ref,'canonical':current_ref,
        'separate_files_transaction_not_claimed_atomic':True,'Game_Task_OBS_RPC_calls':0})


if __name__ == '__main__':
    require(len(sys.argv) == 2 and sys.argv[1] in ('quote','install','canonical'), 'explicit finite phase required')
    value = {'quote':quote,'install':install_sources,'canonical':adopt_canonical}[sys.argv[1]]()
    print(json.dumps(value,ensure_ascii=True))
