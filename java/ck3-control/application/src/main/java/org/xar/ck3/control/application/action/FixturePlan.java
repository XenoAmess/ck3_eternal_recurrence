package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Source-bound fixture DATA. Only the installed composite and its canonical child scope grant custody. */
public record FixturePlan(Kind kind, ExactRef policySource, ExactRef claim, ExactRef producerSource) {
    public static final String SCHEMA="xar.java.fixture-plan/v1";
    public static final String PARENT_SCHEMA="xar.java.fixture-business-observation/v1";
    public enum Kind {
        ROBERT("start-fixture-robert-business-v1","activate-frontend-start-selected-bookmark-v1"),
        SCENARIO("start-fixture-scenario-business-v1","activate-frontend-start-selected-bookmark-faith-e01-v1");
        private final OperationKey parent, start;
        Kind(String parent,String start){this.parent=new OperationKey(parent);this.start=new OperationKey(start);}
        public OperationKey parentOperation(){return parent;}
        public OperationKey startOperation(){return start;}
    }
    public FixturePlan {
        Objects.requireNonNull(kind);Objects.requireNonNull(policySource);Objects.requireNonNull(claim);Objects.requireNonNull(producerSource);
        StrictJson.require(policySource.bytes()>0&&claim.bytes()>0&&producerSource.bytes()>0,"fixture needs actual policy, exclusive claim and installed producer sources");
    }
    public ObjectNode encode(){
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("kind",kind.name());
        row.set("policy_source",policySource.toJson());row.set("claim",claim.toJson());row.set("producer_source",producerSource.toJson());return row;
    }
    public static FixturePlan decode(JsonNode input){
        ObjectNode row=StrictJson.object(input,Set.of("schema","kind","policy_source","claim","producer_source"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact fixture plan schema required");
        return new FixturePlan(Kind.valueOf(StrictJson.text(row.get("kind"))),ExactRef.fromJson(row.get("policy_source")),
                ExactRef.fromJson(row.get("claim")),ExactRef.fromJson(row.get("producer_source")));
    }
    public static boolean isParent(ActionCommand command){
        return java.util.Arrays.stream(Kind.values()).anyMatch(kind->kind.parentOperation().equals(command.operation()));
    }
    public static FixturePlan requireParent(ActionCommand command){
        StrictJson.require(command.origin() instanceof CommandOrigin.Frontend&&isParent(command),"exact upfront frontend fixture parent required");
        FixturePlan plan=decode(DriverJson.toNode(command.arguments()));
        StrictJson.require(plan.kind.parentOperation().equals(command.operation())
                &&command.expectation() instanceof CommandExpectation.Frontend
                &&command.expectation().requireFrontend().before().equals(command.origin().requireFrontend())
                &&command.expectation().requireFrontend().source().equals(command.source())
                &&plan.expected(command.origin().requireFrontend(),command.source()).equals(command.expectation().requireFrontend()),"fixture parent changed its exact branch, origin, source or expectation");
        return plan;
    }
    public FrontendExpectedPostcondition expected(FrontendIdentity before,G2Source source){
        return new FrontendExpectedPostcondition(before,source,PARENT_SCHEMA,java.util.List.of(
                new ExpectedText(new FieldKey("fixture_kind"),kind.name()),new ExpectedText(new FieldKey("status"),"fixture_business_verified"),
                new ExpectedBoolean(new FieldKey("postcondition_verified"),true)));
    }
    public FrontendExpectedPostcondition expectedStart(FrontendIdentity before,G2Source source){
        return new FrontendExpectedPostcondition(before,source,FixtureStartObservation.SCHEMA,java.util.List.of(
                new ExpectedText(new FieldKey("status"),"independent_first_map_observed"),new ExpectedBoolean(new FieldKey("postcondition_verified"),true)));
    }
    public void requireStart(ActionCommand command){
        StrictJson.require(command.origin() instanceof CommandOrigin.Frontend&&kind.startOperation().equals(command.operation()),"fixture Start changed its prepared branch");
        var arguments=DriverJson.toNode(command.arguments());
        StrictJson.require(policySource.equals(ExactRef.fromJson(arguments.get("policy_source")))
                &&claim.equals(ExactRef.fromJson(arguments.get("claim"))),"fixture Start changed its original policy or exclusive claim");
    }
}
