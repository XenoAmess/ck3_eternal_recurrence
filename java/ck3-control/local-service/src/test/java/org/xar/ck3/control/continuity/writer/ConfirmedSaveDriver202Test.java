package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;


import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.OriginalWindowReducer;


final class ConfirmedSaveDriver202Test {
    private static final String MACHINE = "archive-test-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> storageScopes = new java.util.LinkedHashSet<>();
    @AfterEach void closeStorageScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : storageScopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }
    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore artifacts;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException { this(root, false); }
        Fixture(Path root, boolean reopen) throws IOException {
            this.root = root;
            if (!reopen) {
                Files.createDirectory(root); byte[] state = ContinuityJson.canonical(state());
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
                Files.writeString(root.resolve("reviewed-source.txt"), "archive fixture source", StandardOpenOption.CREATE_NEW);
            }
            source = LedgerFiles.read(root.resolve("reviewed-source.txt"), 100).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65_536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = reopen ? StorageWriteGuardTestSupport.forLayout(layout) : StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, artifacts.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("archive fixture must never commit a ledger event"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(artifacts, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); var game = row.putObject("game_binding");
            game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static NativeActionPort.AckReceived ack(String requestId, Optional<String> result) throws IOException {
        String body = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + requestId
                + "\",\"ok\":true" + result.map(token -> ",\"result\":" + token).orElse("") + "}";
        byte[] packet = NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
        var actual = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(actual.requestId(), actual.nativeOk(), actual.result().token().map(value -> new RawJson(value.value())), new RawJson(actual.payload().value()), packet);
    }
    private static ProposalLifecycle.ObservationIdentity observation() {
        return new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1000)), "native-1", BigInteger.ONE, "episode-1"), 1);
    }
    private static GuardEvidence guard(Fixture f, OperationKey operation) {
        return new GuardEvidence(observation(), f.source(), "session-1", BigInteger.ONE, operation, f.source, f.source, "authority-1", NOW, NOW.plusSeconds(30));
    }

    private record Drivers202(DriverStateSnapshot.Complete before, DriverStateSnapshot.Complete after) { }
    private record Sample202(Fixture fixture, ContinuityBatchJournal journal, SessionPorts.SessionIdentity owner,
            DriverSnapshotFacts.Known known, ExactRef beforeRef, DriverStateSnapshot.Complete after,
            ExactRef afterRef, CheckpointPair pair, ActionReceipt publisher, ExactRef publisherRef,
            ActionReceipt save, HistoricalTransition savedEdge, HistoricalTransition readEdge) { }

    @Test void realSmallSavedDriverAdvancesKnownOnceAndUsesTheOriginalColdPublisherCoverage() throws Exception {
        Sample202 sample = sample202("positive", false);
        byte[] original = sample.known().driver().encode();
        byte[] ledger = Files.readAllBytes(sample.fixture().layout.snapshot());
        Object result = replay202(sample, sample.readEdge(), sample.save());
        DriverSnapshotFacts.Known actual = facts202(result);
        assertArrayEquals(sample.after().encode(), actual.driver().encode());
        assertEquals(sample.known().stamp().driverVersion() + 1, actual.stamp().driverVersion());
        assertEquals(sample.known().stamp().episodeEpoch(), actual.stamp().episodeEpoch());
        assertEquals(sample.known().stamp().game(), actual.stamp().game());
        assertEquals(sample.known().originalHistoryBasis(), actual.originalHistoryBasis());
        assertEquals(sample.known().loop(), actual.loop());
        assertEquals(sample.afterRef(), fullRef202(result));
        assertNotEquals(sample.pair().driver().reference().path(), sample.afterRef().path());
        assertEquals(sample.pair().driver().reference().sha256(), sample.afterRef().sha256());
        assertEquals(new OpportunityJson.Bool(false), actual.auxiliary().get("rollback_war_failures_migration_required"));
        assertEquals(sample.known().auxiliary().get("keep"), actual.auxiliary().get("keep"));
        assertEquals(sample.known().actionRows().getFirst(), actual.actionRows().getFirst());
        assertEquals(2, actual.actionRows().size());
        var coverage = actual.actionRows().getLast();
        assertEquals(sample.save().command().actionId(), coverage.actionId());
        assertEquals(526, coverage.durableSequence());
        assertNotEquals(sample.save().sequence(), coverage.durableSequence());
        assertEquals(2, coverage.historyIndex());
        assertInstanceOf(DriverStateSnapshot.NullValue.class, actual.driver().rollbackWarFailure());
        assertEquals("[]", new String(((DriverStateSnapshot.Value) actual.driver().rollbackWarFailures()).json(), StandardCharsets.UTF_8));
        assertArrayEquals(original, sample.known().driver().encode());
        assertArrayEquals(ledger, Files.readAllBytes(sample.fixture().layout.snapshot()));
    }

    @Test void savedDriverRejectsWrongExactSourceVersionPrefixAckAndColdBasis() throws Exception {
        Sample202 sample = sample202("negative", false);
        var alias = readDetails202(sample);
        alias.set("before_driver", sample.pair().driver().reference().toJson());
        var wrongRef = changedRead202(sample, alias, "alias");
        assertThrows(IllegalArgumentException.class, () -> replay202(sample, wrongRef, sample.save()));
        var version = readDetails202(sample);
        version.put("before_version", sample.known().stamp().driverVersion() + 2);
        var wrongVersion = changedRead202(sample, version, "version");
        assertThrows(IllegalArgumentException.class, () -> replay202(sample, wrongVersion, sample.save()));

        Sample202 prefix = sample202("prefix", true);
        assertThrows(IllegalArgumentException.class, () -> replay202(prefix, prefix.readEdge(), prefix.save()));

        ActionReceipt wrongAck = sample.fixture().writer.locked(same -> {
            var archive = sample.fixture().archive.withSession(same);
            var oldAttempt = ActionTransitions.attempt(sample.publisher().state()).orElseThrow();
            var rejected = new ActionReceipt(1, 526, sample.publisher().command(), sample.publisher().bodySha256(),
                    new ActionState.AckReceived(oldAttempt, ack202(oldAttempt.requestId(), false)));
            ExactRef rejectedRef = archive.preserveReceipt(rejected);
            return replaceBasis202(sample.save(), new ObservationProvenance.ColdAfterAcknowledgement(rejectedRef));
        });
        assertThrows(IllegalArgumentException.class, () -> replay202(sample, sample.readEdge(), wrongAck));
        ActionReceipt liveBasis = replaceBasis202(sample.save(), new ObservationProvenance.LiveAfterSetter(sample.publisherRef()));
        assertThrows(IllegalArgumentException.class, () -> replay202(sample, sample.readEdge(), liveBasis));
    }

    private Sample202 sample202(String label, boolean changedPrefix) throws IOException {
        Fixture f = fixture(label);
        var owner = new SessionPorts.SessionIdentity(MACHINE, observation().game(), "session-1");
        var files = new NativeCheckpointFiles();
        Path savePath = temp.resolve(label + "-xar_checkpoint.ck3");
        Files.writeString(savePath, "small software SAVE", StandardOpenOption.CREATE_NEW);
        CheckpointPair.FileWitness saveFile = files.observe(savePath).orElseThrow();
        var checkpoint = StrictJson.object();
        checkpoint.put("status", "saved"); checkpoint.put("name", "xar_checkpoint.ck3");
        checkpoint.put("strategy", "native-autosave-command-v1"); checkpoint.put("java_action_id", "save-202");
        checkpoint.put("save_lineage_id", "lineage-202"); checkpoint.put("path", saveFile.reference().path());
        checkpoint.put("sha256", saveFile.reference().sha256()); checkpoint.put("size", saveFile.reference().bytes());
        checkpoint.put("history_index", 2); checkpoint.put("date_raw", observation().frame().identity().dateRaw());
        checkpoint.put("episode_character_id", observation().frame().identity().player());
        checkpoint.put("episode_run_id", observation().frame().episodeRunId());
        checkpoint.set("java_game_generation", owner.game().toJson()); checkpoint.putNull("succession_lifecycle");
        Drivers202 drivers = drivers202(new DriverStateSnapshot.Session("software-driver-pipe", owner.game().pid(),
                observation().frame().identity().player(), observation().frame().episodeRunId()), checkpoint);
        var after = drivers.after();
        if (changedPrefix) {
            var rows = new java.util.ArrayList<>(after.commandHistory());
            rows.set(0, new DriverStateSnapshot.HistoryEntry(1, new DriverStateSnapshot.Value(bytes202("{\"index\":1,\"command\":\"changed-prefix\",\"ok\":true}"))));
            after = new DriverStateSnapshot.Complete(after.session(), rows, after.lastCheckpoint(), after.rollbackWarFailure(),
                    after.managedRestoreTransaction(), after.successionExpectation(), after.successionLifecycle(), after.campaignGoal(), after.rollbackWarFailures());
        }
        var afterDriver = after;
        Path physicalDriver = temp.resolve(label + "-physical-driver.json");
        Files.write(physicalDriver, after.encode(), StandardOpenOption.CREATE_NEW);
        var driverFile = files.observe(physicalDriver).orElseThrow();
        var transitions = new OrdinaryCycleTransitions(f.archive, (a,b,c) -> { throw new AssertionError("no semantic authority"); },
                (a,b,c,d) -> { throw new AssertionError("no checkpoint authority"); }, new OriginalWindowReducer.Policy(10958), f.writer::requireSession);
        var journal = new ContinuityBatchJournal(f.writer, transitions);
        return f.writer.locked(same -> {
            var archive = f.archive.withSession(same);
            ExactRef beforeRef = archive.preserveMaterial(RawJson.fullMaterial(drivers.before().encode()));
            ExactRef afterRef = archive.preserveMaterial(RawJson.fullMaterial(afterDriver.encode()));
            ExactRef oldRow = archive.preserveMaterial(new RawJson(drivers.before().commandHistory().getFirst().originalRow().json()));
            archive.preserveMaterial(new RawJson(afterDriver.commandHistory().getLast().originalRow().json()));
            var auxiliary = new OpportunityJson.Obj(Map.of("rollback_war_failures_migration_required", new OpportunityJson.Bool(true),
                    "keep", new OpportunityJson.Text("original-auxiliary")));
            var known = new DriverSnapshotFacts.Known(drivers.before(),
                    new DriverSnapshotFacts.Stamp(7, 2, owner.game(), observation().frame().episodeRunId(), beforeRef.sha256()), beforeRef,
                    List.of(new DriverSnapshotFacts.ActionRow("old-action", "a".repeat(64), 100, 1, oldRow)), auxiliary,
                    Optional.of(new DriverSnapshotFacts.LoopWitness("old-batch", 1, 2, true, 1, false, beforeRef)), Optional.empty());
            var operation = new OperationKey("save-checkpoint");
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), f.source(), CheckpointRequestFactory.OBSERVER_SCHEMA,
                    List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("date_raw"), observation().frame().identity().dateRaw()),
                            new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("played_character_id"), observation().frame().identity().player()),
                            new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("checkpoint_pair_verified"), true)));
            var command = new ActionCommand("save-202", observation(), f.source(), owner.sessionId(), operation,
                    new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
            var attempt = new ActionState.Attempt("save-request-202", NOW.plusSeconds(1), guard(f, operation),
                    new NativeRequest("save-checkpoint", Optional.empty(), raw("{}")));
            var ack = ack202(attempt.requestId(), true);
            var publisher = new ActionReceipt(1, 526, command, ActionCodec.bodySha256(command), new ActionState.AckReceived(attempt, ack));
            ExactRef publisherRef = archive.preserveReceipt(publisher);
            ActionReceipt decodedPublisher = archive.loadReceipt(publisherRef);
            var originalAck = decodedPublisher.ack().orElseThrow();
            var pair = new CheckpointPair(saveFile, driverFile, observation(), "lineage-202", 2, command.actionId(),
                    archive.referenceOf(originalAck), NOW.plusSeconds(2));
            var readAckRef = archive.preserve(ack202("fresh-read-202", true));
            var provenance = new ObservationProvenance.FreshSnapshotQuery("fresh-read-202", readAckRef,
                    new NativeRequestChronology.Event(BigInteger.TEN, NOW.plusSeconds(2)), new ObservationProvenance.ColdAfterAcknowledgement(publisherRef));
            var observed = new ActionState.EffectObservation(observation(), f.source(), owner.sessionId(), expected.observerSchema(), expected.values(),
                    provenance, NOW.plusSeconds(2), f.source, List.of(f.source, afterRef));
            var save = new ActionReceipt(1, 527, command, publisher.bodySha256(), new ActionState.Settled(attempt, originalAck, new ActionState.Applied(observed)));
            ObjectNode base = Fixture.state(); base.put("sequence", 527); base.put("last_event_identity", "b".repeat(64));
            var before = ContinuityState.fromJson(base, MACHINE);
            var saveDetails = StrictJson.object(); saveDetails.set("pair", ContinuityJson.parseObject(CheckpointPairCodec.encode(pair), ContinuityJson.DOMAIN_MAX_BYTES));
            var saved = edge202(label + "-saved", before, OrdinaryCycleTransitions.BATCH_KIND, saveDetails, false);
            var readDetails = StrictJson.object(); readDetails.put("before_version", 8); readDetails.put("episode_epoch", 2);
            readDetails.set("before_driver", afterRef.toJson());
            var read = edge202(label + "-read", saved.after(), WriterContracts.DRIVER_READ_HISTORY_KIND, readDetails, true);
            return new Sample202(f, journal, owner, known, beforeRef, afterDriver, afterRef, pair, decodedPublisher, publisherRef, save, saved, read);
        });
    }

    private Drivers202 drivers202(DriverStateSnapshot.Session session, ObjectNode checkpoint) {
        var first = new DriverStateSnapshot.HistoryEntry(1, new DriverStateSnapshot.Value(bytes202("{\"index\":1,\"command\":\"old-step\",\"ok\":true}")));
        var nil = new DriverStateSnapshot.NullValue();
        var before = new DriverStateSnapshot.Complete(session, List.of(first), nil,
                new DriverStateSnapshot.Value(bytes202("{\"legacy\":\"failure\"}")), nil, nil, nil, nil,
                new DriverStateSnapshot.Value(bytes202("[{\"legacy\":\"failure\"}]")));
        var row = StrictJson.object(); row.put("index", 2); row.put("command", "save-checkpoint"); row.put("ok", true);
        row.putObject("result").set("checkpoint", checkpoint);
        var last = new DriverStateSnapshot.HistoryEntry(2, new DriverStateSnapshot.Value(ContinuityJson.canonical(row)));
        var after = new DriverStateSnapshot.Complete(session, List.of(first, last), new DriverStateSnapshot.Value(ContinuityJson.canonical(checkpoint)),
                nil, nil, nil, nil, nil, new DriverStateSnapshot.Value(bytes202("[]")));
        return new Drivers202(before, after);
    }

    private HistoricalTransition edge202(String name, ContinuityState before, String kind, ObjectNode details, boolean read) throws IOException {
        var event = StrictJson.object(); event.put("sequence", before.sequence() + 1); event.put("kind", kind); event.set("details", details);
        byte[] bytes = ContinuityJson.canonical(event); Path path = temp.resolve(name + ".json");
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
        var after = before.toJson(); after.put("sequence", before.sequence() + 1); after.put("last_event_identity", ActionCodec.sha256(bytes));
        if (read) after.set(WriterContracts.DRIVER_READ_HISTORY_FIELD, details);
        return new HistoricalTransition(before.sequence() + 1, kind, ContinuityJson.canonical(details), ActionCodec.sha256(bytes), before,
                ContinuityState.fromJson(after, MACHINE), LedgerFiles.read(path, 65_536).pin());
    }

    private HistoricalTransition changedRead202(Sample202 sample, ObjectNode details, String suffix) throws IOException {
        return edge202("changed-" + suffix, sample.savedEdge().after(), WriterContracts.DRIVER_READ_HISTORY_KIND, details, true);
    }
    private static ObjectNode readDetails202(Sample202 sample) {
        return ContinuityJson.parseObject(sample.readEdge().details(), ContinuityJson.LEDGER_MAX_BYTES);
    }
    private static NativeActionPort.AckReceived ack202(String id, boolean ok) throws IOException {
        byte[] packet = NativeWire.packet(bytes202("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":" + ok + ",\"result\":{}}"));
        var decoded = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(decoded.requestId(), decoded.nativeOk(), decoded.result().token().map(value -> new RawJson(value.value())),
                new RawJson(decoded.payload().value()), packet);
    }
    private static ActionReceipt replaceBasis202(ActionReceipt original, ObservationProvenance.FreshSnapshotBasis basis) {
        var observed = original.applied().orElseThrow().observation();
        var previous = (ObservationProvenance.FreshSnapshotQuery) observed.provenance();
        var proof = new ObservationProvenance.FreshSnapshotQuery(previous.requestId(), previous.readAcknowledgement(), previous.snapshotReceived(), basis);
        var replacement = new ActionState.EffectObservation(observed.after(), observed.source(), observed.sessionId(), observed.observerSchema(),
                observed.actual(), proof, observed.observedAt(), observed.originalEvidence(), observed.supportingEvidence());
        return new ActionReceipt(1, original.sequence(), original.command(), original.bodySha256(), new ActionState.Settled(
                ActionTransitions.attempt(original.state()).orElseThrow(), original.ack().orElseThrow(), new ActionState.Applied(replacement)));
    }
    private static Class<?> retainedClass202() {
        try { return Class.forName("org.xar.ck3.control.application.session.ContinuityBatchJournal$RetainedReadDriver"); }
        catch (ClassNotFoundException failure) { throw new AssertionError(failure); }
    }
    private Object replay202(Sample202 sample, HistoricalTransition read, ActionReceipt save) throws IOException {
        return sample.fixture().writer.locked(same -> {
            try {
                var type = retainedClass202();
                var constructor = type.getDeclaredConstructor(DriverSnapshotFacts.Known.class, ExactRef.class); constructor.setAccessible(true);
                var previous = constructor.newInstance(sample.known(), sample.beforeRef());
                var method = ContinuityBatchJournal.class.getDeclaredMethod("retainConfirmedSaveDriver", SessionPorts.SessionIdentity.class,
                        HistoricalTransition.class, HistoricalTransition.class, type, CheckpointPair.class, ActionReceipt.class, ActionPorts.OutcomeArchive.class);
                method.setAccessible(true);
                return method.invoke(sample.journal(), sample.owner(), sample.savedEdge(), read, previous, sample.pair(), save,
                        sample.fixture().archive.withSession(same));
            } catch (java.lang.reflect.InvocationTargetException failure) {
                if (failure.getCause() instanceof IOException io) throw io;
                if (failure.getCause() instanceof RuntimeException runtime) throw runtime;
                if (failure.getCause() instanceof Error error) throw error;
                throw new AssertionError(failure.getCause());
            } catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
        });
    }
    private static DriverSnapshotFacts.Known facts202(Object value) {
        return (DriverSnapshotFacts.Known) component202(value, "facts");
    }
    private static ExactRef fullRef202(Object value) { return (ExactRef) component202(value, "fullDriver"); }
    private static Object component202(Object value, String name) {
        try { var method = value.getClass().getDeclaredMethod(name); method.setAccessible(true); return method.invoke(value); }
        catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
    }
    private static byte[] bytes202(String value) { return value.getBytes(StandardCharsets.UTF_8); }

}
