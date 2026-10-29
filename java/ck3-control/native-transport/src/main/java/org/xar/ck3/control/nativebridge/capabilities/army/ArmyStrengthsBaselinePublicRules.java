package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.*;

/** Reviewed numeric field roles of the thirteen original families and eight original stage producers.
 * This boundary runs after each real native encoder. It changes declared wide integer leaves only.
 * A Java Long used to retain a byte or DWORD does not grant a wide-string role. */
public final class ArmyStrengthsBaselinePublicRules {
    private ArmyStrengthsBaselinePublicRules() { }
    private static final BigInteger SAFE=BigInteger.valueOf(9_007_199_254_740_991L);
    private static Rule signed(String path){return new Rule(path,Domain.SIGNED_64);}
    private static Rule computed(String path){return new Rule(path,Domain.INTEGER);}
    private static List<Rule> signedPaths(String... paths){return java.util.Arrays.stream(paths).map(ArmyStrengthsBaselinePublicRules::signed).toList();}
    private static List<Rule> prefix(String prefix,List<Rule> rules){return rules.stream().map(r->new Rule(prefix+r.exactPath(),r.domain())).toList();}
    @SafeVarargs private static List<Rule> combine(List<Rule>... parts){List<Rule> result=new ArrayList<>();for(List<Rule> part:parts)result.addAll(part);return List.copyOf(result);}
    private static List<Rule> sourceClock(){return signedPaths("/current_date_storage_raw64","/source_derived_next_date_storage_raw64");}
    private static List<Rule> fleetRate(){
        // The actual native fixed division's Java result is BigInteger, including the explicit
        // zero-divisor native branch. Its exact computed integer domain is deliberately retained.
        return combine(List.of(computed("/conditional_full_fleet_rate_raw")),signedPaths("/commander_divisor_raw","/current_observed_total_rate_raw"));
    }
    private static List<Rule> dateWrite(String collection){return signedPaths(collection+"/1/observed_value",collection+"/1/conditional_value");}
    public static List<Rule> familyRules(ArmyStrengthsFamilies.Key key){
        Objects.requireNonNull(key);
        return switch(key){
            // These exact complete schemas contain only byte/word/DWORD, bool, text or null.
            case REGIMENT_STRENGTHS,NATIVE_ARMY_RESOLUTION_V1,MONTHLY_DAILY_QUEUE_INPUTS_V1,
                 CURRENT_DAILY_SUPPLY_DISPATCH_INPUTS_V1,CURRENT_ARMY_COMBAT_ROLES_PHASE_INPUTS_V1 -> List.of();
            case LOSS_APPLICATION_INPUTS_V1 -> signedPaths("/siege_rate_raw","/raid_rate_raw");
            case CURRENT_MOVEMENT_PROGRESS -> signedPaths("/accumulated_movement_weight_raw","/cached_edge_speed_raw",
                    "/normalized_edge_progress/raw","/first_route_edge_remaining_duration/raw","/current_edge_movement_rate_raw",
                    "/first_route_edge_weight_cost_raw","/loaded_movement_lock_cutoff/raw",
                    "/committed_route_timeline/native_full_route_remaining_days_q100000",
                    "/committed_route_timeline/native_route_prefix_remaining_days_q100000/*");
            case ARMY_UPDATE_CLOCK_V1 -> signedPaths("/last_supply_update_date_storage_raw64","/grace_anchor_date_storage_raw64");
            case MONTHLY_LOSS_BUDGET_INPUTS_V1 -> signedPaths("/commander_supply_modifier_raw","/loaded_supply_state_fractions_raw/*");
            case COUNTY_ENTRY_INPUTS_V1 -> signedPaths("/effective_fraction_raw","/minimum_multiplier_raw",
                    "/multiplier_floor_inputs_v1/base_floor_raw","/multiplier_floor_inputs_v1/army_1d4_nonzero_floor_raw");
            case SOURCE_DERIVED_NEXT_DAILY_SUPPLY_FRAME_INPUTS_V1 -> sourceClock();
            case CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1 -> signedPaths("/terrain_modifier_772_raw","/loaded_fleet_loss_raw",
                    "/commander_modifier_1a9_raw","/loaded_divisor_floor_raw","/loaded_max_loss_raw");
            case FUTURE_DAILY_SUPPLY_SCHEDULE_INPUTS_V1 -> signedPaths("/current_date_storage_raw64");
            default -> throw new IllegalArgumentException("No reviewed baseline family numeric policy: "+key);
        };
    }
    public static List<Rule> stageRules(ArmyStrengthsPipeline.Stage stage){
        Objects.requireNonNull(stage);
        return switch(stage){
            case SAME_INPUT_REPLENISHMENT_V1 -> signedPaths(
                    "/persistent_outputs/*/effective_deficit_by_chunk/*",
                    "/persistent_outputs/*/observations_by_chunk/*/*/calculation/effective_deficit",
                    "/persistent_outputs/*/observations_by_chunk/*/*/calculation/wrapped_product",
                    "/persistent_outputs/*/observations_by_chunk/*/*/calculation/selected_scaled_numerator");
            case SAME_INPUT_CONDITIONAL_NEXT_ADMITTED_DAY_FLEET_RATE_V1 -> prefix("/*/projection",fleetRate());
            case SAME_INPUT_CONDITIONAL_FUTURE_DAILY_SUPPLY_SCHEDULE_V1 -> prefix("/*/projection",combine(
                    signedPaths("/current_date_storage_raw64","/source_derived_next_date_storage_raw64",
                            "/prospective_frames/*/date_storage_raw64"),prefix("/source_next_pair",sourceClock())));
            case SOURCE_DERIVED_NEXT_UPDATER_WRITES_V1 -> prefix("/*/projection",combine(
                    prefix("/source_next_date",sourceClock()),dateWrite("/conditional_writes"),
                    signedPaths("/observed_current_last_supply_update_date_storage_raw64","/observed_current_caller_date_storage_raw64",
                            "/conditional_grace_anchor_190/observed_value","/conditional_grace_anchor_190/conditional_value")));
            case SOURCE_DERIVED_NEXT_FLEET_SUPPLY_BUDGET_V1 -> prefix("/*/projection",combine(
                    prefix("/source_next_global_clock",sourceClock()),
                    signedPaths("/held_current_supply_stock_raw","/supply_base_fraction_raw","/supply_effective_fraction_raw")));
            case SOURCE_DERIVED_NEXT_STOCK_SUPPLY_BUDGET_V1 -> prefix("/*/projection",combine(
                    signedPaths("/observed_current_stock_raw","/observed_current_rate_raw","/observed_current_capacity_raw",
                            "/conditional_post_updater_stock/raw","/conditional_post_updater_stock/signed64_add_raw",
                            "/conditional_budget_getter/stock_raw","/conditional_budget_getter/base_fraction_raw","/conditional_budget_getter/effective_fraction_raw"),
                    prefix("/source_next_date",sourceClock()),dateWrite("/conditional_pre_rate_writes"),
                    List.of(computed("/conditional_rate/raw")),prefix("/conditional_rate/existing_fleet_rate_projection",fleetRate())));
            case CURRENT_CALLBACK_SUPPLY_RISK_V1 -> prefix("/*/projection",signedPaths(
                    "/observed_current_supply_raw","/observed_current_supply_capacity_raw","/observed_current_supply_change_monthly_raw",
                    "/observed_current_attrition_fraction_raw","/observed_last_supply_update_date_raw64","/conditional_post_stock_raw",
                    "/conditional_supply_effective_fraction_raw","/observed_current_stock_state/base_fraction_raw",
                    "/conditional_post_stock_state/base_fraction_raw"));
            case CURRENT_CALLBACK_SOLDIER_EFFECTS_V1 -> prefix("/*/projection",signedPaths(
                    "/conditional_post_stock_raw","/conditional_loss_sequence_v1/conditional_physical_current_delta",
                    "/conditional_loss_sequence_v1/passes/*/requests/*/writer_quantity_raw",
                    "/conditional_loss_sequence_v1/passes/*/requests/*/conditional_chunk_writeback/writes/*/selected_quantity_raw",
                    "/conditional_loss_sequence_v1/passes/*/requests/*/conditional_chunk_writeback/remaining_writer_quantity_raw",
                    "/conditional_loss_sequence_v1/passes/*/requests/*/conditional_chunk_writeback/physical_current_delta"));
            default -> throw new IllegalArgumentException("No reviewed baseline stage numeric policy: "+stage);
        };
    }
    public static RawJson encodeFamily(ArmyStrengthsFamilies.Key key,RawJson nativeJson){return encode(nativeJson,familyRules(key));}
    public static RawJson encodeStage(ArmyStrengthsPipeline.Stage stage,RawJson nativeJson){return encode(nativeJson,stageRules(stage));}
    private static RawJson encode(RawJson nativeJson,List<Rule> rules){
        RawJson result=ArmyStrengthsPublicNumbers.encode(Objects.requireNonNull(nativeJson),rules);
        requireSafe(ArmyStrengthsCodec.parseValue(result),"");
        return result;
    }
    /** Undeclared unsafe integer leaves are an explicit migration error, never a reason to infer a string role. */
    private static void requireSafe(JsonNode value,String path){
        if(value.isIntegralNumber()){
            if(value.bigIntegerValue().abs().compareTo(SAFE)>0)throw new IllegalArgumentException("Undeclared unsafe baseline public integer at "+path);
        }else if(value.isObject()){
            var fields=value.properties().iterator();
            while(fields.hasNext()){var field=fields.next();requireSafe(field.getValue(),path+"/"+field.getKey());}
        }else if(value.isArray()){
            for(int i=0;i<value.size();i++)requireSafe(value.get(i),path+"/"+i);
        }
    }
}

