package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software endpoint write/read failure, sole coordinator, actual writer/archive and Root guards. No Game qualification. */
final class PlanningReadLateAdoptionWriterTest {
    @TempDir Path root;

    @Test void actualUnknownLateAckIsAdoptedOnceWithoutChangingTheOriginalDeadlineOrChronology() throws Exception {
        try (var actual = Scenario.open(root.resolve("late"), true, Optional.empty())) {
            var ticket = actual.start();
            long sequence = actual.fixture.sequence(); int writes = actual.fixture.scenarioReadWrites();
            assertTrue(actual.poll().isEmpty()); assertEquals(writes, actual.fixture.scenarioReadWrites());
            var ack = actual.receiveLate();
            assertEquals(ticket.requestId(), ack.requestId());
            assertTrue(ack.custody().orElseThrow().responseReceived().observedAt().isAfter(actual.originalRequest.deadline()));
            var known = actual.known(actual.adopt(ack));
            assertEquals(actual.originalRequest, known.receipt().request());
            assertEquals(ack, known.receipt().original());
            assertSame(ack.custody().orElseThrow(), known.receipt().original().custody().orElseThrow());
            assertEquals(PlanningReadReceipt.ArchiveVersion.CURRENT_V2, known.receipt().archiveVersion());
            assertTrue(known.receipt().adoption().isPresent());
            actual.fixture.journal.locked(same -> {
                var reopened = actual.fixture.archive.withSession(same.writerSession()).loadRead(known.originalReceipt());
                assertEquals(known.receipt(), reopened);
                assertEquals(known.originalReceipt(), actual.fixture.archive.withSession(same.writerSession()).readReferenceOf(reopened));
                assertEquals(known.value(), actual.contract.replay(reopened)); return null;
            });
            // The exact same actual receive timestamp remains invalid on the ordinary strict path.
            var ordinary = new PlanningReadReceipt(known.receipt().request(), known.receipt().contractId(), known.receipt().requestId(),
                    known.receipt().before(), known.receipt().after(), ack);
            assertThrows(IllegalArgumentException.class, () -> ack.custody().orElseThrow().verify(ordinary));
            var duplicate = actual.known(actual.adopt(ack));
            assertSame(known, duplicate); assertEquals(known.originalReceipt(), duplicate.originalReceipt());
            assertEquals(writes, actual.fixture.scenarioReadWrites()); assertEquals(sequence, actual.fixture.sequence());
            assertEquals(0, actual.fixture.nativeActionWrites()); assertTrue(actual.poll().isEmpty());
        }
    }

    @Test void failedKnownNotificationRetainsTheFirstArchivedReadAndRetriesOnlyThatSameKnown() throws Exception {
        var notifications = new AtomicInteger(); var first = new AtomicReference<PlanningReadResult.Known<?>>();
        PlanningReadCoordinator.KnownReadObserver observer = (same, contract, known) -> {
            if (first.compareAndSet(null, known)) {
                notifications.incrementAndGet(); throw new UncheckedIOException(new IOException("controlled actual known-notification failure"));
            }
            assertSame(first.get(), known); notifications.incrementAndGet();
        };
        try (var actual = Scenario.open(root.resolve("callback"), true, Optional.of(observer))) {
            actual.start(); var ack = actual.receiveLate(); int writes = actual.fixture.scenarioReadWrites();
            var failed = assertInstanceOf(PlanningReadResult.Unavailable.class, actual.adopt(ack));
            assertEquals(ack, failed.original().orElseThrow()); assertNotNull(first.get());
            var known = actual.known(actual.adopt(ack));
            assertSame(first.get(), known); assertEquals(first.get().originalReceipt(), known.originalReceipt());
            assertSame(known, actual.known(actual.adopt(ack))); assertEquals(2, notifications.get());
            assertEquals(writes, actual.fixture.scenarioReadWrites()); assertEquals(0, actual.fixture.nativeActionWrites());
        }
    }

