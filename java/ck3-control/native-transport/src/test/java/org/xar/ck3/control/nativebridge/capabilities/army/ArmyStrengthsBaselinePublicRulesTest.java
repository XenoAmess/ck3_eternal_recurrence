package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.replenishment.*;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ArmyUpdateClockCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.*;
import org.xar.ck3.control.wave2.military.fleetsupply.*;
import org.xar.ck3.control.wave2.military.callbackrisk.*;
import org.xar.ck3.control.wave2.military.supplyschedule.*;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.wave2.military.stocksupply.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.Stage;

/** Existing original normalizers/projectors -> actual Java native encoders -> declared publicV2.
 * Corpus operands are controlled source fixtures, not original native business observations. */
final class ArmyStrengthsBaselinePublicRulesTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static JsonNode captured;
    private record OriginalSource(String relative,String sha256) { }
    private static final List<OriginalSource> ORIGINALS=List.of(
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py","ae960cc6a928eb9d26f2f9c93f30463a978951c374021558d08860c8f9125b2a"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/replenishment_numeric.py","3178c058eb2c9df02643f8050a337869f4fd8b12658b3db85904fdb47b3ad2f9"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_admitted_day_fleet_rate_projection.py","9180943b71a618db5a7bb9c6373e95dbc4e751a149a0a63f76e68e869c47850d"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_projection.py","800446079f7bbee64d422cfffe2419701566a82a25cecb50bc4d073e8a07f951"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_updater_write_projection.py","eef86dad31957d37a1a8c4e7fb305c55b6674a61f0dcb238dfeedfd414bbe9d1"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py","4230195b5c582fdf42c1e9d91b9c7eaf67974ded83162df0552ce766fa35987b"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py","eeec9bc34f85735eef758f78d7e78b7d37770d52cc66fd95a03a69a82f06941f"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_supply_risk_projection.py","105e05a8fa0abf2b5e174cded7eb4e4452683ec63c5c66bda72374debb89427d"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_soldier_effects_projection.py","c0bd8a79cad4c33c96110b909a41952791afcaa71d71fcf701fc32b2e33b4988"),
        new OriginalSource("ck3_autonomous_player/tests/unit/test_current_callback_supply_risk_service_12004.py","2af3e750b16945589f202400d77aeddf0763164d5d6e38aa439c44f41e9f4083"),
        new OriginalSource("ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py","de90a82571ce2ffb1cb3410c924e26ffc6e280dc82fb110d8c14a63da15f0a13"),
        new OriginalSource("ck3_autonomous_player/tests/unit/test_conditional_daily_queue_transfer.py","398901e39e46c78df164878dc5d85b3d5a6f3390e1fe785112045a4d03afa731"),
        new OriginalSource("ck3_autonomous_player/tests/unit/test_army_zero_stock_clock_12004.py","f70f3316d07fca34302ee180fa41565b21d0b832186f882abc8f7c74f1bc0edf"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_roster_admission_contract.py","a9c8ad14f0b528e2f0da49104e6dfc29afd0407ca6155df1cb701fb21bd202b5"),
        new OriginalSource("ck3_autonomous_player/src/xar_autoplayer/simulation/army_daily_assault_roster_admission_12003.py","b0c5397de2b03f0e0826b01c48d71de2120cba814080ddc328dd2484cdbcf0f2"),
        new OriginalSource("ck3_autonomous_player/tests/unit/daily_assault_roster_admission_fixture.py","112a279acfdd73d60cb2ec4891293237a81e092f71dad3d506fb2571d12d1197")
    );
    private static void assertOriginals(Path root) throws Exception {
        for(OriginalSource source:ORIGINALS) {
            byte[] bytes=Files.readAllBytes(root.resolve(source.relative()));
            String actual=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            assertEquals(source.sha256(),actual,"Original numeric source changed: "+source.relative());
        }
    }
    private static final String SCRIPT="""
import copy,json,sys
from pathlib import Path
repo=Path(sys.argv[1])
sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
from test_current_callback_supply_risk_service_12004 import current_packet
from test_conditional_daily_queue_transfer import daily_queue_packet
from test_army_zero_stock_clock_12004 import clock_row
from xar_autoplayer.bridge.war_contract import normalize_army_strengths
from xar_autoplayer.replenishment_numeric import project_observed_replenishment_v1 as replenishment
from xar_autoplayer.bridge.army_next_admitted_day_fleet_rate_projection import project_next_admitted_day_fleet_rate_v1 as fleet_rate
from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_projection import project_native_next_daily_supply_schedule_v1 as schedule
from xar_autoplayer.bridge.army_next_updater_write_projection import project_source_derived_next_updater_writes_v1 as updater
from xar_autoplayer.bridge.army_next_fleet_supply_budget_projection import project_source_derived_next_fleet_supply_budget_v1 as fleet_budget
from xar_autoplayer.bridge.army_next_stock_supply_budget_projection import project_source_derived_next_stock_supply_budget_v1 as stock
from xar_autoplayer.bridge.army_current_callback_supply_risk_projection import project_current_callback_supply_risk_v1 as risk
from xar_autoplayer.bridge.army_current_callback_soldier_effects_projection import project_current_callback_soldier_effects_v1 as effects
from daily_assault_roster_admission_fixture import roster_admission_source
from xar_autoplayer.bridge.army_daily_assault_roster_admission_contract import normalize_current_daily_assault_roster_admission_v1 as roster_normalize
from xar_autoplayer.simulation.army_daily_assault_roster_admission_12003 import project_current_daily_assault_roster_admission_12003 as roster_project
MAX=(1<<63)-1;MIN=-(1<<63);FULL=1234567890123456789;D=264
def base():
    x=current_packet()
    x['native_army_resolution_v1']=dict(status='available',ready=True,branch='reference_absent',raw_reference=-1,reference_index=None,storage_capacity=None,entry_full_id=None)
    x['monthly_daily_queue_inputs_v1']=daily_queue_packet([],[])['monthly_daily_queue_inputs_v1']
    x['current_army_combat_roles_phase_inputs_v1']=None
    x['current_movement_progress']=dict(status='available',source='native_current_route_edge',unit_state_raw=6,
        accumulated_movement_weight_raw=100,cached_edge_speed_raw=7,normalized_edge_progress=dict(raw=94339,scale=100000),
        first_route_edge_remaining_duration=dict(raw=85714,scale=100000),unavailable_reason=None,
        first_route_target_province_type_tag_u32=0xFFFFFFFF,current_province_type_tag_u32=0x80000000,
        current_edge_movement_rate_raw=MIN,first_route_edge_weight_cost_raw=MAX,
        loaded_movement_lock_cutoff=dict(raw=MIN,scale=100000),
        committed_route_timeline=dict(status='available',source='native_committed_route',native_duration_scale=100000,
            unavailable_reason=None,native_full_route_remaining_days_q100000=MAX,committed_route_province_ids=[1,2],
            native_route_prefix_remaining_days_q100000=[MIN,MAX],projected_route_arrival_date_raws=[-2147483648,2147483647]))
    x['county_entry_inputs_v1']=dict(status='available',source='native_current_county_entry_inputs',unavailable_reason=None,
        fraction_scale=100000,soldier_scale=1,whole_soldiers=101,current_loss_budget=10,effective_fraction_raw=10000,
        minimum_multiplier_raw=100000,loaded_minimum_soldiers=0,
        condition=dict(status='available',source='current_stored_route_first_province',unavailable_reason=None,
            actor_character_id=29829,source_province_id=1,target_province_id=2,mode=0,passes=True),
        multiplier_floor_inputs_v1=dict(status='available',source='native_current_county_multiplier_floor_inputs',
            unavailable_reason=None,fraction_scale=100000,base_floor_raw=MAX,army_1d4_nonzero_floor_raw=MIN,army_1d4_raw=255))
    frame=copy.deepcopy(clock_row()['source_derived_next_daily_supply_frame_inputs_v1'])
    frame.update(subject_army_id_u32=0,subject_carmy_id_u32=0,current_date_storage_raw64=FULL,
        current_date_raw_i32=D,current_native_day_index_raw_i32=11,source_derived_next_date_raw_i32=D+24,
        source_derived_next_native_day_index_raw_i32=12,source_derived_next_date_storage_raw64=FULL+24,
        source_derived_next_calendar_day_u8=13,source_derived_next_calendar_month_u8=1,source_derived_full_cdate64_ready=True)
    x['source_derived_next_daily_supply_frame_inputs_v1']=frame
    f=copy.deepcopy(clock_row()['future_daily_supply_schedule_inputs_v1'])
    f.update(subject_army_id_u32=0,subject_carmy_id_u32=0,current_date_storage_raw64=FULL,current_date_raw_i32=D,
        native_day_index_raw_i32=11,selected_phase_index_i32=11)
    x['future_daily_supply_schedule_inputs_v1']=f
    x['current_fleet_supply_tick_inputs_v1']=dict(source='native_current_fleet_supply_tick_inputs',status='available',
        ready=True,unavailable_reason=None,scale=100000,subject_army_id=0,subject_carmy_id=0,province_id=1,
        current_native_date_low32=D,fleet_raw_full_id=23,fleet_resolved_full_id=23,fleet_day_raw=D+24,
        loaded_fleet_day_sentinel_raw=-1,commander_raw_full_id=-1,commander_resolved_full_id=-1,
        terrain_modifier_772_raw=0,loaded_fleet_loss_raw=100000,commander_modifier_1a9_raw=0,
        loaded_divisor_floor_raw=100000,loaded_max_loss_raw=500000,native_fleet_branch_applicable=True,
        fleet_used_native_fallback=False,commander_used_native_fallback=True,terrain_magic_38_raw=0x4744624F,
        terrain_modifier_772_id=0xFFFF)
    x['army_update_clock_v1'].update(last_supply_update_date_storage_raw64=FULL,grace_anchor_date_storage_raw64=MIN)
    x['loss_application_inputs_v1'].update(siege_rate_raw=MIN,raid_rate_raw=MAX)
    return x
families=('regiment_strengths','native_army_resolution_v1','loss_application_inputs_v1','current_movement_progress',
    'army_update_clock_v1','monthly_loss_budget_inputs_v1','monthly_daily_queue_inputs_v1','county_entry_inputs_v1',
    'source_derived_next_daily_supply_frame_inputs_v1','current_fleet_supply_tick_inputs_v1',
    'current_daily_supply_dispatch_inputs_v1','future_daily_supply_schedule_inputs_v1','current_army_combat_roles_phase_inputs_v1')
stages=('same_input_replenishment_v1','same_input_conditional_next_admitted_day_fleet_rate_v1',
    'same_input_conditional_future_daily_supply_schedule_v1','source_derived_next_updater_writes_v1',
    'source_derived_next_fleet_supply_budget_v1','source_derived_next_stock_supply_budget_v1',
    'current_callback_supply_risk_v1','current_callback_soldier_effects_v1')
def repl_input(row):
    out=dict(army_id=row['army_id'])
    if 'regiment_replenishment_records_v1' in row:
        out['regiment_replenishment_records_v1']=[]
        for snap in row['regiment_replenishment_records_v1'] or []:
            s={k:snap[k] for k in ('army_regiment_id','status','native_data_record_count','unavailable_reason')}
            keys=('status','unavailable_reason','record_index','persistent_regiment_id','chunk_index','maximum_soldiers',
                'effective_current_soldiers','persistent_prepared_replenishment_fraction_raw',
                'persistent_prepared_replenishment_fraction_scale','native_chunk_can_replenish')
            s['records']=[{k:r[k] for k in keys} for r in snap['records']]
            out['regiment_replenishment_records_v1'].append(s)
    return dict(schema='xar.replenishment.observed-input/v1',army_rows=[out])
cases=[]
def emit(name,row):
    untouched=copy.deepcopy(row)
    normal=normalize_army_strengths([row])[0]
    normal['monthly_caller_effect_inputs_v1']=dict(army_byte_22_raw=255,current_date_storage_raw64=FULL)
    r=risk(normal)
    outputs=(replenishment([normal]),fleet_rate(normal),schedule(normal),updater(normal),fleet_budget(normal),stock(normal),r,effects(normal,r))
    stage_values={key: value if i==0 else [dict(army_id=normal['army_id'],projection=value)] for i,(key,value) in enumerate(zip(stages,outputs))}
    if row!=untouched:raise RuntimeError('original producer mutated source')
    cases.append(dict(name=name,row=normal,replenishment_input=repl_input(normal),
        families={k:normal.get(k) for k in families},stages=stage_values))
emit('complete_baseline_extreme_fixed_and_date_roles',base())
x=base();x['monthly_loss_budget_inputs_v1'].update(commander_supply_modifier_raw=MAX,loaded_supply_state_fractions_raw=[MIN,0,MAX]);emit('wide_loaded_supply_fractions',x)
x=base();x['current_fleet_supply_tick_inputs_v1'].update(loaded_fleet_loss_raw=10**18,loaded_divisor_floor_raw=10**10);emit('wide_fleet_division',x)
x=base();x['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3;emit('rejected_updater_retains_dates_and_stock',x)
x=base();x['army_update_clock_v1'].update(last_supply_update_date_storage_raw64=MIN,grace_anchor_date_storage_raw64=MAX);emit('opposite_signed_date_extremes',x)
x=base();x['current_fleet_supply_tick_inputs_v1'].update(loaded_divisor_floor_raw=0,commander_modifier_1a9_raw=-100000);emit('native_fleet_zero_divisor',x)
x=base();x['regiment_replenishment_records_v1'][0]['records'][0].update(maximum_soldiers=102,native_chunk_can_replenish=True,persistent_prepared_replenishment_fraction_raw=MAX);emit('low64_replenishment_product',x)
cases[0]['roster_normalized']=roster_normalize(roster_admission_source())
cases[0]['roster_projection']=roster_project(cases[0]['roster_normalized'])
print(json.dumps(cases,separators=(',',':')))
""";
    private static synchronized JsonNode corpus() throws Exception {
        if(captured!=null)return captured;
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"Required actual -Dxar.python; no differential skip");
        assertNotNull(repository,"Required -Dxar.repository.root");
        Path root=Path.of(repository).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py")));
        assertOriginals(root);
        Path temporary=Files.createTempDirectory("baseline-public-original-"),out=temporary.resolve("out.json"),err=temporary.resolve("err.txt");
        Process child=null;
        try {
            child=new ProcessBuilder(python,"-B","-X","utf8","-c",SCRIPT,root.toString()).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
            assertTrue(child.waitFor(60,TimeUnit.SECONDS),"original normalizer/projector timeout");
            assertEquals(0,child.exitValue(),()->diagnostic(err));
            assertTrue(Files.size(out)>0 && Files.size(out)<8*1024*1024,"bounded complete original corpus required");
            captured=JSON.readTree(Files.readAllBytes(out));assertEquals(7,captured.size());assertOriginals(root);return captured;
        } finally {
            if(child!=null && child.isAlive()){child.descendants().forEach(ProcessHandle::destroyForcibly);child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS);}
            Files.deleteIfExists(out);Files.deleteIfExists(err);Files.deleteIfExists(temporary);
        }
    }
    private static String diagnostic(Path p){try{byte[] raw=Files.readAllBytes(p);return new String(raw,0,Math.min(raw.length,8192),java.nio.charset.StandardCharsets.UTF_8);}catch(Exception e){return e.toString();}}
    private static RawJson raw(JsonNode value){try{return new RawJson(JSON.writeValueAsBytes(value));}catch(Exception e){throw new IllegalArgumentException(e);}}
    private static JsonNode tree(RawJson value){return ArmyStrengthsCodec.parseValue(value);}
    private static JsonNode domain(JsonNode n){
        if(n.isIntegralNumber())return BigIntegerNode.valueOf(n.bigIntegerValue());
        if(n.isArray()){ArrayNode a=JSON.createArrayNode();for(JsonNode v:n)a.add(domain(v));return a;}
        if(n.isObject()){ObjectNode o=JSON.createObjectNode();n.properties().iterator().forEachRemaining(e->o.set(e.getKey(),domain(e.getValue())));return o;}
        return n;
    }
    private static JsonNode nativeFamily(Key key,JsonNode input,JsonNode row){
        return switch(key){
            case REGIMENT_STRENGTHS -> {ArrayNode a=JSON.createArrayNode();for(JsonNode r:input)a.add(ArmyStrengthsCodec.regimentJson(ArmyStrengthsCodec.regiment(r)));yield a;}
            case NATIVE_ARMY_RESOLUTION_V1 -> ArmyStrengthsNativeFields.resolutionJson(ArmyStrengthsNativeFields.resolution((ObjectNode)input));
            case LOSS_APPLICATION_INPUTS_V1 -> ArmyStrengthsNativeFields.lossJson(ArmyStrengthsNativeFields.lossInputs((ObjectNode)input));
            case CURRENT_MOVEMENT_PROGRESS -> {try{yield JSON.readTree(CurrentMovementCodec.encode(CurrentMovementCodec.normalize(input)));}catch(Exception e){throw new IllegalArgumentException(e);}}
            case ARMY_UPDATE_CLOCK_V1 -> ArmyUpdateClockCodec.encode(ArmyUpdateClockCodec.decode(input));
            case MONTHLY_LOSS_BUDGET_INPUTS_V1 -> MonthlyLossCodec.encodeFamilyNullable(MonthlyLossCodec.decodeFamilyNullable(input));
            case MONTHLY_DAILY_QUEUE_INPUTS_V1 -> ArmyDailyQueueInputsCodec.encodeNullable(ArmyDailyQueueInputsCodec.decodeNullable(input));
            case COUNTY_ENTRY_INPUTS_V1 -> CountyEntryCodec.inputsNode(CountyEntryCodec.decode(input,row.get("current_soldiers").intValue()));
            case SOURCE_DERIVED_NEXT_DAILY_SUPPLY_FRAME_INPUTS_V1 -> SourceNextFrameCodec.encode(SourceNextFrameCodec.decode(input,row.get("army_id").intValue(),row.get("native_carmy_id").intValue()));
            case CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1 -> input.isNull()?NullNode.instance:FleetSupplyCodec.encodeTick(FleetSupplyCodec.decodeTick(input));
            case CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1 -> CurrentSupplyDispatchCodec.encode(CurrentSupplyDispatchCodec.decode(input,row.get("army_id").intValue(),row.get("native_carmy_id").intValue()));
            case FUTURE_DAILY_SUPPLY_SCHEDULE_INPUTS_V1 -> FutureDailySupplyScheduleCodec.encode(FutureDailySupplyScheduleCodec.decode(input,row.get("army_id").intValue(),row.get("native_carmy_id").intValue()));
            case CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1 -> CombatRolesCodec.encode(CombatRolesCodec.decode(input));
            default -> throw new IllegalArgumentException("nonbaseline test family");
        };
    }
    private static JsonNode nativeStage(Stage stage,JsonNode row,JsonNode replenishmentInput){
        JsonNode projection=switch(stage){
            case SAME_INPUT_REPLENISHMENT_V1 -> {try{yield JSON.readTree(ReplenishmentCodec.encodeProjection(ReplenishmentPolicy.projectObservedReplenishmentV1(ReplenishmentCodec.decodeObservedInput(JSON.writeValueAsBytes(replenishmentInput)))));}catch(Exception e){throw new IllegalArgumentException(e);}}
            case SAME_INPUT_CONDITIONAL_NEXT_ADMITTED_DAY_FLEET_RATE_V1 -> StockSupplyCodec.encodeRate(NextFleetRate.project(StockSupplyCodec.decodeRateRow(row)));
            case SAME_INPUT_CONDITIONAL_FUTURE_DAILY_SUPPLY_SCHEDULE_V1 -> NativeNextDailySupplyScheduleCodec.encode(NativeNextDailySupplyScheduleCodec.fromSameQueryRow(row));
            case SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1 -> UpdaterWriteCodec.encode(UpdaterWriteProjection.project(UpdaterWriteCodec.decode(row)));
            case SOURCE_DERIVED_NEXT_FLEET_SUPPLY_BUDGET_V1 -> FleetSupplyCodec.encodeBudget(FleetSupplyProjection.project(FleetSupplyCodec.decodeRow(row)));
            case SOURCE_DERIVED_NEXT_STOCK_SUPPLY_BUDGET_V1 -> StockSupplyCodec.encode(StockSupplyProjection.project(StockSupplyCodec.decodeRow(row)));
            case CURRENT_CALLBACK_SUPPLY_RISK_V1 -> CallbackSupplyRiskCodec.encode(CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(row)));
            case CURRENT_CALLBACK_SOLDIER_EFFECTS_V1 -> {var risk=CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(row));yield CallbackSoldierEffectsCodec.encode(CallbackSoldierEffects.project(CallbackSoldierEffectsCodec.decodeRow(row,risk)));}
            default -> throw new IllegalArgumentException("nonbaseline test stage");
        };
        if(stage==Stage.SAME_INPUT_REPLENISHMENT_V1)return projection;
        ArrayNode result=JSON.createArrayNode();result.addObject().set("army_id",row.get("army_id"));((ObjectNode)result.get(0)).set("projection",projection);return result;
    }
    private static JsonNode publicExpected(JsonNode nativeValue,List<ArmyStrengthsPublicNumbers.Rule> rules){
        JsonNode expected=nativeValue.deepCopy();
        for(var rule:rules)at(expected,rule.exactPath().substring(1).split("/"),0);
        return expected;
    }
    private static void at(JsonNode n,String[] path,int i){
        if(n==null || n.isNull())return;String part=path[i];
        if(part.equals("*")){assertTrue(n.isArray());for(int j=0;j<n.size();j++){if(i+1==path.length){if(!n.get(j).isNull())((ArrayNode)n).set(j,TextNode.valueOf(n.get(j).bigIntegerValue().toString()));}else at(n.get(j),path,i+1);}return;}
        if(n.isArray()){int index=Integer.parseInt(part);if(index>=n.size())return;if(i+1==path.length){if(!n.get(index).isNull())((ArrayNode)n).set(index,TextNode.valueOf(n.get(index).bigIntegerValue().toString()));}else at(n.get(index),path,i+1);return;}
        JsonNode child=n.get(part);if(child==null || child.isNull())return;
        if(i+1==path.length)((ObjectNode)n).put(part,child.bigIntegerValue().toString());else at(child,path,i+1);
    }

    private static void wide(JsonNode value,String pointer){
        JsonNode field=value.at(pointer);if(field.isMissingNode() || field.isNull())return;
        assertTrue(field.isTextual(),"Declared wide role must be decimal text even when small: "+pointer);
        assertTrue(field.textValue().matches("-?(0|[1-9][0-9]*)"),"canonical decimal role: "+pointer);
    }
    private static void narrow(JsonNode value,String pointer){
        JsonNode field=value.at(pointer);if(field.isMissingNode() || field.isNull())return;
        assertTrue(field.isIntegralNumber(),"Native byte/DWORD/count role stays integer: "+pointer);
    }
    private static void familyRoles(Key key,JsonNode encoded){
        switch(key){
            case REGIMENT_STRENGTHS,NATIVE_ARMY_RESOLUTION_V1,MONTHLY_DAILY_QUEUE_INPUTS_V1,
                 CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1,CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1 -> { }
            case LOSS_APPLICATION_INPUTS_V1 -> {wide(encoded,"/siege_rate_raw");narrow(encoded,"/whole_soldiers");}
            case CURRENT_MOVEMENT_PROGRESS -> {wide(encoded,"/cached_edge_speed_raw");narrow(encoded,"/unit_state_raw");narrow(encoded,"/current_province_type_tag_u32");}
            case ARMY_UPDATE_CLOCK_V1 -> {wide(encoded,"/last_supply_update_date_storage_raw64");narrow(encoded,"/current_date_raw");narrow(encoded,"/loaded_grace_days");}
            case MONTHLY_LOSS_BUDGET_INPUTS_V1 -> {wide(encoded,"/loaded_supply_state_fractions_raw/0");wide(encoded,"/commander_supply_modifier_raw");narrow(encoded,"/loaded_supply_state_levels/0");narrow(encoded,"/commander_supply_modifier_id");}
            case COUNTY_ENTRY_INPUTS_V1 -> {wide(encoded,"/minimum_multiplier_raw");narrow(encoded,"/loaded_minimum_soldiers");narrow(encoded,"/multiplier_floor_inputs_v1/army_1d4_raw");}
            case SOURCE_DERIVED_NEXT_DAILY_SUPPLY_FRAME_INPUTS_V1 -> {wide(encoded,"/current_date_storage_raw64");narrow(encoded,"/subject_army_id_u32");narrow(encoded,"/source_derived_next_calendar_day_u8");}
            case CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1 -> {wide(encoded,"/terrain_modifier_772_raw");narrow(encoded,"/terrain_magic_38_raw");narrow(encoded,"/terrain_modifier_772_id");}
            case FUTURE_DAILY_SUPPLY_SCHEDULE_INPUTS_V1 -> {wide(encoded,"/current_date_storage_raw64");narrow(encoded,"/selected_phase_index_i32");narrow(encoded,"/phases/0/count_raw_i32");}
            default -> throw new IllegalArgumentException("nonbaseline role test");
        }
    }
    private static void stageRoles(Stage stage,JsonNode encoded){
        if(stage==Stage.SAME_INPUT_REPLENISHMENT_V1){
            wide(encoded,"/persistent_outputs/0/effective_deficit_by_chunk/0");
            wide(encoded,"/persistent_outputs/0/observations_by_chunk/0/0/calculation/effective_deficit");
            narrow(encoded,"/persistent_outputs/0/same_input_q_by_chunk/0");return;
        }
        narrow(encoded,"/0/army_id");JsonNode p=encoded.get(0).get("projection");
        switch(stage){
            case SAME_INPUT_CONDITIONAL_NEXT_ADMITTED_DAY_FLEET_RATE_V1 -> {wide(p,"/conditional_full_fleet_rate_raw");narrow(p,"/current_native_date_low32");}
            case SAME_INPUT_CONDITIONAL_FUTURE_DAILY_SUPPLY_SCHEDULE_V1 -> {wide(p,"/current_date_storage_raw64");wide(p,"/prospective_frames/0/date_storage_raw64");narrow(p,"/prospective_frames/0/calendar_day_u8");}
            case SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1 -> {wide(p,"/conditional_writes/1/observed_value");narrow(p,"/conditional_writes/0/observed_value");narrow(p,"/observed_current_army_byte_22_raw");narrow(p,"/observed_current_grace_elapsed_days");}
            case SOURCE_DERIVED_NEXT_FLEET_SUPPLY_BUDGET_V1 -> {wide(p,"/supply_base_fraction_raw");wide(p,"/held_current_supply_stock_raw");narrow(p,"/conditional_supply_budget_soldiers");}
            case SOURCE_DERIVED_NEXT_STOCK_SUPPLY_BUDGET_V1 -> {wide(p,"/conditional_post_updater_stock/raw");wide(p,"/conditional_budget_getter/base_fraction_raw");narrow(p,"/conditional_budget_getter/state_index");}
            case CURRENT_CALLBACK_SUPPLY_RISK_V1 -> {wide(p,"/observed_current_stock_state/base_fraction_raw");narrow(p,"/observed_current_stock_state/stock_integer");narrow(p,"/conditional_supply_budget_soldiers");}
            case CURRENT_CALLBACK_SOLDIER_EFFECTS_V1 -> {wide(p,"/conditional_post_stock_raw");wide(p,"/conditional_loss_sequence_v1/passes/0/requests/0/writer_quantity_raw");narrow(p,"/conditional_loss_sequence_v1/passes/0/requests/0/requested_soldiers");}
            default -> throw new IllegalArgumentException("nonbaseline role test");
        }
    }
    @Test void originalNormalizerAndEveryBaselineStageReachActualNativeAndPublicEncoders() throws Exception {
        for(JsonNode fixture:corpus()){
            String name=fixture.get("name").textValue();JsonNode row=fixture.get("row");
            for(var e=fixture.get("families").properties().iterator();e.hasNext();){
                var entry=e.next();Key key=Key.valueOf(entry.getKey().toUpperCase(Locale.ROOT));JsonNode nativeValue=nativeFamily(key,entry.getValue(),row);
                assertEquals(domain(entry.getValue()),domain(nativeValue),name+" "+key+" actual native encoder");
                RawJson original=raw(nativeValue);RawJson pub=ArmyStrengthsBaselinePublicRules.encodeFamily(key,original);
                assertEquals(domain(publicExpected(entry.getValue(),ArmyStrengthsBaselinePublicRules.familyRules(key))),domain(tree(pub)),name+" "+key+" publicV2");
                familyRoles(key,tree(pub));
                assertEquals(domain(nativeValue),domain(tree(original)),"public encoding cannot mutate native packet");
            }
            for(var e=fixture.get("stages").properties().iterator();e.hasNext();){
                var entry=e.next();Stage stage=Stage.valueOf(entry.getKey().toUpperCase(Locale.ROOT));JsonNode nativeValue=nativeStage(stage,row,fixture.get("replenishment_input"));
                assertEquals(domain(entry.getValue()),domain(nativeValue),name+" "+stage+" actual native producer");
                RawJson original=raw(nativeValue);RawJson pub=ArmyStrengthsBaselinePublicRules.encodeStage(stage,original);
                assertEquals(domain(publicExpected(entry.getValue(),ArmyStrengthsBaselinePublicRules.stageRules(stage))),domain(tree(pub)),name+" "+stage+" publicV2");
                stageRoles(stage,tree(pub));
                assertEquals(domain(nativeValue),domain(tree(original)),"native stage packet is preserved");
            }
        }
    }
    @Test void fieldRolesKeepBytesDwordsFloatsAndMixedWritePositionsWhileRejectingUnknownUnsafe() throws Exception {
        ObjectNode nativeValue=JSON.createObjectNode();nativeValue.put("accumulated_movement_weight_raw",Long.MIN_VALUE);
        nativeValue.put("unit_state_raw",Integer.MIN_VALUE);nativeValue.put("current_province_type_tag_u32",4294967295L);nativeValue.put("float_operand",1.25);
        JsonNode actual=tree(ArmyStrengthsBaselinePublicRules.encodeFamily(Key.CURRENT_MOVEMENT_PROGRESS,raw(nativeValue)));
        assertEquals("-9223372036854775808",actual.get("accumulated_movement_weight_raw").textValue());
        assertTrue(actual.get("unit_state_raw").isIntegralNumber());assertEquals(4294967295L,actual.get("current_province_type_tag_u32").longValue());
        assertTrue(actual.get("float_operand").isFloatingPointNumber());assertEquals(1.25,actual.get("float_operand").doubleValue());
        nativeValue.put("undeclared",Long.MAX_VALUE);
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsBaselinePublicRules.encodeFamily(Key.CURRENT_MOVEMENT_PROGRESS,raw(nativeValue)));
        ArrayNode mixed=JSON.createArrayNode();ObjectNode p=mixed.addObject().putObject("projection");ArrayNode writes=p.putArray("conditional_writes");
        writes.addObject().put("observed_value",255).put("conditional_value",254);writes.addObject().put("observed_value",Long.MIN_VALUE).put("conditional_value",Long.MAX_VALUE);
        JsonNode encoded=tree(ArmyStrengthsBaselinePublicRules.encodeStage(Stage.SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1,raw(mixed)));
        assertTrue(encoded.get(0).path("projection").path("conditional_writes").get(0).get("observed_value").isIntegralNumber());
        assertEquals("9223372036854775807",encoded.get(0).path("projection").path("conditional_writes").get(1).get("conditional_value").textValue());
        for(Key key:List.of(Key.REGIMENT_STRENGTHS,Key.NATIVE_ARMY_RESOLUTION_V1,Key.MONTHLY_DAILY_QUEUE_INPUTS_V1,Key.CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1,Key.CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1))assertTrue(ArmyStrengthsBaselinePublicRules.familyRules(key).isEmpty());
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsBaselinePublicRules.familyRules(Key.CURRENT_DAILY_ASSAULT_TABLE_V1));
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsBaselinePublicRules.stageRules(Stage.CURRENT_DAILY_ASSAULT_PLACEMENT_INPUTS_V1));
    }

    @Test void soleRosterRulesCoverRawAndDerivedClosureWithoutStringifyingFullIdsOrEndMarkers() throws Exception {
        JsonNode first=corpus().get(0);
        var root=ArmyStrengthsRosterContract.decodeRoot(ArmyStrengthsRosterContract.normalizeRoster(first.get("roster_normalized")));
        JsonNode nativeRoot=ArmyStrengthsRosterContract.encodeRoot(root);
        JsonNode publicRoot=tree(ArmyStrengthsPublicNumbers.encode(raw(nativeRoot),
                ArmyStrengthsRosterPublicRules.publicRules("ArmyCurrentDailyAssaultRosterAdmissionV1","")));
        wide(publicRoot,"/occurrences/0/gate/relation_lookup/probes/0/slot_index_i64");
        wide(publicRoot,"/occurrences/0/gate/relation_lookup/candidate_slot_index_i64");
        wide(publicRoot,"/occurrences/0/pending_selection/home_slot_i64");
        narrow(publicRoot,"/occurrences/0/native_index");narrow(publicRoot,"/occurrences/3/raw_full_id_u32");
        narrow(publicRoot,"/occurrences/0/pending_selection/mask_raw_i32");
        JsonNode nativeProjection=ArmyStrengthsRosterContract.encodeProjection(ArmyStrengthsRosterContract.project(root,11));
        assertEquals(domain(first.get("roster_projection")),domain(nativeProjection),"actual original roster projection");
        JsonNode publicProjection=tree(ArmyStrengthsPublicNumbers.encode(raw(nativeProjection),ArmyStrengthsRosterPublicRules.publicRules("Projection","")));
        wide(publicProjection,"/request_prefix/0/source_provenance/relation_lookup/probe_ledger/0/slot_index_i64");
        wide(publicProjection,"/independently_derived_requests/0/source_provenance/pending_selection/probe_ledger/0/physical_slot_i64");
        wide(publicProjection,"/occurrences/0/pending_selection/selected_physical_slot_i64");
        narrow(publicProjection,"/request_prefix/0/siege_full_id_u32");
        narrow(publicProjection,"/request_prefix/0/arrg_full_ids_u32/0");
        assertEquals(20,ArmyStrengthsRosterPublicRules.publicRules("Projection","").size());
        assertEquals(5,ArmyStrengthsRosterPublicRules.publicRules("RequestProvenance","/*/source_provenance").size());
        assertTrue(ArmyStrengthsRosterPublicRules.publicRules("RawReferences","/holder").isEmpty());
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsRosterPublicRules.publicRules("Root",""));
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsRosterPublicRules.publicRules("PendingProbe","/bad/"));
    }
    @Test void declaredWideRolesRejectWrongTypesAndOverflowWithoutInventingMissingNullOrEmpty() throws Exception {
        for(String value:List.of("true","1.0","\"1\"","9223372036854775808","-9223372036854775809")){
            JsonNode input=JSON.readTree("{\"last_supply_update_date_storage_raw64\":"+value+"}");
            assertThrows(IllegalArgumentException.class,()->ArmyStrengthsBaselinePublicRules.encodeFamily(Key.ARMY_UPDATE_CLOCK_V1,raw(input)));
        }
        for(String value:List.of("null","{}","{\"last_supply_update_date_storage_raw64\":null}")){
            JsonNode input=JSON.readTree(value);
            assertEquals(domain(input),domain(tree(ArmyStrengthsBaselinePublicRules.encodeFamily(Key.ARMY_UPDATE_CLOCK_V1,raw(input)))));
        }
        assertEquals(JSON.createArrayNode(),tree(ArmyStrengthsBaselinePublicRules.encodeStage(Stage.SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1,raw(JSON.createArrayNode()))));
    }
}

