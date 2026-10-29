package org.xar.ck3.control.g2.m1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumSet;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;

final class M1EightRouteFixtureTest {
    @TempDir Path temporary;

    @Test void exporterExecutesEveryProducerAndConsumerBeforeWritingExactRoundTripFixtures() throws Exception {
        Path indexPath = M1HttpFixtureExporter.export(temporary.resolve("fixtures"), "synthetic-execution-test");
        JsonNode index = StrictJson.parse(Files.readAllBytes(indexPath), M1ResultConsumers.MAX_BYTES);
        assertFalse(index.path("actual_http_executed").booleanValue());
        assertEquals(0, index.path("native_game_rpc_count").intValue());
        var exported = EnumSet.noneOf(M1Operation.class);
        for (JsonNode operation : index.path("operations")) {
            M1Operation selected = M1Operation.parse(operation.path("operation").textValue());
            assertTrue(exported.add(selected));
            byte[] requestBytes = checkedRead(operation.get("request"));
            byte[] expected = checkedRead(operation.get("expected_result"));
            var request = G2Wire.decodeRequest(requestBytes);
            assertTrue(request.source().exactBuild().startsWith("pure-producer:"));
            var actual = new M1Research().evaluate(request);
            assertArrayEquals(expected, actual.result().bytes());
            M1FixtureCases.consume(selected, actual.result().bytes());
        }
        assertEquals(EnumSet.allOf(M1Operation.class), exported);
        byte[] rejected = checkedRead(index.get("rejected_request"));
        assertThrows(IllegalArgumentException.class, () -> new M1Research().evaluate(G2Wire.decodeRequest(rejected)));
        assertEquals(422, index.path("expected_rejection_http_status").intValue());
        assertThrows(java.nio.file.FileAlreadyExistsException.class,
                () -> M1HttpFixtureExporter.export(indexPath.getParent(), "synthetic-execution-test"));
    }

    @Test void originalExpectedProducerCapturesCoverExactlyThePublicOperationContract() throws Exception {
        var found = EnumSet.noneOf(M1Operation.class);
        for (M1FixtureCases.Fixture fixture : M1FixtureCases.all()) {
            assertTrue(found.add(fixture.operation()));
            var actual = new M1Research().evaluate(fixture.request());
            assertEquals(StrictJson.parse(fixture.expected().bytes(), M1ResultConsumers.MAX_BYTES),
                    StrictJson.parse(actual.result().bytes(), M1ResultConsumers.MAX_BYTES), fixture.operation().wire());
            M1FixtureCases.consume(fixture.operation(), actual.result().bytes());
        }
        assertEquals(EnumSet.allOf(M1Operation.class), found);
    }
    private static byte[] checkedRead(JsonNode ref) throws Exception {
        byte[] raw = Files.readAllBytes(Path.of(ref.path("path").textValue()));
        assertEquals(ref.path("bytes").longValue(), raw.length);
        assertEquals(ref.path("sha256").textValue(), M1FixtureCases.sha256(raw)); return raw;
    }
}
