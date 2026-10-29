package org.xar.ck3.control.wave2.military.prestore;

import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.HexFormat;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPOutputStream;

/** Shared-Job-only sampling of the original full movement/prestore producer and original Service helper. */
public final class CapturePrestoreGolden {
    private CapturePrestoreGolden() { }
    public static String originalProgram() { return PROGRAM; }
    public static void main(String[] args) throws IOException, InterruptedException, NoSuchAlgorithmException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path root = Path.of(args[0]).toRealPath(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path owned = Path.of(System.getProperty("java.io.tmpdir")).toRealPath()
                .resolve("movement-captures/prestore").normalize();
        if (!output.startsWith(owned) || Files.exists(output)) { throw new IllegalArgumentException("fresh owned capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, root.toString(), args[3]));
        builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(262_145); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                throw new IOException("original prestore capture timeout");
            }
            try { bytes = response.get(); }
            catch (ExecutionException error) { throw new IOException("original prestore capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 262_144) {
            throw new IOException("capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        }
        ByteArrayOutputStream compressed = new ByteArrayOutputStream();
        try (var gzip = new GZIPOutputStream(compressed)) { gzip.write(bytes); }
        byte[] payload = compressed.toByteArray();
        if (payload.length > 98_304) { throw new IOException("compressed prestore capture exceeds 96 KiB"); }
        Files.createDirectories(output.getParent()); Files.write(output, payload, StandardOpenOption.CREATE_NEW);
        System.out.println("captured original prestore raw_bytes=" + bytes.length
                + " raw_sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))
                + " gzip_bytes=" + payload.length
                + " gzip_sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload))
                + " machine_id=" + args[3]);
    }


    /** Existing harness's compiled-consumer mode; no extra JVM, Driver replacement or Python business fallback. */
    public static byte[] runCompiledConsumer(Path root, String python, Path fixtureRoot,
            Path wholeConsumer, Path nativeWire, byte[] initialization,
            java.util.function.Function<byte[], byte[]> exchange) throws IOException, InterruptedException {
        if (Files.exists(fixtureRoot)) { throw new IllegalArgumentException("create-new fixture root required"); }
        Path scratch = Path.of(System.getProperty("java.io.tmpdir")).toRealPath();
        if (!fixtureRoot.toAbsolutePath().normalize().startsWith(scratch) || fixtureRoot.equals(scratch)) {
            throw new IllegalArgumentException("D-only allocated fixture root required");
        }
        Files.createDirectory(fixtureRoot);
        ProcessBuilder builder = new ProcessBuilder(List.of(python, "-B", "-X", "utf8", "-c", CONSUMER_PROGRAM,
                root.toString(), fixtureRoot.toString(), wholeConsumer.toString(), nativeWire.toString()));
        builder.directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONUTF8", "1");
        Process child = builder.start();
        try (var workers = Executors.newFixedThreadPool(2)) {
            var errors = workers.submit(() -> {
                try (var stream = child.getErrorStream()) {
                    byte[] bytes = stream.readNBytes(6_145);
                    System.err.write(bytes, 0, Math.min(bytes.length, 6_144));
                    if (bytes.length > 6_144) {
                        child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                        throw new IOException("original consumer stderr exceeded 6 KiB; first 6 KiB retained");
                    }
                    return bytes.length;
                }
            });
            var response = workers.submit(() -> {
                try (var input = new java.io.BufferedInputStream(child.getInputStream());
                        var output = new java.io.BufferedOutputStream(child.getOutputStream())) {
                    output.write(initialization); output.write('\n'); output.flush();
                    byte[] completed = null; int count = 0;
                    byte[] line;
                    while ((line = readConsumerLine(input)) != null) {
                        var node = org.xar.ck3.control.contracts.StrictJson.parse(line, 131_072);
                        if (node.has("completed")) {
                            if (completed != null || !node.path("completed").isBoolean()
                                    || !node.path("completed").booleanValue()) throw new IOException("duplicate/malformed consumer completion");
                            completed = line;
                        } else {
                            if (completed != null || ++count > 4_096) throw new IOException("late or excessive consumer request");
                            byte[] result = exchange.apply(line);
                            output.write(result); output.write('\n'); output.flush();
                        }
                    }
                    if (completed == null || count == 0) throw new IOException("no actual original consumer completion");
                    return completed;
                }
            });
            if (!child.waitFor(90, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IOException("original consumer timeout");
            }
            try {
                byte[] result = response.get();
                errors.get();
                if (child.exitValue() != 0) throw new IOException("original consumer exit " + child.exitValue());
                return result;
            } catch (ExecutionException failure) {
                throw new IOException("original consumer byte exchange failed", failure.getCause());
            }
        } finally {
            if (child.isAlive()) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            }
        }
    }

    private static byte[] readConsumerLine(java.io.InputStream input) throws IOException {
        var bytes = new ByteArrayOutputStream(); int value;
        while ((value = input.read()) != -1) {
            if (value == '\n') { return bytes.toByteArray(); }
            if (bytes.size() >= 131_072) throw new IOException("consumer JSONL frame exceeds bound");
            bytes.write(value);
        }
        if (bytes.size() != 0) throw new IOException("unterminated consumer JSONL frame");
        return null;
    }

    private static final String CONSUMER_PROGRAM = """
import contextlib,copy,gzip,hashlib,importlib.util,io,json,pathlib,sys,types,unittest
root=pathlib.Path(sys.argv[1]); fixture=pathlib.Path(sys.argv[2]); whole_source=pathlib.Path(sys.argv[3]); native_wire=pathlib.Path(sys.argv[4])
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'tools')]
protocol_out=sys.stdout.buffer; protocol_in=sys.stdin.buffer
initial=protocol_in.readline(131074)
if not initial.endswith(b'\\n') or len(initial)>131073:raise RuntimeError('bounded init frame required')
init=json.loads(initial)
sequence=0; counters={key:0 for key in ('COUNTY_NORMALIZE','MOVEMENT_NORMALIZE','PRESTORE_PROJECT','DISEMBARK_NORMALIZE','DISEMBARK_PROJECT')}
rejected=0; exact_negative_tokens=0
def invoke(operation,value):
    global sequence,rejected,exact_negative_tokens
    raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    if not 0<len(raw)<=32768:raise RuntimeError('original callback input exceeds token budget')
    sequence+=1; digest=hashlib.sha256(raw).hexdigest()
    request=dict(sequence=sequence,operation=operation,input_json=raw.decode('utf-8'),input_sha256=digest)
    line=json.dumps(request,ensure_ascii=False,separators=(',',':')).encode('utf-8')+b'\\n'
    protocol_out.write(line);protocol_out.flush()
    response=protocol_in.readline(131074)
    if not response.endswith(b'\\n') or len(response)>131073:raise RuntimeError('bounded Java return frame required')
    result=json.loads(response)
    if set(result)!={'sequence','operation','input_sha256','status','result_json','result_sha256','error_code'}:raise RuntimeError('Java return field drift')
    if type(result['sequence']) is not int or result['sequence']!=sequence or result['operation']!=operation or result['input_sha256']!=digest:raise RuntimeError('Java return identity drift')
    counters[operation]+=1
    if result['status']=='REJECTED':
        if result['result_json'] is not None or result['result_sha256'] is not None or result['error_code']!='CONTRACT_REJECTED':raise RuntimeError('invalid Java refusal')
        rejected+=1
        if b'1.0' in raw or b'true' in raw or b'false' in raw:exact_negative_tokens+=1
        raise ValueError('compiled Java contract rejected original token bytes')
    if result['status']!='ACCEPTED' or result['error_code'] is not None or type(result['result_json']) is not str:raise RuntimeError('invalid Java acceptance')
    returned=result['result_json'].encode('utf-8')
    if not 0<len(returned)<=32768 or hashlib.sha256(returned).hexdigest()!=result['result_sha256']:raise RuntimeError('Java returned raw bytes/SHA drift')
    return json.loads(returned)
def java_county(value,*,current_soldiers,name='county_entry_inputs_v1'):
    return invoke('COUNTY_NORMALIZE',dict(value=value,current_soldiers=current_soldiers))
def java_movement(value,*,name):
    return invoke('MOVEMENT_NORMALIZE',value)
def java_prestore(same_query_strength,*,arrival_transition,army_context,movement_prefix=None):
    return invoke('PRESTORE_PROJECT',dict(strength=same_query_strength,arrival_transition=arrival_transition,army_context=army_context,movement_prefix=movement_prefix))
def java_days(value):
    return invoke('DISEMBARK_NORMALIZE',value)
def java_days_project(value,*,source_provenance):
    return invoke('DISEMBARK_PROJECT',dict(raw=value,source_provenance=source_provenance))
from xar_autoplayer.bridge import war_contract,service,army_current_disembark_penalty_contract as days
from xar_autoplayer.bridge import army_current_unit_arrival_prestore_disembark_write_projection as prestore
war_contract.normalize_army_county_entry_inputs_v1=java_county
war_contract._normalize_current_movement_progress=java_movement
prestore.project_current_unit_arrival_prestore_disembark_write_v1=java_prestore
service.project_current_unit_arrival_prestore_disembark_write_v1=java_prestore
days.normalize_current_disembark_penalty_v1=java_days
war_contract.normalize_current_disembark_penalty_v1=java_days
days.project_current_disembark_penalty_v1=java_days_project
service.project_current_disembark_penalty_v1=java_days_project
class Utf8Capture(io.TextIOBase):
    def __init__(self):self.buffer=io.BytesIO()
    def write(self,value):self.buffer.write(value.encode('utf-8'));return len(value)
    def flush(self):pass
def same(left,right,path):
    if type(left) is not type(right):raise RuntimeError('JSON domain drift at '+path)
    if type(left) is dict:
        if set(left)!=set(right):raise RuntimeError('JSON field drift at '+path)
        for key in left:same(left[key],right[key],path+'.'+key)
    elif type(left) is list:
        if len(left)!=len(right):raise RuntimeError('JSON array drift at '+path)
        for index,(a,b) in enumerate(zip(left,right)):same(a,b,path+'['+str(index)+']')
    elif left!=right:raise RuntimeError('JSON scalar drift at '+path)
def golden(path,compressed=False):
    raw=pathlib.Path(path).read_bytes()
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(262145)
    if len(raw)>262144:raise RuntimeError('bounded original golden required')
    return json.loads(raw)
def recipe(program,expected,fields):
    capture=Utf8Capture();old_argv=sys.argv
    try:
        sys.argv=['existing-capture',str(root),init['machine_id']]
        with contextlib.redirect_stdout(capture):
            exec(compile(program,'<existing-original-capture>','exec'),{'__name__':'_original_capture'})
    finally:sys.argv=old_argv
    raw=capture.buffer.getvalue()
    if len(raw)>262144:raise RuntimeError('bounded original recipe output required')
    actual=json.loads(raw)
    for field in fields:same(actual[field],expected[field],field)
    return actual
county=recipe(init['county_program'],golden(init['county_golden']),('original_tests','original_subtests','original_skipped','contract_cases','risk_cases'))
if county['original_tests']!=18 or county['original_subtests']!=43 or county['original_skipped']!=0:raise RuntimeError('18 parent/43 subtests incomplete')
arrival=recipe(init['prestore_program'],golden(init['prestore_golden'],True),('cases','county_risks','movements','rejections'))
current_days=recipe(init['disembark_program'],golden(init['disembark_golden']),('samples','rejections','service_rows'))
if len(arrival['cases'])!=15 or len(current_days['service_rows'])!=5:raise RuntimeError('original complete Service corpus changed')
compact_outputs=[]
def compact_sink(path,value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    compact_outputs.append(dict(name=str(path.relative_to(fixture)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    if len(json.dumps(compact_outputs,separators=(',',':')).encode('utf-8'))>8192:raise RuntimeError('compact original output records exceed 8 KiB')
if not native_wire.is_file():raise RuntimeError('original compiled whole fixture is unavailable; no whole-consumer qualification')
spec=importlib.util.spec_from_file_location('movement_original_whole_consumer',whole_source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module._OPTIONS=types.SimpleNamespace(source_root=root,native_wire=native_wire,output_dir=fixture,
    java_prestore=java_prestore,java_movement=java_movement,java_days=java_days,compact_sink=compact_sink)
suite=unittest.TestSuite([module.CurrentUnitArrivalPrestoreDisembarkWriteWholeService12004Tests(
    'test_loaded_rule_value_reaches_the_conditional_fixed_write_through_registered_routes')])
with contextlib.redirect_stdout(sys.stderr):
    result=unittest.TextTestRunner(verbosity=1,stream=sys.stderr).run(suite)
if result.testsRun!=1 or not result.wasSuccessful() or result.skipped:raise RuntimeError('original native Driver/Service/MCP consumer failed or skipped')
if not all(counters.values()) or exact_negative_tokens==0:raise RuntimeError('Java production operations or original negative-token path unexecuted')
summary=dict(completed=True,schema='xar.compiled-movement-original-consumers/v1',machine_id=init['machine_id'],
    original_parent_tests=18,original_subtests=43,original_skipped=0,original_prestore_service_cases=15,
    original_current_days_service_cases=5,original_whole_consumer_tests=1,registered_whole_passes=14,
    java_calls=counters,java_rejections=rejected,negative_token_calls=exact_negative_tokens,compact_original_outputs=compact_outputs,
    no_live_game=True,no_native_producer_reexecution=True,production_deployment=False)
protocol_out.write(json.dumps(summary,ensure_ascii=False,separators=(',',':')).encode('utf-8')+b'\\n');protocol_out.flush()
""";

    private static final String PROGRAM = """
import copy,datetime,hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);machine=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'tools'))
from xar_autoplayer.bridge.war_contract import normalize_army_strengths,_normalize_current_movement_progress
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.army_current_unit_arrival_prestore_disembark_write_projection import PROJECTION_KEY
from xar_autoplayer.bridge.army_current_unit_next_movement_prefix_projection import PROJECTION_KEY as PREFIX
from xar_autoplayer.bridge.army_current_unit_next_arrival_transition_projection import PROJECTION_KEY as ARRIVAL
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/'+name+'.py' for name in ('war_contract','service','army_current_disembark_penalty_contract','army_current_unit_arrival_prestore_disembark_write_projection','army_county_entry_route_risk_projection','army_county_entry_inputs_contract','army_current_unit_next_movement_prefix_projection','army_current_unit_next_first_edge_selection_projection','army_current_unit_next_arrival_transition_projection','army_current_unit_new_date_entry_normalization_projection','army_current_unit_new_date_schedule_inputs_contract','army_monthly_loss_budget_inputs_contract')]
before={path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in paths}
def movement():return dict(status='available',source='native_current_route_edge',unit_state_raw=6,accumulated_movement_weight_raw=100,cached_edge_speed_raw=7,normalized_edge_progress=dict(raw=94339,scale=100000),first_route_edge_remaining_duration=dict(raw=85714,scale=100000),unavailable_reason=None,native_army_movement_admission=True,first_route_edge_weight_cost_raw=106,first_edge_arrival_provider_byte_e_u8=0,first_route_target_province_type_tag_u32=0x50726F76,current_province_type_tag_u32=0x50726F76,unit_kind_18_raw_i32=0,current_province_definition_byte_1b_u8=0,first_route_target_province_definition_byte_1b_u8=1,loaded_disembark_penalty_days_rule_i32=18)
def row():
    x=dict(status='available',army_id=16777217,native_carmy_id=33554433,scope_role='player',war_ids=[],regiment_count=0,current_soldiers=100,maximum_soldiers=100,ai_base_power_raw=0,ai_base_power_scale=100000,unavailable_reason=None,current_movement_progress=movement())
    x['current_disembark_penalty_v1']=dict(schema_version=1,source='native_current_disembark_penalty_days_12003',status='available',remaining_days=12,unavailable_reason=None)
    x['native_army_resolution_v1']=dict(status='available',ready=True,branch='reference_absent',raw_reference=-1,reference_index=None,storage_capacity=None,entry_full_id=None)
    x['monthly_loss_budget_inputs_v1']=dict(status='unavailable',ready=False,unavailable_reason='capture_partial_monthly_inputs',scale=100000,unit_native_170_raw=0,army_gathering_count_raw=None,native_unit_in_combat=None,native_unit_gathering=None,native_fleet_supply_loss_suppressed=None,commander_valid=None,loaded_supply_state_levels=None,loaded_supply_state_fractions_raw=None,commander_supply_modifier_id=None,commander_supply_modifier_raw=None)
    x['current_unit_new_date_callback_entry_inputs_v1']=dict(schema_version=1,source='native_current_unit_new_date_callback_entry_inputs_12004',capture_boundary='current_query_before_unit_new_date_stage',status='available',ready=True,unavailable_reason=None,subject_army_id_u32=x['army_id'],subject_carmy_id_u32=x['native_carmy_id'],unit_route_count_i32=2)
    x['current_unit_new_date_schedule_inputs_v1']=dict(schema_version=1,source='native_current_unit_new_date_schedule_inputs_12004',capture_boundary='current_query_before_unit_new_date_stage',status='available',ready=True,unavailable_reason=None,subject_army_id_u32=x['army_id'],subject_carmy_id_u32=x['native_carmy_id'],vector_header_count_i32=4,subject_stored_id_occurrence_count_i32=2,vector_data_present=True,subject_stored_id_positions=[1,3],actual_unit_new_date_callback_observed=False,actual_movement_or_arrival_observed=False,earlier_stage_outputs_reconstructed=False,full_daily_supply_transition_ready=False,full_monthly_ready=False)
    x['county_entry_inputs_v1']=dict(status='available',source='native_current_county_entry_inputs',unavailable_reason=None,fraction_scale=100000,soldier_scale=1,whole_soldiers=100,current_loss_budget=10,effective_fraction_raw=10000,minimum_multiplier_raw=100000,loaded_minimum_soldiers=0,condition=dict(status='available',source='current_stored_route_first_province',unavailable_reason=None,actor_character_id=29829,source_province_id=1,target_province_id=2,mode=1,passes=True),multiplier_floor_inputs_v1=dict(status='available',source='native_current_county_multiplier_floor_inputs',unavailable_reason=None,fraction_scale=100000,base_floor_raw=100000,army_1d4_nonzero_floor_raw=100000,army_1d4_raw=0))
    return x
context=dict(army_id=16777217,current_province_id=1,route_province_ids=[2,3],route_source_count=2,route_read_status='complete_nonempty')
snapshot=dict(snapshot_id='prestore:42',revision=42,native_revision=7,player_armies=[context])
scenes=[('baseline',{}),('signed_min',{'loaded_disembark_penalty_days_rule_i32':-(1<<31)}),('signed_max',{'loaded_disembark_penalty_days_rule_i32':(1<<31)-1}),('current_type_missing',{'current_province_type_tag_u32':None}),('current_type_not_province',{'current_province_type_tag_u32':1}),('unit_kind_missing',{'unit_kind_18_raw_i32':None}),('unit_kind_other',{'unit_kind_18_raw_i32':1}),('target_byte_missing',{'first_route_target_province_definition_byte_1b_u8':None}),('target_byte_zero',{'first_route_target_province_definition_byte_1b_u8':0}),('current_byte_missing',{'current_province_definition_byte_1b_u8':None}),('current_byte_nonzero',{'current_province_definition_byte_1b_u8':1}),('loaded_rule_missing',{'loaded_disembark_penalty_days_rule_i32':None}),('arrival_not_selected',{'first_route_edge_weight_cost_raw':107}),('arrival_unavailable',{'first_route_target_province_type_tag_u32':None}),('context_drift',{})]
risks=[];cases=[]
for name,changes in scenes:
    original=row();original['current_movement_progress'].update(changes)
    untouched=copy.deepcopy(original)
    normal=normalize_army_strengths([original],expected_scope=[dict(army_id=16777217,scope_role='player',war_ids=[])])
    query=dict(queried_snapshot_id='prestore:42',queried_revision=43 if name=='context_drift' else 42,queried_native_revision=7)
    actual=GameplayBridgeService._unit_next_movement_projection_rows(query,normal,snapshot=copy.deepcopy(snapshot))
    full=copy.deepcopy(actual[PROJECTION_KEY][0]);expected=full.pop('projection');risk=expected.pop('county_entry_risk_v1')
    if risk not in risks:risks.append(risk)
    selected_context=None if name=='context_drift' else copy.deepcopy(context)
    strength={key:copy.deepcopy(normal[0].get(key)) for key in ('status','army_id','native_carmy_id','current_soldiers','county_entry_inputs_v1','current_movement_progress','current_disembark_penalty_v1')}
    prefix=actual[PREFIX][0]['projection'];arrival=actual[ARRIVAL][0]['projection']
    narrow_prefix={key:copy.deepcopy(prefix[key]) for key in ('movement_prefix_input_ready','subject_army_id_u32','subject_carmy_id_u32','conditional_unit_170_raw_after_next_new_date_entry_prefix')}
    narrow_arrival={key:copy.deepcopy(arrival[key]) for key in ('arrival_transition_input_ready','conditional_first_province_assignment_selected','unavailable_reason','subject_army_id_u32','subject_carmy_id_u32','subject_stored_id_positions')}
    cases.append(dict(id=name,input_projection_not_original=True,input=dict(strength=strength,arrival_transition=narrow_arrival,army_context=selected_context,movement_prefix=narrow_prefix),query=query,snapshot=snapshot,expected_top=expected,county_risk_index=risks.index(risk),expected_service_provenance=full['source_provenance']))
    if original!=untouched:raise RuntimeError('original service helper mutated the source row')
movements=[]
base=movement();minimum={key:base[key] for key in ('status','source','unit_state_raw','accumulated_movement_weight_raw','cached_edge_speed_raw','normalized_edge_progress','first_route_edge_remaining_duration','unavailable_reason')}
for name,raw in [('minimal',minimum),('full',base),('null',None),('optional_null',dict(base,current_edge_movement_rate_raw=None,loaded_movement_lock_cutoff=None)),('extremes',dict(base,current_edge_movement_rate_raw=-(1<<63),accumulated_movement_weight_raw=(1<<63)-1,loaded_movement_lock_cutoff=dict(raw=-(1<<63),scale=100000)))]:
    movements.append(dict(id=name,input=raw,expected=_normalize_current_movement_progress(raw,name='movement')))
for status in ('available','not_applicable','unavailable'):
    timeline=dict(status=status,source='native_committed_route',native_duration_scale=100000,unavailable_reason='native_route_unavailable' if status=='unavailable' else None,native_full_route_remaining_days_q100000=-(1<<63) if status=='available' else None,committed_route_province_ids=[2] if status=='available' else None if status=='unavailable' else [],native_route_prefix_remaining_days_q100000=[-(1<<63)] if status=='available' else None if status=='unavailable' else [],projected_route_arrival_date_raws=[-(1<<31)] if status=='available' else None if status=='unavailable' else [])
    raw=dict(base,committed_route_timeline=timeline)
    movements.append(dict(id='timeline_'+status,input=raw,expected=_normalize_current_movement_progress(raw,name='movement')))
reject=[]
for key,value in [('unit_state_raw',True),('cached_edge_speed_raw',1.0),('accumulated_movement_weight_raw',1<<63),('current_province_type_tag_u32',-1),('unit_kind_18_raw_i32',1<<31),('current_province_definition_byte_1b_u8',256),('first_route_target_province_definition_byte_1b_u8',False),('loaded_disembark_penalty_days_rule_i32',1.0),('committed_route_timeline',None)]:
    raw=movement();raw[key]=value
    try:_normalize_current_movement_progress(raw,name='movement')
    except ValueError:reject.append(dict(id=key,raw_json=json.dumps(raw,separators=(',',':'))))
    else:raise RuntimeError('original movement unexpectedly accepted '+key)
refs=[]
for path in paths:
    data=(root/path).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=before[path]:raise RuntimeError('source changed during capture '+path)
    refs.append(dict(path=path,bytes=len(data),sha256=digest))
print(json.dumps(dict(schema='xar.prestore.original-producer-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='source producer and real Service helper executed on synthetic raw DTOs; saved inputs are declared projections_not_original of actual normalized rows and actual predecessor outputs; risk pool is lossless deduplication of original full output; no native callback/write/live qualification',source_refs=refs,cases=cases,county_risks=risks,movements=movements,rejections=reject),ensure_ascii=False,separators=(',',':')))
""";
}
