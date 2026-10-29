package org.xar.ck3.control.wave2.finance.feastcounters;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalProjectionPort;

/** Domain ports use the actual retained producer/consumer oracle, never a Python process. */
final class FeastProjectionPortTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @TestFactory
    Stream<DynamicTest> terminalPortMatchesAllOriginalProducerCases() throws IOException {
        var port = new FeastTerminalProjectionPort();
        JsonNode reference = golden("/feastterminal/terminal-producer-golden-v1.json");
        assertEquals(48, reference.get("cases").size());
        return StreamSupport.stream(reference.get("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!row.get("accepted").booleanValue()) {
                        assertThrows(IllegalArgumentException.class, () -> port.decode(input));
                    } else {
                        assertEquals(row.get("result"), JSON.readTree(port.encode(port.project(port.decode(input)))));
                    }
                }));
    }

    @TestFactory
    Stream<DynamicTest> nativeCounterPortMatchesAllOriginalFourFieldCases() throws IOException {
        var port = new OutcomeCounterNormalizeProjectionPort();
        JsonNode reference = golden("/feastcounters/counter-producer-consumer-golden-v1.json");
        assertEquals(25, reference.get("producer_cases").size());
        return StreamSupport.stream(reference.get("producer_cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!row.get("accepted").booleanValue()) {
                        assertThrows(IllegalArgumentException.class, () -> port.decode(input));
                    } else {
                        assertEquals(row.get("result"), JSON.readTree(port.encode(port.project(port.decode(input)))));
                    }
                }));
    }

    @TestFactory
    Stream<DynamicTest> oneCounterPortFeedsBothActualSeedAndValueConsumers() throws IOException {
        var port = new OutcomeCounterConsumerProjectionPort();
        JsonNode reference = golden("/feastcounters/counter-producer-consumer-golden-v1.json");
        assertEquals(9, reference.get("projection_cases").size());
        return StreamSupport.stream(reference.get("projection_cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    JsonNode receipt = JSON.readTree(port.encode(port.project(port.decode(input))));
                    assertEquals(2, receipt.size());
                    assertEquals(row.get("actual_start_seed"), receipt.get("pre_outcome_values"));
                    assertEquals(row.get("expected"), receipt.get("value_observation"));
                }));
    }

    @Test
    void profilesAreExplicitAndDoNotIncreaseTheCounterLeafOrTerminalContainerLimits() {
        var terminal = new FeastTerminalProjectionPort();
        var nativeCounter = new OutcomeCounterNormalizeProjectionPort();
        var consumer = new OutcomeCounterConsumerProjectionPort();
        assertEquals(ProjectionOperation.FEAST_TERMINAL_NORMALIZE, terminal.operation());
        assertEquals(1_048_576, terminal.inputMaximumBytes());
        assertEquals(2_097_152, terminal.outputMaximumBytes());
        assertEquals(ProjectionOperation.FEAST_COUNTER_NORMALIZE, nativeCounter.operation());
        assertEquals(16_384, nativeCounter.inputMaximumBytes());
        assertEquals(16_384, nativeCounter.outputMaximumBytes());
        assertEquals(ProjectionOperation.FEAST_COUNTER_PROJECT, consumer.operation());
        assertEquals(16_384, consumer.inputMaximumBytes());
        assertEquals(16_384, consumer.outputMaximumBytes());
    }

    @Test
    void actualServiceLoaderRegistrationsConsumeEveryOriginalCounterVector() throws IOException {
        JsonNode reference = golden("/feastcounters/counter-producer-consumer-golden-v1.json");
        var summary = ProbeCompiledCounterConsumers.verifyRegisteredProjections(reference);
        assertEquals(25, summary.producerCases());
        assertEquals(25, summary.accepted() + summary.rejected());
        assertEquals(StreamSupport.stream(reference.get("producer_cases").spliterator(), false)
                .filter(row -> row.get("accepted").booleanValue()).count(), summary.accepted());
        assertEquals(9, summary.consumerCases());
    }

    private static JsonNode golden(String resource) throws IOException {
        try (InputStream input = FeastProjectionPortTest.class.getResourceAsStream(resource)) {
            if (input == null) throw new IOException("required original producer/consumer oracle unavailable: " + resource);
            return JSON.readTree(input.readAllBytes());
        }
    }
}
