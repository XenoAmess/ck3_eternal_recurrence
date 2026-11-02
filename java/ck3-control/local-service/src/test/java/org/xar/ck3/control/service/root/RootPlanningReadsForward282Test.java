package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** New facade/view boundaries over real software packets, writer, guards and archive; no live endpoint. */
final class RootPlanningReadsForward282Test {
    private static final OperationKey OP = new OperationKey("query-root-planning-forward-v1");
    private static final String CAP = "game.query.root-planning-forward";
    private static final RawJson JSON = new RawJson("{}".getBytes(StandardCharsets.UTF_8));
    private static final String DURABLE = "xar.immutable-artifact-commit/v1";
    private static final String PLANNING = "xar.immutable-artifact-commit/v1-planning";
    @TempDir Path root;

    private static ReadContract<RawJson> contract(ExactRef source) {
        return new ReadContract<>("root-planning-forward/v1", OP, Optional.of(CAP), "root-planning-forward",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                (request, requestId) -> new NativeRequest(OP.value(), CAP, JSON),
                receipt -> receipt.original().originalResultToken().orElseThrow());
    }

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(
            AtomicReference<ReadContract<RawJson>> selected) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "root-planning-forward", source -> {
            ReadContract<RawJson> installed = contract(source);
            selected.set(installed);
            return List.of(installed);
        }, request -> JSON);
    }

    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual, String name) throws Exception {
        var command = actual.command(name);
        return new PlanningReadRequest(command.before(), command.source(), command.sessionId(), OP,
                new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(10));
    }

    private static PlanningReadResult.Known<?> known(PlanningReadResult<RawJson> result, PlanningReadRequest requested) {
        if (!(result instanceof PlanningReadResult.Known<?> value))
            throw new AssertionError("real software READ must be Known, got " + result);
        assertEquals(JSON, value.value());
        assertSame(requested, value.receipt().request());
        assertTrue(value.receipt().original().nativeOk());
        return value;
    }

    /** Inspect this receipt's real CAS commit, without preserve/promotion or a fabricated archive. */
    private static void assertCommitSchema(ExactRef reference, String schema) throws IOException {
        Path payload = Path.of(reference.path());
        assertEquals(reference.sha256() + ".bin", payload.getFileName().toString());
        Path marker = payload.resolveSibling(reference.sha256() + ".commit.json");
        var row = StrictJson.object(StrictJson.parse(Files.readAllBytes(marker), 65_536),
                Set.of("schema", "payload", "payload_identity", "commit_identity"));
        assertEquals(schema, StrictJson.text(row.get("schema")));
        assertEquals(reference, ExactRef.fromJson(row.get("payload")));
    }

    @Test void explicitViewIsLazyAndRetainsTheOneWriterAndInstalledContract() throws Exception {
        var selected = new AtomicReference<ReadContract<RawJson>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("lazy"), false, scenario(selected))) {
            assertSame(actual.writer, actual.archive.writer());
            var sourceOwner = new RootPlanningReads(actual.archive.writer());
            var view = assertInstanceOf(RootPlanningReads.class, sourceOwner.planningReads());
            assertNotSame(sourceOwner, view);
            assertSame(view, view.planningReads(), "the explicit view is idempotent");
            assertNotSame(view, sourceOwner.planningReads(), "another explicit view may share this owner");
            assertFalse(sourceOwner.isBound());
            assertFalse(view.isBound());

            PlanningReadRequest requested = request(actual, "forward282-lazy");
            int before = actual.nativeReadWrites();
            int sourceChecksBefore = actual.sourceChecks.get();
            assertThrows(IllegalStateException.class, () -> view.bind(actual.reads));
            assertThrows(IllegalStateException.class, () -> sourceOwner.read(selected.get(), requested));
            assertThrows(IllegalStateException.class, () -> view.read(selected.get(), requested));
            assertEquals(before, actual.nativeReadWrites());
            assertEquals(sourceChecksBefore, actual.sourceChecks.get());

            sourceOwner.bind(actual.reads);
            assertTrue(sourceOwner.isBound());
            assertTrue(view.isBound());
            assertThrows(IllegalStateException.class, () -> sourceOwner.bind(actual.reads));
            ReadContract<RawJson> lookalike = contract(selected.get().sourceRef());
            assertNotSame(selected.get(), lookalike);
            assertThrows(ContractViolationException.class, () -> view.read(lookalike, requested));
            assertEquals(before, actual.nativeReadWrites(), "same-shaped unregistered contract never dispatches");
            assertEquals(sourceChecksBefore, actual.sourceChecks.get());

            known(sourceOwner.read(selected.get(), requested), requested);
            assertEquals(before + 1, actual.nativeReadWrites());
            PlanningReadRequest borrowedRequest = request(actual, "forward282-borrowed");
            int beforeBorrowed = actual.nativeReadWrites();
            actual.writer.locked(same -> {
                actual.writer.requireSession(same);
                known(view.read(same, selected.get(), borrowedRequest), borrowedRequest);
                return null;
            });
            assertEquals(beforeBorrowed + 1, actual.nativeReadWrites());

            var foreignSelected = new AtomicReference<ReadContract<RawJson>>();
            try (var foreign = new ActionWriterIntegrationFixture(root.resolve("foreign"), false, scenario(foreignSelected))) {
                int ownReads = actual.nativeReadWrites(), foreignReads = foreign.nativeReadWrites();
                int ownChecks = actual.sourceChecks.get(), foreignChecks = foreign.sourceChecks.get();
                foreign.writer.locked(other -> {
                    foreign.writer.requireSession(other);
                    var rejected = assertThrows(UncheckedIOException.class,
                            () -> view.read(other, selected.get(), borrowedRequest));
                    assertInstanceOf(IOException.class, rejected.getCause());
                    assertEquals("borrowed session belongs to a different ContinuityWriter authority",
                            rejected.getCause().getMessage());
                    foreign.writer.requireSession(other);
                    return null;
                });
                assertEquals(ownReads, actual.nativeReadWrites());
                assertEquals(foreignReads, foreign.nativeReadWrites());
                assertEquals(ownChecks, actual.sourceChecks.get());
                assertEquals(foreignChecks, foreign.sourceChecks.get());
                assertEquals(0, foreign.nativeActionWrites());
            }

            var escaped = new AtomicReference<ContinuityStorePort.Session>();
            actual.writer.locked(same -> { escaped.set(same); return null; });
            int beforeClosed = actual.nativeReadWrites();
            int beforeClosedChecks = actual.sourceChecks.get();
            var closed = assertThrows(ContractViolationException.class,
                    () -> view.read(escaped.get(), selected.get(), borrowedRequest));
            assertEquals("live original-lock session on owning thread required", closed.getMessage());
            assertEquals(beforeClosed, actual.nativeReadWrites());
            assertEquals(beforeClosedChecks, actual.sourceChecks.get());
            assertEquals(0, actual.nativeActionWrites());
            assertTrue(actual.sourceChecks.get() > 0, "positive reads retained real source guards");
        }
    }

    @Test void defaultKnownRemainsDurableWhileViewKnownUsesPlanningAndFailureCustodyStaysStrong() throws Exception {
        var selected = new AtomicReference<ReadContract<RawJson>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("modes"), false, scenario(selected))) {
            var sourceOwner = new RootPlanningReads(actual.archive.writer());
            var view = assertInstanceOf(RootPlanningReads.class, sourceOwner.planningReads());
            sourceOwner.bind(actual.reads);
            // Original fixture edge is armed before any scenario READ, not an invented negative ACK.
            actual.rejectNextScenarioReadAfter(2);

            PlanningReadRequest strongRequest = request(actual, "forward282-default");
            int beforeStrong = actual.nativeReadWrites();
            var strong = known(sourceOwner.read(selected.get(), strongRequest), strongRequest);
            assertEquals(beforeStrong + 1, actual.nativeReadWrites());
            assertCommitSchema(strong.originalReceipt(), DURABLE);

            PlanningReadRequest plannedRequest = request(actual, "forward282-planning");
            int beforePlanning = actual.nativeReadWrites();
            var planned = known(view.read(selected.get(), plannedRequest), plannedRequest);
            assertEquals(beforePlanning + 1, actual.nativeReadWrites());
            assertNotEquals(strong.originalReceipt(), planned.originalReceipt());
            assertCommitSchema(planned.originalReceipt(), PLANNING);
            assertSame(view, view.planningReads());

            PlanningReadRequest failedRequest = request(actual, "forward282-failed");
            int beforeFailure = actual.nativeReadWrites();
            var observed = new AtomicReference<PlanningReadResult.Unavailable<?>>();
            var callbacks = new AtomicInteger();
            actual.writer.locked(same -> {
                PlanningReadPort.FailureEvidenceObserver observer = (original, identical, current, exact, attempted, originals) -> {
                    assertSame(same, original);
                    actual.writer.requireSession(original);
                    assertSame(selected.get(), identical);
                    assertSame(failedRequest, current);
                    var proof = attempted.orElseThrow();
                    proof.requireOriginal(original, identical, current, exact, originals);
                    var equalRequest = new PlanningReadRequest(current.origin(), current.source(), current.sessionId(),
                            current.operation(), current.arguments(), current.deadline());
                    assertEquals(current, equalRequest);
                    assertNotSame(current, equalRequest);
                    assertThrows(ContractViolationException.class,
                            () -> proof.requireOriginal(original, identical, equalRequest, exact, originals));
                    var ack = assertInstanceOf(NativeActionPort.AckReceived.class, proof.original());
                    assertFalse(ack.nativeOk());
                    assertSame(ack, exact.original().orElseThrow());
                    assertCommitSchema(proof.originalRef(), DURABLE);
                    assertCommitSchema(proof.preparedRef(), DURABLE);
                    assertEquals(ack, originals.load(proof.originalRef()));
                    assertEquals(proof.prepared(), originals.loadRequest(proof.preparedRef()));
                    observed.set(exact);
                    callbacks.incrementAndGet();
                };
                var failed = view.readWithFailureEvidence(same, selected.get(), failedRequest, observer);
                assertNotNull(observed.get());
                assertSame(observed.get(), failed);
                assertInstanceOf(PlanningReadResult.Unavailable.class, failed);
                return null;
            });
            assertEquals(1, callbacks.get());
            assertEquals(beforeFailure + 1, actual.nativeReadWrites());
            assertEquals(0, actual.nativeActionWrites());
            assertTrue(actual.sourceChecks.get() > 0);
        }
    }
}
