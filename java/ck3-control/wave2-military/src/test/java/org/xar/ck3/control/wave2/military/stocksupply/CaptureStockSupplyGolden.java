package org.xar.ck3.control.wave2.military.stocksupply;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Locale;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Central sampling-owner entry: invokes the unmodified original producers, never JUnit fallback. */
public final class CaptureStockSupplyGolden {
    static final int MAX_RAW_BYTES = 131_072;
    static final int MAX_GZIP_BYTES = 16_384;
    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);machine=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_admitted_day_fleet_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_fleet_supply_tick_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_full_land_supply_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_next_stock_supply_budget_projection import project_source_derived_next_stock_supply_budget_v1 as stock
from xar_autoplayer.bridge.army_next_admitted_day_fleet_rate_projection import project_next_admitted_day_fleet_rate_v1 as rate
def base():
    tick=dict(source='native_current_fleet_supply_tick_inputs',status='available',ready=True,unavailable_reason=None,scale=100000,subject_army_id=11,subject_carmy_id=12,province_id=1,current_native_date_low32=53288448,fleet_raw_full_id=23,fleet_resolved_full_id=23,fleet_day_raw=53288472,loaded_fleet_day_sentinel_raw=-1,commander_raw_full_id=-1,commander_resolved_full_id=-1,terrain_modifier_772_raw=0,loaded_fleet_loss_raw=100000,commander_modifier_1a9_raw=0,loaded_divisor_floor_raw=100000,loaded_max_loss_raw=500000,native_fleet_branch_applicable=True,fleet_used_native_fallback=False,commander_used_native_fallback=True,terrain_magic_38_raw=0x4744624f,terrain_modifier_772_id=0x1b0)
    frame=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,current_date_storage_raw64=304845178016701952,current_date_raw_i32=53288448,current_native_day_index_raw_i32=395352,source_derived_next_date_raw_i32=53288472,source_derived_next_native_day_index_raw_i32=395353,subject_army_id_u32=11,subject_carmy_id_u32=12,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False,source_derived_next_date_storage_raw64=304845178016701976,source_derived_next_calendar_day_u8=13,source_derived_next_calendar_month_u8=1,source_derived_full_cdate64_ready=True)
    inputs=dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0,native_fleet_supply_loss_suppressed=True,loaded_supply_state_levels=[2000,1000,0],loaded_supply_state_fractions_raw=[0,12500,25000],commander_valid=False,commander_supply_modifier_raw=None)
    return dict(status='available',army_id=11,native_carmy_id=12,current_supply_raw=100000000,current_supply_capacity_raw=200000000,current_supply_change_monthly_raw=0,current_fleet_supply_tick_inputs_v1=tick,source_derived_next_daily_supply_frame_inputs_v1=frame,monthly_loss_budget_inputs_v1=inputs,loss_application_inputs_v1=dict(supply_eligible_soldiers=100,current_supply_loss_budget=0),army_update_clock_v1=dict(current_date_raw=53288448,grace_anchor_date_raw=53288400,loaded_grace_days=2,last_supply_update_date_storage_raw64=21528124856,last_supply_update_date_raw=53287992,grace_anchor_date_storage_raw64=38707994064),monthly_caller_effect_inputs_v1=dict(army_byte_22_raw=0,current_date_storage_raw64=304845178016701952))
rows=[]
def add(name,change):
    row=base();change(row);rows.append((name,row))
