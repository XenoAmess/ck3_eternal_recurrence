package org.xar.ck3.control.application.planning.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.StrictJson;

/** Initial automation history DATA only. It contains no Game, episode, character or observed result. */
public final class FamilyInitialData {
    private FamilyInitialData() { }
    public enum History { ABSENT, EMPTY }
    public record Body(Slot slot, History history) {
        public Body { requireSlot(slot); Objects.requireNonNull(history); }
    }
    public record Documents(Body family, Body childMatrilineal, Body defaultMarriage) {
        public Documents {
            Objects.requireNonNull(family); Objects.requireNonNull(childMatrilineal); Objects.requireNonNull(defaultMarriage);
            StrictJson.require(family.slot() == Slot.FAMILY && childMatrilineal.slot() == Slot.CHILD_MATRILINEAL
                    && defaultMarriage.slot() == Slot.DEFAULT_MARRIAGE, "initial family documents must retain their three exact slots");
        }
        public List<Body> bodies() { return List.of(family, childMatrilineal, defaultMarriage); }
        public Body body(Slot slot) {
            requireSlot(slot);
            return switch (slot) {
                case FAMILY -> family;
                case CHILD_MATRILINEAL -> childMatrilineal;
                case DEFAULT_MARRIAGE -> defaultMarriage;
                default -> throw new IllegalArgumentException("not an initial family DATA slot");
            };
        }
    }
    /** Deliberate initial value, never a fallback for a missing or unreadable existing domain. */
    public static Documents fresh() {
        return new Documents(new Body(Slot.FAMILY, History.ABSENT), new Body(Slot.CHILD_MATRILINEAL, History.ABSENT),
                new Body(Slot.DEFAULT_MARRIAGE, History.ABSENT));
    }
    public static byte[] encode(Body body) {
        Objects.requireNonNull(body);
        ObjectNode value = StrictJson.object().put("schema", FamilyDomainSource.schema(body.slot()));
        value.putNull("pending"); value.putNull("resolved");
        if (body.history() == History.EMPTY) value.putArray("episode_history");
        byte[] bytes = StrictJson.canonical(value, ContinuityJson.DOMAIN_MAX_BYTES);
        FamilyDomainSource.validate(body.slot(), bytes);
        return bytes;
    }
    /** This initial-value codec rejects existing transaction/history content; resume uses the original domain codec. */
    public static Body decode(Slot slot, byte[] bytes) {
        requireSlot(slot); Objects.requireNonNull(bytes);
        JsonNode parsed = StrictJson.parse(bytes, ContinuityJson.DOMAIN_MAX_BYTES);
        StrictJson.require(parsed.isObject(), "initial family DATA must be an object");
        boolean history = parsed.has("episode_history");
        ObjectNode value = StrictJson.object(parsed, history ? Set.of("schema", "pending", "resolved", "episode_history")
                : Set.of("schema", "pending", "resolved"));
        StrictJson.require(FamilyDomainSource.schema(slot).equals(StrictJson.text(value.get("schema"))), "initial family DATA schema differs from its slot");
        StrictJson.require(value.get("pending").isNull() && value.get("resolved").isNull(), "initial family DATA requires explicit null pending and resolved");
        if (history) StrictJson.require(value.get("episode_history").isArray() && value.get("episode_history").isEmpty(),
                "initial family history must be absent or an explicit empty array");
        FamilyDomainSource.validate(slot, bytes);
        return new Body(slot, history ? History.EMPTY : History.ABSENT);
    }
    private static void requireSlot(Slot slot) {
        Objects.requireNonNull(slot);
        StrictJson.require(slot == Slot.FAMILY || slot == Slot.CHILD_MATRILINEAL || slot == Slot.DEFAULT_MARRIAGE,
                "only the three family automation DATA slots are supported");
    }
}
