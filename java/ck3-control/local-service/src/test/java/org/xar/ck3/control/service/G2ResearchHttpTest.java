package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.eclipse.microprofile.config.ConfigProvider;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.CampaignMapProtocol;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.client.G2Evaluation;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientBatchSession;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Real Quarkus resource and shared typed client. Missing producer vectors fail; they are never skipped. */
@QuarkusTest
class G2ResearchHttpTest {
    private static final ObjectMapper TEST_JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @Inject G2ResearchHost host;
    private final HttpClient rawClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    @Test void allEightActualProvidersIncludeTheSelectedSingleM7SchedulingProvider() throws Exception {
        List<G2Domain> providers = ServiceLoader.load(G2Domain.class).stream().map(ServiceLoader.Provider::get).toList();
        assertEquals(8, providers.size(), "the actual selected descriptor must load all eight real domains");
        EnumSet<Milestone> discovered = EnumSet.noneOf(Milestone.class);
        List<ProviderOrigin> origins = new ArrayList<>();
        for (G2Domain provider : providers) {
            assertTrue(discovered.add(provider.milestone()), "duplicate actual milestone provider");
            String expected = provider.milestone() == Milestone.M7
                    ? "org.xar.ck3.control.g2.m7.schedule.M7SchedulingDomain"
                    : "org.xar.ck3.control.g2." + provider.milestone().name().toLowerCase(java.util.Locale.ROOT)
                            + "." + provider.milestone().name() + "Research";
            assertEquals(expected, provider.getClass().getName());
            var codeSource = provider.getClass().getProtectionDomain().getCodeSource();
            assertNotNull(codeSource, "actual domain CodeSource must remain observable");
            origins.add(new ProviderOrigin(provider.milestone(), provider.getClass().getName(), codeSource.getLocation().toExternalForm()));
        }
        assertEquals(EnumSet.allOf(Milestone.class), discovered);
        String configured = System.getProperty("xar.g2.http.evidence-dir");
        if (configured != null) {
            Path root = Path.of(configured).toAbsolutePath().normalize(); Files.createDirectories(root);
            ProviderInventory evidence = new ProviderInventory("xar.g2-quarkus-provider-inventory/v1",
                    WindowsJobProcess.currentMachineId(), Instant.now().toString(), List.copyOf(origins));
            Files.write(root.resolve("actual-providers.json"), TEST_JSON.writeValueAsBytes(evidence), StandardOpenOption.CREATE_NEW);
        }
    }

