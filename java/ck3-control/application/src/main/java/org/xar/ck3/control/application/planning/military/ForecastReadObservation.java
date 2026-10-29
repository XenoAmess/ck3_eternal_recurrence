package org.xar.ck3.control.application.planning.military;

import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;

/** Validated read values cross into Driver publication without an application -> native module dependency. */
public sealed interface ForecastReadObservation permits ForecastReadObservation.CombatInputs,
        ForecastReadObservation.WarEntry,ForecastReadObservation.CurrentKnight,ForecastReadObservation.PhaseTrace {
    enum Kind { COMBAT_V2,COMBAT_V3,WAR_ENTRY,CURRENT_KNIGHT,PHASE_TRACE }
    Kind kind();
    Obj normalizedResult();
    record RequestedEffectiveTarget(int requested,int effective) {
        public RequestedEffectiveTarget {org.xar.ck3.control.planning.opportunity.OpportunityJson.require(requested>0&&effective>0,"positive requested/effective CharacterID required");}
    }
    record CombatInputs(CombatObservationCache.Observation observation,Obj normalizedResult) implements ForecastReadObservation {
        public CombatInputs {Objects.requireNonNull(observation);Objects.requireNonNull(normalizedResult);}
        @Override public Kind kind(){return observation.version()==CombatObservationCache.Version.V2?Kind.COMBAT_V2:Kind.COMBAT_V3;}
        @Override public boolean equals(Object other){return other instanceof CombatInputs value&&kind()==value.kind()&&normalizedResult.equals(value.normalizedResult)&&observation.frame().equals(value.observation.frame())
                &&observation.request().equals(value.observation.request())&&observation.scope().equals(value.observation.scope())&&observation.toInternalJson().equals(value.observation.toInternalJson());}
        @Override public int hashCode(){return Objects.hash(kind(),normalizedResult,observation.frame(),observation.request(),observation.scope(),observation.toInternalJson());}
    }
    record WarEntry(Obj assessments,Arr targetScopes,Obj normalizedResult) implements ForecastReadObservation {
        public WarEntry {Objects.requireNonNull(assessments);Objects.requireNonNull(targetScopes);Objects.requireNonNull(normalizedResult);}
        @Override public Kind kind(){return Kind.WAR_ENTRY;}
        /** Exact normalized source values only; this getter adds no freshness or query authority. */
        public RequestedEffectiveTarget singleTarget() {
            var requested=org.xar.ck3.control.planning.opportunity.OpportunityJson.array(assessments.get("requested_target_character_ids"),"requested war-entry targets");
            var rows=org.xar.ck3.control.planning.opportunity.OpportunityJson.array(assessments.get("assessments"),"normalized war-entry assessments");
            org.xar.ck3.control.planning.opportunity.OpportunityJson.require(requested.size()==1&&rows.size()==1,"single complete war-entry target required");
            var row=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(rows.getFirst(),"assessment");
            int target=org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(requested.getFirst(),"requested target").intValueExact();
            org.xar.ck3.control.planning.opportunity.OpportunityJson.require(new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(target)).equals(row.get("target_character_id")),"assessment differs from requested target");
            return new RequestedEffectiveTarget(target,org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(row.get("effective_target_character_id"),"effective target").intValueExact());
        }
    }
    record CurrentKnight(Obj knight,Obj normalizedResult) implements ForecastReadObservation {
        public CurrentKnight {Objects.requireNonNull(knight);Objects.requireNonNull(normalizedResult);}
        @Override public Kind kind(){return Kind.CURRENT_KNIGHT;}
    }
    record PhaseTrace(Obj trace,Obj normalizedResult) implements ForecastReadObservation {
        public PhaseTrace {Objects.requireNonNull(trace);Objects.requireNonNull(normalizedResult);}
        @Override public Kind kind(){return Kind.PHASE_TRACE;}
    }
}
