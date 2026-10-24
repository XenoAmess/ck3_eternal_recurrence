package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Shared read-only consumer of one completed direct-admin registration; never submits or retries. */
public final class NativeProjectExeRegistration {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final int LIMIT = 1 << 20;
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";

    private NativeProjectExeRegistration() { }

    public record Qualification(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef planRef, ControlBuild.FileRef resultRef,
            ControlBuild.FileRef intentRef, ControlBuild.FileRef launchObservationRef,
            ControlBuild.FileRef helperReceiptRef, NativeProjectExeUac.ReceiptQualification receipt,
            List<NativeProjectExeUac.SelectedExecutable> executables) {
        public Qualification { executables = List.copyOf(executables); }
    }

    /**
     * Revalidates original completed bytes and native input identities. Expired cards remain readable
     * as historical evidence; this method neither renews their deadline nor grants a new launch.
     */
    public static Qualification readVerified(Path planPath, String rootReviewedPlanSha256,
            String actualSharedStageDeadlineUtc, ControlBuild.FileRef resultRef) throws IOException {
        Objects.requireNonNull(planPath); Objects.requireNonNull(resultRef);
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(planPath.toRealPath());
        NativeProjectExeUac.requireReviewedPlan(planRef, rootReviewedPlanSha256);
        NativeProjectExeUac.Plan plan = NativeProjectExeUac.parsePlan(read(planRef));
        NativeProjectExeUac.requireSharedStageDeadline(plan.deadlineAtUtc(), actualSharedStageDeadlineUtc);
        NativeProjectExeUac.validateCompletedInputs(plan);
        require(samePath(resultRef.path(), plan.resultPath()), "result is outside the reviewed exact output path");
        NativeProjectExeUac.Result result = JSON.readValue(read(resultRef), NativeProjectExeUac.Result.class);
        require(result.review() != null, "original completed review missing");
        NativeProjectExeUac.Review review = NativeProjectExeUac.completedReview(plan, planRef, result.review().observedAtUtc());
        ControlBuild.FileRef intentRef = measure(plan.intentPath());
        ControlBuild.FileRef launchRef = measure(plan.launchObservationPath());
        NativeProjectExeUac.Intent intent = JSON.readValue(read(intentRef), NativeProjectExeUac.Intent.class);
        NativeProjectExeUac.LaunchObservation launch = JSON.readValue(read(launchRef), NativeProjectExeUac.LaunchObservation.class);
        require(result.helperReceiptRef() != null && samePath(result.helperReceiptRef().path(), plan.helperReceiptPath()),
                "original helper receipt path differs from reviewed plan");
        ControlBuild.FileRef receiptRef = result.helperReceiptRef();
        byte[] receiptBytes = read(receiptRef);
        List<ControlBuild.FileRef> inputs = NativeProjectExeUac.inputs(plan, planRef);
        requireGuards(intent.guardedInputs(), inputs);
        NativeProjectExeUac.ReceiptExpectation expected = NativeProjectExeUac.receiptExpectation(plan.nativeBuildRoot(),
                JSON.readTree(read(plan.manifestRef())));
        NativeProjectExeUac.ReceiptQualification receipt = qualifyEvidence(plan.observedAtUtc(), plan.deadlineAtUtc(),
                review, intent, launch, result, expected, receiptBytes, receiptRef);
        for (ControlBuild.FileRef ref : List.of(planRef, resultRef, intentRef, launchRef, receiptRef)) ref.verify();
        NativeProjectExeUac.verifySourceRefs(inputs);
        requireGuards(intent.guardedInputs(), inputs);
        return new Qualification("xar.project-exe-registration-qualification/v1", MACHINE, Instant.now().toString(),
                planRef, resultRef, intentRef, launchRef, receiptRef, receipt, plan.executables());
    }

