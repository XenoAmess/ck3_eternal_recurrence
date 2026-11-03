package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Public reducer and actual owned software CAS; no Root issuer, commit of the proposed row or live Native. */
final class ActionAuthorityHistoricalScopeTest {
    private static final ActionPorts.HistoricalReadLimits LIMITS =
            new ActionPorts.HistoricalReadLimits(4096, 256L * 1024 * 1024, 8192);
    @TempDir Path directory;

    private static ActionContinuityAuthority authority(ActionPorts.OutcomeArchive archive,
            Supplier<ContinuityStorePort.Session> sessions) {
        ActionPorts.GuardPort guard = (head, command) -> { throw new AssertionError("reduce cannot call guard"); };
        ActionPorts.RecordedEvidenceVerifier verifier = (head, receipt) -> { throw new AssertionError("reduce cannot call evidence verifier"); };
        ActionPorts.PreparationPort policy = new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new AssertionError("reduce cannot prepare"); }
        };
        return sessions == null
                ? new ActionContinuityAuthority("owned-software-authority", archive, guard, verifier, Clock.systemUTC(), policy)
                : new ActionContinuityAuthority("owned-software-authority", archive, guard, verifier, Clock.systemUTC(), policy, sessions);
    }

    private static ActionCommand next(ActionCommand original) {
        return new ActionCommand(original.actionId() + "-next", original.origin(), original.source(), original.sessionId(),
                original.operation(), original.arguments(), original.expectation(), original.claims(), original.deadline(), original.protocolIdentity());
    }

    private static WriterContracts.Request originalRequest(ActionWriterIntegrationFixture fixture,
            WriterContracts.Head head, ActionCommand command) {
        var receipt = new ActionReceipt(1, Math.addExact(head.state().sequence(), 1), command,
                ActionCodec.bodySha256(command), new ActionState.IntentDurable());
        var receiptRef = fixture.archive.preserveReceipt(receipt);
        var record = new ActionRecord(receipt, ContinuityActionJournal.recordHead(head.state()));
        var recordRef = fixture.archive.preserveRecord(record);
        var details = StrictJson.object();
        details.put("evidence_id", command.actionId() + ":" + receipt.sequence());
        details.set("source", ProposalLifecycleCodec.source(command.source()));
        details.set("receipt_ref", recordRef.toJson());
        return new WriterContracts.Request(ContinuityActionJournal.KIND, ContinuityJson.canonical(details),
                List.of(recordRef, receiptRef));
    }

    private static final class ObservedArchive {
        final AtomicInteger records = new AtomicInteger();
        final AtomicInteger scopes = new AtomicInteger();
        final ActionPorts.OutcomeArchive archive;
        ObservedArchive(ActionPorts.OutcomeArchive actual, IOException completedScopeFailure) {
            archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> {
                        if (method.getName().equals("loadRecord")) records.incrementAndGet();
                        boolean scope = method.getName().equals("inHistoricalReadScope");
                        if (scope) scopes.incrementAndGet();
                        Object result;
                        try { result = method.invoke(actual, arguments); }
                        catch (InvocationTargetException failure) { throw failure.getCause(); }
                        // Adapter failure after the actual native-CAS scope has completed; not a forced CloseHandle failure.
                        if (scope && completedScopeFailure != null) throw completedScopeFailure;
                        return result;
                    });
        }
    }

    @Test void realArchivedHistoryMatchesLegacyAndLegacyNestedRouteRemainsAvailable() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("normal"), false)) {
            var command = fixture.command("authority-history");
            fixture.journal.locked(locked -> locked.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            fixture.writer.locked(same -> {
                var head = same.head();
                assertTrue(ContinuityActionJournal.recordHead(head.state()).isPresent());
                var request = originalRequest(fixture, head, next(command));
                var observed = new ObservedArchive(fixture.archive, null);
                var borrowed = new AtomicInteger();
                var legacy = authority(observed.archive, null);
                var opted = authority(observed.archive, () -> {
                    borrowed.incrementAndGet();
                    try { return fixture.writer.borrowedSession(); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                });
                ContinuityState expected = legacy.reduce(head.state(), request);
                assertEquals(0, observed.scopes.get());
                assertEquals(expected.toJson(), opted.reduce(head.state(), request).toJson());
                assertEquals(1, observed.scopes.get());
                assertEquals(1, borrowed.get());
                assertEquals(expected.toJson(), fixture.archive.inHistoricalReadScope(same, LIMITS,
                        scoped -> legacy.reduce(head.state(), request)).toJson());

                assertThrows(IOException.class, () -> fixture.archive.inHistoricalReadScope(same, LIMITS, scoped -> {
                    var nested = assertThrows(UncheckedIOException.class, () -> opted.reduce(head.state(), request));
                    assertTrue(nested.getCause().getMessage().contains("nested historical CAS"));
                    return null;
                }));
                assertEquals(expected.toJson(), fixture.archive.inHistoricalReadScope(same, LIMITS,
                        scoped -> legacy.reduce(head.state(), request)).toJson());
                assertEquals(head.digest(), same.head().digest());
                return null;
            });
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void firstReceiptSupplierAndCompletedScopeFailuresCannotReturnReducedState() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory.resolve("failure"), false)) {
            var command = fixture.command("authority-failure");
            fixture.journal.locked(locked -> locked.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            fixture.writer.locked(same -> {
                var head = same.head();
                var request = originalRequest(fixture, head, next(command));
                IOException marker = new IOException("completed-scope-original-marker");
                var observed = new ObservedArchive(fixture.archive, marker);
                var borrowed = new AtomicInteger();
                var opted = authority(observed.archive, () -> { borrowed.incrementAndGet(); return same; });
                var wrongKind = new WriterContracts.Request("not-an-action", request.details(), request.evidence());
                assertThrows(ContractViolationException.class, () -> opted.reduce(head.state(), wrongKind));
                assertEquals(0, borrowed.get());
                assertEquals(0, observed.records.get());
                var failed = assertThrows(UncheckedIOException.class, () -> opted.reduce(head.state(), request));
                assertSame(marker, failed.getCause());
                assertEquals(1, borrowed.get());
                assertEquals(1, observed.scopes.get());
                assertEquals(1, observed.records.get(), "the original second record load cannot run after scope failure");

                var supplierArchive = new ObservedArchive(fixture.archive, null);
                UncheckedIOException supplierFailure = new UncheckedIOException(new IOException("borrow-marker"));
                var unavailable = authority(supplierArchive.archive, () -> { throw supplierFailure; });
                assertSame(supplierFailure, assertThrows(UncheckedIOException.class, () -> unavailable.reduce(head.state(), request)));
                assertEquals(1, supplierArchive.records.get(), "receipt/source validation precedes supplier resolution");
                assertEquals(0, supplierArchive.scopes.get());
                assertEquals(head.digest(), same.head().digest());
                return null;
            });
            assertEquals(0, fixture.nativeActionWrites());
        }
    }
}
