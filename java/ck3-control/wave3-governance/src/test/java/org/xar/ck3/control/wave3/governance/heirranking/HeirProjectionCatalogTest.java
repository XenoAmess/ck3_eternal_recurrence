package org.xar.ck3.control.wave3.governance.heirranking;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnosticConsumerPort;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;

final class HeirProjectionCatalogTest {
    private static ProjectionDispatcher dispatcher() {
        return ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
    }

    @Test void actualProducerVectorsTraverseTheProductionDispatcherAndItsExactWire() throws IOException {
        verify(ProjectionOperation.GOVERNANCE_HEIR_INTAKE, "/heirintake/producer-golden.json", "expected", 7);
        verify(ProjectionOperation.GOVERNANCE_HEIR_RANK, "/heirranking/producer-golden.json", "expected_choices", 7);
        verify(ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC, "/heirdiagnostic/producer-golden.json", "expected", 3);
        var operations = Set.of(ProjectionOperation.GOVERNANCE_HEIR_INTAKE,
                ProjectionOperation.GOVERNANCE_HEIR_RANK, ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC);
        var profiles = dispatcher().profiles().stream().filter(profile -> operations.contains(profile.operation())).toList();
        for (var profile : profiles) {
            assertEquals(65_536, profile.inputMaximumBytes());
            assertEquals(65_536, profile.outputMaximumBytes());
        }
        assertEquals(3, profiles.size(), "the production descriptor must discover all three unique heir ports");
    }

    private static void verify(ProjectionOperation operation, String resource, String expected, int cases) throws IOException {
        JsonNode golden = golden(resource);
        assertEquals(cases, golden.path("cases").size());
        int index = 0;
        for (JsonNode vector : golden.path("cases")) {
            var identity = new ProjectionCall.Identity("heir-dispatch-" + operation.name() + "-" + index++, operation);
            byte[] payload = StrictJson.canonical(vector.path("input"));
            var call = new ProjectionCall(identity, ProjectionJson.object(payload, 65_536));
            byte[] raw = ProjectionWire.encodeCall(call);
            var result = assertInstanceOf(ProjectionResult.Succeeded.class, dispatcher().dispatch(raw));
            assertEquals(identity, result.identity());
            assertArrayEquals(StrictJson.canonical(vector.path(expected)), result.result().bytes(), vector.path("name").textValue());
            var decoded = assertInstanceOf(ProjectionResult.Succeeded.class,
                    ProjectionWire.decodeResult(ProjectionWire.encodeResult(result)));
            assertEquals(identity, decoded.identity());
            assertArrayEquals(result.result().bytes(), decoded.result().bytes(), "result raw token survives the actual host wire");
        }
    }

    @Test void wrongFieldTypesAndMissingProofAreRejectedByTheRealDomainCodec() throws IOException {
        JsonNode input = golden("/heirdiagnostic/producer-golden.json").path("cases").get(0).path("input");
        ObjectNode missing = ((ObjectNode) input).deepCopy(); missing.remove("choice");
        reject(ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC, StrictJson.canonical(missing));
        String raw = new String(StrictJson.canonical(input), StandardCharsets.UTF_8);
        String needle = "\"native_revision\":7";
        assertTrue(raw.contains(needle), "send the existing original token, never a reconstructed substitute");
        for (String wrong : List.of("true", "7.0", "7e0", "\"7\"", "null")) {
            reject(ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC,
                    raw.replace(needle, "\"native_revision\":" + wrong).getBytes(StandardCharsets.UTF_8));
        }
    }

