package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.OrdinaryAdmissionFixture225.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

final class OrdinarySubmissionAdmission225Test {
    private static Fixture completed() throws IOException {
        Fixture f = new Fixture(false);
        f.journal.retainCycle(OWNER, f.receipt);
        f.journal.settleCycle(OWNER, f.receipt, semantic(frame(2, 24024, "after"), TIME.plusSeconds(3)));
        assertEquals(2, f.store.commits);
        return f;
    }
    private static SemanticEvidence later() { return semantic(frame(6, 24120, "later"), TIME.plusSeconds(10)); }
    private static ObservationIdentity observed(long nativeRevision, long publicRevision, long date,
            BigInteger actor, String episode, int version) {
        return new ObservationIdentity(OWNER.machineId(), OWNER.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(actor, BigInteger.valueOf(nativeRevision), BigInteger.valueOf(date)),
                "altered", BigInteger.valueOf(publicRevision), episode), version);
    }
    private static void rejectedUnchanged(Fixture f, SemanticEvidence sem) {
        byte[] before = f.store.current.canonicalBytes(); int commits = f.store.commits;
        assertThrows(IllegalArgumentException.class, () -> f.journal.validateOrdinarySubmission(OWNER, sem));
        assertArrayEquals(before, f.store.current.canonicalBytes()); assertEquals(commits, f.store.commits);
    }

    @Test void laterOrdinaryQualifiesWithoutMintingSaveProofOrChangingCanonicalState() throws IOException {
        Fixture f = completed(); byte[] before = f.store.current.canonicalBytes();
        f.journal.validateOrdinarySubmission(OWNER, later());
        assertThrows(IllegalArgumentException.class, () -> f.journal.cycleProof(OWNER, later()));
        assertTrue(f.journal.cycleProof(OWNER, semantic(frame(3, 24024, "same-day"), TIME.plusSeconds(8))).isPresent());
        assertArrayEquals(before, f.store.current.canonicalBytes()); assertEquals(2, f.store.commits);
        assertEquals(3, f.store.current.settledCycles()); assertEquals(24000, f.store.current.settledDateRaw());
    }

    @Test void dateNativePublicAndObservationTimeRegressionsIndependentlyFailClosed() throws IOException {
        Fixture f = completed(); BigInteger actor = BigInteger.valueOf(29829);
        for (ObservationIdentity bad : List.of(
                observed(6, 6, 24000, actor, "episode-1", 1),
                observed(1, 6, 24120, actor, "episode-1", 1),
                observed(6, 1, 24120, actor, "episode-1", 1))) {
            rejectedUnchanged(f, semantic(bad, TIME.plusSeconds(10)));
        }
        rejectedUnchanged(f, semantic(frame(6, 24120, "backward-time"), TIME.plusSeconds(2)));
    }

    @Test void exactOwnerActorEpisodeAndObservationVersionRemainRequired() throws IOException {
        Fixture f = completed(); byte[] before = f.store.current.canonicalBytes();
        var foreign = new SessionIdentity("foreign-machine", OWNER.game(), OWNER.sessionId());
        assertThrows(IllegalArgumentException.class, () -> f.journal.validateOrdinarySubmission(foreign, later()));
        var otherSession = new SessionIdentity(OWNER.machineId(), OWNER.game(), "another-session");
        assertThrows(IllegalArgumentException.class, () -> f.journal.validateOrdinarySubmission(otherSession, later()));
        for (ObservationIdentity bad : List.of(
                observed(6, 6, 24120, BigInteger.valueOf(29830), "episode-1", 1),
                observed(6, 6, 24120, BigInteger.valueOf(29829), "episode-2", 1),
                observed(6, 6, 24120, BigInteger.valueOf(29829), "episode-1", 2))) {
            rejectedUnchanged(f, semantic(bad, TIME.plusSeconds(10)));
        }
        assertArrayEquals(before, f.store.current.canonicalBytes());
    }

    @Test void pendingCycleAndDifferentLinkedCanonicalUnknownCannotBeConcealed() throws IOException {
        Fixture pending = new Fixture(false); pending.journal.retainCycle(OWNER, pending.receipt);
        rejectedUnchanged(pending, later());
        Fixture f = completed(); var original = f.receipt.command();
        var command = new ActionCommand("unknown-other-2", original.before(), original.source(), original.sessionId(),
                original.operation(), original.arguments(), original.expected(), original.claims(), original.deadline());
        var unknown = new ActionReceipt(1, 4, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "unresolved original", List.of(REF)));
        ExactRef previous = ExactRef.fromJson(f.store.current.toJson().get(ContinuityActionJournal.STATE_FIELD));
        f.archive.preserveReceipt(unknown);
        ExactRef linked = f.archive.preserveRecord(new ActionRecord(unknown, Optional.of(previous)));
        ObjectNode state = f.store.current.toJson(); state.put("sequence", 4);
        state.set(ContinuityActionJournal.STATE_FIELD, linked.toJson());
        f.store.current = ContinuityState.fromJson(state, OWNER.machineId());
        assertTrue(ContinuityActionJournal.receipts(f.store.current, f.archive).stream()
                .anyMatch(receipt -> receipt.command().actionId().equals("unknown-other-2") && !receipt.settled()));
        rejectedUnchanged(f, later());
    }

    @Test void completeSemanticFailureAndFinalHeadDriftCannotGrantSubmission() throws IOException {
        Fixture failure = completed(); failure.rejectSemantic = true;
        byte[] before = failure.store.current.canonicalBytes();
        assertThrows(IOException.class, () -> failure.journal.validateOrdinarySubmission(OWNER, later()));
        assertArrayEquals(before, failure.store.current.canonicalBytes()); assertEquals(2, failure.store.commits);
        Fixture drift = completed();
        drift.semanticHook = () -> {
            ObjectNode state = drift.store.current.toJson(); state.put("sequence", drift.store.current.sequence() + 1);
            drift.store.current = ContinuityState.fromJson(state, OWNER.machineId());
        };
        assertThrows(IllegalArgumentException.class, () -> drift.journal.validateOrdinarySubmission(OWNER, later()));
        assertEquals(2, drift.store.commits);
    }

    @Test void borrowedQualificationNeedsItsActualHeldStoreAndAllowsLegitimateSameSession() throws IOException {
        Fixture f = completed(); Store foreignStore = new Store();
        foreignStore.locked(foreign -> {
            assertThrows(IOException.class, () -> f.journal.validateOrdinarySubmission(foreign, OWNER, later()));
            return true;
        });
        assertThrows(IOException.class, () -> f.journal.validateOrdinarySubmission(f.store.session, OWNER, later()));
        f.store.locked(same -> { f.journal.validateOrdinarySubmission(same, OWNER, later()); return true; });
        assertEquals(2, f.store.commits);
    }

    @Test void legacyFunctionalJournalDefaultRemainsFailClosedWithoutACommit() {
        int[] commits = {0};
        BatchJournal journal = input -> { commits[0]++; return new JournalCommit(REF, 0); };
        assertThrows(IOException.class, () -> journal.validateOrdinarySubmission(OWNER, later()));
        assertEquals(0, commits[0]);
    }

    @Test void historicalScopeClosesBeforeLiveSemanticQualificationAndPreservesAllHistoryReads() throws IOException {
        Fixture f = completed(); f.archive.trackHistorical = true;
        f.semanticHook = () -> { assertFalse(f.archive.inHistorical); assertEquals(1, f.archive.scopeEntries); };
        byte[] before = f.store.current.canonicalBytes();
        f.journal.validateOrdinarySubmission(OWNER, later());
        assertEquals(1, f.archive.scopeEntries); assertTrue(f.archive.scopeMaterialReads > 0);
        assertTrue(f.archive.scopeReceiptReads > 0); assertFalse(f.archive.inHistorical);
        assertArrayEquals(before, f.store.current.canonicalBytes()); assertEquals(2, f.store.commits);
    }

    @Test void historicalEntryOrCloseFailureNeverReachesTheLiveVerifier() throws IOException {
        for (boolean close : List.of(false, true)) {
            Fixture f = completed(); f.archive.trackHistorical = true;
            f.archive.failScopeEntry = !close; f.archive.failScopeClose = close;
            f.semanticHook = () -> fail("scope failure reached current qualification");
            byte[] before = f.store.current.canonicalBytes();
            assertThrows(IOException.class, () -> f.journal.validateOrdinarySubmission(OWNER, later()));
            assertFalse(f.archive.inHistorical); assertArrayEquals(before, f.store.current.canonicalBytes());
            assertEquals(2, f.store.commits);
        }
    }

    @Test void historicalValidationFailurePropagatesAndClosesItsScope() throws IOException {
        Fixture f = completed(); f.archive.trackHistorical = true;
        f.archive.failScopeRead = true;
        f.semanticHook = () -> fail("historical tamper reached current qualification");
        byte[] before = f.store.current.canonicalBytes();
        assertThrows(IllegalArgumentException.class, () -> f.journal.validateOrdinarySubmission(OWNER, later()));
        assertFalse(f.archive.inHistorical); assertEquals(1, f.archive.scopeEntries);
        assertArrayEquals(before, f.store.current.canonicalBytes()); assertEquals(2, f.store.commits);
    }
}
