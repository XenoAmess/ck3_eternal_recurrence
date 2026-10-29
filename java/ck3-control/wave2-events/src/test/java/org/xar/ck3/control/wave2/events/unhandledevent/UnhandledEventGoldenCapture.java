package org.xar.ck3.control.wave2.events.unhandledevent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** One-time original producer capture; no Game, transport, or production writer ownership. */
public final class UnhandledEventGoldenCapture {
    private UnhandledEventGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3 && arguments.length != 6) throw new IllegalArgumentException("repository python-executable new-output-file [verified-stock-game-root pinned-stock-input-manifest fixed-cohort]");
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path python = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (!Files.isDirectory(root) || !Files.isRegularFile(python) || Files.exists(output)) throw new IllegalArgumentException("capture paths");
        Files.createDirectories(output.getParent());
        String machine = new String(run(List.of(python.toString(), root.resolve("tools/ck3_live_run_id.py").toString(), "machine"),
            root, output.resolveSibling(output.getFileName() + ".machine.stderr"), 4096, new byte[0]), StandardCharsets.UTF_8).strip();
        if (!machine.matches("[A-Za-z0-9][A-Za-z0-9._-]{3,127}")) throw new IllegalStateException("machine identity unavailable");
        boolean sourceReview = arguments.length == 6;
        List<String> producer = sourceReview ? List.of(python.toString(), "-", root.toString(), machine,
                Path.of(arguments[3]).toAbsolutePath().normalize().toString(), Path.of(arguments[4]).toAbsolutePath().normalize().toString(), arguments[5])
            : List.of(python.toString(), "-", root.toString(), machine);
        if (sourceReview && (!Files.isDirectory(Path.of(arguments[3])) || !Files.isRegularFile(Path.of(arguments[4]))
                || Files.size(Path.of(arguments[4])) > 16_384)) throw new IllegalArgumentException("actual stock game root and bounded input manifest required; source review NOT RUN");
        byte[] golden = run(producer, root,
            output.resolveSibling(output.getFileName() + ".producer.stderr"), 65_536, (sourceReview ? SOURCE_REVIEW_CAPTURE : CAPTURE).getBytes(StandardCharsets.UTF_8));
        Files.write(output, golden, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + golden.length + " bytes on " + machine);
    }
    private static byte[] run(List<String> command, Path root, Path errors, int maximum, byte[] standardInput) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command).directory(root.toFile()).redirectError(errors.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
        Process process = builder.start();
        FutureTask<byte[]> reading = new FutureTask<>(() -> process.getInputStream().readNBytes(maximum + 1));
        Thread.startVirtualThread(reading);
        try {
            try (var input = process.getOutputStream()) { input.write(standardInput); }
            if (!process.waitFor(90, TimeUnit.SECONDS)) throw new IOException("original capture timed out");
            byte[] bytes = reading.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || bytes.length > maximum) throw new IOException("original producer capture rejected: " + process.exitValue());
            return bytes;
        } catch (ExecutionException | TimeoutException error) { throw new IOException("capture output unavailable", error); }
        finally { if (process.isAlive()) process.destroyForcibly(); reading.cancel(true); }
    }
    private static final String CAPTURE = """
from pathlib import Path
from datetime import datetime, timezone
import copy, gzip, hashlib, inspect, json, sys, tempfile
root, machine = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
import test_unhandled_event_fallback as fixture
from xar_autoplayer.vanilla_events import unhandled_fallback as original
from xar_autoplayer.bridge.driver import BridgeUnavailableError
base_snapshot, base_context, base_actions = inspect.unwrap(fixture.event_case)()
cases=[]
def make_request(snapshot, context, actions, summary=None, registry=None):
    return {'schema':'xar.ck3.unhandled-event-plan-input/v1','snapshot':snapshot,'event_context':context,
        'event_summary':{'instance_id':41} if summary is None else summary,
        'registry_decision':{'status':'not_registered','unavailable_reason':'synthetic-uncovered-card'} if registry is None else registry,
        'action_steps':sorted(actions)}
def add(name, mutate=None):
    payload=make_request(copy.deepcopy(base_snapshot),copy.deepcopy(base_context),set(base_actions))
    if mutate: mutate(payload)
    expected=original.plan_unhandled_event_fallback_v1(snapshot=payload['snapshot'],event_context=payload['event_context'],
        event_summary=payload['event_summary'],registry_decision=payload['registry_decision'],action_steps=payload['action_steps'])
    cases.append({'name':name,'request':payload,'expected_plan':expected})
add('first-display-native6-is-option7')
add('array-order-is-not-display-order',lambda p:p['event_context']['options'].reverse())
add('first-disabled-next-enabled',lambda p:p['event_context']['options'][0].update(enabled=False))
add('all-disabled-retain-diagnosis',lambda p:[r.update(enabled=False) for r in p['event_context']['options']])
add('first-unadvertised-never-pick-later-advertised',lambda p:p['action_steps'].remove('select-event-option-7'))
add('first-hidden-next-shown',lambda p:p['event_context']['options'][0].update(shown=False))
add('duplicate-rendered-index',lambda p:p['event_context']['options'][1].update(rendered_index=0))
add('negative-rendered-index',lambda p:p['event_context']['options'][0].update(rendered_index=-1))
add('native-outside-authored-count',lambda p:p['event_context']['options'][0].update(native_option_index=7))
add('event-instance-drift',lambda p:p['event_context'].update(current_event_instance_id=42))
add('public-cannot-replace-native-revision',lambda p:p['event_context'].update(snapshot_revision=3))
add('date-drift',lambda p:p['event_context'].update(date_raw=53000017))
def active_null(p): p['snapshot']['current_event']=copy.deepcopy(p['snapshot']['active_event']);p['snapshot']['active_event']=None
add('active-null-does-not-use-current-event',active_null)
def active_missing(p): p['snapshot']['current_event']=p['snapshot'].pop('active_event')
add('active-missing-uses-current-event',active_missing)
add('null-main-diagnostics-use-original-fallback',lambda p:p['snapshot'].update(connection_generation=None,bridge_pid=None))
add('empty-options',lambda p:p['event_context'].update(options=[]))
add('null-options',lambda p:p['event_context'].update(options=None))
add('null-event-context',lambda p:p.update(event_context=None))
add('null-snapshot',lambda p:p.update(snapshot=None))
add('unknown-definition-is-preserved-not-invented',lambda p:p['event_context'].update(event_definition_key=None))
add('opaque-diagnostic-floats-and-wide-counter',lambda p:p['event_summary'].update(diagnostic_ratio=1.0,uninterpreted_counter=9007199254740993))
after_cases=[]
body_cases=[]
base_plan=cases[0]['expected_plan']
def after(name, result=None, error=None):
    selection={'status':'event_instance_advanced','postcondition_verified':True,'old_event_instance_id':41,
        'new_event_instance_id':None,'selected_native_option_index':6,'selected_option_number':7}
    outcome={'status':'executed','result':{'accepted':True,'event_selection':selection}}
    if result is not None: outcome['result']=result
    if error is not None: outcome=None
    with tempfile.TemporaryDirectory(prefix='java-unhandled-event-') as temporary:
        planned={'snapshot_id':base_snapshot['snapshot_id'],'revision':base_snapshot['revision'],'plan':copy.deepcopy(base_plan)}
        ticket=original.capture_unhandled_event_before_v1(temporary,planned)
        response=original.capture_unhandled_event_after_v1(ticket,outcome=outcome,error=error)
        before_body=json.loads(Path(ticket['before']['path']).read_bytes())
        after_body=json.loads(Path(response['after']['path']).read_bytes())
        body_cases.append({'name':name,
            'before_request':{'schema':'xar.events-unhandled-before-body-input/v1','planned':planned,'incident_id':ticket['incident_id'],'captured_at_utc':before_body['captured_at_utc']},
            'expected_before':before_body,
            'after_request':{'schema':'xar.events-unhandled-after-body-input/v1','ticket':ticket,'outcome':outcome,
                'error':{'type':type(error).__name__,'message':str(error)} if error is not None else None,'captured_at_utc':after_body['captured_at_utc']},
            'expected_after':after_body})
        expected={k:response[k] for k in ('command_acknowledged','event_instance_advanced_verified','replay_allowed')}
    request={'schema':'xar.ck3.unhandled-event-after-input/v1','ticket':{'current_event_instance_id':41,'selected_native_option_index':6},'outcome':outcome}
    after_cases.append({'name':name,'request':request,'expected':expected})
after('independent-next-none-verified')
after('ack-only',{'accepted':True})
def selected(**updates):
    value={'status':'event_instance_advanced','postcondition_verified':True,'old_event_instance_id':41,
        'new_event_instance_id':42,'selected_native_option_index':6,'selected_option_number':7}; value.update(updates)
    return {'accepted':True,'event_selection':value}
after('independent-next-instance-verified',selected())
after('same-instance-remains-unknown',selected(new_event_instance_id=41))
after('wrong-old-instance',selected(old_event_instance_id=99))
after('wrong-native-option',selected(selected_native_option_index=0))
after('postcondition-not-verified',selected(postcondition_verified=False))
after('wrong-selection-status',selected(status='submitted'))
after('rejected-ack',{'accepted':False,'event_selection':selected()['event_selection']})
after('unknown-native-error',error=BridgeUnavailableError('synthetic unknown native submission outcome'))
after_cases.append({'name':'no-ticket-no-receipt','request':{'schema':'xar.ck3.unhandled-event-after-input/v1','ticket':None,'outcome':{'result':{'accepted':True}}},'expected':None})
dedicated=(copy.deepcopy(base_snapshot),copy.deepcopy(base_context),set(base_actions))
dedicated[1]['event_definition_key']='health.1001'
dedicated[1]['options']=[fixture._option(i,n) for i,n in enumerate((3,4,6))]
dedicated[1]['saved_scopes']=[{'name':'physician','name_identifier':1,'scope':fixture._scope(100)},
    {'name':'sick_character','name_identifier':2,'scope':fixture._scope(99)},
    {'name':'disease_type','name_identifier':3,'scope':fixture._scope()}]
known=fixture._choose(dedicated)
paths=['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/unhandled_fallback.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/event_contract.py',
    'ck3_autonomous_player/src/xar_autoplayer/strategy.py',
    'ck3_autonomous_player/tests/unit/test_unhandled_event_fallback.py']
record={'schema':'xar.ck3.unhandled-event-golden/v1','machine_id':machine,'captured_at':datetime.now(timezone.utc).isoformat(),
    'evidence_scope':'actual-old-plan-and-before-after-producer-and-dedicated-strategy; synthetic-native-boundary-fixtures; no-game-no-action',
    'producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],
    'plan_cases':cases,'after_cases':after_cases,'body_cases':body_cases,'dedicated_strategy':{'phase':known.get('phase'),'selected_step':known.get('selected_step'),
        'unhandled_event_fallback':known.get('unhandled_event_fallback')}}
payload=json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\\n'
print('uncompressed_golden_bytes='+str(len(payload)),file=sys.stderr)
sys.stdout.buffer.write(gzip.compress(payload,compresslevel=9,mtime=0))
""";
    /** Actual original producers and retained stock files, never patched review anchors. */
    private static final String SOURCE_REVIEW_CAPTURE = """
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import base64, copy, gzip, hashlib, inspect, json, sys, tempfile
import pytest
root,machine,game=Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]).resolve()
input_manifest,cohort=Path(sys.argv[4]).resolve(),sys.argv[5]
cohort_counts={'generic':14,'council':7,'council-source-drift':1,'liberty':7,'liberty-source-drift':1,'sway':7,'sway-source-drift':1,'factions':20}
if cohort not in cohort_counts:raise RuntimeError('undeclared source-review cohort')
manifest_raw=input_manifest.read_bytes()
if len(manifest_raw)>16384:raise RuntimeError('stock input manifest exceeds declared bound')
manifest=json.loads(manifest_raw)
if (manifest.get('schema')!='xar.events-stock-source-inputs/v1' or manifest.get('machine_id')!=machine
        or Path(manifest.get('game_root','')).resolve()!=game or manifest.get('source_gui_expected_anchors_match') is not True):
    raise RuntimeError('actual stock input manifest machine/root/source qualification differs')
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
import test_event_offline_analysis as generic
import test_reviewed_letter_source_rebind_v1 as letter_fixture
import test_independence0001_known_refusal as independence_fixture
import test_populist1001_current_source_binding as populist_fixture
from xar_autoplayer.vanilla_events import event_offline_analysis as offline
from xar_autoplayer.vanilla_events import reviewed_letter_source_rebind_v1 as letters
from xar_autoplayer.vanilla_events import populist1001_known_refusal_v1 as policies
from xar_autoplayer.vanilla_events import unhandled_fallback as fallback
cases=[]; blobs={}; stock_refs={}
def digest(raw): return hashlib.sha256(raw).hexdigest()
def retain(path,relative,kind):
    if not isinstance(relative,str):raise RuntimeError('retained reconstruction path must be a string')
    logical=PurePosixPath(relative)
    if (chr(92) in relative or ':' in relative or not logical.parts or logical.is_absolute()
            or logical.as_posix()!=relative or '..' in logical.parts):
        raise RuntimeError('retained reconstruction path must be canonical bounded POSIX relative')
    path=Path(path).resolve(); raw=path.read_bytes(); sha=digest(raw)
    if len(raw)>2*1024*1024:raise RuntimeError('retained original file exceeds original source bound')
    blobs.setdefault(sha,base64.b64encode(gzip.compress(raw,compresslevel=9,mtime=0)).decode('ascii'))
    return {'path':str(path),'relative':relative,'kind':kind,'sha256':sha,'bytes':len(raw)}
def verify_stock_inputs():
    expected={review['source_relative']:('source',review['source_sha256']) for review in letters.REVIEWS.values()}
    expected.update({relative:('gui',sha) for relative,sha in letters.GUI_SOURCES.items()})
    declared=manifest.get('files')
    if not isinstance(declared,list) or len(declared)!=len(expected):raise RuntimeError('complete stock input manifest rows required')
    pins={row.get('relative_path'):row for row in declared if isinstance(row,dict)}
    if set(pins)!=set(expected) or len(pins)!=len(declared):raise RuntimeError('stock input manifest paths duplicated or missing')
    observed={}
    for relative,(kind,wanted) in sorted(expected.items()):
        path=(game/relative).resolve()
        if not path.is_relative_to(game) or not path.is_file() or path.stat().st_size>2*1024*1024:
            raise RuntimeError('actual stock source/GUI path or original byte bound unavailable: '+relative)
        raw=path.read_bytes();row={'path':str(path),'relative':'game/'+relative,'kind':kind,'sha256':digest(raw),'bytes':len(raw)}
        pin=pins[relative]
        if (Path(pin.get('path','')).resolve()!=path or type(pin.get('bytes')) is not int or pin['bytes']!=row['bytes']
                or pin.get('sha256')!=wanted or pin.get('expected_sha256')!=wanted
                or row['bytes']>2*1024*1024 or row['sha256']!=wanted):
            raise RuntimeError('actual stock source/GUI SHA differs from unpatched review: '+relative)
        observed[relative]=row
    if stock_refs and observed!=stock_refs:raise RuntimeError('actual stock source/GUI changed during capture')
    stock_refs.update(observed)
verify_stock_inputs()
def files(state):
    rows=[]
    if state is None:return rows
    for entry_path in sorted((Path(state)/'evidence/event-source-registry').glob('*.json')):
        entry=json.loads(entry_path.read_bytes()); fp=entry_path.stem
        facts_path=Path(entry['source_facts']['path']); source=Path(entry['source_path']).resolve()
        rows.append(retain(entry_path,'state/evidence/event-source-registry/'+entry_path.name,'entry'))
        rows.append(retain(facts_path,'state/evidence/event-source-registry/facts/'+facts_path.name,'facts'))
        rel=source.relative_to(game).as_posix() if source.is_relative_to(game) else 'synthetic/'+source.name
        rows.append(retain(source,'game/'+rel,'source'))
    if any(Path(row['path']).is_relative_to(game) for row in rows):
        for relative,expected in letters.GUI_SOURCES.items():
            path=game/relative;raw=path.read_bytes()
            if digest(raw)!=expected:raise RuntimeError('actual stock GUI SHA differs: '+relative)
            rows.append(retain(path,'game/'+relative,'gui'))
    unique={row['path']:row for row in rows}
    return list(unique.values())
def emit(name,plan,state,snapshot,steps,mode='annotation',request=None):
    expected=copy.deepcopy(plan)
    if mode!='policy':expected=offline.annotate_source_reviewed_event_plan_v1(expected,state)
    if mode in ('policy','pipeline'):expected=policies.choose_source_reviewed_populist_refusal_v1(expected,snapshot=snapshot,action_steps=steps)
    cases.append({'name':name,'mode':mode,'plan':copy.deepcopy(plan),'state_directory':str(state) if state is not None else None,
        'snapshot':copy.deepcopy(snapshot),'action_steps':sorted(steps),'request':copy.deepcopy(request),'expected':expected,'files':files(state)})
def request_plan(capture,snapshot,steps):
    request={'schema':'xar.ck3.unhandled-event-plan-input/v1','snapshot':copy.deepcopy(snapshot),
        'event_context':copy.deepcopy(capture['window_context']),'event_summary':copy.deepcopy(snapshot['active_event']),
        'registry_decision':copy.deepcopy(capture.get('original_registry_decision',{'status':'not_registered'})),
        'action_steps':sorted(steps)}
    plan=fallback.plan_unhandled_event_fallback_v1(snapshot=request['snapshot'],event_context=request['event_context'],event_summary=request['event_summary'],registry_decision=request['registry_decision'],action_steps=request['action_steps'])
    if plan is None:raise RuntimeError('actual old fallback producer could not bind fixture')
    return request,plan
def publish_stock(directory,plan):
    state=directory/'state';frame=plan['unhandled_event_fallback']['binding']
    ticket=fallback.capture_unhandled_event_before_v1(state,{'plan':plan,'snapshot_id':frame['snapshot_id'],'revision':frame['revision']})
    manifest=directory/'batch.json';manifest.write_text(json.dumps({'completed_control_sequence':1,'new_incidents':[{'incident_id':ticket['incident_id'],
        'event_definition_key':plan['unhandled_event_fallback']['event_definition_key'],'before':ticket['before']['path'],'before_sha256':ticket['before']['sha256']}]}),encoding='utf-8')
    report=offline.analyze_event_batch(manifest,game,directory/'review',publish_state_dir=state)
    if report['unresolved'] or len(report['entries'])!=1:raise RuntimeError('actual stock source review unavailable: '+json.dumps(report['unresolved']))
    return state
with tempfile.TemporaryDirectory(prefix='java-source-review-') as temporary:
    scratch=Path(temporary)
    with pytest.MonkeyPatch.context() as monkey:
        directory=scratch/'generic';directory.mkdir()
        c=inspect.unwrap(generic.reviewed_case)(directory,monkey)
        emit('generic-unknown-before-publish',c['plan'],c['state'],c['snapshot'],c['actions'])
        generic.publish(c)
        emit('generic-exact-known',c['plan'],c['state'],c['snapshot'],c['actions'])
        known=offline.annotate_source_reviewed_event_plan_v1(c['plan'],c['state'])
        emit('generic-repeat-known-no-new-todo',known,c['state'],c['snapshot'],c['actions'])
        emit('state-directory-null-keeps-existing-plan',known,None,c['snapshot'],c['actions'])
        for change in ('build','count','option','source','facts','calculated','root','disabled','unadvertised','stale'):
            plan=copy.deepcopy(c['plan']);capture=plan['unhandled_event_fallback'];ctx=capture['window_context']
            source_original=c['source'].read_bytes()
            fact_path=next((c['state']/'evidence/event-source-registry/facts').glob('*.json'));facts_original=fact_path.read_bytes()
            if change=='build':ctx['provenance']['backend_id']='ck3-1.20.0.3-native-event-window-v1'
            elif change=='count':capture['snapshot_option_count']+=1
            elif change=='option':ctx['options'][0]['native_option_index']=99
            elif change=='source':c['source'].write_bytes(source_original+b'changed')
            elif change=='facts':fact_path.write_bytes(b'{}')
            elif change in ('calculated','root','stale'):ctx['calculated_event_id']+=1
            elif change=='disabled':
                ctx['options'][0]['enabled']=False
                _,plan=request_plan(capture,c['snapshot'],c['actions'])
            elif change=='unadvertised':plan['selected_step']=None
            if change=='root':ctx['root_scope']['typed_identity']['character_id']=999
            if change=='stale':capture['selection']['native_option_index']=0
            emit('generic-character-rebound' if change=='calculated' else 'generic-'+change,plan,c['state'],c['snapshot'],c['actions'])
            c['source'].write_bytes(source_original);fact_path.write_bytes(facts_original)
        generic.test_source_known_repeat_does_not_generate_another_analysis_todo(c,directory,monkey)
        repeat_path=directory/'known-next-review/EVENT-SOURCE-REVIEW.json'
        repeat_known_batch={'report':json.loads(repeat_path.read_bytes()),
            'original_report':retain(repeat_path,'repeat-known/EVENT-SOURCE-REVIEW.json','report')}
    # Reuse native fixture shapes only. Restore every synthetic anchor patch BEFORE stock review.
    for key in sorted(letters.KEYS):
        directory=scratch/key;directory.mkdir()
        shape_directory=directory/'native-shape';shape_directory.mkdir()
        with pytest.MonkeyPatch.context() as monkey:
            request=type('FixtureRequest',(),{'param':key})()
            capture,_,_,_,_=inspect.unwrap(letter_fixture.case)(request,shape_directory,monkey)
        frame=capture['binding'];snapshot={**frame,'played_character':{'character_id':frame['actor_character_id'],'alive':True},
            'active_event':{'instance_id':capture['current_event_instance_id'],'option_count':capture['snapshot_option_count']},
            'diagnostics':{'bridge_pid':frame['bridge_pid'],'connection_generation':frame['connection_generation']}}
        steps={'select-event-option-'+str(i+1) for i in range(capture['snapshot_option_count'])}
        req,plan=request_plan(capture,snapshot,steps);state=publish_stock(directory,plan)
        emit(key+'-exact-stock',plan,state,snapshot,steps,'pipeline',req)
        for change in ('cold-id','root','role-type','provider','frame','gui','source'):
            changed=copy.deepcopy(plan);ctx=changed['unhandled_event_fallback']['window_context'];ctx['calculated_event_id']+=1
            if change=='root':ctx['root_scope']['typed_identity']['character_id']=999
            elif change=='role-type':ctx['saved_scopes'][0]['scope']['raw_type_index']=99
            elif change=='provider':ctx['provenance']['idler_vtable_rva']='0x1'
            elif change=='frame':changed['unhandled_event_fallback']['binding']['native_revision']+=1
            # Never mutate installed stock. Drift files are retained copies with rewritten source locations.
            if change in ('gui','source'):
                old=next((state/'evidence/event-source-registry').glob('*.json'));entry=json.loads(old.read_bytes())
                fact_path=Path(entry['source_facts']['path']);fact=json.loads(fact_path.read_bytes());source_path=Path(entry['source_path'])
                localgame=directory/('drift-'+change)/'game';relative=source_path.relative_to(game);local=localgame/relative;local.parent.mkdir(parents=True)
                local.write_bytes(source_path.read_bytes()+(b'changed' if change=='source' else b''))
                for gui_relative in letters.GUI_SOURCES:
                    p=localgame/gui_relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((game/gui_relative).read_bytes()+(b'changed' if change=='gui' else b''))
                fact['source_path']=str(local);driftstate=directory/('drift-'+change)/'state'
                ref=offline.write_immutable(driftstate/'evidence/event-source-registry/facts'/fact_path.name,fact)
                entry.update(source_path=str(local),source_facts=ref);offline.write_immutable(driftstate/'evidence/event-source-registry'/old.name,entry)
                # Retain local GUI bytes explicitly even though this source root is outside stock game.
                emit(key+'-'+change,changed,driftstate,snapshot,steps)
                for gui_relative in letters.GUI_SOURCES:cases[-1]['files'].append(retain(localgame/gui_relative,'game/'+gui_relative,'gui'))
                for row in cases[-1]['files']:
                    if row['kind']=='source':row['relative']='game/'+relative.as_posix()
            else:
                if change=='cold-id':
                    changed_capture=changed['unhandled_event_fallback'];changed_req,changed=request_plan(changed_capture,snapshot,steps)
                    emit(key+'-cold-id',changed,state,snapshot,steps,'pipeline',changed_req)
                else:emit(key+'-'+change,changed,state,snapshot,steps)
    # Original populated actual-native projection + actual stock source; no old audit is trusted.
    fixture=populist_fixture.case();plan=copy.deepcopy(fixture['plan']);capture=plan['unhandled_event_fallback']
    req,plan=request_plan(capture,fixture['snapshot'],{'select-event-option-3','select-event-option-4'})
    directory=scratch/'populist';directory.mkdir();state=publish_stock(directory,plan)
    emit('populist-exact-stock-pipeline',plan,state,fixture['snapshot'],req['action_steps'],'pipeline',req)
    for change in ('cold-id','target','scope','layout','unadvertised'):
        p=copy.deepcopy(plan);ctx=p['unhandled_event_fallback']['window_context'];ctx['calculated_event_id']+=1
        steps=set(req['action_steps'])
        if change in ('target','scope'):
            role=next(row for row in ctx['saved_scopes'] if row['name']==('faction_target' if change=='target' else 'peasant_county'))
            if change=='target':role['scope']['typed_identity']['character_id']+=1
            else:role['scope']['typed_identity']={'status':'unavailable','reason':'synthetic negative'}
        elif change=='layout':ctx['options'][1]['rendered_index']=2
        elif change=='unadvertised':steps.remove('select-event-option-4')
        if change=='cold-id':
            changed_req,p=request_plan(p['unhandled_event_fallback'],fixture['snapshot'],steps)
            emit('populist-cold-id-stock-pipeline',p,state,fixture['snapshot'],steps,'pipeline',changed_req)
        elif change=='unadvertised':
            changed_req,p=request_plan(p['unhandled_event_fallback'],fixture['snapshot'],steps)
            emit('populist-'+change,p,state,fixture['snapshot'],steps,'pipeline',changed_req)
        else:emit('populist-'+change,p,state,fixture['snapshot'],steps)
    for co_emperor in (False,True):
        c=independence_fixture.case(co_emperor=co_emperor)
        for change in ('none','disabled','unadvertised','date','pid','target','rejected-exact'):
            changed=copy.deepcopy(c);ctx=changed['plan']['unhandled_event_fallback']['window_context']
            if change=='disabled':ctx['options'][-1]['enabled']=False
            elif change=='unadvertised':changed['steps'].remove('select-event-option-3')
            elif change=='date':changed['snapshot']['date_raw']+=1
            elif change=='pid':changed['snapshot']['diagnostics']['bridge_pid']+=1
            elif change=='target':ctx['saved_scopes'][1]['scope']['typed_identity']['character_id']+=1
            elif change=='rejected-exact':changed['plan']['unhandled_event_fallback']['source_knowledge']['rejected_entries']=[{'reason':'source changed'}]
            emit('independence-'+str(co_emperor).lower()+'-'+change,changed['plan'],None,changed['snapshot'],changed['steps'],'policy')
def in_cohort(name):
    if cohort=='generic':return name.startswith('generic-') or name=='state-directory-null-keeps-existing-plan'
    if cohort=='factions':return name.startswith('populist-') or name.startswith('independence-')
    keys={'council':'ecumenical_council_events.0082','liberty':'faction_demand.0101','sway':'sway_ongoing.1003'}
    leaf=cohort.removesuffix('-source-drift');key=keys[leaf]
    return name==key+'-source' if cohort.endswith('-source-drift') else name.startswith(key+'-') and name!=key+'-source'
if len(cases)!=58 or len({row['name'] for row in cases})!=58:raise RuntimeError('complete finite source-review case set differs')
cases=[row for row in cases if in_cohort(row['name'])]
if len(cases)!=cohort_counts[cohort]:raise RuntimeError('fixed source-review cohort case count differs')
if cohort!='generic':repeat_known_batch=None
used={row['sha256'] for case in cases for row in case['files']}
if repeat_known_batch is not None:used.add(repeat_known_batch['original_report']['sha256'])
blobs={sha:blobs[sha] for sha in sorted(used)}
paths=['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/'+name for name in ('event_offline_analysis.py','builds.py','reviewed_letter_source_rebind_v1.py','populist1001_known_refusal_v1.py','independence0001_known_refusal_v1.py','faction_demand1001_context.py','unhandled_fallback.py','source_index.py','migration_1_20_0_4.py','records_faith_creation1021_12004.py','records_head_of_faith0100_12004.py','records_pam_bull0004_12004.py')]
paths+=['ck3_autonomous_player/src/xar_autoplayer/interaction_offline_analysis.py']
paths+=['ck3_autonomous_player/src/xar_autoplayer/bridge/event_contract.py']
paths+=['ck3_autonomous_player/tests/unit/'+name for name in ('test_event_offline_analysis.py','test_reviewed_letter_source_rebind_v1.py','test_independence0001_known_refusal.py','test_populist1001_current_source_binding.py')]
input_paths=['ck3_autonomous_player/tests/unit/fixtures/p43_populist_actual193_projection.json',
    'ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data/source_index_1_20_0_3.json']
verify_stock_inputs()
if input_manifest.read_bytes()!=manifest_raw:raise RuntimeError('stock input manifest changed during capture')
record={'schema':'xar.ck3.source-review-golden/v1','machine_id':machine,'captured_at':datetime.now(timezone.utc).isoformat(),
    'scope':'actual-old-annotation-loader-and-policies; real installed stock source/GUI; synthetic native frames; no Game/RPC/writer custody',
    'projection':'tests relocate only declared source_path/path/entry_path and derived sha256/entry_sha256; source bytes/binding/options fingerprints unchanged',
    'producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':digest((root/p).read_bytes())} for p in paths],
    'input_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':digest((root/p).read_bytes())} for p in input_paths],
    'stock_input_manifest':{'path':str(input_manifest),'bytes':len(manifest_raw),'sha256':digest(manifest_raw)},
    'cohort':cohort,'required_cohorts':list(cohort_counts),'cohort_case_count':len(cases),'complete_case_count':58,
    'blob_encoding':'gzip-base64',
    'stock_game_root':str(game),'stock_refs':[stock_refs[relative] for relative in sorted(stock_refs)],
    'repeat_known_batch':repeat_known_batch,'cases':cases,'blobs':blobs}
payload=json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\\n'
if len(payload)>1048576:raise RuntimeError('source-review actual corpus exceeds existing 1 MiB decompression budget')
packed=gzip.compress(payload,compresslevel=9,mtime=0)
if len(packed)>65536:raise RuntimeError('source-review actual corpus exceeds existing 64 KiB compressed budget')
print(json.dumps({'case_count':len(cases),'raw_bytes':len(payload),'compressed_bytes':len(packed),'sha256':digest(packed)}),file=sys.stderr)
sys.stdout.buffer.write(packed)
""";
}
