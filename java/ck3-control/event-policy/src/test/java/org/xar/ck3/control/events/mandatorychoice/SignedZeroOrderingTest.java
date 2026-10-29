package org.xar.ck3.control.events.mandatorychoice;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Mode;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;

/** Regression for the actual original Python numeric ordering; source IEEE bits remain untouched. */
final class SignedZeroOrderingTest {
    @Test void signedZeroCoordinatesTieAndPreserveOriginalGeometryBits() throws Exception {
        ObjectMapper json = new ObjectMapper();
        JsonNode retained;
        try (var input = getClass().getResourceAsStream("/mandatorychoice/producer-golden-v1.json")) {
            assertNotNull(input, "complete original producer fixture required");
            retained = json.readTree(input);
        }
        for (String axis : List.of("top", "left")) {
            ObjectNode input = retained.get("cases").get(0).get("input").deepCopy();
            ((ObjectNode) input.get("choices").get(0).get("bounds")).put(axis, 0.0);
            ((ObjectNode) input.get("choices").get(1).get("bounds")).put(axis, -0.0);
            var window = MandatoryChoiceCodec.decode(json.writeValueAsBytes(input));
            var first = (NativeChoice) window.choices().get(0);
            var second = (NativeChoice) window.choices().get(1);
            assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(axis.equals("top")
                    ? second.geometry().orElseThrow().top() : second.geometry().orElseThrow().left()));
            var indexed = IndexedNativeChoices.build(new Object(), ignored -> { }, window);
            assertEquals(first.identity(), MandatoryChoicePolicy.selectUnknownMandatory(window, Optional.empty()).selectedChoice().orElseThrow().identity());
            assertEquals(first.identity(), indexed.select(Optional.empty(), Mode.UNKNOWN_MANDATORY).selectedChoice().orElseThrow().identity());
            assertSame(second, indexed.entries().get(1).value());
            assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(axis.equals("top")
                    ? second.geometry().orElseThrow().top() : second.geometry().orElseThrow().left()));
            assertEquals(List.of(0, 1), indexed.entries().stream().map(OrderedCandidateIndex.Slot::position).toList());
        }
    }
}
