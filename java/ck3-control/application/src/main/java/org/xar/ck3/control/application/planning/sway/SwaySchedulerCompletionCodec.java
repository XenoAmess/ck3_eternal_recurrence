package org.xar.ck3.control.application.planning.sway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict wire DATA decoder; neither decoding nor constructor validation grants canonical credit. */
public final class SwaySchedulerCompletionCodec {
    public static final String SCHEMA = "xar.java.sway-scheduler-completion/v1";
    public static final int MAX_BYTES = 524288;
    private SwaySchedulerCompletionCodec() { }
    public static byte[] encode(SwaySchedulerCompletion value) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("parent_action_id", value.parentActionId()); row.put("body_sha256", value.bodySha256()); row.set("original_run", value.originalRun().toJson());
        var witness = row.putObject("publication"); witness.set("event", value.witness().event().toJson()); witness.set("predecessor", value.witness().predecessor().toJson()); witness.set("result", value.witness().result().toJson()); witness.set("producer_input", value.witness().producerInput().toJson()); witness.put("sequence", value.witness().sequence()); witness.put("event_identity", value.witness().eventIdentity()); witness.put("previous_head_sha", value.witness().previousHeadSha());
        var frame = row.putObject("final_frame"); frame.set("native_frame", value.finalFrame().nativeFrame().toJson()); frame.set("driver_facts", value.finalFrame().driverFacts().toJson());
        var reads = row.putArray("final_reads"); value.finalReads().forEach(ref -> reads.add(ref.toJson())); var children = row.putArray("child_receipts"); value.childReceiptRefs().forEach(ref -> children.add(ref.toJson()));
        if (value.exactContinuation().isPresent()) row.set("exact_continuation", SwayFormalCodec.chunks(ActionCodec.encodeCommand(value.exactContinuation().orElseThrow()))); else row.putNull("exact_continuation");
        if (value.fullPlanOriginals().isPresent()) { var full = row.putObject("fullplan_originals"); full.set("request", value.fullPlanOriginals().orElseThrow().request().toJson()); full.set("result", value.fullPlanOriginals().orElseThrow().result().toJson()); } else row.putNull("fullplan_originals");
        row.put("continuation", value.continuation().name());
        var business = row.putObject("business"); if (value.business() instanceof SwaySchedulerCompletion.NewStartConfirmed start) { business.put("kind", "new_start_confirmed"); business.put("child_action_id", start.childActionId()); business.put("child_body_sha256", start.childBodySha256()); } else business.put("kind", "no_new_business");
        return StrictJson.canonical(row, MAX_BYTES);
    }
    public static SwaySchedulerCompletion decodeRecorded(byte[] raw) {
        JsonNode row = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "parent_action_id", "body_sha256", "original_run", "publication", "final_frame", "final_reads", "child_receipts", "exact_continuation", "fullplan_originals", "continuation", "business")); SwayNativeWire.equals(row, "schema", SCHEMA);
        JsonNode publication = StrictJson.object(row.get("publication"), Set.of("event", "predecessor", "result", "producer_input", "sequence", "event_identity", "previous_head_sha"));
        var witness = new SwayCanonicalDomain.PublicationWitness(ExactRef.fromJson(publication.get("event")), DomainBodies.BodyRef.fromJson(publication.get("predecessor")), DomainBodies.BodyRef.fromJson(publication.get("result")), ExactRef.fromJson(publication.get("producer_input")), StrictJson.integer(publication.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER), text(publication, "event_identity"), text(publication, "previous_head_sha"));
        JsonNode frame = StrictJson.object(row.get("final_frame"), Set.of("native_frame", "driver_facts"));
        JsonNode business = row.get("business"); SwaySchedulerCompletion.Business classified = switch(text(business, "kind")) {
            case "no_new_business" -> { StrictJson.object(business, Set.of("kind")); yield new SwaySchedulerCompletion.NoNewBusiness(); }
            case "new_start_confirmed" -> { StrictJson.object(business, Set.of("kind", "child_action_id", "child_body_sha256")); yield new SwaySchedulerCompletion.NewStartConfirmed(text(business, "child_action_id"), text(business, "child_body_sha256")); }
            default -> throw new IllegalArgumentException("unknown recorded Sway business branch");
        };
        return new SwaySchedulerCompletion(text(row, "parent_action_id"), text(row, "body_sha256"), ExactRef.fromJson(row.get("original_run")), witness, new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(frame.get("native_frame")), ExactRef.fromJson(frame.get("driver_facts"))), refs(row.get("final_reads"), 4), refs(row.get("child_receipts"), 1), SwayFormalCodec.optional(row.get("exact_continuation")).map(value -> ActionCodec.decodeCommand(SwayFormalCodec.bytes(value))), SwayFormalCodec.optional(row.get("fullplan_originals")).map(value -> { StrictJson.object(value, Set.of("request", "result")); return new SwaySchedulerCompletion.FullPlanOriginals(ExactRef.fromJson(value.get("request")), ExactRef.fromJson(value.get("result"))); }), SwaySchedulerCompletion.Continuation.valueOf(text(row, "continuation")), classified);
    }
    private static String text(JsonNode row, String key) { return StrictJson.text(row.get(key)); }
    private static List<ExactRef> refs(JsonNode values, int maximum) { StrictJson.require(values != null && values.isArray() && values.size() <= maximum, "bounded exact reference list required"); var refs = new ArrayList<ExactRef>(); values.forEach(value -> refs.add(ExactRef.fromJson(value))); return List.copyOf(refs); }
}
