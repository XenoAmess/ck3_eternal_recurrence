package org.xar.ck3.control.wave3.planning.realmmembership;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedSummaryCodec;

final class RealmProjectionCatalogTest {
    @Test void actualServiceLoaderFindsTheSingleCatalogWithAllThreeExactOperationsAndRoleBudgets() {
        List<RealmProjectionCatalog> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type().equals(RealmProjectionCatalog.class))
                .map(provider -> (RealmProjectionCatalog) provider.get()).toList();
        assertEquals(1, providers.size(), "actual packaged provider discovery is required");
        List<RegisteredProjection> ports = providers.get(0).registrations();
        assertEquals(List.of(ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK,
                ProjectionOperation.REALM_DIFFERENCE, ProjectionOperation.REALM_DATED_SUMMARY),
                ports.stream().map(RegisteredProjection::operation).toList());
        assertEquals(List.of(1_048_576, 524_288, 524_288), ports.stream().map(RegisteredProjection::inputMaximumBytes).toList());
        assertEquals(List.of(1_048_576, 524_288, 524_288), ports.stream().map(RegisteredProjection::outputMaximumBytes).toList());
        assertEquals(65_536, StrictJson.INPUT_MAX_BYTES);
    }

    @Test void actualFeedbackFactoryIsTheCatalogProducerAndItsExactBytesReachTheFollowingSummary() throws IOException {
        JsonNode input = golden().path("bases").path("first");
        byte[] raw = SdkProjectionJson.encode(input, RealmMembershipFeedback.MAX_BYTES);
        byte[] feedback = succeeded(ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK, raw);
        RealmMembershipFeedback.VerifiedFeedback verified = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class,
                RealmMembershipFeedback.project(raw));
        assertArrayEquals(verified.wireJson(), feedback, "the registered factory must return its original result bytes");
        var summaryRequest = StrictJson.object();
        summaryRequest.set("feedback", StrictJson.parse(feedback, RealmMembershipFeedback.MAX_BYTES));
        summaryRequest.set("current_source_frame", input.get("source_frame"));
        byte[] summary = succeeded(ProjectionOperation.REALM_DATED_SUMMARY,
                SdkProjectionJson.encode(summaryRequest, RealmDifferenceCodec.MAX_BYTES));
        byte[] typedSummary = DatedSummaryCodec.encode(DatedRealmSummary.fromVerified(verified,
                SdkProjectionJson.encode(input.get("source_frame"), RealmDifferenceCodec.MAX_BYTES)));
        assertArrayEquals(typedSummary, summary, () -> payloadEvidence(typedSummary, summary));
    }

    @Test void theDifferenceRegistrationConsumesTheActualOriginalBeforeAndAfterObservations() throws IOException {
        JsonNode captured = golden();
        JsonNode before = captured.path("cases").get(0).path("expected").get("observation");
        JsonNode after = captured.path("cases").get(2).path("expected").get("observation");
        var request = StrictJson.object(); request.set("previous", before); request.set("observation", after);
        JsonNode result = StrictJson.parse(succeeded(ProjectionOperation.REALM_DIFFERENCE,
                SdkProjectionJson.encode(request, RealmDifferenceCodec.MAX_BYTES)), RealmDifferenceCodec.MAX_BYTES);
        assertEquals(captured.path("cases").get(2).path("expected").get("difference"), result);
    }

    @Test void opaqueFloatBooleanAndLargeIntegerTokensSurviveTheActualFeedbackToSummaryRegistrations() throws IOException {
        for (String token : List.of("1.0", "true", "9007199254740993")) {
            var request = golden().path("bases").path("first").deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode) request.get("source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            String source = new String(SdkProjectionJson.encode(request, RealmMembershipFeedback.MAX_BYTES), StandardCharsets.UTF_8);
            byte[] raw = source.replace("\"__RAW_TOKEN__\"", token).getBytes(StandardCharsets.UTF_8);
            JsonNode feedback = StrictJson.parse(succeeded(ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK, raw),
                    RealmMembershipFeedback.MAX_BYTES);
            var summaryRequest = StrictJson.object(); summaryRequest.set("feedback", feedback);
            summaryRequest.set("current_source_frame", feedback.path("observation").get("source_frame"));
            byte[] wireSummary = succeeded(ProjectionOperation.REALM_DATED_SUMMARY,
                    SdkProjectionJson.encode(summaryRequest, RealmDifferenceCodec.MAX_BYTES));
            JsonNode summary = StrictJson.parse(wireSummary, RealmDifferenceCodec.MAX_BYTES);
            RealmMembershipFeedback.VerifiedFeedback verified = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class,
                    RealmMembershipFeedback.project(raw));
            byte[] typedSummary = DatedSummaryCodec.encode(DatedRealmSummary.fromVerified(verified,
                    SdkProjectionJson.encode(StrictJson.parse(raw, RealmMembershipFeedback.MAX_BYTES).get("source_frame"),
                            RealmDifferenceCodec.MAX_BYTES)));
            assertArrayEquals(typedSummary, wireSummary, () -> token + " " + payloadEvidence(typedSummary, wireSummary));
            JsonNode retained = summary.path("source_frame").get("sdk_extension");
            assertEquals(StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)), retained);
            assertEquals(token.equals("1.0"), retained.isFloatingPointNumber());
            assertEquals(token.equals("true"), retained.isBoolean());
            assertEquals(token.equals("9007199254740993"), retained.isIntegralNumber());
        }
    }

    @Test void actualRegistryRejectsOneByteOverEachRoleInsteadOfRaisingTheSharedDefault() {
        for (ProjectionOperation operation : List.of(ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK,
                ProjectionOperation.REALM_DIFFERENCE, ProjectionOperation.REALM_DATED_SUMMARY)) {
            RegisteredProjection port = port(operation);
            String json = switch (operation) {
                case REALM_MEMBERSHIP_FEEDBACK -> "{\"snapshot\":{},\"source_frame\":null,\"faction_result\":null,\"previous\":null}";
                case REALM_DIFFERENCE -> "{\"previous\":null,\"observation\":null}";
                case REALM_DATED_SUMMARY -> "{\"feedback\":null,\"current_source_frame\":null}";
                default -> throw new AssertionError(operation);
            };
            byte[] prefix = json.getBytes(StandardCharsets.UTF_8);
            byte[] exact = Arrays.copyOf(prefix, port.inputMaximumBytes());
            Arrays.fill(exact, prefix.length, exact.length, (byte) ' ');
            assertInstanceOf(ProjectionResult.Succeeded.class, port.execute(call(operation, exact)));
            byte[] over = Arrays.copyOf(exact, exact.length + 1); over[over.length - 1] = ' ';
            ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, port.execute(call(operation, over)));
            assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, rejected.error().code());
            assertEquals(call(operation, over).identity(), rejected.identity().orElseThrow());
        }
    }

    @Test void decodedMalformedShapeAndExplicitProjectRefusalKeepDistinctErrorCategories() {
        ProjectionResult.Rejected decoded = assertInstanceOf(ProjectionResult.Rejected.class,
                port(ProjectionOperation.REALM_DIFFERENCE).execute(call(ProjectionOperation.REALM_DIFFERENCE,
                        "{\"previous\":null}".getBytes(StandardCharsets.UTF_8))));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, decoded.error().code());
        ProjectionResult.Rejected projected = assertInstanceOf(ProjectionResult.Rejected.class,
                port(ProjectionOperation.REALM_DATED_SUMMARY).execute(call(ProjectionOperation.REALM_DATED_SUMMARY,
                        "{\"feedback\":{\"status\":\"available\",\"schema\":\"wrong\"},\"current_source_frame\":null}"
                                .getBytes(StandardCharsets.UTF_8))));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, projected.error().code());
    }

    @Test void unexpectedObservationFormatterFailureCannotBecomeAnUnavailableDomainResult() throws IOException {
        JsonNode previous = golden().path("cases").get(0).path("expected").get("observation");
        var broken = new com.fasterxml.jackson.databind.node.ObjectNode(
                com.fasterxml.jackson.databind.node.JsonNodeFactory.instance,
                new java.util.HashMap<String, JsonNode>() {
                    private static final long serialVersionUID = 1L;
                    @Override public JsonNode get(Object key) { throw new IllegalArgumentException("unexpected formatter sentinel"); }
                });
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> RealmDifference.compare(previous, broken));
        assertEquals("unexpected formatter sentinel", failure.getMessage());
    }

    private static String payloadEvidence(byte[] typed, byte[] wire) {
        return "REALM_TYPED_BASE64=" + java.util.Base64.getEncoder().encodeToString(typed)
                + " REALM_WIRE_BASE64=" + java.util.Base64.getEncoder().encodeToString(wire);
    }

    private static RegisteredProjection port(ProjectionOperation operation) {
        return new RealmProjectionCatalog().registrations().stream().filter(port -> port.operation() == operation).findFirst().orElseThrow();
    }
    private static ProjectionCall call(ProjectionOperation operation, byte[] raw) {
        return new ProjectionCall(new ProjectionCall.Identity("realm-consumer-regression:1", operation),
                ProjectionJson.object(raw, RealmMembershipFeedback.MAX_BYTES + 1));
    }
    private static byte[] succeeded(ProjectionOperation operation, byte[] raw) {
        return assertInstanceOf(ProjectionResult.Succeeded.class, port(operation).execute(call(operation, raw))).result().bytes();
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = RealmProjectionCatalogTest.class.getResourceAsStream("/realmmembership/original-producer-golden.json")) {
            assertNotNull(input, "actual original producer resource required; never skip");
            return StrictJson.parse(input.readAllBytes(), RealmMembershipFeedback.MAX_BYTES);
        }
    }
}

