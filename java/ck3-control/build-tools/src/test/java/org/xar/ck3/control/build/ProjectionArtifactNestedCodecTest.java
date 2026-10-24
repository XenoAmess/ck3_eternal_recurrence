package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Regression for the actual strict Jackson nested-value failure; no runtime authority. */
final class ProjectionArtifactNestedCodecTest {
    record Envelope(Observed observed) { }
    private static Observed observation() {
        var reference = new ControlBuild.FileRef(Path.of("response.json").toAbsolutePath().normalize().toString(), 1, "a".repeat(64));
        return new Observed(new Context("fixture-machine", Instant.parse("2026-10-23T00:00:00Z"), Optional.empty()), reference);
    }
    @Test void nestedObservedConsumesOnlyItsCurrentValueAndPreservesOuterStrictParser() throws Exception {
        var value = new Envelope(observation());
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value);
        assertEquals(value, ControlBuild.strictMapper().readValue(raw, Envelope.class));
    }
    @Test void rootTrailingValuesStillFailForStandaloneAndNestedObservations() throws Exception {
        for (Object value : new Object[]{observation(), new Envelope(observation())}) {
            String raw = ControlBuild.strictMapper().writeValueAsString(value) + " {}";
            if (value instanceof Envelope) assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(raw, Envelope.class));
            else assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(raw, Observed.class));
        }
    }
    @Test void nestedUnknownFieldsNullAndWrongContextTypesRemainRejected() throws Exception {
        var original = ControlBuild.strictMapper().valueToTree(new Envelope(observation()));
        for (String field : new String[]{"extra_observed", "extra_context", "null_context", "wrong_context"}) {
            var row = original.deepCopy();
            var observed = (com.fasterxml.jackson.databind.node.ObjectNode) row.get("observed");
            switch (field) {
                case "extra_observed" -> observed.put("unknown", 1);
                case "extra_context" -> ((com.fasterxml.jackson.databind.node.ObjectNode) observed.get("context")).put("unknown", 1);
                case "null_context" -> observed.putNull("context");
                case "wrong_context" -> observed.put("context", true);
                default -> throw new IllegalStateException(field);
            }
            byte[] raw = row.toString().getBytes(StandardCharsets.UTF_8);
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(raw, Envelope.class));
        }
    }
}
