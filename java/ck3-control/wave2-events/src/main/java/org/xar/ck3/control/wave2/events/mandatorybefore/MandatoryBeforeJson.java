package org.xar.ck3.control.wave2.events.mandatorybefore;

import static org.xar.ck3.control.wave2.events.mandatorybefore.MandatoryBeforeModel.*;

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
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceCodec;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.IntegerIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;

/** Original capture_before validations and detached body composition, with actual integer token checks. */
public final class MandatoryBeforeJson {
    public static final String SCHEMA = "xar.java-mandatory-choice-before-body-request/v1";
    private static final String CAPTURE_SCHEMA = "xar.unknown-mandatory-choice-incident/v1";
    private static final String SELECT_STEP = "select-mandatory-choice-v1";
    private static final int MAX_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private MandatoryBeforeJson() { }

    public static Input decode(byte[] raw) {
        ObjectNode request = exact(parse(raw), Set.of("schema", "planned", "incident_id", "captured_at_utc"));
        require(SCHEMA.equals(text(request.get("schema"))), "before-body request schema");
        ObjectNode planned = object(request.get("planned")); ObjectNode plan = object(planned.get("plan"));
        ObjectNode capture = object(plan.get("unknown_mandatory_choice_v1"));
        require(CAPTURE_SCHEMA.equals(text(capture.get("schema"))), "missing mandatory-choice capture");
        FrameBinding frame = MandatoryChoiceCodec.decodeFrame(bytes(capture.get("frame_binding")));
        NativeWindow window = MandatoryChoiceCodec.decode(bytes(capture.get("native_window")));
        require(frame.equals(window.frame()), "before capture lost exact frame");
        require(frame.snapshotId().equals(text(planned.get("snapshot_id")))
                && frame.revision().equals(integer(planned.get("revision"))), "planned public frame changed");
        ObjectNode proof = object(capture.path("native_window").get("blocking_proof"));
        require(Set.of("blocks_simulation", "exclusive_modal_blocks_input").contains(text(proof.get("kind"))), "native blocker kind");
        trueValue(proof.get("verified")); text(proof.get("source"));
        trueValue(capture.path("native_window").get("choices_complete"));
        trueValue(capture.get("blocking_proof_verified")); trueValue(capture.get("catalogue_complete"));
        ObjectNode selection = object(capture.get("selection"));
        require(SELECT_STEP.equals(text(selection.get("selected_step")))
                && SELECT_STEP.equals(text(plan.get("selected_step"))), "only existing mandatory token route can be captured");
        ChoiceIdentity choiceId = identity(selection.get("choice_id"));
        String token = text(selection.get("action_token"));
        List<NativeChoice> matches = window.choices().stream().filter(row -> row instanceof NativeChoice)
                .map(row -> (NativeChoice) row).filter(choice -> choice.identity().equals(choiceId)).toList();
        require(matches.size() == 1, "before capture requires exactly one original selected row, even for identical duplicates");
        NativeChoice choice = matches.getFirst();
        require(choice.actionToken().hasValue() && token.equals(choice.actionToken().value())
                && choice.visible().hasValue() && choice.visible().value()
                && choice.enabled().hasValue() && choice.enabled().value()
                && choice.isChoice().hasValue() && choice.isChoice().value(), "selected native row is not the original legal token");
        return new Input(text(request.get("incident_id")), text(request.get("captured_at_utc")), frame, window, choice,
                new EvidenceDocument(new String(bytes(capture), StandardCharsets.UTF_8)));
    }
    public static byte[] produce(byte[] raw) { return produce(raw, BeforeBody::new); }
    public static byte[] produce(byte[] raw, MandatoryBeforePort consumer) {
        java.util.Objects.requireNonNull(consumer); return encode(consumer.produce(decode(raw)));
    }
    public static byte[] encode(BeforeBody body) {
        Input input = body.source(); ObjectNode output = object(parse(input.originalCapture().json().getBytes(StandardCharsets.UTF_8)));
        output.put("incident_id", input.incidentId()); output.put("stage", "before_submission"); output.put("captured_at_utc", input.capturedAtUtc());
        output.put("dispatch_attempted", body.dispatchAttempted()); output.put("offline_followup_required", body.offlineFollowupRequired());
        output.put("replay_allowed", body.replayAllowed()); return bytes(output);
    }
    private static ChoiceIdentity identity(JsonNode node) {
        if (node != null && node.isTextual()) { return new TextIdentity(text(node)); }
        BigInteger value = integer(node); require(value.compareTo(BigInteger.ONE.shiftLeft(63).negate()) >= 0
                && value.compareTo(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)) <= 0, "native ID 64-bit domain");
        return new IntegerIdentity(value);
    }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "integer token required; no bool/float/string"); return node.bigIntegerValue(); }
    private static void trueValue(JsonNode node) { require(node != null && node.isBoolean() && node.booleanValue(), "actual native true required"); }
    private static String text(JsonNode node) { require(node != null && node.isTextual(), "string required"); return StrictJson.text(node.textValue()); }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "capture object required"); return (ObjectNode) node; }
    private static ObjectNode exact(JsonNode node, Set<String> fields) {
        ObjectNode row = object(node); Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields), "exact before-body wrapper fields required"); return row;
    }
    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded UTF-8 before-body JSON required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = JSON.readTree(value); require(node != null, "JSON value required"); validate(node, 0); return node;
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/trailing before JSON", error); }
    }
    private static void validate(JsonNode node, int depth) {
        require(depth <= 64, "bounded before-body nesting");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        if (node.isFloatingPointNumber()) { require(Double.isFinite(node.doubleValue()), "finite geometry JSON number"); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(name -> { if (!name.isEmpty()) { StrictJson.text(name); } }); }
        if (node.isContainerNode()) { node.forEach(value -> validate(value, depth + 1)); }
    }
    private static byte[] bytes(JsonNode node) {
        try { byte[] result = JSON.writeValueAsBytes(node); require(result.length <= MAX_BYTES, "before-body output budget"); return result; }
        catch (IOException error) { throw new IllegalArgumentException("before-body serialization failed", error); }
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
