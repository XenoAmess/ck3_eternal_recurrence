package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual temporary Windows writer transactions; no Game operation or live ledger is used. */
class WriterFieldOwnershipTest {
    @TempDir Path root;
    private static final List<String> CYCLE_FIELDS = List.of(ORDINARY_CYCLE_FIELD, ORDINARY_SAVED_CYCLE_FIELD,
            ORDINARY_CYCLE_REBIND_FIELD, ORDINARY_BATCH_BOUNDARY_FIELD);
    private record Fixture(Layout layout, ContinuityWriter writer, List<ExactRef> sources) { }

    private Fixture fixture(String name, ObjectNode seed, UnaryOperator<ObjectNode> reducer) throws IOException {
        assertTrue(Platform.isWindows());
        WriterFixture base = new WriterFixture(root.resolve(name));
        Path anchor = Path.of(base.layout.anchor().path());
        Files.write(anchor, ContinuityJson.canonical(seed));
        Files.write(base.layout.snapshot(), ContinuityJson.canonical(seed));
        Layout layout = new Layout(base.layout.snapshot(), LedgerFiles.read(anchor, 65_536).pin().reference(), WriterFixture.MACHINE);
        List<ExactRef> sources = List.of(LedgerFiles.read(base.source, 65_536).pin().reference());
        TransitionAuthority authority = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, Request request) { return request.identity(); }
            @Override public ContinuityState reduce(ContinuityState predecessor, Request request) {
                return ContinuityState.fromJson(reducer.apply(predecessor.toJson()), predecessor.machineId());
            }
        };
        return new Fixture(layout, new ContinuityWriter(layout, sources, authority, StorageWriteGuardTestSupport.forLayout(layout)), sources);
    }
    private static ObjectNode seeded() {
        ObjectNode row = WriterFixture.state();
        for (String field : CYCLE_FIELDS) row.putObject(field).put("retained", field);
        row.putObject("UNKNOWN").put("AUTO11558", "must_remain_unresolved");
        row.putArray("unknown_requests").add(11558);
        return row;
    }
    private static Request request(String kind, String id) {
        ObjectNode details = StrictJson.object(); details.put("evidence_id", id); details.put("source", "writer-ownership-fixture/v1");
        return new Request(kind, ContinuityJson.canonical(details), List.of());
    }
    private static void noEvent(Fixture fixture) throws IOException {
        assertFalse(Files.exists(fixture.layout().event(1)));
        long sequence = fixture.writer().locked(session -> session.head().state().sequence());
        assertEquals(0L, sequence);
    }

    @Test void unrelatedAuthorityCannotAddChangeRemoveOrCoerceMissingAndNullCycleFields() throws Exception {
        int index = 0;
        for (String field : CYCLE_FIELDS) {
            for (int operation = 0; operation < 4; operation++) {
                ObjectNode before = seeded();
                if (operation == 0) before.remove(field);
                if (operation == 1) before.putNull(field);
                int actualOperation = operation;
                Fixture fixture = fixture("unrelated-" + index++, before, next -> {
                    if (actualOperation == 0) next.putNull(field);
                    else if (actualOperation == 1) next.remove(field);
                    else if (actualOperation == 2) next.put(field, "changed");
                    else next.remove(field);
                    return next;
                });
                Request request = request(ACTION_LIFECYCLE_KIND, "unrelated-" + index);
                assertThrows(ContractViolationException.class, () -> fixture.writer().preview(request));
                noEvent(fixture);
            }
        }
    }

    @Test void cycleAndBatchKindsHaveSeparateFieldOwnershipAndKeepOriginalUnknownAndPending() throws Exception {
        int index = 0;
        for (String kind : List.of(ORDINARY_CYCLE_KIND, ORDINARY_BATCH_KIND)) {
            List<String> owned = kind.equals(ORDINARY_CYCLE_KIND)
                    ? List.of(ORDINARY_CYCLE_FIELD, ORDINARY_CYCLE_REBIND_FIELD)
                    : List.of(ORDINARY_SAVED_CYCLE_FIELD, ORDINARY_BATCH_BOUNDARY_FIELD);
            ObjectNode before = seeded();
            Fixture allowed = fixture("allowed-" + index++, before, next -> {
                for (String field : owned) next.putObject(field).put("actual", "new-branch");
                return next;
            });
            Request request = request(kind, "owned-" + index);
            Receipt receipt = allowed.writer().commit(allowed.writer().preview(request));
            assertEquals(Disposition.COMMITTED, receipt.disposition());
            for (String field : CYCLE_FIELDS) if (!owned.contains(field)) assertEquals(before.get(field), receipt.head().toJson().get(field));
            for (String field : PRESERVED_RUNTIME_FIELDS) {
                assertEquals(before.has(field), receipt.head().toJson().has(field));
                if (before.has(field)) assertEquals(before.get(field), receipt.head().toJson().get(field));
            }
            assertEquals(Disposition.ALREADY_COMMITTED, allowed.writer().commit(allowed.writer().preview(request)).disposition());
            assertFalse(Files.exists(allowed.layout().event(2)));
            for (String foreign : CYCLE_FIELDS) if (!owned.contains(foreign)) {
                Fixture rejected = fixture("foreign-" + index++, seeded(), next -> { next.remove(foreign); return next; });
                assertThrows(ContractViolationException.class, () -> rejected.writer().preview(request(kind, "foreign-" + foreign)));
                noEvent(rejected);
            }
            Fixture pending = fixture("pending-" + index++, seeded(), next -> { next.remove("pending_cycle"); return next; });
            assertThrows(ContractViolationException.class, () -> pending.writer().preview(request(kind, "pending")));
            noEvent(pending);
        }
    }

    @Test void commitRechecksFieldOwnershipInsideTheActualWriterLockBeforeAnyDurableWrite() throws Exception {
        AtomicInteger reductions = new AtomicInteger();
        Fixture fixture = fixture("recheck", seeded(), next -> {
            next.putObject(ORDINARY_CYCLE_FIELD).put("actual", "cycle");
            if (reductions.incrementAndGet() > 1) next.remove(ORDINARY_SAVED_CYCLE_FIELD);
            return next;
        });
        Prepared prepared = fixture.writer().preview(request(ORDINARY_CYCLE_KIND, "late-cross-owner"));
        assertThrows(ContractViolationException.class, () -> fixture.writer().commit(prepared));
        noEvent(fixture);
    }

    @Test void borrowedSessionIsTheSameAuthorityAndCannotOpenReplaceEscapeOrCrossThreads() throws Exception {
        Fixture fixture = fixture("borrowed", seeded(), UnaryOperator.identity());
        Fixture other = fixture("other-authority", seeded(), UnaryOperator.identity());
        ContinuityWriter sameLayout = new ContinuityWriter(fixture.layout(), fixture.sources(), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { return request.identity(); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) { return head; }
        }, StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        assertThrows(IOException.class, fixture.writer()::borrowedSession);
        AtomicReference<ContinuityStorePort.Session> escaped = new AtomicReference<>();
        fixture.writer().locked(session -> {
            assertSame(session, fixture.writer().borrowedSession()); escaped.set(session);
            assertThrows(IOException.class, sameLayout::borrowedSession);
            assertThrows(IOException.class, other.writer()::borrowedSession);
            assertThrows(IOException.class, () -> fixture.writer().locked(nested -> null));
            assertThrows(IOException.class, () -> other.writer().locked(nested -> null));
            assertSame(session, fixture.writer().borrowedSession());
            AtomicReference<Throwable> crossThread = new AtomicReference<>();
            Thread child = new Thread(() -> { try { fixture.writer().borrowedSession(); } catch (Throwable failure) { crossThread.set(failure); } });
            child.start();
            try { child.join(5_000); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
            assertFalse(child.isAlive()); assertInstanceOf(IOException.class, crossThread.get());
            return null;
        });
        assertThrows(IOException.class, fixture.writer()::borrowedSession);
        assertThrows(ContractViolationException.class, () -> escaped.get().head());
    }

    @Test void sourceLoaderFailureRemovesBorrowedScopeAndNextTransactionUsesANewSession() throws Exception {
        Fixture fixture = fixture("cleanup", seeded(), UnaryOperator.identity());
        AtomicReference<ContinuityStorePort.Session> escaped = new AtomicReference<>();
        assertThrows(IOException.class, () -> fixture.writer().locked(session -> {
            escaped.set(session); assertSame(session, fixture.writer().borrowedSession());
            throw new IOException("actual source loader failure");
        }));
        assertThrows(IOException.class, fixture.writer()::borrowedSession);
        assertThrows(ContractViolationException.class, () -> escaped.get().head());
        fixture.writer().locked(session -> {
            assertNotSame(escaped.get(), session); assertSame(session, fixture.writer().borrowedSession()); return null;
        });
        assertThrows(IOException.class, fixture.writer()::borrowedSession);
    }

    @Test void newRetreatAndCrossRunSlotsUseTheOriginalRegisteredImportAndStrictBodyReferenceRoundTrip() throws Exception {
        int index = 0;
        for (DomainBodies.Slot slot : List.of(DomainBodies.Slot.ACTIVE_RETREAT, DomainBodies.Slot.CROSS_RUN_PLANNING)) {
            Fixture fixture = fixture("new-slot-" + index++, seeded(), UnaryOperator.identity());
            Path archiveRoot = fixture.layout().snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout().lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout().lock()));
            DomainBodies.Registration registration = new DomainBodies.Registration(slot, "fixture.original-state/v1", 65_536, fixture.sources(),
                    (head, previous, request, body) -> {
                        ObjectNode raw = ContinuityJson.parseObject(body, 65_536);
                        StrictJson.require(StrictJson.integer(raw.get("format_version"), 1, 1) == 1
                                && raw.get("pending").isNull() && raw.get("retained_unknown").isArray(), "actual complete original fixture body");
                        StrictJson.require(previous.isEmpty() && request.evidenceId().equals("explicit-original-state"), "source-bound first import qualification");
                        return ContinuityJson.digest(raw);
                    });
            TransitionAuthority unused = new TransitionAuthority() {
                @Override public String revalidate(ContinuityState head, Request request) { throw new AssertionError("domain requires its registered producer verifier"); }
                @Override public ContinuityState reduce(ContinuityState head, Request request) { throw new AssertionError("ordinary reducer cannot import a body"); }
            };
            ContinuityWriter writer = new ContinuityWriter(fixture.layout(), fixture.sources(), unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(artifacts), Optional.empty()), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
            ObjectNode original = StrictJson.object(); original.put("format_version", 1); original.putNull("pending");
            original.putArray("retained_unknown").add("AUTO11558");
            Path body = fixture.layout().snapshot().getParent().resolve("actual-original-state.json");
            Files.write(body, ContinuityJson.canonical(original));
            var request = new DomainBodies.ImportRequest(slot, registration.contractSchema(), LedgerFiles.read(body, 65_536).pin().reference(),
                    ContinuityJson.canonical(original), List.of(), "explicit-original-state");
            Receipt committed = writer.commitImport(writer.previewImport(request));
            assertEquals(Disposition.COMMITTED, committed.disposition());
            DomainBodies.Available available = assertInstanceOf(DomainBodies.Available.class, writer.read(slot));
            assertEquals(slot, available.reference().slot()); assertEquals(original, WriterContracts.object(available.canonicalBody()));
            assertEquals(available.reference(), DomainBodies.BodyRef.fromJson(available.reference().toJson()));
            assertEquals(available.reference(), DomainBodies.reference(committed.head(), slot).orElseThrow());
            assertEquals(seeded().get("pending_cycle"), committed.head().toJson().get("pending_cycle"));
            assertEquals(seeded().get("UNKNOWN"), committed.head().toJson().get("UNKNOWN"));
        }
    }

    @Test void rollbackRejectsForgedCycleHistoryAndPreservesAllOrdinaryBranchesDuringTheRealPairCommit() throws Exception {
        assertTrue(Platform.isWindows());
        var previous = new CanonicalContinuityTransactionsTest.PairFixture(root.resolve("rollback"));
        ObjectNode seed = previous.writer.locked(session -> session.head().state().toJson());
        for (String field : CYCLE_FIELDS) seed.putObject(field).put("retained", field);
        Path anchor = Path.of(previous.layout.anchor().path());
        Files.write(anchor, ContinuityJson.canonical(seed)); Files.write(previous.layout.snapshot(), ContinuityJson.canonical(seed));
        Layout layout = new Layout(previous.layout.snapshot(), LedgerFiles.read(anchor, 65_536).pin().reference(), WriterFixture.MACHINE);
        List<ExactRef> sources = List.of(LedgerFiles.read(previous.initial.source, 65_536).pin().reference());
        TransitionAuthority unused = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { throw new AssertionError("ordinary authority is not rollback qualification"); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) { throw new AssertionError("ordinary reducer is not rollback qualification"); }
        };
        ContinuityWriter writer = new ContinuityWriter(layout, sources, unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.empty(), Optional.of((head, proof) -> previous.evidence)), StorageWriteGuardTestSupport.forLayout(layout));
        RollbackPair.Plan plan = writer.previewRollback(previous.evidence.proof());
        for (String field : CYCLE_FIELDS) {
            ObjectNode reduced = plan.first().reduced().toJson(), committed = plan.first().committed().toJson();
            reduced.remove(field); committed.remove(field);
            var first = new RollbackPair.EventPlan(plan.first().request(), ContinuityState.fromJson(reduced, WriterFixture.MACHINE),
                    ContinuityState.fromJson(committed, WriterFixture.MACHINE));
            var forged = new RollbackPair.Plan(plan.originalHead(), plan.evidence(), first, plan.second(), plan.transactionId());
            assertThrows(ContractViolationException.class, () -> writer.commitRollback(forged));
            assertFalse(Files.exists(layout.event(2)));
        }
        writer.commitRollback(plan);
        ObjectNode actual = writer.locked(session -> session.head().state().toJson());
        for (String field : CYCLE_FIELDS) assertEquals(seed.get(field), actual.get(field));
        for (String field : PRESERVED_RUNTIME_FIELDS) if (seed.has(field)) assertEquals(seed.get(field), actual.get(field));
        assertEquals(0, writer.commitRollback(plan).writes());
    }
}
