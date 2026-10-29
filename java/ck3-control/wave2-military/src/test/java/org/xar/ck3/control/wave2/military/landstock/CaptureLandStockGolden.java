package org.xar.ck3.control.wave2.military.landstock;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer sample capture; never used by default JUnit. */
public final class CaptureLandStockGolden {
    private static final String SCRIPT = """
import copy, datetime, hashlib, json, pathlib, random, runpy, sys
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_full_land_supply_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_land_supply_rate_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_land_resupply_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_province_supply_contributors_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/tests/unit/test_current_full_land_supply_rate.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_target_land_supply_projection_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_loss_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_admitted_day_fleet_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_post_refill_besieging_current_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_post_refill_land_supply_rate_projection.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_full_land_supply_rate_projection import _project_land_rate_operands_v1, _native_fixed_mul, _native_fixed_div
from xar_autoplayer.bridge.army_next_land_stock_supply_budget_projection import project_source_derived_next_land_stock_supply_budget_v1
factories=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_current_full_land_supply_rate.py'))
fields=('usage','limit','province_component_raw','native_resupply_eligible','loaded_gain_raw','loaded_excess_slope_raw','loaded_min_loss_raw','loaded_max_loss_raw','loaded_divisor_floor_raw','commander_modifier_1a9_raw','captured_stock_raw','captured_capacity_raw')
def base(**changes):
    x=dict(usage=100,limit=100,province_component_raw=-600000,native_resupply_eligible=True,loaded_gain_raw=2345678,loaded_excess_slope_raw=10000,loaded_min_loss_raw=200000,loaded_max_loss_raw=5000000,loaded_divisor_floor_raw=300000,commander_modifier_1a9_raw=100000,captured_stock_raw=100000000,captured_capacity_raw=200000000)
    x.update(changes); return x
def actual_outer(x):
    if any(x[k] is None for k in fields[:10]) or not -(1<<31)<=x['usage']<(1<<31) or not -(1<<31)<=x['limit']<(1<<31): return None
    rate=factories['inputs'](**{k:x[k] for k in fields[2:3]+fields[5:10]})
    row=factories['row'](rate,gain=x['loaded_gain_raw'])
    row['current_land_resupply_v1']['native_resupply_eligible']=x['native_resupply_eligible']
    row['current_province_supply_contributors_v1'].update(native_supply_usage_soldiers=x['usage'],native_supply_limit_soldiers=x['limit'])
    row.update(current_supply_raw=x['captured_stock_raw'],current_supply_capacity_raw=x['captured_capacity_raw'],monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0),army_update_clock_v1=dict(current_date_raw=43800024,grace_anchor_date_raw=43799976,loaded_grace_days=0,last_supply_update_date_storage_raw64=43799304))
    row['source_derived_next_daily_supply_frame_inputs_v1']=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,subject_army_id_u32=11,subject_carmy_id_u32=12,current_date_storage_raw64=43800024,current_date_raw_i32=43800024,current_native_day_index_raw_i32=1,source_derived_next_date_raw_i32=43800048,source_derived_next_native_day_index_raw_i32=2,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False)
    untouched=copy.deepcopy(row); result=project_source_derived_next_land_stock_supply_budget_v1(row)
    if row != untouched: raise RuntimeError('original outer producer mutated row')
    if result['next_admission']['admitted'] is not True: raise RuntimeError('fixture failed original ordered admission')
    return result['conditional_post_updater_stock']
samples=[base(),base(usage=80),base(usage=110,province_component_raw=700000),base(usage=200,province_component_raw=0,loaded_max_loss_raw=400000),base(usage=110,province_component_raw=0,loaded_min_loss_raw=600000,loaded_max_loss_raw=400000),base(loaded_divisor_floor_raw=0,commander_modifier_1a9_raw=-100000,loaded_gain_raw=0),base(province_component_raw=0,native_resupply_eligible=False,loaded_gain_raw=None,loaded_divisor_floor_raw=None,commander_modifier_1a9_raw=None,loaded_max_loss_raw=None),base(usage=101,limit=100,province_component_raw=0,native_resupply_eligible=None,loaded_gain_raw=None,loaded_excess_slope_raw=100000,loaded_min_loss_raw=100000,loaded_max_loss_raw=500000,loaded_divisor_floor_raw=100000,commander_modifier_1a9_raw=0),base(province_component_raw=0,loaded_gain_raw=2000000,captured_stock_raw=199000000),base(captured_stock_raw=(1<<63)-1),base(captured_stock_raw=None),base(captured_capacity_raw=None),base(captured_capacity_raw=-1),base(usage=(1<<63)-1,limit=-(1<<63),province_component_raw=0)]
for k in fields[:10]: samples.append(base(**{k:None}))
rng=random.Random(0x24e51a0)
for i in range(28):
    samples.append(base(usage=rng.randint(0,1000),limit=rng.randint(0,1000),province_component_raw=rng.randint(-10000000,10000000),loaded_gain_raw=rng.randint(-1000000,5000000),loaded_excess_slope_raw=rng.randint(-50000,200000),loaded_min_loss_raw=rng.randint(0,1000000),loaded_max_loss_raw=rng.randint(0,10000000),loaded_divisor_floor_raw=rng.choice((0,1,100000,10**10)),commander_modifier_1a9_raw=rng.randint(-200000,200000),native_resupply_eligible=bool(rng.getrandbits(1))))
rates=[]
for i,x in enumerate(samples):
    operands={k:x[k] for k in fields[5:10]}
    expected=_project_land_rate_operands_v1(usage=x['usage'],limit=x['limit'],p=x['province_component_raw'],resupply=x['native_resupply_eligible'],gain=x['loaded_gain_raw'],operands=operands)
    item={'id':'land_numeric_'+str(i),'input':dict(schema='xar.land-stock.numeric-input/v1',**x),'expected_rate':expected}
    post=actual_outer(x)
    if post is not None:item['expected_poststock']=post
    rates.append(item)
muls=[(3037000499,3037000499),(3037000500,3037000499),((1<<63)-1,100000),(-(1<<63),100000),(-1,1),(-(1<<63),-(1<<63))]
divs=[(-600000,-300000),(-10**18,10**10),(-92233720368548,3),(-10**18,-(1<<63)),(-1,0),(1,0),(0,0),(-(1<<63),-1),((1<<63)-1,1)]
for _ in range(52):
    muls.append((rng.randint(-(1<<63),(1<<63)-1),rng.randint(-(1<<63),(1<<63)-1)))
    divs.append((rng.randint(-(1<<63),(1<<63)-1),rng.choice((0,1,-1,100000,-100000,10**10,-(1<<63)))))
multiplications=[dict(id='native_mul_'+str(i),base=a,multiplier=b,expected=_native_fixed_mul(a,b)) for i,(a,b) in enumerate(muls)]
divisions=[]
for i,(a,b) in enumerate(divs):
    value,path=_native_fixed_div(a,b);divisions.append(dict(id='native_div_'+str(i),value=a,divisor=b,expected_value=value,expected_path=path))
refs=[]
for p in paths:
    data=(root/p).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest != before[p]: raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(data),sha256=digest))
out=dict(schema='xar.landstock.original-producer-golden/v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; pure native numeric kernel; poststock samples from original outer LAND producer; not actual future observation, callback or qualification',original_full_service_tests_executed=False,original_full_service_test_scope='not_executed; fixture source factory reused only, obsolete divisor-zero assertion differs from current producer; separate integration remains required',source_refs=refs,rates=rates,multiplications=multiplications,divisions=divisions)
print(json.dumps(out,separators=(',',':')))
""";

    private CaptureLandStockGolden() {}
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("repo-root python-exe D-scratch owned-output machine-id required");
        Path root = Path.of(args[0]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!output.startsWith(root.resolve("java/ck3-control/wave2-military/src/test/resources/landstock"))
                || !scratch.toString().toLowerCase(java.util.Locale.ROOT).startsWith("d:")) {
            throw new IllegalArgumentException("capture paths outside owned bounded roots");
        }
        if (Files.exists(output)) throw new IOException("capture will not overwrite existing evidence");
        Path stdout = Files.createTempFile(scratch, "landstock-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "landstock-capture-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1");
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process child = builder.start();
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IOException("original producer sample capture timeout");
        }
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original sample producer exit " + child.exitValue());
        byte[] bytes = Files.readAllBytes(stdout);
        if (bytes.length == 0 || bytes.length > 110_000) throw new IOException("golden exceeded leaf sample budget");
        Files.createDirectories(output.getParent());
        Files.write(output, bytes, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + args[4] + " observed_at_utc=" + Instant.now() + " bytes=" + bytes.length
                + " sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
}
