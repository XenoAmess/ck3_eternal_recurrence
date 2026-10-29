package org.xar.ck3.control.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m4.M4ConstructionCheckpoint;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.CurrentInput;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Context;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.CopiedObject;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Outlay;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Reason;
import static org.junit.jupiter.api.Assertions.*;

/** The same real Quarkus host and typed client feed every M4 construction consumer. */
@QuarkusTest
public class M4ConsumerHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;

    @Test public void actualProducerFixtureTraversesHttpAllThreeConsumersAndOriginalPersistenceField() throws Exception {
        G2Request original = original();
        JsonNode payload = StrictJson.parse(original.payload().bytes(), 131072);
        JsonNode expected = StrictJson.parse(fixture("M4.expected-result.json"), 131072);
        AtomicInteger reads = new AtomicInteger();
        M4ConstructionConsumers.CurrentInputs current = () -> { reads.incrementAndGet(); return current(original); };
        try (G2JavaClient client = client()) {
            var before = M4ConstructionConsumers.beforeOptionalQuery(client::evaluate, current, "m4-http-before", kind(payload));
            var quote = M4ConstructionConsumers.afterNativeQuote(client::evaluate, current, "m4-http-quote", outlay(payload));
            var finalCheck = M4ConstructionConsumers.requireCurrentBeforeIntent(client::evaluate, current,
                    "m4-http-final", outlay(payload));
            assertEquals(3, reads.get(), "all three current observation positions must be consumed");
            assertTrue(before.decision().newSpendAllowed());
            assertTrue(quote.decision().newSpendAllowed());
            assertTrue(finalCheck.decision().newSpendAllowed());
            assertEquals(expected, StrictJson.parse(quote.response().result().bytes(), 131072));
            assertEquals(expected, StrictJson.parse(finalCheck.response().result().bytes(), 131072));
            for (var value : List.of(before, quote, finalCheck)) {
                assertEquals(value.request().requestId(), value.response().requestId());
                assertEquals(Milestone.M4, value.response().milestone());
                assertEquals(original.source(), value.response().source());
                var restored = M4ConstructionCheckpoint.decode(M4ConstructionCheckpoint.encode(value, 262144), 262144);
                assertEquals(value.stage(), restored.stage());
                assertArrayEquals(value.request().payload().bytes(), restored.request().payload().bytes());
                assertArrayEquals(value.response().result().bytes(), restored.response().result().bytes());
                assertEquals(value.decision(), restored.decision());
                ProjectionJson oldPlan = ProjectionJson.object(("{\"selected_step\":\"life-advance\","
                        + "\"construction_pending_action\":{\"status\":\"action_state_unknown\"},"
                        + "\"extension\":{\"fraction\":1.0,\"nil\":null,\"rows\":[]}}").getBytes(StandardCharsets.UTF_8), 65536);
                var attachment = M4ConstructionConsumers.attach(restored, oldPlan, 131072);
                JsonNode persisted = StrictJson.parse(attachment.enrichedUtf8(), 131072);
                assertEquals(StrictJson.parse(oldPlan.bytes()).get("selected_step"), persisted.get("selected_step"));
                assertEquals(StrictJson.parse(oldPlan.bytes()).get("construction_pending_action"), persisted.get("construction_pending_action"));
                assertEquals(StrictJson.parse(oldPlan.bytes()).get("extension"), persisted.get("extension"));
                assertEquals(StrictJson.parse(value.response().result().bytes()), persisted.get(M4ConstructionConsumers.ATTACHMENT_FIELD));
                assertArrayEquals(oldPlan.bytes(), attachment.originalUtf8());
            }
        }
    }

    @Test public void unknownActualOutlayDefersOverHttpAndFinalGuardCannotReuseEarlierAmpleResult() throws Exception {
        G2Request original = splitRevision(original());
        JsonNode payload = StrictJson.parse(original.payload().bytes(), 131072);
        assertNotEquals(payload.get("snapshot").get("revision"), payload.get("snapshot").get("native_revision"));
        AtomicInteger freshReads = new AtomicInteger();
        M4ConstructionConsumers.CurrentInputs current = () -> { freshReads.incrementAndGet(); return current(original); };
        try (G2JavaClient client = client()) {
            var old = M4ConstructionConsumers.afterNativeQuote(client::evaluate, current, "m4-http-old", outlay(payload));
            assertTrue(old.decision().newSpendAllowed());
            var missing = new Outlay(kind(payload), Optional.empty());
            var observed = M4ConstructionConsumers.afterNativeQuote(client::evaluate, current, "m4-http-unknown-outlay", missing);
            assertFalse(observed.decision().newSpendAllowed());
            assertEquals(Reason.COST, observed.decision().reason().orElseThrow());
            var refused = assertThrows(M4ConstructionConsumers.DeferredConstructionException.class,
                    () -> M4ConstructionConsumers.requireCurrentBeforeIntent(client::evaluate, current,
                            "m4-http-final-unknown", missing));
            assertEquals(Reason.COST, refused.evaluation().decision().reason().orElseThrow());
            assertEquals(3, freshReads.get());
            JsonNode result = StrictJson.parse(refused.evaluation().response().result().bytes());
            assertEquals(42, result.get("source_frame").get("revision").intValue());
            assertEquals(3, result.get("source_frame").get("native_revision").intValue());
            assertEquals(0, result.get("loan_or_refund_credited_raw").bigIntegerValue().signum());
            assertEquals(0, result.get("future_income_credited_raw").bigIntegerValue().signum());
            assertTrue(result.get("does_not_open_or_refresh_mercenary_procurement_epoch").booleanValue());
        }
    }

    @Test public void booleanFloatAndStringNativeCostsReceiveTypedDomainRefusalFromActualHttp() throws Exception {
        G2Request original = original();
        try (G2JavaClient client = client()) {
            for (String kind : List.of("boolean", "floating", "string")) {
                ObjectNode payload = (ObjectNode) StrictJson.parse(original.payload().bytes(), 131072);
                switch (kind) {
                    case "boolean" -> payload.put("construction_gold_raw", true);
                    case "floating" -> payload.put("construction_gold_raw", 23000000.0);
                    case "string" -> payload.put("construction_gold_raw", "23000000");
                    default -> throw new IllegalArgumentException("unexpected wrong token");
                }
                G2Request bad = new G2Request("m4-http-wrong-" + kind, Milestone.M4, original.source(),
                        ProjectionJson.object(SdkProjectionJson.encode(payload, 131072), 131072));
                G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(bad));
                assertEquals(G2ClientException.Reason.HTTP_REJECTED, failure.reason());
                assertEquals(G2HttpError.Code.DOMAIN_REJECTED, failure.httpError().orElseThrow().code());
                assertTrue(failure.responseBytes().length > 0, "actual typed refusal body must be retained");
            }
        }
    }

    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }

    private static G2Request original() throws IOException {
        G2Request request = G2Wire.decodeRequest(fixture("M4.request.json"));
        assertEquals(Milestone.M4, request.milestone()); return request;
    }
    private static G2Request splitRevision(G2Request original) {
        ObjectNode input = (ObjectNode) StrictJson.parse(original.payload().bytes(), 131072);
        ((ObjectNode) input.get("snapshot")).put("revision", 42);
        ((ObjectNode) input.get("market_source_frame")).put("revision", 42);
        return new G2Request("m4-http-public-42-native-3", original.milestone(), original.source(),
                ProjectionJson.object(SdkProjectionJson.encode(input, 131072), 131072));
    }
    private static CurrentInput current(G2Request original) {
        JsonNode input = StrictJson.parse(original.payload().bytes(), 131072);
        Context context = new Context(new CopiedObject(SdkProjectionJson.encode(input.get("snapshot"))),
                optional(input, "root"), optional(input, "spending"), optional(input, "market"),
                optional(input, "market_source_frame"), optional(input, "mercenary_ledger"), optional(input, "procurement_decision"));
        return new CurrentInput(original.source(), context);
    }
    private static Optional<CopiedObject> optional(JsonNode input, String key) {
        JsonNode value = input.get(key); assertNotNull(value, "actual producer field is required: " + key);
        return value.isNull() ? Optional.empty() : Optional.of(new CopiedObject(SdkProjectionJson.encode(value)));
    }
    private static String kind(JsonNode input) { assertTrue(input.get("kind").isTextual()); return input.get("kind").textValue(); }
    private static Outlay outlay(JsonNode input) {
        JsonNode cost = input.get("construction_gold_raw");
        assertTrue(cost.isNull() || cost.isIntegralNumber(), "actual producer cost integer/null required");
        return new Outlay(kind(input), cost.isNull() ? Optional.empty() : Optional.of(cost.bigIntegerValue()));
    }
    private static byte[] fixture(String name) throws IOException {
        String path = "/g2-http/" + name;
        try (var input = M4ConsumerHttpTest.class.getResourceAsStream(path)) {
            assertNotNull(input, "actual producer fixture is mandatory; missing is not a skip: " + path);
            byte[] raw = input.readNBytes(G2Wire.MAX_REQUEST_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= G2Wire.MAX_REQUEST_BYTES, "bounded actual producer fixture required");
            return raw;
        }
    }
}
