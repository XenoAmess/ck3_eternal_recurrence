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
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exercises the actual temporary writer; native entry evidence is qualified by its production owner. */
class GameplayEntryWriterOwnershipTest {
    @TempDir Path root;
    private static final List<String> ENTRY_FIELDS = List.of(DRIVER_HISTORY_BASELINE_FIELD, GAMEPLAY_ENTRY_FIELD);
    private record Fixture(Layout layout, List<ExactRef> sources, ContinuityWriter writer) { }
    private Fixture fixture(String name, ObjectNode seed, UnaryOperator<ObjectNode> mutation) throws IOException {
        assertTrue(Platform.isWindows()); WriterFixture initial = new WriterFixture(root.resolve(name));
        Path anchor = Path.of(initial.layout.anchor().path());
        Files.write(anchor, ContinuityJson.canonical(seed)); Files.write(initial.layout.snapshot(), ContinuityJson.canonical(seed));
        Layout layout = new Layout(initial.layout.snapshot(), LedgerFiles.read(anchor, 65_536).pin().reference(), WriterFixture.MACHINE);
        List<ExactRef> sources = List.of(LedgerFiles.read(initial.source, 65_536).pin().reference());
        TransitionAuthority authority = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before, Request request) { return request.identity(); }
            @Override public ContinuityState reduce(ContinuityState before, Request request) {
                return ContinuityState.fromJson(mutation.apply(before.toJson()), before.machineId());
            }
        };
        return new Fixture(layout, sources, new ContinuityWriter(layout, sources, authority, StorageWriteGuardTestSupport.forLayout(layout)));
    }
    private static ObjectNode seed() {
        ObjectNode row = WriterFixture.state();
        row.putObject("UNKNOWN").put("AUTO11558", "unresolved_do_not_replay");
        row.putObject(ACTION_LIFECYCLE_FIELD).put("retained", "original-action-chain");
        for (String field : List.of(ORDINARY_CYCLE_FIELD, ORDINARY_SAVED_CYCLE_FIELD, ORDINARY_CYCLE_REBIND_FIELD, ORDINARY_BATCH_BOUNDARY_FIELD))
            row.putObject(field).put("retained", field);
        return row;
    }
    private static Request request(String kind, String id) {
        ObjectNode details = StrictJson.object(); details.put("evidence_id", id); details.put("source", "actual-writer-entry-fixture/v1");
        return new Request(kind, ContinuityJson.canonical(details), List.of());
    }
    @Test void everyOtherEventKindPreservesEntryMissingNullAndValueBeforeAnyReceipt() throws Exception {
        int counter = 0;
        for (String kind : List.of(ACTION_LIFECYCLE_KIND, ORDINARY_CYCLE_KIND, ORDINARY_BATCH_KIND, "settled_batch"))
            for (String field : ENTRY_FIELDS) for (int variant = 0; variant < 4; variant++) {
                ObjectNode before = seed();
                if (variant == 1) before.putNull(field);
                if (variant >= 2) before.putObject(field).put("retained", "actual-entry");
                int operation = variant;
                Fixture fixture = fixture("foreign-" + counter++, before, next -> {
                    if (operation == 0) next.putNull(field);
                    else if (operation == 1 || operation == 2) next.remove(field);
                    else next.putObject(field).put("changed", "forbidden");
                    return next;
                });
                assertThrows(ContractViolationException.class, () -> fixture.writer().preview(request(kind, "foreign-" + field)));
                assertFalse(Files.exists(fixture.layout().event(1)));
            }
    }
    @Test void entryWritesOnlyItsOwnFieldsAndRetainsTheExactActionUnknownPendingAndCycleState() throws Exception {
        ObjectNode before = seed();
        Fixture fixture = fixture("entry", before, next -> {
            next.putObject(DRIVER_HISTORY_BASELINE_FIELD).put("fixture", "first-actual-driver");
            next.putObject(GAMEPLAY_ENTRY_FIELD).put("fixture", "entry-evidence"); return next;
        });
        Request request = request(GAMEPLAY_ENTRY_KIND, "one-entry");
        Receipt result = fixture.writer().commit(fixture.writer().preview(request));
        assertEquals(Disposition.COMMITTED, result.disposition());
        for (String field : PRESERVED_RUNTIME_FIELDS) {
            assertEquals(before.has(field), result.head().toJson().has(field));
            if (before.has(field)) assertEquals(before.get(field), result.head().toJson().get(field));
        }
        for (String field : List.of(ACTION_LIFECYCLE_FIELD, ORDINARY_CYCLE_FIELD, ORDINARY_SAVED_CYCLE_FIELD,
                ORDINARY_CYCLE_REBIND_FIELD, ORDINARY_BATCH_BOUNDARY_FIELD)) assertEquals(before.get(field), result.head().toJson().get(field));
        assertEquals(Disposition.ALREADY_COMMITTED, fixture.writer().commit(fixture.writer().preview(request)).disposition());
        assertFalse(Files.exists(fixture.layout().event(2)));
        Fixture crossOwner = fixture("entry-cross-owner", seed(), next -> { next.remove(ORDINARY_CYCLE_FIELD); return next; });
        assertThrows(ContractViolationException.class, () -> crossOwner.writer().preview(request(GAMEPLAY_ENTRY_KIND, "cross-owner")));
    }
    @Test void entryOwnershipIsCheckedAgainAtCommitInsideTheOriginalLock() throws Exception {
        AtomicInteger calls = new AtomicInteger(); ObjectNode before = seed(); before.putNull(GAMEPLAY_ENTRY_FIELD);
        Fixture fixture = fixture("late", before, next -> { if (calls.incrementAndGet() > 1) next.remove(GAMEPLAY_ENTRY_FIELD); return next; });
        Prepared prepared = fixture.writer().preview(request(ORDINARY_CYCLE_KIND, "late-entry-change"));
        assertThrows(ContractViolationException.class, () -> fixture.writer().commit(prepared));
        assertFalse(Files.exists(fixture.layout().event(1)));
    }
    @Test void rollbackCannotRewriteEntryOrItsFirstDriverBaseline() throws Exception {
        assertTrue(Platform.isWindows());
        var original = new CanonicalContinuityTransactionsTest.PairFixture(root.resolve("rollback"));
        ObjectNode before = original.writer.locked(session -> session.head().state().toJson());
        for (String field : ENTRY_FIELDS) before.putObject(field).put("retained", field);
        Path anchor = Path.of(original.layout.anchor().path());
        Files.write(anchor, ContinuityJson.canonical(before)); Files.write(original.layout.snapshot(), ContinuityJson.canonical(before));
        Layout layout = new Layout(original.layout.snapshot(), LedgerFiles.read(anchor, 65_536).pin().reference(), WriterFixture.MACHINE);
        TransitionAuthority unused = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState state, Request request) { throw new AssertionError("entry guard cannot replace rollback authority"); }
            @Override public ContinuityState reduce(ContinuityState state, Request request) { throw new AssertionError("entry reducer cannot restore the original window"); }
        };
        ContinuityWriter writer = new ContinuityWriter(layout, List.of(LedgerFiles.read(original.initial.source, 65_536).pin().reference()), unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.empty(), Optional.of((head, proof) -> original.evidence)), StorageWriteGuardTestSupport.forLayout(layout));
        RollbackPair.Plan plan = writer.previewRollback(original.evidence.proof());
        for (String field : ENTRY_FIELDS) {
            ObjectNode reduced = plan.first().reduced().toJson(), committed = plan.first().committed().toJson(); reduced.remove(field); committed.remove(field);
            var changed = new RollbackPair.EventPlan(plan.first().request(), ContinuityState.fromJson(reduced, WriterFixture.MACHINE), ContinuityState.fromJson(committed, WriterFixture.MACHINE));
            var forged = new RollbackPair.Plan(plan.originalHead(), plan.evidence(), changed, plan.second(), plan.transactionId());
            assertThrows(ContractViolationException.class, () -> writer.commitRollback(forged)); assertFalse(Files.exists(layout.event(2)));
        }
        writer.commitRollback(plan);
        ObjectNode after = writer.locked(session -> session.head().state().toJson());
        for (String field : ENTRY_FIELDS) assertEquals(before.get(field), after.get(field));
        assertEquals(before.get("UNKNOWN"), after.get("UNKNOWN")); assertEquals(before.get("pending_cycle"), after.get("pending_cycle"));
        assertEquals(0, writer.commitRollback(plan).writes());
    }
    @Test void onceClaimSlotMustUseTheRegisteredFullBodyProducerAndItsReferenceRoundTrips() throws Exception {
        Fixture fixture = fixture("claim", seed(), UnaryOperator.identity());
        Path archiveRoot = fixture.layout().snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
        var archive = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout().lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout().lock()));
        var registration = new DomainBodies.Registration(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, "fixture.ordinary-once-claim/v1", 65_536, fixture.sources(),
                (head, previous, input, bytes) -> {
                    ObjectNode body = WriterContracts.object(bytes);
                    StrictJson.require(body.get("claims").isArray() && body.get("pending").isNull(), "full fixture claim body required");
                    return ContinuityJson.digest(body);
                });
        TransitionAuthority unused = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { throw new AssertionError("once claim is a registered original domain"); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) { throw new AssertionError("no second claim reducer"); }
        };
        ContinuityWriter writer = new ContinuityWriter(fixture.layout(), fixture.sources(), unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(archive), Optional.empty()), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        ObjectNode body = StrictJson.object(); body.putArray("claims"); body.putNull("pending");
        Path input = fixture.layout().snapshot().getParent().resolve("original-claims.json"); Files.write(input, ContinuityJson.canonical(body));
        var request = new DomainBodies.ImportRequest(registration.slot(), registration.contractSchema(), LedgerFiles.read(input, 65_536).pin().reference(),
                ContinuityJson.canonical(body), List.of(), "source-bound-first-claims");
        writer.commitImport(writer.previewImport(request));
        var actual = assertInstanceOf(DomainBodies.Available.class, writer.read(DomainBodies.Slot.ORDINARY_ONCE_CLAIM));
        assertEquals(body, WriterContracts.object(actual.canonicalBody()));
        assertEquals(actual.reference(), DomainBodies.BodyRef.fromJson(actual.reference().toJson()));
        assertEquals(seed().get("UNKNOWN"), writer.locked(session -> session.head().state().toJson().get("UNKNOWN")));
    }
}
