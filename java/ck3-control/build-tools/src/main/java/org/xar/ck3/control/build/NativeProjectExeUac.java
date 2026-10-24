package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.platform.win32.Advapi32;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.Ole32;
import com.sun.jna.platform.win32.Shell32;
import com.sun.jna.platform.win32.ShellAPI;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

/**
 * One finite, exact two-target adapter to the existing administrator helper.
 * No broker installation, WMI implementation, Task.Run, PowerShell, process termination,
 * automatic retry, Game/Driver/SAVE access, or native fixture execution is implemented.
 * Runtime admission and compilation qualification must precede either CLI command.
 */
public final class NativeProjectExeUac {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final Path REPO = Path.of("Z:/ck3_mod_rewrite");
    private static final Path WORK = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1");
    private static final Set<String> ALLOWED_BUILD_NAMES = Set.of("native-prisoners-combat04", "native-prisoners-combat05");
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final List<String> TARGETS = List.of("ck3_12003_prisoner_native_kinship_test",
            "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test");
    private static final int WAIT_SECONDS = 190;
    private static final int REGISTER_TOTAL_SECONDS = 240;
    private static final int LIMIT = 1 << 20;
    private static final int WAIT_TIMEOUT = 258;

    private NativeProjectExeUac() { }

    public enum Status { VERIFIED, CANCELLED, LAUNCH_REJECTED, SETTINGS_FAILED, UNKNOWN }
    public enum ProofScope { DIRECT_ADMIN_EXCLUSION_PATH }
    public record SelectedExecutable(String target, ControlBuild.FileRef fileRef) { }
    public record NativeBuildRoot(String path) {
        public NativeBuildRoot {
            if (path == null || !Path.of(path).isAbsolute()) throw new IllegalArgumentException("explicit actual native build root required");
            Path root = Path.of(path).toAbsolutePath().normalize();
            if (!Path.of(path).equals(root)) throw new IllegalArgumentException("canonical native build root required");
            if (!WORK.resolve("build").equals(root.getParent()) || !ALLOWED_BUILD_NAMES.contains(root.getFileName().toString()))
                throw new IllegalArgumentException("native root lies outside the two explicitly named task candidates");
            path = root.toString();
        }
        public Path root() { return Path.of(path); }
    }
    public record Plan(String schema, String machineId, String observedAtUtc, String deadlineAtUtc,
            String owner, int waitSeconds, NativeBuildRoot nativeBuildRoot, ControlBuild.FileRef resourceCardRef,
            ControlBuild.FileRef manifestRef, ControlBuild.FileRef buildActualRef,
            ControlBuild.FileRef dependencyRef, ControlBuild.FileRef pythonRef,
            ControlBuild.FileRef helperRef, List<ControlBuild.FileRef> sourceRefs,
            List<SelectedExecutable> executables, String outputRoot, String helperReceiptPath,
            String intentPath, String launchObservationPath, String resultPath) {
        public Plan {
            sourceRefs = List.copyOf(sourceRefs); executables = List.copyOf(executables);
            Objects.requireNonNull(nativeBuildRoot);
            Objects.requireNonNull(resourceCardRef); Objects.requireNonNull(manifestRef);
            Objects.requireNonNull(buildActualRef); Objects.requireNonNull(dependencyRef);
            Objects.requireNonNull(pythonRef); Objects.requireNonNull(helperRef);
        }
    }
    public record NativeFileIdentity(String volumeSerialDecimal, String fileIdDecimal,
            String sizeDecimal, String nativeFinalPath, boolean directory) { }
    public record GuardedInput(String requestedPath, NativeFileIdentity identity) { }
    public record ProcessIdentity(String pidDecimal, String creationFiletimeDecimal, String executable) {
        public ProcessIdentity {
            canonicalUnsigned(pidDecimal, 32, true, "PID");
            canonicalUnsigned(creationFiletimeDecimal, 64, true, "process birth FILETIME");
            if (executable == null || !Path.of(executable).isAbsolute()) throw new IllegalArgumentException("absolute actual process image required");
        }
    }
    public record ManifestFile(String path, long size, String sha256, String target, String targetId) {
        public ManifestFile {
            if (path == null || !Path.of(path).isAbsolute() || size < 1 || sha256 == null || !sha256.matches("[0-9a-f]{64}")
                    || !TARGETS.contains(target) || targetId == null || targetId.isBlank()) throw new IllegalArgumentException("exact typed selected EXE row required");
            Path executable = Path.of(path).toAbsolutePath().normalize();
            if (executable.getParent() == null || executable.getParent().getFileName() == null
                    || !executable.getFileName().toString().equals(target + ".exe") || !executable.getParent().getFileName().toString().equals("bin"))
                throw new IllegalArgumentException("foreign EXE filename or artifact directory rejected");
            new NativeBuildRoot(executable.getParent().getParent().toString());
        }
    }
    public record ReceiptExpectation(NativeBuildRoot nativeBuildRoot, String manifestSemanticSha256, List<ManifestFile> files) {
        public ReceiptExpectation {
            Objects.requireNonNull(nativeBuildRoot);
            files = List.copyOf(files);
            if (manifestSemanticSha256 == null || !manifestSemanticSha256.matches("[0-9a-f]{64}") || files.size() != 2
                    || !new HashSet<>(files.stream().map(ManifestFile::target).toList()).equals(new HashSet<>(TARGETS)))
                throw new IllegalArgumentException("exact double-target receipt expectation required");
            for (ManifestFile file : files) {
                if (!normalizedPath(file.path()).equals(normalizedPath(nativeBuildRoot.root().resolve("bin/" + file.target() + ".exe").toString())))
                    throw new IllegalArgumentException("receipt expectation mixed or changed native build root");
            }
        }
    }
    public record TerminalProof(boolean shellAcknowledged, ProcessIdentity processIdentity, Boolean tokenElevated,
            boolean nativeSignalled, boolean timedOut, String processExitCodeDecimal) { }
    public record ReceiptQualification(String rawSha256, long rawBytes, ProcessIdentity processIdentity, ProofScope proofScope) { }
    public record RegisterCardExpectation(String owner, NativeBuildRoot nativeBuildRoot, Path outputRoot, Instant deadlineAtUtc) {
        public RegisterCardExpectation {
            if (!"/root/native_fixture09".equals(owner)) throw new IllegalArgumentException("current unique native owner required");
            Objects.requireNonNull(nativeBuildRoot); Objects.requireNonNull(deadlineAtUtc); Objects.requireNonNull(outputRoot);
            if (!outputRoot.isAbsolute() || !outputRoot.equals(outputRoot.toAbsolutePath().normalize()))
                throw new IllegalArgumentException("canonical absolute card output root required");
        }
    }
    public record Review(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef planRef, ControlBuild.FileRef resourceCardRef,
            ControlBuild.FileRef manifestRef, NativeBuildRoot nativeBuildRoot, String manifestSemanticSha256, String lpVerb,
            String lpFile, String lpParameters, String lpDirectory, int nShow,
            int waitSeconds, List<SelectedExecutable> executables) { }
    public record Intent(String schema, String machineId, String observedAtUtc, Review review,
            List<GuardedInput> guardedInputs, String unresolvedActionPolicy) { }
    public record LaunchObservation(String schema, String machineId, String observedAtUtc,
            boolean shellAcknowledged, ProcessIdentity processIdentity, Boolean tokenElevated) { }
    public record Result(String schema, String machineId, String observedAtUtc, Status status, ProofScope proofScope,
            Review review, boolean launchCallEntered, boolean shellAcknowledged,
            Integer launchWin32Error, ProcessIdentity processIdentity, Boolean tokenElevated,
            String processExitCodeDecimal, boolean waitTimedOut, ControlBuild.FileRef helperReceiptRef,
            List<String> diagnostics, boolean automaticallyRetried, boolean processTerminated, TerminalProof terminalProof) {
        public Result { diagnostics = List.copyOf(diagnostics); }
    }