    /** Pure production boundary shared by the file reader and synthetic regression. */
    public static NativeProjectExeUac.ReceiptQualification qualifyEvidence(String planObservedAtUtc, String deadlineAtUtc,
            NativeProjectExeUac.Review expectedReview, NativeProjectExeUac.Intent intent,
            NativeProjectExeUac.LaunchObservation launch, NativeProjectExeUac.Result result,
            NativeProjectExeUac.ReceiptExpectation expectedReceipt, byte[] rawReceipt,
            ControlBuild.FileRef receiptRef) throws IOException {
        require(expectedReview != null && intent != null && launch != null && result != null, "complete causal registration evidence required");
        require("xar.exact-two-exe-uac-result/v4".equals(result.schema()) && MACHINE.equals(result.machineId())
                && result.status() == NativeProjectExeUac.Status.VERIFIED
                && result.proofScope() == NativeProjectExeUac.ProofScope.DIRECT_ADMIN_EXCLUSION_PATH,
                "verified current result with direct-admin proof scope required");
        require("xar.exact-two-exe-uac-review/v2".equals(expectedReview.schema()) && MACHINE.equals(expectedReview.machineId())
                && expectedReview.equals(result.review()) && expectedReview.equals(intent.review()),
                "intent/result differs from original reviewed plan and command");
        require(expectedReceipt != null && expectedReceipt.nativeBuildRoot().equals(expectedReview.nativeBuildRoot())
                && expectedReceipt.manifestSemanticSha256().equals(expectedReview.manifestSemanticSha256()),
                "original reviewed build root and receipt source disagree");
        require("xar.exact-two-exe-uac-intent/v2".equals(intent.schema()) && MACHINE.equals(intent.machineId())
                && intent.guardedInputs() != null && !intent.guardedInputs().isEmpty()
                && intent.unresolvedActionPolicy() != null && !intent.unresolvedActionPolicy().isBlank(), "original one-shot guarded intent required");
        require("xar.exact-two-exe-uac-launch/v1".equals(launch.schema()) && MACHINE.equals(launch.machineId())
                && launch.shellAcknowledged() && Boolean.TRUE.equals(launch.tokenElevated()) && launch.processIdentity() != null,
                "original elevated launch observation required");
        require(result.launchCallEntered() && result.shellAcknowledged() && result.launchWin32Error() == null
                && Boolean.TRUE.equals(result.tokenElevated()) && !result.waitTimedOut()
                && !result.automaticallyRetried() && !result.processTerminated() && result.diagnostics() != null && result.diagnostics().isEmpty()
                && result.processIdentity() != null && launch.processIdentity().equals(result.processIdentity())
                && receiptRef.equals(result.helperReceiptRef()), "result launch/process/receipt provenance inconsistent");
        NativeProjectExeUac.TerminalProof terminal = result.terminalProof();
        require(terminal != null && terminal.shellAcknowledged() == result.shellAcknowledged()
                && Objects.equals(terminal.processIdentity(), result.processIdentity())
                && Objects.equals(terminal.tokenElevated(), result.tokenElevated())
                && Objects.equals(terminal.processExitCodeDecimal(), result.processExitCodeDecimal())
                && terminal.timedOut() == result.waitTimedOut(), "native terminal proof disagrees with persisted result");
        Instant planTime = instant(planObservedAtUtc), reviewTime = instant(expectedReview.observedAtUtc());
        Instant intentTime = instant(intent.observedAtUtc()), launchTime = instant(launch.observedAtUtc());
        Instant resultTime = instant(result.observedAtUtc()), deadline = instant(deadlineAtUtc);
        require(!reviewTime.isBefore(planTime) && !intentTime.isBefore(reviewTime) && !launchTime.isBefore(intentTime)
                && !resultTime.isBefore(launchTime) && resultTime.isBefore(deadline), "registration evidence chronology exceeds original deadline");
        return NativeProjectExeUac.qualifyCompletion(terminal, expectedReview.lpFile(), expectedReceipt, rawReceipt, receiptRef);
    }

    private static void requireGuards(List<NativeProjectExeUac.GuardedInput> observed,
            List<ControlBuild.FileRef> inputs) throws IOException {
        require(observed != null && observed.size() == inputs.size(), "intent lacks complete actual input identity closure");
        Set<String> paths = new HashSet<>();
        Map<String, NativeProjectExeUac.GuardedInput> current = new LinkedHashMap<>();
        for (ControlBuild.FileRef ref : inputs) {
            NativeProjectExeUac.GuardedInput value = NativeProjectExeUac.probeNativeInput(ref);
            require(current.putIfAbsent(key(value.requestedPath()), value) == null, "duplicate current input identity");
        }
        for (NativeProjectExeUac.GuardedInput guard : observed) {
            require(guard != null && guard.identity() != null && paths.add(key(guard.requestedPath())), "duplicate or missing intent input identity");
            NativeProjectExeUac.GuardedInput now = current.get(key(guard.requestedPath()));
            require(now != null && guard.identity().equals(now.identity()), "current input differs from original intent native file identity");
        }
    }

    private static ControlBuild.FileRef measure(String path) throws IOException {
        require(path != null && Files.isRegularFile(Path.of(path), LinkOption.NOFOLLOW_LINKS), "original evidence file missing or reparse");
        return ControlBuild.FileRef.measure(Path.of(path).toRealPath());
    }
    private static byte[] read(ControlBuild.FileRef ref) throws IOException {
        require(ref.bytes() > 0 && ref.bytes() <= LIMIT && Files.isRegularFile(Path.of(ref.path()), LinkOption.NOFOLLOW_LINKS), "bounded original evidence file required");
        ref.verify(); byte[] bytes = Files.readAllBytes(Path.of(ref.path()));
        require(bytes.length == ref.bytes() && NativeProjectExeUac.sha(bytes).equals(ref.sha256()), "evidence byte pin changed during read");
        return bytes;
    }
    private static boolean samePath(String left, String right) { return key(left).equals(key(right)); }
    private static String key(String value) { return Path.of(value).toAbsolutePath().normalize().toString().toLowerCase(java.util.Locale.ROOT); }
    private static Instant instant(String value) throws IOException {
        try { return Instant.parse(value); } catch (RuntimeException malformed) { throw new IOException("valid original UTC timestamp required", malformed); }
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
