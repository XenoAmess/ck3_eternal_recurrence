package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.CompositeContinuationReport;
import org.xar.ck3.control.application.action.CompositeContinuationToken;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Report DATA only: canonical child attempts are not physical writes, effects, or replay permission. */
public final class SuccessorUiContinuationJson {
    public static final String SCHEMA="xar.ck3.java-successor-ui-continuation/v1";
    private SuccessorUiContinuationJson() { }
    public static ObjectNode encode(BatchReport.SuccessorUiContinuation actual) {
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA).put("kind",actual.kind().name())
                .put("disposition",actual.actual().disposition().name()).put("new_parent_submitted",false);
        row.put("original_parent_action_id",actual.actual().parent().command().actionId())
                .put("original_parent_body_sha256",actual.actual().parent().bodySha256());
        row.set("canonical_domain",actual.canonicalDomain().toJson());
        row.set("actual_published_driver",actual.actualPublishedDriver().toJson());
        row.set("canonical_publication_proof",actual.canonicalPublicationProof().toJson());
        var children=row.putArray("new_child_attempts");
        for(ActionReceipt child:actual.actual().children()) {
            children.addObject().put("action_id",child.command().actionId()).put("body_sha256",child.bodySha256())
                    .put("operation",child.command().operation().value()).put("outcome",child.outcome().name())
                    .put("writer_sequence",Long.toString(child.sequence()));
        }
        validate(row);return row;
    }
    public static void validate(JsonNode value) {
        StrictJson.require(value!=null&&value.isObject(),"actual successor UI report object required");
        var fields=Set.of("schema","kind","disposition","new_parent_submitted","original_parent_action_id",
                "original_parent_body_sha256","canonical_domain","actual_published_driver","canonical_publication_proof","new_child_attempts");
        StrictJson.require(value.size()==fields.size(),"closed successor UI report fields required");
        value.fieldNames().forEachRemaining(key->StrictJson.require(fields.contains(key),"unknown successor UI report field"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))),"successor UI report schema required");
        var kind=CompositeContinuationToken.Kind.valueOf(StrictJson.text(value.get("kind")));
        StrictJson.require(kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE||kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT||kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE,
                "finite successor UI continuation kind required");
        var disposition=CompositeContinuationReport.Disposition.valueOf(StrictJson.text(value.get("disposition")));
        StrictJson.require(value.get("new_parent_submitted").isBoolean()&&!value.get("new_parent_submitted").booleanValue(),
                "a continuation cannot report a replacement parent submission");
        actionId(value.get("original_parent_action_id"));digest(value.get("original_parent_body_sha256"));
        for(String field:java.util.List.of("canonical_domain","actual_published_driver","canonical_publication_proof"))
            StrictJson.require(ExactRef.fromJson(value.get(field)).bytes()>0,"actual canonical continuation source required");
        JsonNode children=value.get("new_child_attempts");StrictJson.require(children.isArray(),"actual child attempt array required");
        StrictJson.require((disposition==CompositeContinuationReport.Disposition.NEW_CHILD_ATTEMPT)==!children.isEmpty(),
                "continuation disposition differs from actual new child attempts");
        var ids=new HashSet<String>();var childFields=Set.of("action_id","body_sha256","operation","outcome","writer_sequence");
        for(JsonNode child:children) {
            StrictJson.require(child.isObject()&&child.size()==childFields.size(),"closed actual child attempt fields required");
            child.fieldNames().forEachRemaining(key->StrictJson.require(childFields.contains(key),"unknown actual child attempt field"));
            actionId(child.get("action_id"));StrictJson.require(ids.add(StrictJson.text(child.get("action_id"))),"duplicate actual child attempt");
            StrictJson.require(!child.get("action_id").equals(value.get("original_parent_action_id")),"parent is not a new child attempt");
            digest(child.get("body_sha256"));StrictJson.text(child.get("operation"));ActionReceipt.Outcome.valueOf(StrictJson.text(child.get("outcome")));
            String sequence=StrictJson.text(child.get("writer_sequence"));
            StrictJson.require(sequence.matches("[1-9][0-9]{0,15}")&&new java.math.BigInteger(sequence).compareTo(java.math.BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,
                    "actual receipt sequence must be a canonical positive safe-integer string");
        }
    }
    private static void actionId(JsonNode value) {StrictJson.require(StrictJson.text(value).matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),"actual action ID required");}
    private static void digest(JsonNode value) {StrictJson.require(StrictJson.text(value).matches("[0-9a-f]{64}"),"actual action body digest required");}
}
