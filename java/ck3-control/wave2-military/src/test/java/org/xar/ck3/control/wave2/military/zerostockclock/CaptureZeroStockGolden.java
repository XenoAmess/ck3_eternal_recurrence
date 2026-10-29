package org.xar.ck3.control.wave2.military.zerostockclock;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Test-only original producer capture; shared storage scheduler supplies a bounded parent Job. */
public final class CaptureZeroStockGolden {
    private CaptureZeroStockGolden() { }
    private static final String SCRIPT = """
import copy, datetime, hashlib, json, pathlib, runpy, sys
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_zero_stock_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_update_clock_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_future_daily_supply_schedule_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_future_daily_supply_schedule_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_inputs_contract.py','ck3_autonomous_player/tests/unit/test_army_zero_stock_clock_12004.py','ck3_autonomous_player/tests/unit/test_r05_first_zero_budget_capture.py','ck3_autonomous_player/tests/unit/test_r05_zero_preparation_decision.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_zero_stock_clock_12004 import project_zero_stock_next_callback_candidate_12004 as candidate, successful_supply_occurrences_to_zero_12004 as opportunities
factory=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_army_zero_stock_clock_12004.py'))
base=factory['clock_row']();base.update(current_supply_raw=1,current_supply_capacity_raw=10000000,current_supply_change_monthly_raw=-1)
base['monthly_loss_budget_inputs_v1'].update(status='available',ready=True,unavailable_reason=None,scale=100000,native_fleet_supply_loss_suppressed=False,loaded_supply_state_levels=[60,10,0],loaded_supply_state_fractions_raw=[0,0,5000],commander_valid=True,commander_supply_modifier_id=77,commander_supply_modifier_raw=0)
base['loss_application_inputs_v1']=dict(supply_eligible_soldiers=20)
base['extension_field']=dict(source_only='declared SDK projection')
cases=[]
def apply(row,changes):
    for path,value in changes.items():
        parts=path.split('/')[1:]; owner=row
        for part in parts[:-1]:owner=owner[int(part)] if isinstance(owner,list) else owner[part]
        if isinstance(owner,list):owner[int(parts[-1])]=copy.deepcopy(value)
        else:owner[parts[-1]]=copy.deepcopy(value)
    return row
def case(name,changes):
    row=apply(copy.deepcopy(base),changes); untouched=copy.deepcopy(row); result=candidate(row)
    if row!=untouched:raise RuntimeError('original zero-stock producer mutated source row')
    cases.append(dict(name=name,changes=changes,expected=result))
case('first-zero-positive-budget',{})
case('zero-retaining-current-stock',{'/current_supply_raw':0,'/current_supply_change_monthly_raw':0})
case('zero-entry-but-positive-post-stock',{'/current_supply_raw':0,'/current_supply_change_monthly_raw':1000000})
case('unrelated-phase-unavailable',{'/future_daily_supply_schedule_inputs_v1/status':'partial','/future_daily_supply_schedule_inputs_v1/ready':False,'/future_daily_supply_schedule_inputs_v1/unavailable_reason':'phase29_unreadable','/future_daily_supply_schedule_inputs_v1/phases/29/status':'unavailable','/future_daily_supply_schedule_inputs_v1/phases/29/ready':False,'/future_daily_supply_schedule_inputs_v1/phases/29/unavailable_reason':'header_unreadable'})
case('selected-phase-empty',{'/future_daily_supply_schedule_inputs_v1/phases/1/matching_positions':[],'/future_daily_supply_schedule_inputs_v1/phases/1/subject_occurrence_count_i32':0})
case('selected-phase-unavailable',{'/future_daily_supply_schedule_inputs_v1/status':'partial','/future_daily_supply_schedule_inputs_v1/ready':False,'/future_daily_supply_schedule_inputs_v1/unavailable_reason':'phase1_unreadable','/future_daily_supply_schedule_inputs_v1/phases/1/status':'unavailable','/future_daily_supply_schedule_inputs_v1/phases/1/ready':False,'/future_daily_supply_schedule_inputs_v1/phases/1/unavailable_reason':'header_unreadable'})
case('missing-source-next-pair',{'/source_derived_next_daily_supply_frame_inputs_v1':None})
case('missing-clock',{'/army_update_clock_v1':None})
case('grace-equality-rejected',{'/army_update_clock_v1/loaded_grace_days':1})
case('combat-gate-rejected',{'/monthly_loss_budget_inputs_v1/native_unit_in_combat':True})
case('compact-gate-only-family',{'/monthly_loss_budget_inputs_v1':dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0)})
case('missing-capacity',{'/current_supply_capacity_raw':None})
case('negative-capacity',{'/current_supply_capacity_raw':-1})
case('negative-stock',{'/current_supply_raw':-1})
case('native-positive-add-wraps-to-zero',{'/current_supply_raw':(1<<63)-1,'/current_supply_capacity_raw':(1<<63)-1,'/current_supply_change_monthly_raw':1})
case('supply-fleet-suppressed',{'/monthly_loss_budget_inputs_v1/native_fleet_supply_loss_suppressed':True})
case('count-rounds-budget-to-zero',{'/loss_application_inputs_v1/supply_eligible_soldiers':19})
case('missing-eligible-count',{'/loss_application_inputs_v1/supply_eligible_soldiers':None})
case('commander-component-clamp-zero',{'/monthly_loss_budget_inputs_v1/commander_supply_modifier_raw':-100000})
case('absent-commander-unclamped-negative-budget',{'/loss_application_inputs_v1/supply_eligible_soldiers':1,'/monthly_loss_budget_inputs_v1/commander_valid':False,'/monthly_loss_budget_inputs_v1/commander_supply_modifier_id':None,'/monthly_loss_budget_inputs_v1/commander_supply_modifier_raw':None,'/monthly_loss_budget_inputs_v1/loaded_supply_state_fractions_raw':[0,0,100000*(1<<31)]})
case('empty-levels-known-zero',{'/monthly_loss_budget_inputs_v1/loaded_supply_state_levels':[]})
case('unknown-levels',{'/monthly_loss_budget_inputs_v1/status':'unavailable','/monthly_loss_budget_inputs_v1/ready':False,'/monthly_loss_budget_inputs_v1/unavailable_reason':'unknown_levels','/monthly_loss_budget_inputs_v1/loaded_supply_state_levels':None})
case('missing-army-identity',{'/army_id':None})
vectors=[]
for stock,cap,rate in ((3,100,-1),((1<<63)-1,(1<<63)-1,-1),(30000000,10000000,-1),(30000000,10000000,-1000000),(10,100,-10),(0,10000000,0),(10000000,0,0),(0,0,2000000),(0,10000000,1),(100,100,0),(100,100,None),(None,100,-1),(100,None,-1),(-1,100,-1),(100,-1,-1),(0,100,-1),((1<<63)-1,(1<<63)-1,-(1<<63)),((1<<63)-1,0,(1<<63)-1)):
    vectors.append(dict(stock=stock,capacity=cap,monthly=rate,expected=opportunities(stock,cap,rate)))
after={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
if before!=after:raise RuntimeError('original source drifted during zero-stock capture')
print(json.dumps(dict(schema='xar.java.zerostockclock.original-producer-golden.v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_basis='deterministic original test fixture and unchanged Python producers; no native execution evidence',source_sha256=before,base_row=base,cases=cases,opportunities=vectors),ensure_ascii=False,separators=(',',':')))
""";

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--gzip-existing")) { gzipExisting(args); return; }
        if (args.length != 5) throw new IllegalArgumentException("root python output scratch machine_id required");
        Path root = Path.of(args[0]).toRealPath(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[3]).toRealPath();
        if (!output.startsWith(scratch) || output.equals(scratch)) {
            throw new IOException("zero stock capture paths outside allocated roots");
        }
        if (Files.exists(output)) throw new IOException("capture refuses to replace original evidence");
        Path stdout = Files.createTempFile(scratch, "zerostock-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "zerostock-golden-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1"); builder.redirectOutput(stdout.toFile()).redirectError(ProcessBuilder.Redirect.PIPE);
        Process child = builder.start(); Diagnostics diagnostics = beginDiagnostics(child, stderr);
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IOException("zero stock producer capture timeout");
        }
        finishDiagnostics(diagnostics);
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original zero stock producer exit " + child.exitValue());
        byte[] bytes = Files.readAllBytes(stdout);
        writeGolden(bytes, output, args[4]);
    }

    private static final int RAW_MAX = 131_072;
    private static final int GZIP_MAX = 16_384;
    private static void writeGolden(byte[] raw, Path output, String machine) throws Exception {
        if (raw.length == 0 || raw.length > RAW_MAX) throw new IOException("raw golden exceeds 128KiB profile");
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw));
        java.io.ByteArrayOutputStream packed = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(packed)) { gzip.write(raw); }
        byte[] compressed = packed.toByteArray();
        if (compressed.length > GZIP_MAX) throw new IOException("gzip golden exceeds 16KiB profile; all cases retained");
        try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            if (!java.util.Arrays.equals(raw, gzip.readNBytes(RAW_MAX + 1))) throw new IOException("gzip changed original token bytes");
        }
        Files.createDirectories(output.getParent()); Files.write(output, compressed, java.nio.file.StandardOpenOption.CREATE_NEW);
        java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
        System.out.println("machine_id=" + machine + " observed_at_utc=" + Instant.now() + " raw_bytes=" + raw.length
                + " raw_sha256=" + java.util.HexFormat.of().formatHex(digest.digest(raw)) + " gzip_bytes=" + compressed.length
                + " gzip_sha256=" + java.util.HexFormat.of().formatHex(digest.digest(compressed)));
    }

    private static void gzipExisting(String[] args) throws Exception {
        if (args.length != 8) throw new IllegalArgumentException("--gzip-existing repository Python exactRaw oldActual qualifiedScratch freshOutput machineId required");
        Path root = Path.of(args[1]).toRealPath(); Path raw = Path.of(args[3]).toRealPath(); Path actual = Path.of(args[4]).toRealPath();
        Path scratch = Path.of(args[5]).toRealPath(); Path output = Path.of(args[6]).toAbsolutePath().normalize();
        if (!output.startsWith(scratch) || output.equals(scratch) || Files.exists(output)
                || Files.size(raw) > RAW_MAX || Files.size(actual) > 131_072) throw new IOException("fresh allocated output and bounded retained inputs required");
        Path stdout = Files.createTempFile(scratch, "gzip-existing-", ".raw");
        Path stderr = Files.createTempFile(scratch, "gzip-existing-", ".stderr");
        String beforeActual = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(actual)));
        ProcessBuilder builder = new ProcessBuilder(args[2], "-B", "-X", "utf8", "-c", EXISTING_PROGRAM,
                root.toString(), raw.toString(), actual.toString(), args[7]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectOutput(stdout.toFile()).redirectError(ProcessBuilder.Redirect.PIPE);
        Process child = builder.start(); Diagnostics diagnostics = beginDiagnostics(child, stderr);
        if (!child.waitFor(45, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IOException("existing raw qualification timed out");
        }
        if (Files.size(stderr) > 8192) throw new IOException("qualification diagnostics exceed 8KiB");
        finishDiagnostics(diagnostics);
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("retained actual/raw qualification exit " + child.exitValue());
        byte[] bytes = Files.readAllBytes(stdout);
        if (!java.util.Arrays.equals(bytes, Files.readAllBytes(raw))) throw new IOException("qualified raw changed during transfer");
        writeGolden(bytes, output, args[7]);
        String afterActual = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(actual)));
        if (!beforeActual.equals(afterActual)) throw new IOException("old actual proof drifted");
        System.out.println("qualification=EXISTING_ORIGINAL_PASS_RAW original_actual_sha256=" + beforeActual);
    }
    private static final String EXISTING_PROGRAM = """
EXPECTED_SCHEMA='xar.java.zerostockclock.original-producer-golden.v1'
import hashlib,json,pathlib,sys
def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate receipt/raw field '+key)
        result[key]=value
    return result
def invalid(value):raise ValueError('nonfinite JSON token '+value)
def load(raw):return json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=unique,parse_constant=invalid)
root=pathlib.Path(sys.argv[1]).resolve();raw_path=pathlib.Path(sys.argv[2]).resolve();actual_path=pathlib.Path(sys.argv[3]).resolve();machine=sys.argv[4]
raw=raw_path.read_bytes()
if not 0<len(raw)<=131072:raise ValueError('raw outside 128KiB profile')
actual=load(actual_path.read_bytes());result=actual['result']
if actual.get('schema')!='xar.shared-golden-capture-actual/v1' or actual.get('status')!='PASS' or actual.get('source_unchanged') is not True:raise ValueError('qualified original PASS actual required')
if type(result.get('exit_code')) is not int or result['exit_code']!=0 or type(result['accounting'].get('active_processes')) is not int or result['accounting']['active_processes']!=0 or result.get('stop_reason') is not None:raise ValueError('original child/Job terminal not qualified')
if actual.get('machine_id')!=machine:raise ValueError('actual source machine differs')
ref=actual['output_ref']
if type(ref.get('bytes')) is not int or ref['bytes']!=len(raw) or ref.get('sha256')!=hashlib.sha256(raw).hexdigest():raise ValueError('original raw byte/length/SHA differs')
if not pathlib.Path(ref['path']).resolve().samefile(raw_path) or not pathlib.Path(actual['request']['output_path']).resolve().samefile(raw_path):raise ValueError('raw is not exact qualified original output')
payload=load(raw)
if payload.get('schema')!=EXPECTED_SCHEMA or payload.get('machine_id')!=machine:raise ValueError('original producer schema or machine differs')
pins=payload.get('source_sha256')
if type(pins) is not dict or not pins:raise ValueError('retained original source hashes required')
for relative,sha in pins.items():
    source=(root/relative).resolve()
    if not source.is_relative_to(root) or hashlib.sha256(source.read_bytes()).hexdigest()!=sha:raise ValueError('current qualified source differs '+relative)
    matches=[item for item in actual['request']['source_refs'] if item['path'].replace(chr(92),'/').lower().endswith('/'+relative.lower())]
    if len(matches)!=1 or matches[0]['sha256']!=sha:raise ValueError('raw source is not bound to actual proof '+relative)
sys.stdout.buffer.write(raw)
""";

    private record Diagnostics(Thread reader, java.util.concurrent.atomic.AtomicBoolean overflow,
            java.util.concurrent.atomic.AtomicReference<IOException> failure) { }
    private static Diagnostics beginDiagnostics(Process child, Path file) {
        var overflow = new java.util.concurrent.atomic.AtomicBoolean();
        var failure = new java.util.concurrent.atomic.AtomicReference<IOException>();
        Thread reader = Thread.startVirtualThread(() -> {
            try (var input = child.getErrorStream(); var output = Files.newOutputStream(file)) {
                byte[] buffer = new byte[1024]; int total = 0, count;
                while ((count = input.read(buffer)) != -1) {
                    int retained = Math.min(count, 8192 - total); output.write(buffer, 0, retained); total += retained;
                    if (retained != count) { overflow.set(true); child.destroyForcibly(); }
                }
            } catch (IOException error) { failure.set(error); child.destroyForcibly(); }
        });
        return new Diagnostics(reader, overflow, failure);
    }
    private static void finishDiagnostics(Diagnostics value) throws IOException, InterruptedException {
        value.reader().join(5000);
        if (value.reader().isAlive()) throw new IOException("diagnostic reader did not terminate");
        if (value.failure().get() != null) throw new IOException("diagnostic transfer failed", value.failure().get());
        if (value.overflow().get()) throw new IOException("diagnostics exceeded 8KiB; bounded prefix retained");
    }
}
