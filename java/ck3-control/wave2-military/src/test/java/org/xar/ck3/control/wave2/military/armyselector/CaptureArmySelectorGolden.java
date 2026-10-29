package org.xar.ck3.control.wave2.military.armyselector;


import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

/** Explicit bounded capture of the original producer and real memory-service strategy consumer. */
public final class CaptureArmySelectorGolden {
    private CaptureArmySelectorGolden() {}
    private static final int MAX_RAW_BYTES = 128 * 1024;
    private static final int MAX_GZIP_BYTES = 24 * 1024;
    private static final String SCRIPT = """
import copy, datetime, hashlib, json, os, pathlib, runpy, sys
root=pathlib.Path(sys.argv[1]); machine=sys.argv[2]; scratch=pathlib.Path(sys.argv[3])
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]

# A compiled probe supplies complete Java return bytes. It never falls back after a
# missing, rejected or unknown transport result. Baseline mode records the same
# original provider calls made by the actual complete consumer suites.
from contextlib import ExitStack
from unittest.mock import patch
from pathlib import Path
import gzip
def consumer_json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def consumer_strict(raw):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value: raise RuntimeError('duplicate compiled packet JSON key')
            value[key]=item
        return value
    def constant(value): raise RuntimeError('non-JSON compiled packet constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
consumer_mode=len(sys.argv)>5 and sys.argv[5] in ('baseline','compiled')
consumer_packet_path=Path(sys.argv[4]) if consumer_mode and sys.argv[4] else None
consumer_packet_bytes=None
consumer_packet=None
consumer_inputs=[]
consumer_services=[]
consumer_cursor=0
consumer_phase='reference'
if consumer_packet_path is not None:
    if not consumer_packet_path.is_file() or consumer_packet_path.is_symlink() or consumer_packet_path.stat().st_size>524288:
        raise RuntimeError('compiled packet input is missing, linked or oversized')
    consumer_packet_bytes=consumer_packet_path.read_bytes()
    consumer_packet=consumer_strict(consumer_packet_bytes)
    required={'schema','family','observed_at_utc','qualified_main_jar','qualified_main_jar_sha256','qualified_test_classes','qualified_test_class_sha256','original_golden_sha256','cases'}
    if type(consumer_packet) is not dict or set(consumer_packet)!=required or consumer_packet['schema']!='xar.compiled-army-consumer-wire-packet/v1' or consumer_packet['family']!='armyselector' or type(consumer_packet['cases']) is not list:
        raise RuntimeError('compiled packet schema/family differs')
    consumer_phase='java'
def consumer_invoke(value,reference):
    global consumer_cursor
    raw=consumer_json(value)
    if consumer_phase=='java':
        index=consumer_cursor
        consumer_cursor+=1
        if index>=len(consumer_packet['cases']):
            raise RuntimeError('unexpected consumer call; no producer fallback or retry')
        supplied=consumer_packet['cases'][index]
        if type(supplied) is not dict or set(supplied)!={'input_json','accepted','output_json'} or supplied['input_json']!=raw or type(supplied['accepted']) is not bool:
            raise RuntimeError('consumer call order or exact source operand bytes drifted')
        if supplied['accepted']:
            if type(supplied['output_json']) is not str: raise RuntimeError('compiled complete result lacks return bytes')
            result=consumer_strict(supplied['output_json'])
            consumer_inputs.append(dict(input_json=raw,accepted=True,output_json=supplied['output_json']))
            return result
        if supplied['output_json'] is not None: raise RuntimeError('rejected compiled result carries output')
        consumer_inputs.append(dict(input_json=raw,accepted=False,output_json=None))
        raise ValueError('actual compiled producer rejected original raw operand tokens')
    try:
        result=reference()
    except (ValueError,TypeError):
        consumer_inputs.append(dict(input_json=raw,accepted=False,output_json=None))
        raise
    consumer_inputs.append(dict(input_json=raw,accepted=True,output_json=consumer_json(result)))
    return result
def consumer_finish(payload):
    if not consumer_mode: return payload
    if consumer_packet is not None and (consumer_cursor!=len(consumer_packet['cases']) or consumer_packet_path.read_bytes()!=consumer_packet_bytes):
        raise RuntimeError('compiled packet was not consumed exactly once or drifted')
    payload['schema']='xar.armyselector.original-consumer-baseline/v1'
    payload['consumer_inputs']=consumer_inputs
    payload['actual_service_consumers']=consumer_services
    payload['transport_contract']={'native_query_limit_per_service_call':1,'unknown_result_retries':0,'python_fallback_after_java_failure':False,'all_original_tests_passed':True,'compiled_calls':consumer_cursor}
    if consumer_packet is not None:
        payload['schema']='xar.armyselector.compiled-java-consumer-probe/v1'
        payload['compiled_java_input']={key:consumer_packet[key] for key in ('qualified_main_jar','qualified_main_jar_sha256','qualified_test_classes','qualified_test_class_sha256','original_golden_sha256')}
        payload['compiled_java_input'].update(packet_path=str(consumer_packet_path),packet_bytes=len(consumer_packet_bytes),packet_sha256=hashlib.sha256(consumer_packet_bytes).hexdigest())
    for key in ('cases','rows','projections','refreshes','consumers'):payload.pop(key,None)
    return payload

paths=('ck3_autonomous_player/src/xar_autoplayer/current_replenishment_army_selector_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_scoped_ordered_refill_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_refresh_projection.py','ck3_autonomous_player/src/xar_autoplayer/replenishment_numeric.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_scoped_ordered_refill_contract.py','ck3_autonomous_player/tests/unit/test_current_replenishment_normal_plan_v1.py','ck3_autonomous_player/tests/unit/test_scoped_ordered_refill_service.py','ck3_autonomous_player/tests/unit/test_gameplay_bridge.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.current_replenishment_army_selector_v1 import select_current_replenishment_army_v1
from xar_autoplayer.bridge.army_scoped_ordered_refill_projection import project_scoped_observed_prepared_ordered_refill
from xar_autoplayer.bridge.army_regiment_refresh_projection import project_observed_raised_regiment_refresh
import test_current_replenishment_normal_plan_v1 as original
rows=[original._strength(11,10000),original._strength(22,0),original._strength(11,10000,90)]
missing=original._strength(11,10000)
missing['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][0].update(unit_position_owner_resolved_full_id=707,unit_position_holder_resolved_full_id=808,native_unit_position_eligible=None)
rows.append(missing)
rows.extend([original._strength(11,1),original._strength(11,-1)])
cleanup=original._strength(11,10000)
cleanup['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][1]['owner_guard_138_raw']=None
rows.append(cleanup)
same=original._strength(11,10000)
same['scoped_ordered_refill_inputs_v1']['subject_carmy_id']=999
rows.append(same)
alias=original._strength(11,10000)
alias['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][1]['q_ordinal_raw']=0
rows.append(alias)
no_refresh=original._strength(11,10000)
no_refresh['scoped_ordered_refill_inputs_v1']['army_refresh_occurrence_indices']=[]
rows.append(no_refresh)
row_fields=('army_id','native_carmy_id','status','scope_role','current_soldiers','war_ids','regiment_count','regiment_replenishment_records_v1','regiment_strengths','scoped_ordered_refill_inputs_v1')
chunk_fields=('physical_index','current_soldiers','maximum_soldiers','q_ordinal_raw','army_regiment_id_raw','exclusion_byte_14_raw','state_raw','origin_province_788_raw','origin_province_73c_raw','associated_arrg_magic_raw','associated_arrg_resolved_full_id','army_byte_1d4_raw','army_byte_1ec_raw','native_army_in_combat','unit_170_raw','unit_position_province_magic_raw','unit_position_owner_resolved_full_id','unit_position_holder_resolved_full_id','native_unit_position_eligible','owner_guard_138_raw','owner_definition_magic_38_raw')
def compact(row):
    out={k:copy.deepcopy(row[k]) for k in row_fields}
    out['regiment_replenishment_records_v1']=[{k:copy.deepcopy(s[k]) for k in ('army_regiment_id','status','native_loss_writer_skipped','records')} for s in row['regiment_replenishment_records_v1']]
    for s in out['regiment_replenishment_records_v1']:
        s['records']=[{k:r[k] for k in ('record_index','persistent_regiment_id','chunk_index','state_raw','current_soldiers','maximum_soldiers')} for r in s['records']]
    out['regiment_strengths']=[{k:s[k] for k in ('army_regiment_id','current_soldiers','maximum_soldiers')} for s in row['regiment_strengths']]
    for p in out['scoped_ordered_refill_inputs_v1']['persistent_regiments']:p['chunks']=[{k:c[k] for k in chunk_fields} for c in p['chunks']]
    return out
def army(row,province):return dict(army_id=row['army_id'],soldiers=row['current_soldiers'],army_state='regular',move_target_province_id=None,route_province_ids=[],current_province_id=province)
cases=[]
def case(name,indices,*,changes=None,army_changes=None,wars=(88,)):
    sources=[copy.deepcopy(rows[i]) for i in indices]
    armies=[army(r,2630+i) for i,r in enumerate(sources)]
    snap=dict(paused=True,snapshot_id='same-frame',revision=42,army_strengths_status='available',army_strengths_queried_snapshot_id='same-frame',army_strengths_queried_revision=42,army_strengths=sources)
    if changes:
        for k,v in changes.items():
            if v=='__MISSING__':snap.pop(k,None)
            else:snap[k]=v
    if army_changes:
        for index,values in army_changes.items():armies[index].update(values)
    untouched=copy.deepcopy((armies,snap)); selected,expected=select_current_replenishment_army_v1(armies,snap,active_war_ids=wars)
    if untouched != (armies,snap):raise RuntimeError('original selector mutated input')
    meta={k:v for k,v in snap.items() if k!='army_strengths'}
    cases.append(dict(id=name,row_indices=indices,armies=armies,snapshot=meta,active_war_ids=list(wars),expected=expected))
case('positive-versus-zero',[0,1]);case('actual-strength-primary',[2,1]);case('missing-permission',[3,1]);case('qualified-zero-cleanup',[4,1]);case('negative-fraction',[5,1]);case('cleanup-unknown',[6,1]);case('subject-identity',[7,1]);case('ordinal-alias',[8,1]);case('no-manager-refresh',[9,1])
case('query-status-missing',[0,1],changes={'army_strengths_status':'__MISSING__'});case('query-status-null',[0,1],changes={'army_strengths_status':None});case('unpaused',[0,1],changes={'paused':False});case('stale-snapshot',[0,1],changes={'army_strengths_queried_snapshot_id':'stale'});case('stale-revision',[0,1],changes={'army_strengths_queried_revision':41});case('not-available',[0,1],changes={'army_strengths_status':'unavailable'});case('duplicate-row',[0,0,1]);case('same-province',[0,1],army_changes={1:{'current_province_id':2630}});case('moving',[0,1],army_changes={0:{'route_province_ids':[2631]}});case('no-wars',[0,1],wars=());case('deduplicate-wars',[0,1],wars=(99,88,88));case('empty',[])
projections=[]
for index,row in enumerate(rows):
    out=project_scoped_observed_prepared_ordered_refill(row)
    projections.append(dict(row_index=index,expected={k:out[k] for k in ('ordered_core_ready','conditional_raised_current_maximum_ready','conditional_current_soldiers','conditional_maximum_soldiers','missing_inputs')}))
refreshes=[]
def refresh_case(name,*,skipped=False,status='available',state=0,physical=None):
    data=copy.deepcopy(rows[0]['regiment_replenishment_records_v1'][0]);data['native_loss_writer_skipped']=skipped;data['status']=status
    for r in data['records']:r['state_raw']=state
    expected=project_observed_raised_regiment_refresh(data,physical_chunks_after=physical)
    compact_data={k:data[k] for k in ('army_regiment_id','status','native_loss_writer_skipped')}
    compact_data['records']=[{k:r[k] for k in ('record_index','persistent_regiment_id','chunk_index','state_raw','current_soldiers','maximum_soldiers')} for r in data['records']]
    refreshes.append(dict(id=name,data=compact_data,physical_chunks_after=physical,expected=expected))
refresh_case('observed-aliases');refresh_case('character-override',skipped=True);refresh_case('missing-character-predicate',skipped=None);refresh_case('unavailable-DATA',status='partial');refresh_case('explicit-empty-replay',physical=[])
refresh_case('signed32-overflow',physical=[dict(persistent_regiment_id=50011,chunk_index=0,current_soldiers=2147483647,maximum_soldiers=2147483647)])
refresh_case('state3-zero-effective',state=3,physical=[dict(persistent_regiment_id=50011,chunk_index=0,current_soldiers=0,maximum_soldiers=100)])
consumer_output=scratch/'armyselector-original-consumer.json'
os.environ['XAR_CURRENT_REPLENISHMENT_FIRST_OUTPUT']=str(consumer_output)
consumer_plans=[]
if consumer_mode:
    import unittest
    from xar_autoplayer import strategy as consumer_strategy
    original_select=select_current_replenishment_army_v1
    army_fields=('army_id','soldiers','army_state','move_target_province_id','route_province_ids','current_province_id')
    snapshot_fields=('paused','snapshot_id','revision','army_strengths_status','army_strengths_queried_snapshot_id','army_strengths_queried_revision')
    def consumed_selector(armies,snapshot,*,active_war_ids):
        armies=list(armies);wars=tuple(active_war_ids)
        projection={key:copy.deepcopy(snapshot[key]) for key in snapshot_fields if key in snapshot}
        if 'army_strengths' in snapshot:
            projection['army_strengths']=None if snapshot['army_strengths'] is None else [compact(row) for row in snapshot['army_strengths']]
        request=dict(schema='xar.current-replenishment-selector-input/v1',armies=[{key:copy.deepcopy(army[key]) for key in army_fields if key in army} for army in armies],snapshot=projection,active_war_ids=list(wars))
        def reference():return original_select(armies,snapshot,active_war_ids=wars)[1]
        receipt=consumer_invoke(request,reference)
        selected=next((army for army in armies if army.get('army_id')==receipt['selected_army_id']),None)
        if receipt['selected_army_id'] is not None and selected is None:raise RuntimeError('actual Java selected identity is absent from actual observed roster')
        return selected,receipt
    # Run the complete unchanged original suite in its original mode. It also
    # asserts Python-internal core call counts; those are baseline assertions.
    consumer_phase='reference'
    with patch.object(consumer_strategy,'select_current_replenishment_army_v1',side_effect=consumed_selector):
        suite=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(original))
    if suite.testsRun!=1 or not suite.wasSuccessful() or suite.skipped:
        raise RuntimeError('complete original normal-plan consumer suite failed or skipped')
    original_consumer_baseline=list(consumer_inputs)
    if consumer_packet is not None:
        # Execute the same real CallbackGameplayDriver -> Service -> strategy
        # consumer again with actual Java return bytes and no Python fallback.
        consumer_inputs.clear();consumer_phase='java'
        def actual_plan(name,sources,status):
            armies=[original._army(row['army_id'],soldiers=row['current_soldiers'],province_id=2630+index,controllable=True,army_state='regular',army_state_code=1,route_province_ids=[]) for index,row in enumerate(sources)]
            before=copy.deepcopy((armies,sources));provider_before=consumer_cursor
            def frame(revision):
                return {**original._snapshot(revision),'snapshot_id':'normal-refill-frame','army_strengths_queried_snapshot_id':'normal-refill-frame','army_strengths_queried_revision':revision}
            from xar_autoplayer.bridge.driver import CallbackGameplayDriver as ConsumerDriver
            with patch('test_gameplay_bridge._snapshot',side_effect=frame),patch.object(consumer_strategy,'select_current_replenishment_army_v1',side_effect=consumed_selector),patch.object(ConsumerDriver,'execute_step',side_effect=AssertionError('planner-only consumer must not submit actions')) as action_guard:
                returned=original._native_war_plan(player=armies[0],players=armies,enemies=[],score=17,date_raw=53216640,objective=2640,army_strengths=sources,army_strengths_status=status,move_route_preview_supported=False,steps=('query-army-strengths-v1','life-advance','move-army-11-to-2640','move-army-22-to-2640'))
            if consumer_cursor-provider_before!=1 or action_guard.call_count!=0:raise RuntimeError('actual strategy consumer repeated provider call or submitted an action')
            if before!=(armies,sources):raise RuntimeError('actual Java strategy consumer mutated source fixture')
            receipt=next((war.get('current_replenishment_selection_v1') for war in returned.get('active_wars',[]) if war.get('current_replenishment_selection_v1')),None)
            consumer_plans.append(dict(id=name,selected_step=returned['selected_step'],receipt=receipt,army_strength_scope=returned.get('army_strength_scope'),fixture='test_gameplay_bridge._native_war_plan actual CallbackGameplayDriver and GameplayBridgeService',java_provider_calls=consumer_cursor-provider_before,native_actions_submitted=action_guard.call_count,query_selection_only=True))
        actual_plan('current-positive-versus-zero',[copy.deepcopy(rows[0]),copy.deepcopy(rows[1])],'available')
        actual_plan('actual-force-stays-primary',[copy.deepcopy(rows[2]),copy.deepcopy(rows[1])],'available')
        actual_plan('missing-current-permission-keeps-legacy',[copy.deepcopy(rows[3]),copy.deepcopy(rows[1])],'available')
        actual_plan('absent-current-query-is-requested-once',[copy.deepcopy(rows[0]),copy.deepcopy(rows[1])],None)
else:
    original.CurrentReplenishmentNormalPlanV1Tests('test_normal_plan_dispatches_equal_force_without_consuming_future_troops').test_normal_plan_dispatches_equal_force_without_consuming_future_troops()
consumer=json.loads(consumer_output.read_text(encoding='utf-8'))
consumers=[]
for name,out in consumer.items():
    receipt=next((w.get('current_replenishment_selection_v1') for w in out.get('active_wars',[]) if w.get('current_replenishment_selection_v1')),None)
    consumers.append(dict(id=name,selected_step=out['selected_step'],receipt=receipt,army_strength_scope=out.get('army_strength_scope')))
if consumer_mode and consumer_packet is not None:
    if len(consumer_plans)!=len(consumers):raise RuntimeError('actual Java normal-plan consumer count differs')
    for actual,expected in zip(consumer_plans,consumers):
        if any(actual[key]!=expected[key] for key in ('id','selected_step','receipt','army_strength_scope')):
            raise RuntimeError('actual Java output changed original strategy Service/query consumer')
refs=[]
for path in paths:
    data=(root/path).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=before[path]:raise RuntimeError('source drift during capture: '+path)
    refs.append(dict(path=path,bytes=len(data),sha256=digest))
payload=dict(schema='xar.armyselector.original-producer-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; original pure producer and actual memory-service normal strategy consumer; no Game or native submission',original_normal_plan_test_executed=True,source_refs=refs,rows=[compact(r) for r in rows],cases=cases,projections=projections,refreshes=refreshes,consumers=consumers )
if consumer_mode:
    payload['actual_normal_plan_consumers']=consumer_plans
payload=consumer_finish(payload)
print(json.dumps(payload,separators=(',',':')))
""";

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && ("--consumer-baseline".equals(args[0]) || "--compiled-consumers".equals(args[0]))) { consumerProbe(args); return; }
        if (args.length == 5 && "--gzip-existing".equals(args[0])) {
            Path source = Path.of(args[1]).toRealPath();
            long expectedBytes = Long.parseLong(args[4]);
            if (expectedBytes < 1 || expectedBytes > MAX_RAW_BYTES || Files.size(source) != expectedBytes)
                throw new IOException("existing raw golden size differs");
            byte[] bytes = Files.readAllBytes(source);
            String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
            if (!digest.equals(args[3])) throw new IOException("existing raw golden SHA-256 differs");
            writeGzip(Path.of(args[2]), bytes);
            System.out.println("lossless gzip only; original producer not rerun; raw_bytes=" + bytes.length + " raw_sha256=" + digest);
            return;
        }
        if (args.length != 5) throw new IllegalArgumentException("repo-root python-exe D-scratch owned-output machine-id required");
        Path root = Path.of(args[0]).toRealPath();
        Path scratch = Path.of(args[2]).toAbsolutePath().normalize();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!scratch.toString().toLowerCase(Locale.ROOT).startsWith("d:")
                || !output.getParent().equals(scratch)) throw new IllegalArgumentException("capture output must be directly inside the owned D scratch directory");
        Files.createDirectories(scratch);
        if (!scratch.toRealPath().equals(scratch)) throw new IllegalArgumentException("capture scratch must not redirect through a link");
        if (Files.exists(output)) throw new IOException("capture cannot overwrite evidence");
        Path stdout = Files.createTempFile(scratch, "armyselector-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "armyselector-capture-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString(), args[4], scratch.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process child = builder.start();
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IOException("original producer capture timeout");
        }
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original producer capture exit " + child.exitValue());
        byte[] bytes = Files.readAllBytes(stdout);
        if (bytes.length == 0 || bytes.length > MAX_RAW_BYTES) throw new IOException("golden exceeds bounded sample budget: " + bytes.length);
        writeGzip(output, bytes);
        System.out.println("machine_id=" + args[4] + " observed_at_utc=" + Instant.now() + " bytes=" + bytes.length);
    }

    private static void writeGzip(Path requestedOutput, byte[] bytes) throws IOException {
        Path output = requestedOutput.toAbsolutePath().normalize();
        if (!output.toString().toLowerCase(Locale.ROOT).startsWith("d:")
                || !output.getFileName().toString().endsWith(".json.gz"))
            throw new IllegalArgumentException("gzip golden requires a bounded D .json.gz output");
        if (Files.exists(output)) throw new IOException("capture cannot overwrite evidence");
        ByteArrayOutputStream compressed = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(compressed)) { gzip.write(bytes); }
        byte[] packed = compressed.toByteArray();
        if (packed.length > MAX_GZIP_BYTES) throw new IOException("compressed golden exceeds 24KiB");
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            byte[] restored = gzip.readNBytes(MAX_RAW_BYTES + 1);
            if (!Arrays.equals(bytes, restored)) throw new IOException("gzip roundtrip changed original golden bytes");
        }
        Files.createDirectories(output.getParent());
        Files.write(output, packed, java.nio.file.StandardOpenOption.CREATE_NEW);
    }

    private static final int CONSUMER_RAW_LIMIT = 256 * 1024;
    private static final int CONSUMER_GZIP_LIMIT = 24 * 1024;
    private static final int CONSUMER_PACKET_LIMIT = 512 * 1024;
    private static final ObjectMapper CONSUMER_JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    /**
     * Existing collector's qualified compiled mode. Only fixture transport is
     * substituted; the original complete tests, Service and queue consumers run.
     */
    private static void consumerProbe(String[] args) throws IOException, InterruptedException {
        boolean compiled = args.length > 0 && "--compiled-consumers".equals(args[0]);
        if ((!compiled && (args.length != 7 || !"--consumer-baseline".equals(args[0])))
                || (compiled && args.length != 13)) {
            throw new IllegalArgumentException("baseline: mode/repo/python/output/fresh-scratch/machine/owned-root; compiled: mode/repo/python/golden/output/fresh-scratch/main-jar/main-sha/golden-sha/test-classes/test-class-sha/machine/owned-root");
        }
        Path repository = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[compiled ? 4 : 3]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[compiled ? 5 : 4]).toAbsolutePath().normalize();
        String machine = args[compiled ? 11 : 5];
        Path ownedRoot = Path.of(args[compiled ? 12 : 6]).toAbsolutePath().normalize();
        if (!output.getParent().equals(ownedRoot) || !scratch.getParent().equals(ownedRoot)
                || !Files.isDirectory(ownedRoot) || Files.isSymbolicLink(ownedRoot)
                || !ownedRoot.toRealPath().equals(ownedRoot)
                || !output.getFileName().toString().endsWith(".json.gz")
                || Files.exists(output) || Files.exists(scratch) || machine.isBlank()) {
            throw new IllegalArgumentException("fresh bounded owned output/scratch and explicit actual machine required");
        }
        Path mainJar = null, golden = null, testClasses = null, packetPath = null, classFile = null;
        String mainSha = null, goldenSha = null, classSha = null, packetSha = null;
        if (compiled) {
            mainJar = Path.of(args[6]).toAbsolutePath().normalize();
            golden = Path.of(args[3]).toAbsolutePath().normalize();
            testClasses = Path.of(args[9]).toAbsolutePath().normalize();
            if (!consumerOrigin(ArmySelectorCodec.class).equals(mainJar)
                    || !consumerOrigin(CaptureArmySelectorGolden.class).equals(testClasses)) {
                throw new IllegalStateException("actual compiled producer or consumer bridge origin differs");
            }
            classFile = testClasses.resolve(CaptureArmySelectorGolden.class.getName().replace('.', '/') + ".class");
            mainSha = consumerHash(mainJar, 16 * 1024 * 1024);
            goldenSha = consumerHash(golden, CONSUMER_RAW_LIMIT);
            classSha = consumerHash(classFile, 1024 * 1024);
            if (!mainSha.equals(args[7]) || !goldenSha.equals(args[8]) || !classSha.equals(args[10])) {
                throw new IllegalStateException("actual main/reference/compiled test class SHA differs");
            }
            JsonNode reference = CONSUMER_JSON.readTree(consumerReadGolden(golden));
            if (!"xar.armyselector.original-consumer-baseline/v1".equals(reference.path("schema").asText())
                    || !reference.path("consumer_inputs").isArray()
                    || reference.path("consumer_inputs").isEmpty()
                    || reference.path("consumer_inputs").size() > 512) {
                throw new IllegalArgumentException("complete original consumer baseline is required");
            }
            ObjectNode packet = CONSUMER_JSON.createObjectNode();
            packet.put("schema", "xar.compiled-army-consumer-wire-packet/v1");
            packet.put("family", "armyselector"); packet.put("observed_at_utc", Instant.now().toString());
            packet.put("qualified_main_jar", mainJar.toString()); packet.put("qualified_main_jar_sha256", mainSha);
            packet.put("qualified_test_classes", testClasses.toString()); packet.put("qualified_test_class_sha256", classSha);
            packet.put("original_golden_sha256", goldenSha);
            ArrayNode cases = packet.putArray("cases");
            for (JsonNode row : reference.path("consumer_inputs")) {
                if (!row.path("input_json").isTextual() || !row.path("accepted").isBoolean()) {
                    throw new IllegalArgumentException("original consumer operand/acceptance fields differ");
                }
                String raw = row.get("input_json").textValue(); byte[] wire = null;
                try { wire = ArmySelectorCodec.select(raw.getBytes(StandardCharsets.UTF_8)); }
                catch (IllegalArgumentException rejection) {
                    if (row.get("accepted").booleanValue()) throw rejection;
                }
                if ((wire != null) != row.get("accepted").booleanValue()) {
                    throw new IllegalStateException("actual compiled producer acceptance differs from original consumer baseline");
                }
                ObjectNode value = cases.addObject(); value.put("input_json", raw);
                value.put("accepted", wire != null);
                if (wire == null) value.putNull("output_json");
                else {
                    if (!row.path("output_json").isTextual()
                            || !CONSUMER_JSON.readTree(wire).equals(CONSUMER_JSON.readTree(row.get("output_json").textValue()))) {
                        throw new IllegalStateException("actual Java return differs before original consumer transport");
                    }
                    value.put("output_json", new String(wire, StandardCharsets.UTF_8));
                }
            }
            byte[] packetBytes = CONSUMER_JSON.writeValueAsBytes(packet);
            if (packetBytes.length > CONSUMER_PACKET_LIMIT) throw new IllegalArgumentException("compiled return packet exceeds finite transport profile");
            packetPath = output.resolveSibling(output.getFileName().toString() + ".java-wire-packet.json");
            Files.createDirectories(output.getParent());
            Files.write(packetPath, packetBytes, java.nio.file.StandardOpenOption.CREATE_NEW);
            packetSha = consumerHash(packetPath, CONSUMER_PACKET_LIMIT);
        }
        Files.createDirectories(scratch);
        if (!scratch.toRealPath().equals(scratch)) throw new IllegalArgumentException("consumer scratch redirects through a link");
        Path rawOutput = scratch.resolve("original-consumers.raw.json");
        Path errors = scratch.resolve("original-consumers.stderr.log");
        java.util.List<String> command = new java.util.ArrayList<>(java.util.List.of(args[2], "-B", "-X", "utf8", "-c", SCRIPT));
        command.add(repository.toString()); command.add(machine);
        command.add(scratch.toString());
        command.add(packetPath == null ? "" : packetPath.toString());
        command.add(compiled ? "compiled" : "baseline");
        ProcessBuilder builder = new ProcessBuilder(command).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONHASHSEED", "0");
        builder.environment().put("PYTHONPATH", repository + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/src") + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        for (String name : java.util.List.of("XAR_DAILY_QUEUE_APPEND_FIRST_OUTPUT", "XAR_ASSAULT_FIRST_REMOVAL_FIRST_OUTPUT", "XAR_CURRENT_REPLENISHMENT_FIRST_OUTPUT")) {
            builder.environment().remove(name);
        }
        Process child = builder.start();
        byte[] rawProof, errorBytes;
        boolean timedOut;
        try (var readers = java.util.concurrent.Executors.newFixedThreadPool(2)) {
            var stdout = readers.submit(() -> { try (var stream = child.getInputStream()) { return stream.readNBytes(CONSUMER_RAW_LIMIT + 1); } });
            var stderr = readers.submit(() -> { try (var stream = child.getErrorStream()) { return stream.readNBytes(65_537); } });
            timedOut = !child.waitFor(90, TimeUnit.SECONDS);
            if (timedOut) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly().waitFor(); }
            try { rawProof = stdout.get(); errorBytes = stderr.get(); }
            catch (java.util.concurrent.ExecutionException failure) { throw new IOException("bounded consumer stream failed", failure.getCause()); }
        }
        Files.write(rawOutput, java.util.Arrays.copyOf(rawProof, Math.min(rawProof.length, CONSUMER_RAW_LIMIT)), java.nio.file.StandardOpenOption.CREATE_NEW);
        Files.write(errors, java.util.Arrays.copyOf(errorBytes, Math.min(errorBytes.length, 65_536)), java.nio.file.StandardOpenOption.CREATE_NEW);
        if (errorBytes.length > 65_536 || rawProof.length > CONSUMER_RAW_LIMIT) throw new IOException("actual consumer stream exceeded hard profile; bounded partial evidence retained");
        if (timedOut) throw new IOException("actual original consumer probe timed out; bounded evidence retained; unknown result is not retried");
        System.err.println("original_consumer_stderr_bytes=" + errorBytes.length + " retained=" + errors);
        if (child.exitValue() != 0) throw new IOException("actual original consumer probe exit " + child.exitValue());
        if (rawProof.length < 1) throw new IOException("actual consumer proof is empty");
        JsonNode proof = CONSUMER_JSON.readTree(rawProof);
        String expectedSchema = compiled ? "xar.armyselector.compiled-java-consumer-probe/v1" : "xar.armyselector.original-consumer-baseline/v1";
        if (!expectedSchema.equals(proof.path("schema").asText())
                || !proof.path("transport_contract").path("all_original_tests_passed").isBoolean()
                || !proof.path("transport_contract").path("all_original_tests_passed").booleanValue()) {
            throw new IOException("actual complete original consumer proof is missing");
        }
        if (compiled && (!consumerHash(mainJar, 16 * 1024 * 1024).equals(mainSha)
                || !consumerHash(golden, CONSUMER_RAW_LIMIT).equals(goldenSha)
                || !consumerHash(classFile, 1024 * 1024).equals(classSha)
                || !consumerHash(packetPath, CONSUMER_PACKET_LIMIT).equals(packetSha))) {
            throw new IOException("qualified artifact/reference/return packet drifted during actual consumer calls");
        }
        java.io.ByteArrayOutputStream packed = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(packed)) { gzip.write(rawProof); }
        byte[] zipped = packed.toByteArray();
        if (zipped.length > CONSUMER_GZIP_LIMIT) throw new IOException("actual consumer proof exceeds bounded gzip profile");
        try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(zipped))) {
            if (!java.util.Arrays.equals(rawProof, gzip.readNBytes(CONSUMER_RAW_LIMIT + 1))) throw new IOException("consumer proof gzip lost original bytes");
        }
        Files.createDirectories(output.getParent());
        Files.write(output, zipped, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + machine + " family=armyselector compiled=" + compiled
                + " raw_bytes=" + rawProof.length + " gzip_bytes=" + zipped.length + " original_consumers_completed=true");
    }
    private static Path consumerOrigin(Class<?> type) throws IOException {
        try { return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize(); }
        catch (URISyntaxException failure) { throw new IOException("compiled class origin is invalid", failure); }
    }
    private static String consumerHash(Path file, int maximum) throws IOException {
        if (!Files.isRegularFile(file) || Files.size(file) < 1 || Files.size(file) > maximum) throw new IOException("qualified input path/size rejected");
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException("SHA-256 unavailable", failure); }
    }
    private static byte[] consumerReadGolden(Path file) throws IOException {
        try (java.io.InputStream raw = Files.newInputStream(file);
                java.io.InputStream input = file.getFileName().toString().endsWith(".gz") ? new java.util.zip.GZIPInputStream(raw) : raw) {
            byte[] bytes = input.readNBytes(CONSUMER_RAW_LIMIT + 1);
            if (bytes.length == 0 || bytes.length > CONSUMER_RAW_LIMIT) throw new IOException("consumer baseline raw size rejected");
            return bytes;
        }
    }

}
