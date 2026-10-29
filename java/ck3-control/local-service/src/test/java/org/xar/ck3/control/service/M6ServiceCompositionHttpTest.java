package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.InputStream;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m6.M6ServiceIntegration;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;

/** Must run on the shared Quarkus host; direct evaluation is not HTTP qualification. */
@QuarkusTest
class M6ServiceCompositionHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path persistence;

    @Test void actualTwoOriginalCompositionsTraverseHostClientAndReopenedWireWithUnknownPreserved() throws Exception {
        G2Request original = G2Wire.decodeRequest(fixture("/g2-http/M6.request.json"));
        var evidence = M6SourceProducer.fromEvidencePacket(original.payload().bytes(), original.source());
        List<M6ServiceIntegration.EpisodeSources> sources = evidence.episodes().stream().map(episode -> {
            JsonNode nativeRead = StrictJson.parse(episode.originalResolved().bytes()).at("/latest_instance_observation/native_observation");
            return new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(), new M6TerminalSourceComposition.Inputs(
                    Optional.of(ProjectionJson.object(StrictJson.canonical(nativeRead), M6SourceProducer.MAX_BYTES)), Optional.empty(), Optional.empty(), Optional.empty()));
        }).toList();
        byte[] payload = M6ServiceIntegration.encode(original.payload().bytes(), original.source().sourceRef(), sources);
        G2Request request = request("m6-service-http-originals", payload, original.source());
        try (G2JavaClient client = client()) {
            var call = client.evaluateWithEvidence(request);
            assertTrue(call.evidence().actualHttpInvoked()); assertTrue(call.evidence().responseComplete()); assertEquals(200, call.evidence().httpStatus().orElseThrow());
            assertEquals(request.source(), call.response().source());
            JsonNode result = StrictJson.parse(call.response().result().bytes(), M6SourceProducer.MAX_BYTES);
            JsonNode oracle = StrictJson.parse(fixture("/actual-original-producers.json"));
            assertEquals(oracle.get("compositions"), result.get("compositions"));
            assertFalse(result.get("whole_m6_complete").booleanValue()); assertFalse(result.get("grants_submission_authority").booleanValue());
            assertFalse(result.get("request_retried").booleanValue()); assertFalse(result.get("ledger_committed").booleanValue());
            assertFalse(result.at("/assessment/attributed_success_evidence").booleanValue());
            byte[] wire = G2Wire.encodeResponse(call.response()); Path saved = persistence.resolve("m6-service-http-response.json");
            Files.write(saved, wire); byte[] reopened = Files.readAllBytes(saved); assertArrayEquals(wire, reopened);
            assertArrayEquals(call.response().result().bytes(), G2Wire.decodeResponse(reopened).result().bytes());
            assertTrue(result.at("/compositions/0/current_instance_observation").isNull());
            assertEquals(0, result.at("/compositions/1/current_instance_observation/native_status_raw").intValue());
        }
    }

    @Test void malformedCopiedJournalGenerationIsActualHttpRefusalWithoutFallbackOrReplay() throws Exception {
        G2Request original = G2Wire.decodeRequest(fixture("/g2-http/M6.request.json"));
        var episode = M6SourceProducer.fromEvidencePacket(original.payload().bytes(), original.source()).episodes().getFirst();
        ObjectNode journal = StrictJson.object(); journal.put("schema", "xar.ck3.sway-completion-termination.v1");
        journal.put("build_version", M6SourceProducer.BUILD); journal.put("executable_sha256", M6SourceProducer.EXE); journal.put("available", true); journal.put("retention_gap", false);
        journal.put("actor_character_id", episode.identity().actorCharacterId()); journal.put("target_character_id", episode.identity().targetCharacterId());
        journal.put("scheme_instance_id", episode.identity().schemeInstanceId()); journal.put("scheme_instance_generation", true); journal.putArray("records");
        var inputs = new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.empty(), Optional.of(ProjectionJson.object(StrictJson.canonical(journal), M6SourceProducer.MAX_BYTES)), Optional.empty());
        byte[] payload = M6ServiceIntegration.encode(original.payload().bytes(), original.source().sourceRef(), List.of(new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(), inputs)));
        G2Request request = request("m6-service-http-reject", payload, original.source());
        try (G2JavaClient client = client()) {
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(request));
            assertEquals(G2ClientException.Reason.HTTP_REJECTED, failure.reason());
            assertEquals(G2HttpError.Code.DOMAIN_REJECTED, failure.httpError().orElseThrow().code());
            assertTrue(failure.evidence().actualHttpInvoked()); assertTrue(failure.evidence().responseComplete());
        }
    }

    private G2JavaClient client() { return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES)); }
    private static G2Request request(String id, byte[] payload, G2Source original) throws Exception {
        ExactRef ref = new ExactRef("fixture:" + id, payload.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload)));
        return new G2Request(id, Milestone.M6, new G2Source(original.machineId(), original.observedAtUtc(), original.exactBuild(), ref), ProjectionJson.object(payload, M6SourceProducer.MAX_BYTES));
    }
    private static byte[] fixture(String name) throws Exception {
        try (InputStream input = M6ServiceCompositionHttpTest.class.getResourceAsStream(name)) {
            if (input == null) throw new IllegalStateException("actual producer fixture required; no skip or fallback: " + name); return input.readAllBytes();
        }
    }
}
