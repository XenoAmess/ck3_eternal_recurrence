package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.Acceptance;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.AutoAccept;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.Available;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.NativeAnswer;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.NotEvaluatedUnsendable;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.OptionsNotRetained;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.Unavailable;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.Roles;

/** Exact 1.20.0.3 negotiated preview wire; constants are not action qualifications. */
public final class NegotiatedPreviewCodec {
    public static final int MAXIMUM_BYTES = 16_384;
    private static final Set<String> ENVELOPE = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "requested_option_mask_bits");
    private static final Set<String> AVAILABLE = union(ENVELOPE, Set.of("snapshot_id", "public_revision",
            "native_revision", "proof_epoch", "date_raw", "definition", "payload_shape", "roles",
            "puppet_or_actor_character_id", "option_keys", "selected_option_mask_bits", "can_send",
            "costs", "acceptance", "readiness"));
    private static final Set<String> READINESS = Set.of("definition_ready", "actor_ready", "recipient_ready",
            "finalized_context_ready", "can_send_ready", "costs_ready", "acceptance_ready", "same_frame_ready");

    private NegotiatedPreviewCodec() { }

    public static NegotiatedPreview12003 decode(byte[] raw, FrameBinding frame, int requestedMask) {
        return decode(StrictJson.parse(raw, MAXIMUM_BYTES), frame, requestedMask);
    }

    /** A declared nested leaf projection; the enclosing SDK root remains extensible. */
    public static NegotiatedPreview12003 decode(JsonNode raw, FrameBinding frame, int requestedMask) {
        java.util.Objects.requireNonNull(frame, "frame");
        NegotiatedPreview12003.requestedMask(requestedMask);
        StrictJson.require(raw != null && raw.isObject(), "negotiated preview object required");
        StrictJson.trueValue(raw.get("private_build"));
        StrictJson.trueValue(raw.get("read_only"));
        falseValue(raw.get("advertised"));
        falseValue(raw.get("action_surface_present"));
        equalInteger(raw.get("requested_option_mask_bits"), requestedMask);
        String status = StrictJson.text(raw.get("status"));
        if (status.equals("unavailable")) {
            String reason = StrictJson.text(raw.get("unavailable_reason"));
            if (reason.equals("requested_release_options_not_retained")) {
                StrictJson.object(raw, union(ENVELOPE, Set.of("unavailable_reason", "observed_option_mask_bits")));
                return new OptionsNotRetained(requestedMask,
                        (int) StrictJson.integer(raw.get("observed_option_mask_bits"), 0, NegotiatedPreview12003.MAXIMUM_MASK));
            }
            StrictJson.object(raw, union(ENVELOPE, Set.of("unavailable_reason")));
            return new Unavailable(requestedMask, reason);
        }
        StrictJson.require(status.equals("available"), "available or unavailable status required");
        ObjectNode value = StrictJson.object(raw, AVAILABLE);
        StrictJson.require(StrictJson.text(value.get("snapshot_id")).equals("native:" + frame.nativeRevision()),
                "native snapshot differs from frame");
        StrictJson.require(StrictJson.integer(value.get("public_revision"), java.math.BigInteger.ONE,
                StrictJson.UINT64_MAX).equals(frame.nativeRevision()), "public revision differs from frame");
        StrictJson.require(StrictJson.integer(value.get("native_revision"), java.math.BigInteger.ONE,
                StrictJson.UINT64_MAX).equals(frame.nativeRevision()), "native revision differs from frame");
        equalInteger(value.get("date_raw"), frame.dateRaw());
        Roles roles = ReleasePreviewValues12003.readRoles(value.get("roles"));
        StrictJson.require(roles.actorCharacterId() == frame.playerCharacterId()
                && roles.recipientCharacterId() == frame.prisonerCharacterId(), "custody roles differ from frame");
        equalInteger(value.get("puppet_or_actor_character_id"), frame.playerCharacterId());
        StrictJson.require(StrictJson.text(value.get("payload_shape")).equals("two_role_selected_release_options"),
                "selected release payload shape required");
        readOptionKeys(value.get("option_keys"), true);
        equalInteger(value.get("selected_option_mask_bits"), requestedMask);
        boolean canSend = booleanValue(value.get("can_send"));
        Acceptance acceptance = readAcceptance(value.get("acceptance"), canSend);
        ObjectNode readiness = StrictJson.object(value.get("readiness"), READINESS);
        for (String key : READINESS) {
            if (key.equals("acceptance_ready")) {
                StrictJson.require(booleanValue(readiness.get(key)) == canSend, "acceptance readiness differs from CanSend");
            } else { StrictJson.trueValue(readiness.get(key)); }
        }
        return new Available(frame, StrictJson.integer(value.get("proof_epoch"), java.math.BigInteger.ONE,
                StrictJson.UINT64_MAX), ReleasePreviewValues12003.readDefinition(value.get("definition")),
                requestedMask, canSend, ReleasePreviewValues12003.readCosts(value.get("costs")), acceptance);
    }

    public static List<ReleaseOption> decodeRequestedOptions(byte[] raw) {
        List<ReleaseOption> options = readOptionKeys(StrictJson.parse(raw, MAXIMUM_BYTES), false);
        NegotiatedPreview12003.releaseOptionMask(options);
        return options;
    }

    public static byte[] encode(NegotiatedPreview12003 preview) {
        return StrictJson.canonical(toJson(preview), MAXIMUM_BYTES);
    }

    public static ObjectNode toJson(NegotiatedPreview12003 preview) {
        java.util.Objects.requireNonNull(preview, "preview");
        ObjectNode out = StrictJson.object();
        out.put("private_build", true).put("read_only", true).put("advertised", false)
                .put("action_surface_present", false).put("requested_option_mask_bits", preview.requestedOptionMaskBits());
        if (preview instanceof Unavailable unavailable) {
            return out.put("status", "unavailable").put("unavailable_reason", unavailable.unavailableReason());
        }
        if (preview instanceof OptionsNotRetained mismatch) {
            return out.put("status", "unavailable").put("unavailable_reason", mismatch.unavailableReason())
                    .put("observed_option_mask_bits", mismatch.observedOptionMaskBits());
        }
        Available value = (Available) preview;
        FrameBinding frame = value.frame();
        out.put("status", "available").put("snapshot_id", "native:" + frame.nativeRevision())
                .put("public_revision", frame.nativeRevision()).put("native_revision", frame.nativeRevision())
                .put("proof_epoch", value.proofEpoch()).put("date_raw", frame.dateRaw())
                .put("payload_shape", "two_role_selected_release_options")
                .put("puppet_or_actor_character_id", frame.playerCharacterId())
                .put("selected_option_mask_bits", value.requestedOptionMaskBits()).put("can_send", value.canSend());
        out.set("definition", ReleasePreviewValues12003.writeDefinition(value.definition()));
        out.set("roles", ReleasePreviewValues12003.writeRoles(new Roles(frame.playerCharacterId(), frame.prisonerCharacterId())));
        var options = out.putArray("option_keys");
        ReleasePreviewValues12003.optionKeys().forEach(options::add);
        out.set("costs", ReleasePreviewValues12003.writeCosts(value.costs()));
        out.set("acceptance", writeAcceptance(value.acceptance()));
        ObjectNode readiness = out.putObject("readiness");
        for (String key : READINESS) { readiness.put(key, !key.equals("acceptance_ready") || value.canSend()); }
        return out;
    }

    static boolean booleanValue(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean required");
        return node.booleanValue();
    }

    private static Acceptance readAcceptance(JsonNode value, boolean canSend) {
        StrictJson.require(value != null && value.isObject(), "acceptance object required");
        boolean autoAccept = booleanValue(value.get("auto_accept"));
        if (!canSend) {
            StrictJson.object(value, Set.of("kind", "auto_accept"));
            StrictJson.require(StrictJson.text(value.get("kind")).equals("not_evaluated_unsendable"),
                    "unsendable offer requires an unevaluated native answer");
            return new NotEvaluatedUnsendable(autoAccept);
        }
        if (autoAccept) {
            StrictJson.object(value, Set.of("kind", "auto_accept", "would_accept_now"));
            StrictJson.require(StrictJson.text(value.get("kind")).equals("auto_accept"), "native autoaccept kind required");
            StrictJson.trueValue(value.get("would_accept_now"));
            return new AutoAccept();
        }
        StrictJson.object(value, Set.of("kind", "auto_accept", "raw_scale", "recipient_acceptance_score_raw",
                "recipient_answer_status_raw", "would_accept_now"));
        StrictJson.require(StrictJson.text(value.get("kind")).equals("native_answer"), "native answer kind required");
        equalInteger(value.get("raw_scale"), 100_000);
        NativeAnswer answer = new NativeAnswer(StrictJson.integer(value.get("recipient_acceptance_score_raw"),
                Long.MIN_VALUE, Long.MAX_VALUE), NegotiatedPreview12003.AnswerStatus.fromRaw(
                        (int) StrictJson.integer(value.get("recipient_answer_status_raw"), 0, 2)));
        StrictJson.require(booleanValue(value.get("would_accept_now")) == answer.wouldAcceptNow(),
                "native answer differs from would-accept input");
        return answer;
    }

    public static ObjectNode writeAcceptance(Acceptance value) {
        ObjectNode out = StrictJson.object().put("auto_accept", value.autoAccept());
        if (value instanceof NotEvaluatedUnsendable) { return out.put("kind", "not_evaluated_unsendable"); }
        if (value instanceof AutoAccept) { return out.put("kind", "auto_accept").put("would_accept_now", true); }
        NativeAnswer answer = (NativeAnswer) value;
        return out.put("kind", "native_answer").put("raw_scale", 100_000)
                .put("recipient_acceptance_score_raw", answer.recipientAcceptanceScoreRaw())
                .put("recipient_answer_status_raw", answer.recipientAnswerStatus().raw())
                .put("would_accept_now", answer.wouldAcceptNow());
    }

    private static List<ReleaseOption> readOptionKeys(JsonNode node, boolean complete) {
        StrictJson.require(node != null && node.isArray(), "option keys array required");
        List<ReleaseOption> options = new ArrayList<>();
        for (JsonNode key : node) { options.add(ReleaseOption.fromKey(StrictJson.text(key))); }
        if (complete) {
            StrictJson.require(options.equals(List.of(ReleaseOption.values())), "all thirteen option keys in native order required");
        }
        return List.copyOf(options);
    }

    private static void equalInteger(JsonNode node, long value) {
        StrictJson.require(StrictJson.integer(node, value, value) == value, "integer differs from selected frame");
    }

    private static void falseValue(JsonNode value) {
        StrictJson.require(!booleanValue(value), "actual JSON false required");
    }

    private static Set<String> union(Set<String> first, Set<String> second) {
        Set<String> result = new HashSet<>(first);
        result.addAll(second);
        return Set.copyOf(result);
    }
}
