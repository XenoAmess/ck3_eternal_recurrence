package org.xar.ck3.control.wave2.events.interactionbefore;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.*;

/** Source-pinned evidence composition only; persistence and dispatch remain outside this module. */
public final class InteractionBeforeComposer {
    public static final int MAX_BYTES = 65_536;
    private static final JsonFactory JSON = new JsonFactory();
    private InteractionBeforeComposer() { }

    public static Result compose(byte[] originalPlanned, String expectedSha256, Identity identity, GuiSourcePin trustedGui) {
        sha(expectedSha256); java.util.Objects.requireNonNull(identity); java.util.Objects.requireNonNull(trustedGui);
        StrictJson.require(originalPlanned != null && digest(originalPlanned).equals(expectedSha256), "planned original source pin mismatch");
        JsonNode root = StrictJson.parse(originalPlanned); StrictJson.require(root.isObject(), "original planned object required");
        JsonNode plan = root.get("plan");
        if (plan == null || !plan.isObject()) { return new NotApplicable(); }
        JsonNode capture = plan.get("unhandled_interaction_fallback");
        if (capture == null || !capture.isObject()) { return new NotApplicable(); }
        StrictJson.object(capture, Set.of("schema", "kind", "policy", "pending_interaction_id", "interaction_definition_key", "binding", "context", "gui_binding",
                "reply_options", "selection", "registry_known", "reviewed_rule", "offline_registry_audit", "presented_choice_policy", "offline_followup_required", "original_plan", "semantic_optimal", "native_ai_equivalent"));
        StrictJson.require(text(capture, "schema").equals("xar.pending-interaction-left-reply/v1") && text(capture, "kind").equals("pending_character_interaction")
                && text(capture, "policy").equals("user-authorized-native-gui-left-reply"), "unsupported before-capture contract");
        int pending = signedId(capture.get("pending_interaction_id"));
        Frame frame = frame(capture.get("binding"));
        StrictJson.require(text(root, "snapshot_id").equals(frame.snapshotId()) && unsigned(root.get("revision")).equals(frame.revision()), "before evidence lost the original planned frame");
        JsonNode selection = capture.get("selection"); StrictJson.require(selection.isObject(), "selected native reply object required");
        Action action = switch (text(selection, "action")) {
            case "reject" -> Action.REJECT; case "acknowledge" -> Action.ACKNOWLEDGE;
            default -> throw new ContractViolationException("fallback before evidence cannot substitute right acceptance");
        };
        StrictJson.require(text(selection, "step").equals(action.step()) && text(selection, "position").equals(action.position())
                && StrictJson.integer(selection.get("rendered_index"), 0, 0) == 0, "selected reply/action/rendered position mismatch");
        boolean nativeLegal = bool(selection.get("native_legal")); boolean reachable = bool(selection.get("action_reachable"));
        JsonNode selected = plan.get("selected_step");
        if (selected != null && !selected.isNull()) {
            StrictJson.require(StrictJson.text(selected).equals(action.step()) && nativeLegal && reachable, "before evidence lost its legal reachable original reply");
        }
        JsonNode gui = capture.get("gui_binding"); StrictJson.require(gui != null && gui.isObject(), "original GUI binding required");
        StrictJson.require(text(gui, "source").equals(trustedGui.source()) && text(gui, "sha256").equals(trustedGui.sha256()), "before GUI source pin mismatch");
        CurrentInteractionPresentation.validateCapture(capture,
                selected == null || selected.isNull() ? null : StrictJson.text(selected), false);
        JsonNode replies = capture.get("reply_options"); StrictJson.require(replies.isArray() && replies.size() == 2, "complete normal GUI reply list required");
        reply(replies.get(0), "left", "reject", 0); reply(replies.get(1), "right", "accept", 1);
        falseValue(capture.get("semantic_optimal")); falseValue(capture.get("native_ai_equivalent"));
        JsonNode context = capture.get("context"); StrictJson.require(context != null && context.isObject(), "retained native context required");
        StrictJson.require(text(context, "status").equals("available") && unsigned(context.get("snapshot_revision")).equals(frame.nativeRevision())
                && unsigned(context.get("date_raw")).equals(frame.dateRaw()) && signedId(context.get("pending_interaction_id")) == pending, "before context crossed its original frame or pending ID");
        if (selected != null && !selected.isNull()) {
            JsonNode legality = context.path("legality").path(action.wire());
            StrictJson.require(legality.isObject() && text(legality, "status").equals("available"), "selected reply lacks current native legality"); StrictJson.trueValue(legality.get("allowed"));
        }
        byte[] rawCapture = captureBytes(originalPlanned);
        ObjectNode metadata = StrictJson.object(); metadata.put("incident_id", identity.incidentId()); metadata.put("stage", "before_submission");
        metadata.put("captured_at_utc", identity.capturedAtUtc()); metadata.put("machine_id", identity.machineId()); metadata.put("dispatch_attempted", false);
        byte[] suffix = StrictJson.canonical(metadata); ByteArrayOutputStream output = new ByteArrayOutputStream(rawCapture.length + suffix.length);
        output.write(rawCapture, 0, rawCapture.length - 1); output.write(','); output.write(suffix, 1, suffix.length - 2); output.write('}');
        byte[] bytes = output.toByteArray(); StrictJson.require(bytes.length <= MAX_BYTES, "before evidence exceeds bounded output");
        // Validate the completed bytes as JSON without re-encoding its retained float, integer, null or Unicode tokens.
        StrictJson.parse(bytes);
        Optional<String> selectedStep = selected == null || selected.isNull() ? Optional.empty() : Optional.of(selected.textValue());
        return new Prepared(bytes, identity, frame, pending, action, selectedStep, expectedSha256);
    }

