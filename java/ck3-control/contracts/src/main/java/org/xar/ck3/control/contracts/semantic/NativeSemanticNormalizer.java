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
    public static final String FLORIN_SCHEMA="ck3_1210_full_state_v1";
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
        boolean florin=florinState(raw);
        ObjectNode result = raw.deepCopy();
        result.put("format_version", 1); result.put("snapshot_id", snapshotId); result.put("revision", nativeRevision);
        result.set("history", raw.path("history").isArray() ? raw.path("history").deepCopy() : JSON.arrayNode());
        result.set("active_event", NativeActiveEvent.normalize(input(raw, "active_event"), "native"));
        result.set("one_life_settlement", NativeOneLifeSettlement.normalize(input(raw, "one_life_settlement")));
        result.set("played_character",florin
                ?NativePlayedCharacter.normalizeFlorin(raw.path("played_character"),nativeRevision,raw.path("date_raw"))
                :NativePlayedCharacter.normalize(raw.path("played_character"),nativeRevision,raw.path("date_raw")));
        for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values())
            result.set(resource.wire(), NativePlayedResources.normalize(input(raw, resource.wire()), resource));
        result.set("pending_character_interaction", NativePendingInteraction.normalize(input(raw, "pending_character_interaction")));
        if (raw.path("top_exclusive_modal_choice_hint") instanceof ObjectNode modal) {
            ObjectNode stable = modal.deepCopy(); stable.remove("pump_epoch"); stable.remove("thread_id");
            result.set("top_exclusive_modal_choice_hint", stable);
        }
        return new Canonical(result);
    }
    private static boolean florinState(ObjectNode raw) {
        JsonNode marker=raw.get("schema");
        if(marker!=null&&marker.isTextual()&&FLORIN_SCHEMA.equals(marker.textValue())) {
            NativePlayedCharacter.requireFlorinIdentity(raw,FLORIN_SCHEMA);
            JsonNode played=raw.get("played_character");
            if(played!=null&&!played.isNull()) {
                NativePlayedCharacter.requireFlorinIdentity(played,NativePlayedCharacter.FLORIN_SCHEMA);
                for(String field:java.util.List.of("game_version","adapter_id","backend"))
                    StrictJson.require(raw.path(field).textValue().equals(played.path(field).textValue()),"Florin actor/root profile mismatch");
                StrictJson.require(raw.path("executable_sha256").textValue().equalsIgnoreCase(played.path("executable_sha256").textValue()),
                        "Florin actor/root executable mismatch");
            }
            if(org.xar.ck3.control.contracts.ExactCk3Build.CK3_1210_STEAM_26757580.matches(
                    raw.path("game_version").textValue(),raw.path("executable_sha256").textValue())) {
                StrictJson.require(raw.has("active_event")&&raw.path("active_event").isNull(),
                        "hotfix initial Full profile requires an explicit null active_event");
                for(String field:java.util.List.of("active_wars","player_armies"))
                    StrictJson.require(raw.path(field).isArray()&&raw.path(field).isEmpty(),
                            "hotfix initial Full profile requires explicit empty "+field);
            }
            return true;
        }
        // Historical unknown root metadata remains transparent. A Florin actor cannot escape its explicit root branch.
        JsonNode actor=raw.path("played_character"),actorMarker=actor.path("schema");
        StrictJson.require(!actorMarker.isTextual()||!NativePlayedCharacter.FLORIN_SCHEMA.equals(actorMarker.textValue()),
                "Florin actor marker requires its explicit full-state root marker");
        return false;
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
