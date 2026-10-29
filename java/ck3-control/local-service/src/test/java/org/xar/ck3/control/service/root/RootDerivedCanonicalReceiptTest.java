package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real writer/codec boundary tests; these do not create a qualified Root or native derived-child permit. */
final class RootDerivedCanonicalReceiptTest {
    @TempDir Path temporary;

    private record Trace(ActionCommand command, ActionReceipt unknown, WriterContracts.Head initial,
            WriterContracts.Head intent) { }

    private static Trace execute(ActionWriterIntegrationFixture fixture) throws Exception {
        var initial = new AtomicReference<WriterContracts.Head>();
        var intent = new AtomicReference<WriterContracts.Head>();
        fixture.bindGuardObserver((head, command) -> {
            if (!initial.compareAndSet(null, head)) intent.set(head);
        });
        var command = fixture.command("derived-canonical-boundary");
        var unknown = fixture.coordinator.execute(command);
        assertInstanceOf(ActionState.Unknown.class, unknown.state());
        assertNotNull(initial.get()); assertNotNull(intent.get());
        return new Trace(command, unknown, initial.get(), intent.get());
    }

    private static ActionReceipt submitting(WriterContracts.Head head, ActionPorts.OutcomeArchive archive) {
        var cursor = ContinuityActionJournal.recordHead(head.state());
        while (cursor.isPresent()) {
            var record = archive.loadRecord(cursor.orElseThrow());
            if (record.receipt().state() instanceof ActionState.Submitting) return record.receipt();
            cursor = record.previous();
        }
        throw new AssertionError("real writer did not retain its original Submitting record");
    }

