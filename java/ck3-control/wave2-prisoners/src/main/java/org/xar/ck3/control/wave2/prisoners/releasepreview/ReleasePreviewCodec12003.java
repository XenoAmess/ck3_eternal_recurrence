package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Exact leaf codec matching normalize_prisoner_release_preview_12003. */
public final class ReleasePreviewCodec12003 {
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> UNAVAILABLE = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "unavailable_reason");
    private static final Set<String> AVAILABLE = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "snapshot_id", "public_revision", "native_revision",
            "proof_epoch", "date_raw", "definition", "payload_shape", "roles",
            "unconditional_prisoner_release", "can_send", "costs", "acceptance", "readiness",
            "option_keys", "selected_option_mask_bits", "puppet_or_actor_character_id");
    private static final Set<String> READINESS = Set.of("definition_ready", "actor_ready", "recipient_ready",
            "finalized_context_ready", "can_send_ready", "costs_ready", "acceptance_ready", "same_frame_ready");

    private ReleasePreviewCodec12003() { }

    public static ReleasePreview12003 decode(byte[] raw, FrameBinding binding) {
        return fromNode(StrictJson.parse(raw, MAX_BYTES), binding);
    }

    public static ReleasePreview12003 fromNode(JsonNode node, FrameBinding binding) {
        Objects.requireNonNull(binding, "binding");
        StrictJson.require(node != null && node.isObject(), "private release object required");
        StrictJson.trueValue(node.get("private_build"));
        StrictJson.trueValue(node.get("read_only"));
        falseValue(node.get("advertised"));
        falseValue(node.get("action_surface_present"));
        String status = StrictJson.text(node.get("status"));
        if ("unavailable".equals(status)) {
            ObjectNode value = StrictJson.object(node, UNAVAILABLE);
            return new ReleasePreview12003.Unavailable(StrictJson.text(value.get("unavailable_reason")));
        }
        StrictJson.require("available".equals(status), "unknown release preview status");
        ObjectNode value = StrictJson.object(node, AVAILABLE);
        StrictJson.require(binding.snapshotId().equals(StrictJson.text(value.get("snapshot_id")))
                && integer(value.get("public_revision")).equals(binding.nativeRevision())
                && integer(value.get("native_revision")).equals(binding.nativeRevision())
                && StrictJson.integer(value.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)
                == binding.dateRaw(), "release preview differs from its paused native frame");
        BigInteger proofEpoch = integer(value.get("proof_epoch"));
        var definition = ReleasePreviewValues12003.readDefinition(value.get("definition"));
        var roles = ReleasePreviewValues12003.readRoles(value.get("roles"));
        StrictJson.require(roles.equals(binding.roles())
                && StrictJson.integer(value.get("puppet_or_actor_character_id"), 1,
                        ReleasePreviewValues12003.UINT32_MAX) == binding.playerCharacterId(),
                "release roles differ from actual player custody");
        StrictJson.require("two_role_all_release_options_off".equals(StrictJson.text(value.get("payload_shape"))),
                "ordinary release payload required");
        StrictJson.trueValue(value.get("unconditional_prisoner_release"));
        StrictJson.integer(value.get("selected_option_mask_bits"), 0, 0);
        JsonNode options = value.get("option_keys");
        StrictJson.require(options != null && options.isArray()
                && options.size() == ReleasePreviewValues12003.optionKeys().size(), "thirteen options required");
        for (int index = 0; index < options.size(); index++) {
            StrictJson.require(ReleasePreviewValues12003.optionKeys().get(index)
                    .equals(StrictJson.text(options.get(index))), "release option order differs");
        }
        boolean canSend = booleanValue(value.get("can_send"));
        var costs = ReleasePreviewValues12003.readCosts(value.get("costs"));
        ObjectNode acceptance = StrictJson.object(value.get("acceptance"),
                Set.of("kind", "auto_accept", "would_accept_now"));
        StrictJson.require("auto_accept".equals(StrictJson.text(acceptance.get("kind"))),
                "compact native auto-accept required");
        StrictJson.trueValue(acceptance.get("auto_accept"));
        StrictJson.trueValue(acceptance.get("would_accept_now"));
        ObjectNode readiness = StrictJson.object(value.get("readiness"), READINESS);
        for (String key : READINESS) { StrictJson.trueValue(readiness.get(key)); }
        return new ReleasePreview12003.Available(binding, proofEpoch, definition, canSend, costs);
    }

    public static byte[] encode(ReleasePreview12003 preview) {
        return StrictJson.canonical(toNode(preview), MAX_BYTES);
    }

    public static ObjectNode toNode(ReleasePreview12003 preview) {
        Objects.requireNonNull(preview, "preview");
        ObjectNode value = StrictJson.object();
        value.put("private_build", true);
        value.put("read_only", true);
        value.put("advertised", false);
        value.put("action_surface_present", false);
        if (preview instanceof ReleasePreview12003.Unavailable unavailable) {
            value.put("status", "unavailable");
            value.put("unavailable_reason", unavailable.reason());
            return value;
        }
        ReleasePreview12003.Available available = (ReleasePreview12003.Available) preview;
        FrameBinding frame = available.binding();
        value.put("status", "available");
        value.put("snapshot_id", frame.snapshotId());
        value.put("public_revision", frame.nativeRevision());
        value.put("native_revision", frame.nativeRevision());
        value.put("proof_epoch", available.proofEpoch());
        value.put("date_raw", frame.dateRaw());
        value.set("definition", ReleasePreviewValues12003.writeDefinition(available.definition()));
        value.put("payload_shape", "two_role_all_release_options_off");
        value.set("roles", ReleasePreviewValues12003.writeRoles(frame.roles()));
        value.put("puppet_or_actor_character_id", frame.playerCharacterId());
        value.put("unconditional_prisoner_release", true);
        ArrayNode options = value.putArray("option_keys");
        ReleasePreviewValues12003.optionKeys().forEach(options::add);
        value.put("selected_option_mask_bits", 0);
        value.put("can_send", available.canSend());
        value.set("costs", ReleasePreviewValues12003.writeCosts(available.costs()));
        ObjectNode acceptance = value.putObject("acceptance");
        acceptance.put("kind", "auto_accept");
        acceptance.put("auto_accept", true);
        acceptance.put("would_accept_now", true);
        ObjectNode readiness = value.putObject("readiness");
        for (String key : READINESS) { readiness.put(key, true); }
        return value;
    }

    private static BigInteger integer(JsonNode node) {
        return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX);
    }

    private static boolean booleanValue(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual release JSON boolean required");
        return node.booleanValue();
    }

    private static void falseValue(JsonNode node) {
        StrictJson.require(!booleanValue(node), "private release envelope must retain false");
    }
}