    private static void reject(ProjectionOperation operation, byte[] payload) {
        var identity = new ProjectionCall.Identity("heir-dispatch-reject", operation);
        var call = new ProjectionCall(identity, ProjectionJson.object(payload, 65_536));
        var result = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher().dispatch(ProjectionWire.encodeCall(call)));
        assertEquals(identity, result.identity().orElseThrow());
        assertEquals("DOMAIN_REJECTED", result.error().code().name(),
                "the negative must execute the registered production domain codec");
    }

    @Test void anInternalPolicyInvariantFailureIsNotAValueErrorDomainRefusal() throws IOException {
        ObjectNode input = ((ObjectNode) golden("/heirranking/producer-golden.json")
                .path("cases").get(0).path("input")).deepCopy();
        ((ObjectNode) input.path("projection").path("rows").get(0)).remove("possible_alliance_pairs");
        var identity = new ProjectionCall.Identity("heir-internal-project-failure", ProjectionOperation.GOVERNANCE_HEIR_RANK);
        var call = new ProjectionCall(identity, ProjectionJson.object(StrictJson.canonical(input), 65_536));
        var result = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher().dispatch(ProjectionWire.encodeCall(call)));
        assertEquals("PROJECTION_FAILED", result.error().code().name());
        assertEquals(identity, result.identity().orElseThrow());
        assertFalse(result.error().message().contains("eligible marriage"), "internal invariant details cannot be a public business refusal");
    }

    @Test void typedRequestsRetainTheirOriginalBytesAndImmutableDomainFacts() throws IOException {
        JsonNode rank = golden("/heirranking/producer-golden.json").path("cases").get(0);
        byte[] rankInput = StrictJson.canonical(rank.path("input"));
        var ranking = HeirCandidateRankingConsumerPort.decode(rankInput);
        rankInput[0] = '[';
        ranking.sourceJson()[0] = '[';
        assertThrows(UnsupportedOperationException.class, () -> ranking.legalRows().clear());
        assertArrayEquals(StrictJson.canonical(rank.path("expected_choices")),
                HeirCandidateRankingConsumerPort.evaluate(ranking).choices());
        JsonNode intake = golden("/heirintake/producer-golden.json").path("cases").get(0);
        byte[] intakeInput = StrictJson.canonical(intake.path("input"));
        var pool = HeirCandidateIntakeConsumerPort.decode(intakeInput);
        intakeInput[0] = '[';
        pool.sourceJson()[0] = '[';
        assertThrows(UnsupportedOperationException.class, () -> pool.legalRows().clear());
        assertArrayEquals(StrictJson.canonical(intake.path("expected")),
                HeirCandidateIntakeConsumerPort.evaluate(pool).result());
        JsonNode diagnostic = golden("/heirdiagnostic/producer-golden.json").path("cases").get(0);
        byte[] diagnosticInput = StrictJson.canonical(diagnostic.path("input"));
        var proof = HeirCandidateDiagnosticConsumerPort.decode(diagnosticInput);
        diagnosticInput[0] = '[';
        proof.sourceJson()[0] = '[';
        assertThrows(UnsupportedOperationException.class, () -> proof.rows().clear());
        assertArrayEquals(StrictJson.canonical(diagnostic.path("expected")),
                HeirCandidateDiagnosticConsumerPort.evaluate(proof).diagnostic());
    }

    @Test void roleLimitDoesNotBecomeTheLargerGoldenCollectionLimit() {
        String oversized = "{\"extension\":\"" + "x".repeat(65_536) + "\"}";
        var identity = new ProjectionCall.Identity("heir-dispatch-overflow", ProjectionOperation.GOVERNANCE_HEIR_INTAKE);
        var call = new ProjectionCall(identity, ProjectionJson.object(oversized.getBytes(StandardCharsets.UTF_8), 98_304));
        var result = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher().dispatch(ProjectionWire.encodeCall(call)));
        assertEquals("PAYLOAD_TOO_LARGE", result.error().code().name());
        assertEquals(identity, result.identity().orElseThrow());
    }

    private static JsonNode golden(String path) throws IOException {
        try (var input = HeirProjectionCatalogTest.class.getResourceAsStream(path)) {
            if (input == null) { throw new IOException("actual producer golden required; no skip or Python fallback: " + path); }
            return StrictJson.parse(input.readNBytes(98_305), 98_304);
        }
    }
}
