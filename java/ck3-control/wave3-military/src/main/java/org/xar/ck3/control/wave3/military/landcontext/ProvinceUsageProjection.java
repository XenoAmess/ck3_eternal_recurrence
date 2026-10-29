package org.xar.ck3.control.wave3.military.landcontext;

import static org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection.number;
import static org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection.strings;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;

/** One refill of each physical DATA cache, followed by every native ordered Province occurrence. */
public final class ProvinceUsageProjection {
    private ProvinceUsageProjection() {}
    public record Location(int provinceStoredIndex,int armyId,int regimentStoredIndex) {}
    public record PhysicalCoverage(int armyRegimentId,List<Location> occurrences){public PhysicalCoverage{occurrences=List.copyOf(occurrences);}}
    public record RegimentResult(int storedIndex,int armyRegimentId,Boolean eligible,Integer currentBefore,Integer maximumBefore,
            boolean ready,Integer current,Integer maximum,Integer contribution,List<String> missing){public RegimentResult{missing=List.copyOf(missing);}}
    public sealed interface OccurrenceGap permits FieldGap,RegimentGap {}
    public record FieldGap(String input) implements OccurrenceGap {}
    public record RegimentGap(int storedIndex,int armyRegimentId,List<String> inputs) implements OccurrenceGap{public RegimentGap{inputs=List.copyOf(inputs);}}
    public record OccurrenceResult(ProvinceContributors.Occurrence source,boolean ready,Integer contribution,List<RegimentResult> regiments,List<OccurrenceGap> missing){
        public OccurrenceResult{regiments=List.copyOf(regiments);missing=List.copyOf(missing);}
    }
    public record Result(AssociatedRefillProjection.Status status,ProvinceContributors source,boolean currentSumReady,Integer currentSum,
            boolean conditionalReady,Integer conditionalUsage,List<OccurrenceResult> occurrences,AssociatedRefillProjection.Result refill,
            List<PhysicalCoverage> physicalCoverage,boolean rosterReady) {
        public Result{occurrences=List.copyOf(occurrences);physicalCoverage=List.copyOf(physicalCoverage);}
    }
    public static Result project(JsonNode row) {
        StrictJson.require(row!=null&&row.isObject(),"Province usage row required");
        return project(LandContextCodec.decodeProvince(row.get("current_province_supply_contributors_v1")));
    }
    public static Result project(ProvinceContributors family) {
        if(family==null)return new Result(AssociatedRefillProjection.Status.UNAVAILABLE,null,false,null,false,null,List.of(),null,List.of(),false);
        Map<Integer,List<ProvinceContributors.Regiment>> byRegiment=new LinkedHashMap<>();Map<Integer,List<Location>> locations=new LinkedHashMap<>();
        for(var occurrence:family.occurrences())if(Boolean.TRUE.equals(occurrence.included()))for(var regiment:occurrence.regiments())if(Boolean.TRUE.equals(regiment.nativeSupplyLossEligible())) {
            byRegiment.computeIfAbsent(regiment.armyRegimentId(),ignored->new ArrayList<>()).add(regiment);
            locations.computeIfAbsent(regiment.armyRegimentId(),ignored->new ArrayList<>()).add(new Location(occurrence.storedIndex(),occurrence.armyId(),regiment.storedIndex()));
        }
        List<FullDataModel.Snapshot> snapshots=new ArrayList<>();List<LossSequenceModel.Regiment> strengths=new ArrayList<>();Map<Integer,String> unavailable=new LinkedHashMap<>();
        for(var entry:byRegiment.entrySet()) {
            List<FullDataModel.Snapshot> candidates=entry.getValue().stream().map(ProvinceContributors.Regiment::replenishmentRecords).filter(java.util.Objects::nonNull).toList();
            List<FullDataModel.Snapshot> complete=candidates.stream().filter(s->s.status()==FullDataModel.Coverage.AVAILABLE).toList();
            var chosen=!complete.isEmpty()?complete.getFirst():!candidates.isEmpty()?candidates.getFirst():null;
            if(chosen==null){unavailable.put(entry.getKey(),"observed_associated_DATA");continue;}
            if(complete.stream().anyMatch(s->!s.equals(chosen))){unavailable.put(entry.getKey(),"consistent_same_physical_ArRg_DATA");continue;}
            snapshots.add(chosen);var first=entry.getValue().getFirst();strengths.add(new LossSequenceModel.Regiment(entry.getKey(),first.currentSoldiers(),first.maximumSoldiers(),null,null,true));
        }
        var refill=AssociatedRefillProjection.project(new AssociatedRefillProjection.Input(true,family.subjectArmyId()==null?0:family.subjectArmyId(),snapshots,strengths));
        Map<Integer,RaisedRegimentRefresh.Result> refreshes=new LinkedHashMap<>();refill.refreshes().forEach(r->refreshes.put(r.regimentId(),r));
        List<PhysicalCoverage> coverage=locations.entrySet().stream().map(e->new PhysicalCoverage(e.getKey(),e.getValue())).toList();
        List<OccurrenceResult> occurrences=new ArrayList<>();int currentSum=0,conditionalSum=0;boolean currentRows=true,conditionalRows=true;
        for(var occurrence:family.occurrences()) {
            Boolean included=occurrence.included();Integer current=Boolean.FALSE.equals(included)?Integer.valueOf(0):occurrence.nativeEligibleCurrentSoldiers();
            if(included==null||current==null)currentRows=false;else currentSum+=current;
            List<RegimentResult> regiments=new ArrayList<>();List<OccurrenceGap> missing=new ArrayList<>();boolean ready=false;Integer contribution=null;
            if(Boolean.FALSE.equals(included)){ready=true;contribution=0;}
            else if(included==null)missing.add(new FieldGap("native_owner_admission"));
            else {
                int sum=0;boolean all=true;
                for(var r:occurrence.regiments()) {
                    boolean rr=false;Integer after=null,max=null,amount=null;List<String> gaps=new ArrayList<>();
                    if(Boolean.FALSE.equals(r.nativeSupplyLossEligible())){rr=true;after=r.currentSoldiers();max=r.maximumSoldiers();amount=0;}
                    else if(r.nativeSupplyLossEligible()==null)gaps.add("native_supply_loss_eligibility");
                    else if(unavailable.containsKey(r.armyRegimentId()))gaps.add(unavailable.get(r.armyRegimentId()));
                    else {
                        var refresh=refreshes.get(r.armyRegimentId());
                        if(refresh!=null&&refresh.ready()){rr=true;after=refresh.current();max=refresh.maximum();amount=after;}
                        else gaps.addAll(refresh==null?List.of("conditional_ArRg_refresh"):refresh.missingInputs());
                    }
                    if(rr)sum+=amount;else all=false;
                    regiments.add(new RegimentResult(r.storedIndex(),r.armyRegimentId(),r.nativeSupplyLossEligible(),r.currentSoldiers(),r.maximumSoldiers(),rr,after,max,amount,gaps));
                }
                if(occurrence.status()!=FullDataModel.RecordStatus.AVAILABLE){all=false;missing.add(new FieldGap("complete_native_ArRg_roster"));}
                if(all){ready=true;contribution=sum;}
                else for(var r:regiments)if(!r.ready())missing.add(new RegimentGap(r.storedIndex(),r.armyRegimentId(),r.missing()));
            }
            if(ready)conditionalSum+=contribution;else conditionalRows=false;
            occurrences.add(new OccurrenceResult(occurrence,ready,contribution,regiments,missing));
        }
        boolean roster=family.contributorsReady()&&family.nativeProvinceUnitCount()!=null&&family.nativeProvinceUnitCount()>=0&&family.nativeProvinceUnitCount()==family.occurrences().size();
        boolean currentReady=roster&&currentRows,conditionalReady=roster&&conditionalRows;
        boolean any=family.currentUsageReady()||currentReady||occurrences.stream().anyMatch(OccurrenceResult::ready);
        return new Result(conditionalReady?AssociatedRefillProjection.Status.AVAILABLE:any?AssociatedRefillProjection.Status.PARTIAL:AssociatedRefillProjection.Status.UNAVAILABLE,
                family,currentReady,currentReady?currentSum:null,conditionalReady,conditionalReady?conditionalSum:null,occurrences,refill,coverage,roster);
    }
    public static ObjectNode encode(Result result) {
        ObjectNode out=StrictJson.object();out.put("projection_kind","conditional_current_province_supply_usage");out.put("source_contract_game_version","1.20.0.3");
        out.put("input_basis","observed_Province_mode0_roster_admission_and_eligibility; one_explicit_core_invocation_per_observed_persistent_cache");out.put("status",result.status().name().toLowerCase(java.util.Locale.ROOT));
        out.put("current_usage_ready",false);out.put("contributors_ready",false);out.putNull("native_supply_usage_soldiers");out.putNull("native_supply_limit_soldiers");out.put("soldiers_scale",1);
        out.put("current_contributor_sum_ready",result.currentSumReady());number(out,"current_contributor_sum_soldiers",result.currentSum());out.put("conditional_usage_ready",result.conditionalReady());number(out,"conditional_supply_usage_soldiers",result.conditionalUsage());
        out.put("actual_replenishment",false);out.put("actual_loss",false);out.putNull("actual_post_stage_current");out.putNull("actual_post_supply_usage_soldiers");out.put("full_regular_refill_ready",false);out.put("full_monthly_ready",false);
        ArrayNode excluded=out.putArray("excluded_stages");excluded.add("manager_roster_order_and_preparation").add("post_refill_supply_rate_and_stock").add("actual_monthly_entry_and_loss_application");
        out.putNull("physical_refill");ArrayNode occurrences=out.putArray("occurrences"),missing=out.putArray("missing_inputs");
        if(result.source()==null){missing.add("current_province_supply_contributors_v1");return out;}
        var source=result.source();out.put("current_usage_ready",source.currentUsageReady());out.put("contributors_ready",source.contributorsReady());
        number(out,"province_id",source.provinceId());number(out,"subject_army_id",source.subjectArmyId());number(out,"subject_carmy_id",source.subjectCarmyId());number(out,"owner_character_id",source.ownerCharacterId());number(out,"native_province_unit_count",source.nativeProvinceUnitCount());number(out,"native_supply_usage_soldiers",source.nativeSupplyUsageSoldiers());number(out,"native_supply_limit_soldiers",source.nativeSupplyLimitSoldiers());
        out.put("native_observation_status",source.status().name().toLowerCase(java.util.Locale.ROOT));if(source.unavailableReason()==null)out.putNull("native_observation_unavailable_reason");else out.put("native_observation_unavailable_reason",source.unavailableReason());
        for(var occurrence:result.occurrences()) {
            var s=occurrence.source();ObjectNode row=occurrences.addObject();row.put("stored_index",s.storedIndex());row.put("army_id",s.armyId());number(row,"native_carmy_id",s.nativeCarmyId());number(row,"owner_character_id",s.ownerCharacterId());
            if(s.included()==null)row.putNull("included");else row.put("included",s.included());if(s.inclusionBasis()==null)row.putNull("inclusion_basis");else row.put("inclusion_basis",s.inclusionBasis().name().toLowerCase(java.util.Locale.ROOT));
            number(row,"native_eligible_current_soldiers",s.nativeEligibleCurrentSoldiers());row.put("conditional_ready",occurrence.ready());number(row,"conditional_eligible_current_soldiers",occurrence.contribution());
            ArrayNode regiments=row.putArray("regiments");for(var r:occurrence.regiments()) {
                ObjectNode n=regiments.addObject();n.put("stored_index",r.storedIndex());n.put("army_regiment_id",r.armyRegimentId());if(r.eligible()==null)n.putNull("native_supply_loss_eligible");else n.put("native_supply_loss_eligible",r.eligible());
                number(n,"current_soldiers_before",r.currentBefore());number(n,"maximum_soldiers_before",r.maximumBefore());n.put("conditional_ready",r.ready());number(n,"conditional_current_soldiers",r.current());number(n,"conditional_maximum_soldiers",r.maximum());number(n,"conditional_supply_contribution",r.contribution());strings(n,"missing_inputs",r.missing());
            }
            encodeGaps(row.putArray("missing_inputs"),occurrence.missing());
            if(!occurrence.ready()){ObjectNode gap=missing.addObject();gap.put("province_stored_index",s.storedIndex());gap.put("army_id",s.armyId());encodeGaps(gap.putArray("inputs"),occurrence.missing());}
        }
        if(!result.rosterReady())missing.add("complete_native_Province_occurrence_roster");
        out.set("physical_refill",AssociatedRefillProjection.encode(result.refill()));ArrayNode coverage=out.putArray("physical_regiment_coverage");
        for(var c:result.physicalCoverage()){ObjectNode n=coverage.addObject();n.put("army_regiment_id",c.armyRegimentId());ArrayNode positions=n.putArray("occurrences");for(var p:c.occurrences()){ObjectNode x=positions.addObject();x.put("province_stored_index",p.provinceStoredIndex());x.put("army_id",p.armyId());x.put("regiment_stored_index",p.regimentStoredIndex());}}
        return out;
    }
    private static void encodeGaps(ArrayNode out,List<OccurrenceGap> gaps){for(var gap:gaps)switch(gap){case FieldGap g->out.add(g.input());case RegimentGap g->{ObjectNode n=out.addObject();n.put("regiment_stored_index",g.storedIndex());n.put("army_regiment_id",g.armyRegimentId());strings(n,"inputs",g.inputs());}}}
}
