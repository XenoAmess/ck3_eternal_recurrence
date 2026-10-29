package org.xar.ck3.control.wave2.events.eventtraits;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Synthetic source facts, no Game. */
final class EventEffectPhaseTest {
    private static EventEffectPhase.SourceBinding health() {
        return new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE,
            EventEffectPhase.HEALTH_PATH, EventEffectPhase.HEALTH_SHA);
    }
    private static EventEffectPhase.SourceBinding poet() {
        return new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE,
            PoetTraitOutcome.SOURCE_PATH, PoetTraitOutcome.SOURCE_SHA256);
    }
    @Test void recoveryIsImmediate() {
        var phases = EventEffectPhase.classify("health.1101", health(), 0).orElseThrow();
        assertEquals(List.of(EventEffectPhase.Effect.ILL_REMOVED, EventEffectPhase.Effect.TREATMENT_CLEANED), phases.immediateEffects());
        assertEquals(List.of(), phases.optionEffects()); assertTrue(phases.tooltipOnly());
        assertEquals(phases, EventEffectPhase.decode(EventEffectPhase.encode(phases)));
    }
    @Test void poetPhasesAreSeparate() {
        for (int index = 0; index < 3; index++) {
            var phases = EventEffectPhase.classify(PoetTraitOutcome.EVENT, poet(), index).orElseThrow();
            assertTrue(phases.immediateEffects().contains(EventEffectPhase.Effect.HAD_EVENT_FLAG_SET));
            assertEquals(List.of(EventEffectPhase.Effect.POEM_CONTEXT_CLEANED), phases.afterEffects());
            assertEquals(index == 0, phases.optionAdds(EventTraitMembership.Trait.LIFESTYLE_POET));
            assertEquals(index == 1, phases.optionAdds(EventTraitMembership.Trait.JOURNALLER));
            assertEquals(phases, EventEffectPhase.decode(EventEffectPhase.encode(phases)));
        }
    }
    @Test void wrongSourceHasNoFacts() {
        assertTrue(EventEffectPhase.classify("health.1101", health(), 1).isEmpty());
        assertTrue(EventEffectPhase.classify(PoetTraitOutcome.EVENT, poet(), 3).isEmpty());
        assertTrue(EventEffectPhase.classify("health.1101", new EventEffectPhase.SourceBinding("1.19.0.6", EventEffectPhase.EXE,
            EventEffectPhase.HEALTH_PATH, EventEffectPhase.HEALTH_SHA), 0).isEmpty());
        assertTrue(EventEffectPhase.classify("health.1101", new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE,
            EventEffectPhase.HEALTH_PATH, "a".repeat(64)), 0).isEmpty());
    }
    @Test void malformedPhaseRejects() {
        byte[] good = EventEffectPhase.encode(EventEffectPhase.classify("health.1101", health(), 0).orElseThrow());
        ObjectNode forged = (ObjectNode) StrictJson.parse(good); forged.putArray("option_effects").add("ill_removed");
        assertThrows(IllegalArgumentException.class, () -> EventEffectPhase.decode(StrictJson.canonical(forged)));
        ObjectNode missing = (ObjectNode) StrictJson.parse(good); missing.remove("immediate_effects");
        assertThrows(IllegalArgumentException.class, () -> EventEffectPhase.decode(StrictJson.canonical(missing)));
        ObjectNode bool = (ObjectNode) StrictJson.parse(good); bool.put("native_option_index", false);
        assertThrows(IllegalArgumentException.class, () -> EventEffectPhase.decode(StrictJson.canonical(bool)));
        String text = new String(good, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EventEffectPhase.decode(text.replace("\"native_option_index\":0",
            "\"native_option_index\":0.0").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EventEffectPhase.decode(text.replace("\"tooltip_only\":true",
            "\"tooltip_only\":true,\"tooltip_only\":true").getBytes(StandardCharsets.UTF_8)));
    }
}
