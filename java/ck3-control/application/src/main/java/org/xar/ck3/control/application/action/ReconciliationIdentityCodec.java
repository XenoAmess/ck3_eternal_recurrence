package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.application.effects.RootGuardEvidence.WriterPoint;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Sole closed representation of factual readonly reconciliation; parsing creates no readiness or submission authority. */
public final class ReconciliationIdentityCodec {
    public static final String SCHEMA = "xar.java.reconciliation-identity/v1";
    public static final String HISTORY_SCHEMA = "xar.java.reconciliation-identity/v2";
    private ReconciliationIdentityCodec() { }
    public static ObjectNode encode(ReconciliationIdentity value) {
        ObjectNode row = StrictJson.object();boolean history=value.driverRelation()==ReconciliationIdentity.DriverRelation.HISTORY_APPEND;
        row.put("schema",history?HISTORY_SCHEMA:SCHEMA);
        if(history){
            row.put("driver_relation",ReconciliationIdentity.DriverRelation.HISTORY_APPEND.name());var point=value.historyPoint().orElseThrow();
            row.putObject("history_point").put("sequence",point.sequence()).put("digest",point.digest());
        }
        row.set("factual", ProposalLifecycleCodec.observation(value.factual())); row.set("source", ProposalLifecycleCodec.source(value.source()));
        row.put("session_id", value.sessionId()); row.put("connection_generation", new CrossJsDecimalUInt64(value.connectionGeneration().toString()).decimal());
        ObjectNode pending = row.putObject("pending"); pending.put("action_id", value.pending().actionId()); pending.put("body_sha256", value.pending().bodySha256());
        pending.put("request_id", value.pending().requestId()); pending.set("original_before", ProposalLifecycleCodec.observation(value.pending().originalBefore()));
        pending.set("original_receipt", value.pending().originalReceipt().toJson()); pending.set("original_before_driver", value.pending().originalBeforeDriver().toJson());
        ObjectNode evidence = row.putObject("evidence"); evidence.set("actual_native_packet", value.evidence().actualNativePacket().toJson());
        evidence.set("actual_hello", value.evidence().actualHello().toJson()); evidence.set("original_heartbeat", value.evidence().originalHeartbeat().toJson());
        evidence.set("observation_manifest", value.evidence().observationManifest().toJson()); evidence.set("current_original_driver", value.evidence().currentOriginalDriver().toJson());
        evidence.set("complete_source_qualification", ExactRef.optionalToJson(value.evidence().completeSourceQualification()));
        row.put("observed_at", value.observedAt().toString()); return row;
    }
    public static ReconciliationIdentity decode(JsonNode value) {
        ObjectNode object=ContinuityJson.object(value);String schema=text(object,"schema");boolean history=HISTORY_SCHEMA.equals(schema);
        StrictJson.require(SCHEMA.equals(schema)||history,"exact readonly reconciliation identity version required");
        Set<String> fields=history?Set.of("schema","factual","source","session_id","connection_generation","pending","evidence","observed_at","driver_relation","history_point"):
                Set.of("schema","factual","source","session_id","connection_generation","pending","evidence","observed_at");
        ObjectNode row=StrictJson.object(object,fields);Optional<WriterPoint> point=Optional.empty();
        if(history){
            StrictJson.require(text(row,"driver_relation").equals(ReconciliationIdentity.DriverRelation.HISTORY_APPEND.name()),"v2 requires its exact history-append DATA relation");
            ObjectNode actual=StrictJson.object(row.get("history_point"),Set.of("sequence","digest"));
            point=Optional.of(new WriterPoint(StrictJson.integer(actual.get("sequence"),0,StrictJson.MAX_SAFE_INTEGER),text(actual,"digest")));
        }
        ObjectNode pending = StrictJson.object(row.get("pending"), Set.of("action_id", "body_sha256", "request_id", "original_before", "original_receipt", "original_before_driver"));
        ObjectNode evidence = StrictJson.object(row.get("evidence"), Set.of("actual_native_packet", "actual_hello", "original_heartbeat", "observation_manifest", "current_original_driver"),Set.of("complete_source_qualification"));
        BigInteger generation = new BigInteger(new CrossJsDecimalUInt64(text(row, "connection_generation")).decimal()); FrontendFrame.positive(generation);
        return new ReconciliationIdentity(ProposalLifecycleCodec.decodeObservation(row.get("factual")), G2Wire.source(row.get("source")),
                text(row, "session_id"), generation,
                new ReconciliationIdentity.Pending(text(pending, "action_id"), text(pending, "body_sha256"), text(pending, "request_id"),
                        ProposalLifecycleCodec.decodeObservation(pending.get("original_before")), ExactRef.fromJson(pending.get("original_receipt")), ExactRef.fromJson(pending.get("original_before_driver"))),
                new ReconciliationIdentity.Evidence(ExactRef.fromJson(evidence.get("actual_native_packet")), ExactRef.fromJson(evidence.get("actual_hello")),
                        ExactRef.fromJson(evidence.get("original_heartbeat")), ExactRef.fromJson(evidence.get("observation_manifest")),
                        ExactRef.fromJson(evidence.get("current_original_driver")), ExactRef.optionalFromJson(evidence.get("complete_source_qualification"))),
                instant(text(row, "observed_at")),history?ReconciliationIdentity.DriverRelation.HISTORY_APPEND:ReconciliationIdentity.DriverRelation.EXACT,point);
    }
    private static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
    private static Instant instant(String raw) {
        Instant value;
        try { value = Instant.parse(raw); }
        catch (DateTimeParseException malformed) { throw new IllegalArgumentException("canonical actual reconciliation UTC instant required", malformed); }
        StrictJson.require(value.toString().equals(raw), "canonical actual reconciliation UTC instant required"); return value;
    }
}
