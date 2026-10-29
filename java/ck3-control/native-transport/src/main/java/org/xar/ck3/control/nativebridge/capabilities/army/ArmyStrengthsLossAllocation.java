package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferCodec;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection;
import org.xar.ck3.control.wave2.military.armytransfer.ManagerCleanupProjection;
import org.xar.ck3.control.wave2.military.lossallocation.ObservedLossRequests;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;
import org.xar.ck3.control.wave2.military.losssequence.LossSequencePolicy;
import org.xar.ck3.control.wave2.military.monthlycaller.ArmyMonthlyCaller;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossPolicy;
import org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection;
import org.xar.ck3.control.wave3.military.landcontext.ProvinceUsageProjection;

/** Complete original project_observed_army_loss_requests stage, with all ten actual pure dependencies. */
public final class ArmyStrengthsLossAllocation {
    private ArmyStrengthsLossAllocation(){}
    public record ArmyProjection(int armyId,ObservedLossRequests.Result observed,ObservedLossRequests.InitialWriteback initial,
            LossSequenceModel.Result explicitSequence,MonthlyLossModel.Result monthly,LossSequenceModel.Result monthlySequence,
            ArmyMonthlyCaller.Result caller,DailyQueueTransferProjection.Result transfer,ManagerCleanupProjection.Result cleanup,
            ArmyHelperDomainProjection.Result domain,ArmyHelperPointProjection.Result points,AssociatedRefillProjection.Result associated,
            ProvinceUsageProjection.Result province){
        public ArmyProjection{Objects.requireNonNull(monthly);Objects.requireNonNull(caller);Objects.requireNonNull(transfer);Objects.requireNonNull(cleanup);Objects.requireNonNull(domain);Objects.requireNonNull(points);Objects.requireNonNull(associated);Objects.requireNonNull(province);}}
    public record Allocation(List<ArmyProjection> armies){public Allocation{armies=List.copyOf(armies);}}
    /** Families are registered by their sole normalizer owners. This installer adds only the complete stage. */
    public static void install(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline,ExactRef actualJavaBundleSource){
        Objects.requireNonNull(registry);Objects.requireNonNull(pipeline);Objects.requireNonNull(actualJavaBundleSource);
        pipeline.register(ArmyStrengthsPipeline.Stage.LOSS_ALLOCATION_REQUESTS_V1,Allocation.class,List.of(),
            (input,earlier)->new Allocation(input.selected().stream().map(row->projectRow(earlier.rowJson(row))).toList()),
            ArmyStrengthsLossAllocation::encode,ArmyStrengthsLossAllocation::encodePublicV2,actualJavaBundleSource);
    }
    /** Declared normalized row entry also serves original-producer differential capture without native IO. */
    public static ArmyProjection projectRow(JsonNode row){
        StrictJson.require(row!=null&&row.isObject(),"normalized Army loss stage row required");
        int id=(int)StrictJson.integer(row.get("army_id"),0,Integer.MAX_VALUE);
        var monthly=MonthlyLossPolicy.constructConditionalMonthlyLossBudgets(MonthlyLossCodec.decodeArmyProjection(row));
        var rawLoss=ObservedLossRequests.decode(row);var monthlySequence=monthly.lossSequenceSeed()==null?null:LossSequencePolicy.projectWithDerivedBudgets(rawLoss.writer(),monthly.lossSequenceSeed());
        Integer nativeId=row.get("native_carmy_id")==null||row.get("native_carmy_id").isNull()?null:(int)StrictJson.integer(row.get("native_carmy_id"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        var domainSource=ArmyStrengthsMonthlyCodec.decodeDomain(row.get("monthly_current_helper_domain_inputs_v1"));
        var domain=ArmyHelperDomainProjection.project(nativeId,domainSource);
        var points=ArmyHelperPointProjection.project(nativeId,ArmyStrengthsMonthlyCodec.decodePoint(row.get("monthly_current_helper_point_store_inputs_v1")),domainSource,domain);
        var associated=AssociatedRefillProjection.project(row);var province=ProvinceUsageProjection.project(row);
        var caller=ArmyMonthlyCaller.project(row,monthly,monthlySequence);
        var transfer=DailyQueueTransferCodec.projectStrength(row);var cleanup=ManagerCleanupProjection.project(row,transfer);
        var observed=ObservedLossRequests.project(rawLoss);var initial=observed==null?null:ObservedLossRequests.initial(rawLoss,observed);
        var sequence=observed==null?null:LossSequencePolicy.project(rawLoss.writer());
        return new ArmyProjection(id,observed,initial,sequence,monthly,monthlySequence,caller,transfer,cleanup,domain,points,associated,province);
    }
    public static ObjectNode encodeArmy(ArmyProjection value){
        ObjectNode out=ObservedLossRequests.encode(value.observed());out.put("army_id",value.armyId());
        ObjectNode monthly=MonthlyLossCodec.kernelNode(value.monthly());monthly.putNull("same_input_conditional_loss_sequence_v1");
        if(value.monthlySequence()!=null)monthly.set("same_input_conditional_loss_sequence_v1",LossSequenceCodec.sequenceNode(value.monthlySequence(),LossSequenceCodec.InputBasis.DERIVED_BUDGET_AND_LOSS_SUBSYSTEM));
        out.set("same_input_conditional_monthly_loss_budgets_v1",monthly);
        out.set("same_input_conditional_monthly_caller_effects_v1",ArmyMonthlyCaller.encode(value.caller()));
        out.set("same_input_conditional_daily_id_transfer_v1",DailyQueueTransferCodec.toJson(value.transfer()));
        out.set("same_input_conditional_first_removal_manager_cleanup_v1",ManagerCleanupProjection.encode(value.cleanup()));
        out.set("same_input_conditional_current_helper_domain_updates_v1",ArmyHelperDomainProjection.encode(value.domain()));
        out.set("same_input_conditional_current_helper_point_stores_v1",ArmyHelperPointProjection.encode(value.points()));
        out.set("same_input_conditional_associated_refill_current_v1",AssociatedRefillProjection.encode(value.associated()));
        out.set("same_input_conditional_province_supply_usage_v1",ProvinceUsageProjection.encode(value.province()));
        if(value.observed()!=null){
            out.set("same_input_conditional_chunk_writeback_v1",ObservedLossRequests.encodeInitial(value.initial()));
            out.set("same_input_conditional_loss_sequence_v1",LossSequenceCodec.sequenceNode(value.explicitSequence()));
            out.put("input_basis","current_readonly_inputs; conditional requests, not updater execution");
        }
        return out;
    }
    public static RawJson encode(Allocation value){
        ArrayNode out=StrictJson.object().arrayNode();value.armies().forEach(v->out.add(encodeArmy(v)));return new RawJson(ArmyJson.bytes(out));
    }
    public static RawJson encodePublicV2(Allocation value){return ArmyStrengthsPublicNumbers.encode(encode(value),publicNumberRules());}
    public static List<ArmyStrengthsPublicNumbers.Rule> publicNumberRules(){
        List<ArmyStrengthsPublicNumbers.Rule> rules=new ArrayList<>();
        add(rules,"/*/passes/*/requests/*/writer_quantity_raw");
        String monthly="/*/same_input_conditional_monthly_loss_budgets_v1";
        for(String field:List.of("conditional_post_supply_raw","supply_base_fraction_raw","supply_effective_fraction_raw"))add(rules,monthly+"/"+field);
        sequenceRules(rules,monthly+"/same_input_conditional_loss_sequence_v1");sequenceRules(rules,"/*/same_input_conditional_loss_sequence_v1");
        String caller="/*/same_input_conditional_monthly_caller_effects_v1";
        for(String field:List.of("supply_update_date_before_raw64","conditional_supply_update_date_raw64","actual_caller_passed_date_raw64"))add(rules,caller+"/"+field);
        String domain="/*/same_input_conditional_current_helper_domain_updates_v1";
        for(String field:List.of("conditional_delta_raw64","conditional_domain_value_48_before_raw64","conditional_domain_value_48_after_raw64","actual_domain_value_48_after_raw64"))add(rules,domain+"/record_projections/*/"+field);
        for(String field:List.of("observed_initial_domain_value_48_raw64","conditional_domain_value_48_after_raw64","actual_domain_value_48_after_raw64"))add(rules,domain+"/domain_value_projections/*/"+field);
        writerRules(rules,"/*/same_input_conditional_chunk_writeback_v1/requests/*");
        return List.copyOf(rules);
    }
    /** Shared nested budget/caller codec paths for the REFILL installer; prefixes are explicit schema locations. */
    public static List<ArmyStrengthsPublicNumbers.Rule> monthlyPublicNumberRules(String monthlyPrefix,String callerPrefix){
        List<ArmyStrengthsPublicNumbers.Rule> rules=new ArrayList<>();
        for(String field:List.of("conditional_post_supply_raw","supply_base_fraction_raw","supply_effective_fraction_raw"))add(rules,monthlyPrefix+"/"+field);
        sequenceRules(rules,monthlyPrefix+"/same_input_conditional_loss_sequence_v1");
        for(String field:List.of("supply_update_date_before_raw64","conditional_supply_update_date_raw64","actual_caller_passed_date_raw64"))add(rules,callerPrefix+"/"+field);
        return List.copyOf(rules);
    }
    private static void sequenceRules(List<ArmyStrengthsPublicNumbers.Rule> rules,String prefix){
        add(rules,prefix+"/conditional_physical_current_delta");add(rules,prefix+"/passes/*/requests/*/writer_quantity_raw");
        writerRules(rules,prefix+"/passes/*/requests/*/conditional_chunk_writeback");
    }
    private static void writerRules(List<ArmyStrengthsPublicNumbers.Rule> rules,String prefix){
        for(String field:List.of("remaining_writer_quantity_raw","physical_current_delta"))add(rules,prefix+"/"+field);
        add(rules,prefix+"/writes/*/selected_quantity_raw");
    }
    private static void add(List<ArmyStrengthsPublicNumbers.Rule> rules,String path){rules.add(new ArmyStrengthsPublicNumbers.Rule(path,ArmyStrengthsPublicNumbers.Domain.SIGNED_64));}
}
