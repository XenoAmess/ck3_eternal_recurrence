package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Root proof producer codec to the consumer binding guard; no writer/cause or Game authority. */
final class NaturalEngineClockProofTest {
    private static final String MACHINE = "unit-machine";
    private static final Instant OBSERVED = Instant.parse("2026-10-23T22:40:00Z");
    private static final String HEAD = "a".repeat(64);
    private static final ExactRef PREDECESSOR = ref("predecessor");
    private static final ExactRef FINAL_PACKET = ref("actual-final");

    @Test void actualRootSchemaRoundTripsAndUnknownDoesNotBecomeReplayPermission() {
        for (ActionReceipt.Outcome outcome : List.of(ActionReceipt.Outcome.APPLIED_CONFIRMED,
                ActionReceipt.Outcome.UNRESOLVED, ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT)) {
            NaturalEngineClockProof produced = proof(outcome);
            byte[] original = NaturalEngineClockProof.encode(produced);
            NaturalEngineClockProof consumed = NaturalEngineClockProof.decode(original);
            assertEquals(produced, consumed);
            assertArrayEquals(original, NaturalEngineClockProof.encode(consumed));
            assertFalse(consumed.replayAuthorized());
            assertDoesNotThrow(() -> consumed.requireBoundTo(MACHINE, OBSERVED, HEAD, PREDECESSOR, FINAL_PACKET));
        }
    }

    @Test void realConsumerBindingRejectsDifferentWriterRootOrActualFinalPacket() {
        NaturalEngineClockProof consumed = NaturalEngineClockProof.decode(NaturalEngineClockProof.encode(proof(ActionReceipt.Outcome.UNRESOLVED)));
        assertThrows(IllegalArgumentException.class, () -> consumed.requireBoundTo("other-machine", OBSERVED, HEAD, PREDECESSOR, FINAL_PACKET));
        assertThrows(IllegalArgumentException.class, () -> consumed.requireBoundTo(MACHINE, OBSERVED.plusNanos(1), HEAD, PREDECESSOR, FINAL_PACKET));
        assertThrows(IllegalArgumentException.class, () -> consumed.requireBoundTo(MACHINE, OBSERVED, "b".repeat(64), PREDECESSOR, FINAL_PACKET));
        assertThrows(IllegalArgumentException.class, () -> consumed.requireBoundTo(MACHINE, OBSERVED, HEAD, ref("other-predecessor"), FINAL_PACKET));
        assertThrows(IllegalArgumentException.class, () -> consumed.requireBoundTo(MACHINE, OBSERVED, HEAD, PREDECESSOR, ref("other-final")));
    }

    @Test void typedEventWindowClearanceAndNonemptyBytesAreNotEngineOriginalProofs() {
        for (String token : List.of("{}", "{\"type\":\"SSuccessionEventData\",\"player_heir_character_id\":7}",
                "{\"identity\":\"death_succession_modal\",\"cleared\":true}", "true", "null")) {
            assertThrows(IllegalArgumentException.class,
                    () -> NaturalEngineClockProof.decode(token.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode foreignSchema = encoded();
        foreignSchema.put("schema", "xar.java.natural-engine-clock-actor-originals/v1");
        assertRejected(foreignSchema);
    }

    @Test void everyOriginalIsRequiredAndCannotBeReplacedByNullOrWrongJsonTypes() {
        for (String field : List.of("original_domain", "clock_receipt", "clock_command", "predecessor_root",
                "actual_final_packet", "complete_source_qualification")) {
            ObjectNode missing = encoded(); missing.remove(field); assertRejected(missing);
            for (String bad : List.of("null", "true", "[]", "\"original\"", "1.0")) {
                ObjectNode row = encoded(); row.set(field, parse(bad)); assertRejected(row);
            }
            ObjectNode empty = encoded(); object(empty.get(field)).put("bytes", 0); assertRejected(empty);
            ObjectNode booleanBytes = encoded(); object(booleanBytes.get(field)).put("bytes", true); assertRejected(booleanBytes);
        }
        for (String field : List.of("machine_id", "observed_at_utc")) {
            ObjectNode missing = encoded(); missing.remove(field); assertRejected(missing);
            for (String bad : List.of("null", "true", "[]", "1")) {
                ObjectNode wrong = encoded(); wrong.set(field, parse(bad)); assertRejected(wrong);
            }
        }
        ObjectNode wrongTime = encoded(); wrongTime.put("observed_at_utc", "2026-10-24T00:00:00+01:00"); assertRejected(wrongTime);
        ObjectNode renamed = encoded(); renamed.set("root", renamed.remove("predecessor_root")); assertRejected(renamed);
    }

    @Test void proofCannotAuthorizeReplayOrUseUnknownAndRejectedOutcomeNames() {
        for (String value : List.of("true", "1", "0.0", "\"false\"", "null")) {
            ObjectNode row = encoded(); row.set("replay_authorized", parse(value)); assertRejected(row);
        }
        for (String value : List.of("ACK", "applied_confirmed", "REJECTED_CONFIRMED", "REJECTED_BEFORE_DISPATCH")) {
            ObjectNode row = encoded(); row.put("clock_outcome", value); assertRejected(row);
        }
        ObjectNode notText = encoded(); notText.put("clock_outcome", true); assertRejected(notText);
        ObjectNode unknownField = encoded(); unknownField.put("natural_death_proven", true); assertRejected(unknownField);
    }

    private static NaturalEngineClockProof proof(ActionReceipt.Outcome outcome) {
        return new NaturalEngineClockProof(MACHINE, OBSERVED, HEAD, outcome, false, ref("domain"), ref("clock-receipt"),
                ref("clock-command"), PREDECESSOR, FINAL_PACKET, ref("full-source-qualification"));
    }
    private static ExactRef ref(String name) { return new ExactRef("C:/unit/" + name + ".json", 1, "c".repeat(64)); }
    private static ObjectNode encoded() {
        return object(StrictJson.parse(NaturalEngineClockProof.encode(proof(ActionReceipt.Outcome.UNRESOLVED))));
    }
    private static JsonNode parse(String source) { return StrictJson.parse(source.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode object(JsonNode value) {
        if (value instanceof ObjectNode object) return object;
        throw new IllegalArgumentException("fixture object required");
    }
    private static void assertRejected(ObjectNode row) {
        assertThrows(IllegalArgumentException.class, () -> NaturalEngineClockProof.decode(StrictJson.canonical(row)));
    }
}
