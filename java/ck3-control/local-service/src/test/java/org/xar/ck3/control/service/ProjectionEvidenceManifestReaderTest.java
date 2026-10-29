package org.xar.ck3.control.service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionEvidenceManifestReaderTest {
    @TempDir Path directory;
    @Test void fixedManifestRefreshesWithoutHostRestartAndOldProjectionSnapshotIsStable() throws Exception {
        Path manifest = directory.resolve("evidence-grants.json");
        var first = new ProjectionEvidenceGrant(directory.resolve("first.json").toAbsolutePath(), 1, "a".repeat(64), "unknown", ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        var second = new ProjectionEvidenceGrant(directory.resolve("second.json").toAbsolutePath(), 2, "b".repeat(64), "fixture-machine", ProjectionEvidenceRole.UI_RECOVERY_AFTER);
        Files.write(manifest, ProjectionEvidenceCodec.encode(List.of(first)));
        var reader = new ProjectionEvidenceManifestReader(manifest.toAbsolutePath());
        var original = reader.currentGrants();
        Files.write(manifest, ProjectionEvidenceCodec.encode(List.of(second)));
        assertEquals(List.of(first), original); assertEquals(List.of(second), reader.currentGrants());
        assertFalse(Files.exists(first.path()), "manifest pins do not themselves read or qualify their referenced files");
    }
    @Test void missingMalformedAndOversizedFixedMetadataStayUnavailable() throws Exception {
        Path manifest = directory.resolve("fixed.json");
        var reader = new ProjectionEvidenceManifestReader(manifest.toAbsolutePath());
        assertThrows(ProjectionProtocolException.class, reader::currentGrants);
        Files.writeString(manifest, "{}"); assertThrows(ProjectionProtocolException.class, reader::currentGrants);
        Files.write(manifest, new byte[ProjectionEvidenceCodec.MAX_BYTES + 1]);
        assertThrows(ProjectionProtocolException.class, reader::currentGrants);
        assertThrows(IllegalArgumentException.class, () -> new ProjectionEvidenceManifestReader(Path.of("relative")));
    }
}
