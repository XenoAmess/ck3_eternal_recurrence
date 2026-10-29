package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.eventtraits.EventEffectPhase;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** The existing Driver event-selection material shape, constructed only from independent original observations. */
public final class EventSelectionMaterial {
    private EventSelectionMaterial() { }
    private static final BigInteger I32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger I64_MIN = BigInteger.valueOf(Long.MIN_VALUE), I64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private enum Scalar {
        STRESS("stress", "stress_points", null), GOLD("gold", "gold_raw", "played_character_gold"),
        PRESTIGE("prestige", "prestige_raw", "played_character_prestige");
        private final String key, field, resource;
        Scalar(String key, String field, String resource) { this.key = key; this.field = field; this.resource = resource; }
    }
    public static ObjectNode selection(ActionCommand command, NativeEffectSnapshots.Pair pair, JsonNode additionalMaterial) {
        StrictJson.require(command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}"), "canonical event option operation required");
        int number = Integer.parseInt(command.operation().value().substring("select-event-option-".length()));
        ObjectNode before = EffectJson.object(pair.before().semantic()), after = EffectJson.object(pair.after().semantic());
        StrictJson.trueValue(before.get("paused")); StrictJson.trueValue(after.get("paused")); StrictJson.trueValue(after.get("map_ready"));
        // This method formats already-proved old-instance advancement. It cannot supply the proof itself.
        ObjectNode oldEvent = EffectJson.object(before.get("active_event"));
        JsonNode next = after.get("active_event");
        StrictJson.require(next != null && (next.isNull() || next.isObject()), "explicit independent active-event observation required");
        BigInteger oldInstance = EffectJson.integer(oldEvent.get("instance_id"));
        StrictJson.require(oldInstance.signum() > 0 && oldInstance.compareTo(I32_MAX) <= 0
            && (next.isNull() || !oldInstance.equals(EffectJson.integer(next.get("instance_id"))))
            && pair.before().identity().equals(command.before()) && pair.before().source().equals(command.source())
            && pair.before().sessionId().equals(command.sessionId())
            && pair.before().identity().frame().identity().dateRaw().equals(pair.after().identity().frame().identity().dateRaw()),
            "event selection material requires the independently advanced old instance in the original paused date");
        ObjectNode selected = StrictJson.object();
        selected.put("status", "event_instance_advanced").put("postcondition_verified", true)
            .put("old_event_instance_id", oldInstance).put("selected_option_number", number)
            .put("selected_native_option_index", number - 1).put("starting_snapshot_id", pair.before().identity().frame().snapshotId())
            .put("starting_revision", pair.before().identity().frame().revision()).put("ending_snapshot_id", pair.after().identity().frame().snapshotId())
            .put("ending_revision", pair.after().identity().frame().revision()).put("episode_run_id", pair.after().identity().frame().episodeRunId());
        if (next.isNull()) selected.putNull("new_event_instance_id"); else selected.put("new_event_instance_id", EffectJson.integer(next.get("instance_id")));
        ObjectNode diagnostics = EffectJson.object(before.get("diagnostics"));
        selected.put("connection_generation", EffectJson.integer(diagnostics.get("connection_generation")))
            .put("bridge_pid", EffectJson.integer(diagnostics.get("bridge_pid")));
        for (Scalar scalar : Scalar.values()) {
            selected.set("starting_played_character_" + scalar.key, scalar(before, scalar));
            selected.set("ending_played_character_" + scalar.key, scalar(after, scalar));
        }
        for (var item : List.of(new FrameLeaf("starting_played_character_event_traits", before), new FrameLeaf("ending_played_character_event_traits", after))) {
            JsonNode raw = EffectJson.object(item.frame().get("played_character")).get("event_trait_membership");
            if (raw == null) selected.putNull(item.key()); else selected.set(item.key(), raw.deepCopy());
        }
        JsonNode expected = EffectJson.object(command.arguments()).get("event_material_postcondition");
        if (expected != null && expected.isObject()) {
            String event = StrictJson.text(expected.get("event_definition_key"));
            if (Bookmark1070Material.EVENT.equals(event)) {
                Bookmark1070Material.Observation initial = Bookmark1070Material.observe(before, null, null);
                List<BigInteger> prior = initial.armies() == null ? List.of() : initial.armies().stream().map(Bookmark1070Material.Army::armyId).toList();
                selected.set("starting_bookmark1070_armies", StrictJson.parse(Bookmark1070Material.encode(initial)));
                selected.set("ending_bookmark1070_armies", StrictJson.parse(Bookmark1070Material.encode(Bookmark1070Material.observe(after, additionalMaterial, prior))));
            } else if (RiteGrowthMaterial.EVENT.equals(event)) {
                JsonNode initial = before.get("rite_growth_fulfillment_observation");
                if (initial == null) selected.putNull("starting_rite_growth_fulfillment"); else selected.set("starting_rite_growth_fulfillment", initial.deepCopy());
                selected.set("ending_rite_growth_fulfillment", StrictJson.parse(RiteGrowthMaterial.encode(RiteGrowthMaterial.observe(additionalMaterial, after))));
            }
        }
        return selected;
    }
    private record FrameLeaf(String key, ObjectNode frame) { }
    /** Missing or wrong scalar tokens retain the original unavailable observation; a boolean is never an integer. */
    private static ObjectNode scalar(ObjectNode frame, Scalar scalar) {
        JsonNode character = frame.get("played_character"), id = character == null ? null : character.get("character_id");
        JsonNode raw = scalar.resource == null ? (character == null ? null : character.get("stress_points"))
            : frame.path(scalar.resource).get("raw");
        JsonNode scale = scalar.resource == null ? null : frame.path(scalar.resource).get("scale");
        boolean available = integer(id, BigInteger.ONE, I32_MAX) && integer(raw, scalar.resource == null ? BigInteger.ZERO : I64_MIN,
            scalar.resource == null ? I32_MAX : I64_MAX) && (scalar.resource == null || integer(scale, BigInteger.valueOf(100000), BigInteger.valueOf(100000)));
        ObjectNode result = StrictJson.object().put("status", available ? "available" : "unavailable");
        if (available) result.put("character_id", id.bigIntegerValue()).put(scalar.field, raw.bigIntegerValue()).putNull("unavailable_reason");
        else result.putNull("character_id").putNull(scalar.field).put("unavailable_reason", "played_character_" + scalar.key + "_unavailable");
        if (scalar.resource != null) result.put("scale", 100000);
        return result;
    }
    private static boolean integer(JsonNode value, BigInteger minimum, BigInteger maximum) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(minimum) >= 0 && value.bigIntegerValue().compareTo(maximum) <= 0;
    }
    public static Optional<ObjectNode> evaluation(ActionCommand command, ObjectNode selection) {
        JsonNode expected = EffectJson.object(command.arguments()).get("event_material_postcondition");
        if (expected == null || expected.isNull()) return Optional.empty();
        if (PoetTraitOutcome.EVENT.equals(StrictJson.text(expected.get("event_definition_key"))) && !optionPhaseQualified(command, expected)) {
            ObjectNode unavailable = EffectJson.object(expected).deepCopy();
            unavailable.put("status", "unavailable").putNull("relation_satisfied").putNull("material_change_observed")
                .putNull("ending_value").putNull("delta").put("unavailable_reason", "event_option_phase_source_unavailable");
            return Optional.of(unavailable);
        }
        var retainedExpected = RetainedJson.object(RetainedJson.parse(StrictJson.canonical(expected, StrictJson.EXPLICIT_MAX_BYTES)));
        var retainedSelection = RetainedJson.object(RetainedJson.parse(StrictJson.canonical(selection, StrictJson.EXPLICIT_MAX_BYTES)));
        return Optional.of(EffectJson.object(StrictJson.parse(RetainedJson.encode(RegisteredEventMaterial.evaluate(retainedExpected, retainedSelection)), StrictJson.EXPLICIT_MAX_BYTES)));
    }
    private static boolean optionPhaseQualified(ActionCommand command, JsonNode expected) {
        JsonNode raw = EffectJson.object(command.arguments()).get("event_effect_phase");
        if (raw == null || !raw.isObject()) return false;
        EventEffectPhase.Phases phase;
        try { phase = EventEffectPhase.decode(StrictJson.canonical(raw)); }
        catch (IllegalArgumentException malformed) { return false; }
        JsonNode nativeIndex = expected.get("selected_native_option_index");
        if (!integer(nativeIndex, BigInteger.ZERO, BigInteger.ONE) || !PoetTraitOutcome.EVENT.equals(phase.eventDefinitionKey())
                || !command.source().exactBuild().equals(phase.source().ck3Build())
                || phase.nativeIndex() != nativeIndex.intValue() || !command.operation().value().equals("select-event-option-" + (phase.nativeIndex() + 1))) return false;
        return phase.optionAdds(phase.nativeIndex() == 0 ? EventTraitMembership.Trait.LIFESTYLE_POET : EventTraitMembership.Trait.JOURNALLER);
    }
}
