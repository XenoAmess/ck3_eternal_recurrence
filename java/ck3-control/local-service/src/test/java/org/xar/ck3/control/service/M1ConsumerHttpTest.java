package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m1.M1RealmComparisons;
import org.xar.ck3.control.g2.m1.M1Research;
import org.xar.ck3.control.g2.m1.M1ResultConsumers;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;

/** Real HTTP -> shared client -> typed M1 consumers -> JSON persistence, using unchanged producer captures. */
@QuarkusTest
class M1ConsumerHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path persistence;
    private int persistedResponses;

    @Test void allEightActualM1RoutesReachTypedConsumersAndPersistedResponses() throws Exception {
        JsonNode realmGolden = parse(resource("realm-membership.json", "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253"));
        JsonNode realmInput = realmGolden.path("bases").path("first");
        JsonNode monthGolden = parse(resource("monthly-observation.json", "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae"));
        JsonNode monthCase = monthlyCase(monthGolden, "sample-baseline");
        List<String> savedLines = new String(resource("saved-membership.jsonl",
                "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96"), StandardCharsets.UTF_8).lines().toList();
        JsonNode savedCase = parse(utf8(savedLines.get(1)));
        byte[] savedInput = utf8(savedCase.path("input_json").textValue());
        try (G2JavaClient client = client()) {
            G2Response feedbackResponse = evaluate(client, "realm-feedback", write(realmInput));
            var feedback = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class,
                    M1ResultConsumers.realmFeedback(feedbackResponse.result().bytes()));
            assertEquals(3, feedback.observation().component().countyTitleIds().size());
            assertTrue(feedback.observation().component().complete());
            JsonNode nativeObservation = parse(feedbackResponse.result().bytes()).get("observation");
            ObjectNode nativePair = StrictJson.object();
            nativePair.set("cached", nativeObservation); nativePair.set("current", nativeObservation);
            assertEquals(M1RealmComparisons.CacheStatus.CURRENT,
                    M1ResultConsumers.cache(evaluate(client, "native-cache", write(nativePair)).result().bytes()));
            ObjectNode difference = StrictJson.object(); difference.putNull("previous"); difference.set("observation", nativeObservation);
            RealmDifference.Unavailable noPrevious = assertInstanceOf(RealmDifference.Unavailable.class,
                    M1ResultConsumers.nativeDifference(evaluate(client, "native-difference", write(difference)).result().bytes()));
            assertEquals("previous_complete_observation_missing", noPrevious.reason());

            G2Response month = evaluate(client, "monthly-observation", write(monthCase.get("request")));
            var monthObservation = M1ResultConsumers.monthlyObservation(month.result().bytes()).orElseThrow();
            assertEquals(monthCase.path("expected").get("value"), parse(month.result().bytes()));
            assertEquals(monthCase.path("request").path("campaign_anchor").path("founder_character_id").bigIntegerValue(),
                    monthObservation.campaignAnchor().founderCharacterId());
            ObjectNode monthlyPair = StrictJson.object();
            monthlyPair.set("cached", monthCase.get("request")); monthlyPair.set("current", monthCase.get("request"));
            assertEquals(M1RealmComparisons.CacheStatus.CURRENT,
                    M1ResultConsumers.cache(evaluate(client, "monthly-cache", write(monthlyPair)).result().bytes()));
            assertTrue(M1ResultConsumers.monthlyObservation(evaluate(client, "monthly-observation",
                    write(monthlyCase(monthGolden, "sample-nonboundary").get("request"))).result().bytes()).isEmpty());

            G2Response saved = evaluate(client, "saved-membership", savedInput);
            assertEquals(savedCase.get("expected"), parse(saved.result().bytes()));
            assertTrue(M1ResultConsumers.savedMembership(saved.result().bytes()).realm().complete());
            ObjectNode savedPair = StrictJson.object();
            savedPair.set("previous", parse(savedInput)); savedPair.set("current", parse(savedInput)); savedPair.put("scope", "realm");
            var unavailable = assertInstanceOf(M1RealmComparisons.SavedUnavailable.class,
                    M1ResultConsumers.savedDifference(evaluate(client, "saved-difference", write(savedPair)).result().bytes()));
            assertEquals(M1RealmComparisons.Reason.DATE_NOT_STRICTLY_EARLIER, unavailable.reason());
            JsonNode summaries = parse(resource("dated-summary.json", "7bc6d62177f58fe3f7763d302cfab9d739f7821ae37937485bd088d5622418fc"));
            for (String id : List.of("current-loss", "historical-revision", "no-feedback")) {
                JsonNode row = monthlyCase(summaries, id);
                G2Response summaryResponse = evaluate(client, "dated-summary", write(row.get("request")));
                assertEquals(row.path("expected").get("value"), parse(summaryResponse.result().bytes()));
                var summary = M1ResultConsumers.datedSummary(summaryResponse.result().bytes());
                if (id.equals("no-feedback")) { assertEquals(M1ResultConsumers.NoQualifiedSummary.INSTANCE, summary); }
                else {
                    var retained = assertInstanceOf(M1ResultConsumers.RetainedSummary.class, summary);
                    assertEquals(2, retained.lastObservedCount());
                    assertEquals(id.equals("current-loss") ? org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary.Status.CURRENT
                            : org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary.Status.HISTORICAL, retained.status());
                }
            }
        }
    }

    @Test void originalNumericTokenKindsRemainDistinctAcrossTheActualHttpClientAndDisk() throws Exception {
        JsonNode golden = parse(resource("realm-membership.json", "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253"));
        ObjectNode input = (ObjectNode) golden.path("bases").path("first").deepCopy();
        ((ObjectNode) input.get("source_frame")).set("sdk_extension", parse(utf8("1.0")));
        try (G2JavaClient client = client()) {
            var complete = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class,
                    M1ResultConsumers.realmFeedback(evaluate(client, "realm-feedback", write(input)).result().bytes()));
            assertTrue(complete.observation().sourceFrame().get("sdk_extension").isFloatingPointNumber());
            for (String token : List.of("true", "1.0", "\"1\"")) {
                ObjectNode invalid = input.deepCopy();
                ((ObjectNode) invalid.get("faction_result")).set("query_sequence", parse(utf8(token)));
                var unavailable = assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class,
                        M1ResultConsumers.realmFeedback(evaluate(client, "realm-feedback", write(invalid)).result().bytes()));
                assertEquals("faction_original_query_sequence_unavailable", unavailable.reason());
            }
        }
        G2Request rejected = request("unsupported-operation", write(input), "realm-membership.json");
        HttpResponse<byte[]> response = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + endpoint.getPort()).resolve(G2Wire.HTTP_PATH)).timeout(Duration.ofSeconds(20)).header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofByteArray(G2Wire.encodeRequest(rejected))).build(),
                HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(422, response.statusCode());
        assertEquals(G2HttpError.Code.DOMAIN_REJECTED, G2Wire.decodeError(response.body()).code());
    }

    private G2Response evaluate(G2JavaClient client, String operation, byte[] input) throws Exception {
        String fixture = operation.equals("dated-summary") ? "dated-summary.json" : operation.startsWith("saved-") ? "saved-membership.jsonl"
                : operation.startsWith("monthly-") ? "monthly-observation.json" : "realm-membership.json";
        G2Request request = request(operation, input, fixture);
        G2Response response = client.evaluate(request);
        assertEquals(request.requestId(), response.requestId()); assertEquals(Milestone.M1, response.milestone());
        assertEquals(request.source(), response.source());
        Path path = persistence.resolve(operation + "-" + persistedResponses++ + ".json");
        byte[] encoded = G2Wire.encodeResponse(response);
        Files.write(path, encoded, StandardOpenOption.CREATE_NEW);
        G2Response restored = G2Wire.decodeResponse(Files.readAllBytes(path));
        assertArrayEquals(response.result().bytes(), restored.result().bytes());
        assertEquals(response.source(), restored.source());
        return restored;
    }
    private static G2Request request(String operation, byte[] input, String fixture) throws Exception {
        byte[] corpus;
        JsonNode metadata;
        String machine;
        String observed;
        String build;
        if (fixture.equals("saved-membership.jsonl")) {
            corpus = resource(fixture, "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96");
            metadata = parse(utf8(new String(corpus, StandardCharsets.UTF_8).lines().findFirst().orElseThrow()));
            machine = metadata.path("machine_id").textValue(); observed = metadata.path("observed_at_utc").textValue();
            build = "pure-producer:" + metadata.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue();
        } else if (fixture.equals("monthly-observation.json") || fixture.equals("dated-summary.json")) {
            corpus = resource(fixture, fixture.equals("dated-summary.json")
                    ? "7bc6d62177f58fe3f7763d302cfab9d739f7821ae37937485bd088d5622418fc"
                    : "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae");
            metadata = parse(corpus);
            machine = metadata.path("machine_id").textValue(); observed = metadata.path("observed_at_utc").textValue();
            build = "pure-producer:" + metadata.path("producer").path("sha256").textValue();
        } else {
            corpus = resource(fixture, "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253");
            metadata = parse(corpus);
            machine = metadata.path("capture").path("machine_id").textValue(); observed = metadata.path("capture").path("observed_at_utc").textValue();
            JsonNode hello = metadata.path("bases").path("first").path("snapshot").path("diagnostics").path("hello");
            build = hello.path("game_version").textValue() + ":" + hello.path("executable_sha256").textValue();
        }
        // Pure captures bind their original producer implementation. They contain no current native build grant.
        G2Source source = new G2Source(machine, Instant.parse(observed).toString(), build,
                new ExactRef("classpath:/m1/" + fixture, corpus.length, hash(corpus)));
        ByteArrayOutputStream payload = new ByteArrayOutputStream();
        payload.writeBytes(utf8("{\"operation\":\"" + operation + "\",\"input\":"));
        payload.writeBytes(input); payload.write('}');
        return new G2Request("m1-http-" + operation, Milestone.M1, source,
                ProjectionJson.object(payload.toByteArray(), M1Research.MAX_BYTES));
    }
    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }
    private static JsonNode monthlyCase(JsonNode golden, String id) throws IOException {
        for (JsonNode row : golden.path("cases")) { if (row.path("id").asText().equals(id)) { return row; } }
        throw new IOException("required actual producer case missing: " + id);
    }
    private static byte[] resource(String name, String sha256) throws Exception {
        try (InputStream stream = M1ConsumerHttpTest.class.getResourceAsStream("/m1/" + name)) {
            assertNotNull(stream, "actual single-source M1 producer fixture required");
            byte[] raw = stream.readAllBytes(); assertEquals(sha256, hash(raw)); return raw;
        }
    }
    private static String hash(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
    private static JsonNode parse(byte[] raw) { return StrictJson.parse(raw, M1ResultConsumers.MAX_BYTES); }
    private static byte[] write(JsonNode node) { return SdkProjectionJson.encode(node, M1ResultConsumers.MAX_BYTES); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
