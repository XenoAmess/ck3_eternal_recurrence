package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual shared read coordinator, endpoint custody, writer and archive. Instrumentation supplies no authority. */
final class PlanningReadLifecycleWriterTest {
    @TempDir Path root;
    private enum Fail { NONE, PREPARED, RECEIVED, KNOWN }

    @Test void actualGeneratedRequestAndOriginalReturnReachTheObserverAfterRealGuardAndArchive() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("known"), false)) {
            var request = request(fixture); var recorder = new Recorder(fixture, Fail.NONE, false);
            int reads = fixture.nativeReadWrites(); long sequence = fixture.sequence();
            PlanningReadResult<?> actual = fixture.journal.locked(locked -> fixture.reads.read(locked.writerSession(), fixture.readContract, request, recorder));
            PlanningReadResult.Known<?> known = assertInstanceOf(PlanningReadResult.Known.class, actual);
            assertEquals(List.of("prepared", "received", "known"), recorder.events);
            assertEquals(recorder.requestId, known.receipt().requestId());
            assertEquals(recorder.requestId, recorder.original.requestId());
            assertEquals(recorder.requestId, recorder.known.receipt().requestId());
            assertEquals(fixture.readContract.operation().value(), recorder.prepared.step());
            assertEquals(known.originalReceipt(), recorder.known.originalReceipt());
            assertEquals(reads + 1, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites());
            assertEquals(sequence, fixture.sequence());
        }
    }

    @Test void diagnosticFailureBeforeNativeReadStopsTheActualEndpointWrite() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("before-native"), false)) {
            var request = request(fixture); var recorder = new Recorder(fixture, Fail.PREPARED, false);
            int reads = fixture.nativeReadWrites();
            PlanningReadResult.Unavailable<?> unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class,
                    fixture.reads.read(fixture.readContract, request, recorder));
            assertEquals(List.of("prepared", "failed"), recorder.events); assertNotNull(recorder.requestId);
            assertTrue(unavailable.original().isEmpty()); assertTrue(recorder.failedOriginal.isEmpty());
            assertEquals(reads, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void diagnosticFailureAfterTheActualReturnKeepsTheExactOriginalAckUnavailable() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("after-native"), false)) {
            var request = request(fixture); var recorder = new Recorder(fixture, Fail.RECEIVED, false);
            int reads = fixture.nativeReadWrites();
            PlanningReadResult.Unavailable<?> unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class,
                    fixture.reads.read(fixture.readContract, request, recorder));
            assertEquals(List.of("prepared", "received", "failed"), recorder.events);
            assertSame(recorder.original, unavailable.original().orElseThrow());
            assertSame(recorder.original, recorder.failedOriginal.orElseThrow());
            assertEquals(recorder.requestId, recorder.original.requestId());
            assertEquals(reads + 1, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void knownDiagnosticFailurePreservesTheAlreadyArchivedReadRatherThanFabricatingAnotherResult() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("after-known"), false)) {
            var request = request(fixture); var recorder = new Recorder(fixture, Fail.KNOWN, false);
            int reads = fixture.nativeReadWrites();
            PlanningReadResult.Unavailable<?> unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class,
                    fixture.reads.read(fixture.readContract, request, recorder));
            assertEquals(List.of("prepared", "received", "known", "failed"), recorder.events);
            assertSame(recorder.original, unavailable.original().orElseThrow());
            fixture.journal.locked(locked -> {
                assertEquals(recorder.known.receipt(), fixture.archive.withSession(locked.writerSession()).loadRead(recorder.known.originalReceipt()));
                return null;
            });
            assertEquals(reads + 1, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void failedDiagnosticCannotDiscardAnActualNativeReturnOrTriggerAnotherWrite() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("failed-diagnostic"), false)) {
            var request = request(fixture); var recorder = new Recorder(fixture, Fail.RECEIVED, true);
            int reads = fixture.nativeReadWrites();
            PlanningReadResult.Unavailable<?> unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class,
                    fixture.reads.read(fixture.readContract, request, recorder));
            assertSame(recorder.original, unavailable.original().orElseThrow());
            assertTrue(unavailable.reason().contains("failure diagnostic unavailable"));
            assertEquals(List.of("prepared", "received", "failed"), recorder.events);
            assertEquals(reads + 1, fixture.nativeReadWrites()); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void actualSourceGuardFailureHasNoPreparedRequestAndIsRecordedAsAnUnavailableRead() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("source-failure"), false)) {
            var original = request(fixture); var source = original.source();
            var foreign = new G2Source(source.machineId(), source.observedAtUtc(), "foreign-build", source.sourceRef());
            var request = new PlanningReadRequest(original.before(), foreign, original.sessionId(), original.operation(), original.arguments(), original.deadline());
            var recorder = new Recorder(fixture, Fail.NONE, false); int reads = fixture.nativeReadWrites();
            PlanningReadResult.Unavailable<?> unavailable = assertInstanceOf(PlanningReadResult.Unavailable.class,
                    fixture.reads.read(fixture.readContract, request, recorder));
            assertEquals(List.of("failed"), recorder.events); assertNull(recorder.requestId);
            assertTrue(unavailable.original().isEmpty()); assertEquals(reads, fixture.nativeReadWrites());
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    private static PlanningReadRequest request(ActionWriterIntegrationFixture fixture) throws Exception {
        var command = fixture.command("read-diagnostic-data");
        return new PlanningReadRequest(command.before(), command.source(), command.sessionId(), fixture.readContract.operation(),
                new OpportunityJson.Obj(Map.of()), command.deadline());
    }
    private static final class Recorder implements PlanningReadCoordinator.ReadLifecycleObserver {
        private final ActionWriterIntegrationFixture fixture; private final Fail fail; private final boolean failFailed;
        private final List<String> events = new ArrayList<>();
        private String requestId; private NativeRequest prepared; private NativeActionPort.DispatchOutcome original;
        private PlanningReadResult.Known<?> known; private Optional<NativeActionPort.DispatchOutcome> failedOriginal = Optional.empty();
        private Recorder(ActionWriterIntegrationFixture fixture, Fail fail, boolean failFailed) {
            this.fixture = fixture; this.fail = fail; this.failFailed = failFailed;
        }
        private void requireOriginalSession(ContinuityStorePort.Session same, ReadContract<?> contract) throws IOException {
            fixture.writer.requireSession(same); assertSame(fixture.readContract, contract);
        }
        @Override public void prepared(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request,
                String actualRequestId, NativeRequest actual) throws IOException {
            requireOriginalSession(same, contract); events.add("prepared"); requestId = actualRequestId; prepared = actual;
            if (fail == Fail.PREPARED) throw new IOException("controlled prepared diagnostic persistence failure");
        }
        @Override public void received(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request,
                String actualRequestId, NativeActionPort.DispatchOutcome actual) throws IOException {
            requireOriginalSession(same, contract); events.add("received"); assertEquals(requestId, actualRequestId); original = actual;
            if (fail == Fail.RECEIVED) throw new IOException("controlled received diagnostic persistence failure");
        }
        @Override public void known(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadResult.Known<?> actual) throws IOException {
            requireOriginalSession(same, contract); events.add("known"); known = actual;
            assertEquals(actual.receipt(), fixture.archive.withSession(same).loadRead(actual.originalReceipt()));
            if (fail == Fail.KNOWN) throw new IOException("controlled known diagnostic persistence failure");
        }
        @Override public void failed(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request,
                Optional<NativeActionPort.DispatchOutcome> actual, String reason) throws IOException {
            requireOriginalSession(same, contract); events.add("failed"); failedOriginal = actual;
            if (failFailed) throw new IOException("controlled failed diagnostic persistence failure");
        }
    }
}