    @Test void firstSubmittingFromRealWriterPreviewsIntentAndRoundtripsThenRequiresCompleteHistoricalReceipt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("first-submitting"), true)) {
            var trace = execute(fixture);
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> { try {
                var head = same.head(); var child = submitting(head, archive);
                assertEquals(trace.intent().state().toJson(), same.requireHistoricalState(trace.intent().state().sequence(), trace.intent().digest()).toJson());
                var canonical = ContinuityActionJournal.lookup(trace.intent().state(), trace.command().actionId(), archive).orElseThrow();
                assertInstanceOf(ActionState.IntentDurable.class, canonical.state());
                assertEquals(Math.addExact(trace.intent().state().sequence(), 1), child.sequence());
                assertNotEquals(ActionTransitions.attempt(canonical.state()), ActionTransitions.attempt(child.state()),
                        "the former unconditional Attempt comparison rejects this actual first Submitting event");
                var bytes = ActionReceiptCodec.encodeReceipt(child, archive);
                var decoded = ActionReceiptCodec.decodeReceipt(bytes, archive);
                assertArrayEquals(bytes, ActionReceiptCodec.encodeReceipt(decoded, archive));
                RootDerivedChildAuthority.requireCanonicalOrPreview(trace.intent(), decoded, archive);
                RootDerivedChildAuthority.requireCanonicalOrPreview(head, decoded, archive);
                assertEquals(trace.unknown(), archive.loadReceipt(archive.receiptReferenceOf(trace.unknown())));
                return null;
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }));
            int reads = fixture.nativeReadWrites();
            assertEquals(trace.unknown(), fixture.reopenAndReturnExisting(trace.command()));
            assertEquals(1, fixture.nativeActionWrites()); assertEquals(reads, fixture.nativeReadWrites());
        }
    }

    @Test void candidateMustBeExactlyNextWithItsActualExistingPredecessorAndCompleteBody() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("candidate-boundaries"), true)) {
            var trace = execute(fixture);
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> { try {
                var child = submitting(same.head(), archive);
                var gap = new ActionReceipt(child.version(), Math.addExact(child.sequence(), 1), child.command(), child.bodySha256(), child.state());
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(trace.intent(), gap, archive));
                var missing = new ActionReceipt(child.version(), Math.addExact(trace.initial().state().sequence(), 1),
                        child.command(), child.bodySha256(), child.state());
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(trace.initial(), missing, archive));
                var original = child.command();
                var changed = new ActionCommand(original.actionId(), original.origin(), original.source(), original.sessionId(), original.operation(),
                        new OpportunityJson.Obj(Map.of("changed", new OpportunityJson.Bool(true))),
                        original.expectation(), original.claims(), original.deadline(), original.protocolIdentity());
                var changedBody = new ActionReceipt(child.version(), child.sequence(), changed, ActionCodec.bodySha256(changed), child.state());
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(trace.intent(), changedBody, archive));
                return null;
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }));
            assertEquals(1, fixture.nativeActionWrites());
        }
    }

    @Test void unknownMayRetainItsOriginalAttemptButCannotReturnToSubmittingOrReplaceIt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("unknown-transition"), true)) {
            var trace = execute(fixture);
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> { try {
                var head = same.head(); var old = assertInstanceOf(ActionState.Unknown.class, trace.unknown().state());
                long next = Math.addExact(head.state().sequence(), 1);
                var retained = new ActionReceipt(1, next, trace.command(), trace.unknown().bodySha256(),
                        new ActionState.Unknown(old.attempt(), old.dispatch(), "actual original remains unknown", old.evidence()));
                RootDerivedChildAuthority.requireCanonicalOrPreview(head, retained, archive);
                var attempt = old.attempt().orElseThrow();
                var replay = new ActionReceipt(1, next, trace.command(), trace.unknown().bodySha256(), new ActionState.Submitting(attempt));
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(head, replay, archive));
                var replaced = new ActionState.Attempt(attempt.requestId(), attempt.submittedAt().plusNanos(1), attempt.guard(), attempt.preparedRequest());
                var changed = new ActionReceipt(1, next, trace.command(), trace.unknown().bodySha256(),
                        new ActionState.Unknown(Optional.of(replaced), old.dispatch(), old.reason(), old.evidence()));
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(head, changed, archive));
                return null;
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }));
            assertEquals(trace.unknown(), fixture.coordinator.execute(trace.command()));
            assertEquals(1, fixture.nativeActionWrites());
        }
    }

    @Test void historicalReceiptCannotChangeReasonEvidenceStateOrSequenceDespiteSameOriginalAttempt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("historical-integrity"), true)) {
            var trace = execute(fixture);
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> { try {
                var head = same.head(); var original = trace.unknown();
                var old = assertInstanceOf(ActionState.Unknown.class, original.state());
                var changedReason = new ActionReceipt(1, original.sequence(), original.command(), original.bodySha256(),
                        new ActionState.Unknown(old.attempt(), old.dispatch(), old.reason() + " changed", old.evidence()));
                var changedEvidence = new ActionReceipt(1, original.sequence(), original.command(), original.bodySha256(),
                        new ActionState.Unknown(old.attempt(), old.dispatch(), old.reason(), List.of(original.command().source().sourceRef())));
                var changedState = new ActionReceipt(1, original.sequence(), original.command(), original.bodySha256(),
                        new ActionState.Submitting(old.attempt().orElseThrow()));
                for (var changed : List.of(changedReason, changedEvidence, changedState)) {
                    assertEquals(ActionTransitions.attempt(original.state()), ActionTransitions.attempt(changed.state()));
                    assertThrows(IllegalArgumentException.class,
                            () -> RootDerivedChildAuthority.requireCanonicalOrPreview(head, changed, archive));
                }
                var shifted = new ActionReceipt(1, original.sequence() - 1, original.command(), original.bodySha256(), original.state());
                assertThrows(IllegalArgumentException.class,
                        () -> RootDerivedChildAuthority.requireCanonicalOrPreview(head, shifted, archive));
                RootDerivedChildAuthority.requireCanonicalOrPreview(head, original, archive);
                return null;
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }));
            assertEquals(1, fixture.nativeActionWrites());
        }
    }
}
