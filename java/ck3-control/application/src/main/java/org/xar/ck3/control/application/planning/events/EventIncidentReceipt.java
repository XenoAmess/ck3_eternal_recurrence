package org.xar.ck3.control.application.planning.events;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Optional;
import java.util.Base64;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedPopulistReceipt;

/** Adapter for the original post-capture service comparison, shared by live Journal and original-index replay. */
public final class EventIncidentReceipt {
    private static final String PHASE="active_event_source_reviewed_populist_refusal";
    private static final String SCHEMA="xar.java-event-policy-receipt-input/v1";
    private static final int MAXIMUM_BYTES=1 << 20;
    private EventIncidentReceipt() { }

    /** Called after an independently observed effect and its actual after body exist. It grants no result credit. */
    public static Optional<RawJson> prepare(OpportunityJson.Obj originalPlan, RawJson originalCompatible,
            ExactRef actualBefore, ExactRef actualAfter, RawJson actualAfterBody) {
        Objects.requireNonNull(originalPlan);Objects.requireNonNull(originalCompatible);Objects.requireNonNull(actualBefore);
        Objects.requireNonNull(actualAfter);Objects.requireNonNull(actualAfterBody);
        if(!new OpportunityJson.Text(PHASE).equals(originalPlan.get("phase")))return Optional.empty();
        ObjectNode plan=object(new RawJson(DriverJson.encode(originalPlan))),result=object(originalCompatible),after=object(actualAfterBody);
        // These service-envelope fields state the already observed operation. ACK acceptance remains
        // exclusively in the unmodified original compatible result, including an absent ACK for UNKNOWN.
        ObjectNode body=StrictJson.object().put("status","executed");body.set("selected_step",plan.get("selected_step"));
        body.set("plan",plan);body.set("result",result);
        ObjectNode evidence=body.putObject("unhandled_event_fallback_evidence");
        for(String field:java.util.List.of("incident_id","command_acknowledged","event_instance_advanced_verified","replay_allowed"))
            evidence.set(field,after.get(field));
        evidence.set("before",actualBefore.toJson());evidence.set("after",actualAfter.toJson());
        ObjectNode wrapper=StrictJson.object().put("schema",SourceReviewedPopulistReceipt.SCHEMA);wrapper.set("body",body);
        return Optional.of(encode(new PreparedInput(new RawJson(DriverJson.encode(originalPlan)),new RawJson(StrictJson.canonical(wrapper,MAXIMUM_BYTES)))));
    }
    /** Replays exactly the stored shared comparator input against the original command hash and incident pins. */
    public static Optional<RetainedJson.ObjectValue> verify(RawJson serialized, String originalArgumentsSha256,
            ExactRef actualBefore, ExactRef actualAfter, RawJson actualBeforeBody, RawJson actualAfterBody) {
        Objects.requireNonNull(serialized);StrictJson.text(originalArgumentsSha256);Objects.requireNonNull(actualBefore);
        Objects.requireNonNull(actualAfter);Objects.requireNonNull(actualBeforeBody);Objects.requireNonNull(actualAfterBody);
        PreparedInput prepared=decode(serialized);ObjectNode wrapper=object(prepared.legacyInput()),body=object(wrapper.get("body"));
        var plan=DriverJson.object(StrictJson.canonical(body.get("plan"),MAXIMUM_BYTES),MAXIMUM_BYTES);
        StrictJson.require(DriverJson.sha256(prepared.originalArguments().bytes()).equals(originalArgumentsSha256)
            &&DriverJson.object(prepared.originalArguments().bytes(),MAXIMUM_BYTES).equals(plan),"policy receipt changed original command arguments");
        ObjectNode evidence=object(body.get("unhandled_event_fallback_evidence")),after=object(actualAfterBody);
        ObjectNode before=object(actualBeforeBody),capture=object(body.path("plan").get("unhandled_event_fallback"));
        capture.properties().forEach(field->StrictJson.require(Objects.equals(field.getValue(),before.get(field.getKey())),"policy receipt changed captured before field "+field.getKey()));
        StrictJson.require(actualBefore.equals(ExactRef.fromJson(evidence.get("before")))&&actualAfter.equals(ExactRef.fromJson(evidence.get("after"))),"policy receipt changed original incident pins");
        for(String field:java.util.List.of("incident_id","command_acknowledged","event_instance_advanced_verified","replay_allowed"))
            StrictJson.require(Objects.equals(evidence.get(field),after.get(field)),"policy receipt changed original after assessment "+field);
        StrictJson.require(Objects.equals(body.path("result").get("event_selection"),after.get("event_selection")),"policy receipt changed original native selection");
        StrictJson.require(DriverJson.sha256(actualAfterBody.bytes()).equals(actualAfter.sha256())&&actualAfterBody.bytes().length==actualAfter.bytes(),"policy receipt actual after bytes changed");
        StrictJson.require(DriverJson.sha256(actualBeforeBody.bytes()).equals(actualBefore.sha256())&&actualBeforeBody.bytes().length==actualBefore.bytes(),"policy receipt actual before bytes changed");
        // The original Python service comparison is an ACK-specific receipt classifier. Java can
        // independently settle a lost-reply action; absence of its ACK supplies no legacy receipt
        // credit and must not erase that separately proven effect or ask to repeat the option.
        if(!body.path("result").has("accepted"))return Optional.empty();
        return SourceReviewedPopulistReceipt.verify(SourceReviewedPopulistReceipt.decode(prepared.legacyInput().bytes()));
    }
    private record PreparedInput(RawJson originalArguments,RawJson legacyInput) {
        private PreparedInput {Objects.requireNonNull(originalArguments);Objects.requireNonNull(legacyInput);}
    }
    private static RawJson encode(PreparedInput input) {
        ObjectNode envelope=StrictJson.object().put("schema",SCHEMA).put("original_arguments_base64",Base64.getEncoder().encodeToString(input.originalArguments().bytes()));
        envelope.set("legacy_input",object(input.legacyInput()));return new RawJson(StrictJson.canonical(envelope,MAXIMUM_BYTES));
    }
    private static PreparedInput decode(RawJson serialized) {
        ObjectNode envelope=StrictJson.object(object(serialized),Set.of("schema","original_arguments_base64","legacy_input"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(envelope.get("schema"))),"versioned policy receipt input required");
        String token=StrictJson.text(envelope.get("original_arguments_base64"));byte[] original=Base64.getDecoder().decode(token);
        StrictJson.require(original.length>0&&original.length<=MAXIMUM_BYTES&&Base64.getEncoder().encodeToString(original).equals(token),"canonical bounded original arguments encoding required");
        return new PreparedInput(new RawJson(original),new RawJson(StrictJson.canonical(envelope.get("legacy_input"),MAXIMUM_BYTES)));
    }
    private static ObjectNode object(RawJson raw) { return object(StrictJson.parse(raw.bytes(),MAXIMUM_BYTES)); }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode,"actual receipt object required");return (ObjectNode)node; }
}
