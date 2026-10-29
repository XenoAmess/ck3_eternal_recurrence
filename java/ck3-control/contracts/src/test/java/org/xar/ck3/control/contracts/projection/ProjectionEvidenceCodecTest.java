package org.xar.ck3.control.contracts.projection;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionEvidenceCodecTest {
    private static ProjectionEvidenceGrant grant(String file) {
        return new ProjectionEvidenceGrant(Path.of(file).toAbsolutePath(), 3, "a".repeat(64), "unknown", ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
    }
    @Test void exactMetadataRoundTripsWithoutGrantingCurrentMachineOrBroadRoots() {
        var grant = grant("historical-facts.json");
        assertEquals(List.of(grant), ProjectionEvidenceCodec.decode(ProjectionEvidenceCodec.encode(List.of(grant))));
        assertEquals("unknown", grant.originMachineId());
        assertThrows(IllegalArgumentException.class, () -> new ProjectionEvidenceGrant(Path.of("relative"), 3, "a".repeat(64), "unknown", grant.role()));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionEvidenceGrant(grant.path(), 9007199254740992L, grant.sha256(), "unknown", grant.role()));
        assertThrows(IllegalArgumentException.class, () -> ProjectionEvidenceCodec.validated(List.of(grant, grant)));
    }
    @Test void wrongFieldTypesAndUnknownRolesCannotBecomeReadGrants() {
        String valid = new String(ProjectionEvidenceCodec.encode(List.of(grant("facts.json"))), StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "3.0", "3e0", "\"3\"", "null", "-1", "9007199254740992")) {
            assertThrows(IllegalArgumentException.class, () -> ProjectionEvidenceCodec.decode(valid.replace("\"bytes\":3", "\"bytes\":" + wrong).getBytes(StandardCharsets.UTF_8)));
        }
        for (String changed : List.of(valid.replace("event-source-facts", "unknown-role"),
                valid.replace("\"grants\":", "\"extra\":null,\"grants\":"),
                valid.replace("\"bytes\":3", "\"bytes\":3,\"bytes\":3"))) {
            assertThrows(IllegalArgumentException.class, () -> ProjectionEvidenceCodec.decode(changed.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void oneProjectionSnapshotStaysImmutableAcrossLaterOfflinePublication() {
        var first = grant("facts-first.json"); var second = grant("facts-second.json");
        AtomicReference<List<ProjectionEvidenceGrant>> published = new AtomicReference<>(List.of(first));
        var context = new EventSourceReadContext("fixture-machine", Path.of("state-root").toAbsolutePath(),
                Path.of("stock-root").toAbsolutePath(), published::get);
        List<ProjectionEvidenceGrant> projectionSnapshot = context.evidenceGrants(); published.set(List.of(second));
        assertEquals(List.of(first), projectionSnapshot); assertEquals(List.of(second), context.evidenceGrants());
        assertThrows(UnsupportedOperationException.class, () -> projectionSnapshot.add(second));
        published.set(List.of(first, first));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE,
                assertThrows(ProjectionProtocolException.class, context::evidenceGrants).code());
    }
}
