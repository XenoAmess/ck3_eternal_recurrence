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
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
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

/** Actual public Controller retained-DATA/drain consumers; no private Root ticket, Session, Game or job deletion. */
final class OfflineUnacceptedDrain75Test {
    @TempDir Path temporary;
    private static final Instant BASE = Instant.parse("2026-10-25T18:00:00Z");
    private static final int NATIVE_DATE = org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.1.1");
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "retained-entry-session");


    @Test void unacceptedLocalOriginalDrainsAfterCapacityReturnsEvenWithoutAnyDurableRequest() throws Exception {
        Captured original=capture("full-before-durable");Queue port=new Queue(Files.createDirectory(temporary.resolve("queue-one")));
        port.full=true;
        SessionController controller=controller(original.request().source().sourceRef(),Optional.of(source(original)),port);
        assertSame(port.capacityFailure,assertThrows(IOException.class,controller::enqueueRetainedIncidentData));
        assertEquals(1,port.attempts.size());BatchRequest first=port.attempts.getFirst();
        assertEquals(original.batch(),first);assertTrue(port.retainedOriginals().isEmpty());assertTrue(port.workFiles.isEmpty());
        assertIdleDataOnly(controller);
        port.full=false;port.mode=Mode.SUCCESS;
        controller.drainForCleanRestart(BASE.plusSeconds(60));
        assertEquals(2,port.attempts.size());assertSame(first,port.attempts.getLast(),"retry the exact Controller-held immutable object, not a rebuilt request");
        assertEquals(1,port.accepted.size());assertTrue(port.future(first.batchId()).isDone());assertFalse(port.future(first.batchId()).isCompletedExceptionally());
        AnalysisCompletion actual=port.future(first.batchId()).join();assertEquals(first.batchId(),actual.batchId());port.assertMaterial(actual.publishedKnowledge());
        for(ExactRef ref:actual.persistedReviews())port.assertMaterial(ref);
        assertEquals(first,OfflineEventAnalysisWire.decodeBatch(Files.readAllBytes(port.workFiles.get(first.batchId()))));
        controller.drainForCleanRestart(BASE.plusSeconds(60));controller.enqueueRetainedIncidentData();controller.drainForCleanRestart(BASE.plusSeconds(60));
        assertEquals(2,port.attempts.size(),"a completed original and matching durable/local inputs must not enqueue again");
        assertEquals(List.of(first),port.retainedOriginals());assertEquals(first,original.journal().scan(origin(original.request())).batch().orElseThrow());
        assertIdleDataOnly(controller);
    }

    @Test void mergedDuplicateBodiesAreCheckedBeforeAdmissionAndLegacyDurablesStillDrainOnce() throws Exception {
        Captured original=capture("duplicate-local");Captured different=capture("duplicate-other-original");
        BatchRequest conflicting=new BatchRequest(original.batch().batchId(),different.batch().manifestRef(),different.batch().capturedRefs());
        assertNotEquals(original.batch(),conflicting);
        Queue conflict=new Queue(Files.createDirectory(temporary.resolve("queue-conflict")));conflict.full=true;
        SessionController rejected=controller(original.request().source().sourceRef(),Optional.of(source(original)),conflict);
        assertThrows(IOException.class,rejected::enqueueRetainedIncidentData);conflict.publishDurable(conflicting);conflict.full=false;conflict.mode=Mode.SUCCESS;
        int attempted=conflict.attempts.size();
        for(int i=0;i<2;i++) {
            var failure=assertThrows(IllegalArgumentException.class,()->rejected.drainForCleanRestart(BASE.plusSeconds(60)));
            assertEquals("durable offline batch ID changed captured originals",failure.getMessage());
            assertEquals(attempted,conflict.attempts.size(),"validate the entire local+durable union before any new enqueue");
        }
        assertEquals(List.of(conflicting),conflict.retainedOriginals());assertIdleDataOnly(rejected);
        Queue equal=new Queue(Files.createDirectory(temporary.resolve("queue-equal")));equal.full=true;
        SessionController deduplicated=controller(original.request().source().sourceRef(),Optional.of(source(original)),equal);
        assertThrows(IOException.class,deduplicated::enqueueRetainedIncidentData);BatchRequest held=equal.attempts.getFirst();
        equal.publishDurable(new BatchRequest(held.batchId(),held.manifestRef(),held.capturedRefs()));equal.full=false;equal.mode=Mode.SUCCESS;
        deduplicated.drainForCleanRestart(BASE.plusSeconds(60));deduplicated.drainForCleanRestart(BASE.plusSeconds(60));
        assertEquals(2,equal.attempts.size());assertSame(held,equal.attempts.getLast());assertEquals(1,equal.accepted.size());assertIdleDataOnly(deduplicated);
        Queue legacy=new Queue(Files.createDirectory(temporary.resolve("queue-legacy")));legacy.publishDurable(original.batch());legacy.mode=Mode.SUCCESS;
        SessionController restored=controller(original.request().source().sourceRef(),Optional.empty(),legacy);
        restored.drainForCleanRestart(BASE.plusSeconds(60));restored.drainForCleanRestart(BASE.plusSeconds(60));
        assertEquals(List.of(original.batch()),legacy.attempts);assertEquals(1,legacy.accepted.size());assertIdleDataOnly(restored);
    }

    @Test void acceptedFutureFailureTimeoutAndRecordedFailureNeverBecomeCleanByDroppingJobs() throws Exception {
        Captured original=capture("future-and-report");
        Queue failed=new Queue(Files.createDirectory(temporary.resolve("queue-failure")));failed.mode=Mode.FAILURE;
        SessionController blocked=controller(original.request().source().sourceRef(),Optional.of(source(original)),failed);
        blocked.enqueueRetainedIncidentData();int scans=failed.originalScans;
        for(int i=0;i<2;i++) {
            IOException failure=assertThrows(IOException.class,()->blocked.drainForCleanRestart(BASE.plusSeconds(60)));
            assertInstanceOf(ExecutionException.class,failure.getCause());assertSame(failed.futureFailure,failure.getCause().getCause());
        }
        assertEquals(scans,failed.originalScans,"accepted futures are joined before asking the port for durable originals");
        assertEquals(1,failed.attempts.size());assertTrue(Files.exists(failed.workFiles.get(original.batch().batchId())));assertIdleDataOnly(blocked);
        Queue delayed=new Queue(Files.createDirectory(temporary.resolve("queue-timeout")));delayed.mode=Mode.PENDING;
        SessionController waiting=controller(original.request().source().sourceRef(),Optional.of(source(original)),delayed);
        waiting.enqueueRetainedIncidentData();
        var timeout=assertThrows(IOException.class,()->waiting.drainForCleanRestart(BASE.plusMillis(5)));
        assertInstanceOf(TimeoutException.class,timeout.getCause());assertFalse(delayed.future(original.batch().batchId()).isDone());
        assertFalse(delayed.future(original.batch().batchId()).isCancelled());assertEquals(1,delayed.attempts.size());
        delayed.complete(original.batch(),false);waiting.drainForCleanRestart(BASE.plusSeconds(60));waiting.drainForCleanRestart(BASE.plusSeconds(60));
        assertEquals(1,delayed.attempts.size());assertIdleDataOnly(waiting);
        // A malformed earlier producer result is negative DATA. Its immutable failed report must remain a drain guard
        // even after the same real original is subsequently processed successfully and all live futures are gone.
        Queue malformed=new Queue(Files.createDirectory(temporary.resolve("queue-report")));malformed.publishDurable(original.batch());malformed.mode=Mode.WRONG_ID;
        SessionController reported=controller(original.request().source().sourceRef(),Optional.of(List::of),malformed);
        assertThrows(IllegalArgumentException.class,()->reported.drainForCleanRestart(BASE.plusSeconds(60)));
        malformed.mode=Mode.SUCCESS;
        assertThrows(IllegalArgumentException.class,()->reported.drainForCleanRestart(BASE.plusSeconds(60)));
        assertEquals(2,malformed.attempts.size());assertFalse(malformed.future(original.batch().batchId()).isCompletedExceptionally());
        reported.requestStop();
        BatchReport report=reported.runBatch(new BatchLimits("retain-original-analysis-failure",1,Duration.ofSeconds(30),Duration.ofSeconds(1),Duration.ofMillis(1),1));
        assertEquals(BatchReport.Terminal.OPERATOR_STOP,report.terminal());assertTrue(report.failedAnalysisBatchIds().contains(original.batch().batchId()));
        assertTrue(report.pendingAnalysisBatchIds().isEmpty());assertEquals(0,report.committedSavedDays());assertTrue(report.turns().isEmpty());
        int before=malformed.attempts.size();
        var guarded=assertThrows(IllegalArgumentException.class,()->reported.drainForCleanRestart(BASE.plusSeconds(60)));
        assertEquals("clean restart requires the actual offline queue to drain successfully",guarded.getMessage());
        assertEquals(before,malformed.attempts.size());assertSame(report,reported.lastReport().orElseThrow());
        assertTrue(Files.exists(malformed.workFiles.get(original.batch().batchId())));assertFalse(reported.isRunning());
    }

    private static RetainedIncidentBatchSource source(Captured actual){return ()->actual.journal().scan(origin(actual.request())).batch().stream().toList();}
    private enum Mode { PENDING,SUCCESS,WRONG_ID,FAILURE }
    /** Controlled original OfflineAnalysisPort: immutable request publication precedes ACK; output files precede future completion. */
    private static final class Queue implements OfflineAnalysisPort {
        final Path root;boolean full;Mode mode=Mode.PENDING;int originalScans,serial;
        final IOException capacityFailure=new IOException("offline analysis executor is full");
        final IllegalStateException futureFailure=new IllegalStateException("actual controlled offline producer failed");
        final List<BatchRequest> attempts=new ArrayList<>(),accepted=new ArrayList<>();
        final Map<String,BatchRequest> durable=new LinkedHashMap<>();final Map<String,Path> workFiles=new LinkedHashMap<>();
        final Map<String,CompletableFuture<AnalysisCompletion>> futures=new LinkedHashMap<>();
        Queue(Path root){this.root=root;}
        @Override public AnalysisTicket enqueue(BatchRequest work)throws IOException {
            attempts.add(work);if(full)throw capacityFailure;
            publishDurable(work);accepted.add(work);var future=new CompletableFuture<AnalysisCompletion>();futures.put(work.batchId(),future);
            if(mode==Mode.FAILURE)future.completeExceptionally(futureFailure);
            else if(mode==Mode.SUCCESS||mode==Mode.WRONG_ID)complete(work,mode==Mode.WRONG_ID);
            return new AnalysisTicket(work.batchId(),future);
        }
        void publishDurable(BatchRequest work)throws IOException {
            BatchRequest old=durable.get(work.batchId());
            if(old!=null){if(!old.equals(work))throw new IOException("same durable ID changed its original request");return;}
            Path file=root.resolve("request-"+(serial++)+".json");Files.write(file,OfflineEventAnalysisWire.encode(work),java.nio.file.StandardOpenOption.CREATE_NEW);
            assertEquals(work,OfflineEventAnalysisWire.decodeBatch(Files.readAllBytes(file)));durable.put(work.batchId(),work);workFiles.put(work.batchId(),file);
        }
        @Override public List<BatchRequest> retainedOriginals(){originalScans++;return List.copyOf(durable.values());}
        CompletableFuture<AnalysisCompletion> future(String id){return java.util.Objects.requireNonNull(futures.get(id));}
        void complete(BatchRequest work,boolean wrongId)throws IOException {
            var review=StrictJson.object().put("schema","controlled-offline-review/v1").put("batch_id",work.batchId());review.set("original_manifest",work.manifestRef().toJson());
            Path reviewFile=root.resolve("review-"+(serial++)+".json");Files.write(reviewFile,StrictJson.canonical(review),java.nio.file.StandardOpenOption.CREATE_NEW);
            var knowledge=StrictJson.object().put("schema","controlled-offline-knowledge/v1").put("batch_id",work.batchId());knowledge.set("review",EpisodeIncidentJournal.measure(reviewFile).toJson());
            Path knowledgeFile=root.resolve("knowledge-"+(serial++)+".json");Files.write(knowledgeFile,StrictJson.canonical(knowledge),java.nio.file.StandardOpenOption.CREATE_NEW);
            var result=new AnalysisCompletion(wrongId?"different-producer-result":work.batchId(),List.of(EpisodeIncidentJournal.measure(reviewFile)),EpisodeIncidentJournal.measure(knowledgeFile));
            assertMaterial(result.publishedKnowledge());for(ExactRef ref:result.persistedReviews())assertMaterial(ref);
            assertTrue(future(work.batchId()).complete(result));
        }
        void assertMaterial(ExactRef ref)throws IOException {assertEquals(ref,EpisodeIncidentJournal.measure(Path.of(ref.path())));}
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
        BatchJournal noJournal = input -> new JournalCommit(source,0); // Public software metadata acknowledgement for stop-before-Game only; no canonical writer/admission.
        SessionClock noRunClock = new SessionClock() {
            @Override public Tick now() { return new Tick(0,BASE); }
            @Override public void waitFor(Duration duration) { throw new AssertionError("no Game wait"); }
        };
        var controller = new SessionController(OWNER, (same, until) -> { throw new AssertionError("no lifecycle read"); },
                (same, until) -> { throw new AssertionError("no Ready observation"); }, planner, noActions, saves, requests,
                noJournal, queue, noRunClock, Optional.empty(), 0, noPlanning,
                (same, receipt, until) -> { throw new AssertionError("no episode continuation"); });
        originalSource.ifPresent(controller::bindRetainedIncidents); return controller;
    }
}
