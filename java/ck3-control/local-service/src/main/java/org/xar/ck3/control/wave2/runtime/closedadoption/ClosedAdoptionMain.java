package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.RootSoftwareChildBootstrap;
import org.xar.ck3.control.build.SdkDerivedSource32;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsJobSdkMeasurementRunner;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Root-managed temporary CLI and an explicit independently reviewed continuation in the same JVM. */
public final class ClosedAdoptionMain {
    private ClosedAdoptionMain() { }
    public record Invocation(String machine, ExactRef request, ExactRef ticket, Path repo, Path python, Path output,
            long memoryBytes, Duration timeout, Instant deadline, long minimumFreeBytes, long maximumOutputBytes,
            ExactRef mechanicalSource, ExactRef coldOwnerSource) {
        public static Invocation decode(byte[] raw) {
            ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema","machine_id","adoption_request_ref","sdk_read_ticket_ref",
                    "repo","python_executable","output_root","memory_limit_bytes","timeout_seconds","lease_deadline_utc",
                    "minimum_free_bytes","maximum_output_bytes","mechanical_source_ref","cold_owner_source_ref"));
            StrictJson.require("xar.closed-partial-temporary-invocation/v1".equals(text(row,"schema")), "temporary transaction invocation schema");
            return new Invocation(text(row,"machine_id"),ExactRef.fromJson(row.get("adoption_request_ref")),ExactRef.fromJson(row.get("sdk_read_ticket_ref")),
                    path(row,"repo"),path(row,"python_executable"),path(row,"output_root"),
                    StrictJson.integer(row.get("memory_limit_bytes"),1,512L*1024*1024),
                    Duration.ofSeconds(StrictJson.integer(row.get("timeout_seconds"),1,120)),
                    Instant.parse(StrictJson.utc(text(row,"lease_deadline_utc"))),
                    StrictJson.integer(row.get("minimum_free_bytes"),1,StrictJson.MAX_SAFE_INTEGER),
                    StrictJson.integer(row.get("maximum_output_bytes"),1,16L*1024*1024),
                    ExactRef.fromJson(row.get("mechanical_source_ref")),ExactRef.fromJson(row.get("cold_owner_source_ref")));
        }
    }

    /** Arguments are the Root-measured invocation path, exact byte length and lowercase SHA-256. */
    public static void main(String[] args) throws IOException, InterruptedException {
        StrictJson.require(args.length == 3 && args[1].matches("[1-9][0-9]*"), "usage: ClosedAdoptionMain invocation-path exact-bytes sha256");
        RecoveryEvidence result = runTemporary(new ExactRef(args[0],Long.parseLong(args[1]),args[2]));
        System.out.println(new String(result.bytes(),java.nio.charset.StandardCharsets.UTF_8));
    }

    public static RecoveryEvidence runTemporary(ExactRef invocationRef) throws IOException, InterruptedException {
        return runTemporaryRetained(invocationRef,Optional.empty()).result();
    }
    private record RetainedTemporary(ExactRef invocationRef, Invocation invocation, SavedProofReadTicket ticket,
            SavedCheckpointMeasurementCoordinator measured, ClosedAdoptionSourceLoader source,
            WindowsFileWriterSession.Settings settings, RecoveryEvidence result, FileStatIdentity resultIdentity) { }
    private enum RootStage { AWAITING_ROOT_REVIEW, PRODUCTION_ORIGINAL_WRITER_ATTEMPTED,
        PRODUCTION_ORIGINAL_WRITER_COMMITTED, PRODUCTION_COLD_INPUTS_VERIFIED_ROOT_CONSUMER_SESSION, ROOT_CONSUMER_SESSION_ENDED }
    private enum RootStatus { EXPIRED_NO_PRODUCTION_WRITER, DECLINED_NO_PRODUCTION_WRITER, STOPPED_NO_PRODUCTION_WRITER,
        PRODUCTION_COMMITTED_COLD_UNVERIFIED, PRODUCTION_CLOSED_INPUTS_VERIFIED,
        PRODUCTION_CLOSED_INPUTS_VERIFIED_FOLLOWUP_UNAVAILABLE, PRODUCTION_ATTEMPTED_RESULT_UNAVAILABLE,
        REJECTED_OR_UNAVAILABLE_NO_PRODUCTION_WRITER }
    private enum ProductionWriteStatus { NOT_ATTEMPTED, UNKNOWN, COMMITTED }

    /** Distinct explicit Root entry. The original three-argument Main remains temporary only. */
    public static final class RootSessionMain {
        private RootSessionMain() { }
        public static void main(String[] args) throws IOException, InterruptedException {
            StrictJson.require(args.length == 6 && args[1].matches("[1-9][0-9]*") && args[4].matches("[1-9][0-9]*"),
                    "usage: RootSessionMain invocation-path exact-bytes sha256 review-plan-path exact-bytes sha256");
            RecoveryEvidence result = runRootTwoStage(new ExactRef(args[0],Long.parseLong(args[1]),args[2]),
                    new ExactRef(args[3],Long.parseLong(args[4]),args[5]));
            System.out.println(new String(result.bytes(),java.nio.charset.StandardCharsets.UTF_8));
        }
    }

    /** Retains one measured cache while Root independently reviews the published temporary result. */
    public static RecoveryEvidence runRootTwoStage(ExactRef invocationRef, ExactRef reviewPlanRef) throws IOException, InterruptedException {
        return runRootSessionInternal(invocationRef,reviewPlanRef,Optional.empty(),Optional.empty(),Optional.empty());
    }
    /** Actual Root continuation. The workflow executes only after explicit Root review and original locked admission. */
    public static RecoveryEvidence runRootSession(ExactRef invocationRef, ExactRef reviewPlanRef,
            NativeOwnerResumeSession.Workflow workflow) throws IOException, InterruptedException {
        return runRootSessionInternal(invocationRef,reviewPlanRef,Optional.of(java.util.Objects.requireNonNull(workflow)),Optional.empty(),Optional.empty());
    }
    public static RecoveryEvidence runRootColdSession(ExactRef invocationRef,ExactRef reviewPlanRef,
            RootColdResumeSession.Workflow workflow) throws IOException,InterruptedException {
        return runRootSessionInternal(invocationRef,reviewPlanRef,Optional.empty(),Optional.of(java.util.Objects.requireNonNull(workflow)),Optional.empty());
    }
    /** Explicit source-bound SDK installation for every independent cold producer in this Root session. */
    public static RecoveryEvidence runRootColdSession(ExactRef invocationRef,ExactRef reviewPlanRef,
            RootSoftwareChildBootstrap.SdkLineageBinding lineage,RootColdResumeSession.Workflow workflow)
            throws IOException,InterruptedException {
        return runRootSessionInternal(invocationRef,reviewPlanRef,Optional.empty(),
                Optional.of(java.util.Objects.requireNonNull(workflow)),Optional.of(java.util.Objects.requireNonNull(lineage)));
    }
    private static RecoveryEvidence runRootSessionInternal(ExactRef invocationRef, ExactRef reviewPlanRef,
            Optional<NativeOwnerResumeSession.Workflow> workflow,Optional<RootColdResumeSession.Workflow> coldWorkflow,
            Optional<RootSoftwareChildBootstrap.SdkLineageBinding> lineage) throws IOException, InterruptedException {
        var identities = new WindowsSavedProofIdentityReader();
        var plan = ClosedAdoptionReview.Plan.decode(exactEvidence(reviewPlanRef,RecoveryEvidence.MAX_BYTES,identities).bytes());
        RetainedTemporary retained = runTemporaryRetained(invocationRef,Optional.of(plan));
        requireSdkLineage(retained.ticket(),lineage);
        return runRootContinuation(new RetainedReviewContext(retained.invocationRef(),retained.invocation(),retained.ticket().nonce(),
                retained.ticket().reviewAt(),retained.result(),retained.resultIdentity(),retainedStages(retained,plan.deadlineUtc(),workflow,coldWorkflow,lineage)),reviewPlanRef,plan);
    }
    private static void requireSdkLineage(SavedProofReadTicket ticket,
            Optional<RootSoftwareChildBootstrap.SdkLineageBinding> lineage) throws IOException {
        String schema = StrictJson.text(StrictJson.parse(exactBytes(ticket.sdkFreeze(),2_097_152,
                new WindowsSavedProofIdentityReader())).get("schema"));
        if (lineage.isEmpty()) {
            StrictJson.require(!SdkDerivedSource32.SCHEMA.equals(schema),
                    "Derived SDK requires the explicit typed Root cold entry");
            return;
        }
        var selected = lineage.orElseThrow(); var actual = selected.sdkFreezeRef(); ExactRef released = ticket.sdkFreeze();
        StrictJson.require(actual.path().equals(released.path()) && actual.bytes()==released.bytes()
                && actual.sha256().equals(released.sha256()),"Root SDK installation equals the actual same-session read ticket");
        actual.verify();
        StrictJson.require((selected.kind()==RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32)
                == SdkDerivedSource32.SCHEMA.equals(schema),"explicit Root SDK kind matches the actual source schema");
        if (selected.kind()==RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32) {
            var verified = SdkDerivedSource32.readVerifiedEmission(selected.verifiedEmissionRef());
            StrictJson.require(verified.machineId().equals(ticket.machineId()) && verified.lineageRef().equals(actual)
                    && Path.of(verified.sdkRoot()).equals(ticket.sdkRoot()) && !verified.runtimeAdmitted()
                    && !verified.nativeRestoreAdmitted(),"actual Java emission matches Root read source and machine");
        }
    }
    /** In-memory scope only. The operational implementation closes over the actual non-deserializable measurement owner. */
    interface RetainedStages {
        ClosedAdoptionRequest request();
        ClosedAdoptionMaterial.CurrentSource currentSource();
        void requireCurrentMeasurement() throws IOException;
        void preflightProductionPublications() throws IOException;
        ClosedAdoptionApplication.Completed runProduction(OriginalWriterTransaction.Target target,
                ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionApplication.CommitObserver observer)
                throws IOException, InterruptedException;
        default ClosedAdoptionApplication.Completed runProductionWithRestore(OriginalWriterTransaction.Target target,
                ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionMaterial.CurrentSource handoffCurrent,
                Runnable rootScope, ClosedAdoptionApplication.CommitObserver observer) throws IOException, InterruptedException {
            return runProduction(target,lockedCurrent,observer);
        }
        RecoveryEvidence serveFollowup(ClosedAdoptionApplication.Completed complete, Path sessionDirectory, Instant deadline)
                throws IOException, InterruptedException;
    }
    record RetainedReviewContext(ExactRef invocationRef, Invocation invocation, String ticketNonce, Instant ticketReviewAt,
            RecoveryEvidence result, FileStatIdentity resultIdentity, RetainedStages stages) { }
    private static RetainedStages retainedStages(RetainedTemporary retained, Instant reviewDeadline,
            Optional<NativeOwnerResumeSession.Workflow> workflow,Optional<RootColdResumeSession.Workflow> coldWorkflow,
            Optional<RootSoftwareChildBootstrap.SdkLineageBinding> lineage) {
        var original = withinLease(retained.settings(),reviewDeadline);
        WindowsFileWriterSession.Settings productionSettings = new WindowsFileWriterSession.Settings(original.python(),original.repo(),
                original.outputRoot(),original.memoryLimitBytes(),original.timeout(),original.leaseDeadline(),original.environment(),
                original.mechanicalSource(),original.coldOwnerSource(),original.capacityGuard(),lineage);
        return new RetainedStages() {
            private Optional<OriginalWriterTransaction.RetainedSession> writerSession = Optional.empty();
            @Override public ClosedAdoptionRequest request() { return retained.source().request(); }
            @Override public ClosedAdoptionMaterial.CurrentSource currentSource() { return retained.source(); }
            @Override public void requireCurrentMeasurement() throws IOException { retained.measured().requireCurrentCached(); }
            @Override public void preflightProductionPublications() throws IOException { retained.source().preflightProductionPublications(); }
            @Override public ClosedAdoptionApplication.Completed runProduction(OriginalWriterTransaction.Target target,
                    ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionApplication.CommitObserver observer)
                    throws IOException, InterruptedException {
                return ClosedAdoptionApplication.runProduction(retained.source(),target,lockedCurrent,productionSettings,observer);
            }
            @Override public ClosedAdoptionApplication.Completed runProductionWithRestore(OriginalWriterTransaction.Target target,
                    ClosedAdoptionMaterial.CurrentSource lockedCurrent, ClosedAdoptionMaterial.CurrentSource handoffCurrent,
                    Runnable rootScope, ClosedAdoptionApplication.CommitObserver observer) throws IOException, InterruptedException {
                StrictJson.require(writerSession.isEmpty(),"one actual production writer continuation per Root session");
                var complete = ClosedAdoptionApplication.runProductionRetained(retained.source(),target,lockedCurrent,handoffCurrent,rootScope,
                        retained.ticket(),productionSettings,observer);
                writerSession = Optional.of(complete.writerSession());
                return complete.completed();
            }
            @Override public RecoveryEvidence serveFollowup(ClosedAdoptionApplication.Completed complete, Path directory, Instant deadline)
                    throws IOException, InterruptedException {
                return OriginalColdConsumerSession.serveRootSession(retained.source(),complete.writer(),retained.source()::currentCanonicalReceipt,
                        complete.basis(),complete.qualification(),productionSettings,directory,deadline,
                        retained.measured().retainClosedMeasurement(),writerSession,workflow,coldWorkflow);
            }
        };
    }
    /** Every original writer/consumer uses the explicit transport repo and ticket SDK, without inherited Python roots. */
    static Map<String,String> sessionEnvironment(Path repo, Path sdkRoot, Path output, Map<String,String> inherited) {
        Map<String,String> environment = new HashMap<>(inherited);
        Set<String> controlled = Set.of("PYTHONPATH","PYTHONHOME","PYTHONUSERBASE","PYTHONNOUSERSITE",
                "PYTHONSAFEPATH","PYTHONDONTWRITEBYTECODE","PYTHONUTF8","TMP","TEMP");
        environment.keySet().removeIf(key -> controlled.contains(key.toUpperCase(java.util.Locale.ROOT)));
        environment.put("PYTHONPATH",repo.toAbsolutePath().normalize()+java.io.File.pathSeparator+sdkRoot.toAbsolutePath().normalize());
        environment.put("PYTHONNOUSERSITE","1"); environment.put("PYTHONSAFEPATH","1");
        environment.put("PYTHONDONTWRITEBYTECODE","1"); environment.put("PYTHONUTF8","1");
        environment.put("TMP",output.toAbsolutePath().normalize().toString()); environment.put("TEMP",output.toAbsolutePath().normalize().toString());
        return Map.copyOf(environment);
    }
    static WindowsFileWriterSession.Settings withinLease(WindowsFileWriterSession.Settings original, Instant deadline) {
        StrictJson.require(!deadline.isAfter(original.leaseDeadline()),"production processes cannot extend the original action lease");
        return new WindowsFileWriterSession.Settings(original.python(),original.repo(),original.outputRoot(),original.memoryLimitBytes(),
                original.timeout(),deadline,original.environment(),original.mechanicalSource(),original.coldOwnerSource(),original.capacityGuard(),original.sdkLineageBinding());
    }
    static RecoveryEvidence runRootContinuation(RetainedReviewContext retained, ExactRef reviewPlanRef,
            ClosedAdoptionReview.Plan plan) throws IOException, InterruptedException {
        var identities = new WindowsSavedProofIdentityReader();
        Path output = retained.invocation().output().toRealPath();
        Path terminal = output.resolve("root-two-stage-result.json");
        RootStage stage = RootStage.AWAITING_ROOT_REVIEW; boolean attempted = false;
        AtomicReference<OriginalWriterTransaction.Committed> committed = new AtomicReference<>();
        AtomicReference<ClosedAdoptionApplication.Completed> productionCompleted = new AtomicReference<>();
        RecoveryEvidence approvalEvidence = null;
        try {
            StrictJson.require(!Files.exists(ClosedAdoptionReview.approvalPath(output),LinkOption.NOFOLLOW_LINKS),
                    "Root approval must be supplied after the temporary result and challenge are published");
            StrictJson.require(identities.stat(Path.of(retained.result().reference().path())).equals(retained.resultIdentity()),
                    "temporary publication retains its actual native identity before Root review");
            exactEvidence(retained.result().reference(),RecoveryEvidence.MAX_BYTES,identities);
            var challenge = ClosedAdoptionReview.createChallenge(plan,retained.result().reference(),retained.invocation().machine(),
                    retained.invocation().ticket(),retained.ticketNonce(),retained.ticketReviewAt(),retained.invocation().deadline(),Instant.now());
            RecoveryEvidence publishedChallenge = publish(output.resolve("root-review-challenge.json"),challenge.toJson());
            Path approvalPath = ClosedAdoptionReview.approvalPath(output);
            while (!Files.exists(approvalPath,LinkOption.NOFOLLOW_LINKS)) {
                if (!Instant.now().isBefore(plan.deadlineUtc())) {
                    return publish(terminal,rootResult(retained,reviewPlanRef,RootStatus.EXPIRED_NO_PRODUCTION_WRITER,stage,false,null,null));
                }
                guard(retained.invocation(),output);
                Thread.sleep(250);
            }
            exactEvidence(reviewPlanRef,RecoveryEvidence.MAX_BYTES,identities);
            exactEvidence(publishedChallenge.reference(),RecoveryEvidence.MAX_BYTES,identities);
            StrictJson.require(identities.stat(Path.of(retained.result().reference().path())).equals(retained.resultIdentity()),
                    "actual reviewed temporary result retains its native identity");
            exactEvidence(retained.result().reference(),RecoveryEvidence.MAX_BYTES,identities);
            byte[] approvalRaw = read(approvalPath,RecoveryEvidence.MAX_BYTES,identities);
            approvalEvidence = new RecoveryEvidence(new ExactRef(approvalPath.toString(),approvalRaw.length,RecoveryEvidence.sha256(approvalRaw)),approvalRaw);
            var decision = ClosedAdoptionReview.validateApproval(challenge,ClosedAdoptionReview.Approval.decode(approvalRaw),Instant.now());
            if (decision == ClosedAdoptionReview.Decision.DECLINE) {
                return publish(terminal,rootResult(retained,reviewPlanRef,RootStatus.DECLINED_NO_PRODUCTION_WRITER,stage,false,null,approvalEvidence));
            }
            retained.stages().requireCurrentMeasurement();
            requireProductionPredecessor(plan,retained.stages().request(),identities);
            retained.stages().preflightProductionPublications();
            ObjectNode consumed = StrictJson.object(); consumed.put("schema","xar.closed-adoption-root-approval-consumed/v1");
            consumed.put("machine_id",retained.invocation().machine()); consumed.put("observed_at_utc",Instant.now().toString());
            consumed.set("approval_ref",approvalEvidence.reference().toJson()); consumed.set("challenge_ref",publishedChallenge.reference().toJson());
            consumed.put("ticket_nonce",retained.ticketNonce()); consumed.put("session_nonce",challenge.nonce());
            publish(output.resolve("root-review-approval-consumed.json"),consumed);
            stage = RootStage.PRODUCTION_ORIGINAL_WRITER_ATTEMPTED; attempted = true;
            ExactRef approvedRef = approvalEvidence.reference();
            FileStatIdentity approvedIdentity = identities.stat(approvalPath);
            ClosedAdoptionMaterial.CurrentSource lockedCurrent = () -> {
                try {
                    guard(retained.invocation(),output);
                    StrictJson.require(Instant.now().isBefore(plan.deadlineUtc()),"Root production approval remains within its finite lease");
                    StrictJson.require(identities.stat(approvalPath).equals(approvedIdentity),"same Root approval native identity under the original writer lock");
                    exactEvidence(approvedRef,RecoveryEvidence.MAX_BYTES,identities);
                    exactEvidence(reviewPlanRef,RecoveryEvidence.MAX_BYTES,identities);
                    requireProductionPredecessor(plan,retained.stages().request(),identities);
                    return retained.stages().currentSource().current();
                } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
            };
            Runnable rootScope = () -> {
                try {
                    guard(retained.invocation(),output);
                    StrictJson.require(Instant.now().isBefore(plan.deadlineUtc()),"Root restore approval remains within its original finite lease");
                    StrictJson.require(identities.stat(approvalPath).equals(approvedIdentity),"same actual Root approval native identity for restore handoff");
                    exactEvidence(approvedRef,RecoveryEvidence.MAX_BYTES,identities);
                    exactEvidence(reviewPlanRef,RecoveryEvidence.MAX_BYTES,identities);
                } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
            };
            ClosedAdoptionMaterial.CurrentSource handoffCurrent = () -> {
                rootScope.run();
                // Compare the now-committed head under the later original writer lock, not the old predecessor identity.
                return retained.stages().currentSource().current();
            };
            var complete = retained.stages().runProductionWithRestore(plan.target(),lockedCurrent,handoffCurrent,rootScope,value -> {
                committed.set(value);
                ObjectNode checkpoint = rootResult(retained,reviewPlanRef,RootStatus.PRODUCTION_COMMITTED_COLD_UNVERIFIED,
                        RootStage.PRODUCTION_ORIGINAL_WRITER_COMMITTED,true,value,null);
                publish(output.resolve("root-production-committed.json"),checkpoint);
            });
            productionCompleted.set(complete);
            stage = RootStage.PRODUCTION_COLD_INPUTS_VERIFIED_ROOT_CONSUMER_SESSION;
            RecoveryEvidence followup = retained.stages().serveFollowup(complete,output.resolve("root-consumer-session"),plan.deadlineUtc());
            guardOutput(retained.invocation(),output,false);
            ObjectNode result = rootResult(retained,reviewPlanRef,RootStatus.PRODUCTION_CLOSED_INPUTS_VERIFIED,
                    RootStage.ROOT_CONSUMER_SESSION_ENDED,true,complete.writer(),approvalEvidence);
            result.put("production_cold_inputs_verified",true);
            result.set("root_consumer_session_receipt_ref",followup.reference().toJson());
            result.set("production_basis_ref",complete.basis().reference().toJson());
            result.set("production_qualification_ref",complete.qualification().reference().toJson());
            result.set("original_cold_consumer_result",StrictJson.parse(complete.consumer().originalConsumerReceipt()));
            var jobs = result.putArray("actual_production_processes");
            for (var job : complete.actualJobs()) {
                ObjectNode value = jobs.addObject(); value.put("pid",job.identity().pid()); value.put("creation_filetime",job.identity().creationFiletimeDecimal());
                value.put("exit_code",job.exitCode()); value.put("active_processes",job.accounting().activeProcesses());
                value.put("elapsed_seconds_decimal",Double.toString(job.elapsedSeconds()));
            }
            return publish(terminal,result);
        } catch (IOException | InterruptedException | RuntimeException error) {
            RootStatus status = productionCompleted.get() != null ? RootStatus.PRODUCTION_CLOSED_INPUTS_VERIFIED_FOLLOWUP_UNAVAILABLE
                    : committed.get() != null ? RootStatus.PRODUCTION_COMMITTED_COLD_UNVERIFIED
                    : attempted ? RootStatus.PRODUCTION_ATTEMPTED_RESULT_UNAVAILABLE
                    : error instanceof InterruptedException ? RootStatus.STOPPED_NO_PRODUCTION_WRITER
                    : !Instant.now().isBefore(plan.deadlineUtc()) ? RootStatus.EXPIRED_NO_PRODUCTION_WRITER
                    : RootStatus.REJECTED_OR_UNAVAILABLE_NO_PRODUCTION_WRITER;
            ObjectNode result = rootResult(retained,reviewPlanRef,status,stage,attempted,committed.get(),approvalEvidence);
            if (productionCompleted.get() != null) {
                result.put("production_cold_inputs_verified",true);
                result.set("production_basis_ref",productionCompleted.get().basis().reference().toJson());
                result.set("production_qualification_ref",productionCompleted.get().qualification().reference().toJson());
            }
            String message = error.getClass().getSimpleName()+": "+error.getMessage();
            result.put("error",message.substring(0,Math.min(message.length(),2048)));
            try { publish(terminal,result); } catch (IOException | RuntimeException reporting) { error.addSuppressed(reporting); }
            throw error;
        }
    }
    private static RetainedTemporary runTemporaryRetained(ExactRef invocationRef, Optional<ClosedAdoptionReview.Plan> review)
            throws IOException, InterruptedException {
        WindowsSavedProofIdentityReader identities = new WindowsSavedProofIdentityReader();
        RecoveryEvidence invocationEvidence = exactEvidence(invocationRef,RecoveryEvidence.MAX_BYTES,identities);
        Invocation invocation = Invocation.decode(invocationEvidence.bytes());
        RecoveryEvidence requestEvidence = exactEvidence(invocation.request(),RecoveryEvidence.MAX_BYTES,identities);
        RecoveryEvidence ticketEvidence = exactEvidence(invocation.ticket(),RecoveryEvidence.MAX_BYTES,identities);
        ClosedAdoptionRequest request = ClosedAdoptionRequest.decode(requestEvidence.bytes());
        SavedProofReadTicket ticket = SavedProofReadTicket.parse(ticketEvidence);
        Path output = invocation.output().toRealPath();
        StrictJson.require(invocation.machine().equals(WindowsJobProcess.currentMachineId())
                && invocation.machine().equals(request.machineId()) && invocation.machine().equals(ticket.machineId()), "actual shared invocation/request/ticket machine");
        StrictJson.require(output.equals(ticket.outputRoot().toRealPath()) && Files.isDirectory(output,LinkOption.NOFOLLOW_LINKS)
                && request.canonicalPath().toRealPath().equals(output.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json").toRealPath())
                && request.metadataRoot().toRealPath().equals(output.resolve("metadata").toRealPath()),
                "existing temporary canonical and metadata belong to the independently released SDK output root");
        StrictJson.require(invocation.python().equals(ticket.pythonExecutable()) && invocation.deadline().isAfter(Instant.now())
                && !invocation.deadline().isAfter(ticket.reviewAt()), "one actual interpreter and earliest finite lease");
        Path resultPath = output.resolve("closed-adoption-result.json");
        StrictJson.require(!Files.exists(resultPath), "create-only temporary transaction result");
        Runnable capacity = () -> guard(invocation,output);
        Map<String,String> environment = sessionEnvironment(invocation.repo(),ticket.sdkRoot(),output,System.getenv());
        var settings = new WindowsFileWriterSession.Settings(invocation.python(),invocation.repo(),output,invocation.memoryBytes(),
                invocation.timeout(),invocation.deadline(),environment,invocation.mechanicalSource(),invocation.coldOwnerSource(),capacity);
        if (review.isPresent()) { preflightReview(review.orElseThrow(),invocation,request,ticket,identities); }
        exactBytes(invocation.mechanicalSource(),2*1024*1024,identities); exactBytes(invocation.coldOwnerSource(),2*1024*1024,identities);
        var measured = new SavedCheckpointMeasurementCoordinator(new WindowsJobSdkMeasurementRunner(capacity),identities);
        var sources = new ClosedAdoptionSourceLoader(request,measured);
        sources.preflightSources();
        if (review.isPresent()) { sources.preflightProductionPublications(); }
        byte[] currentCanonical = read(request.canonicalPath(),RecoveryEvidence.MAX_BYTES,identities);
        StrictJson.require(java.util.Arrays.equals(currentCanonical,exactEvidence(request.inputs().predecessor(),RecoveryEvidence.MAX_BYTES,identities).bytes()),
                "temporary canonical starts at the exact immutable predecessor");
        long sequence = StrictJson.integer(StrictJson.parse(currentCanonical).get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
        Path originalEvent = request.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS")
                .resolve(String.format(java.util.Locale.ROOT,"%08d.json",sequence));
        StrictJson.require(StrictJson.parse(read(originalEvent,RecoveryEvidence.MAX_BYTES,identities)).get("after").equals(StrictJson.parse(currentCanonical)),
                "temporary original writer has its real committed predecessor event");
        capacity.run();
        String stage = "single-original-SDK-measurement";
        try {
            measured.measureOnce(ticket);
            stage = "temporary-original-writer-and-cold-consumer";
            var completed = ClosedAdoptionApplication.runTemporary(sources,settings);
            capacity.run();
            ObjectNode result = temporaryResult(invocationRef,invocation,measured.requireCurrentCached().canonicalCheckpointProof(),completed);
            RecoveryEvidence publication = publish(resultPath,result);
            return new RetainedTemporary(invocationRef,invocation,ticket,measured,sources,settings,publication,identities.stat(resultPath));
        } catch (IOException | InterruptedException | RuntimeException error) {
            ObjectNode result = base(invocationRef,invocation,"REJECTED_OR_UNAVAILABLE",stage);
            result.put("measurement_cached",measured.hasMeasuredCache());
            String message = error.getClass().getSimpleName()+": "+error.getMessage();
            result.put("error",message.substring(0,Math.min(message.length(),2048)));
            try { publish(resultPath,result); } catch (IOException | RuntimeException reporting) { error.addSuppressed(reporting); }
            throw error;
        }
    }
    /** One factual receipt producer for the operational entry and the actual-process fixture seam. */
    static ObjectNode temporaryResult(ExactRef invocationRef, Invocation invocation, ExactRef canonicalProof,
            ClosedAdoptionApplication.Completed completed) {
        ObjectNode result = base(invocationRef,invocation,"TEMPORARY_CLOSED_INPUTS_VERIFIED","temporary-original-writer-and-cold-consumer");
        result.set("canonical_checkpoint_proof",canonicalProof.toJson());
        result.set("temporary_head_ref",completed.writer().head().evidence().reference().toJson());
        result.set("temporary_event_ref",completed.writer().event().evidence().reference().toJson());
        result.set("temporary_index_ref",completed.writer().index().evidence().reference().toJson());
        result.set("basis_ref",completed.basis().reference().toJson()); result.set("qualification_ref",completed.qualification().reference().toJson());
        var jobs = result.putArray("actual_original_processes");
        for (var job : completed.actualJobs()) {
            ObjectNode item = jobs.addObject(); item.put("pid",job.identity().pid()); item.put("creation_filetime",job.identity().creationFiletimeDecimal());
            item.put("executable",job.identity().executable()); item.put("exit_code",job.exitCode());
            item.put("active_processes",job.accounting().activeProcesses()); item.put("elapsed_seconds_decimal",Double.toString(job.elapsedSeconds()));
        }
        result.set("original_cold_consumer_result",StrictJson.parse(completed.consumer().originalConsumerReceipt()));
        return result;
    }
    private static void preflightReview(ClosedAdoptionReview.Plan plan, Invocation invocation, ClosedAdoptionRequest request,
            SavedProofReadTicket ticket, WindowsSavedProofIdentityReader identities) throws IOException {
        StrictJson.require(plan.machineId().equals(invocation.machine()) && plan.ticketRef().equals(invocation.ticket())
                && plan.ticketNonce().equals(ticket.nonce()) && Instant.now().isBefore(plan.deadlineUtc())
                && !plan.deadlineUtc().isAfter(ticket.reviewAt()) && !plan.deadlineUtc().isAfter(invocation.deadline()),
                "Root plan binds the actual ticket nonce, machine and earliest existing lease");
        Path output = invocation.output().toRealPath();
        for (String name : java.util.List.of("root-review-challenge.json","root-review-approval.json","root-review-approval-consumed.json",
                "root-production-committed.json","root-two-stage-result.json","root-consumer-session")) {
            StrictJson.require(!Files.exists(output.resolve(name),LinkOption.NOFOLLOW_LINKS),"Root review paths must be absent before the temporary stage");
        }
        StrictJson.require(!plan.target().canonicalPath().toRealPath().startsWith(output)
                && plan.target().originalWriter().equals(request.writerSource()),"distinct actual production target and original writer source");
        requireProductionPredecessor(plan,request,identities);
    }
    private static void requireProductionPredecessor(ClosedAdoptionReview.Plan plan, ClosedAdoptionRequest request,
            WindowsSavedProofIdentityReader identities) throws IOException {
        ExactRef immutable = request.inputs().predecessor();
        StrictJson.require(!Path.of(immutable.path()).toRealPath().equals(plan.target().canonicalPath().toRealPath())
                && immutable.bytes() == plan.predecessorRef().bytes() && immutable.sha256().equals(plan.predecessorRef().sha256()),
                "production head observation and separately addressed immutable input have identical exact bytes");
        StrictJson.require(identities.stat(plan.target().canonicalPath()).equals(plan.predecessorIdentity()),"Root-approved production predecessor native identity");
        exactEvidence(plan.predecessorRef(),RecoveryEvidence.MAX_BYTES,identities);
        StrictJson.require(identities.stat(plan.target().canonicalPath()).equals(plan.predecessorIdentity()),"stable Root-approved production predecessor identity");
    }
    private static ObjectNode rootResult(RetainedReviewContext retained, ExactRef planRef, RootStatus status, RootStage stage,
            boolean attempted, OriginalWriterTransaction.Committed committed, RecoveryEvidence approval) {
        ObjectNode row = base(retained.invocationRef(),retained.invocation(),status.name(),stage.name());
        row.put("schema","xar.closed-adoption-root-two-stage-result/v1");
        row.set("review_plan_ref",planRef.toJson()); row.set("temporary_result_ref",retained.result().reference().toJson());
        row.put("ticket_nonce",retained.ticketNonce()); row.put("production_writer_attempted",attempted);
        row.put("production_cold_inputs_verified",false);
        if (approval == null) { row.putNull("root_approval_ref"); } else { row.set("root_approval_ref",approval.reference().toJson()); }
        if (committed != null) {
            row.put("production_canonical_written",true); row.put("production_write_status",ProductionWriteStatus.COMMITTED.name());
            row.set("production_head_ref",committed.head().evidence().reference().toJson());
            row.set("production_event_ref",committed.event().evidence().reference().toJson());
            row.set("production_index_ref",committed.index().evidence().reference().toJson());
        } else if (attempted) { row.putNull("production_canonical_written"); row.put("production_write_status",ProductionWriteStatus.UNKNOWN.name()); }
        else { row.put("production_canonical_written",false); row.put("production_write_status",ProductionWriteStatus.NOT_ATTEMPTED.name()); }
        row.put("automatic_retry_authorized",false); return row;
    }
    private static ObjectNode base(ExactRef ref, Invocation invocation, String status, String stage) {
        ObjectNode row = StrictJson.object(); row.put("schema","xar.closed-partial-temporary-transaction-result/v1");
        row.put("machine_id",invocation.machine()); row.put("observed_at_utc",Instant.now().toString()); row.put("status",status); row.put("stage",stage);
        row.set("invocation_ref",ref.toJson()); row.set("request_ref",invocation.request().toJson()); row.set("sdk_read_ticket_ref",invocation.ticket().toJson());
        row.put("production_canonical_written",false); row.put("raw_pending_modified",false); row.put("original_actions_replayed",false);
        row.put("new_game_day_credit",0); row.put("new_ordinary_cycle_credit",0); row.put("grants_new_warm_attachment",false); return row;
    }
    private static RecoveryEvidence publish(Path path, ObjectNode value) throws IOException {
        byte[] raw = StrictJson.canonical(value); Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        return new RecoveryEvidence(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
    }
    private static RecoveryEvidence exactEvidence(ExactRef ref, int maximum, WindowsSavedProofIdentityReader identities) throws IOException {
        return new RecoveryEvidence(ref,exactBytes(ref,maximum,identities));
    }
    private static byte[] exactBytes(ExactRef ref, int maximum, WindowsSavedProofIdentityReader identities) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= maximum, "bounded exact Root parameter/source");
        byte[] raw = read(Path.of(ref.path()),maximum,identities);
        StrictJson.require(raw.length == ref.bytes() && RecoveryEvidence.sha256(raw).equals(ref.sha256()),
                "exact original input length and SHA required");
        return raw;
    }
    private static byte[] read(Path path, int maximum, WindowsSavedProofIdentityReader identities) throws IOException {
        String name = path.toString().replace('\\','/').toLowerCase(java.util.Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"), "CLI only reads small metadata/source inputs");
        var before = identities.stat(path); StrictJson.require(before.bytes().longValueExact() <= maximum, "bounded complete metadata/source input");
        byte[] raw; try (var input = Files.newInputStream(path)) { raw = input.readNBytes(maximum+1); }
        StrictJson.require(raw.length == before.bytes().longValueExact() && raw.length <= maximum && before.equals(identities.stat(path)), "stable native metadata/source read"); return raw;
    }
    private static void guard(Invocation invocation, Path output) {
        guardOutput(invocation,output,true);
    }
    /** Final factual metadata can be retained after the action lease ended; all space and inventory bounds still apply. */
    private static void guardOutput(Invocation invocation, Path output, boolean enforceActionLease) {
        try {
            StrictJson.require((!enforceActionLease || Instant.now().isBefore(invocation.deadline()))
                    && Files.getFileStore(output).getUsableSpace() >= invocation.minimumFreeBytes(),
                    "Root finite lease and existing policy free-space threshold");
            long bytes = 0; int count = 0;
            try (var paths = Files.walk(output)) {
                var iterator = paths.iterator();
                while (iterator.hasNext()) {
                    Path path = iterator.next();
                    StrictJson.require(++count <= 512 && !Files.isSymbolicLink(path), "bounded owned temporary output inventory");
                    if (Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)) { bytes = Math.addExact(bytes,Files.size(path)); }
                }
            }
            StrictJson.require(bytes <= invocation.maximumOutputBytes(), "Root finite temporary metadata/log output budget");
        } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static Path path(ObjectNode row, String field) {
        Path value = Path.of(text(row,field)); StrictJson.require(value.isAbsolute() && value.normalize().equals(value), "absolute normalized Root path"); return value;
    }
}
