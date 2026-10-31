package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.ObservationProvenanceCodec;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;

/**
 * Tests the new ObservationProvenance.FreshSnapshotQuery codec roundtrip and strict validation
 * using actual fixture-generated data. Does not test Root qualification or Factory verification.
 */
final class NativeFreshProvenanceCodec179Test {
    @TempDir Path root;

    private ActionWriterIntegrationFixture createFixture() throws IOException {
        var profile = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ExactCk3Build.CK3_12004.executableSha256(), "ck3-1.20.0.4-msvc-x64",
                ignored -> List.of(), ignored -> { throw new AssertionError("no additional ordinary READ installed"); },
                Optional.of(ExactCk3Build.CK3_12004.version()), Set.of(NativeFreshSnapshotPort.CAPABILITY));
        var fixture = new ActionWriterIntegrationFixture(root.resolve("codec-test"), false, profile);
        fixture.configureSoftwareFreshRead179("success");
        return fixture;
    }

    @Test void freshSnapshotQueryCodecRoundtripAndStrictValidation() throws Exception {
        try (var fixture = createFixture()) {
            var command = fixture.command("codec-test-action");
            var transport = fixture.physicalInputs().transport();

            // Execute mutation to get setter ACK
            var receipt = fixture.coordinator.execute(command);
            var setterAck = receipt.ack().orElseThrow();
            assertTrue(setterAck.nativeOk());

            // Perform actual fresh read
            var readResult = transport.readFreshFullState(Instant.now().plusSeconds(15));
            var received = assertInstanceOf(NativeFreshSnapshotPort.Received.class, readResult);

            // Verify relationship between setter and read
            NativeFreshSnapshotPort.verifyAfter(setterAck, received);

            // Preserve actual ACKs in archive
            var setterRef = fixture.archive.preserve(setterAck);
            var readAckRef = fixture.archive.preserve(received.acknowledgement());

            // Construct FreshSnapshotQuery with LiveAfterSetter basis
            var requestId = received.acknowledgement().requestId();
            var readAck = received.acknowledgement();
            var snapshotReceived = received.snapshotReceived();
            var basis = new ObservationProvenance.LiveAfterSetter(setterRef);

            var query = new ObservationProvenance.FreshSnapshotQuery(
                    requestId, readAckRef, snapshotReceived, basis);

            // Test independentOf
            assertTrue(query.independentOf(setterAck.requestId()));
            assertFalse(query.independentOf(requestId));

            // Encode and decode roundtrip
            var encoded = ObservationProvenanceCodec.encode(query);
            var decoded = ObservationProvenanceCodec.decode(encoded);

            // Assert decoded is FreshSnapshotQuery with LiveAfterSetter
            var decodedQuery = assertInstanceOf(ObservationProvenance.FreshSnapshotQuery.class, decoded);
            assertEquals(requestId, decodedQuery.requestId());
            assertEquals(readAckRef, decodedQuery.readAcknowledgement());
            assertEquals(snapshotReceived.order(), decodedQuery.snapshotReceived().order());
            assertEquals(snapshotReceived.observedAt(), decodedQuery.snapshotReceived().observedAt());

            var decodedBasis = assertInstanceOf(ObservationProvenance.LiveAfterSetter.class, decodedQuery.basis());
            assertEquals(setterRef, decodedBasis.setterAcknowledgement());

            // Test strict validation: missing field
            var missingField = encoded.deepCopy();
            missingField.remove("request_id");
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(missingField));

            // Test strict validation: extra field
            var extraField = encoded.deepCopy();
            extraField.put("extra_field", "unexpected");
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(extraField));

            // Test strict validation: wrong basis kind
            var wrongBasis = encoded.deepCopy();
            var basisNode = (ObjectNode) wrongBasis.get("basis");
            basisNode.put("kind", "unknown_basis");
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(wrongBasis));

            var wrongAcknowledgementRole = encoded.deepCopy();
            wrongAcknowledgementRole.put("read_acknowledgement", true);
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(wrongAcknowledgementRole));
            var wrongEventOrderType = encoded.deepCopy();
            ((ObjectNode) wrongEventOrderType.get("snapshot_received")).put("order", 1);
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(wrongEventOrderType));

            // Test plain Query remains plain Query
            var plainQuery = new ObservationProvenance.Query("plain-request-id");
            var plainEncoded = ObservationProvenanceCodec.encode(plainQuery);
            var plainDecoded = ObservationProvenanceCodec.decode(plainEncoded);
            var decodedPlainQuery = assertInstanceOf(ObservationProvenance.Query.class, plainDecoded);
            assertEquals("plain-request-id", decodedPlainQuery.requestId());

            // Verify archived read ACK can be loaded
            var loadedReadAck = fixture.archive.load(readAckRef);
            assertEquals(readAck, loadedReadAck);
        }
    }
}