package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.ProcessIdentity;
import org.xar.ck3.control.wave2.runtime.closedadoption.ClockOriginalWriterLockFixture;
import org.xar.ck3.control.wave2.runtime.closedadoption.ClockOriginalWriterLockFixture.PreparedHook;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import static org.junit.jupiter.api.Assertions.*;

/** Actual original writer lock refuses synthetic live-Game evidence. No successful live or closed adoption is claimed. */
class ClockReaderOriginalWriterLockTest {
    @TempDir Path temporary;
    private enum Failure { GAME_CLOSED, DIFFERENT_HEAD_PATH }

    @Test void gameClosingAfterThreeReadProposalRejectsInsideActualOriginalWriterLock() throws Exception {
        assertLockedRefusal(Failure.GAME_CLOSED);
    }
    @Test void equalHeadAtAnotherPathCannotAuthorizeTheActualOriginalWriterTarget() throws Exception {
        assertLockedRefusal(Failure.DIFFERENT_HEAD_PATH);
    }
    private void assertLockedRefusal(Failure mode) throws IOException, InterruptedException {
        AtomicReference<ClockReaderTest.Fixture> observed = new AtomicReference<>();
        var rejection = ClockOriginalWriterLockFixture.assertRejected((canonical, actualHead) -> {
            var expectedHead = actualHead;
            if (mode == Failure.DIFFERENT_HEAD_PATH) {
                Path other = temporary.resolve("same-bytes-other-writer-head.json");
                byte[] raw = Files.readAllBytes(canonical); Files.write(other, raw);
                expectedHead = ClockPinnedFiles.capture(other.toAbsolutePath(), actualHead.sha256(), 65_536);
                assertEquals(actualHead.sha256(), expectedHead.sha256()); assertEquals(actualHead.bytes(), expectedHead.bytes());
                assertNotEquals(actualHead.contentStamp().realPath(), expectedHead.contentStamp().realPath());
            }
            var support = new ClockReaderTest(); support.temporary = temporary;
            var fixture = support.new Fixture("clock-channel", new ProcessIdentity(23456, new CrossJsDecimalUInt64("2000")),
                    false, expectedHead);
            observed.set(fixture);
            var reader = fixture.open();
            var session = new ClockReaderSession(reader, new ClockReaderApplication(reader, fixture.time), fixture.attempt, expectedHead);
            try {
                var proposal = session.reconcile(fixture.budget(), new ReadLedger(List.of()));
                assertEquals(Outcome.PROPOSED, proposal.assessment().outcome());
                assertEquals(3, fixture.served.size()); assertEquals(0, proposal.originalCredit()); assertTrue(proposal.neverReplay());
                var originalHook = session.originalWriterLockedRecheck(proposal);
                return new PreparedHook(target -> {
                    if (!canonical.toRealPath().equals(target.canonicalPath().toRealPath())) {
                        throw new IOException("actual original writer target changed before the Clock hook");
                    }
                    if (mode == Failure.GAME_CLOSED) { fixture.processClosed = true; }
                    originalHook.verify(target);
                }, session::close);
            } catch (IOException | InterruptedException | RuntimeException | AssertionError failure) {
                try { session.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        });
        String reason = rejection.failure().getMessage();
        assertTrue(reason.contains(mode == Failure.GAME_CLOSED ? "fixture kernel process exited" : "original locked writer target differs"), reason);
        assertTrue(rejection.sourceChecks() >= 2); assertEquals(1, rejection.lockedChecks());
        assertNotEquals(0, rejection.actualExit().exitCode()); assertEquals(0, rejection.actualExit().accounting().activeProcesses());
        var fixture = observed.get(); assertNotNull(fixture);
        assertEquals(3, fixture.served.size()); assertEquals(List.of(ClockMcpRowDecoder.STATUS_TOOL,
                ClockMcpRowDecoder.SEMANTIC_TOOL, ClockMcpRowDecoder.STATUS_TOOL), fixture.tools);
        try (var requests = Files.list(fixture.root.resolve("requests"))) { assertEquals(3, requests.count()); }
        assertFalse(Files.exists(fixture.root.resolve("ACTIVE-READ.json")));
    }
}
