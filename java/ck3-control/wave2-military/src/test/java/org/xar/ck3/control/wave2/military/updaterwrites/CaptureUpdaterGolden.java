package org.xar.ck3.control.wave2.military.updaterwrites;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Explicit data-only original producer capture. Never invoked by default JUnit. */
public final class CaptureUpdaterGolden {
    static final int MAX_RAW_BYTES = 131_072;
    static final int MAX_GZIP_BYTES = 16_384;
    private static final String SCRIPT = """
import copy, datetime, hashlib, json, pathlib, sys
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_zero_stock_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_projection.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_next_updater_write_projection import project_source_derived_next_updater_writes_v1 as project
from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_contract import normalize_source_derived_next_daily_supply_frame_inputs_v1 as normalize
D=53288448;FULL=1234567890123456789
def frame(extended=True):
    x=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,current_date_storage_raw64=FULL,current_date_raw_i32=D,current_native_day_index_raw_i32=1,source_derived_next_date_raw_i32=D+24,source_derived_next_native_day_index_raw_i32=2,subject_army_id_u32=11,subject_carmy_id_u32=12,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False)
    if extended:x.update(source_derived_next_date_storage_raw64=FULL+1,source_derived_next_calendar_day_u8=17,source_derived_next_calendar_month_u8=6,source_derived_full_cdate64_ready=True)
    return x
def base(extended=True):
    return dict(status='available',army_id=11,native_carmy_id=12,unrelated_sdk_extension={'retained_outer_data':True},source_derived_next_daily_supply_frame_inputs_v1=frame(extended),monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0,unrelated_loaded_budget_value=777),army_update_clock_v1=dict(current_date_raw=D,last_supply_update_date_raw=D-24,grace_anchor_date_raw=D-48,loaded_grace_days=0,last_supply_update_date_storage_raw64=FULL,grace_anchor_date_storage_raw64=8888),monthly_caller_effect_inputs_v1=dict(army_byte_22_raw=0,current_date_storage_raw64=FULL))
cases=[]
def add(name,row):
    untouched=copy.deepcopy(row); expected=project(row)
    if row!=untouched:raise RuntimeError('original updater producer mutated row')
    cases.append(dict(id=name,input=row,expected=expected))
add('extended_admitted',base());add('legacy_admitted_no_full_date',base(False))
for key,value in (('unit_native_170_raw',3),('native_unit_in_combat',True),('native_unit_gathering',True),('army_gathering_count_raw',1)):
    x=base();x['monthly_loss_budget_inputs_v1'][key]=value
    add('gate_rejected_'+key,x)
for key in ('unit_native_170_raw','native_unit_in_combat','native_unit_gathering','army_gathering_count_raw'):
    x=base();x['monthly_loss_budget_inputs_v1'][key]=None;add('gate_missing_'+key,x)
for key in ('grace_anchor_date_raw','loaded_grace_days'):
    x=base();x['army_update_clock_v1'][key]=None;add('grace_missing_'+key,x)
x=base();x['army_update_clock_v1']['loaded_grace_days']=3;add('grace_strict_equal_rejected',x)
x=base();x['army_update_clock_v1'].update(current_date_raw=100,grace_anchor_date_raw=123,loaded_grace_days=-1);x['source_derived_next_daily_supply_frame_inputs_v1']['source_derived_next_date_raw_i32']=100;add('negative_delta_trunc_zero',x)
x=base();x['army_update_clock_v1'].update(current_date_raw=2147483647,grace_anchor_date_raw=2147483647,loaded_grace_days=-1);x['source_derived_next_daily_supply_frame_inputs_v1']['source_derived_next_date_raw_i32']=-2147483648;add('int32_elapsed_wrap',x)
x=base();x['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3;x.pop('source_derived_next_daily_supply_frame_inputs_v1');add('no_frame_early_rejection',x)
x=base();x['source_derived_next_daily_supply_frame_inputs_v1']=None;add('null_frame_reached_grace_missing',x)
x=base();x['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3;x['army_update_clock_v1']['last_supply_update_date_storage_raw64']=None;add('rejected_missing_retained188',x)
x=base();x['army_update_clock_v1']['last_supply_update_date_storage_raw64']=None;add('admitted_missing_old188_next_full_available',x)
x=base();x['status']='unavailable';add('unavailable_row',x)
x=base();x['native_carmy_id']=None;add('untyped_native_row',x)
x=base(False);x['monthly_loss_budget_inputs_v1']['army_gathering_count_raw']=1;add('legacy_rejected_retained188_ready',x)
x=base();f=x['source_derived_next_daily_supply_frame_inputs_v1'];f.update(source_derived_full_cdate64_ready=False,source_derived_next_date_storage_raw64=None,source_derived_next_calendar_day_u8=None,source_derived_next_calendar_month_u8=None);add('extended_null_complete_date_not_filled',x)
x=base();x['monthly_caller_effect_inputs_v1']['current_date_storage_raw64']=FULL+2;add('comparison_mismatch_is_reported',x)
rejections=[]
def reject(name,raw):
    try: normalize(json.loads(raw),expected_army_id=11,expected_carmy_id=12)
    except ValueError as error: rejections.append(dict(id=name,raw_json=raw,original_error_type=type(error).__name__,original_error=str(error)))
    else:raise RuntimeError('original source normalizer accepted rejection vector '+name)
canonical=json.dumps(frame(),separators=(',',':'))
schema_token=chr(34)+'schema_version'+chr(34)+':1'
if schema_token not in canonical:raise RuntimeError('schema token mutation pattern absent')
for name,token in (('schema_bool','true'),('schema_float','1.0'),('schema_exponent_float','1e0')):
    changed=canonical.replace(schema_token,chr(34)+'schema_version'+chr(34)+':'+token,1)
    if changed==canonical:raise RuntimeError('schema token mutation was a no-op')
    reject(name,changed)
reject('storage_bool',canonical.replace(str(FULL),'true',1))
reject('storage_float',canonical.replace(str(FULL),'1.0',1))
x=frame();x['subject_army_id_u32']=4294967296;reject('uint32_overflow',json.dumps(x))
x=frame();x['subject_army_id_u32']=12;reject('same_row_subject_drift',json.dumps(x))
x=frame();x['actual_future_callback_observed']=True;reject('future_callback_claim',json.dumps(x))
x=frame();x['source_derived_next_calendar_day_u8']=256;reject('u8_overflow',json.dumps(x))
x=frame();x.pop('source_derived_next_calendar_day_u8');reject('partial_extended_fields',json.dumps(x))
refs=[]
for p in paths:
    data=(root/p).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if before[p]!=digest:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(data),sha256=digest))
print(json.dumps(dict(schema='xar.source-next-updater.original-producer-golden/v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; conditional native source frame/updater proposal only; no Game callback, writes, source qualification or saved progress',whole_service_test_executed=False,whole_service_not_executed_reason='external whole native wire corpus and registered SDK setup are not part of this pure producer capture',source_refs=refs,projections=cases,rejections=rejections),separators=(',',':')))
""";
    private CaptureUpdaterGolden() {}
    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 8) throw new IllegalArgumentException(
                "repo-root python-exe D-scratch owned-gzip-output machine-id [--existing-raw path sha256] required");
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path stagedOutput = scratch.resolve("capture-output/updaterwrites");
        if ((!output.startsWith(root.resolve("java/ck3-control/wave2-military/src/test/resources/updaterwrites"))
                && !output.startsWith(stagedOutput))
                || !scratch.toString().toLowerCase(java.util.Locale.ROOT).startsWith("d:")) throw new IllegalArgumentException("unowned capture path");
        if (!output.toString().endsWith(".json.gz")) throw new IllegalArgumentException("gzip output extension required");
        if (Files.exists(output)) throw new IOException("capture refuses to overwrite evidence");
        boolean existingRaw = args.length == 8;
        Path stdout;
        if (existingRaw) {
            if (!"--existing-raw".equals(args[5]) || !args[7].matches("[a-f0-9]{64}")) {
                throw new IllegalArgumentException("explicit existing raw and SHA required");
            }
            stdout = Path.of(args[6]).toRealPath();
            if (!stdout.startsWith(scratch)) throw new IllegalArgumentException("existing raw outside owned scratch");
        } else {
            stdout = Files.createTempFile(scratch, "updater-golden-", ".json");
            Path stderr = Files.createTempFile(scratch, "updater-capture-", ".log");
            ProcessBuilder builder = new ProcessBuilder(args[1], "-X", "utf8", "-B", "-c", SCRIPT, root.toString(), args[4]);
            builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
            builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
            Process child = builder.start();
            if (!child.waitFor(120, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IOException("original updater producer timeout");
            }
            System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
            if (child.exitValue() != 0) throw new IOException("original updater capture exit " + child.exitValue());
        }
        if (Files.size(stdout) < 1 || Files.size(stdout) > MAX_RAW_BYTES) throw new IOException("updater raw exceeds 128 KiB budget");
        byte[] bytes = Files.readAllBytes(stdout);
        String rawSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        if (existingRaw && !args[7].equals(rawSha)) throw new IOException("existing raw SHA mismatch");
        byte[] compressed = compressGolden(bytes);
        if (!java.util.Arrays.equals(bytes, decompressGolden(compressed))) throw new IOException("gzip roundtrip changed original bytes");
        Files.createDirectories(output.getParent()); Files.write(output, compressed, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + args[4] + " observed_at_utc=" + Instant.now()
                + " existing_raw_lossless_packaging=" + existingRaw + " original_producer_rerun=" + !existingRaw
                + " raw_bytes=" + bytes.length + " raw_sha256=" + rawSha + " gzip_bytes=" + compressed.length
                + " gzip_sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
    }

    static byte[] compressGolden(byte[] raw) throws IOException {
        validateRaw(raw);
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(buffer)) { gzip.write(raw); }
        byte[] compressed = buffer.toByteArray();
        if (compressed.length > MAX_GZIP_BYTES) throw new IOException("updater gzip exceeds 16 KiB budget");
        return compressed;
    }

    static byte[] decompressGolden(byte[] compressed) throws IOException {
        if (compressed.length == 0 || compressed.length > MAX_GZIP_BYTES) throw new IOException("updater gzip exceeds 16 KiB budget");
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] raw = gzip.readNBytes(MAX_RAW_BYTES + 1);
            validateRaw(raw);
            return raw;
        }
    }

    private static void validateRaw(byte[] raw) throws IOException {
        if (raw.length == 0 || raw.length > MAX_RAW_BYTES) throw new IOException("updater raw exceeds 128 KiB budget");
        StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw));
    }
}
