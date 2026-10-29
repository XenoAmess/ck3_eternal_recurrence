package org.xar.ck3.control.events.mandatorychoice;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Mode;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;

/** Indexed production branch runs in the existing event-policy Maven/CI lifecycle. */
final class IndexedNativeChoicesTest {
    @Test void everyRetainedProducerVectorUsesTheCompleteIndexedProductionBranch() throws Exception {
        ObjectMapper json = new ObjectMapper();
        JsonNode golden;
        try (var input = getClass().getResourceAsStream("/mandatorychoice/producer-golden-v1.json")) {
            assertNotNull(input, "retained original producer corpus required; no skip");
            golden = json.readTree(input);
        }
        assertEquals(17, golden.get("cases").size());
        for (JsonNode vector : golden.get("cases")) {
            var window = MandatoryChoiceCodec.decode(json.writeValueAsBytes(vector.get("input")));
            var active = new AtomicBoolean(true);
            Object scope = new Object();
            var indexed = IndexedNativeChoices.build(scope, expected -> {
                if (!active.get() || expected != scope) { throw new IllegalStateException("owner token revoked"); }
            }, window);
            assertEquals(window.choices().size(), indexed.entries().size());
            for (int position = 0; position < window.choices().size(); position++) {
                assertSame(window.choices().get(position), indexed.entries().get(position).value());
                assertEquals(position, indexed.entries().get(position).position());
                if (window.choices().get(position) instanceof NativeChoice choice) {
                    assertTrue(indexed.matching(choice.identity()).stream()
                            .anyMatch(slot -> slot.value() == choice && slot.position() == choice.inputIndex()));
                }
            }
            Optional<FrameBinding> expected = vector.get("expected_frame").isNull() ? Optional.empty()
                    : Optional.of(MandatoryChoiceCodec.decodeFrame(json.writeValueAsBytes(vector.get("expected_frame"))));
            Mode mode = vector.get("mode").asText().equals("unknown") ? Mode.UNKNOWN_MANDATORY : Mode.EXISTING_NATIVE_DOMAIN;
            assertEquals(vector.get("output"), json.readTree(MandatoryChoiceCodec.encodeDecision(indexed.select(expected, mode))),
                    vector.get("name").asText());
            active.set(false);
            assertThrows(IllegalStateException.class, indexed::entries);
            assertThrows(IllegalStateException.class, () -> indexed.select(expected, mode));
        }
    }
}
