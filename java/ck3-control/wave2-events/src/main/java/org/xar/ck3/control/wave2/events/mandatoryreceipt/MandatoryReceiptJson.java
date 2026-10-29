package org.xar.ck3.control.wave2.events.mandatoryreceipt;

import static org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.IntegerIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;

/** Exact v1 request wrapper; original ticket/native result containers are explicit retained projections. */
public final class MandatoryReceiptJson {
    public static final String SCHEMA = "xar.java-mandatory-choice-after-response-request/v1";
    private static final int MAX_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private MandatoryReceiptJson() { }

    public static Input decode(byte[] raw) {
        ObjectNode row = exact(parse(raw), Set.of("schema", "ticket", "outcome", "error", "captured_at_utc"));
        require(SCHEMA.equals(text(row.get("schema"), false)), "after-response schema");
        ObjectNode sourceTicket = object(row.get("ticket"));
        Ticket ticket = new Ticket(text(sourceTicket.get("incident_id"), false), ExactRef.fromJson(sourceTicket.get("before")),
                identity(sourceTicket.get("window_id")), identity(sourceTicket.get("instance")), identity(sourceTicket.get("choice_id")));
        JsonNode outcome = row.get("outcome");
        require(outcome.isNull() || outcome.isObject(), "outcome must be object or explicit null");
        JsonNode result = outcome.isObject() ? valueOrNull(outcome.get("result")) : JSON.getNodeFactory().nullNode();
        boolean accepted = result.isObject() && optionalTrue(result.get("accepted"));
        Optional<NativePostcondition> post = Optional.empty();
        if (result.isObject() && result.path("mandatory_choice_postcondition").isObject()) {
            JsonNode nativePost = result.get("mandatory_choice_postcondition");
            post = Optional.of(new NativePostcondition(optionalTrue(nativePost.get("verified")), optionalIdentity(nativePost.get("old_window_id")),
                    optionalIdentity(nativePost.get("old_instance")), optionalIdentity(nativePost.get("selected_choice_id")),
                    optionalTrue(nativePost.get("old_window_no_longer_blocking"))));
        }
        Optional<ErrorDetails> error = Optional.empty();
        if (!row.get("error").isNull()) {
            ObjectNode sourceError = exact(row.get("error"), Set.of("type", "message", "native_raw_receipt"));
            error = Optional.of(new ErrorDetails(text(sourceError.get("type"), false), text(sourceError.get("message"), true),
                    document(sourceError.get("native_raw_receipt"))));
        }
        return new Input(ticket, new Reply(accepted, post, document(result)), error, text(row.get("captured_at_utc"), false));
    }

    public static byte[] produce(byte[] raw) { return produce(raw, new MandatoryReceiptProducer()); }
    public static byte[] produce(byte[] raw, MandatoryReceiptPort consumer) {
        java.util.Objects.requireNonNull(consumer); return encode(consumer.produce(decode(raw)));
    }
    public static byte[] encode(AfterResponse body) {
        ObjectNode out = JSON.createObjectNode(); out.put("schema", "xar.unknown-mandatory-choice-incident/v1");
        out.put("incident_id", body.ticket().incidentId()); out.put("stage", "after_response"); out.put("captured_at_utc", body.capturedAtUtc());
        out.set("before", body.ticket().before().toJson()); out.put("command_acknowledged", body.commandAcknowledged());
        out.put("original_blocking_window_advanced_verified", body.originalWindowAdvancedVerified());
        out.set("action_receipt", parse(body.actionReceipt().json().getBytes(StandardCharsets.UTF_8)));
        if (body.error().isPresent()) {
            ErrorDetails error = body.error().orElseThrow(); ObjectNode item = out.putObject("error");
            item.put("type", error.type()); item.put("message", error.message()); item.set("native_raw_receipt", parse(error.nativeRawReceipt().json().getBytes(StandardCharsets.UTF_8)));
        } else { out.putNull("error"); }
        out.put("replay_allowed", body.replayAllowed()); out.put("material_effects_verified", body.materialEffectsVerified());
        out.put("offline_followup_required", body.offlineFollowupRequired()); return bytes(out);
    }
    private static Optional<ChoiceIdentity> optionalIdentity(JsonNode node) { return node == null || node.isNull() ? Optional.empty() : Optional.of(identity(node)); }
    private static ChoiceIdentity identity(JsonNode node) {
        if (node != null && node.isTextual()) { return new TextIdentity(text(node, false)); }
        require(node != null && node.isIntegralNumber(), "identity integer token required; no bool/float/string coercion");
        BigInteger value = node.bigIntegerValue(); require(value.compareTo(BigInteger.ONE.shiftLeft(63).negate()) >= 0
                && value.compareTo(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)) <= 0, "identity 64-bit domain");
        return new IntegerIdentity(value);
    }
    private static boolean optionalTrue(JsonNode node) {
        if (node == null || node.isNull()) { return false; }
        require(node.isBoolean(), "actual native boolean token required"); return node.booleanValue();
    }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node; }
    private static ObjectNode exact(JsonNode node, Set<String> fields) {
        ObjectNode row = object(node); Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields), "exact versioned wrapper fields required"); return row;
    }
    private static String text(JsonNode node, boolean allowEmpty) {
        require(node != null && node.isTextual(), "string token required"); String value = node.textValue();
        require(allowEmpty || !value.isEmpty(), "nonempty text required"); if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded UTF-8 after-response JSON required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode result = JSON.readTree(value); require(result != null, "JSON value required"); validate(result, 0); return result;
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/trailing receipt JSON", error); }
    }
    private static void validate(JsonNode node, int depth) {
        require(depth <= 64, "bounded receipt nesting");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        if (node.isFloatingPointNumber()) { require(Double.isFinite(node.doubleValue()), "finite JSON number required"); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(name -> { if (!name.isEmpty()) { StrictJson.text(name); } }); }
        if (node.isContainerNode()) { node.forEach(value -> validate(value, depth + 1)); }
    }
    private static JsonNode valueOrNull(JsonNode value) { return value == null ? JSON.getNodeFactory().nullNode() : value; }
    private static EvidenceDocument document(JsonNode value) { return new EvidenceDocument(new String(bytes(value), StandardCharsets.UTF_8)); }
    private static byte[] bytes(JsonNode value) {
        try { byte[] raw = JSON.writeValueAsBytes(value); require(raw.length <= MAX_BYTES, "after-response output byte budget"); return raw; }
        catch (IOException error) { throw new IllegalArgumentException("receipt serialization failed", error); }
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
