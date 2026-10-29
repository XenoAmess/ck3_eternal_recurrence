package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m5.M5Research.ExistingWarPlan;
import org.xar.ck3.control.g2.m5.M5Research.MissingPlan;
import org.xar.ck3.control.g2.m5.M5Research.ObservedPlan;
import org.xar.ck3.control.g2.m5.M5Research.Result;

/** Adds complete published participant facts to the existing reason scope without changing a decision. */
public final class M5DecisionConsumer {
    private static final String REASON_SCOPE = "war_decision_reason_scope_v1";
    public enum OriginalScopePresence { PLAN_MISSING, PLAN_NULL, SCOPE_MISSING, SCOPE_NULL, OBSERVED }
    public record Consumption(ExistingWarPlan annotatedPlan, OriginalScopePresence originalScopePresence,
                              Obj reasonScope) {
        public Consumption {
            Objects.requireNonNull(annotatedPlan); Objects.requireNonNull(originalScopePresence);
            Objects.requireNonNull(reasonScope);
        }
        public boolean actionAuthorized() { return false; }
    }

    private M5DecisionConsumer() { }

    public static Consumption consume(byte[] savedResult) {
        return consume(M5PayloadCodec.decodeResult(savedResult));
    }

    public static Consumption consume(Result result) {
        M5PayloadCodec.validateResult(result);
        ExistingWarPlan original = result.existingWarPlan();
        OriginalScopePresence presence;
        Map<String, Value> fields = new LinkedHashMap<>();
        if (original instanceof ObservedPlan observed) {
            Value previous = observed.plan().get(REASON_SCOPE);
            if (!observed.plan().members().containsKey(REASON_SCOPE)) presence = OriginalScopePresence.SCOPE_MISSING;
            else if (previous == Nil.INSTANCE) presence = OriginalScopePresence.SCOPE_NULL;
            else {
                fields.putAll(object(previous, "original ordinary war reason scope").members());
                presence = OriginalScopePresence.OBSERVED;
            }
        } else presence = original instanceof MissingPlan ? OriginalScopePresence.PLAN_MISSING : OriginalScopePresence.PLAN_NULL;
        // Retain every existing cash-priority/primary-union field. In particular,
        // qualified nonleading siege cash protection is not narrowed to primary wars.
        fields.put("participating_war_threat_observation_v1", M5PayloadCodec.participatingWars(result.participatingWars()));
        fields.put("existing_cash_priority_source_binding", new Text("not_established_by_payload"));
        fields.put("participant_threats_source_binding", new Text("original_intake_frame"));
        fields.put("nonparticipant_liege_wars_assessment", new Text("unassessed"));
        fields.put("territorial_consequences_verified", new Bool(false));
        Obj scope = new Obj(fields);
        ExistingWarPlan annotated = original instanceof ObservedPlan observed
                ? new ObservedPlan(observed.plan().with(REASON_SCOPE, scope)) : original;
        return new Consumption(annotated, presence, scope);
    }

    static Obj toJson(Consumption consumption) {
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("original_reason_scope_presence", new Text(consumption.originalScopePresence().name()));
        fields.put("reason_scope_field", new Text(REASON_SCOPE));
        fields.put("participant_observation_source_field", new Text("participating_wars"));
        fields.put("updated_reason_scope_fields", new Arr(List.of(
                new Text("participating_war_threat_observation_v1"), new Text("existing_cash_priority_source_binding"),
                new Text("participant_threats_source_binding"), new Text("nonparticipant_liege_wars_assessment"),
                new Text("territorial_consequences_verified"))));
        fields.put("selected_step_changed", new Bool(false));
        fields.put("cash_priority_changed", new Bool(false));
        fields.put("candidate_ranking_changed", new Bool(false));
        fields.put("action_authorized", new Bool(consumption.actionAuthorized()));
        return new Obj(fields);
    }
}
