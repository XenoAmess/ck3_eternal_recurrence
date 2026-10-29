package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;

/** Identifier/material custody vectors; physical request persistence is exercised by the archive owner. */
final class NativeRequestPreparationEvidenceTest {
    @Test void preparationEvidenceIsImmutableAndPartOfTheExactPreparedRequestButNotItsWireArguments() {
        var ref = new ExactRef("D:/contract-vectors/actual-preparation.json", 1, "a".repeat(64)); var inputs = new ArrayList<>(List.of(ref));
        var raw = new RawJson("{\"target\":73}".getBytes(StandardCharsets.UTF_8));
        var current = new NativeRequest("private-test", Optional.empty(), raw, inputs); inputs.clear();
        assertEquals(List.of(ref), current.preparationEvidence()); assertThrows(UnsupportedOperationException.class, () -> current.preparationEvidence().clear());
        var historical = new NativeRequest("private-test", Optional.empty(), raw);
        assertNotEquals(current, historical); assertEquals(current.additionalFields(), historical.additionalFields()); assertEquals(raw.objectFieldNames(), current.additionalFields().objectFieldNames());
        assertThrows(IllegalArgumentException.class, () -> new NativeRequest("private-test", Optional.empty(), raw, List.of(ref, ref)));
    }
}
