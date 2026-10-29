package org.xar.ck3.control.wave2.events.interactionreceipt;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import static org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt.*;

/** Declared projection of extensible SDK response objects. Source origin is an out-of-band adapter argument. */
public final class InteractionReceiptCodec {
    private InteractionReceiptCodec() { }
    public static Response parseResponse(byte[] original, String expectedSha256) {
        String actual = InteractionRegistryCodec.digest(java.util.Objects.requireNonNull(original));
        StrictJson.require(actual.equals(expectedSha256), "original response source pin mismatch");
        JsonNode root = StrictJson.parse(original);
        if (root.isNull()) { return new Response(Presence.NULL, null, absentBoolean(), absentBoolean(), new Outcome(Presence.MISSING, null, null), new Remaining(Presence.MISSING, null), null, absentBoolean(), actual); }
        StrictJson.require(root.isObject(), "SDK result object or explicit null required");
        JsonNode step = root.get("step"); String selected = step == null || step.isNull() ? null : StrictJson.text(step);
        JsonNode interaction = root.get("interaction_result"); Outcome outcome;
        if (interaction == null || interaction.isNull()) { outcome = new Outcome(interaction == null ? Presence.MISSING : Presence.NULL, null, null); }
        else {
            StrictJson.require(interaction.isObject(), "interaction result object required");
            OutcomeStatus status = switch (StrictJson.text(interaction.get("status"))) {
                case "accepted" -> OutcomeStatus.ACCEPTED; case "rejected" -> OutcomeStatus.REJECTED; case "acknowledged" -> OutcomeStatus.ACKNOWLEDGED;
                default -> throw new ContractViolationException("unknown interaction outcome status");
            };
            outcome = new Outcome(Presence.VALUE, signedId(interaction.get("instance_id")), status);
        }
        JsonNode remaining = root.get("remaining_pending_character_interaction"); Remaining pending;
        if (remaining == null || remaining.isNull()) { pending = new Remaining(remaining == null ? Presence.MISSING : Presence.NULL, null); }
        else { StrictJson.require(remaining.isObject(), "remaining pending object required"); pending = new Remaining(Presence.VALUE, signedId(remaining.get("instance_id"))); }
        JsonNode wrapper = root.get("interaction_instance_id"); Integer wrapperId = wrapper == null || wrapper.isNull() ? null : signedId(wrapper);
        return new Response(Presence.VALUE, selected, bool(root.get("accepted")), bool(root.get("paused")), outcome, pending, wrapperId, bool(root.get("acknowledged")), actual);
    }

    public static byte[] encodeAssessment(Assessment value) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.pending-interaction-response-assessment/v1"); row.put("origin", lower(value.origin()));
        row.put("command_acknowledged", lower(value.commandAcknowledged()));
        if (value.replyAcceptArgument() == null) { row.putNull("reply_accept_argument"); } else { row.put("reply_accept_argument", value.replyAcceptArgument()); }
        row.put("original_pending_advanced_in_response", value.originalPendingAdvancedInResponse()); row.put("legacy_capture_would_mark_advanced", value.legacyCaptureWouldMarkAdvanced());
        var gaps = row.putArray("gaps"); value.gaps().forEach(gap -> gaps.add(lower(gap)));
        if (value.error() == null) { row.putNull("error"); } else { ObjectNode error = StrictJson.object(); error.put("type", value.error().type()); error.put("message", value.error().message()); row.set("error", error); }
        row.put("original_sha256", value.originalSha256()); row.put("replay_allowed", false); row.put("material_effects_verified", false);
        return StrictJson.canonical(row, 16_384);
    }
    private static int signedId(JsonNode node) { int result = (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); id(result); return result; }
    private static BooleanField absentBoolean() { return new BooleanField(Presence.MISSING, null); }
    private static BooleanField bool(JsonNode node) {
        if (node == null || node.isNull()) { return new BooleanField(node == null ? Presence.MISSING : Presence.NULL, null); }
        StrictJson.require(node.isBoolean(), "exact receipt boolean required"); return new BooleanField(Presence.VALUE, node.booleanValue());
    }
    private static String lower(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