    /** Explicit Windows Unicode API. All libraries resolve to System32, not a user search path. */
    public interface FileKernel32 extends Kernel32 {
        WinNT.HANDLE CreateFileW(WString path, int access, int sharing,
                WinBase.SECURITY_ATTRIBUTES security, int creation, int flags, WinNT.HANDLE template);
        boolean GetFileInformationByHandle(WinNT.HANDLE file, Pointer information);
        int GetFinalPathNameByHandleW(WinNT.HANDLE file, char[] path, int count, int flags);
    }
    private record Apis(FileKernel32 kernel, Shell32 shell, Ole32 ole, Advapi32 security) { }

    /** No mutation, no ShellExecuteEx call. The printed command is the concrete Root review surface. */
    public static Review review(Path planPath) throws IOException {
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(planPath.toRealPath());
        Plan plan = parsePlan(read(planPath, LIMIT));
        validate(plan);
        return completedReview(plan, planRef, Instant.now().toString());
    }

    static Review completedReview(Plan plan, ControlBuild.FileRef planRef, String observedAtUtc) throws IOException {
        JsonNode manifest = tree(Path.of(plan.manifestRef().path()));
        return new Review("xar.exact-two-exe-uac-review/v2", MACHINE, observedAtUtc,
                planRef, plan.resourceCardRef(), plan.manifestRef(), plan.nativeBuildRoot(), semanticSha(manifest), "runas",
                plan.pythonRef().path(), parameters(plan), REPO.toRealPath().toString(), 0,
                WAIT_SECONDS, plan.executables());
    }