    @Test void absentHeldScopeRejectsWithoutRecaptureAndTheRetainedAckCanStillBeAdoptedInTheRealScope() throws Exception {
        try (var actual = Scenario.open(root.resolve("no-held"), true, Optional.empty())) {
            var ticket = actual.start(); var ack = actual.receiveLate();
            var request = actual.currentRequest(Instant.now().plusSeconds(10));
            int writes = actual.fixture.scenarioReadWrites();
            var failed = actual.fixture.journal.locked(same -> {
                try { return actual.fixture.reads.adoptOriginal(same.writerSession(), ticket, ack, request, actual.originalSemantic); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            assertInstanceOf(PlanningReadResult.Unavailable.class, failed);
            assertEquals(writes, actual.fixture.scenarioReadWrites());
            assertEquals(ack, actual.known(actual.adopt(ack)).receipt().original());
        }
    }

    @Test void sourceWithoutExplicitReuseCannotTurnItsLateReadIntoKnown() throws Exception {
        try (var actual = Scenario.open(root.resolve("no-reuse"), false, Optional.empty())) {
            actual.start(); var ack = actual.receiveLate();
            var rejected = assertInstanceOf(PlanningReadResult.Unavailable.class, actual.adopt(ack));
            assertEquals(ack, rejected.original().orElseThrow());
            assertTrue(rejected.reason().contains("explicit canonical reuse"));
            assertEquals(1, actual.fixture.scenarioReadWrites()); assertEquals(0, actual.fixture.nativeActionWrites());
        }
    }

    @Test void anotherInstalledCoordinatorCannotPollOrAdoptTheOpaqueOriginalTicket() throws Exception {
        try (var original = Scenario.open(root.resolve("one"), true, Optional.empty());
                var other = Scenario.open(root.resolve("two"), true, Optional.empty())) {
            var ticket = original.start(); var ack = original.receiveLate();
            assertThrows(IllegalArgumentException.class, () -> other.fixture.reads.pollOriginal(ticket));
            var rejected = other.fixture.reads.adoptOriginal(ticket, ack, original.currentRequest(Instant.now().plusSeconds(10)), original.originalSemantic);
            assertInstanceOf(PlanningReadResult.Unavailable.class, rejected);
            assertEquals(0, other.fixture.scenarioReadWrites());
            assertEquals(ack, original.known(original.adopt(ack)).receipt().original());
        }
    }

    @Test void changedArgumentsAndForgedTokenAreRejectedWithoutDiscardingOrResendingTheActualAck() throws Exception {
        try (var actual = Scenario.open(root.resolve("bad-original"), true, Optional.empty())) {
            var ticket = actual.start(); var ack = actual.receiveLate();
            var current = actual.currentRequest(Instant.now().plusSeconds(10));
            var changed = new PlanningReadRequest(current.origin(), current.source(), current.sessionId(), current.operation(),
                    new OpportunityJson.Obj(Map.of("unexpected", new OpportunityJson.Bool(true))), current.deadline());
            assertInstanceOf(PlanningReadResult.Unavailable.class,
                    actual.fixture.reads.adoptOriginal(ticket, ack, changed, actual.originalSemantic));
            var forged = new NativeActionPort.AckReceived(ack.requestId(), ack.nativeOk(), Optional.of(raw("{\"forged\":true}")),
                    ack.originalFrame(), ack.originalPacket(), ack.outbound(), ack.custody());
            assertInstanceOf(PlanningReadResult.Unavailable.class, actual.adopt(forged));
            var known = actual.known(actual.adopt(ack)); assertEquals(ack, known.receipt().original());
            assertEquals(1, actual.fixture.scenarioReadWrites()); assertEquals(0, actual.fixture.nativeActionWrites());
        }
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }

    /** Package-private actual producer vector for the archive owner's cold/strict-schema regressions. */
    static final class Scenario implements AutoCloseable {
        private static final OperationKey OP = new OperationKey("query-software-late-original29-v1");
        private static final String CAP = "software_late_original29_v1";
        final ActionWriterIntegrationFixture fixture;
        final ReadContract<RawJson> contract;
        PlanningReadRequest originalRequest;
        OpportunityJson.Obj originalSemantic;
        PlanningReadCoordinator.OriginalRead<RawJson> ticket;
        private Scenario(ActionWriterIntegrationFixture fixture, ReadContract<RawJson> contract) {
            this.fixture = fixture; this.contract = contract;
        }
        static Scenario open(Path root, boolean reuse, Optional<PlanningReadCoordinator.KnownReadObserver> observer) throws IOException {
            var installed = new AtomicReference<ReadContract<RawJson>>();
            var inputs = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-adapter", source -> {
                var actual = contract(source, reuse); installed.set(actual); return List.of(actual);
            }, request -> raw("{\"actual_status\":\"late_original\"}"), Optional.empty(), Set.of(CAP));
            var fixture = new ActionWriterIntegrationFixture(root, false, inputs);
            try {
                fixture.loseReadAckOnce();
                if (observer.isPresent()) fixture.bindKnownReadObserver((same, contract, known) -> {
                    if (contract == installed.get()) observer.orElseThrow().afterKnown(same, contract, known);
                });
                return new Scenario(fixture, java.util.Objects.requireNonNull(installed.get()));
            } catch (IOException | RuntimeException failure) { fixture.close(); throw failure; }
        }
        private static ReadContract<RawJson> contract(ExactRef source, boolean reuse) {
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare = (request, id) ->
                    new NativeRequest(OP.value(), Optional.of(CAP), raw("{}"));
            Function<PlanningReadReceipt, RawJson> decode = receipt -> receipt.original().originalResultToken().orElseThrow();
            if (!reuse) return new ReadContract<>("software-late-original29/v1", OP, Optional.of(CAP), CAP,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source, prepare, decode, decode);
            return new ReadContract<>("software-late-original29/v1", OP, Optional.of(CAP), CAP,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source, prepare, decode, decode, (original, value, current, semantic) -> {
                        StrictJson.require(original.request().origin().equals(current.origin()) && original.request().source().equals(current.source())
                                && original.request().sessionId().equals(current.sessionId()) && original.request().operation().equals(current.operation())
                                && original.request().arguments().equals(current.arguments()), "software source rejects changed original binding");
                        StrictJson.require(value.equals(decode.apply(original)), "source-owned reuse changed original decoded data");
                        StrictJson.require(!semantic.members().isEmpty(), "actual current semantic required");
                    });
        }
        PlanningReadCoordinator.OriginalRead<RawJson> start() throws Exception {
            var ready = fixture.ready(); originalSemantic = ready.request().observations().snapshot();
            originalRequest = new PlanningReadRequest(ready.request().before(), fixture.observationSource(), fixture.observationIdentity().sessionId(),
                    OP, new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(1));
            var attempt = fixture.journal.locked(same -> fixture.reads.readOriginal(same.writerSession(), contract, originalRequest));
            var unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class, attempt.result());
            assertInstanceOf(NativeActionPort.Unknown.class, unavailable.original().orElseThrow());
            ticket = attempt.original().orElseThrow(); return ticket;
        }
        Optional<NativeActionPort.AckReceived> poll() throws IOException {
            try { return fixture.journal.locked(same -> {
                try { return fixture.reads.pollOriginal(same.writerSession(), ticket); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
        }
        NativeActionPort.AckReceived receiveLate() throws Exception {
            long remaining = Duration.between(Instant.now(), originalRequest.deadline().plusMillis(30)).toMillis();
            if (remaining > 0) Thread.sleep(remaining + 1);
            fixture.releaseLateReadAck(); fixture.physicalInputs().transport().observe(Instant.now().plusSeconds(5));
            return poll().orElseThrow();
        }
        PlanningReadRequest currentRequest(Instant deadline) {
            return new PlanningReadRequest(originalRequest.origin(), originalRequest.source(), originalRequest.sessionId(), OP,
                    originalRequest.arguments(), deadline);
        }
        PlanningReadResult<RawJson> adopt(NativeActionPort.AckReceived ack) throws IOException {
            try { return fixture.journal.locked(same -> {
                try { return fixture.collector.withHeldReadScope(same.writerSession(), fixture.observationIdentity(), Instant.now().plusSeconds(10), frame -> {
                    var current = new PlanningReadRequest(frame.identity(), fixture.observationSource(), frame.sessionId(), OP,
                            originalRequest.arguments(), Instant.now().plusSeconds(5));
                    return fixture.reads.adoptOriginal(same.writerSession(), ticket, ack, current, frame.semantic());
                }); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
        }
        PlanningReadResult.Known<RawJson> known(PlanningReadResult<RawJson> result) {
            if (result instanceof PlanningReadResult.Known<RawJson> actual) return actual;
            throw new AssertionError("actual late-read adoption unavailable: " + result);
        }
        @Override public void close() throws IOException { fixture.close(); }
    }
}
