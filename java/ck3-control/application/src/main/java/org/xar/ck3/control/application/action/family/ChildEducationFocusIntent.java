package org.xar.ck3.control.application.action.family;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Desired child/focus only. A retained planner query never authorizes native legality or submission. */
public record ChildEducationFocusIntent(long childFullId, FocusKey target, Optional<Obj> planningProof) {
    public static final String SCHEMA="xar.java.child-education-focus-intent/v1";
    public static final String STEP="private-select-child-education-focus-v1";
    public static final String OBSERVER_SCHEMA="xar.java.family-action-observation/v1";
    public enum FocusKey {
        EDUCATION_DIPLOMACY, EDUCATION_MARTIAL, EDUCATION_STEWARDSHIP, EDUCATION_INTRIGUE, EDUCATION_LEARNING;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        public static FocusKey fromWire(String value) {
            StrictJson.text(value);
            for(var key:values())if(key.wire().equals(value))return key;
            throw new IllegalArgumentException("unknown exact child education focus key");
        }
    }
    public ChildEducationFocusIntent {
        StrictJson.require(childFullId>0&&childFullId<0xFFFF_FFFFL,"full native child identity required");
        Objects.requireNonNull(target);Objects.requireNonNull(planningProof);
    }
    public Obj toJson() {
        var n=StrictJson.object().put("schema",SCHEMA).put("child_full_id",childFullId).put("target_key",target.wire());
        if(planningProof.isPresent())n.set("planning_proof",DriverJson.toNode(planningProof.orElseThrow()));else n.putNull("planning_proof");
        return DriverJson.object(StrictJson.canonical(n),DriverJson.MAX_NATIVE_BYTES);
    }
    public static ChildEducationFocusIntent fromJson(Obj original) {
        JsonNode n=DriverJson.toNode(original);StrictJson.object(n,Set.of("schema","child_full_id","target_key","planning_proof"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))),"canonical child focus intent schema required");
        var proof=n.get("planning_proof");
        Optional<Obj> retained=proof.isNull()?Optional.empty():Optional.of(DriverJson.object(StrictJson.canonical(proof),DriverJson.MAX_NATIVE_BYTES));
        return new ChildEducationFocusIntent(StrictJson.integer(n.get("child_full_id"),1,0xFFFF_FFFEL),
                FocusKey.fromWire(StrictJson.text(n.get("target_key"))),retained);
    }
    public ExpectedPostcondition expected(ObservationIdentity before,G2Source source) {
        return new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,before,source,OBSERVER_SCHEMA,values());
    }
    public List<ExpectedValue> values() {
        return List.of(new ExpectedInteger(new FieldKey("child_full_id"),BigInteger.valueOf(childFullId)),
                new ExpectedText(new FieldKey("focus_key"),target.wire()),new ExpectedBoolean(new FieldKey("focus_present"),true));
    }
}
