package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Dedicated state DATA codec. No legacy Attempt/Guard/SUBMITTING can be created
 * from this envelope; admission and complete originals belong to the actual
 * installed prepared-cleanup replay, never to this public constructor. */
public final class PreparedCleanupActionCodec {
    public static final String SCHEMA="xar.java.prepared-cleanup-action-receipt/v1";
    private PreparedCleanupActionCodec(){}
    static ObjectNode encode(PreparedCleanupAction state,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object();row.put("kind","PREPARED_CLEANUP");row.put("phase",state.phase().name());
        row.set("preparation_ref",state.preparationReference().toJson());
        row.set("late_ref",ref(state.lateBindingReference()));
        row.set("dispatch_ref",state.originalDispatch().map(value->(JsonNode)archive.referenceOf(value).toJson()).orElse(NullNode.instance));
        row.set("captured_ref",ref(state.capturedPostAcknowledgement()));row.set("failure_ref",ref(state.failureReference()));return row;
    }
    static PreparedCleanupAction decode(JsonNode node,ActionPorts.OutcomeArchive archive){
        var row=StrictJson.object(node,Set.of("kind","phase","preparation_ref","late_ref","dispatch_ref","captured_ref","failure_ref"));
        StrictJson.require(row.path("kind").asText().equals("PREPARED_CLEANUP"),"exact prepared cleanup state kind required");
        return new PreparedCleanupAction(PreparedCleanupAction.Phase.valueOf(StrictJson.text(row.path("phase").asText())),
                ExactRef.fromJson(row.get("preparation_ref")),optional(row.get("late_ref")),
                row.get("dispatch_ref").isNull()?Optional.empty():Optional.of(archive.load(ExactRef.fromJson(row.get("dispatch_ref")))),
                optional(row.get("captured_ref")),optional(row.get("failure_ref")));
    }
    private static JsonNode ref(Optional<ExactRef> value){return value.map(item->(JsonNode)item.toJson()).orElse(NullNode.instance);}
    private static Optional<ExactRef> optional(JsonNode value){return value.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(value));}
    public static java.util.List<ExactRef> references(PreparedCleanupAction state,ActionPorts.OutcomeArchive archive){
        var result=new java.util.ArrayList<ExactRef>();result.add(state.preparationReference());state.lateBindingReference().ifPresent(result::add);
        state.originalDispatch().ifPresent(value->result.add(archive.referenceOf(value)));
        state.capturedPostAcknowledgement().ifPresent(result::add);state.failureReference().ifPresent(result::add);return java.util.List.copyOf(result);
    }
    static boolean follows(PreparedCleanupAction before,PreparedCleanupAction after){
        if(before.terminal()||!before.preparationReference().equals(after.preparationReference()))return false;
        if(before.originalDispatch().isPresent()&&!before.originalDispatch().equals(after.originalDispatch()))return false;
        if(before.lateBindingReference().isPresent()&&!before.lateBindingReference().equals(after.lateBindingReference()))return false;
        return before.phase()==PreparedCleanupAction.Phase.PREPARED
                ?after.phase()!=PreparedCleanupAction.Phase.PREPARED
                :before.phase()==PreparedCleanupAction.Phase.UNKNOWN
                    &&(after.phase()==PreparedCleanupAction.Phase.UNKNOWN||after.phase()==PreparedCleanupAction.Phase.CONFIRMED);
    }
}
