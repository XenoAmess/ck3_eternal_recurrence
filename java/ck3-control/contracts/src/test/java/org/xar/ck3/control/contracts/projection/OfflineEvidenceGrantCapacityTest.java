package org.xar.ck3.control.contracts.projection;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class OfflineEvidenceGrantCapacityTest {
    @Test void originalCompletedUiPairCohortFitsWithoutChangingByteOrBusinessBudgets() {
        List<ProjectionEvidenceGrant> grants = new ArrayList<>();
        for (int index = 0; index < 897; index++) {
            grants.add(new ProjectionEvidenceGrant(Path.of("historical-evidence-" + index + ".json").toAbsolutePath(), 1, "a".repeat(64), "unknown",
                    index < 128 ? ProjectionEvidenceRole.EVENT_SOURCE_FACTS : ProjectionEvidenceRole.UI_RECOVERY_AFTER));
        }
        assertEquals(1024, ProjectionEvidenceCodec.MAX_GRANTS); assertEquals(1048576, ProjectionEvidenceCodec.MAX_BYTES);
        byte[] raw = ProjectionEvidenceCodec.encode(grants); assertEquals(grants, ProjectionEvidenceCodec.decode(raw));
        assertTrue(raw.length < 1048576);
        while (grants.size() <= 1024) {
            grants.add(new ProjectionEvidenceGrant(Path.of("overflow-" + grants.size() + ".json").toAbsolutePath(), 1, "a".repeat(64), "unknown", ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
        }
        assertThrows(IllegalArgumentException.class, () -> ProjectionEvidenceCodec.validated(grants));
    }
}
