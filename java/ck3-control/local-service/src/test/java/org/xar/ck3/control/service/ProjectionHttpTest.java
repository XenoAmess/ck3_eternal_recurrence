package org.xar.ck3.control.service;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.common.http.TestHTTPResource;
import java.math.BigInteger;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.EnumSet;
import java.util.ServiceLoader;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOpaqueGameGenerationV1;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import static org.junit.jupiter.api.Assertions.*;

/** Actual HTTP and actual classpath service discovery, with no Python, CK3, SDK or native provider. */
@QuarkusTest
class ProjectionHttpTest {
    @TestHTTPResource("/v1/projections/") URI base;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    @Test void classpathCatalogsAreActuallyDiscoveredByTheSameResidentHttpHost() throws Exception {
        EnumSet<ProjectionOperation> discovered = EnumSet.noneOf(ProjectionOperation.class);
        ServiceLoader.load(ProjectionPortCatalog.class).forEach(catalog -> catalog.registrations().forEach(port -> {
            assertTrue(discovered.add(port.operation()), "duplicate provider operation " + port.operation());
        }));
        assertFalse(discovered.isEmpty(), "domain service descriptors must be present in the actual host classpath");
        assertTrue(discovered.containsAll(EnumSet.of(ProjectionOperation.GOVERNANCE_GOVERNMENT_CONTEXT,
                ProjectionOperation.DEADLINE_TRANSPORT_PROJECT, ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK,
                ProjectionOperation.CONSTRUCTION_INTENT)), "required integrated domain catalogs missing");
        HttpResponse<byte[]> response = client.send(HttpRequest.newBuilder(base.resolve("identity")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode()); headers(response);
        var identity = StrictJson.parse(response.body());
        assertEquals("xar.projection-host-identity/v1", identity.path("schema").textValue());
        assertEquals(ProjectionWire.MAX_ENVELOPE_BYTES, identity.path("envelope_max_bytes").intValue());
        EnumSet<ProjectionOperation> advertised = EnumSet.noneOf(ProjectionOperation.class);
        identity.path("operations").forEach(row -> {
            assertTrue(advertised.add(ProjectionOperation.fromWire(row.path("operation").textValue())));
            assertTrue(row.path("input_max_bytes").isIntegralNumber()); assertTrue(row.path("output_max_bytes").isIntegralNumber());
        });
        discovered.add(ProjectionOperation.MAP_ADMISSION_COMPOSE); assertEquals(discovered, advertised);
        assertEquals(EnumSet.allOf(ProjectionOperation.class), advertised,
                "the complete selected operation contract must have actual registered host ports");
        assertEquals(ProjectionOperation.values().length, identity.path("operations").size());
        assertProfile(identity, ProjectionOperation.GOVERNANCE_CROWN_CHOOSE, 65_536, 65_536);
        assertProfile(identity, ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION, 131_072, 131_072);
        assertProfile(identity, ProjectionOperation.MILITARY_ROUTE_GEOMETRY, 1_048_576, 1_048_576);
        assertProfile(identity, ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE, 65_536, 65_536);
    }

    @Test void originalMapProducerToTypedPortToHttpPreservesActualUint64Output() throws Exception {
        byte[] payload = mapPayload(); byte[] expected = CampaignMapAdmissionComposer.compose(payload);
        HttpResponse<byte[]> response = post(call(payload)); assertEquals(200, response.statusCode()); headers(response);
        var decoded = assertInstanceOf(ProjectionResult.Succeeded.class, ProjectionWire.decodeResult(response.body()));
        assertArrayEquals(expected, decoded.result().bytes());
        var result = StrictJson.parse(response.body());
        assertEquals("xar.projection-result/v1", result.path("schema").textValue());
        assertEquals("http-map-1", result.path("request_id").textValue());
        assertEquals("map-admission-compose", result.path("operation").textValue());
        assertEquals("succeeded", result.path("status").textValue());
        assertEquals(new BigInteger("18446744073709551615"), result.path("result").path("game_creation_filetime").bigIntegerValue());
    }

    @Test void catalogsReportActualLoadedProviderCodeSourcesAndSameOperationProfiles() throws Exception {
        HttpResponse<byte[]> response = client.send(HttpRequest.newBuilder(base.resolve("catalogs")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode()); headers(response); var result = StrictJson.parse(response.body());
        assertEquals("xar.projection-host-catalogs/v1", result.path("schema").textValue());
        assertFalse(result.path("machine_id").textValue().isEmpty());
        java.time.Instant.parse(result.path("observed_at_utc").textValue());
        EnumSet<ProjectionOperation> operations = EnumSet.noneOf(ProjectionOperation.class);
        result.path("catalogs").forEach(row -> {
            assertFalse(row.path("provider_class").textValue().isBlank());
            assertTrue(Path.of(row.path("artifact_path").textValue()).isAbsolute());
            row.path("operations").forEach(profile -> assertTrue(operations.add(ProjectionOperation.fromWire(profile.path("operation").textValue()))));
        });
        assertTrue(operations.contains(ProjectionOperation.MAP_ADMISSION_COMPOSE));
        assertTrue(operations.contains(ProjectionOperation.DEADLINE_TRANSPORT_PROJECT));
        assertEquals(EnumSet.allOf(ProjectionOperation.class), operations,
                "catalog origins must cover the same complete operation inventory");
    }

    @Test void httpDispatchUsesTheActualDomainCodecForWrongIntegerTokens() throws Exception {
        for (String wrong : new String[] {"true", "false", "1.0", "1e0", "\"1\"", "null", "[]", "{}",
                "0", "-1", "18446744073709551616", "\"18446744073709551615\""}) {
            String payload = new String(mapPayload(), StandardCharsets.UTF_8).replace("18446744073709551615", wrong);
            HttpResponse<byte[]> response = post(call(payload.getBytes(StandardCharsets.UTF_8)));
            assertEquals(400, response.statusCode());
            assertEquals("invalid-payload", StrictJson.parse(response.body()).path("error").path("code").textValue());
        }
    }

    @Test void currentStringIdentityCannotEnterTheOpaqueMapV1HttpRoute() throws Exception {
        ObjectNode payload = assertInstanceOf(ObjectNode.class, StrictJson.parse(mapPayload()));
        var game = new GameGeneration(12345, new PythonOnlyUInt64(StrictJson.UINT64_MAX));
        payload.set("native_launch", game.toJson());
        assertTrue(payload.path("native_launch").path("creation_filetime").isTextual());
        HttpResponse<byte[]> rejected = post(call(StrictJson.canonical(payload)));
        assertEquals(400, rejected.statusCode());
        assertEquals("invalid-payload", StrictJson.parse(rejected.body()).path("error").path("code").textValue());
        payload.set("native_launch", PythonOpaqueGameGenerationV1.toJson(game));
        byte[] originalRequest = StrictJson.canonical(payload);
        HttpResponse<byte[]> accepted = post(call(originalRequest));
        assertEquals(200, accepted.statusCode()); headers(accepted);
        var result = assertInstanceOf(ProjectionResult.Succeeded.class, ProjectionWire.decodeResult(accepted.body()));
        assertArrayEquals(CampaignMapAdmissionComposer.compose(originalRequest), result.result().bytes());
        assertTrue(StrictJson.parse(result.result().bytes()).path("game_creation_filetime").isIntegralNumber());
        assertEquals(StrictJson.UINT64_MAX,
                StrictJson.parse(result.result().bytes()).path("game_creation_filetime").bigIntegerValue());
    }

    @Test void mapHttpRejectsMissingUnknownAndWrongTypedIdentityFieldsBeforeComposition() throws Exception {
        for (String field : new String[] {"pid", "creation_filetime"}) {
            ObjectNode payload = assertInstanceOf(ObjectNode.class, StrictJson.parse(mapPayload()));
            assertInstanceOf(ObjectNode.class, payload.get("native_launch")).remove(field);
            HttpResponse<byte[]> rejected = post(call(StrictJson.canonical(payload)));
            assertEquals(400, rejected.statusCode());
            assertEquals("invalid-payload", StrictJson.parse(rejected.body()).path("error").path("code").textValue());
        }
        for (String token : new String[] {"true", "1.0", "\"12345\"", "null", "[]", "0", "4294967296"}) {
            byte[] payload = new String(mapPayload(), StandardCharsets.UTF_8)
                    .replace("\"pid\":12345", "\"pid\":" + token).getBytes(StandardCharsets.UTF_8);
            HttpResponse<byte[]> rejected = post(call(payload));
            assertEquals(400, rejected.statusCode());
            assertEquals("invalid-payload", StrictJson.parse(rejected.body()).path("error").path("code").textValue());
        }
        ObjectNode payload = assertInstanceOf(ObjectNode.class, StrictJson.parse(mapPayload()));
        assertInstanceOf(ObjectNode.class, payload.get("native_launch"))
                .put("creationFiletime", StrictJson.UINT64_MAX.toString());
        HttpResponse<byte[]> rejected = post(call(StrictJson.canonical(payload)));
        assertEquals(400, rejected.statusCode());
        assertEquals("invalid-payload", StrictJson.parse(rejected.body()).path("error").path("code").textValue());
    }

    @Test void ordinaryHostPublishesTheAbsenceOfTrustedEventSourceRoots() throws Exception {
        HttpResponse<byte[]> response = client.send(HttpRequest.newBuilder(base.resolve("context")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode()); headers(response); var result = StrictJson.parse(response.body());
        assertEquals("xar.projection-host-context/v1", result.path("schema").textValue());
        java.time.Instant.parse(result.path("observed_at_utc").textValue());
        assertTrue(result.has("event_sources")); assertTrue(result.path("event_sources").isNull());
        var request = ProjectionWire.encodeCall(new ProjectionCall(new ProjectionCall.Identity("source-unconfigured", ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED),
                ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 65536)));
        HttpResponse<byte[]> unavailable = post(request); assertEquals(503, unavailable.statusCode());
        assertEquals(ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED,
                assertInstanceOf(ProjectionResult.Rejected.class, ProjectionWire.decodeResult(unavailable.body())).identity().orElseThrow().operation());
    }

    @Test void unknownOperationIsAClosedHttpProtocolFailure() throws Exception {
        byte[] raw = new String(call(mapPayload()), StandardCharsets.UTF_8).replace("map-admission-compose", "unknown-operation").getBytes(StandardCharsets.UTF_8);
        HttpResponse<byte[]> response = post(raw); assertEquals(400, response.statusCode());
        var result = StrictJson.parse(response.body()); assertEquals("rejected", result.path("status").textValue());
        assertEquals("unsupported-operation", result.path("error").path("code").textValue());
        assertTrue(result.path("request_id").isNull()); assertTrue(result.path("operation").isNull());
    }

    @Test void largerProjectionFramingDoesNotWidenTheOriginalMapRouteGuard() throws Exception {
        HttpRequest request = HttpRequest.newBuilder(base.resolve("/v1/map-admissions/compose"))
                .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofByteArray(new byte[65_537])).build();
        assertEquals(413, client.send(request, HttpResponse.BodyHandlers.ofByteArray()).statusCode());
    }

    @Test void evidenceMetadataIsSeparateAndTheExistingContextShapeStaysStable() throws Exception {
        HttpResponse<byte[]> response = client.send(HttpRequest.newBuilder(base.resolve("evidence-grants")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode()); headers(response); var result = StrictJson.parse(response.body(), 1048576);
        assertEquals("xar.projection-host-evidence-grants/v1", result.path("schema").textValue());
        assertEquals(4, result.size()); assertTrue(result.path("grants").isArray()); assertEquals(0, result.path("grants").size());
        java.time.Instant.parse(result.path("observed_at_utc").textValue());
        HttpResponse<byte[]> context = client.send(HttpRequest.newBuilder(base.resolve("context")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        var fixed = StrictJson.parse(context.body()); assertEquals(4, fixed.size()); assertTrue(fixed.path("event_sources").isNull());
    }

    private HttpResponse<byte[]> post(byte[] raw) throws Exception {
        return client.send(HttpRequest.newBuilder(base.resolve("call")).timeout(Duration.ofSeconds(20))
                .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofByteArray(raw)).build(), HttpResponse.BodyHandlers.ofByteArray());
    }
    private static void assertProfile(com.fasterxml.jackson.databind.JsonNode identity,
            ProjectionOperation operation, int inputMaximum, int outputMaximum) {
        var matching = java.util.stream.StreamSupport.stream(identity.path("operations").spliterator(), false)
                .filter(row -> operation.wire().equals(row.path("operation").textValue())).toList();
        assertEquals(1, matching.size(), "one advertised profile required for " + operation.wire());
        var profile = matching.getFirst();
        assertTrue(profile.path("input_max_bytes").isIntegralNumber());
        assertTrue(profile.path("output_max_bytes").isIntegralNumber());
        assertEquals(inputMaximum, profile.path("input_max_bytes").intValue());
        assertEquals(outputMaximum, profile.path("output_max_bytes").intValue());
    }
    private static void headers(HttpResponse<byte[]> response) {
        assertEquals(ProjectionResource.PRODUCER, response.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals(ProjectionResource.PRODUCER_VERSION, response.headers().firstValue("X-Xar-Producer-Version").orElseThrow());
        assertEquals(ProjectionCall.SCHEMA, response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
    }
    private static byte[] call(byte[] payload) {
        return ProjectionWire.encodeCall(new ProjectionCall(new ProjectionCall.Identity("http-map-1", ProjectionOperation.MAP_ADMISSION_COMPOSE),
                ProjectionJson.object(payload, StrictJson.INPUT_MAX_BYTES)));
    }
    private static byte[] mapPayload() {
        var row = StrictJson.object(); row.put("schema", CampaignMapAdmissionComposer.REQUEST_SCHEMA);
        row.put("machine_id", "http-projection-fixture"); row.put("observed_at_utc", "2026-10-22T12:00:00Z");
        row.set("native_launch", PythonOpaqueGameGenerationV1.toJson(
                new GameGeneration(12345, new PythonOnlyUInt64(StrictJson.UINT64_MAX))));
        row.put("recording_session_id", "projection-fixture");
        row.set("actual_initial_frame", new SavedFrame("native:1", 2, 1, 53279400, 40526, "fixture-episode").toJson());
        row.put("game_map_visible", true); row.put("decision_text_visible", true); return StrictJson.canonical(row);
    }
}