add('ordered_fleet_poststock_boundary',lambda x:None)
add('rejected_updater_retains_stock',lambda x:x['monthly_loss_budget_inputs_v1'].update(unit_native_170_raw=3))
add('rejected_missing_stock',lambda x:(x.update(current_supply_raw=None),x['monthly_loss_budget_inputs_v1'].update(native_unit_in_combat=True)))
add('suppressed_getter_zero_with_missing_stock',lambda x:(x.update(current_supply_raw=None),x['current_fleet_supply_tick_inputs_v1'].update(fleet_day_raw=53288473)))
add('negative_wrapped_stock_before_capacity',lambda x:(x.update(current_supply_raw=(1<<63)-1,current_supply_capacity_raw=None),x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=-1)))
add('missing_capacity',lambda x:x.update(current_supply_capacity_raw=None))
add('source_next_legacy19',lambda x:[x['source_derived_next_daily_supply_frame_inputs_v1'].pop(k) for k in ('source_derived_next_date_storage_raw64','source_derived_next_calendar_day_u8','source_derived_next_calendar_month_u8','source_derived_full_cdate64_ready')])
add('unavailable_typed_row',lambda x:x.update(status='unavailable'))
add('land_rate_source_role_not_closed',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(status='not_fleet',native_fleet_branch_applicable=False))
add('unknown_updater_gate',lambda x:x['monthly_loss_budget_inputs_v1'].update(native_unit_in_combat=None))
vectors=[]
for name,row in rows:
    prior=copy.deepcopy(row);expected=stock(row)
    if row != prior:raise RuntimeError('original stock producer mutated row')
    vectors.append(dict(id=name,input=row,expected=expected))
rate_cases=[]
def add_rate(name,change):
    row=base();change(row);prior=copy.deepcopy(row);expected=rate(row)
    if row != prior:raise RuntimeError('original rate producer mutated row')
    rate_cases.append(dict(id=name,input=row,expected=expected))
add_rate('fleet_equality',lambda x:None)
add_rate('fleet_future_date',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(fleet_day_raw=53288473))
add_rate('non_gdbo_terrain',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(terrain_magic_38_raw=0))
add_rate('positive_terrain_modifier',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(terrain_modifier_772_raw=1))
add_rate('nonnegative_base',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=-123))
add_rate('zero_divisor',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(loaded_divisor_floor_raw=0,commander_modifier_1a9_raw=-100000))
add_rate('minimum_loss_wrap',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=-(1<<63)))
add_rate('wide_divisor',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=10**18,loaded_divisor_floor_raw=10**10))
add_rate('decomposed_divisor',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=10**18,loaded_divisor_floor_raw=3,commander_modifier_1a9_raw=-100000))
add_rate('int32_next_clock_wrap',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(current_native_date_low32=(1<<31)-8,fleet_day_raw=-(1<<31)+16))
add_rate('missing_family',lambda x:x.update(current_fleet_supply_tick_inputs_v1=None))
add_rate('not_fleet',lambda x:x['current_fleet_supply_tick_inputs_v1'].update(status='not_fleet',native_fleet_branch_applicable=False))
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from test_conditional_monthly_loss_budgets import monthly_budget_packet,MemoryStrengthService
service_input=monthly_budget_packet();source=base()
for name,value in source.items():
    if name in ('army_id','native_carmy_id','monthly_caller_effect_inputs_v1'):continue
    if name in ('monthly_loss_budget_inputs_v1','army_update_clock_v1','loss_application_inputs_v1'):service_input[name].update(value)
    else:service_input[name]=copy.deepcopy(value)
service_input['current_fleet_supply_tick_inputs_v1'].update(subject_army_id=0,subject_carmy_id=0)
service_input['source_derived_next_daily_supply_frame_inputs_v1'].update(subject_army_id_u32=0,subject_carmy_id_u32=0)
service_input['monthly_loss_budget_inputs_v1'].update(commander_supply_modifier_id=None,commander_supply_modifier_raw=None)
service_input['loss_application_inputs_v1'].update(supply_eligible_soldiers=12)
class StockMemoryService(MemoryStrengthService):
    def snapshot(self):
        frame=super().snapshot();frame['date_raw']=self.row['army_update_clock_v1']['current_date_raw'];return frame
service=StockMemoryService(service_input);untouched=copy.deepcopy(service_input)
service_result=service.query_army_strengths([0],expected_revision=2)
if service.calls!=1 or service_input!=untouched:raise RuntimeError('actual Service count/input preservation failed')
service_fields={k:service_result[k] for k in ('source_derived_next_stock_supply_budget_v1','same_input_conditional_next_admitted_day_fleet_rate_v1')}
if service_fields['source_derived_next_stock_supply_budget_v1'][0]['projection']!=stock(service_input):raise RuntimeError('actual Service stock producer differs')
if service_fields['same_input_conditional_next_admitted_day_fleet_rate_v1'][0]['projection']!=rate(service_input):raise RuntimeError('actual Service rate producer differs')
refs=[]
for p in paths:
    body=(root/p).read_bytes();digest=hashlib.sha256(body).hexdigest()
    if digest != before[p]:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(body),sha256=digest))
