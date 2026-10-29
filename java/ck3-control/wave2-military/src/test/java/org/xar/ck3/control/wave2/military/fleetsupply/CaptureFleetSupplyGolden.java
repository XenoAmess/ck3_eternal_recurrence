package org.xar.ck3.control.wave2.military.fleetsupply;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Explicit original Python producer capture, run only by the shared bounded-Job scheduler. */
public final class CaptureFleetSupplyGolden {
    private CaptureFleetSupplyGolden() { }

    private static final String SCRIPT = """
import copy, datetime, hashlib, json, pathlib, sys
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_fleet_supply_tick_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/test_source_derived_next_fleet_supply_budget_whole_service_12004.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_next_fleet_supply_budget_projection import project_source_derived_next_fleet_supply_budget_v1 as project, _project_source_next_fleet_supply_budget_at_stock_v1 as explicit
tick=dict(source='native_current_fleet_supply_tick_inputs',status='available',ready=True,unavailable_reason=None,scale=100000,subject_army_id=11,subject_carmy_id=12,province_id=13,current_native_date_low32=53288448,fleet_raw_full_id=20,fleet_resolved_full_id=20,fleet_day_raw=53288472,loaded_fleet_day_sentinel_raw=-1,commander_raw_full_id=None,commander_resolved_full_id=None,terrain_modifier_772_raw=None,loaded_fleet_loss_raw=None,commander_modifier_1a9_raw=None,loaded_divisor_floor_raw=None,loaded_max_loss_raw=None,native_fleet_branch_applicable=True,fleet_used_native_fallback=False,commander_used_native_fallback=None,terrain_magic_38_raw=0,terrain_modifier_772_id=None)
future=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,current_date_storage_raw64=53288448,current_date_raw_i32=53288448,current_native_day_index_raw_i32=1,source_derived_next_date_raw_i32=53288472,source_derived_next_native_day_index_raw_i32=2,subject_army_id_u32=11,subject_carmy_id_u32=12,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False)
base=dict(status='available',army_id=11,native_carmy_id=12,current_supply_raw=123450000,current_fleet_supply_tick_inputs_v1=tick,source_derived_next_daily_supply_frame_inputs_v1=future,monthly_loss_budget_inputs_v1=dict(loaded_supply_state_levels=[2000,1000,0],loaded_supply_state_fractions_raw=[0,12500,25000],commander_valid=False,commander_supply_modifier_raw=None,native_fleet_supply_loss_suppressed=True),loss_application_inputs_v1=dict(supply_eligible_soldiers=100,current_supply_loss_budget=0),sdk_extension=dict(preserved='not a closed row schema'))
def merge(target,patch):
    for k,v in patch.items():
        if isinstance(v,dict) and isinstance(target.get(k),dict): merge(target[k],v)
        else: target[k]=copy.deepcopy(v)
    return target
def fleet(**kw): return dict(current_fleet_supply_tick_inputs_v1=kw)
def numeric(**kw): return dict(monthly_loss_budget_inputs_v1=kw)
cases=[]
def case(name,patch,stock_marker=False,stock=None):
    row=merge(copy.deepcopy(base),patch); untouched=copy.deepcopy(row)
    result=explicit(row,stock,stock_basis='conditional_post_updater_stock',post_updater_stock_used=True,stock_input_name='conditional_post_updater_stock_raw') if stock_marker else project(row)
    if row!=untouched: raise RuntimeError('original fleet getter mutated same-query row')
    item=dict(name=name,patch=patch,explicit_stock=stock_marker,expected=result)
    if stock_marker: item['stock']=stock
    cases.append(item)
case('equality-unsuppressed',{})
case('strict-greater-suppresses-without-stock',merge(fleet(fleet_day_raw=53288473),dict(current_supply_raw=None)))
case('strict-less-unsuppressed',fleet(fleet_day_raw=53288471))
case('sentinel-needs-no-global-date',merge(fleet(fleet_day_raw=-1),dict(source_derived_next_daily_supply_frame_inputs_v1=None)))
case('not-fleet-needs-no-global-date',merge(fleet(status='not_fleet',native_fleet_branch_applicable=False),dict(source_derived_next_daily_supply_frame_inputs_v1=None)))
case('missing-global-date',dict(source_derived_next_daily_supply_frame_inputs_v1=None))
case('missing-current-stock',dict(current_supply_raw=None))
case('unavailable-row',dict(status='unavailable'))
case('missing-tick',dict(current_fleet_supply_tick_inputs_v1=None))
case('unknown-branch',fleet(status='unavailable',ready=False,unavailable_reason='fixture unknown branch',native_fleet_branch_applicable=None))
case('missing-fleet-operands',fleet(status='unavailable',ready=False,unavailable_reason='fixture missing operands',fleet_day_raw=None,loaded_fleet_day_sentinel_raw=None))
case('missing-levels',numeric(loaded_supply_state_levels=None))
case('empty-levels-zero-without-fractions',numeric(loaded_supply_state_levels=[],loaded_supply_state_fractions_raw=None))
case('missing-fractions',numeric(loaded_supply_state_fractions_raw=None))
case('short-fractions-default-zero',numeric(loaded_supply_state_fractions_raw=[]))
case('commander-unknown',numeric(commander_valid=None))
case('commander-modifier-missing',numeric(commander_valid=True))
case('commander-clamp-zero',numeric(commander_valid=True,commander_supply_modifier_raw=-100000))
case('missing-eligible-count',dict(loss_application_inputs_v1=dict(supply_eligible_soldiers=None)))
case('empty-monthly-family',dict(monthly_loss_budget_inputs_v1=None))
case('extended23-preserved',dict(source_derived_next_daily_supply_frame_inputs_v1=dict(source_derived_full_cdate64_ready=True,source_derived_next_date_storage_raw64=53288472,source_derived_next_calendar_day_u8=2,source_derived_next_calendar_month_u8=3)))
case('explicit-poststock-does-not-change-held-stock',{},True,50000000)
case('explicit-poststock-missing',{},True,None)
case('signed64-stock-wrapped-state',{},True,-(1<<63))
case('unclamped-invalid-commander-wide-fraction',numeric(loaded_supply_state_fractions_raw=[0,(1<<63)-1,25000]),True,123450000)
case('signed32-date-comparison',merge(fleet(fleet_day_raw=-(1<<31)),dict(source_derived_next_daily_supply_frame_inputs_v1=dict(source_derived_next_date_raw_i32=(1<<31)-1))))
after={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
if before!=after: raise RuntimeError('source files drifted while capturing original producer')
out=dict(schema='xar.java.fleetsupply.original-producer-golden.v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_basis='deterministic same-query fixtures passed through unchanged original Python producers; not native execution evidence',source_sha256=before,base_row=base,cases=cases)
print(json.dumps(out,ensure_ascii=False,separators=(',',':')))
""";

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--gzip-existing")) { gzipExisting(args); return; }
        if (args.length != 5) throw new IllegalArgumentException("root python output scratch machine_id required");
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[3]).toRealPath();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (!output.startsWith(scratch) || output.equals(scratch)) {
            throw new IOException("capture paths outside allocated leaf roots");
        }
        if (Files.exists(output)) throw new IOException("capture refuses to overwrite original evidence");
        Path stdout = Files.createTempFile(scratch, "fleetsupply-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "fleetsupply-golden-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        builder.redirectOutput(stdout.toFile()).redirectError(ProcessBuilder.Redirect.PIPE); Process child = builder.start(); Diagnostics diagnostics = beginDiagnostics(child, stderr);
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IOException("fleet original producer capture timeout");
        }
        finishDiagnostics(diagnostics);
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original fleet producer exit " + child.exitValue());
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
EXPECTED_SCHEMA='xar.java.fleetsupply.original-producer-golden.v1'
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
