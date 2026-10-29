package org.xar.ck3.control.application.action.ordinary;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.require;

/** The exact pair selected by planning; fresh native terms belong to preparation. */
public record RulerMarriageIntent(String choiceId, long actorId, long candidateId, Optional<Obj> planningProof) {
    public static final String SCHEMA = "xar.ck3.ruler-marriage-intent/v1";
    public RulerMarriageIntent {
        character(actorId); character(candidateId);
        require(actorId != candidateId && (actorId + "-" + candidateId).equals(choiceId), "exact canonical ruler marriage pair");
        planningProof = Objects.requireNonNull(planningProof);
    }
    public String step() { return "arrange-marriage-" + choiceId; }
    public Obj toJson() {
        return new Obj(Map.of("schema", new Text(SCHEMA), "choice_id", new Text(choiceId), "actor_id", number(actorId),
                "candidate_id", number(candidateId), "planning_proof", planningProof.<Value>map(value -> value).orElse(Nil.INSTANCE)));
    }
    public static RulerMarriageIntent fromJson(Obj value) {
        require(value.members().keySet().equals(Set.of("schema", "choice_id", "actor_id", "candidate_id", "planning_proof")), "closed ruler marriage intent fields");
        require(SCHEMA.equals(OpportunityJson.text(value.get("schema"), "schema")), "ruler marriage intent version");
        return new RulerMarriageIntent(OpportunityJson.text(value.get("choice_id"), "choice_id"), id(value.get("actor_id")), id(value.get("candidate_id")),
                value.get("planning_proof") == Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.object(value.get("planning_proof"), "planning_proof")));
    }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static long id(Value value) { long id = OpportunityJson.integer(value, "full Character ID").longValueExact(); character(id); return id; }
    private static void character(long value) { require(value > 0 && value <= 0xffff_fffeL, "complete generation-bearing uint32 Character ID"); }
}