out=dict(schema='xar.stocksupply.original-producer-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; actual unmodified Python next-stock and next-admitted Fleet-rate producers; synthetic same-query operands, no future callback or gameplay qualification',original_full_service_executed=False,original_full_service_scope='NOTRUN; whole native fixture not consumed; actual Service calculation over memory transport fixture separately recorded',source_refs=refs,vectors=vectors,rate_vectors=rate_cases,service_consumer=dict(actual_service_method='GameplayBridgeService.query_army_strengths',fixture='StockMemoryService extends existing MemoryStrengthService; readonly snapshot date aligned to captured current row',execute_step_calls=service.calls,input=service_input,expected_fields=service_fields,registered_mcp_or_native_pipeline_executed=False))
print(json.dumps(out,separators=(',',':')))
""";
    private CaptureStockSupplyGolden() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 8) throw new IllegalArgumentException(
                "repo-root python-exe D-scratch owned-gzip-output machine-id [--existing-raw path sha256] required");
        Path root = Path.of(args[0]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path stagedOutput = scratch.resolve("capture-output/stocksupply");
        if ((!output.startsWith(root.resolve("java/ck3-control/wave2-military/src/test/resources/stocksupply"))
                && !output.startsWith(stagedOutput))
                || !scratch.toString().toLowerCase(Locale.ROOT).startsWith("d:")) throw new IllegalArgumentException("capture paths outside owned roots");
        if (!output.toString().endsWith(".json.gz")) throw new IllegalArgumentException("gzip output extension required");
        if (Files.exists(output)) throw new IOException("capture will not overwrite existing evidence");
        boolean existingRaw = args.length == 8;
        Path stdout;
        if (existingRaw) {
            if (!"--existing-raw".equals(args[5]) || !args[7].matches("[a-f0-9]{64}")) {
                throw new IllegalArgumentException("explicit existing raw and SHA required");
            }
            stdout = Path.of(args[6]).toRealPath();
            if (!stdout.startsWith(scratch)) throw new IllegalArgumentException("existing raw outside owned scratch");
        } else {
            stdout = Files.createTempFile(scratch, "stocksupply-golden-", ".json");
            Path stderr = Files.createTempFile(scratch, "stocksupply-capture-", ".log");
            ProcessBuilder builder = new ProcessBuilder(args[1], "-X", "utf8", "-B", "-c", SCRIPT, root.toString(), args[4]);
            builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
            Process child = builder.start();
            if (!child.waitFor(120, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IOException("original stock supply capture timeout");
            }
            System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
            if (child.exitValue() != 0) throw new IOException("original stock supply capture exit " + child.exitValue());
        }
        if (Files.size(stdout) < 1 || Files.size(stdout) > MAX_RAW_BYTES) throw new IOException("stock raw exceeds 128 KiB budget");
        byte[] bytes = Files.readAllBytes(stdout);
        String rawSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        if (existingRaw && !args[7].equals(rawSha)) throw new IOException("existing raw SHA mismatch");
        byte[] compressed = compressGolden(bytes);
        if (!java.util.Arrays.equals(bytes, decompressGolden(compressed))) throw new IOException("gzip roundtrip changed original bytes");
        Files.createDirectories(output.getParent());
        Files.write(output, compressed, StandardOpenOption.CREATE_NEW);
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
        if (compressed.length > MAX_GZIP_BYTES) throw new IOException("stock gzip exceeds 16 KiB budget");
        return compressed;
    }

    static byte[] decompressGolden(byte[] compressed) throws IOException {
        if (compressed.length == 0 || compressed.length > MAX_GZIP_BYTES) throw new IOException("stock gzip exceeds 16 KiB budget");
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] raw = gzip.readNBytes(MAX_RAW_BYTES + 1);
            validateRaw(raw);
            return raw;
        }
    }

    private static void validateRaw(byte[] raw) throws IOException {
        if (raw.length == 0 || raw.length > MAX_RAW_BYTES) throw new IOException("stock raw exceeds 128 KiB budget");
        StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw));
    }
}
