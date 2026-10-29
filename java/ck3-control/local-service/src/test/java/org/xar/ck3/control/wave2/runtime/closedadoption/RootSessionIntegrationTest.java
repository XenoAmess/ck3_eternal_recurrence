package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Main's actual approval loop and actual original processes; SDK authority alone is explicitly synthetic. */
class RootSessionIntegrationTest {
    private static final String TICKET_NONCE = "1".repeat(32);
    private enum Fault { NONE, LOCKED_PREDECESSOR_DRIFT, BASIS_AFTER_COMMIT, COMMITTED_RESPONSE_LOST }

    /** Never serialized or inserted into the real SavedCheckpointMeasurementCoordinator. */
    private static final class SyntheticSdkMeasurement {
        private final ClosedAdoptionMaterial material;
        private final AtomicInteger measurements = new AtomicInteger();
        private final AtomicInteger currentReads = new AtomicInteger();
        private boolean measured;
        private SyntheticSdkMeasurement(ClosedAdoptionMaterial material) { this.material = material; }
        private synchronized void measureOnce() {
            assertFalse(measured,"synthetic SDK seam is measured only once in the owning JVM");
            measured = true; measurements.incrementAndGet();
        }
        private synchronized ClosedAdoptionMaterial requireCurrent() {
            assertTrue(measured,"a missing synthetic measurement cannot become cached authority");
            currentReads.incrementAndGet(); return material;
        }
    }

    private static final class Stages implements ClosedAdoptionMain.RetainedStages {
        private final ClosedAdoptionTransactionTest.Fixture fixture;
        private final SyntheticSdkMeasurement measured;
        private final ClosedAdoptionRequest request;
        private final WindowsFileWriterSession.Settings settings;
        private final ClosedAdoptionMaterial.CurrentSource current;
        private final Path basisPath, qualificationPath;
        private final AtomicInteger productionRuns = new AtomicInteger();
        private final AtomicInteger followups = new AtomicInteger();
        private final AtomicReference<OriginalWriterTransaction.Committed> actualProductionCommit = new AtomicReference<>();
        private Instant reviewDeadline;
        private Fault fault = Fault.NONE;
        private Stages(ClosedAdoptionTransactionTest.Fixture fixture, SyntheticSdkMeasurement measured,
                WindowsFileWriterSession.Settings settings) {
            this.fixture = fixture; this.measured = measured; this.settings = settings;
            this.request = RootSessionIntegrationTest.request(fixture); this.current = measured::requireCurrent;
            basisPath = fixture.root().resolve("production-basis.json");
            qualificationPath = fixture.root().resolve("production-qualification.json");
        }
        @Override public ClosedAdoptionRequest request() { return request; }
        @Override public ClosedAdoptionMaterial.CurrentSource currentSource() { return current; }
        @Override public void requireCurrentMeasurement() { measured.requireCurrent(); }
        @Override public void preflightProductionPublications() {
            StrictJson.require(!Files.exists(basisPath) && !Files.exists(qualificationPath),
                    "fixture production publications are create-only and distinct from temporary publications");
        }
        @Override public ClosedAdoptionApplication.Completed runProduction(OriginalWriterTransaction.Target target,
                ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionApplication.CommitObserver observer)
                throws IOException, InterruptedException {
            productionRuns.incrementAndGet(); preflightProductionPublications();
            Instant originalDeadline = settings.leaseDeadline();
            var productionSettings = ClosedAdoptionMain.withinLease(settings,reviewDeadline);
            assertEquals(reviewDeadline,productionSettings.leaseDeadline());
            assertEquals(originalDeadline,settings.leaseDeadline(),"clamping production must preserve the original settings");
            assertThrows(ContractViolationException.class,() ->
                    ClosedAdoptionMain.withinLease(settings,originalDeadline.plusNanos(1)));
            AtomicInteger writerCurrentCalls = new AtomicInteger();
            ClosedAdoptionMaterial.CurrentSource guarded = () -> {
                if (fault == Fault.LOCKED_PREDECESSOR_DRIFT && writerCurrentCalls.incrementAndGet() == 2) {
                    try {
                        FileTime original = Files.getLastModifiedTime(target.canonicalPath());
                        Files.setLastModifiedTime(target.canonicalPath(),FileTime.from(original.toInstant().plusSeconds(2)));
                    } catch (IOException error) { throw new UncheckedIOException(error); }
                }
                return lockedCurrent.current();
            };
            return ClosedAdoptionApplication.runOriginal(target,guarded,current,fixture::canonical,
                    raw -> {
                        if (fault == Fault.BASIS_AFTER_COMMIT) { throw new IOException("synthetic post-commit basis publication refusal"); }
                        return publish(basisPath,raw);
                    }, raw -> publish(qualificationPath,raw),productionSettings,value -> {
                        actualProductionCommit.set(value);
                        if (fault == Fault.COMMITTED_RESPONSE_LOST) {
                            throw new IOException("synthetic committed writer response lost before Root observation");
                        }
                        observer.committed(value);
                    });
        }
        @Override public RecoveryEvidence serveFollowup(ClosedAdoptionApplication.Completed completed,
                Path sessionDirectory, Instant deadline) throws IOException {
            followups.incrementAndGet();
            assertTrue(Instant.now().isBefore(deadline)); assertSame(actualProductionCommit.get(),completed.writer());
            // This test covers the actual one-shot original cold consumer above, not a formal persistent followup.
            Files.createDirectory(sessionDirectory); ObjectNode row = StrictJson.object();
            row.put("schema","xar.synthetic-no-root-followup-test-receipt/v1");
            row.put("machine_id",ClosedAdoptionTransactionTest.MACHINE); row.put("observed_at_utc",Instant.now().toString());
            row.put("synthetic_sdk_authority",true); row.put("formal_qualified",false);
            row.put("persistent_root_consumer_tested",false); row.put("grants_new_warm_attachment",false);
            return publish(sessionDirectory.resolve("synthetic-no-followup.json"),StrictJson.canonical(row));
        }
    }

