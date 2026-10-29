package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.governance.council.CouncilCodec.*;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

/** Original mailbox replies remain separate packets. A pending reply grants no candidate material. */
public final class CouncilPrivateCodec {
    private CouncilPrivateCodec() { }
    public static final String QUERY = "private-query-council-composition-candidates-v1";
    public static final String GATES = "private-query-council-final-gates-v1";
    public static final String STATUS = "private-council-application-main-status-v1";
    private static final String COMPOSITION = "query-council-composition-candidates-v1";
    private static final Set<String> ENVELOPE_REQUIRED = Set.of("schema", "step", "accepted", "status", "query_sequence", "snapshot_revision", "backend_id");
    private static final Set<String> ENVELOPE_OPTIONAL = Set.of("council_composition_candidates", "council_final_gates", "private", "advertised", "native_helper_invocations_delta", "owner_character_id", "date_raw", "native_revision", "unavailable_reason");
    private static final Set<String> GATE_BOOLEANS = Set.of("final_gate_available", "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction", "incumbent_fireability_evaluated", "incumbent_can_be_fired");
    private static final Set<String> ACTION_FIELDS = Set.of("council_assign_councillor_ack", "council_assign_councillor_receipt", "action_request_id");
    public sealed interface Reply permits Pending, Terminal { JsonBody original(); }
    public record Pending(JsonBody original) implements Reply { public Pending { Objects.requireNonNull(original); } }
    /** Payload validation deliberately follows durable archival of this actual terminal packet. */
    public record Terminal(JsonBody original) implements Reply { public Terminal { Objects.requireNonNull(original); } }

    public static Reply decodeReply(byte[] resultBytes, String wireStep) {
        StrictJson.require(Set.of(QUERY, GATES, STATUS).contains(wireStep), "unsupported Council mailbox read");
        ObjectNode value = object(StrictJson.parse(resultBytes));
        if (value.has("private_council_transport")) {
            StrictJson.object(value, Set.of("private_council_transport", "advertised", "step", "status"));
            StrictJson.trueValue(value.get("private_council_transport"));
            StrictJson.require(!bool(value.get("advertised")) && text(value, "step").equals(wireStep)
                    && text(value, "status").equals("pending"), "Council mailbox is idle, malformed or belongs to another step");
            return new Pending(new JsonBody(resultBytes));
        }
        // Preserve malformed business material in its own archived receipt before rejecting it.
        StrictJson.require(text(value, "schema").equals("xar.ck3.council-application-main/v1"), "Council terminal schema mismatch");
        StrictJson.trueValue(value.get("accepted"));
        StrictJson.require(text(value, "backend_id").equals("native-headless"), "Council terminal backend mismatch");
        u64(value.get("query_sequence"), true); u64(value.get("snapshot_revision"), true);
        return new Terminal(new JsonBody(resultBytes));
    }

    /** Must pass before marking the held mailbox consumed. No synthetic ticket or initial-request receipt. */
    public static void requireTerminalBinding(Terminal terminal, String initialStep, Frame nativeFrame) {
        ObjectNode value = object(StrictJson.parse(terminal.original().bytes()));
        StrictJson.require(text(value, "step").equals(semanticStep(initialStep))
                && u64(value.get("snapshot_revision"), true).equals(nativeFrame.nativeRevision()), "Council terminal crossed its original operation/native frame");
        StrictJson.require(ACTION_FIELDS.stream().noneMatch(value::has), "Council read returned action material");
        for (String key : List.of("business_action_submitted", "native_action_submitted", "assignment_submitted", "materialized"))
            StrictJson.require(!value.has(key) || !bool(value.get(key)), "Council read submitted a business action");
        StrictJson.require(!Set.of("pending", "native_helper_invoked_verification_pending", "rejected_before_submit", "applied", "postcondition_failed")
                .contains(text(value, "status")), "Council terminal is an action state");
    }

