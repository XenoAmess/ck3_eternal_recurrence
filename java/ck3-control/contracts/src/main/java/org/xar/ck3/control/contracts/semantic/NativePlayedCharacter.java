package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Shared receive projection for fingerprint, Driver and replay. Public actor IDs follow the actual native signed-int32 wire;
 * this intentionally fixes legacy Python's nonnegative narrowing. Nested leaf domains retain their independent rules. */
public final class NativePlayedCharacter {
    private static final BigInteger STRESS_MAXIMUM = BigInteger.valueOf(Integer.MAX_VALUE);
    private NativePlayedCharacter() { }

    private record Heir(boolean hasHeir, Optional<BigInteger> characterId) {
        private Heir {
            Objects.requireNonNull(characterId); need(hasHeir == characterId.isPresent(), "heir pair differs");
        }
    }
    private record Relations(Optional<BigInteger> betrothedId, Optional<BigInteger> primarySpouseId,
            List<BigInteger> spouseIds) {
        private Relations {
            Objects.requireNonNull(betrothedId); Objects.requireNonNull(primarySpouseId); spouseIds = List.copyOf(spouseIds);
            need(new HashSet<>(spouseIds).size() == spouseIds.size(), "original spouse IDs contain duplicates");
            need(primarySpouseId.isEmpty() || spouseIds.contains(primarySpouseId.orElseThrow()),
                    "original primary spouse is not in spouse IDs");
        }
    }
    private record Played(NativeCharacterId characterId, boolean alive, OptionalInt stressPoints,
            Optional<NativePlayerEventTraitMembership.Observation> eventTraits, Optional<Heir> heir,
            Optional<Relations> relations) {
        private Played {
            Objects.requireNonNull(characterId); Objects.requireNonNull(stressPoints); Objects.requireNonNull(eventTraits);
            Objects.requireNonNull(heir); Objects.requireNonNull(relations);
        }
    }

    /** Java parameters are nonnull; original absent/null played value is JSON null. Extra original actor fields are projected away. */
    public static JsonNode normalize(JsonNode original, BigInteger nativeRevision, JsonNode dateRaw) {
        Objects.requireNonNull(original); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw);
        if (original.isMissingNode() || original.isNull()) return NullNode.instance;
        need(original instanceof ObjectNode, "native played_character must be an object");
        NativeCharacterId characterId = NativeCharacterId.fromJson(original.get("character_id"));
        JsonNode alive = original.get("alive"); need(alive != null && alive.isBoolean(), "original played alive must be boolean");
        OptionalInt stress = OptionalInt.empty();
        if (original.has("stress_points")) {
            BigInteger value = nonnegative(original.get("stress_points"), "stress_points");
            need(value.compareTo(STRESS_MAXIMUM) <= 0, "original stress_points exceeds signed int32 maximum");
            stress = OptionalInt.of(value.intValueExact());
        }
        Optional<NativePlayerEventTraitMembership.Observation> traits = original.has("event_trait_membership")
                ? Optional.of(NativePlayerEventTraitMembership.read(original.get("event_trait_membership"), characterId.asBigInteger(), nativeRevision, dateRaw))
                : Optional.empty();
        Optional<Heir> heir = Optional.empty();
        if (original.has("primary_heir_id") || original.has("has_heir")) {
            JsonNode hasHeir = original.get("has_heir"); need(hasHeir != null && hasHeir.isBoolean(), "original has_heir must be boolean");
            JsonNode id = original.get("primary_heir_id");
            Optional<BigInteger> actualId;
            if (hasHeir.booleanValue()) actualId = Optional.of(nonnegative(id, "primary_heir_id"));
            else {
                need(id == null || id.isNull(), "original primary_heir_id conflicts with has_heir");
                actualId = Optional.empty();
            }
            heir = Optional.of(new Heir(hasHeir.booleanValue(), actualId));
        }
        Optional<Relations> relations = Optional.empty();
        boolean betrothed = original.has("betrothed_id"), primary = original.has("primary_spouse_id"), spouses = original.has("spouse_ids");
        if (betrothed || primary || spouses) {
            need(betrothed && primary && spouses, "original relationship state is incomplete");
            JsonNode ids = original.get("spouse_ids"); need(ids.isArray(), "original spouse_ids must be an array");
            List<BigInteger> values = new ArrayList<>();
            for (JsonNode id : ids) values.add(nonnegative(id, "spouse_ids item"));
            relations = Optional.of(new Relations(nullableId(original.get("betrothed_id"), "betrothed_id"),
                    nullableId(original.get("primary_spouse_id"), "primary_spouse_id"), values));
        }
        return toJson(new Played(characterId, alive.booleanValue(), stress, traits, heir, relations));
    }

    private static ObjectNode toJson(Played value) {
        ObjectNode row = JsonNodeFactory.instance.objectNode();
        row.set("character_id", value.characterId().toJson());
        row.put("alive", value.alive()).put("source", "native");
        value.stressPoints().ifPresent(stress -> row.put("stress_points", stress));
        value.eventTraits().ifPresent(traits -> row.set("event_trait_membership", NativePlayerEventTraitMembership.toJson(traits)));
        value.heir().ifPresent(heir -> {
            if (heir.characterId().isPresent()) row.put("primary_heir_id", heir.characterId().orElseThrow()); else row.putNull("primary_heir_id");
            row.put("has_heir", heir.hasHeir());
        });
        value.relations().ifPresent(relations -> {
            if (relations.betrothedId().isPresent()) row.put("betrothed_id", relations.betrothedId().orElseThrow()); else row.putNull("betrothed_id");
            if (relations.primarySpouseId().isPresent()) row.put("primary_spouse_id", relations.primarySpouseId().orElseThrow()); else row.putNull("primary_spouse_id");
            var ids = row.putArray("spouse_ids"); relations.spouseIds().forEach(ids::add);
        });
        return row;
    }
    private static Optional<BigInteger> nullableId(JsonNode value, String field) {
        need(value != null, "required nullable original relationship field missing");
        return value.isNull() ? Optional.empty() : Optional.of(nonnegative(value, field));
    }
    private static BigInteger nonnegative(JsonNode value, String field) {
        need(value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0,
                "original " + field + " must be a nonnegative integer token, not bool/float/string");
        return value.bigIntegerValue();
    }
    private static void need(boolean value, String message) { StrictJson.require(value, message); }
}
