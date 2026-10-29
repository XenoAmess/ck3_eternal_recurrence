package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual coordinator/writer dual-guard ordering and cold original-state reads; no detached Root permission. */
final class RootDerivedUnsubmittedGuardTest {
    @TempDir Path temporary;
    @Test void originalGuardThenIntentDurableSubmissionGuardAndTheirRealHistoryPointsRemainUnsubmittedOnly() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("dual-guard"), true)) {
            var calls = new AtomicInteger(); var initial = new AtomicReference<WriterContracts.Head>();
            var atSubmission = new AtomicReference<WriterContracts.Head>();
            fixture.bindGuardObserver((head, command) -> {
                try {
                    var same = fixture.writer.borrowedSession(); fixture.writer.requireSession(same);
                    assertEquals(head.digest(), same.head().digest());
                    var canonical = ContinuityActionJournal.lookup(head.state(), command.actionId(), fixture.archive.withSession(same));
                    RootDerivedChildAuthority.requireUnsubmitted(canonical, command);
                    if (calls.getAndIncrement() == 0) { assertTrue(canonical.isEmpty()); initial.set(head); }
                    else { assertInstanceOf(ActionState.IntentDurable.class, canonical.orElseThrow().state()); atSubmission.set(head); }
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            var command = fixture.command("actual-dual-guard");
            var unknown = fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, unknown.state());
            assertEquals(2, calls.get(), "actual coordinator must exercise both original and atSubmission guards");
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                for (var point : List.of(initial.get(), atSubmission.get())) {
                    var actualOld = same.requireHistoricalState(point.state().sequence(), point.digest());
                    var original = ContinuityActionJournal.lookup(actualOld, command.actionId(), archive);
                    RootDerivedChildAuthority.requireUnsubmitted(original, command);
                    assertEquals(point == initial.get(), original.isEmpty());
                    if (original.isPresent()) {
                        var changed = new ActionCommand(command.actionId(), command.origin(), command.source(), command.sessionId(), command.operation(),
                                new OpportunityJson.Obj(Map.of("changed", new OpportunityJson.Bool(true))),
                                command.expectation(), command.claims(), command.deadline(), command.protocolIdentity());
                        assertThrows(IllegalArgumentException.class, () -> RootDerivedChildAuthority.requireUnsubmitted(original, changed));
                    }
                }
                var current = ContinuityActionJournal.lookup(same.head().state(), command.actionId(), archive);
                assertThrows(IllegalArgumentException.class, () -> RootDerivedChildAuthority.requireUnsubmitted(current, command));
                return null;
            });
            int reads = fixture.nativeReadWrites();
            assertEquals(unknown, fixture.coordinator.execute(command));
            assertEquals(2, calls.get()); assertEquals(1, fixture.nativeActionWrites()); assertEquals(reads, fixture.nativeReadWrites());
            // This observer never supplies a GuardEvidence, domain claim, source qualification or ManagedGameSession.
        }
    }
}
