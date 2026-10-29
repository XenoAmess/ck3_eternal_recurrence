package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared receive-time projection of the original native pending-interaction semantic field. */
public final class NativePendingInteraction {
    private NativePendingInteraction() { }

    /** Sender is an exact original integer; domain-specific CharacterID qualification is a later guard. */
    public record Pending(int instanceId, BigInteger senderCharacterId, boolean autoAcceptNotification) {
        public Pending {
            requireInstanceId(instanceId);
            Objects.requireNonNull(senderCharacterId);
        }
    }

    /** Native pending identity is a signed generation-bearing int32, including zero, except -1. */
    public static int requireInstanceId(int value) {
        StrictJson.require(value != -1, "pending instance must not use CK3's -1 invalid sentinel");
        return value;
    }

    /** Missing or null whole values normalize to absence; the three fields of a present object are required. */
    public static Optional<Pending> decode(JsonNode original) {
        Objects.requireNonNull(original, "a native JSON value or explicit MissingNode is required");
        if (original.isNull() || original.isMissingNode()) return Optional.empty();
        StrictJson.require(original.isObject(), "native pending_character_interaction must be an object");
        JsonNode instance = original.get("instance_id");
        JsonNode sender = original.get("sender_character_id");
        JsonNode notification = original.get("auto_accept_notification");
        StrictJson.require(instance != null && instance.isIntegralNumber() && instance.canConvertToInt(),
                "native pending_character_interaction is malformed");
        StrictJson.require(sender != null && sender.isIntegralNumber(),
                "native pending_character_interaction is malformed");
        StrictJson.require(notification != null && notification.isBoolean(),
                "native pending_character_interaction is malformed");
        try {
            return Optional.of(new Pending(instance.intValue(), sender.bigIntegerValue(), notification.booleanValue()));
        } catch (IllegalArgumentException invalidInstance) {
            throw new IllegalArgumentException("native pending_character_interaction is malformed", invalidInstance);
        }
    }

    /** The central semantic facade uses this same decoder for its receive, fingerprint and archive projections. */
    public static JsonNode normalize(JsonNode original) {
        return encode(decode(original));
    }

    /** Emits the original semantic JSON domain. Extra input metadata is discarded and source is always native. */
    public static JsonNode encode(Optional<Pending> value) {
        Objects.requireNonNull(value);
        if (value.isEmpty()) return NullNode.getInstance();
        Pending pending = value.orElseThrow();
        ObjectNode result = JsonNodeFactory.instance.objectNode();
        result.put("instance_id", pending.instanceId());
        result.put("sender_character_id", pending.senderCharacterId());
        result.put("auto_accept_notification", pending.autoAcceptNotification());
        result.put("source", "native");
        return result;
    }
}
