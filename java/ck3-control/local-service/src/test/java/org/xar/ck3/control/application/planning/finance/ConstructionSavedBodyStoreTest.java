package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Windows store/history/pinned-file boundaries. The fixture verifier grants no Root/SAVE/Game qualification. */
final class ConstructionSavedBodyStoreTest {
    @TempDir Path root;
    private final java.util.ArrayList<StorageWriteGuardTestSupport> retainedGuards = new java.util.ArrayList<>();
    @AfterEach void closeActualSoftwareAllocationScopes() throws IOException {
        for (StorageWriteGuardTestSupport guard : retainedGuards) guard.close();
    }
    @Test void actualSavedHistoricalBodyIsReadAfterALaterHeadAndMissingOrForgedHeadsDoNotInitialize() throws Exception {
        Fixture fixture = new Fixture(root);
        var saved = fixture.publish("actual-original", clear());
        fixture.publish("later-current", clear().with("later_observation", new Bool(true)));
        fixture.writer.locked(same -> {
            var original = ConstructionSavedBody.read(same, saved.head(), fixture.sources);
            assertEquals(clear(), original.ledger().original());
            original.requireUnchanged(same);
            assertEquals(2, same.head().state().sequence());
            assertThrows(IOException.class, () -> ConstructionSavedBody.read(same, fixture.anchor, fixture.sources));
            var forged = saved.head().toJson(); forged.put("manual_repair_count", 99);
            assertThrows(IOException.class, () -> ConstructionSavedBody.read(same,
                    ContinuityState.fromJson(forged, Fixture.MACHINE), fixture.sources));
            assertEquals(2, same.head().state().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(3)));
    }
    @Test void replacingTheSavedBodyWithIdenticalBytesStillFailsItsOriginalNativeIdentity() throws Exception {
        Fixture fixture = new Fixture(root);
        var saved = fixture.publish("original", clear());
        var reference = DomainBodies.reference(saved.head(), DomainBodies.Slot.CONSTRUCTION).orElseThrow();
        byte[] unchanged = Files.readAllBytes(Path.of(reference.payload().path()));
        Path replacement = root.resolve("same-content-new-file.json"); Files.write(replacement, unchanged);
        Files.move(replacement, Path.of(reference.payload().path()), StandardCopyOption.REPLACE_EXISTING);
        fixture.writer.locked(same -> {
            assertThrows(RuntimeException.class, () -> ConstructionSavedBody.read(same, saved.head(), fixture.sources));
            return null;
        });
        assertArrayEquals(unchanged, Files.readAllBytes(Path.of(reference.payload().path())));
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
    @Test void currentUnknownPendingSurvivesTheSavedBodyAndConflictingPendingBodiesAreRejected() {
        Obj original = ConstructionCoordinatorPendingTest.original().with("status", new Text("action_state_unknown"));
        var saved = ConstructionLedgerCodec.decodeLedger(encode(clear()));
        var current = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", original)));
        var provenance = provenance();
        Obj result = ConstructionRestoreReducer.reduce(saved, Optional.of(current), List.of(), provenance);
        assertEquals(original, result.get("pending"));
        assertEquals(provenance.toJson(), result.get("java_restored_construction_originals_v1"));
        Obj another = original.with("action_request_id", new Text("other-real-original"));
        var conflictingSaved = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", another)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreReducer.reduce(conflictingSaved, Optional.of(current), List.of(), provenance));
        var otherWorker = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", original.with("source_bridge_pid", new IntegerValue(java.math.BigInteger.valueOf(43))))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreReducer.reduce(otherWorker, Optional.of(current), List.of(), provenance));
        assertEquals(original, current.pending().orElseThrow().original());
    }
    @Test void currentPendingFromAnotherEpisodeOrActorCannotSurviveThroughSavedClearBody() {
        var saved = ConstructionLedgerCodec.decodeLedger(encode(clear()));
        Obj pending = ConstructionCoordinatorPendingTest.original().with("status", new Text("action_state_unknown"));
        for (Obj other : List.of(pending.with("episode_run_id", new Text("another-episode")),
                pending.with("actor_character_id", new IntegerValue(java.math.BigInteger.TWO)))) {
            var current = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", other)));
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreReducer.reduce(saved, Optional.of(current), List.of(), provenance()));
            assertEquals(other, current.pending().orElseThrow().original());
        }
    }
    @Test void canonicalRequestIdentityCannotHideAChangedOriginalCandidateOrQuoteEpoch() {
        Obj pending = ConstructionCoordinatorPendingTest.original();
        var ref = new ExactRef("D:/construction-fixture-receipt.json", 2, "a".repeat(64));
        var source = new org.xar.ck3.control.g2.common.G2Source("construction-test-machine", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        // Original native bridge PID42 remains distinct from this actual Game PID99.
        var game = new org.xar.ck3.control.contracts.GameGeneration(99, new org.xar.ck3.control.contracts.PythonOnlyUInt64(java.math.BigInteger.valueOf(133000000000000000L)));
        var frame = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                        new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(java.math.BigInteger.ONE, java.math.BigInteger.TWO, java.math.BigInteger.valueOf(100)),
                        "native:2", java.math.BigInteger.TWO, "episode"), 1);
        Obj diagnostic = obj("bridge_pid", new IntegerValue(java.math.BigInteger.valueOf(42)), "bridge_creation_date", new Text("legacy-process"));
        Obj query = obj("starting_snapshot", obj("diagnostics", diagnostic));
        Obj arguments = obj("candidate", pending.get("candidate"), "pre_proof_epoch", pending.get("pre_proof_epoch"),
                "ordinary_cash_request", obj("quoted_outlay", obj("query_observation", query)));
        var expected = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1, frame, source, "construction-test/v1",
                List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"), true)));
        var command = new org.xar.ck3.control.application.action.ActionCommand("actual-coordinator", frame, source, "actual-session", OrdinaryConstructionPolicy.OPERATION,
                arguments, expected, new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(), java.util.Set.of(), java.util.Set.of(), java.util.Set.of()),
                java.time.Instant.parse("2026-10-24T00:00:30Z"));
        String digest = ActionCodec.bodySha256(command);
        pending = pending.with("coordinator_action_id", new Text(command.actionId())).with("coordinator_body_sha256", new Text(digest))
                .with("action_request_id", new Text(org.xar.ck3.control.application.action.RequestIds.forActionBody(digest)));
        var receipt = new org.xar.ck3.control.application.action.ActionReceipt(1, 1, command, digest, new org.xar.ck3.control.application.action.ActionState.IntentDurable());
        var canonical = List.of(new ConstructionRestoreReducer.Canonical(receipt, ref));
        var saved = ConstructionLedgerCodec.decodeLedger(encode(clear()));
        var current = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", pending)));
        Obj result = ConstructionRestoreReducer.reduce(saved, Optional.of(current), canonical, provenance());
        assertEquals(new Text("action_state_unknown"), object(result.get("pending"), "retained unknown").get("status"));
        Obj changedCandidate = pending.with("candidate", object(pending.get("candidate"), "original candidate").with("building_type_id", new IntegerValue(java.math.BigInteger.valueOf(12))));
        Obj changedEpoch = pending.with("pre_proof_epoch", new IntegerValue(java.math.BigInteger.valueOf(4)));
        for (Obj changed : List.of(changedCandidate, changedEpoch)) {
            var other = ConstructionLedgerCodec.decodeLedger(encode(clear().with("pending", changed)));
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreReducer.reduce(saved, Optional.of(other), canonical, provenance()));
            assertEquals(changed, other.pending().orElseThrow().original());
        }
    }
    private static ConstructionRestoreProvenance provenance() {
        var ref = new ExactRef("D:/construction-fixture-original.json", 2, ActionCodec.sha256(new byte[]{'{','}'}));
        var game = new org.xar.ck3.control.contracts.GameGeneration(43, new org.xar.ck3.control.contracts.PythonOnlyUInt64(java.math.BigInteger.valueOf(133000000000000000L)));
        return new ConstructionRestoreProvenance(ref, ref, ref, 1, "a".repeat(64), "episode", java.math.BigInteger.ONE, game, "actual-replacement");
    }
    private static Obj clear() {
        return obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", Nil.INSTANCE,
                "applied", Nil.INSTANCE, "applied_prior", new Arr(List.of()));
    }
    private final class Fixture {
        static final String MACHINE = "construction-store-test-machine";
        final Layout layout;
        final ContinuityWriter writer;
        final List<ExactRef> sources;
        final ContinuityState anchor;
        Fixture(Path root) throws IOException {
            assertTrue(System.getProperty("os.name").startsWith("Windows"), "actual Windows ledger/FileID boundary is required; not skipped");
            Files.createDirectories(root);
            var state = StrictJson.object();
            state.put("schema", "root.ck3.continuity-window/v1"); state.put("machine_id", MACHINE); state.put("sequence", 0);
            state.put("window_id", 1); state.put("status", "running"); state.put("target_days", 10958); state.put("target_years", 30);
            state.put("calendar_year_days", 365.25); state.put("start_date_raw", 1000); state.put("target_date_raw", 1000 + 10958 * 24);
            state.put("last_settled_date_raw", 1000); state.put("last_settled_cycles", 1); state.put("manual_repair_count", 1);
            state.put("automatic_recovery_count", 0); state.put("binding_lineage_count", 0);
            var game = state.putObject("game_binding"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
            state.putNull("latest_binding"); var pending = state.putObject("pending_cycle"); pending.put("stage", "auto_unsettled"); pending.put("auto_sequence", 1);
            state.put("NEXT", 2); anchor = ContinuityState.fromJson(state, MACHINE);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial = root.resolve("anchor.json");
            Files.write(snapshot, ContinuityJson.canonical(state)); Files.write(initial, ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]); Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source = root.resolve("actual-fixture-producer.txt"); Files.writeString(source, "construction store boundary fixture");
            sources = List.of(ref(source));
            layout = new Layout(snapshot, ref(initial), MACHINE);
            Path archive = root.resolve("archive"); Files.createDirectory(archive);
            var guard = StorageWriteGuardTestSupport.create(layout.snapshot().getParent(), layout.lock(), 8 * 1024 * 1024);
            retainedGuards.add(guard);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive, layout.lock(), ConstructionDomainLifecycle.MAX_BYTES), guard);
            var registration = new DomainBodies.Registration(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA,
                    ConstructionDomainLifecycle.MAX_BYTES, sources, (head, previous, request, body) -> {
                        var decoded = ConstructionLedgerCodec.decodeLedger(body);
                        StrictJson.require(request.producerInput().length > 0 && encode(decoded.original()).length == body.length, "actual complete fixture body required");
                        return ActionCodec.sha256(body);
                    });
            writer = new ContinuityWriter(layout, sources, new TransitionAuthority() {
                @Override public String revalidate(ContinuityState head, Request input) { throw new AssertionError("domain imports use their actual store verifier"); }
                @Override public ContinuityState reduce(ContinuityState head, Request input) { throw new AssertionError("domain imports use their actual store reducer"); }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(store), Optional.empty()), guard);
            assertSame(guard, store.storageGuard()); assertSame(guard, writer.storageGuard());
        }
        Receipt publish(String identity, Obj body) throws IOException {
            Path original = rootPath().resolve(identity + ".json"); Files.write(original, encode(body));
            var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA, ref(original),
                    encode(obj("fixture_actual_producer", new Text(identity))), List.of(), identity);
            return writer.commitImport(writer.previewImport(request));
        }
        private Path rootPath() { return layout.snapshot().getParent(); }
        private static ExactRef ref(Path actual) throws IOException {
            byte[] raw = Files.readAllBytes(actual); return new ExactRef(actual.toAbsolutePath().toString(), raw.length, ActionCodec.sha256(raw));
        }
    }
}
