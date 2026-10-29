package org.xar.ck3.control.wave3.planning.military;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionResult;

/** Reads only a separately captured actual original producer corpus; missing evidence fails instead of skipping. */
class MilitaryRouteGeometryProducerTest {
    @Test void actualOriginalProducerToRegisteredJavaConsumer() throws IOException {
        try (InputStream stream = getClass().getResourceAsStream("/militarycontact/geometry-original-producer.json")) {
            assertNotNull(stream, "actual original geometry producer fixture is required");
            byte[] original = stream.readAllBytes();
            StrictJson.parse(original, 1_048_576);
            // Keep float token identity when replaying the original producer's input through bytes.
            JsonNode corpus = JsonMapper.builder().enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
                    .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build().readTree(original);
            assertTrue(corpus.isArray()); assertEquals(14, corpus.size());
            for (JsonNode row : corpus) {
                byte[] raw = row.get("input").toString().getBytes(StandardCharsets.UTF_8);
                var port = new MilitaryPlanningProjectionCatalog().registrations().getFirst();
                assertEquals(1_048_576, port.inputMaximumBytes()); assertEquals(1_048_576, port.outputMaximumBytes());
                var result = port.execute(new ProjectionCall(new ProjectionCall.Identity("geometry-producer-differential", port.operation()), ProjectionJson.object(raw, ProjectionJson.MAX_BYTES)));
                var success = assertInstanceOf(ProjectionResult.Succeeded.class, result);
                assertEquals(row.get("expected"), StrictJson.parse(success.result().bytes()), row.get("name").textValue());
            }
        }
    }
}
