package org.xar.ck3.control.application.action.family;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Selected pair and requested option only. Planning proof never authorizes fresh native terms or a retry. */
public record FamilyMarriageIntent(Route route,long actorId,int subjectId,int candidateId,int recipientId,
        boolean matrilineal,List<Integer> comparisonCandidateIds,Optional<Obj> planningProof) {
    public static final String SCHEMA="xar.ck3.family-marriage-intent/v1";
    public enum Route {
        FIRST_HEIR("first_heir","submit-observed-first-heir-marriage-v1-private"),
        FULFILL_BETROTHAL("fulfill_betrothal","submit-current-first-heir-betrothal-fulfillment-v1-private"),
        CHILD_MATRILINEAL("child_matrilineal","submit-player-child-matrilineal-marriage-v1-private"),
        CHILD_DEFAULT("child_default","submit-player-child-default-marriage-v1-private");
        private final String wire,step;
        Route(String wire,String step){this.wire=wire;this.step=step;}
        public String wire(){return wire;}public String step(){return step;}
        public static Route fromWire(String wire){for(Route value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("unknown family marriage intent route");}
    }
    public FamilyMarriageIntent {
        Objects.requireNonNull(route);Objects.requireNonNull(planningProof);comparisonCandidateIds=List.copyOf(comparisonCandidateIds);
        StrictJson.require(actorId>0 && actorId<0xFFFF_FFFFL && subjectId>0 && candidateId>0 && recipientId>0 && subjectId!=candidateId && actorId!=subjectId,
                "private family intent requires the full uint32 actor and distinct native positive int32 pair roles");
        if(route==Route.FIRST_HEIR)StrictJson.require(comparisonCandidateIds.size()==5
                && new HashSet<>(comparisonCandidateIds).size()==5 && comparisonCandidateIds.stream().allMatch(id->id>0)
                && comparisonCandidateIds.contains(candidateId),"first-heir intent must retain the exact five comparison IDs and selected candidate");
        else StrictJson.require(comparisonCandidateIds.isEmpty(),"only the first-heir five-row route carries comparison IDs");
        if(route==Route.CHILD_MATRILINEAL)StrictJson.require(matrilineal,"matrilineal child intent must select the native option");
        if(route==Route.CHILD_DEFAULT)StrictJson.require(!matrilineal,"default child intent cannot select the matrilineal option");
    }
    public String step(){return route.step();}
    public Obj toJson() {
        var n=StrictJson.object().put("schema",SCHEMA).put("route",route.wire()).put("actor_id",actorId).put("subject_id",subjectId)
                .put("candidate_id",candidateId).put("recipient_id",recipientId).put("matrilineal",matrilineal);
        var ids=n.putArray("comparison_candidate_ids");comparisonCandidateIds.forEach(ids::add);
        if(planningProof.isPresent())n.set("planning_proof",DriverJson.toNode(planningProof.orElseThrow()));else n.putNull("planning_proof");
        return DriverJson.object(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
    }
    public static FamilyMarriageIntent fromJson(Obj value) {
        JsonNode n=DriverJson.toNode(value);StrictJson.object(n,Set.of("schema","route","actor_id","subject_id","candidate_id","recipient_id","matrilineal","comparison_candidate_ids","planning_proof"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))),"family marriage intent schema differs");
        JsonNode ids=n.get("comparison_candidate_ids");StrictJson.require(ids.isArray() && ids.size()<=5,"bounded explicit comparison array required");
        List<Integer> comparisons=new ArrayList<>();for(JsonNode id:ids)comparisons.add((int)StrictJson.integer(id,1,Integer.MAX_VALUE));
        JsonNode proof=n.get("planning_proof");Optional<Obj> retained=proof.isNull()?Optional.empty():Optional.of(
                DriverJson.object(proof.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES));
        JsonNode matrilineal=n.get("matrilineal");
        StrictJson.require(matrilineal!=null && matrilineal.isBoolean(),"actual JSON boolean required for matrilineal");
        return new FamilyMarriageIntent(Route.fromWire(StrictJson.text(n.get("route"))),StrictJson.integer(n.get("actor_id"),1,0xFFFF_FFFEL),id(n,"subject_id"),id(n,"candidate_id"),id(n,"recipient_id"),
                matrilineal.booleanValue(),comparisons,retained);
    }
    private static int id(JsonNode n,String key){return (int)StrictJson.integer(n.get(key),1,Integer.MAX_VALUE);}
}
