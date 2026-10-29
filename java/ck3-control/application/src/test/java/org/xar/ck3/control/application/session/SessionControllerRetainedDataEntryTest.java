package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.offline.RetainedIncidentBatchSource;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original journal DATA reaches the same Controller queue without entering any Game/batch authority.
 * Synthetic frame identity does not qualify public Root installation, native exit or continuity credit. */
public final class SessionControllerRetainedDataEntryTest {
    @TempDir Path temporary;
    private static final Instant BASE = Instant.parse("2026-10-25T18:00:00Z");
    private static final int NATIVE_DATE = org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.1.1");
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "retained-entry-session");

    @Test void rejectedEntryQueuesActualJournalDataOnceWithoutBatchClockWriterOrObservation() throws IOException {
        Captured actual = capture("rejected-entry");
        var held = new AtomicReference<SessionController>(); var scans = new AtomicInteger(); var enqueues = new AtomicInteger();
        var pending = new CompletableFuture<AnalysisCompletion>();
        RetainedIncidentBatchSource source = () -> {
            scans.incrementAndGet(); assertTrue(held.get().isRunning());
            assertThrows(IllegalArgumentException.class, () -> held.get().enqueueRetainedIncidentData());
            return actual.journal().scan(origin(actual.request())).batch().stream().toList();
        };
        SessionController controller = controller(actual.request().source().sourceRef(), Optional.of(source), work -> {
            assertEquals(actual.batch(), work);
            assertEquals(work, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(work)));
            assertEquals(work.manifestRef(), EpisodeIncidentJournal.measure(Path.of(work.manifestRef().path())));
            enqueues.incrementAndGet(); return new AnalysisTicket(work.batchId(), pending);
        });
        held.set(controller); controller.enqueueRetainedIncidentData();
        assertEquals(1, scans.get()); assertEquals(1, enqueues.get()); assertFalse(pending.isDone());
        assertIdleDataOnly(controller);
        controller.enqueueRetainedIncidentData();
        assertEquals(2, scans.get()); assertEquals(1, enqueues.get()); assertFalse(pending.isDone());
        assertEquals(actual.batch(), actual.journal().scan(origin(actual.request())).batch().orElseThrow());
        assertIdleDataOnly(controller);
    }

    @Test void rejectedQueueRetainsItsOriginalEvenWhenTheNextHistoricalScanFails() throws IOException {
        Captured actual = capture("rejected-retry"); var scans = new AtomicInteger(); var enqueues = new AtomicInteger();
        var scanFailure = new IOException("historical custody unavailable");
        var pending = new CompletableFuture<AnalysisCompletion>();
        RetainedIncidentBatchSource source = () -> {
            if (scans.incrementAndGet() == 1) return List.of(actual.batch());
            throw scanFailure;
        };
        SessionController controller = controller(actual.request().source().sourceRef(), Optional.of(source), work -> {
            assertSame(actual.batch(), work, "the first rejected original must survive without constructing another request");
            if (enqueues.incrementAndGet() == 1) throw new IOException("original queue admission unavailable");
            return new AnalysisTicket(work.batchId(), pending);
        });
        var first = assertThrows(IOException.class, controller::enqueueRetainedIncidentData);
        assertEquals("original queue admission unavailable", first.getMessage()); assertIdleDataOnly(controller);
        var second = assertThrows(IOException.class, controller::enqueueRetainedIncidentData);
        assertSame(scanFailure, second.getCause()); assertEquals(2, enqueues.get()); assertFalse(pending.isDone());
        assertIdleDataOnly(controller);
        assertThrows(IOException.class, controller::enqueueRetainedIncidentData);
        assertEquals(3, scans.get()); assertEquals(2, enqueues.get(), "an accepted original is not queued again after another failed scan");
        assertEquals(actual.batch(), actual.journal().scan(origin(actual.request())).batch().orElseThrow());
        assertIdleDataOnly(controller);
    }

    @Test void rejectedEntryRequiresTheBoundSourceAndRejectsItsOversizedDataBeforeQueueAdmission() throws IOException {
        Captured actual = capture("rejected-bound"); var enqueues = new AtomicInteger();
        SessionController controller = controller(actual.request().source().sourceRef(), Optional.empty(), work -> {
            enqueues.incrementAndGet(); throw new AssertionError("invalid source cannot reach the queue");
        });
        assertThrows(IllegalArgumentException.class, controller::enqueueRetainedIncidentData); assertIdleDataOnly(controller);
        controller.bindRetainedIncidents(() -> java.util.Collections.nCopies(RetainedIncidentBatchSource.MAX_BATCHES + 1, actual.batch()));
        var rejected = assertThrows(IOException.class, controller::enqueueRetainedIncidentData);
        assertInstanceOf(IllegalArgumentException.class, rejected.getCause());
        assertEquals(0, enqueues.get()); assertIdleDataOnly(controller);
        assertThrows(IOException.class, controller::enqueueRetainedIncidentData); assertIdleDataOnly(controller);
    }

    private static void assertIdleDataOnly(SessionController controller) {
        assertFalse(controller.isRunning()); assertFalse(controller.isQuarantined()); assertFalse(controller.isRetired());
        assertTrue(controller.lastReport().isEmpty(), "rejected Root entry must not invent an execution report");
        assertTrue(controller.savedPair().isEmpty());
    }
    private record Captured(PlanningRequest request, EpisodeIncidentJournal journal, BatchRequest batch) { }
    private static EpisodeIncidentJournal.Binding origin(PlanningRequest request) {
        return new EpisodeIncidentJournal.Binding(request.before(), request.source(), request.sessionId());
    }
    /** Existing persisted journal/scan/wire producers; no Native result, Ready, after or review ACK. */
    private Captured capture(String name) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name)); Path original = root.resolve("original-source.json");
        Files.writeString(original, "{\"scope\":\"synthetic-rejected-entry-source-data\"}");
        var source = new G2Source(OWNER.machineId(), BASE.toString(), "SYNTHETIC-REJECTED-ENTRY", EpisodeIncidentJournal.measure(original));
        var before = new ObservationIdentity(OWNER.machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE,
                        BigInteger.valueOf(NATIVE_DATE)), "frame-1", BigInteger.ONE, "episode-1"), 1);
        var snapshot = OpportunityJson.object(OpportunityJson.parse(("{\"paused\":true,\"map_ready\":true,\"revision\":1,\"native_revision\":1,"
                + "\"date_raw\":" + NATIVE_DATE + ",\"snapshot_id\":\"frame-1\",\"episode_run_id\":\"episode-1\","
                + "\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8)), "synthetic source envelope");
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        var request = new PlanningRequest(before, source, OWNER.sessionId(), BASE.plusSeconds(30), observation);
        var configuration = new EpisodeIncidentJournal.Configuration(Files.createDirectory(root.resolve("incidents")),
                Files.createDirectory(root.resolve("scans")), Clock.fixed(BASE, ZoneOffset.UTC), bytes -> {
                    if (bytes < 0 || bytes > 1_048_576) throw new IOException("finite original journal test write bound");
                }, Optional.empty());
        var journal = EpisodeIncidentJournal.initialize(configuration, origin(request));
        var diagnostic = StrictJson.object().put("schema", "xar.unhandled-native-window-diagnostic/v1")
                .put("kind", "unhandled_event").put("current_event_instance_id", 41).putNull("event_definition_key")
                .putNull("selection").putNull("context").put("diagnostic_reason", "synthetic unavailable native source")
                .put("offline_followup_required", true);
        diagnostic.set("origin", ProposalLifecycleCodec.observation(before));
        diagnostic.set("snapshot", StrictJson.parse(DriverJson.encode(snapshot)));
        var plan = StrictJson.object().putNull("selected_step"); plan.set("unhandled_native_window_diagnostic", diagnostic);
        journal.captureBlocked(request, OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)), "original diagnostic"), source.sourceRef());
        BatchRequest batch = journal.scan(origin(request)).batch().orElseThrow();
        assertEquals(batch, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(batch)));
        return new Captured(request, journal, batch);
    }
    /** All non-DATA ports refuse: the public hook may only consume the installed original source and queue. */
    private static SessionController controller(ExactRef source, Optional<RetainedIncidentBatchSource> originalSource,
            OfflineAnalysisPort queue) {
        CheckpointFiles noFiles = new CheckpointFiles() {
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw new AssertionError("no SAVE observation"); }
            @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw new AssertionError("no SAVE read"); }
            @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw new AssertionError("no SAVE write"); }
            @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw new AssertionError("no SAVE creation"); }
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw new AssertionError("no SAVE copy"); }
        };
        DriverCheckpointStore.SnapshotSupplier noSnapshot = new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw new AssertionError("no Driver freeze"); }
        };
        var drivers = new DriverCheckpointStore(noFiles, Path.of("D:/fixture/unused-Driver.json"), "retained-entry-only", noSnapshot);
        CheckpointRequest.ObservationPort noCheckpoint = until -> { throw new AssertionError("no checkpoint readiness"); };
        var saves = new CheckpointService(noFiles, drivers, noCheckpoint, Path.of("D:/fixture/unused-evidence"), Clock.fixed(BASE, ZoneOffset.UTC),
                (pair, receipt) -> { throw new AssertionError("no seed adoption"); });
        var requests = new CheckpointRequestFactory(Path.of("D:/fixture/unused.ck3"), noCheckpoint);
        var planner = new OrdinaryPlanner(List.of(), Clock.fixed(BASE, ZoneOffset.UTC), new RealmLifecycle(source));
        ActionCoordinatorPort noActions = new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) { throw new AssertionError("no action"); }
            @Override public ActionReceipt reconcile(String actionId) { throw new AssertionError("no reconciliation"); }
        };
        OrdinaryPlanCompletion.PlanningScope noPlanning = new OrdinaryPlanCompletion.PlanningScope() {
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) { throw new AssertionError("no planning scope"); }
            @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult result) { throw new AssertionError("no planning"); }
            @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw new AssertionError("no action completion"); }
        };
        BatchJournal noJournal = input -> { throw new AssertionError("no batch/writer transition"); };
        SessionClock noRunClock = new SessionClock() {
            @Override public Tick now() { throw new AssertionError("no execution clock"); }
            @Override public void waitFor(Duration duration) { throw new AssertionError("no Game wait"); }
        };
        var controller = new SessionController(OWNER, (same, until) -> { throw new AssertionError("no lifecycle read"); },
                (same, until) -> { throw new AssertionError("no Ready observation"); }, planner, noActions, saves, requests,
                noJournal, queue, noRunClock, Optional.empty(), 0, noPlanning,
                (same, receipt, until) -> { throw new AssertionError("no episode continuation"); });
        originalSource.ifPresent(controller::bindRetainedIncidents); return controller;
    }
}
