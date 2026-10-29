package org.xar.ck3.control.application.action.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.CommandOriginCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** One strict persistence contract for the manifest and every immutable request/result row. */
public final class CouncilContinuationCodec {
    private CouncilContinuationCodec() { }
    public static byte[] encodeState(State state) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("machine_id", state.machineId());
        row.set("active", state.active().map(CouncilContinuationCodec::scope).orElse(null));
        var records = row.putArray("records"); state.records().forEach(ref -> records.add(ref.toJson()));
        row.set("completed_scope_chain", state.completedScopeChain().map(ExactRef::toJson).orElse(null));
        return StrictJson.canonical(row, MAX_BODY_BYTES);
    }
    public static State decodeState(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAX_BODY_BYTES), Set.of("schema", "machine_id", "active", "records", "completed_scope_chain"));
        StrictJson.require(SCHEMA.equals(text(row, "schema")), "exact continuation manifest schema required");
        return new State(text(row, "machine_id"), row.get("active").isNull() ? Optional.empty() : Optional.of(scope(row.get("active"))),
                refs(row.get("records")), optionalRef(row.get("completed_scope_chain")));
    }
    public static byte[] encodeEntry(Entry value) {
        var row = StrictJson.object(); row.put("schema", "xar.java-council-continuation-entry/v1"); row.set("request", request(value.request()));
        row.put("status", value.status().name()); row.set("outcome", value.outcome().map(ExactRef::toJson).orElse(null));
        row.put("result_sequence", value.resultSequence());
        row.set("issued", value.issued().map(CouncilContinuationCodec::custody).orElse(null)); return StrictJson.canonical(row, MAX_BODY_BYTES);
    }
    public static Entry decodeEntry(byte[] raw) {
        var row = StrictJson.object(StrictJson.parse(raw, MAX_BODY_BYTES), Set.of("schema", "request", "status", "outcome", "issued", "result_sequence"));
        StrictJson.require("xar.java-council-continuation-entry/v1".equals(text(row, "schema")), "exact continuation entry schema required");
        return new Entry(request(row.get("request")), Status.valueOf(text(row, "status")), optionalRef(row.get("outcome")),
                row.get("issued").isNull() ? Optional.empty() : Optional.of(custody(row.get("issued"))), StrictJson.integer(row.get("result_sequence"), 0, StrictJson.MAX_SAFE_INTEGER));
    }
    public static ObjectNode request(Request value) {
        var row = StrictJson.object(); row.put("schema", "xar.java-council-continuation-request/v1"); row.set("scope", scope(value.scope()));
        row.put("request_id", value.requestId()); row.put("stage", value.stage().name()); row.set("original_parent_receipt", value.originalParentReceipt().toJson());
        row.set("prepared_request", value.preparedRequest().toJson()); row.set("guard", CommandOriginCodec.guard(value.guard()));
        row.put("issued_at", value.issuedAt().toString()); row.put("deadline", value.deadline().toString()); row.put("issued_sequence", value.issuedSequence());
        var refs = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> refs.add(ref.toJson())); return row;
    }
    public static Request request(JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("schema", "scope", "request_id", "stage", "original_parent_receipt", "prepared_request", "guard", "issued_at", "deadline", "issued_sequence", "supporting_evidence"));
        StrictJson.require("xar.java-council-continuation-request/v1".equals(text(row, "schema")), "exact continuation request schema required");
        return new Request(scope(row.get("scope")), text(row, "request_id"), Stage.valueOf(text(row, "stage")), ExactRef.fromJson(row.get("original_parent_receipt")),
                ExactRef.fromJson(row.get("prepared_request")), CommandOriginCodec.guard(row.get("guard")), instant(row, "issued_at"), instant(row, "deadline"),
                StrictJson.integer(row.get("issued_sequence"), 1, StrictJson.MAX_SAFE_INTEGER), refs(row.get("supporting_evidence")));
    }
    public static ObjectNode custody(IssuedCustody value) {
        var row = StrictJson.object(); row.set("record", value.record().toJson()); row.set("domain_payload", value.domainPayload().toJson()); row.set("event", value.event().toJson()); return row;
    }
    public static IssuedCustody custody(JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("record", "domain_payload", "event"));
        return new IssuedCustody(ExactRef.fromJson(row.get("record")), ExactRef.fromJson(row.get("domain_payload")), ExactRef.fromJson(row.get("event")));
    }
    private static ObjectNode scope(Scope value) {
        var row = StrictJson.object(); row.put("parent_action_id", value.parentActionId()); row.put("parent_body_sha256", value.parentBodySha256());
        row.put("original_attempt_request_id", value.originalAttemptRequestId()); return row;
    }
    private static Scope scope(JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("parent_action_id", "parent_body_sha256", "original_attempt_request_id"));
        return new Scope(text(row, "parent_action_id"), text(row, "parent_body_sha256"), text(row, "original_attempt_request_id"));
    }
    private static Optional<ExactRef> optionalRef(JsonNode raw) { return raw.isNull() ? Optional.empty() : Optional.of(ExactRef.fromJson(raw)); }
    private static List<ExactRef> refs(JsonNode raw) {
        StrictJson.require(raw != null && raw.isArray(), "explicit continuation references array required"); List<ExactRef> refs = new ArrayList<>();
        raw.forEach(value -> refs.add(ExactRef.fromJson(value))); return List.copyOf(refs);
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static Instant instant(ObjectNode row, String field) {
        String token = text(row, field); Instant value = Instant.parse(token); StrictJson.require(token.equals(value.toString()), "canonical UTC continuation time required"); return value;
    }
}
