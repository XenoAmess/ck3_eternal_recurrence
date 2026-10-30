package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionReceipt;

/** Relocated worker101 canonical98 topology; DATA-only software fixture, no physical admission. */
final class SettledRestartCaptureRecoveryRegressionTest {
    @TempDir Path temporary;
    @Test void retainedRestartCapturesPreserveDirtyFocusAndConsumedBatchFrontier() throws Exception {
        Path root = PortableRestart98Fixture.materialize(temporary);
        byte[] before = Files.readAllBytes(root.resolve("continuity.json"));
        var fixture = new SettledSameGameRecoveryRegressionTest.Fixture(root);
        var data = fixture.read();
        assertEquals(98, data.canonicalSequence());
        assertEquals(0, fixture.commits);
        assertEquals(1, data.settledActions().size());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, data.settledActions().getFirst().outcome());
        assertTrue(data.controller().dirty());
        assertEquals(1, data.controller().unsavedGameplayActions().size());
        assertEquals(data.settledActions().getFirst().command().actionId(), data.controller().unsavedGameplayActions().iterator().next());
        assertEquals(15, data.controller().nextBatchSequence());
        assertEquals(IntStream.range(0,15).mapToObj(sequence -> data.controller().batchPrefix()+"-"+sequence).collect(Collectors.toSet()),
                data.controller().usedBatches());
        assertEquals(0, data.controller().eligibleSinceSave());
        assertEquals(0, data.controller().totalCommittedDays());
        assertTrue(data.controller().savedPair().isEmpty());
        assertFalse(data.controller().localUnresolved());
        assertEquals(2, fixture.history().stream().filter(edge -> edge.sequence()==73 || edge.sequence()==95)
                .filter(edge -> new String(edge.details(), java.nio.charset.StandardCharsets.UTF_8).contains("WORKER_RESTART_CAPTURE")).count());
        assertArrayEquals(before, Files.readAllBytes(root.resolve("continuity.json")));
        fixture.assertNoCredit();
        System.out.println("PASS relocated canonical98 topology restart-capture73+95 next15 used0..14 dirtyFocus1 pending0 SAVE0 committedDays0; no fresh HELLO qualification");
    }
}