    private record Harness(ClosedAdoptionTransactionTest.Fixture fixture, OriginalWriterTransaction.Target production,
            SyntheticSdkMeasurement measured, Stages stages, ClosedAdoptionApplication.Completed temporary,
            ClosedAdoptionMain.RetainedReviewContext context, ClosedAdoptionReview.Plan plan, ExactRef planRef) { }

    private static ClosedAdoptionRequest request(ClosedAdoptionTransactionTest.Fixture fixture) {
        var material = fixture.material(); var input = material.input(); var closed = material.sources(); var business = material.business();
        var inputs = new ClosedAdoptionRequest.InputRefs(input.predecessor().reference(),input.savedBasis().reference(),
                input.priorQualification().reference(),input.fullRequest().reference(),input.failedFull().reference(),
                input.autoRequest().reference(),input.failedAuto().reference(),input.rawState().reference(),
                input.rawGovernance().reference(),input.actualNext().reference());
        var closures = new ClosedAdoptionRequest.ClosedRefs(closed.sdkClosed().reference(),closed.gameExit().reference(),
                closed.supervisorClosed().reference(),closed.recordingClosed().reference(),closed.captureClosed().reference(),closed.screenReleased().reference());
        List<ClosedAdoptionRequest.TaskRefs> tasks = closed.tasks().stream().map(task -> new ClosedAdoptionRequest.TaskRefs(
                task.role(),task.spec().reference(),task.closed().reference(),task.unregistered().reference())).toList();
        List<ClosedAdoptionRequest.CycleRefs> cycles = new ArrayList<>();
        for (int index = 0; index < closed.settledCycles().size(); index++) {
            var rpc = closed.settledCycles().get(index); var metadata = business.cycles().get(index);
            cycles.add(new ClosedAdoptionRequest.CycleRefs(rpc.auto().reference(),rpc.metrics().reference(),metadata.event().reference(),
                    metadata.ordinaryCredit().reference(),metadata.autoAfter().reference(),metadata.metricsAfter().reference(),
                    metadata.beforePlan().reference(),metadata.readonlySaveSkip().map(RecoveryEvidence::reference)));
        }
        var businessRefs = new ClosedAdoptionRequest.BusinessRefs(business.savedSeed().reference(),business.savedGovernance().reference(),
                business.coldBound().reference(),business.openingSemantic().reference(),business.openingCapabilities().reference(),
                business.classifierPin().reference(),business.classifierSource(),business.queueSource(),business.captureProbe().reference(),business.captureCleanup().reference());
        return new ClosedAdoptionRequest(input.machineId(),input.observedAtUtc(),inputs,closures,tasks,cycles,businessRefs,
                fixture.target().canonicalPath(),fixture.root(),fixture.target().originalWriter());
    }
    private static RecoveryEvidence publish(Path path, byte[] raw) throws IOException {
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        return new RecoveryEvidence(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
    }
    private static RecoveryEvidence small(Path path, String schema) throws IOException {
        ObjectNode row = StrictJson.object(); row.put("schema",schema); row.put("synthetic_sdk_authority",true);
        return publish(path,StrictJson.canonical(row));
    }
    private static Harness prepare(Duration reviewWindow) throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var production = ClosedAdoptionTransactionTest.productionFixture(fixture);
        var measured = new SyntheticSdkMeasurement(fixture.material()); measured.measureOnce();
        var settings = ClosedAdoptionTransactionTest.settings(fixture); var stages = new Stages(fixture,measured,settings);
        var temporary = ClosedAdoptionApplication.runOriginal(fixture.target(),stages.currentSource(),stages.currentSource(),fixture::canonical,
                raw -> publish(fixture.root().resolve("temporary-basis.json"),raw),
                raw -> publish(fixture.root().resolve("temporary-qualification.json"),raw),settings,value -> { });
        var invocationRef = small(fixture.root().resolve("synthetic-invocation.json"),"synthetic-invocation-test-only/v1").reference();
        var requestRef = small(fixture.root().resolve("synthetic-request-marker.json"),"synthetic-typed-request-is-held-in-JVM/v1").reference();
        var ticketRef = small(fixture.root().resolve("synthetic-ticket.json"),"synthetic-ticket-NOT-ACTUAL-SDK/v1").reference();
        var invocation = new ClosedAdoptionMain.Invocation(ClosedAdoptionTransactionTest.MACHINE,requestRef,ticketRef,
                settings.repo(),settings.python(),fixture.root(),settings.memoryLimitBytes(),settings.timeout(),settings.leaseDeadline(),
                1_048_576,16L*1024*1024,settings.mechanicalSource(),settings.coldOwnerSource());
        // Use Main's actual result producer; this canonical ref still names the fixture's explicit NOT-ACTUAL-SDK proof.
        ObjectNode result = ClosedAdoptionMain.temporaryResult(invocationRef,invocation,fixture.canonical().reference(),temporary);
        var temporaryResult = publish(fixture.root().resolve("closed-adoption-result.json"),StrictJson.canonical(result));
        var identities = new WindowsSavedProofIdentityReader(); Instant deadline = Instant.now().plus(reviewWindow);
        assertTrue(deadline.isBefore(settings.leaseDeadline()),"review remains within the original finite process lease");
        byte[] predecessor = fixture.material().input().predecessor().bytes();
        ExactRef productionPredecessor = new ExactRef(production.canonicalPath().toString(),predecessor.length,RecoveryEvidence.sha256(predecessor));
        var plan = new ClosedAdoptionReview.Plan(ClosedAdoptionTransactionTest.MACHINE,ticketRef,TICKET_NONCE,
                production,productionPredecessor,identities.stat(production.canonicalPath()),deadline);
        stages.reviewDeadline = deadline;
        ExactRef planRef = publish(fixture.root().resolve("review-plan.json"),StrictJson.canonical(plan.toJson())).reference();
        var context = new ClosedAdoptionMain.RetainedReviewContext(invocationRef,invocation,TICKET_NONCE,settings.leaseDeadline(),
                temporaryResult,identities.stat(Path.of(temporaryResult.reference().path())),stages);
        return new Harness(fixture,production,measured,stages,temporary,context,plan,planRef);
    }
    private static Future<RecoveryEvidence> start(ExecutorService owner, Harness harness) {
        return owner.submit(() -> ClosedAdoptionMain.runRootContinuation(harness.context(),harness.planRef(),harness.plan()));
    }
    private static ClosedAdoptionReview.Challenge awaitChallenge(Harness harness, Future<RecoveryEvidence> running) throws Exception {
        Path path = harness.fixture().root().resolve("root-review-challenge.json"); long limit = System.nanoTime()+TimeUnit.SECONDS.toNanos(10);
        while (System.nanoTime() < limit) {
            if (Files.exists(path)) {
                try { return ClosedAdoptionReview.Challenge.decode(Files.readAllBytes(path)); }
                catch (ContractViolationException partialPublication) { /* Wait for the same bounded create-only publication to finish. */ }
            }
            if (running.isDone()) { running.get(); fail("Root continuation ended before publishing its review challenge"); }
            Thread.sleep(10);
        }
        fail("Root did not publish the finite review challenge"); throw new AssertionError("unreachable");
    }
    private static void decide(Harness harness, ClosedAdoptionReview.Challenge challenge, ClosedAdoptionReview.Decision decision) throws IOException {
        publishApproval(harness,new ClosedAdoptionReview.Approval(challenge,decision,Instant.now()));
    }
    private static RecoveryEvidence publishApproval(Harness harness, ClosedAdoptionReview.Approval approval) throws IOException {
        byte[] raw = StrictJson.canonical(approval.toJson());
        Path pending = harness.fixture().root().resolve("root-review-approval.pending.json");
        Files.write(pending,raw,StandardOpenOption.CREATE_NEW);
        Path destination = ClosedAdoptionReview.approvalPath(harness.fixture().root());
        Files.move(pending,destination,StandardCopyOption.ATOMIC_MOVE);
        byte[] actual = Files.readAllBytes(destination); assertArrayEquals(raw,actual,"Root receives the actual complete approval bytes");
        return new RecoveryEvidence(new ExactRef(destination.toString(),actual.length,RecoveryEvidence.sha256(actual)),actual);
    }
    private static JsonNode terminal(Harness harness) throws IOException {
        return StrictJson.parse(Files.readAllBytes(harness.fixture().root().resolve("root-two-stage-result.json")));
    }
    private static long sequence(Path canonical) throws IOException {
        return StrictJson.parse(Files.readAllBytes(canonical)).get("sequence").longValue();
    }
    private static long requestFiles(Harness harness, String mode) throws IOException {
        try (var files = Files.list(harness.fixture().root())) {
            return files.filter(path -> path.getFileName().toString().startsWith("closed-partial-"+mode+"-")
                    && path.getFileName().toString().endsWith(".request.jsonl")).count();
        }
    }
    private static void assertCreditsAndNoRetry(JsonNode result) {
        assertFalse(result.get("automatic_retry_authorized").booleanValue());
        assertFalse(result.get("raw_pending_modified").booleanValue()); assertFalse(result.get("original_actions_replayed").booleanValue());
        assertEquals(0,result.get("new_game_day_credit").longValue()); assertEquals(0,result.get("new_ordinary_cycle_credit").longValue());
        assertFalse(result.get("grants_new_warm_attachment").booleanValue());
    }
    private static void assertNotRetried(Harness harness) throws Exception {
        int runs = harness.stages().productionRuns.get(); long writers = requestFiles(harness,"writer");
        Exception rejected = assertThrows(Exception.class, () ->
                ClosedAdoptionMain.runRootContinuation(harness.context(),harness.planRef(),harness.plan()));
        assertTrue(rejected instanceof IOException || rejected instanceof ContractViolationException);
        assertEquals(runs,harness.stages().productionRuns.get()); assertEquals(writers,requestFiles(harness,"writer"));
        assertEquals(1,harness.measured().measurements.get());
    }