    static Frame frame(JsonNode row) {
        StrictJson.object(row, Set.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready", "actor_character_id", "connection_generation", "bridge_pid"));
        return new Frame(text(row, "snapshot_id"), unsigned(row.get("revision")), unsigned(row.get("native_revision")), unsigned(row.get("date_raw")), text(row, "episode_run_id"),
                bool(row.get("paused")), bool(row.get("map_ready")), NativeCharacterId.fromJson(row.get("actor_character_id")).value(),
                unsigned(row.get("connection_generation")), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL));
    }
    private static void reply(JsonNode row, String position, String action, int index) {
        StrictJson.require(row != null && row.isObject() && text(row, "position").equals(position) && text(row, "action").equals(action)
                && StrictJson.integer(row.get("rendered_index"), index, index) == index && text(row, "step").equals(action + "-pending-character-interaction"), "native reply options lost their actual source GUI order");
    }
    private static byte[] captureBytes(byte[] raw) {
        try (var parser = JSON.createParser(raw)) {
            parser.nextToken();
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String field = parser.currentName(); JsonToken token = parser.nextToken();
                if (field.equals("plan") && token == JsonToken.START_OBJECT) {
                    while (parser.nextToken() != JsonToken.END_OBJECT) {
                        String nested = parser.currentName(); token = parser.nextToken();
                        if (nested.equals("unhandled_interaction_fallback") && token == JsonToken.START_OBJECT) {
                            int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); parser.skipChildren();
                            int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                            StrictJson.require(end > start && raw[end - 1] == '}', "exact capture object byte range required"); return Arrays.copyOfRange(raw, start, end);
                        }
                        parser.skipChildren();
                    }
                } else { parser.skipChildren(); }
            }
        } catch (IOException error) { throw new ContractViolationException("cannot retain original before-capture bytes", error); }
        throw new ContractViolationException("original capture byte range unavailable");
    }
    public static String digest(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA-256 unavailable", error); }
    }
    private static String text(JsonNode row, String field) { String value = StrictJson.text(row.get(field)); stable(value); return value; }
    private static BigInteger unsigned(JsonNode node) { return StrictJson.integer(node, BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static int signedId(JsonNode node) { int value = (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); StrictJson.require(value != -1, "invalid pending ID sentinel"); return value; }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue(); }
    private static void falseValue(JsonNode node) { StrictJson.require(node != null && node.isBoolean() && !node.booleanValue(), "source evidence cannot claim semantic or native-AI equivalence"); }
}
