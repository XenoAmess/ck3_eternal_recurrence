package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.g2.common.G2Wire;

/** Single JSON contract for terminal dispositions; decoding remains DATA until the installed domain verifier replays originals. */
public final class ActionTerminalCodec {
    private ActionTerminalCodec() { }
    public static ObjectNode encode(ActionTerminalObservation value, Function<PlanningReadReceipt, ExactRef> readReference) {
        var row = StrictJson.object(); row.put("schema", "xar.action-terminal-observation/v1"); row.put("command_body_sha256", value.commandBodySha256()); row.put("attempt_request_id", value.attemptRequestId());
        var disposition = row.putObject("disposition"); disposition.put("kind", value.disposition() instanceof ActionTerminalObservation.PrisonerTransferred ? "PRISONER_TRANSFERRED" : "PRISONER_TARGET_DEAD");
        disposition.put("target_id", value.disposition().targetId());
        if (value.disposition() instanceof ActionTerminalObservation.PrisonerTransferred transferred) disposition.put("current_jailer_id", transferred.currentJailerId());
        row.set("before", ProposalLifecycleCodec.observation(value.before())); row.set("after", ProposalLifecycleCodec.observation(value.after())); row.set("source", ProposalLifecycleCodec.source(value.source()));
        row.put("session_id", value.sessionId()); row.set("observation_provenance", ObservationProvenanceCodec.encode(value.provenance())); row.put("observed_at", value.observedAt().toString());
        row.set("original_evidence", value.originalEvidence().toJson()); row.set("original_submission", value.originalSubmission().toJson());
        row.set("selected_collection_ref", readReference.apply(value.selectedCollection()).toJson()); row.set("after_collection_ref", readReference.apply(value.afterCollection()).toJson());
        var refs = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> refs.add(ref.toJson())); return row;
    }
    public static ActionTerminalObservation decode(JsonNode raw, Function<ExactRef, PlanningReadReceipt> loadRead) {
        var row = StrictJson.object(raw, Set.of("schema", "command_body_sha256", "attempt_request_id", "disposition", "before", "after", "source", "session_id", "observation_provenance", "observed_at", "original_evidence", "original_submission", "selected_collection_ref", "after_collection_ref", "supporting_evidence"));
        StrictJson.require("xar.action-terminal-observation/v1".equals(StrictJson.text(row.get("schema"))), "exact terminal observation schema required");
        StrictJson.require(row.get("disposition") instanceof ObjectNode, "typed terminal disposition object required");
        ObjectNode d = (ObjectNode) row.get("disposition"); String kind = StrictJson.text(d.get("kind")); ActionTerminalObservation.Disposition disposition;
        if (kind.equals("PRISONER_TRANSFERRED")) { StrictJson.object(d, Set.of("kind", "target_id", "current_jailer_id")); disposition = new ActionTerminalObservation.PrisonerTransferred(id(d.get("target_id")), id(d.get("current_jailer_id"))); }
        else { StrictJson.require(kind.equals("PRISONER_TARGET_DEAD"), "known independent terminal disposition required"); StrictJson.object(d, Set.of("kind", "target_id")); disposition = new ActionTerminalObservation.PrisonerTargetDead(id(d.get("target_id"))); }
        StrictJson.require(row.get("supporting_evidence").isArray(), "terminal evidence array required"); List<ExactRef> refs = new ArrayList<>(); row.get("supporting_evidence").forEach(ref -> refs.add(ExactRef.fromJson(ref)));
        String time = StrictJson.text(row.get("observed_at")); Instant observed = Instant.parse(time); StrictJson.require(time.equals(observed.toString()), "canonical terminal observation UTC time required");
        return new ActionTerminalObservation(StrictJson.text(row.get("command_body_sha256")), StrictJson.text(row.get("attempt_request_id")), disposition,
                ProposalLifecycleCodec.decodeObservation(row.get("before")), ProposalLifecycleCodec.decodeObservation(row.get("after")), G2Wire.source(row.get("source")), StrictJson.text(row.get("session_id")),
                ObservationProvenanceCodec.decode(row.get("observation_provenance")), observed, ExactRef.fromJson(row.get("original_evidence")), ExactRef.fromJson(row.get("original_submission")),
                loadRead.apply(ExactRef.fromJson(row.get("selected_collection_ref"))), loadRead.apply(ExactRef.fromJson(row.get("after_collection_ref"))), refs);
    }
    private static BigInteger id(JsonNode raw) { return BigInteger.valueOf(StrictJson.integer(raw, 1, StrictJson.MAX_SAFE_INTEGER)); }
}