    @Test void delayedActualApprovalFileContinuesTheRetainedAuthorityThroughRealWriterAndColdConsumer() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(25)); int cachedReadsBefore = harness.measured().currentReads.get();
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            assertEquals(harness.context().result().reference(),challenge.temporaryResultRef());
            JsonNode temporaryResult = StrictJson.parse(harness.context().result().bytes());
            assertEquals("xar.closed-partial-temporary-transaction-result/v1",temporaryResult.get("schema").textValue());
            assertEquals(harness.fixture().canonical().reference(),ExactRef.fromJson(temporaryResult.get("canonical_checkpoint_proof")));
            assertEquals(2,temporaryResult.get("actual_original_processes").size());
            assertEquals(11559,temporaryResult.get("original_cold_consumer_result").get("next_sequence").longValue());
            assertEquals(StrictJson.parse(harness.temporary().consumer().originalConsumerReceipt()),
                    temporaryResult.get("original_cold_consumer_result"),"Main publishes the complete actual original consumer result");
            assertEquals(241,sequence(harness.fixture().target().canonicalPath())); assertEquals(240,sequence(harness.production().canonicalPath()));
            Thread.sleep(300); assertFalse(running.isDone()); assertEquals(0,harness.stages().productionRuns.get());
            decide(harness,challenge,ClosedAdoptionReview.Decision.APPROVE);
            JsonNode result = StrictJson.parse(running.get(30,TimeUnit.SECONDS).bytes());
            assertEquals("PRODUCTION_CLOSED_INPUTS_VERIFIED",result.get("status").textValue());
            assertTrue(result.get("production_cold_inputs_verified").booleanValue()); assertTrue(result.get("production_canonical_written").booleanValue());
            assertEquals(1,harness.measured().measurements.get()); assertTrue(harness.measured().currentReads.get()>cachedReadsBefore);
            assertEquals(1,harness.stages().productionRuns.get()); assertEquals(1,harness.stages().followups.get());
            assertEquals(241,sequence(harness.production().canonicalPath())); assertEquals(2,requestFiles(harness,"writer"));
            assertEquals(2,requestFiles(harness,"cold_consumer"));
            assertEquals(2,result.get("actual_production_processes").size());
            for (JsonNode job : result.get("actual_production_processes")) {
                assertEquals(0,job.get("exit_code").intValue()); assertEquals(0,job.get("active_processes").intValue());
            }
            JsonNode originalCold = result.get("original_cold_consumer_result");
            assertEquals(11559,originalCold.get("next_sequence").longValue());
            assertTrue(java.util.stream.StreamSupport.stream(originalCold.get("unknown_requests").spliterator(),false)
                    .anyMatch(row -> row.get("sequence").longValue()==11558 && !row.get("replayed").booleanValue()));
            Path followup = Path.of(result.get("root_consumer_session_receipt_ref").get("path").textValue());
            JsonNode syntheticFollowup = StrictJson.parse(Files.readAllBytes(followup));
            assertFalse(syntheticFollowup.get("formal_qualified").booleanValue());
            assertFalse(syntheticFollowup.get("persistent_root_consumer_tested").booleanValue());
            JsonNode basis = StrictJson.parse(Files.readAllBytes(harness.stages().basisPath));
            assertEquals(harness.production().canonicalPath().toString(),basis.get("refs").get("ledger").get("path").textValue());
            JsonNode qualification = StrictJson.parse(Files.readAllBytes(harness.stages().qualificationPath));
            assertEquals(harness.production().canonicalPath().toString(),qualification.get("committed_head_ref").get("path").textValue());
            assertNotEquals(harness.temporary().basis().reference(),ExactRef.fromJson(result.get("production_basis_ref")));
            assertNotEquals(harness.temporary().qualification().reference(),ExactRef.fromJson(result.get("production_qualification_ref")));
            assertEquals(harness.fixture().target().canonicalPath().toString(),StrictJson.parse(harness.temporary().basis().bytes())
                    .get("refs").get("ledger").get("path").textValue());
            assertTrue(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json")));
            assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
    @Test void declineFileIsConsumedWithoutLaunchingAnyProductionProcess() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20));
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            decide(harness,challenge,ClosedAdoptionReview.Decision.DECLINE);
            JsonNode result = StrictJson.parse(running.get(10,TimeUnit.SECONDS).bytes());
            assertEquals("DECLINED_NO_PRODUCTION_WRITER",result.get("status").textValue());
            assertEquals(0,harness.stages().productionRuns.get()); assertEquals(240,sequence(harness.production().canonicalPath()));
            assertEquals(1,requestFiles(harness,"writer")); assertEquals(1,requestFiles(harness,"cold_consumer"));
            assertFalse(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json")));
            assertEquals(1,harness.measured().measurements.get()); assertCreditsAndNoRetry(result);
        }
    }
    @Test void absentApprovalExpiresWithoutRenewingTheTicketOrStartingProduction() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(2));
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); awaitChallenge(harness,running);
            JsonNode result = StrictJson.parse(running.get(10,TimeUnit.SECONDS).bytes());
            assertEquals("EXPIRED_NO_PRODUCTION_WRITER",result.get("status").textValue());
            assertEquals(0,harness.stages().productionRuns.get()); assertEquals(240,sequence(harness.production().canonicalPath()));
            assertEquals(1,harness.measured().measurements.get()); assertEquals(1,requestFiles(harness,"writer"));
            assertFalse(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json"))); assertCreditsAndNoRetry(result);
        }
    }
    @Test void wrongTemporaryResultBindingInActualApprovalOrDeclineFileNeverStartsProduction() throws Exception {
        for (var decision : ClosedAdoptionReview.Decision.values()) {
            Harness harness = prepare(Duration.ofSeconds(20));
            try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
                Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
                ExactRef reviewed = challenge.temporaryResultRef();
                String changedHash = reviewed.sha256().equals("f".repeat(64)) ? "e".repeat(64) : "f".repeat(64);
                var wrong = new ClosedAdoptionReview.Challenge(challenge.plan(),
                        new ExactRef(reviewed.path(),reviewed.bytes(),changedHash),challenge.nonce(),challenge.issuedAtUtc());
                RecoveryEvidence approval = publishApproval(harness,new ClosedAdoptionReview.Approval(wrong,decision,Instant.now()));
                ExecutionException rejected = assertThrows(ExecutionException.class,() -> running.get(10,TimeUnit.SECONDS));
                assertInstanceOf(ContractViolationException.class,rejected.getCause());
                assertTrue(rejected.getCause().getMessage().contains("complete issued challenge"));
                JsonNode result = terminal(harness);
                assertEquals("REJECTED_OR_UNAVAILABLE_NO_PRODUCTION_WRITER",result.get("status").textValue());
                assertEquals(approval.reference(),ExactRef.fromJson(result.get("root_approval_ref")));
                assertEquals(0,harness.stages().productionRuns.get()); assertEquals(240,sequence(harness.production().canonicalPath()));
                assertEquals(1,requestFiles(harness,"writer")); assertEquals(1,requestFiles(harness,"cold_consumer"));
                assertFalse(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json")));
                assertEquals(1,harness.measured().measurements.get()); assertCreditsAndNoRetry(result);
            }
        }
    }
    @Test void physicallyLateApprovalFileCannotRenewTheExpiredReviewOrReplayProduction() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(2));
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            while (Instant.now().isBefore(harness.plan().deadlineUtc().plusMillis(10))) { Thread.sleep(10); }
            publishApproval(harness,new ClosedAdoptionReview.Approval(challenge,ClosedAdoptionReview.Decision.APPROVE,
                    challenge.plan().deadlineUtc().minusNanos(1)));
            try { running.get(10,TimeUnit.SECONDS); }
            catch (ExecutionException expiredDuringApprovalRead) {
                assertInstanceOf(ContractViolationException.class,expiredDuringApprovalRead.getCause());
            }
            JsonNode result = terminal(harness);
            assertEquals("EXPIRED_NO_PRODUCTION_WRITER",result.get("status").textValue());
            assertFalse(result.get("production_writer_attempted").booleanValue()); assertEquals(0,harness.stages().productionRuns.get());
            assertEquals(240,sequence(harness.production().canonicalPath())); assertEquals(1,requestFiles(harness,"writer"));
            assertFalse(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json")));
            assertEquals(1,harness.measured().measurements.get()); assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
    @Test void existingConsumedApprovalMarkerRejectsTheActualCreateOnlyConsumptionBeforeWriterLaunch() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20));
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            var approval = new ClosedAdoptionReview.Approval(challenge,ClosedAdoptionReview.Decision.APPROVE,Instant.now());
            byte[] approvalRaw = StrictJson.canonical(approval.toJson()); Path approvalPath = ClosedAdoptionReview.approvalPath(harness.fixture().root());
            ObjectNode consumed = StrictJson.object(); consumed.put("schema","xar.closed-adoption-root-approval-consumed/v1");
            consumed.put("machine_id",ClosedAdoptionTransactionTest.MACHINE); consumed.put("observed_at_utc",Instant.now().toString());
            consumed.set("approval_ref",new ExactRef(approvalPath.toString(),approvalRaw.length,RecoveryEvidence.sha256(approvalRaw)).toJson());
            Path challengePath = harness.fixture().root().resolve("root-review-challenge.json"); byte[] challengeRaw = Files.readAllBytes(challengePath);
            consumed.set("challenge_ref",new ExactRef(challengePath.toString(),challengeRaw.length,RecoveryEvidence.sha256(challengeRaw)).toJson());
            consumed.put("ticket_nonce",challenge.plan().ticketNonce()); consumed.put("session_nonce",challenge.nonce());
            Path consumedPath = harness.fixture().root().resolve("root-review-approval-consumed.json");
            RecoveryEvidence priorConsumption = publish(consumedPath,StrictJson.canonical(consumed));
            RecoveryEvidence actualApproval = publishApproval(harness,approval);
            ExecutionException rejected = assertThrows(ExecutionException.class,() -> running.get(10,TimeUnit.SECONDS));
            assertInstanceOf(java.nio.file.FileAlreadyExistsException.class,rejected.getCause());
            JsonNode result = terminal(harness);
            assertEquals("REJECTED_OR_UNAVAILABLE_NO_PRODUCTION_WRITER",result.get("status").textValue());
            assertEquals(actualApproval.reference(),ExactRef.fromJson(result.get("root_approval_ref")));
            assertArrayEquals(priorConsumption.bytes(),Files.readAllBytes(consumedPath),"a consumed nonce marker is never replaced");
            assertEquals(0,harness.stages().productionRuns.get()); assertEquals(240,sequence(harness.production().canonicalPath()));
            assertEquals(1,requestFiles(harness,"writer")); assertEquals(1,harness.measured().measurements.get());
            assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
    @Test void identicalBytesAtANewProductionFileIdentityCannotReuseTheApproval() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20));
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            Path replacement = harness.production().canonicalPath().resolveSibling("replacement-predecessor.json");
            Files.write(replacement,harness.fixture().material().input().predecessor().bytes(),StandardOpenOption.CREATE_NEW);
            Files.move(replacement,harness.production().canonicalPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
            assertNotEquals(harness.plan().predecessorIdentity(),new WindowsSavedProofIdentityReader().stat(harness.production().canonicalPath()));
            decide(harness,challenge,ClosedAdoptionReview.Decision.APPROVE);
            assertThrows(ExecutionException.class,() -> running.get(10,TimeUnit.SECONDS)); JsonNode result = terminal(harness);
            assertEquals("REJECTED_OR_UNAVAILABLE_NO_PRODUCTION_WRITER",result.get("status").textValue());
            assertEquals(0,harness.stages().productionRuns.get()); assertEquals(240,sequence(harness.production().canonicalPath()));
            assertEquals(1,requestFiles(harness,"writer")); assertCreditsAndNoRetry(result);
        }
    }
    @Test void productionPredecessorDriftUnderTheOriginalLockCannotCommitOrRetry() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20)); harness.stages().fault = Fault.LOCKED_PREDECESSOR_DRIFT;
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            decide(harness,challenge,ClosedAdoptionReview.Decision.APPROVE);
            assertThrows(ExecutionException.class,() -> running.get(20,TimeUnit.SECONDS)); JsonNode result = terminal(harness);
            assertEquals("PRODUCTION_ATTEMPTED_RESULT_UNAVAILABLE",result.get("status").textValue());
            assertEquals(240,sequence(harness.production().canonicalPath())); assertEquals(1,harness.stages().productionRuns.get());
            assertNull(harness.stages().actualProductionCommit.get()); assertEquals(2,requestFiles(harness,"writer"));
            assertFalse(Files.exists(harness.production().canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000241.json")));
            assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
    @Test void actualCommitThenPublicationFailureRecordsPartialCommitAndKeepsColdUnverified() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20)); harness.stages().fault = Fault.BASIS_AFTER_COMMIT;
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            decide(harness,challenge,ClosedAdoptionReview.Decision.APPROVE);
            assertThrows(ExecutionException.class,() -> running.get(20,TimeUnit.SECONDS)); JsonNode result = terminal(harness);
            assertEquals("PRODUCTION_COMMITTED_COLD_UNVERIFIED",result.get("status").textValue());
            assertEquals("COMMITTED",result.get("production_write_status").textValue()); assertTrue(result.get("production_canonical_written").booleanValue());
            assertFalse(result.get("production_cold_inputs_verified").booleanValue()); assertEquals(241,sequence(harness.production().canonicalPath()));
            assertNotNull(harness.stages().actualProductionCommit.get()); assertEquals(0,harness.stages().actualProductionCommit.get().processExit().exitCode());
            assertTrue(Files.exists(harness.fixture().root().resolve("root-production-committed.json")));
            assertEquals(1,requestFiles(harness,"cold_consumer")); assertFalse(Files.exists(harness.stages().basisPath));
            assertEquals(harness.production().canonicalPath().toString(),result.get("production_head_ref").get("path").textValue());
            assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
    @Test void lostCommittedResponseRemainsUnknownAndTheConsumedApprovalCannotReplayIt() throws Exception {
        Harness harness = prepare(Duration.ofSeconds(20)); harness.stages().fault = Fault.COMMITTED_RESPONSE_LOST;
        try (ExecutorService owner = Executors.newSingleThreadExecutor()) {
            Future<RecoveryEvidence> running = start(owner,harness); var challenge = awaitChallenge(harness,running);
            decide(harness,challenge,ClosedAdoptionReview.Decision.APPROVE);
            assertThrows(ExecutionException.class,() -> running.get(20,TimeUnit.SECONDS)); JsonNode result = terminal(harness);
            assertEquals("PRODUCTION_ATTEMPTED_RESULT_UNAVAILABLE",result.get("status").textValue());
            assertEquals("UNKNOWN",result.get("production_write_status").textValue()); assertTrue(result.get("production_canonical_written").isNull());
            assertEquals(241,sequence(harness.production().canonicalPath())); assertNotNull(harness.stages().actualProductionCommit.get());
            assertFalse(Files.exists(harness.fixture().root().resolve("root-production-committed.json")));
            assertTrue(Files.exists(harness.fixture().root().resolve("root-review-approval-consumed.json")));
            assertEquals(1,requestFiles(harness,"cold_consumer")); assertEquals(2,requestFiles(harness,"writer"));
            assertCreditsAndNoRetry(result); assertNotRetried(harness);
        }
    }
}
