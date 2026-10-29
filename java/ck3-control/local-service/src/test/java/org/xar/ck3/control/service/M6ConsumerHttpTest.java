package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.Base64;
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
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.g2.m6.M6LedgerConsumer;
import org.xar.ck3.control.g2.m6.M6SourceProducer;

/** Same Quarkus host/client and actual Java following consumer; no duplicated domain or canonical writer. */
@QuarkusTest
class M6ConsumerHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path persistence;

    @Test void originalProducerHttpThenActualConsumerAndReopenedJsonPreserveInheritedEpisodes() throws Exception {
        G2Request original = G2Wire.decodeRequest(fixture("M6.request.json"));
        assertEquals(Milestone.M6, original.milestone());
        OriginalArtifacts artifacts = originals(original);
        ObjectNode ledger = object(StrictJson.parse(artifacts.ledger()));
        ObjectNode current = object(ledger.get("resolved"));
        JsonNode previous = current.get("previous_interventions").deepCopy();
        current.put("next_turn_consumed", false);
        object(current.get("first_named_gain_intervention")).put("next_turn_consumed", false);
        byte[] pending = StrictJson.canonical(ledger, M6SourceProducer.MAX_BYTES);
        G2Request pendingRequest = request("m6-consumer-before", pending, original.source(), "synthetic-pending-m6.json", artifacts);
        G2Source pendingSource = ledgerSource(original.source(), "synthetic-pending-m6.json", pending);
        try (G2JavaClient client = client()) {
            var before = client.evaluateWithEvidence(pendingRequest);
            assertTrue(before.evidence().actualHttpInvoked()); assertTrue(before.evidence().responseComplete());
            assertEquals(pendingRequest.source(), before.response().source());
            assertFalse(StrictJson.parse(before.response().result().bytes()).get("whole_m6_complete").booleanValue());
            var update = M6LedgerConsumer.followingTurn(pending, pendingSource, 40526,
                    new Stamp(BigInteger.valueOf(5000), 53290000), M6LedgerConsumer.TurnKind.ORDINARY_AUTO);
            assertTrue(update.observationsConsumed() >= 2); assertFalse(update.ledgerCommitted()); assertFalse(update.actionAuthorized());
            byte[] derived = update.ledger().bytes();
            Path saved = persistence.resolve("derived-ordinary-following.json");
            Files.write(saved, derived, StandardOpenOption.CREATE_NEW);
            byte[] reopened = Files.readAllBytes(saved); assertArrayEquals(derived, reopened);
            G2Request afterRequest = request("m6-consumer-reopened", reopened, original.source(), saved.toString(), artifacts);
            G2Source reopenedSource = ledgerSource(original.source(), saved.toString(), reopened);
            var after = client.evaluateWithEvidence(afterRequest);
            assertTrue(after.evidence().actualHttpInvoked()); assertEquals(200, after.evidence().httpStatus().orElseThrow());
            assertEquals(afterRequest.source(), after.response().source());
            assertEquals(previous, StrictJson.parse(reopened).at("/resolved/previous_interventions"));
            var evidence = M6SourceProducer.fromClosedLedger(reopened, reopenedSource);
            assertEquals(2, evidence.episodes().size());
            assertTrue(evidence.episodes().getFirst().firstNamedGain().orElseThrow().consumption().nextTurnConsumed());
            assertEquals(0, evidence.episodes().get(1).identity().schemeInstanceGeneration());
            assertEquals(new BigInteger("11680299756822511911"),
                    StrictJson.parse(reopened).at("/resolved/native_receipt/post_container_generation").bigIntegerValue());
            assertFalse(StrictJson.parse(after.response().result().bytes()).get("evidence_packet_ready").booleanValue());
            assertFalse(StrictJson.parse(after.response().result().bytes()).get("whole_m6_complete").booleanValue());
            var repeat = M6LedgerConsumer.followingTurn(reopened, reopenedSource, 40526,
                    new Stamp(BigInteger.valueOf(5001), 53290001), M6LedgerConsumer.TurnKind.ORDINARY_AUTO);
            assertEquals(0, repeat.observationsConsumed()); assertArrayEquals(reopened, repeat.ledger().bytes());
            assertArrayEquals(afterRequest.payload().bytes(), G2Wire.decodeRequest(G2Wire.encodeRequest(afterRequest)).payload().bytes());
        }
    }

    @Test void malformedGenerationIsTypedActualHttpRefusalAndObservationOnlyCannotConsume() throws Exception {
        G2Request original = G2Wire.decodeRequest(fixture("M6.request.json"));
        OriginalArtifacts artifacts = originals(original);
        byte[] sourceBytes = artifacts.ledger();
        G2Source originalLedgerSource = new G2Source(original.source().machineId(), original.source().observedAtUtc(),
                original.source().exactBuild(), artifacts.ledgerRef());
        var readOnly = M6LedgerConsumer.followingTurn(sourceBytes, originalLedgerSource, 40526,
                new Stamp(BigInteger.valueOf(5000), 53290000), M6LedgerConsumer.TurnKind.OBSERVATION_ONLY);
        assertArrayEquals(sourceBytes, readOnly.ledger().bytes()); assertEquals(0, readOnly.observationsConsumed());
        ObjectNode wrong = object(StrictJson.parse(sourceBytes));
        object(wrong.at("/resolved/native_receipt")).put("scheme_instance_generation", true);
        byte[] invalid = StrictJson.canonical(wrong, M6SourceProducer.MAX_BYTES);
        G2Request invalidRequest = request("m6-invalid-generation", invalid, original.source(), "synthetic-bool-generation.json", artifacts);
        try (G2JavaClient client = client()) {
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(invalidRequest));
            assertEquals(G2ClientException.Reason.HTTP_REJECTED, failure.reason());
            assertEquals(G2HttpError.Code.DOMAIN_REJECTED, failure.httpError().orElseThrow().code());
            assertTrue(failure.evidence().actualHttpInvoked()); assertTrue(failure.evidence().responseComplete());
        }
    }

    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }
    private static G2Request request(String id, byte[] ledger, G2Source original, String path,
            OriginalArtifacts artifacts) throws Exception {
        G2Source nested = ledgerSource(original, path, ledger);
        byte[] payload = M6SourceProducer.encodeEvidencePacket(ledger, nested.sourceRef(), artifacts.ordinaryAuto(),
                artifacts.ordinaryRef(), artifacts.binding());
        ExactRef packetRef = new ExactRef(path + ".packet", payload.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload)));
        G2Source source = new G2Source(original.machineId(), original.observedAtUtc(), original.exactBuild(), packetRef);
        return new G2Request(id, Milestone.M6, source, ProjectionJson.object(payload, M6SourceProducer.MAX_BYTES));
    }
    private static G2Source ledgerSource(G2Source original, String path, byte[] ledger) throws Exception {
        return new G2Source(original.machineId(), original.observedAtUtc(), original.exactBuild(),
                new ExactRef(path, ledger.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(ledger))));
    }
    private record OriginalArtifacts(byte[] ledger, ExactRef ledgerRef, byte[] ordinaryAuto, ExactRef ordinaryRef,
            M6SourceProducer.OrdinaryStartBinding binding) { }
    private static OriginalArtifacts originals(G2Request request) {
        var evidence = M6SourceProducer.fromEvidencePacket(request.payload().bytes(), request.source());
        JsonNode packet = StrictJson.parse(request.payload().bytes(), M6SourceProducer.MAX_BYTES);
        ExactRef ledgerRef = ExactRef.fromJson(packet.at("/ledger/source_ref"));
        JsonNode ordinary = packet.at("/ordinary_start_sources/0");
        ExactRef ordinaryRef = ExactRef.fromJson(ordinary.get("source_ref"));
        byte[] raw = Base64.getDecoder().decode(ordinary.get("original_bytes_base64").textValue());
        JsonNode admitted = ordinary.get("admitted_binding");
        var binding = new M6SourceProducer.OrdinaryStartBinding(
                StrictJson.integer(admitted.get("actor_character_id"), 1, 0xffff_fffeL),
                StrictJson.text(admitted.get("episode_run_id")), StrictJson.integer(admitted.get("game_pid"), 1, 0xffff_ffffL));
        return new OriginalArtifacts(evidence.originalLedger().bytes(), ledgerRef, raw, ordinaryRef, binding);
    }
    private static byte[] fixture(String name) throws IOException {
        try (InputStream input = M6ConsumerHttpTest.class.getResourceAsStream("/g2-http/" + name)) {
            if (input == null) { throw new IOException("actual Java producer capture is required: " + name + "; no fallback or skip"); }
            return input.readAllBytes();
        }
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "M6 consumer JSON object required"); return (ObjectNode) value;
    }
}
