package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared seven-field native projection. Raw and normalized trees are distinct DATA domains. */
public final class NativeSemanticNormalizer {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final Set<String> OWNED = Set.of("format_version", "snapshot_id", "revision", "history",
            "active_event", "one_life_settlement", "played_character", "played_character_gold",
            "played_character_prestige", "played_character_piety", "pending_character_interaction",
            "top_exclusive_modal_choice_hint");
    private NativeSemanticNormalizer() { }

    public static final class Raw {
        private final ObjectNode original;
        private Raw(ObjectNode original) { this.original = original.deepCopy(); }
    }
    public static final class Canonical {
        private final ObjectNode semantic;
        private Canonical(ObjectNode semantic) { this.semantic = semantic.deepCopy(); }
        public ObjectNode semantic() { return semantic.deepCopy(); }
    }
    /** Only an original native tree belongs here; no Canonical overload exists. */
    public static Raw original(ObjectNode original) { return new Raw(Objects.requireNonNull(original)); }
    public static Set<String> ownedFields() { return OWNED; }

    public static Canonical normalize(Raw original, String snapshotId, BigInteger nativeRevision) {
        Objects.requireNonNull(original); Objects.requireNonNull(nativeRevision);
        StrictJson.require(snapshotId != null && !snapshotId.isEmpty() && nativeRevision.signum() >= 0,
                "actual nonempty snapshot identity and nonnegative native revision required");
        ObjectNode raw = original.original;
        ObjectNode result = raw.deepCopy();
        result.put("format_version", 1); result.put("snapshot_id", snapshotId); result.put("revision", nativeRevision);
        result.set("history", raw.path("history").isArray() ? raw.path("history").deepCopy() : JSON.arrayNode());
        result.set("active_event", NativeActiveEvent.normalize(input(raw, "active_event"), "native"));
        result.set("one_life_settlement", NativeOneLifeSettlement.normalize(input(raw, "one_life_settlement")));
        result.set("played_character", NativePlayedCharacter.normalize(raw.path("played_character"),
                nativeRevision, raw.path("date_raw")));
        for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values())
            result.set(resource.wire(), NativePlayedResources.normalize(input(raw, resource.wire()), resource));
        result.set("pending_character_interaction", NativePendingInteraction.normalize(input(raw, "pending_character_interaction")));
        if (raw.path("top_exclusive_modal_choice_hint") instanceof ObjectNode modal) {
            ObjectNode stable = modal.deepCopy(); stable.remove("pump_epoch"); stable.remove("thread_id");
            result.set("top_exclusive_modal_choice_hint", stable);
        }
        return new Canonical(result);
    }
    private static JsonNode input(ObjectNode raw, String field) { return pythonFloatingPoint(raw.path(field), 0); }

    /** Python json.loads uses binary64 for float tokens; integer identity tokens never traverse double. */
    private static JsonNode pythonFloatingPoint(JsonNode original, int depth) {
        StrictJson.require(depth <= 64, "bounded native semantic input required");
        if (original.isFloatingPointNumber()) {
            double value = original.doubleValue();
            return JSON.numberNode(value);
        }
        if (original instanceof ObjectNode object) {
            ObjectNode result = JSON.objectNode();
            object.properties().forEach(entry -> result.set(entry.getKey(), pythonFloatingPoint(entry.getValue(), depth + 1)));
            return result;
        }
        if (original.isArray()) {
            var result = JSON.arrayNode(); original.forEach(value -> result.add(pythonFloatingPoint(value, depth + 1))); return result;
        }
        return original.deepCopy();
    }
}
