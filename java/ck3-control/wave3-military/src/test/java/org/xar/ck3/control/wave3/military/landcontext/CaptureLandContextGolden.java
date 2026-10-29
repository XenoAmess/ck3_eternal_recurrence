package org.xar.ck3.control.wave3.military.landcontext;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture, never part of normal Java JUnit execution. */
public final class CaptureLandContextGolden {
    private CaptureLandContextGolden() {}
    private static final String SCRIPT = """
import copy, datetime, hashlib, json, pathlib, runpy, sys
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_full_land_supply_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_land_supply_rate_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_land_resupply_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_province_supply_contributors_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_replenishment_records_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_character_role_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_fleet_supply_tick_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_post_refill_land_supply_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_post_refill_besieging_current_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_current_full_land_supply_rate.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_full_land_supply_rate_projection import project_full_land_supply_rate_v1 as fullrate
from xar_autoplayer.bridge.army_next_land_stock_supply_budget_projection import project_source_derived_next_land_stock_supply_budget_v1 as landstock
from xar_autoplayer.bridge.army_current_land_supply_rate_contract import normalize_current_land_supply_rate_inputs_v1 as rate_normalize
from xar_autoplayer.bridge.army_current_land_resupply_contract import normalize_current_land_resupply_v1 as resupply_normalize
from xar_autoplayer.bridge.army_current_province_supply_contributors_contract import normalize_current_province_supply_contributors_v1 as province_normalize
f=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_current_full_land_supply_rate.py'))
D=43800024
base=f['row'](f['inputs']())
base.update(current_supply_raw=100000000,current_supply_capacity_raw=200000000)
base['monthly_loss_budget_inputs_v1']=dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0,loaded_supply_state_levels=[2000,1000,0],loaded_supply_state_fractions_raw=[0,12500,25000],commander_valid=False,commander_supply_modifier_raw=None,native_fleet_supply_loss_suppressed=False)
base['loss_application_inputs_v1']=dict(supply_eligible_soldiers=100,current_supply_loss_budget=12)
base['army_update_clock_v1']=dict(current_date_raw=D,last_supply_update_date_raw=D-24,grace_anchor_date_raw=D-48,loaded_grace_days=0,last_supply_update_date_storage_raw64=D-24,grace_anchor_date_storage_raw64=D-48)
base['monthly_caller_effect_inputs_v1']=dict(army_byte_22_raw=1,current_date_storage_raw64=D)
base['source_derived_next_daily_supply_frame_inputs_v1']=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,current_date_storage_raw64=D,current_date_raw_i32=D,current_native_day_index_raw_i32=1,source_derived_next_date_raw_i32=D+24,source_derived_next_native_day_index_raw_i32=2,subject_army_id_u32=11,subject_carmy_id_u32=12,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False,source_derived_next_date_storage_raw64=1234567890123456789,source_derived_next_calendar_day_u8=2,source_derived_next_calendar_month_u8=3,source_derived_full_cdate64_ready=True)
base['current_fleet_supply_tick_inputs_v1']=dict(source='native_current_fleet_supply_tick_inputs',status='not_fleet',ready=True,unavailable_reason=None,scale=100000,subject_army_id=11,subject_carmy_id=12,province_id=1,current_native_date_low32=None,fleet_raw_full_id=None,fleet_resolved_full_id=None,fleet_day_raw=None,loaded_fleet_day_sentinel_raw=None,commander_raw_full_id=None,commander_resolved_full_id=None,terrain_modifier_772_raw=None,loaded_fleet_loss_raw=None,commander_modifier_1a9_raw=None,loaded_divisor_floor_raw=None,loaded_max_loss_raw=None,native_fleet_branch_applicable=False,fleet_used_native_fallback=None,commander_used_native_fallback=None,terrain_magic_38_raw=None,terrain_modifier_772_id=None)
def merge(target,patch):
    for k,v in patch.items():
        if isinstance(v,dict) and isinstance(target.get(k),dict):merge(target[k],v)
        else:target[k]=copy.deepcopy(v)
    return target
def sample(name,patch,usage=None):
    row=merge(copy.deepcopy(base),patch); untouched=copy.deepcopy(row)
    expected=landstock(row) if usage is None else fullrate(row,selected_refill_usage_soldiers=usage)
    if row!=untouched:raise RuntimeError('original full LAND producer mutated its input')
    item=dict(id=name,patch=patch,expected=expected)
    if usage is not None:item['selected_usage']=usage
    return item
rates=[sample('current_usage',{},80),sample('equal_limit',{},100),sample('over_limit',dict(current_land_supply_rate_inputs_v1=dict(province_component_raw=700000)),110),sample('zero_divisor',dict(current_land_supply_rate_inputs_v1=dict(loaded_divisor_floor_raw=0,commander_modifier_1a9_raw=-100000)),100),sample('unpublished_rate',dict(current_land_supply_rate_inputs_v1=None),100),sample('unavailable_row',dict(status='unavailable'),100),sample('missing_limit',dict(current_province_supply_contributors_v1=dict(native_supply_limit_soldiers=None)),100)]
stocks=[sample('admitted_full_join',{}),sample('rejected_keeps_zero_stock',dict(current_supply_raw=0,monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=3))),sample('capacity_clamp',dict(current_supply_raw=199000000)),sample('negative_wrapped_stock_no_capacity',dict(current_supply_raw=(1<<63)-1,current_supply_capacity_raw=None)),sample('missing_current_usage',dict(current_province_supply_contributors_v1=dict(current_usage_ready=False,native_supply_usage_soldiers=None))),sample('missing_gate',dict(monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=None))),sample('empty_state_levels',dict(monthly_loss_budget_inputs_v1=dict(loaded_supply_state_levels=[],loaded_supply_state_fractions_raw=None)))]
normalizers=[]
def normalized(name,kind,value):
    original=copy.deepcopy(value); fn={'rate':rate_normalize,'resupply':resupply_normalize,'province':province_normalize}[kind];expected=fn(value)
    if value!=original:raise RuntimeError('original normalizer mutated input')
    normalizers.append(dict(id=name,kind=kind,input=value,expected=expected))
normalized('available_rate','rate',base['current_land_supply_rate_inputs_v1'])
x=copy.deepcopy(base['current_land_supply_rate_inputs_v1']);x.update(status='not_land',current_observation_ready=False,native_land_branch_applicable=False,native_province_component_applicable=None,province_component_raw=None,commander_modifier_1a9_raw=None);normalized('not_land_rate','rate',x)
x=copy.deepcopy(base['current_land_resupply_v1']);x.update(status='unavailable',current_observation_ready=False,native_resupply_eligible=None,unavailable_reason=None);normalized('unavailable_resupply_null_reason','resupply',x)
role=dict(source='native_selected_ArRg_character_role_raw',status='available',army_regiment_id=0,native_carmy_id=12,arrg_army_id_140=12,character_raw_id_148=-1,resolved_character_id=None,extension_army_id_f4=None,extension_arrg_id_f8=None,character_magic_1c=None,resolution_used_fallback=True,native_character_predicate=False,character_extension_present=False,same_ArRg_instance_after=True,unavailable_reason=None)
record=dict(status='available',unavailable_reason=None,record_index=0,persistent_regiment_id=0,chunk_index=0,current_soldiers=90,maximum_soldiers=100,effective_current_soldiers=90,state_raw=0,native_can_replenish=False,native_chunk_can_replenish=True,persistent_monthly_replenishment_fraction_raw=99999,persistent_monthly_replenishment_fraction_scale=100000,persistent_prepared_replenishment_fraction_raw=20000,persistent_prepared_replenishment_fraction_scale=100000)
data=dict(army_regiment_id=0,source='native_all_data_records',status='available',ready=True,native_data_record_count=1,unavailable_reason=None,records=[record],native_loss_writer_skipped=False,loss_writer_admission_unavailable_reason=None,native_character_role_v1=role)
regiment=dict(stored_index=0,army_regiment_id=0,status='available',unavailable_reason=None,current_soldiers=90,maximum_soldiers=100,native_supply_loss_eligible=True,replenishment_records_v1=data)
occ=dict(stored_index=0,army_id=11,status='available',unavailable_reason=None,owner_character_id=33388,included=True,inclusion_basis='same_owner',native_carmy_id=12,native_eligible_current_soldiers=90,regiments=[regiment])
p=copy.deepcopy(base['current_province_supply_contributors_v1']);p.update(native_province_unit_count=2,native_supply_usage_soldiers=180,occurrences=[occ,dict(copy.deepcopy(occ),stored_index=1)]);normalized('duplicate_ordered_occurrences_full_DATA_role','province',p)
normalized('known_empty_roster','province',base['current_province_supply_contributors_v1'])
refs=[]
for p in paths:
    raw=(root/p).read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if before[p]!=sha:raise RuntimeError('source drifted during capture: '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=sha))
out=dict(schema='xar.landcontext.original-full-producer-golden/v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; deterministic complete original fullRate/outer LAND producer outputs; no Game or native execution',whole_original_test_executed=False,whole_original_test_reason='legacy fixture factory reused only; its obsolete zero-divisor assertion differs from current producer and is not counted as PASS; registered SDK whole-service corpus not executed',source_refs=refs,base_row=base,rates=rates,stocks=stocks,normalizers=normalizers)
print(json.dumps(out,separators=(',',':')))
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("root python new-scratch owned-output machine-id required");
        Path root = Path.of(args[0]).toRealPath();
        Path output = Path.of(args[3]);
        Path scratch = prepareScratch(System.getenv("XAR_CAPTURE_OUTPUT_ROOT"), Path.of(args[2]), output);
        Path stdout = Files.createTempFile(scratch, "landcontext-golden-", ".json"); Path stderr = Files.createTempFile(scratch, "landcontext-capture-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1"); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile()); Process child = builder.start();
        if (!child.waitFor(120, TimeUnit.SECONDS)) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IOException("full LAND capture timeout"); }
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8)); if (child.exitValue() != 0) throw new IOException("original full LAND producer exit " + child.exitValue());
        byte[] bytes = Files.readAllBytes(stdout); if (bytes.length == 0 || bytes.length > 72_000) throw new IOException("full LAND golden exceeds 72000 B");
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + args[4] + " observed_at_utc=" + Instant.now() + " bytes=" + bytes.length
                + " sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }

    static Path prepareScratch(String configuredRoot, Path scratch, Path output) throws IOException {
        if (configuredRoot == null || configuredRoot.isBlank()) throw new IOException("explicit XAR_CAPTURE_OUTPUT_ROOT required");
        Path owned = Path.of(configuredRoot);
        if (!owned.isAbsolute() || !owned.equals(owned.normalize()) || !owned.equals(owned.toRealPath())
                || !scratch.isAbsolute() || !scratch.equals(scratch.normalize())
                || !output.isAbsolute() || !output.equals(output.normalize())
                || !owned.equals(scratch.getParent()) || !owned.equals(output.getParent())
                || scratch.equals(output)) throw new IOException("capture paths outside explicit owned root");
        if (Files.exists(scratch, java.nio.file.LinkOption.NOFOLLOW_LINKS)
                || Files.exists(output, java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("capture refuses to overwrite evidence or reuse scratch");
        }
        return Files.createDirectory(scratch);
    }
}