    /** Returns the sole six-field Council contract inside a complete public/native frame projection. */
    public static JsonBody normalize(Terminal terminal, String initialStep, Frame nativeFrame, Frame publicFrame,
            Position role, String connectedVersion, String connectedSha256) {
        Objects.requireNonNull(role); requireTerminalBinding(terminal, initialStep, nativeFrame);
        StrictJson.require(nativeFrame.snapshotId().equals("native:" + nativeFrame.nativeRevision())
                && nativeFrame.publicRevision().equals(nativeFrame.nativeRevision())
                && nativeFrame.nativeRevision().equals(publicFrame.nativeRevision())
                && nativeFrame.dateRaw() == publicFrame.dateRaw() && nativeFrame.ownerId() == publicFrame.ownerId(), "Council native/public frame projection mismatch");
        ObjectNode value = object(StrictJson.parse(terminal.original().bytes()));
        fields(value, ENVELOPE_REQUIRED, ENVELOPE_OPTIONAL);
        requireBuild(connectedVersion, connectedSha256);
        if (value.has("private")) StrictJson.trueValue(value.get("private"));
        if (value.has("advertised")) StrictJson.require(!bool(value.get("advertised")), "private Council result was advertised");
        if (value.has("native_helper_invocations_delta")) number(value, "native_helper_invocations_delta", 0, 0);
        if (value.has("owner_character_id") && !value.get("owner_character_id").isNull())
            StrictJson.require(id(value.get("owner_character_id")) == nativeFrame.ownerId(), "Council terminal owner drift");
        if (value.has("date_raw") && !value.get("date_raw").isNull())
            StrictJson.require(number(value, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == nativeFrame.dateRaw(), "Council terminal date drift");
        if (value.has("native_revision") && !value.get("native_revision").isNull())
            StrictJson.require(u64(value.get("native_revision"), true).equals(nativeFrame.nativeRevision()), "Council terminal native revision drift");
        ObjectNode gates = null;
        if (initialStep.equals(GATES) && value.get("council_final_gates") instanceof ObjectNode observedGates) gates = observedGates;
        JsonNode payload = gates == null ? value.get("council_composition_candidates") : gates.get("council_composition_candidates");
        ObjectNode result = value.deepCopy();
        project(result, initialStep, publicFrame);
        if (!(payload instanceof ObjectNode nativePayload)) {
            StrictJson.require((!value.has("council_composition_candidates") || value.get("council_composition_candidates").isNull())
                    && (gates == null || !gates.has("council_composition_candidates") || gates.get("council_composition_candidates").isNull()), "Council malformed candidate material is not absence");
            result.put("native_envelope_status", text(value, "status")).put("status", "unavailable")
                    .put("unavailable_reason", "missing_candidate_payload").put("council_missing_payload_readonly", true);
            return new JsonBody(StrictJson.canonical(result));
        }
        String payloadStatus = text(nativePayload, "status");
        StrictJson.require(Set.of("available", "unavailable").contains(payloadStatus)
                && text(value, "status").equals(payloadStatus), "Council envelope/payload availability mismatch");
        // Exact build and schema are required for unavailable native payloads as well.
        ObjectNode exact = StrictJson.object(nativePayload.get("exact_build"), Set.of("game_version", "executable_sha256"));
        requireBuild(text(exact, "game_version"), text(exact, "executable_sha256"));
        StrictJson.require(text(exact, "game_version").equals(connectedVersion)
                && text(exact, "executable_sha256").equalsIgnoreCase(connectedSha256)
                && text(nativePayload, "schema").equals("xar.ck3.council-composition-candidates/v1")
                && number(nativePayload, "schema_version", 1, 1) == 1
                && text(nativePayload, "capability").equals("game.query.council-composition-candidates-v1"), "Council source/build metadata mismatch");
        result.set("exact_build", exact.deepCopy());
        if (payloadStatus.equals("unavailable")) return new JsonBody(StrictJson.canonical(result));
        Candidates decoded = CouncilCodec.decodeNative(StrictJson.canonical(nativePayload), nativeFrame, role, connectedVersion, connectedSha256);
        JsonNode normalized = StrictJson.parse(CouncilCodec.encode(decoded));
        result.set("council_composition_candidates", normalized);
        if (initialStep.equals(GATES)) {
            StrictJson.require(gates != null, "final-gates read lacks its own gate material");
            StrictJson.object(gates, Set.of("schema", "status", "unavailable_reason", "candidate_count", "rows", "council_composition_candidates"));
            StrictJson.require(text(gates, "schema").equals("xar.ck3.private.council-final-gates/v1")
                    && text(gates, "status").equals("available") && text(gates, "unavailable_reason").equals("none"), "Council final gates unavailable");
            JsonNode rows = gates.get("rows");
            StrictJson.require(rows != null && rows.isArray() && rows.size() == decoded.candidates().size()
                    && number(gates, "candidate_count", 0, 0xffff_ffffL) == decoded.candidates().size(), "Council final gates incomplete");
            Set<String> gateFields = new HashSet<>(GATE_BOOLEANS); gateFields.addAll(Set.of("character_id", "native_collection_ordinal"));
            for (int index = 0; index < rows.size(); index++) {
                ObjectNode row = StrictJson.object(rows.get(index), gateFields); Candidate candidate = decoded.candidates().get(index);
                StrictJson.require(id(row.get("character_id")) == candidate.characterId()
                        && number(row, "native_collection_ordinal", 0, 0xffff_ffffL) == candidate.nativeCollectionOrdinal(), "Council final gate row identity/order drift");
                GATE_BOOLEANS.forEach(key -> bool(row.get(key)));
            }
            ObjectNode normalizedGates = gates.deepCopy(); normalizedGates.set("council_composition_candidates", normalized);
            result.set("council_final_gates", normalizedGates);
        }
        return new JsonBody(StrictJson.canonical(result));
    }
    private static String semanticStep(String initialStep) {
        return switch (initialStep) { case QUERY -> COMPOSITION; case GATES -> GATES; default -> throw new IllegalArgumentException("not a Council initial read"); };
    }
    private static void project(ObjectNode value, String step, Frame frame) {
        value.put("step", step).put("native_step", semanticStep(step)).put("private_build", true).put("advertised", false).put("read_only", true)
                .put("queried_snapshot_id", frame.snapshotId()).put("queried_revision", frame.publicRevision()).put("queried_native_revision", frame.nativeRevision());
        value.set("source_frame", StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.publicRevision())
                .put("native_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw()).put("player_character_id", frame.ownerId()).put("paused", true));
    }
    private static void fields(ObjectNode value, Set<String> required, Set<String> optional) {
        Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.containsAll(required), "Council terminal required fields missing"); actual.removeAll(required);
        StrictJson.require(optional.containsAll(actual), "Council terminal contains unknown fields");
    }
}
