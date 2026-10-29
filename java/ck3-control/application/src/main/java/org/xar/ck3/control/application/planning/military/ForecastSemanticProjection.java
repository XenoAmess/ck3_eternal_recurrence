package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;

/** Original native_driver snapshot fields and independent active-war power trace; no I/O, publication or inferred empty armies. */
public final class ForecastSemanticProjection {
    private ForecastSemanticProjection() {}
    private static final List<String> COMBAT=List.of("","_status","_query_sequence","_target_province_id","_attacker_entry_province_id","_attacker_army_ids","_defender_army_ids","_queried_snapshot_id","_queried_revision");
    private static final Set<String> WAR=Set.of("war_entry_assessments","war_entry_assessments_status","war_entry_assessments_query_sequence","war_entry_assessments_queried_snapshot_id","war_entry_assessments_queried_revision","war_entry_assessments_two_read_trace_v1");
    public record Projection(ForecastReadObservation.Kind kind,Obj fields,boolean semanticCache) {
        public Projection {
            java.util.Objects.requireNonNull(kind);java.util.Objects.requireNonNull(fields);
            Set<String> expected=switch(kind){case COMBAT_V2,COMBAT_V3->new java.util.HashSet<>(COMBAT.stream().map(suffix->prefix(kind)+suffix).toList());case WAR_ENTRY->WAR;case CURRENT_KNIGHT,PHASE_TRACE->Set.of();};
            OpportunityJson.require(fields.members().keySet().equals(expected)&&semanticCache==(kind==ForecastReadObservation.Kind.COMBAT_V2||kind==ForecastReadObservation.Kind.COMBAT_V3||kind==ForecastReadObservation.Kind.WAR_ENTRY),"fixed original forecast semantic fields required");
        }
    }
    public static Projection project(ForecastReadObservation actual,PlanningReadReceipt receipt,Obj currentSnapshot,Obj previousPublished) {
        java.util.Objects.requireNonNull(actual);java.util.Objects.requireNonNull(receipt);java.util.Objects.requireNonNull(currentSnapshot);java.util.Objects.requireNonNull(previousPublished);
        if(actual instanceof ForecastReadObservation.CurrentKnight||actual instanceof ForecastReadObservation.PhaseTrace)return new Projection(actual.kind(),new Obj(Map.of()),false);
        boolean same=sameFrame(receipt,currentSnapshot);
        if(actual instanceof ForecastReadObservation.CombatInputs combat) {
            var observed=combat.observation();boolean valid=same;
            try{valid&=observed.frame().equals(CombatObservationCache.Frame.decode(OpportunityJson.toNode(currentSnapshot)))&&observed.scope().equals(CombatEncounterScope.fromSnapshot(OpportunityJson.toNode(currentSnapshot),observed.request()));}
            catch(IllegalArgumentException invalid){valid=false;}
            var fields=clearCombat(actual.kind());String prefix=prefix(actual.kind());
            if(valid) {
                Obj value=DriverJson.object(org.xar.ck3.control.wave2.military.forecast.CombatJson.canonical(observed.toInternalJson()),DriverJson.MAX_NATIVE_BYTES);
                fields.put(prefix,value.get("combat_simulation_inputs"));
                for(String suffix:COMBAT)if(!suffix.isEmpty())fields.put(prefix+suffix,value.get(suffix.substring(1)));
            }
            return new Projection(actual.kind(),new Obj(fields),true);
        }
        var war=(ForecastReadObservation.WarEntry)actual;var fields=new LinkedHashMap<String,Value>();for(String field:WAR)fields.put(field,Nil.INSTANCE);
        fields.put("war_entry_assessments_two_read_trace_v1",new Arr(List.of()));
        if(same&&currentWarTarget(war,currentSnapshot)) {
            Obj result=war.normalizedResult();fields.put("war_entry_assessments",war.assessments());
            for(String key:List.of("status","query_sequence","queried_snapshot_id","queried_revision"))fields.put("war_entry_assessments_"+key,required(result,key));
            fields.put("war_entry_assessments_two_read_trace_v1",trace(war,currentSnapshot,previousPublished));
        }
        return new Projection(actual.kind(),new Obj(fields),true);
    }
    /** Expire only the original fixed semantic fields; this does not replay or qualify an old native read. */
    public static Projection unavailable(ForecastReadObservation.Kind kind) {
        java.util.Objects.requireNonNull(kind);
        return switch(kind) {
            case COMBAT_V2,COMBAT_V3 -> new Projection(kind,new Obj(clearCombat(kind)),true);
            case WAR_ENTRY -> {
                var fields=new LinkedHashMap<String,Value>();for(String field:WAR)fields.put(field,Nil.INSTANCE);
                fields.put("war_entry_assessments_two_read_trace_v1",new Arr(List.of()));yield new Projection(kind,new Obj(fields),true);
            }
            case CURRENT_KNIGHT,PHASE_TRACE -> new Projection(kind,new Obj(Map.of()),false);
        };
    }
    /** These reads are original history producers only; no synthetic cache or empty tactical roster is added. */
    public static Obj project(MilitaryReadObservation actual,PlanningReadReceipt receipt,Obj currentSnapshot) {
        java.util.Objects.requireNonNull(actual);java.util.Objects.requireNonNull(receipt);java.util.Objects.requireNonNull(currentSnapshot);return new Obj(Map.of());
    }
    private static Map<String,Value> clearCombat(ForecastReadObservation.Kind kind){var fields=new LinkedHashMap<String,Value>();for(String suffix:COMBAT)fields.put(prefix(kind)+suffix,Nil.INSTANCE);return fields;}
    private static String prefix(ForecastReadObservation.Kind kind){return kind==ForecastReadObservation.Kind.COMBAT_V2?"combat_simulation_inputs":"combat_simulation_inputs_v3";}
    private static Value required(Obj source,String key){Value actual=source.get(key);OpportunityJson.require(actual!=null,"normalized original forecast field missing: "+key);return actual;}
    private static boolean sameFrame(PlanningReadReceipt receipt,Obj snapshot) {
        if(!new Bool(true).equals(snapshot.get("paused")))return false;
        try {
            var frame=receipt.request().before().frame();var expected=new ActiveRetreatProposal.SourceFrame(frame.snapshotId(),frame.revision(),frame.identity().nativeRevision(),frame.identity().dateRaw(),frame.episodeRunId(),receipt.before().binding().connectionGeneration());
            return expected.equals(ActiveRetreatProposal.SourceFrame.read(snapshot))&&frame.identity().player().equals(OpportunityJson.integer(OpportunityJson.object(snapshot.get("played_character"),"actual actor").get("character_id"),"actual actor ID"));
        }catch(IllegalArgumentException missing){return false;}
    }
    private static boolean currentWarTarget(ForecastReadObservation.WarEntry actual,Obj snapshot) {
        try {
            List<Value> targets=OpportunityJson.array(actual.assessments().get("requested_target_character_ids"),"original targets");if(targets.size()!=1)return false;
            BigInteger target=OpportunityJson.integer(targets.getFirst(),"target");boolean present=false;
            for(Value value:OpportunityJson.array(snapshot.get("declarable_wars"),"current declarable wars")) {
                BigInteger id=OpportunityJson.integer(OpportunityJson.object(value,"declaration").get("target_character_id"),"declaration target");OpportunityJson.require(id.signum()>0&&id.bitLength()<=31,"positive declaration target required");present|=target.equals(id);
            }
            for(Value value:OpportunityJson.array(snapshot.get("active_wars"),"current active wars")) {
                var opponent=OpportunityJson.object(value,"war").get("primary_opponent_character_id");if(opponent==null||opponent==Nil.INSTANCE)continue;
                BigInteger id=OpportunityJson.integer(opponent,"current war opponent");OpportunityJson.require(id.signum()>=0&&id.bitLength()<=31,"current war opponent type differs");present|=target.equals(id);
            }
            return present;
        }catch(IllegalArgumentException missing){return false;}
    }
    private static Arr trace(ForecastReadObservation.WarEntry actual,Obj snapshot,Obj previous) {
        int target=OpportunityJson.integer(OpportunityJson.array(actual.assessments().get("requested_target_character_ids"),"targets").getFirst(),"target").intValueExact();Optional<Obj> current=activePowerFrame(snapshot,target);
        if(current.isEmpty())return new Arr(List.of());
        Obj frame=current.orElseThrow(),entry=new Obj(Map.of("target_character_id",new IntegerValue(BigInteger.valueOf(target)),"before_snapshot",frame,"after_snapshot",frame,"query",actual.normalizedResult()));
        List<Value> trace=previous.get("war_entry_assessments_two_read_trace_v1") instanceof Arr rows?rows.items():List.of();
        if(trace.size()==1&&trace.getFirst() instanceof Obj prior&&new IntegerValue(BigInteger.valueOf(target)).equals(prior.get("target_character_id"))&&frame.equals(prior.get("after_snapshot"))&&frame.equals(prior.get("before_snapshot"))) {
            Obj query=OpportunityJson.object(prior.get("query"),"original prior query");BigInteger previousSequence=OpportunityJson.integer(query.get("query_sequence"),"previous sequence"),currentSequence=OpportunityJson.integer(actual.normalizedResult().get("query_sequence"),"actual sequence");
            if(previousSequence.add(BigInteger.ONE).equals(currentSequence))return new Arr(List.of(prior,entry));
        }
        return new Arr(List.of(entry));
    }
    /** Existing original _active_war_power_frame_projection, with all full snapshot operands retained. */
    private static Optional<Obj> activePowerFrame(Obj snapshot,int opponent) {
        if(!new Bool(true).equals(snapshot.get("paused"))||!new Bool(true).equals(snapshot.get("map_ready"))||!(snapshot.get("played_character") instanceof Obj actor)||!(snapshot.get("diagnostics") instanceof Obj diagnostics)||!(snapshot.get("active_wars") instanceof Arr wars))return Optional.empty();
        List<Obj> matching=new ArrayList<>();for(Value value:wars.items())if(value instanceof Obj war&&new IntegerValue(BigInteger.valueOf(opponent)).equals(war.get("primary_opponent_character_id"))&&new Text("attacker").equals(war.get("player_side"))&&new Bool(true).equals(war.get("player_is_primary_war_leader")))matching.add(war);
        if(matching.size()!=1)return Optional.empty();Obj war=matching.getFirst();var fields=new LinkedHashMap<String,Value>();for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))fields.put(field,snapshot.get(field)==null?Nil.INSTANCE:snapshot.get(field));
        fields.put("paused",new Bool(true));fields.put("map_ready",new Bool(true));fields.put("diagnostics",new Obj(Map.of("connection_generation",optional(diagnostics,"connection_generation"),"bridge_pid",optional(diagnostics,"bridge_pid"))));
        fields.put("played_character",new Obj(Map.of("character_id",optional(actor,"character_id"))));fields.put("active_wars",new Arr(List.of(new Obj(Map.of("war_id",optional(war,"war_id"),"player_side",war.get("player_side"),"player_is_primary_war_leader",war.get("player_is_primary_war_leader"),"primary_opponent_character_id",new IntegerValue(BigInteger.valueOf(opponent)))))));
        return Optional.of(new Obj(fields));
    }
    private static Value optional(Obj row,String field){Value value=row.get(field);return value==null?Nil.INSTANCE:value;}
}
