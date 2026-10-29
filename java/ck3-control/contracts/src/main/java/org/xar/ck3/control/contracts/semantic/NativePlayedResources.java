package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact shared receive contract for the player's three signed native resources. */
public final class NativePlayedResources {
    public static final int SCALE = 100_000;
    private static final Set<String> AMOUNT_FIELDS = Set.of("raw", "scale");

    private NativePlayedResources() { }

    public enum Resource {
        GOLD("played_character_gold"),
        PRESTIGE("played_character_prestige"),
        PIETY("played_character_piety");

        private final String wire;

        Resource(String wire) { this.wire = wire; }

        public String wire() { return wire; }
    }

    public sealed interface Field permits Missing, NullValue, Amount { }

    /** The enclosing object did not contain this resource field. */
    public record Missing() implements Field { }

    /** The enclosing object explicitly contained JSON null. */
    public record NullValue() implements Field { }

    /** No floating conversion, unit conversion, or rounding occurs in this model. */
    public record Amount(long raw) implements Field {
        public int scale() { return SCALE; }
    }

    public record Fields(Field gold, Field prestige, Field piety) {
        public Fields {
            Objects.requireNonNull(gold, "gold field");
            Objects.requireNonNull(prestige, "prestige field");
            Objects.requireNonNull(piety, "piety field");
        }

        public Field resource(Resource resource) {
            return switch (Objects.requireNonNull(resource, "resource")) {
                case GOLD -> gold;
                case PRESTIGE -> prestige;
                case PIETY -> piety;
            };
        }
    }

    /** Java null and Jackson MissingNode mean absence; neither means JSON null. */
    public static Field decode(JsonNode value) {
        if (value == null || value.isMissingNode()) { return new Missing(); }
        if (value.isNull()) { return new NullValue(); }
        ObjectNode object = StrictJson.object(value, AMOUNT_FIELDS);
        long raw = StrictJson.integer(object.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE);
        StrictJson.integer(object.get("scale"), SCALE, SCALE);
        return new Amount(raw);
    }

    /** A missing sentinel must be omitted by an enclosing writer, never serialized as null. */
    public static JsonNode encode(Field field) {
        return switch (Objects.requireNonNull(field, "resource field")) {
            case Missing ignored -> MissingNode.getInstance();
            case NullValue ignored -> NullNode.getInstance();
            case Amount amount -> StrictJson.object().put("raw", amount.raw()).put("scale", SCALE);
        };
    }

    /** Original state.get projection; raw decode retains missing/null separately. */
    public static JsonNode normalize(JsonNode original, Resource resource) {
        Objects.requireNonNull(resource, "resource");
        Field decoded = decode(original);
        return decoded instanceof Missing ? NullNode.getInstance() : encode(decoded);
    }

    public static Fields decodeState(JsonNode state) {
        StrictJson.require(state != null && state.isObject(), "native semantic state object required");
        return new Fields(decode(state.get(Resource.GOLD.wire())),
                decode(state.get(Resource.PRESTIGE.wire())),
                decode(state.get(Resource.PIETY.wire())));
    }

    /** Writes only these fields while preserving every unrelated semantic state field. */
    public static void writeFields(ObjectNode state, Fields resources) {
        Objects.requireNonNull(state, "state");
        Objects.requireNonNull(resources, "resources");
        for (Resource resource : Resource.values()) {
            Field field = resources.resource(resource);
            if (field instanceof Missing) {
                state.remove(resource.wire());
            } else {
                state.set(resource.wire(), encode(field));
            }
        }
    }
}
