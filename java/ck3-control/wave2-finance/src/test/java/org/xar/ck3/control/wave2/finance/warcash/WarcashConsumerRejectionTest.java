package org.xar.ck3.control.wave2.finance.warcash;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;

/** The exact six negative transitions exercised by the existing full Python consumers. */
final class WarcashConsumerRejectionTest {
    private record Original(ObjectNode request, ObjectNode receipt) { }
    private record Rejection(String name, ObjectNode request, String originalReasonFragment) { }

    @TestFactory
    Stream<DynamicTest> originalConsumerNegativeReasonsRemainJavaDomainRejections() throws Exception {
        Original original = originalCompleteSingle();
        ObjectNode staleInput = original.request().deepCopy();
        newer(object(object(arguments(staleInput).get("inputs")).get("source_frame")));

        ObjectNode wrongWar = original.request().deepCopy();
        ObjectNode wrongInputs = object(arguments(wrongWar).get("inputs"));
        wrongInputs.put("war_id", wrongInputs.get("war_id").bigIntegerValue().add(BigInteger.ONE));

        ObjectNode staleAmount = original.request().deepCopy();
        newer(object(object(object(arguments(staleAmount).get("inputs"))
                .get("future_war_cost_upper_raw")).get("source_frame")));

        ObjectNode scalarAmount = original.request().deepCopy();
        object(arguments(scalarAmount).get("inputs")).put("pending_war_cash_raw", 0);

        ObjectNode reserve = original.receipt().deepCopy();
        reserve.put("joint_gold_reserve_raw", reserve.get("joint_gold_reserve_raw").bigIntegerValue().add(BigInteger.ONE));

        ObjectNode provenance = original.receipt().deepCopy();
        newer(object(object(object(provenance.get("amount_observations"))
                .get("future_war_cost_upper_raw")).get("source_frame")));

        return List.of(
            new Rejection("stale full input frame", staleInput, "full paused frame"),
            new Rejection("wrong input WarID", wrongWar, "WarID"),
            new Rejection("stale sourced amount", staleAmount, "same-frame sourced"),
            new Rejection("unproved scalar zero", scalarAmount, "sourced nonnegative"),
            new Rejection("forged reserve", verify(reserve), "does not balance"),
            new Rejection("receipt provenance", verify(provenance), "lost same-frame provenance")
        ).stream().map(rejection -> DynamicTest.dynamicTest(rejection.name(), () -> {
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                    () -> WarcashCodec.evaluate(StrictJson.canonical(rejection.request())));
            assertTrue(error.getMessage().contains(rejection.originalReasonFragment()), error.getMessage());
        }));
    }

    private static ObjectNode verify(ObjectNode receipt) {
        ObjectNode request = StrictJson.object().put("schema", WarcashCodec.REQUEST_SCHEMA)
                .put("operation", "require_complete_war_cash_resource_v1");
        ObjectNode arguments = request.putObject("arguments");
        arguments.set("receipt", receipt);
        arguments.set("frame", receipt.get("source_frame").deepCopy());
        arguments.set("war_id", receipt.get("war_id"));
        return request;
    }
    private static ObjectNode arguments(ObjectNode request) { return object(request.get("arguments")); }
    private static ObjectNode object(JsonNode value) {
        assertTrue(value instanceof ObjectNode, "the actual original object field is required");
        return (ObjectNode) value;
    }
    private static void newer(ObjectNode frame) {
        frame.put("revision", frame.get("revision").bigIntegerValue().add(BigInteger.ONE));
    }
    private static Original originalCompleteSingle() throws Exception {
        try (InputStream stream = WarcashConsumerRejectionTest.class.getResourceAsStream("/warcash/original-v1.jsonl.gz")) {
            assertNotNull(stream, "actual original golden is mandatory; missing corpus must fail");
            try (GZIPInputStream gzip = new GZIPInputStream(stream)) {
                byte[] raw = gzip.readNBytes(8 * 1024 * 1024 + 1);
                assertTrue(raw.length <= 8 * 1024 * 1024);
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
                String[] lines = text.split("\n", -1);
                assertEquals("", lines[lines.length - 1]);
                assertEquals(0, (lines.length - 2) % 3);
                for (int index = 1; index < lines.length - 1; index += 3) {
                    JsonNode metadata = StrictJson.parse(lines[index].getBytes(StandardCharsets.UTF_8));
                    ObjectNode request = object(StrictJson.parse(lines[index + 1].getBytes(StandardCharsets.UTF_8)));
                    JsonNode receipt = StrictJson.parse(lines[index + 2].getBytes(StandardCharsets.UTF_8));
                    if ("result".equals(metadata.path("expected_kind").textValue())
                            && "observe_active_war_cash_resource_v1".equals(request.path("operation").textValue())
                            && "complete".equals(receipt.path("status").textValue())) {
                        return new Original(request, object(receipt));
                    }
                }
            }
        }
        throw new IllegalStateException("an actual original complete single-war receipt is required");
    }
}
