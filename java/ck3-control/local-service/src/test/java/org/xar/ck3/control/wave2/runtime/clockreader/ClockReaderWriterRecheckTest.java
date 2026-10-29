package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ContentEvidenceRef;
import org.xar.ck3.control.reconciliation.LateOutcome.OriginalFailure;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockCustodyGuard.Role;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderApplication.RunResult;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import static org.junit.jupiter.api.Assertions.*;

/** Actual file adapter; synthetic Game and Queue facts. No original writer lock or commit is claimed. */
class ClockReaderWriterRecheckTest {
    @TempDir Path temporary;
    private ClockReaderTest.Fixture fixture() throws IOException {
        var support = new ClockReaderTest(); support.temporary = temporary; return support.new Fixture();
    }
    @Test void currentOriginalArtifactsAreRecheckedWithoutAnotherQueueRequest() throws Exception {
        var f = fixture(); byte[] failure = Files.readAllBytes(f.pins.get(Role.ORIGINAL_FAILURE).path());
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            assertEquals(Outcome.PROPOSED, proposal.assessment().outcome());
            var callback = application.originalWriterRecheck(proposal); int measuredBefore = f.measurements;
            var current = callback.recheck();
            assertEquals(proposal, current); assertEquals(3, f.tools.size()); assertEquals(3, f.served.size());
            assertTrue(f.measurements > measuredBefore); assertEquals(0, current.originalCredit()); assertTrue(current.neverReplay());
            assertArrayEquals(failure, Files.readAllBytes(f.pins.get(Role.ORIGINAL_FAILURE).path()));
        }
    }
    @Test void reconstructedAssessmentCannotCreateALocalWriterCallback() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var reconstructed = new RunResult(proposal.assessment(), proposal.ledger());
            assertThrows(ContractViolationException.class, () -> application.originalWriterRecheck(reconstructed));
            var anotherApplication = new ClockReaderApplication(reader, f.time);
            assertThrows(ContractViolationException.class, () -> anotherApplication.originalWriterRecheck(proposal));
            assertEquals(3, f.tools.size());
        }
    }
    @Test void actualWriterHeadChangeAfterProposalRejectsTheCallback() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var callback = application.originalWriterRecheck(proposal);
            Files.writeString(f.pins.get(Role.EXPECTED_HEAD).path(), "{\"changed_head\":true}", StandardCharsets.UTF_8);
            assertThrows(IOException.class, callback::recheck); assertEquals(3, f.tools.size());
        }
    }
    @Test void closedGameAfterProposalCannotReuseHistoricalReadEvidence() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var callback = application.originalWriterRecheck(proposal); f.processClosed = true;
            assertThrows(IOException.class, callback::recheck); assertEquals(3, f.tools.size());
        }
    }
    @Test void changedRawOriginalCannotSurviveTheWriterRecheck() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var callback = application.originalWriterRecheck(proposal);
            try (var originals = Files.list(f.root.resolve("originals"))) {
                Files.writeString(originals.findFirst().orElseThrow(), "{}", StandardCharsets.UTF_8);
            }
            assertThrows(IOException.class, callback::recheck); assertEquals(3, f.tools.size());
        }
    }
    @Test void semanticFreshnessStillUsesTheActualRunBudgetAtTheWriterCallback() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var callback = application.originalWriterRecheck(proposal); f.time.elapsed += 2001;
            assertThrows(IOException.class, callback::recheck); assertEquals(3, f.tools.size());
        }
    }
    @Test void laterRunInvalidatesThePreviousCallbackWithoutSubmittingAnotherRead() throws Exception {
        var f = fixture();
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var proposal = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            var callback = application.originalWriterRecheck(proposal);
            var newer = application.run(f.attempt, f.budget(), proposal.ledger());
            assertEquals(Outcome.PROPOSED, newer.assessment().outcome());
            assertThrows(IOException.class, callback::recheck);
            assertEquals(newer, application.originalWriterRecheck(newer).recheck()); assertEquals(3, f.tools.size());
        }
    }
    @Test void unresolvedRunCannotAcquireAWriterRecheckCallback() throws Exception {
        var f = fixture(); f.unpaused = true;
        try (var reader = f.open()) {
            var application = new ClockReaderApplication(reader, f.time);
            var unresolved = application.run(f.attempt, f.budget(), new ReadLedger(java.util.List.of()));
            assertEquals(Outcome.UNRESOLVED, unresolved.assessment().outcome());
            assertThrows(ContractViolationException.class, () -> application.originalWriterRecheck(unresolved));
            assertEquals(8, f.tools.size());
        }
    }
    @Test void admittedFailureAndWriterHeadLengthsMustMatchTheirActualPins() throws Exception {
        var f = fixture();
        var sources = f.pins.entrySet().stream().map(entry -> new ClockCustodyGuard.Source(entry.getKey(), entry.getValue())).toList();
        for (Role role : java.util.List.of(Role.ORIGINAL_FAILURE, Role.EXPECTED_HEAD)) {
            ContentEvidenceRef actual = role == Role.ORIGINAL_FAILURE ? f.attempt.original().receipt() : f.attempt.expectedHead();
            var wrong = new ContentEvidenceRef(actual.sha256(), actual.bytes() + 1, actual.evidenceKey());
            OriginalFailure failure = role == Role.ORIGINAL_FAILURE
                    ? new OriginalFailure(wrong, f.attempt.original().fullSequence(), f.attempt.original().autoSequence(),
                            f.attempt.original().normalStatusQueryAttempted(), f.attempt.original().stopValidationAttempted())
                    : f.attempt.original();
            var attempt = new Attempt(f.attempt.scope(), failure, f.attempt.arm(),
                    role == Role.EXPECTED_HEAD ? wrong : f.attempt.expectedHead(), f.attempt.minNativeRevision(),
                    f.attempt.minVerifiedPumpEpoch(), f.attempt.minHeartbeatSequence());
            assertThrows(ContractViolationException.class, () -> new ClockCustodyGuard(attempt, sources,
                    pid -> { throw new IOException("invalid input must reject before a kernel probe"); }, () -> "synthetic-machine"));
        }
        assertTrue(f.served.isEmpty());
    }
}