    @ParameterizedTest
    @EnumSource(Milestone.class)
    void eachActualDomainProducerTraversesTheSameQuarkusResourceAndSharedClient(Milestone milestone) throws Exception {
        byte[] requestBytes = fixture(milestone, ".request.json");
        byte[] expectedResult = fixture(milestone, ".expected-result.json");
        G2Request request = G2Wire.decodeRequest(requestBytes);
        assertEquals(milestone, request.milestone());
        G2Response direct = host.evaluate(request);
        assertExpectedResult(expectedResult, direct.result().bytes());
        HttpResponse<byte[]> raw = post(requestBytes);
        assertEquals(200, raw.statusCode()); headers(raw);
        assertTrue(raw.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
        assertTrue(raw.body().length > 0 && raw.body()[0] == '{', "raw response must be a JSON document rather than base64");
        assertArrayEquals(G2Wire.encodeResponse(direct), raw.body(), "HTTP serialization changed actual domain JSON tokens");
        G2Response viaRaw = G2Wire.decodeResponse(raw.body());
        assertIdentity(request, viaRaw);
        assertExpectedResult(expectedResult, viaRaw.result().bytes());
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(baseUri(), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES))) {
            G2Evaluation evaluated = client.evaluateWithEvidence(request);
            G2Response viaClient = evaluated.response();
            assertIdentity(request, viaClient);
            assertExpectedResult(expectedResult, viaClient.result().bytes());
            assertTrue(evaluated.evidence().actualHttpInvoked());
            assertTrue(evaluated.evidence().responseComplete());
            assertEquals(200, evaluated.evidence().httpStatus().orElseThrow());
            assertEquals(sha(raw.body()), evaluated.evidence().retainedResponseSha256());
            assertArrayEquals(raw.body(), evaluated.responseBytes(), "shared client must retain the original complete HTTP response bytes");
            retainActualHttpEvidence(milestone, requestBytes, expectedResult, raw, evaluated);
        }
    }

    @Test void oneRetainedClientConsumesEveryActualDomainBeforeProducingTheNextRequest() throws Exception {
        List<Milestone> consumed = new ArrayList<>();
        int[] produced = {0};
        Path retained = batchEvidenceDirectory();
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(baseUri(), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES))) {
            var result = new G2ClientBatchSession(client, WindowsJobProcess.currentMachineId()).run(new G2ClientBatchSession.Budget(8, Duration.ofMinutes(2)),
                    preceding -> {
                        assertEquals(produced[0], consumed.size(), "a dependent producer cannot run before the preceding HTTP consumer");
                        assertEquals(consumed.isEmpty(), preceding.isEmpty());
                        if (preceding.isPresent()) assertEquals(consumed.getLast(), preceding.orElseThrow().response().milestone());
                        if (produced[0] == Milestone.values().length) return G2ClientBatchSession.Complete.INSTANCE;
                        Milestone milestone = Milestone.values()[produced[0]++];
                        try { return new G2ClientBatchSession.Evaluate(G2Wire.decodeRequest(fixture(milestone, ".request.json"))); }
                        catch (IOException error) { throw new UncheckedIOException(error); }
                    }, evaluated -> {
                        Milestone milestone = evaluated.response().milestone();
                        assertEquals(Milestone.values()[consumed.size()], milestone);
                        assertTrue(evaluated.evidence().actualHttpInvoked());
                        assertTrue(evaluated.evidence().responseComplete());
                        assertEquals(200, evaluated.evidence().httpStatus().orElseThrow());
                        try {
                            G2Request request = G2Wire.decodeRequest(fixture(milestone, ".request.json"));
                            assertIdentity(request, evaluated.response());
                            assertExpectedResult(fixture(milestone, ".expected-result.json"), evaluated.response().result().bytes());
                            byte[] original = evaluated.responseBytes();
                            assertEquals(sha(original), evaluated.evidence().retainedResponseSha256());
                            assertArrayEquals(original, G2Wire.encodeResponse(G2Wire.decodeResponse(original)));
                            if (retained != null) retain(retained, milestone.name() + ".original-response.json", original);
                        } catch (IOException error) { throw new UncheckedIOException(error); }
                        consumed.add(milestone);
                    });
            assertEquals(G2ClientBatchSession.Stop.COMPLETE, result.summary().stop(), result.failure().toString());
            assertEquals(8, result.summary().submittedRequests());
            assertEquals(8, result.summary().verifiedResponses());
            assertEquals(8, result.summary().consumedResponses());
            assertEquals(List.of(Milestone.values()), consumed);
            if (retained != null) {
                var summary = result.summary();
                ActualBatchEvidence evidence = new ActualBatchEvidence("xar.g2-quarkus-http-batch-actual/v1",
                        WindowsJobProcess.currentMachineId(), Instant.now().toString(), summary.startedAtUtc().toString(),
                        summary.finishedAtUtc().toString(), summary.elapsedNanos(), summary.stop().name(),
                        summary.submittedRequests(), summary.verifiedResponses(), summary.consumedResponses(), List.copyOf(consumed), 0);
                Files.write(retained.resolve("actual-batch.json"), TEST_JSON.writeValueAsBytes(evidence), StandardOpenOption.CREATE_NEW);
            }
        }
    }

    @Test void strictEnvelopeRejectsMissingExtraNullAndWrongPrimitiveTokensOnTheActualHttpRoute() throws Exception {
        ObjectNode original = object(fixture(Milestone.M0, ".request.json"));
        List<ObjectNode> wrong = new ArrayList<>();
        for (String field : List.of("schema", "schema_version", "request_id", "milestone", "source", "payload")) {
            ObjectNode absent = original.deepCopy(); absent.remove(field); wrong.add(absent);
            ObjectNode nil = original.deepCopy(); nil.putNull(field); wrong.add(nil);
        }
        ObjectNode extra = original.deepCopy(); extra.put("unexpected", true); wrong.add(extra);
        ObjectNode boolId = original.deepCopy(); boolId.put("request_id", true); wrong.add(boolId);
        ObjectNode ordinal = original.deepCopy(); ordinal.put("milestone", 0); wrong.add(ordinal);
        ObjectNode boolVersion = original.deepCopy(); boolVersion.put("schema_version", true); wrong.add(boolVersion);
        ObjectNode floatVersion = original.deepCopy(); floatVersion.put("schema_version", 1.0); wrong.add(floatVersion);
        ObjectNode stringVersion = original.deepCopy(); stringVersion.put("schema_version", "1"); wrong.add(stringVersion);
        ObjectNode zeroVersion = original.deepCopy(); zeroVersion.put("schema_version", 0); wrong.add(zeroVersion);
        ObjectNode unknown = original.deepCopy(); unknown.put("milestone", "M8"); wrong.add(unknown);
        ObjectNode arrayPayload = original.deepCopy(); arrayPayload.putArray("payload"); wrong.add(arrayPayload);
        for (String field : List.of("machine_id", "observed_at_utc", "exact_build", "source_ref")) {
            ObjectNode absent = original.deepCopy(); ((ObjectNode) absent.get("source")).remove(field); wrong.add(absent);
            ObjectNode nil = original.deepCopy(); ((ObjectNode) nil.get("source")).putNull(field); wrong.add(nil);
        }
        ObjectNode extraSource = original.deepCopy(); ((ObjectNode) extraSource.get("source")).put("lease", "not-a-grant"); wrong.add(extraSource);
        ObjectNode booleanBytes = original.deepCopy(); ref(booleanBytes).put("bytes", true); wrong.add(booleanBytes);
        ObjectNode floatingBytes = original.deepCopy(); ref(floatingBytes).put("bytes", 1.0); wrong.add(floatingBytes);
        ObjectNode stringBytes = original.deepCopy(); ref(stringBytes).put("bytes", "1"); wrong.add(stringBytes);
        ObjectNode missingBytes = original.deepCopy(); ref(missingBytes).remove("bytes"); wrong.add(missingBytes);
        ObjectNode extraRef = original.deepCopy(); ref(extraRef).put("qualified", true); wrong.add(extraRef);
        for (ObjectNode value : wrong) assertError(post(TEST_JSON.writeValueAsBytes(value)), G2HttpError.Code.MALFORMED_REQUEST);
    }

    @Test void duplicateMalformedUtf8TrailingTokensAndEmptyBodiesNeverBecomeSuccessfulEvaluations() throws Exception {
        for (byte[] malformed : List.of(
                new byte[0], "{} {}".getBytes(StandardCharsets.UTF_8),
                "{\"schema\":\"x\",\"schema\":\"x\"}".getBytes(StandardCharsets.UTF_8),
                "{\"schema\":true}".getBytes(StandardCharsets.UTF_8),
                new byte[] {'{', '"', 'x', '"', ':', '"', (byte) 0xc3, '(', '"', '}'})) {
            assertError(post(malformed), G2HttpError.Code.MALFORMED_REQUEST);
        }
    }

    @Test void aValidEnvelopeWithInvalidDomainFieldsIsTypedDomainRejection() throws Exception {
        ObjectNode value = object(fixture(Milestone.M0, ".request.json"));
        value.set("payload", StrictJson.object());
        assertError(post(TEST_JSON.writeValueAsBytes(value)), G2HttpError.Code.DOMAIN_REJECTED);
    }

    @Test void theExistingMapRouteAndLocalOnlyApplicationRemainAvailableInTheSameHost() throws Exception {
        HttpResponse<byte[]> response = rawClient.send(HttpRequest.newBuilder(baseUri().resolve("/v1/status")).GET().build(),
                HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode());
        assertEquals("ck3-control", StrictJson.parse(response.body()).path("service").textValue());
        assertEquals("127.0.0.1", ConfigProvider.getConfig().getValue("quarkus.http.host", String.class));
        HttpResponse<byte[]> map = rawClient.send(HttpRequest.newBuilder(baseUri().resolve("/v1/map-admissions/identity")).GET().build(),
                HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, map.statusCode());
        assertEquals(CampaignMapProtocol.PRODUCER, map.headers().firstValue("X-Xar-Producer").orElseThrow());
    }

    private HttpResponse<byte[]> post(byte[] body) throws Exception {
        return rawClient.send(HttpRequest.newBuilder(baseUri().resolve(G2Wire.HTTP_PATH)).timeout(Duration.ofSeconds(20)).header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(body)).build(), HttpResponse.BodyHandlers.ofByteArray());
    }

    private URI baseUri() { return URI.create("http://127.0.0.1:" + endpoint.getPort()); }

    private static ObjectNode object(byte[] raw) throws IOException {
        return (ObjectNode) TEST_JSON.readTree(raw);
    }

    private static ObjectNode ref(ObjectNode value) { return (ObjectNode) value.get("source").get("source_ref"); }

    private static byte[] fixture(Milestone milestone, String suffix) throws IOException {
        String path = "/g2-http/" + milestone.name() + suffix;
        try (var input = G2ResearchHttpTest.class.getResourceAsStream(path)) {
            assertNotNull(input, "missing actual producer/consumer-approved fixture " + path);
            byte[] raw = input.readNBytes(G2Wire.MAX_REQUEST_BYTES + 1);
            assertFalse(raw.length == 0 || raw.length > G2Wire.MAX_REQUEST_BYTES, "finite actual fixture required " + path);
            return raw;
        }
    }

    private static void assertIdentity(G2Request request, G2Response response) {
        assertEquals(request.requestId(), response.requestId());
        assertEquals(request.milestone(), response.milestone());
        assertEquals(request.source(), response.source(), "provenance echo does not grant source/lease authority");
    }

    private static void assertExpectedResult(byte[] expected, byte[] actual) throws IOException {
        // Fixture file whitespace is not a domain outcome. Actual transport bytes are compared above without reparsing.
        assertEquals(TEST_JSON.readTree(expected), TEST_JSON.readTree(actual),
                "actual domain result differs from producer/consumer-approved JSON type/value vector");
    }

    private static void assertError(HttpResponse<byte[]> response, G2HttpError.Code expected) {
        assertEquals(expected.httpStatus(), response.statusCode()); headers(response);
        assertEquals(expected, G2Wire.decodeError(response.body()).code());
    }

    private static void headers(HttpResponse<byte[]> response) {
        assertEquals(G2Wire.PRODUCER, response.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals(G2Wire.PRODUCER_VERSION, response.headers().firstValue("X-Xar-Producer-Version").orElseThrow());
        assertEquals(G2Wire.REQUEST_SCHEMA, response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
    }

    private record ContentRef(String file, long bytes, String sha256) { }
    private record ProviderOrigin(Milestone milestone, String providerClass, String actualCodeSource) { }
    private record ProviderInventory(String schema, String machine_id, String observed_at_utc, List<ProviderOrigin> providers) { }
    private record ActualBatchEvidence(String schema, String machine_id, String observed_at_utc,
            String startedAtUtc, String finishedAtUtc, long elapsedNanos, String stop,
            int submittedRequests, int verifiedResponses, int consumedResponses, List<Milestone> milestones, int newGameDays) { }
    private record ContentDigest(long bytes, String sha256) { }
    private record ClientEvidence(String endpoint, String requestId, String startedAtUtc, String completedAtUtc,
            long elapsedNanos, ContentDigest request, ContentDigest originalResponse, int httpStatus,
            boolean responseComplete, boolean actualHttpInvoked) { }
    private record ActualHttpEvidence(String schema, String machine_id, String observed_at_utc,
            Milestone milestone, String endpoint, int httpStatus, String producer, String producerVersion,
            String contractRevision, ContentRef actualProducerRequest, ContentRef producerExpectedResult,
            ContentRef originalHttpResponse, ContentRef sharedClientResponse,
            ClientEvidence sharedClientEvidence,
            boolean sourceEchoIsMetadataOnly, int newGameDays) { }

    private static Path batchEvidenceDirectory() throws IOException {
        String configured = System.getProperty("xar.g2.http.evidence-dir");
        if (configured == null) return null;
        Path root = Path.of(configured).toAbsolutePath().normalize();
        Files.createDirectories(root);
        return Files.createDirectory(root.resolve("batch"));
    }

    /** Optional retained artifacts are the actual exchange bytes; fixture bytes never become a claimed HTTP result. */
    private void retainActualHttpEvidence(Milestone milestone, byte[] request, byte[] expected,
            HttpResponse<byte[]> raw, G2Evaluation evaluated) throws IOException {
        String configured = System.getProperty("xar.g2.http.evidence-dir");
        if (configured == null) return;
        Path root = Path.of(configured).toAbsolutePath().normalize();
        Files.createDirectories(root);
        Path directory = Files.createDirectory(root.resolve(milestone.name()));
        ContentRef requestRef = retain(directory, "actual-producer.request.json", request);
        ContentRef expectedRef = retain(directory, "producer.expected-result.json", expected);
        ContentRef rawRef = retain(directory, "original-http.response.json", raw.body());
        ContentRef clientRef = retain(directory, "shared-client.original-response.json", evaluated.responseBytes());
        var call = evaluated.evidence();
        ClientEvidence clientEvidence = new ClientEvidence(call.endpoint().toString(), call.requestId(),
                call.startedAtUtc().toString(), call.completedAtUtc().toString(), call.elapsedNanos(),
                new ContentDigest(call.requestBytes(), call.requestSha256()),
                new ContentDigest(call.retainedResponseBytes(), call.retainedResponseSha256()),
                call.httpStatus().orElseThrow(), call.responseComplete(), call.actualHttpInvoked());
        ActualHttpEvidence evidence = new ActualHttpEvidence("xar.g2-quarkus-http-actual/v1",
                WindowsJobProcess.currentMachineId(), Instant.now().toString(), milestone, baseUri().resolve(G2Wire.HTTP_PATH).toString(),
                raw.statusCode(), raw.headers().firstValue("X-Xar-Producer").orElseThrow(),
                raw.headers().firstValue("X-Xar-Producer-Version").orElseThrow(),
                raw.headers().firstValue("X-Xar-Contract-Revision").orElseThrow(), requestRef, expectedRef, rawRef, clientRef,
                clientEvidence, true, 0);
        Files.write(directory.resolve("actual-http.json"), TEST_JSON.writeValueAsBytes(evidence), StandardOpenOption.CREATE_NEW);
    }

    private static ContentRef retain(Path root, String name, byte[] raw) throws IOException {
        Path output = root.resolve(name);
        Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        byte[] readback = Files.readAllBytes(output);
        assertArrayEquals(raw, readback, "retained evidence must contain the original HTTP exchange bytes");
        return new ContentRef(name, readback.length, sha(readback));
    }

    private static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