    /** One native elevation attempt; an existing intent rejects every replay, including UNKNOWN. */
    public static Result executeReviewed(Path planPath, String reviewedPlanSha256, String actualSharedStageDeadlineUtc) throws IOException {
        Review review = review(planPath);
        requireReviewedPlan(review.planRef(), reviewedPlanSha256);
        Plan plan = parsePlan(read(planPath, LIMIT));
        requireSharedStageDeadline(plan.deadlineAtUtc(), actualSharedStageDeadlineUtc);
        Apis apis = apis();
        List<Guard> guards = new ArrayList<>();
        List<String> diagnostics = new ArrayList<>();
        WinNT.HANDLE child = null;
        ProcessIdentity identity = null;
        Boolean elevated = null;
        Integer win32Error = null;
        String exitCode = null;
        ControlBuild.FileRef receiptRef = null;
        boolean entered = false, acknowledged = false, timedOut = false, comInitialized = false, signalled = false;
        Status status = Status.UNKNOWN;
        boolean intentWritten = false;
        try {
            for (ControlBuild.FileRef ref : inputs(plan, review.planRef())) {
                guards.add(Guard.open(apis.kernel(), ref));
            }
            validate(plan); verifyGuards(guards);
            claimIntent(Path.of(plan.intentPath()), new Intent("xar.exact-two-exe-uac-intent/v2", MACHINE,
                    Instant.now().toString(), review, guards.stream().map(Guard::evidence).toList(),
                    "No automatic resubmission. Timeout/crash/missing receipt requires original process and settings resolution."));
            intentWritten = true;
            int initialized = apis.ole().CoInitializeEx(Pointer.NULL, 0x2 | 0x4).intValue();
            require(initialized == 0 || initialized == 1, "COM STA initialization failed: " + initialized);
            comInitialized = true;
            ShellAPI.SHELLEXECUTEINFO info = new ShellAPI.SHELLEXECUTEINFO();
            info.fMask = 0x40 | 0x100; // NOCLOSEPROCESS + NOASYNC; no message loop and no automatic retry.
            info.lpVerb = "runas"; info.lpFile = review.lpFile(); info.lpParameters = review.lpParameters();
            info.lpDirectory = review.lpDirectory(); info.nShow = 0; // SW_HIDE; Windows UAC remains native.
            require(Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc())), "lease expired before launch");
            long started = System.nanoTime();
            entered = true;
            acknowledged = apis.shell().ShellExecuteEx(info);
            if (!acknowledged) {
                win32Error = Native.getLastError();
                status = win32Error == 1223 ? Status.CANCELLED : Status.LAUNCH_REJECTED;
            } else {
                child = info.hProcess;
                require(valid(child), "Shell ACK supplied no actual process handle; result remains UNKNOWN");
                identity = identity(apis.kernel(), child);
                require(Path.of(identity.executable()).toRealPath().equals(Path.of(plan.pythonRef().path()).toRealPath()),
                        "native child image differs from approved interpreter");
                elevated = tokenElevated(apis, child);
                require(elevated, "native child token is not elevated");
                writeNew(Path.of(plan.launchObservationPath()), new LaunchObservation(
                        "xar.exact-two-exe-uac-launch/v1", MACHINE, Instant.now().toString(), true, identity, elevated));
                long bound = Duration.ofSeconds(WAIT_SECONDS).toNanos();
                while (true) {
                    int state = apis.kernel().WaitForSingleObject(child, 0);
                    if (state == 0) break;
                    require(state == WAIT_TIMEOUT, "native process wait failed: " + state);
                    if (System.nanoTime() - started >= bound || !Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc()))) {
                        timedOut = true; break;
                    }
                    state = apis.kernel().WaitForSingleObject(child, 250);
                    require(state == 0 || state == WAIT_TIMEOUT, "native bounded process wait failed: " + state);
                }
                if (timedOut) {
                    diagnostics.add("Elevated child may still be live. No kill and no resubmission; retain original identity and receipt path.");
                } else {
                    signalled = true;
                    IntByReference code = new IntByReference();
                    require(apis.kernel().GetExitCodeProcess(child, code), "native child exit unavailable");
                    exitCode = Integer.toUnsignedString(code.getValue());
                    verifySourceRefs(inputs(plan, review.planRef()));
                    verifyGuards(guards);
                    Path receipt = Path.of(plan.helperReceiptPath());
                    require(Files.isRegularFile(receipt, LinkOption.NOFOLLOW_LINKS), "fresh administrator receipt missing");
                    require(Files.size(receipt) <= LIMIT, "administrator receipt exceeded approved byte ceiling");
                    receiptRef = ControlBuild.FileRef.measure(receipt.toRealPath());
                    byte[] rawBytes = read(receipt, LIMIT);
                    JsonNode raw = object(JSON.readTree(rawBytes));
                    if (code.getValue() != 0 || !"verified".equals(text(raw, "status"))) {
                        status = Status.SETTINGS_FAILED;
                    } else {
                        qualifyCompletion(new TerminalProof(acknowledged, identity, elevated, true, false, exitCode),
                                plan.pythonRef().path(), receiptExpectation(plan.nativeBuildRoot(), tree(Path.of(plan.manifestRef().path()))), rawBytes, receiptRef);
                        receiptRef.verify();
                        require(Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc())), "terminal arrived outside lease");
                        status = Status.VERIFIED;
                    }
                }
            }
        } catch (IOException | RuntimeException failure) {
            diagnostics.add(failure.getClass().getName() + ": " + failure.getMessage());
            status = Status.UNKNOWN;
        } finally {
            if (valid(child) && !apis.kernel().CloseHandle(child)) {
                diagnostics.add("native child handle close failed: " + Native.getLastError()); status = Status.UNKNOWN;
            }
            if (comInitialized) apis.ole().CoUninitialize();
            for (int i = guards.size() - 1; i >= 0; i--) {
                try { guards.get(i).close(); }
                catch (IOException failure) { diagnostics.add(failure.getMessage()); status = Status.UNKNOWN; }
            }
        }
        Result result = new Result("xar.exact-two-exe-uac-result/v4", MACHINE, Instant.now().toString(), status,
                status == Status.VERIFIED ? ProofScope.DIRECT_ADMIN_EXCLUSION_PATH : null, review, entered, acknowledged, win32Error, identity, elevated, exitCode, timedOut,
                receiptRef, List.copyOf(diagnostics), false, false,
                new TerminalProof(acknowledged, identity, elevated, signalled, timedOut, exitCode));
        if (intentWritten) writeNew(Path.of(plan.resultPath()), result);
        else throw new IOException("No UAC submitted; append-only intent could not be established: " + diagnostics);
        return result;
    }

    private static void validate(Plan plan) throws IOException {
        validateCompletedInputs(plan);
        Instant now = Instant.now(), observed = Instant.parse(plan.observedAtUtc()), deadline = Instant.parse(plan.deadlineAtUtc());
        require(!observed.isAfter(now) && Duration.between(observed, now).compareTo(Duration.ofMinutes(5)) <= 0
                && Duration.between(now, deadline).compareTo(Duration.ofSeconds(WAIT_SECONDS)) >= 0,
                "fresh plan and full remaining stage deadline required");
        for (String name : List.of(plan.helperReceiptPath(), plan.intentPath(), plan.launchObservationPath(), plan.resultPath()))
            require(!Files.exists(Path.of(name), LinkOption.NOFOLLOW_LINKS), "registration outputs must be fresh");
    }

    /** Read-only revalidation after completion; does not renew a plan or permit another launch. */
    static void validateCompletedInputs(Plan plan) throws IOException {
        require("xar.exact-two-exe-uac-plan/v2".equals(plan.schema()) && MACHINE.equals(plan.machineId())
                && MACHINE.equals(WindowsJobProcess.currentMachineId()), "schema/current machine mismatch");
        require("/root/native_fixture09".equals(plan.owner()) && plan.waitSeconds() == WAIT_SECONDS,
                "finite unique native owner and typed 190-second inner budget required");
        Instant deadline = Instant.parse(plan.deadlineAtUtc());
        require(plan.executables().size() == 2 && !plan.sourceRefs().isEmpty() && plan.sourceRefs().size() <= 4096, "exactly two EXEs and bounded nonempty caller closure required");
        require(Path.of(plan.helperRef().path()).toRealPath().equals(REPO.resolve("tools/register_project_exe_exclusions.py").toRealPath())
                && Path.of(plan.pythonRef().path()).toRealPath().equals(REPO.resolve("tools/.venv/Scripts/python.exe").toRealPath()),
                "only current repository helper and interpreter permitted");
        verifySourceRefs(inputs(plan, null));
        Path output = Path.of(plan.outputRoot()).toRealPath();
        require(output.startsWith(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")), "approved task output root required");
        Set<Path> uniqueOutputs = new HashSet<>();
        for (String name : List.of(plan.helperReceiptPath(), plan.intentPath(), plan.launchObservationPath(), plan.resultPath())) {
            Path p = Path.of(name).toAbsolutePath().normalize();
            require(p.getParent().toRealPath().equals(output) && uniqueOutputs.add(p),
                    "every output must be distinct and directly inside the exact admitted output root");
        }
        JsonNode card = tree(Path.of(plan.resourceCardRef().path()));
        qualifyRegisterCard(card, new RegisterCardExpectation(plan.owner(), plan.nativeBuildRoot(), output, deadline));
        JsonNode actual = tree(Path.of(plan.buildActualRef().path()));
        qualifyBuildActual(actual);
        JsonNode dependencies = tree(Path.of(plan.dependencyRef().path()));
        require("xar.native-actual-compiler-dependencies/v1".equals(text(dependencies, "schema"))
                && MACHINE.equals(text(dependencies, "machine_id")), "actual current compiler dependencies required");
        JsonNode manifest = tree(Path.of(plan.manifestRef().path()));
        require(keys(manifest).equals(Set.of("schema", "repo", "source_dir", "build_dir", "configuration", "requested_targets",
                "external_candidate", "cmake_index", "cmake_codemodel", "target_provenance", "files")), "exact CMake helper manifest schema required");
        require("xar.project-exe-exclusions.v1".equals(text(manifest, "schema"))
                && Path.of(text(manifest, "repo")).toRealPath().equals(REPO.toRealPath())
                && Path.of(text(manifest, "source_dir")).toRealPath().equals(REPO.resolve("ck3_autonomous_player/native_bridge").toRealPath())
                && Path.of(text(manifest, "build_dir")).toRealPath().equals(plan.nativeBuildRoot().root().toRealPath())
                && "Release".equals(text(manifest, "configuration")) && strings(manifest.get("requested_targets")).equals(TARGETS)
                && manifest.get("external_candidate").isNull(), "only the two current project targets and one explicit actual native root allowed");
        JsonNode codemodel = tree(Path.of(text(object(manifest.get("cmake_codemodel")), "path")));
        require(Path.of(text(object(codemodel.get("paths")), "build")).toRealPath().equals(plan.nativeBuildRoot().root().toRealPath()),
                "actual codemodel build root differs from the reviewed Plan root");
        JsonNode files = array(manifest.get("files")); require(files.size() == 2, "no extra EXE permitted");
        Set<String> observedTargets = new HashSet<>();
        for (SelectedExecutable selected : plan.executables()) {
            require(TARGETS.contains(selected.target()) && observedTargets.add(selected.target()), "duplicate or foreign selected target");
            Path expected = plan.nativeBuildRoot().root().resolve("bin/" + selected.target() + ".exe").toRealPath();
            require(Path.of(selected.fileRef().path()).toRealPath().equals(expected), "exact configured EXE path required");
            JsonNode matching = null;
            for (JsonNode row : files) if (selected.target().equals(text(row, "target"))) { require(matching == null, "duplicate manifest target"); matching = row; }
            require(matching != null && ref(matching, "size").equals(selected.fileRef()), "manifest/approved current EXE pins differ");
            boolean built = false;
            for (JsonNode row : array(actual.get("output_refs"))) if (ref(row, "bytes").equals(selected.fileRef())) built = true;
            require(built, "EXE absent from real accepted build outputs");
        }
    }

    /** Shared v2 producer contract; cleanup Job0 cannot qualify as a naturally successful build. */
    public static WindowsJobProcess.CommandResult qualifyBuildActual(JsonNode actual) throws IOException {
        require("xar.shared-native-stage-actual/v2".equals(text(actual, "schema"))
                && MACHINE.equals(text(actual, "machine_id")) && "two-target-build".equals(text(actual, "stage_id"))
                && "PASS".equals(text(actual, "status")) && bool(actual, "source_unchanged")
                && actual.has("error") && actual.get("error").isNull(), "actual current successful double-target build required");
        Instant.parse(text(actual, "stage_deadline_at_utc"));
        WindowsJobProcess.CommandResult terminal = JSON.treeToValue(object(actual.get("result")), WindowsJobProcess.CommandResult.class);
        WindowsJobProcess.ProcessIdentity owner = JSON.treeToValue(object(actual.get("owner_identity")), WindowsJobProcess.ProcessIdentity.class);
        NativeLifecycleTerminal.Assessment lifecycle = JSON.treeToValue(object(actual.get("lifecycle")), NativeLifecycleTerminal.Assessment.class);
        require(owner.equals(terminal.identity()) && lifecycle.equals(NativeLifecycleTerminal.assess(terminal)) && lifecycle.successful(),
                "actual build owner and naturally successful shared lifecycle required");
        return terminal;
    }

    /** The native consumer passes its actual Context deadline, never an independently renewed budget. */
    public static void requireSharedStageDeadline(String planDeadlineUtc, String actualStageDeadlineUtc) throws IOException {
        require(planDeadlineUtc != null && actualStageDeadlineUtc != null
                && Instant.parse(planDeadlineUtc).equals(Instant.parse(actualStageDeadlineUtc)),
                "reviewed Plan and actual shared native stage absolute deadline differ");
    }

    /** Single production card admission gate; synthetic software tests do not grant an actual card. */
    public static void qualifyRegisterCard(JsonNode card, RegisterCardExpectation expected) throws IOException {
        Objects.requireNonNull(expected);
        require("xar.shared-native-stage-resource-card/v1".equals(text(card, "schema"))
                && MACHINE.equals(text(card, "machine_id")) && expected.owner().equals(text(card, "owner"))
                && "REGISTER".equals(text(card, "allowed_stage")) && "ADMITTED_SINGLE_STAGE".equals(text(card, "status"))
                && integer(card, "timeout_seconds") == REGISTER_TOTAL_SECONDS
                && !expected.deadlineAtUtc().isAfter(Instant.parse(text(card, "review_at_utc"))),
                "current exact REGISTER resource card and owner required");
        List<Path> roots = strings(card.get("output_roots")).stream().map(Path::of).map(Path::toAbsolutePath).map(Path::normalize).toList();
        require(roots.stream().anyMatch(expected.outputRoot()::startsWith), "UAC output root outside REGISTER card");
        require(roots.stream().anyMatch(expected.nativeBuildRoot().root()::startsWith), "actual native build root outside current REGISTER card");
    }

    /** Production decoder; malformed JSON never constructs an executable plan. */
    public static Plan parsePlan(byte[] raw) throws IOException { require(raw != null && raw.length > 0 && raw.length <= LIMIT, "bounded plan bytes required"); return JSON.readValue(raw, Plan.class); }

    public static void requireReviewedPlan(ControlBuild.FileRef actualPlan, String reviewedSha256) throws IOException {
        require(reviewedSha256 != null && reviewedSha256.matches("[0-9a-f]{64}") && actualPlan.sha256().equals(reviewedSha256), "Root-reviewed plan bytes changed");
    }

    public static void verifySourceRefs(List<ControlBuild.FileRef> refs) throws IOException {
        require(refs != null && !refs.isEmpty(), "nonempty production source closure required");
        for (ControlBuild.FileRef ref : refs) ref.verify();
    }

    /** One-shot production filesystem claim. UNKNOWN is deliberately not a replacement permission. */
    static void claimIntent(Path path, Intent intent) throws IOException { writeNew(path, intent); }

    /** Pure production receipt expectation; this does not qualify source or authorize an action. */
    public static ReceiptExpectation receiptExpectation(NativeBuildRoot buildRoot, JsonNode manifest) throws IOException {
        List<ManifestFile> rows = new ArrayList<>();
        for (JsonNode row : array(object(manifest).get("files"))) rows.add(JSON.treeToValue(row, ManifestFile.class));
        return new ReceiptExpectation(buildRoot, semanticSha(manifest), rows);
    }

    /** Pure final production gate, also used by synthetic regressions; ACK alone cannot reach VERIFIED. */
    public static ReceiptQualification qualifyCompletion(TerminalProof terminal, String expectedInterpreter,
            ReceiptExpectation expectation, byte[] rawReceipt, ControlBuild.FileRef rawPin) throws IOException {
        require(terminal != null && terminal.shellAcknowledged() && terminal.processIdentity() != null
                && Boolean.TRUE.equals(terminal.tokenElevated()) && terminal.nativeSignalled() && !terminal.timedOut()
                && "0".equals(terminal.processExitCodeDecimal()), "actual elevated signalled child with exit0 required");
        require(normalizedPath(terminal.processIdentity().executable()).equals(normalizedPath(expectedInterpreter)), "actual child image differs from approved interpreter");
        require(rawReceipt != null && rawReceipt.length > 0 && rawReceipt.length <= LIMIT && rawPin != null
                && rawReceipt.length == rawPin.bytes() && sha(rawReceipt).equals(rawPin.sha256()), "original receipt bytes/pin changed after child exit");
        JsonNode receipt = object(JSON.readTree(rawReceipt));
        require("verified".equals(text(receipt, "status")), "actual helper receipt is not verified");
        validateReceipt(expectation, receipt);
        return new ReceiptQualification(rawPin.sha256(), rawPin.bytes(), terminal.processIdentity(), ProofScope.DIRECT_ADMIN_EXCLUSION_PATH);
    }

    private static void validateReceipt(ReceiptExpectation expectation, JsonNode receipt) throws IOException {
        require("xar.project-exe-exclusions.v1".equals(text(receipt, "schema")) && bool(receipt, "admin_token")
                && !receipt.has("broker_schema") && !bool(receipt, "settings_success_is_runtime_trust")
                && expectation.manifestSemanticSha256().equals(text(receipt, "manifest_sha256")), "direct same-admin receipt/source binding rejected");
        List<ManifestFile> observedFiles = new ArrayList<>();
        for (JsonNode row : array(receipt.get("files"))) observedFiles.add(JSON.treeToValue(row, ManifestFile.class));
        require(observedFiles.equals(expectation.files()), "receipt EXE rows changed");
        Set<String> before = pathSet(strings(receipt.get("before"))), after = pathSet(strings(receipt.get("after")));
        List<String> requested = new ArrayList<>();
        for (JsonNode row : array(receipt.get("files"))) requested.add(text(row, "path"));
        require(after.containsAll(before) && after.containsAll(pathSet(requested))
                && strings(receipt.get("verified_requested_paths")).equals(requested)
                && strings(receipt.get("missing_requested_paths")).isEmpty()
                && bool(receipt, "observed_prior_settings_preserved") && !bool(receipt, "partial_mutation"),
                "actual fresh before/after readback lacks exact paths or prior-path preservation");
    }

    static List<ControlBuild.FileRef> inputs(Plan p, ControlBuild.FileRef planRef) throws IOException {
        List<ControlBuild.FileRef> refs = new ArrayList<>(p.sourceRefs());
        refs.addAll(List.of(p.resourceCardRef(), p.manifestRef(), p.buildActualRef(), p.dependencyRef(), p.pythonRef(), p.helperRef()));
        p.executables().forEach(exe -> refs.add(exe.fileRef())); if (planRef != null) refs.add(planRef);
        JsonNode actual = tree(Path.of(p.buildActualRef().path()));
        ControlBuild.FileRef sourceManifest = ref(object(actual.get("source_manifest_ref")), "bytes");
        refs.add(sourceManifest);
        refs.add(ref(object(actual.get("configured_graph_ref")), "bytes"));
        JsonNode source = tree(Path.of(sourceManifest.path()));
        require("xar.native-stage-source-manifest/v1".equals(text(source, "schema"))
                && MACHINE.equals(text(source, "machine_id")), "actual native source manifest binding required");
        for (String field : List.of("source_refs", "tool_refs", "operation_runtime_refs")) {
            for (JsonNode row : array(source.get(field))) refs.add(ref(row, "bytes"));
        }
        for (JsonNode row : array(actual.get("output_refs"))) refs.add(ref(row, "bytes"));
        JsonNode dependencies = tree(Path.of(p.dependencyRef().path()));
        refs.add(ref(object(dependencies.get("raw_ref")), "bytes"));
        JsonNode dependencyRows = array(dependencies.get("dependency_refs"));
        require(!dependencyRows.isEmpty() && dependencyRows.size() <= 12000, "finite actual dependency closure required");
        for (JsonNode row : dependencyRows) refs.add(ref(row, "bytes"));
        JsonNode manifest = tree(Path.of(p.manifestRef().path()));
        List<JsonNode> cmakePins = new ArrayList<>(List.of(object(manifest.get("cmake_index")), object(manifest.get("cmake_codemodel"))));
        for (JsonNode row : array(manifest.get("target_provenance"))) cmakePins.add(row);
        for (JsonNode row : cmakePins) {
            ControlBuild.FileRef measured = ControlBuild.FileRef.measure(Path.of(text(row, "path")).toRealPath());
            require(measured.sha256().equals(text(row, "sha256")), "current CMake provenance bytes differ");
            refs.add(measured);
        }
        require(refs.size() <= 16384, "finite combined source/dependency/native input closure exceeded");
        LinkedHashMap<String, ControlBuild.FileRef> unique = new LinkedHashMap<>();
        for (ControlBuild.FileRef ref : refs) {
            ControlBuild.FileRef prior = unique.putIfAbsent(Path.of(ref.path()).toAbsolutePath().normalize().toString().toLowerCase(java.util.Locale.ROOT), ref);
            if (prior != null && !prior.equals(ref)) throw new IllegalArgumentException("conflicting input pin");
        }
        return List.copyOf(unique.values());
    }

    private static final class Guard implements AutoCloseable {
        private final FileKernel32 kernel; private final ControlBuild.FileRef ref; private final WinNT.HANDLE handle;
        private final NativeFileIdentity original;
        private Guard(FileKernel32 kernel, ControlBuild.FileRef ref, WinNT.HANDLE handle, NativeFileIdentity original) {
            this.kernel = kernel; this.ref = ref; this.handle = handle; this.original = original;
        }
        static Guard open(FileKernel32 kernel, ControlBuild.FileRef ref) throws IOException {
            Path path = Path.of(ref.path());
            require(path.isAbsolute() && Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "exact non-reparse input file required");
            WinNT.HANDLE handle = kernel.CreateFileW(new WString(path.toString()), WinNT.GENERIC_READ, 1, null, 3, 0x00200000, null);
            require(valid(handle), "read-only native input lease failed: " + Native.getLastError());
            try {
                NativeFileIdentity identity = fileIdentity(kernel, handle);
                require(!identity.directory(), "input is directory"); ref.verify();
                return new Guard(kernel, ref, handle, identity);
            } catch (IOException | RuntimeException failure) { kernel.CloseHandle(handle); throw failure; }
        }
        GuardedInput evidence() { return new GuardedInput(ref.path(), original); }
        void verify() throws IOException {
            ref.verify(); require(original.equals(fileIdentity(kernel, handle)), "held input native identity drift");
            try (Guard fresh = open(kernel, ref)) { require(original.equals(fresh.original), "input path rebound during UAC"); }
        }
        @Override public void close() throws IOException { require(kernel.CloseHandle(handle), "native input lease close failed"); }
    }
    private static NativeFileIdentity fileIdentity(FileKernel32 kernel, WinNT.HANDLE file) throws IOException {
        try (Memory info = new Memory(52)) { // Windows BY_HANDLE_FILE_INFORMATION: 13 DWORDs.
            require(kernel.GetFileInformationByHandle(file, info), "native file identity unavailable");
            int attributes = info.getInt(0); require((attributes & 0x400) == 0, "reparse input rejected");
            char[] path = new char[32768]; int count = kernel.GetFinalPathNameByHandleW(file, path, path.length, 0);
            require(count > 0 && count < path.length, "complete native final path required");
            return new NativeFileIdentity(Integer.toUnsignedString(info.getInt(28)), uint64(info.getInt(44), info.getInt(48)),
                    uint64(info.getInt(32), info.getInt(36)), new String(path, 0, count), (attributes & 0x10) != 0);
        }
    }
    private static void verifyGuards(List<Guard> guards) throws IOException { for (Guard guard : guards) guard.verify(); }
    /** Read-only native ABI/software probe over an explicitly supplied synthetic fixture. Never launches a process. */
    static GuardedInput probeNativeInput(ControlBuild.FileRef ref) throws IOException {
        try (Guard guard = Guard.open(apis().kernel(), ref)) { guard.verify(); return guard.evidence(); }
    }
    /** Portable read-only software regression of the same Guard implementation; no production stage admission. */
    static GuardedInput probeSoftwareNativeInput(ControlBuild.FileRef ref) throws IOException {
        try (Guard guard = Guard.open(readOnlyApis().kernel(), ref)) { guard.verify(); return guard.evidence(); }
    }
    /** Read the current software-test process token only; no elevation or settings operation. */
    static boolean probeCurrentTokenElevation() throws IOException {
        Apis apis = readOnlyApis(); return tokenElevated(apis, apis.kernel().GetCurrentProcess());
    }
    private static ProcessIdentity identity(Kernel32 kernel, WinNT.HANDLE child) throws IOException {
        WinBase.FILETIME created = new WinBase.FILETIME();
        require(kernel.GetProcessTimes(child, created, new WinBase.FILETIME(), new WinBase.FILETIME(), new WinBase.FILETIME()), "child birth unavailable");
        char[] image = new char[32768]; IntByReference count = new IntByReference(image.length);
        require(kernel.QueryFullProcessImageName(child, 0, image, count), "actual child image unavailable");
        return new ProcessIdentity(Integer.toUnsignedString(kernel.GetProcessId(child)),
                uint64(created.dwHighDateTime, created.dwLowDateTime), new String(image, 0, count.getValue()));
    }
    private static boolean tokenElevated(Apis apis, WinNT.HANDLE child) throws IOException {
        WinNT.HANDLEByReference token = new WinNT.HANDLEByReference();
        require(apis.security().OpenProcessToken(child, 0x8, token), "child token query unavailable");
        try {
            WinNT.TOKEN_ELEVATION value = new WinNT.TOKEN_ELEVATION();
            IntByReference length = new IntByReference();
            require(value.size() == 4 && apis.security().GetTokenInformation(token.getValue(), 20, value, value.size(), length) && length.getValue() == 4,
                    "actual child TokenElevation unavailable");
            value.read(); return value.TokenIsElevated != 0;
        } finally { require(apis.kernel().CloseHandle(token.getValue()), "child token handle close failed"); }
    }
    private static Apis apis() throws IOException {
        String configuredScratch = System.getProperty("jna.tmpdir", "");
        require(!configuredScratch.isBlank() && Path.of(configuredScratch).isAbsolute(), "explicit admitted JNA scratch required");
        Path scratch = Path.of(configuredScratch).toRealPath();
        require(scratch.startsWith(WORK.resolve("scratch").toRealPath()),
                "JNA scratch lies outside this machine's admitted native temporary root");
        return readOnlyApis();
    }
    private static Apis readOnlyApis() throws IOException {
        require(System.getProperty("os.name", "").startsWith("Windows") && Native.POINTER_SIZE == 8 && !Boolean.getBoolean("w32.ascii"), "Windows x64 Unicode API required");
        Path system = Path.of(Objects.requireNonNull(System.getenv("SystemRoot")), "System32");
        return new Apis(Native.load(system.resolve("kernel32.dll").toString(), FileKernel32.class, W32APIOptions.UNICODE_OPTIONS),
                Native.load(system.resolve("shell32.dll").toString(), Shell32.class, W32APIOptions.UNICODE_OPTIONS),
                Native.load(system.resolve("ole32.dll").toString(), Ole32.class, W32APIOptions.UNICODE_OPTIONS),
                Native.load(system.resolve("advapi32.dll").toString(), Advapi32.class, W32APIOptions.UNICODE_OPTIONS));
    }
    private static String parameters(Plan plan) {
        return List.of("-B", "-X", "utf8", plan.helperRef().path(), "--manifest", plan.manifestRef().path(), "--receipt", plan.helperReceiptPath())
                .stream().map(NativeProjectExeUac::quote).reduce((a, b) -> a + " " + b).orElseThrow();
    }
    static String quote(String word) {
        if (word.indexOf('\0') >= 0) throw new IllegalArgumentException("NUL in exact argv");
        StringBuilder out = new StringBuilder("\""); int backslashes = 0;
        for (char ch : word.toCharArray()) {
            if (ch == '\\') { backslashes++; continue; }
            out.append("\\".repeat(backslashes * (ch == '"' ? 2 : 1) + (ch == '"' ? 1 : 0)));
            out.append(ch); backslashes = 0;
        }
        return out.append("\\".repeat(backslashes * 2)).append('"').toString();
    }
    static String semanticSha(JsonNode value) throws IOException {
        return sha(pythonJson(value).getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    /** Exact narrow counterpart of helper json.dumps(manifest, sort_keys=True), including ensure_ascii. */
    private static String pythonJson(JsonNode value) throws IOException {
        if (value.isObject()) {
            List<String> rows = new ArrayList<>(); for (String key : new TreeSet<>(keys(value))) rows.add(asciiJson(key) + ": " + pythonJson(value.get(key)));
            return "{" + String.join(", ", rows) + "}";
        }
        if (value.isArray()) { List<String> rows = new ArrayList<>(); for (JsonNode row : value) rows.add(pythonJson(row)); return "[" + String.join(", ", rows) + "]"; }
        if (value.isTextual()) return asciiJson(value.textValue());
        require(value.isIntegralNumber() || value.isBoolean() || value.isNull(), "manifest outside exact JSON integer domain");
        return value.toString();
    }
    private static String asciiJson(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            switch (c) {
                case '"' -> out.append("\\\""); case '\\' -> out.append("\\\\"); case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f"); case '\n' -> out.append("\\n"); case '\r' -> out.append("\\r"); case '\t' -> out.append("\\t");
                default -> { if (c < 0x20 || c >= 0x7f) out.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int)c)); else out.append(c); }
            }
        }
        return out.append('"').toString();
    }
    private static Set<String> keys(JsonNode value) throws IOException { object(value); Set<String> keys = new HashSet<>(); value.fieldNames().forEachRemaining(keys::add); return Set.copyOf(keys); }
    /** Existing Defender entries can be wildcard/directory/environment strings; preserve rather than interpret them. */
    private static Set<String> pathSet(List<String> paths) {
        Set<String> set = new HashSet<>();
        paths.forEach(p -> set.add(p.replace('/', '\\').toLowerCase(java.util.Locale.ROOT)));
        return Set.copyOf(set);
    }
    private static String normalizedPath(String path) { return Path.of(Objects.requireNonNull(path)).toAbsolutePath().normalize().toString().toLowerCase(java.util.Locale.ROOT); }
    private static void canonicalUnsigned(String value, int bits, boolean positive, String label) {
        if (value == null || !value.matches("0|[1-9][0-9]*")) throw new IllegalArgumentException("canonical decimal " + label + " required");
        BigInteger number = new BigInteger(value);
        if (number.bitLength() > bits || (positive && number.signum() == 0)) throw new IllegalArgumentException(label + " outside unsigned domain");
    }
    static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static ControlBuild.FileRef ref(JsonNode row, String size) throws IOException { return new ControlBuild.FileRef(text(row, "path"), integer(row, size), text(row, "sha256")); }
    private static String uint64(int high, int low) { return BigInteger.valueOf(Integer.toUnsignedLong(high)).shiftLeft(32).or(BigInteger.valueOf(Integer.toUnsignedLong(low))).toString(); }
    private static boolean valid(WinNT.HANDLE handle) { return handle != null && Pointer.nativeValue(handle.getPointer()) != 0 && Pointer.nativeValue(handle.getPointer()) != -1; }
    private static String text(JsonNode node, String field) throws IOException { JsonNode value = object(node).get(field); require(value != null && value.isTextual() && !value.textValue().isBlank(), "string field required: " + field); return value.textValue(); }
    private static long integer(JsonNode node, String field) throws IOException { JsonNode value = object(node).get(field); require(value != null && value.isIntegralNumber() && value.canConvertToLong(), "integer field required: " + field); return value.longValue(); }
    private static boolean bool(JsonNode node, String field) throws IOException { JsonNode value = object(node).get(field); require(value != null && value.isBoolean(), "Boolean field required: " + field); return value.booleanValue(); }
    private static JsonNode object(JsonNode node) throws IOException { require(node != null && node.isObject(), "JSON object required"); return node; }
    private static JsonNode array(JsonNode node) throws IOException { require(node != null && node.isArray(), "JSON array required"); return node; }
    private static List<String> strings(JsonNode node) throws IOException { List<String> result = new ArrayList<>(); for (JsonNode row : array(node)) { require(row.isTextual(), "string array required"); result.add(row.textValue()); } return List.copyOf(result); }
    private static JsonNode tree(Path path) throws IOException { return object(JSON.readTree(read(path, LIMIT))); }
    private static byte[] read(Path path, long limit) throws IOException { require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) <= limit, "bounded regular JSON file required: " + path); return Files.readAllBytes(path); }
    private static void writeNew(Path path, Object value) throws IOException { Files.write(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE); }
    private static void require(boolean value, String message) throws IOException { if (!value) throw new IOException(message); }

    public static void main(String[] args) throws IOException {
        if (args.length == 2 && args[0].equals("review")) System.out.println(JSON.writeValueAsString(review(Path.of(args[1]))));
        else if (args.length == 4 && args[0].equals("execute-approved-plan")) {
            Result result = executeReviewed(Path.of(args[1]), args[2], args[3]);
            System.out.println(JSON.writeValueAsString(result));
            if (result.status() != Status.VERIFIED) System.exit(1);
        } else throw new IllegalArgumentException("review <exact-plan.json> | execute-approved-plan <same-plan.json> <Root-reviewed-SHA256> <actual-shared-stage-deadline-UTC>");
    }
}

