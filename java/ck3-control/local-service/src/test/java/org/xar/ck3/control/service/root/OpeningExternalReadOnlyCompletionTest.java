package org.xar.ck3.control.service.root;

import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class OpeningExternalReadOnlyCompletionTest {
    @Test void keepsOnlyTheCompletedReadOnlyOriginalAcrossNamedRemount() throws Exception {
        try (var source = getClass().getResourceAsStream("source56-opening-readonly.json.gz");
             var input = new GZIPInputStream(source)) {
            var original = StrictJson.parse(input.readAllBytes(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var waiting = GovernanceOpeningDocument.decode(ContinuityJson.canonical(original.get("64")));
            var complete = GovernanceOpeningDocument.decode(ContinuityJson.canonical(original.get("65")));
            assertFalse(OpeningTransitions.retainsExternalReadOnlyCompletion(waiting));
            assertTrue(OpeningTransitions.retainsExternalReadOnlyCompletion(complete));
            assertEquals(297908, complete.existingObserved().orElseThrow().game().pid());
            assertEquals("native:34", complete.existingObserved().orElseThrow().frame().snapshotId());
            assertTrue(complete.actionReceipt().isEmpty());
            assertTrue(complete.checkpoint().isEmpty());
        }
    }
}
