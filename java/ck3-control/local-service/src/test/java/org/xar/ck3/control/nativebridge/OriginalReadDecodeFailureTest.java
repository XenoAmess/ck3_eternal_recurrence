package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual native READ, coordinator and archive boundaries; no runtime qualification is issued. */
final class OriginalReadDecodeFailureTest {
    @TempDir Path root;
    private static final OperationKey QUERY = new OperationKey("query-fixture-decode-failure-v1");
    private static final String CAPABILITY = "game.query.fixture-decode-failure";
    private static final class ActualDecodeFailure extends IllegalArgumentException implements OriginalReadDecodeFailure {
        private static final long serialVersionUID = 1L;
        private final ReadContract<?> contract;
        private final PlanningReadReceipt original;
        ActualDecodeFailure(ReadContract<?> contract, PlanningReadReceipt original) {
            super("original source decode failed"); this.contract = contract; this.original = original;
        }
        @Override public void requireOriginal(ReadContract<?> installed, PlanningReadRequest request, PlanningReadReceipt receipt) {
            if (contract != installed || original != receipt || request != original.request())
                throw new IllegalArgumentException("decode failure lost identical live producer custody");
        }
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ReadContract<RawJson> contract(ExactRef source, Function<PlanningReadReceipt, RawJson> decode) {
        return new ReadContract<>("fixture-decode-failure/v1", QUERY, Optional.of(CAPABILITY), "fixture-decode-failure",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                (request, id) -> new NativeRequest(QUERY.value(), CAPABILITY, raw("{}")), decode,
                receipt -> { throw new IllegalArgumentException("pure replay retains its ordinary source failure"); });
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(
            Function<ExactRef, List<ReadContract<?>>> contracts) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-decode-failure", contracts,
                request -> raw("{\"original_payload\":true}"));
    }
    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual, ReadContract<?> contract) throws IOException, InterruptedException {
        var command = actual.command("decode-read-basis");
        return new PlanningReadRequest(command.before(), command.source(), command.sessionId(), contract.operation(),
                new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(10));
    }
    @Test void actualLiveDecoderCauseSurvivesNativeArchiveAndFailurePublicationWithoutAnotherRead() throws Exception {
        AtomicReference<ReadContract<RawJson>> installed = new AtomicReference<>();
        AtomicReference<ActualDecodeFailure> thrown = new AtomicReference<>();
        var scenario = scenario(source -> {
            var contract = contract(source, receipt -> {
                var failure = new ActualDecodeFailure(installed.get(), receipt); thrown.set(failure); throw failure;
            });
            installed.set(contract); return List.of(contract);
        });
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("actual"), false, scenario)) {
            AtomicReference<PlanningReadResult.Unavailable<?>> published = new AtomicReference<>();
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadResult.Known<?> value) {
                    if(contract==installed.get())fail("a decoder failure must not publish Known");
                }
                @Override public void afterUnavailable(ContinuityStorePort.Session same, ReadContract<?> contract,
                        PlanningReadRequest request, PlanningReadResult.Unavailable<?> value,
                        Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                    if(contract!=installed.get())return;
                    assertSame(thrown.get(), value.decodeFailure().orElseThrow());
                    try { attempted.orElseThrow().requireOriginal(same, contract, request, value, actual.archive.withSession(same)); }
                    catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
                    published.set(value);
                }
            });
            var result = assertInstanceOf(PlanningReadResult.Unavailable.class, actual.reads.read(installed.get(), request(actual, installed.get())));
            assertSame(thrown.get(), result.decodeFailure().orElseThrow()); assertSame(published.get(), result);
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class, result.original().orElseThrow()).nativeOk());
            assertEquals(1, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
            assertThrows(IllegalArgumentException.class, () -> installed.get().replay(thrown.get().original));
            assertEquals(1, actual.nativeReadWrites());
        }
    }
    @Test void callbackDiagnosticsKeepTheSameTypedCauseAndOriginalAck() throws Exception {
        AtomicReference<ReadContract<RawJson>> installed = new AtomicReference<>();
        AtomicReference<ActualDecodeFailure> thrown = new AtomicReference<>();
        var scenario = scenario(source -> {
            var contract = contract(source, receipt -> {
                var failure = new ActualDecodeFailure(installed.get(), receipt); thrown.set(failure); throw failure;
            });
            installed.set(contract); return List.of(contract);
        });
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("callback"), false, scenario)) {
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadResult.Known<?> known) { if(contract==installed.get())fail(); }
                @Override public void afterUnavailable(ContinuityStorePort.Session same, ReadContract<?> contract,
                        PlanningReadRequest request, PlanningReadResult.Unavailable<?> value) {
                    if(contract==installed.get())throw new IllegalStateException("actual callback failure");
                }
            });
            PlanningReadCoordinator.ReadLifecycleObserver observer = new PlanningReadCoordinator.ReadLifecycleObserver() {
                @Override public void prepared(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request, String id, NativeRequest prepared) { }
                @Override public void received(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request, String id, NativeActionPort.DispatchOutcome original) { }
                @Override public void known(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadResult.Known<?> known) { fail(); }
                @Override public void failed(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadRequest request,
                        Optional<NativeActionPort.DispatchOutcome> original, String reason) throws IOException { throw new IOException("actual lifecycle diagnostic failure"); }
            };
            var result = assertInstanceOf(PlanningReadResult.Unavailable.class, actual.reads.read(installed.get(), request(actual, installed.get()), observer));
            assertSame(thrown.get(), result.decodeFailure().orElseThrow());
            assertSame(thrown.get().original.original(), result.original().orElseThrow());
            assertTrue(result.reason().contains("actual failed-query publication unavailable"));
            assertTrue(result.reason().contains("read lifecycle failure diagnostic unavailable"));
            assertEquals(1, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void anotherReceiptCannotLaunderAnOrdinaryFailureIntoLiveDecodeCustody() throws Exception {
        AtomicReference<ReadContract<RawJson>> installed = new AtomicReference<>();
        AtomicReference<PlanningReadReceipt> first = new AtomicReference<>();
        var scenario = scenario(source -> {
            var contract = contract(source, receipt -> {
                if (first.compareAndSet(null, receipt)) return receipt.original().originalResultToken().orElseThrow();
                throw new ActualDecodeFailure(installed.get(), first.get());
            });
            installed.set(contract); return List.of(contract);
        });
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("wrong-origin"), false, scenario)) {
            var firstResult=actual.reads.read(installed.get(), request(actual, installed.get()));
            assertInstanceOf(PlanningReadResult.Known.class, firstResult, () -> "actual first original READ: "+firstResult);
            var result = assertInstanceOf(PlanningReadResult.Unavailable.class, actual.reads.read(installed.get(), request(actual, installed.get())));
            assertTrue(result.decodeFailure().isEmpty());
            assertTrue(result.reason().contains("decode failure lost identical live producer custody"));
            assertEquals(2, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
            assertThrows(IllegalArgumentException.class, () -> new PlanningReadResult.Unavailable<>("no original", Optional.empty(),
                    Optional.of(new ActualDecodeFailure(installed.get(), first.get()))));
        }
    }
}
