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
 * Versioned exact project EXE UAC adapter. The historical two-target helper contract stays intact.
 * The current single-injector contract enters this same class with one runas, checks its actual
 * same-owner elevated token, then runs the exact frozen S26 whole REGISTER in its own classpath.
 * No broker, arbitrary command, external Add/import, automatic retry, or Game/Driver/SAVE access.
 * The parent only closes its elevated-child query handle on UNKNOWN; the existing WindowsJobProcess
 * retains its original owned S26 subtree timeout and cleanup semantics.
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
    public enum ProofScope { DIRECT_ADMIN_EXCLUSION_PATH, SAME_OWNER_ADMIN_SHARED_REGISTER_THREE_SETTINGS, DECLARED_PROJECT_EXE_PATH_ONLY, SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS }
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
    /** TokenUser is read through the same explicitly bound System32 library as TokenElevation. */
    public interface TokenAdvapi32 extends Advapi32 {
        boolean GetTokenInformation(WinNT.HANDLE token, int informationClass, Pointer information,
                int informationLength, IntByReference returnedLength);
        boolean ConvertSidToStringSidW(Pointer sid, com.sun.jna.ptr.PointerByReference text);
    }

    private record Apis(FileKernel32 kernel, Shell32 shell, Ole32 ole, TokenAdvapi32 security) { }

    /** No mutation, no ShellExecuteEx call. The printed command is the concrete Root review surface. */
    private static final ObjectMapper CURRENT_NATIVE_JSON = RootNativePlanJson.mapper();
    private static final String CURRENT_PLAN_SCHEMA = "xar.current-native-build-uac-plan/v1";
    private static final String CURRENT_PROVIDER_PLAN_SCHEMA = "xar.current-native-build-uac-plan/v2";
    private static final String CURRENT_PROVIDER_INPUT_SCHEMA = "xar.current-native-build-uac-input/v2";
    private static final String CURRENT_SOURCE_ROOT = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/dev61/ck3_autonomous_player/native_bridge";
    private static final String CURRENT_BUILD_ROOT = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/build61/dev";
    private static final String CURRENT_STATE_ROOT = "D:/ck3-state/ck3-java-g2-r5-native61";
    private static final String CURRENT_INJECTOR_SHA256 = "5337dd8be7c5aa44e4b7f48f9086ba6ee973f085316a74ff86881f73db59a185";
    private static final String S26_BUILD_SHA256 = "b88971ee1680a659363ba41a685a8ba4766c746787b46a9431aa730d8aefe461";
    private static final String CURRENT_JAVA_SHA256 = "bd3d87dfb44651a1c61c995e08ca4fcadb458437a373d46941381f9aeff9d6a0";
    private static final String ADMIN_CHILD_ROLE = "current-native-build-admin-child";
    private static final long CURRENT_JVM_RESERVE = 256L << 20;
    private static final String SETTINGS_SCHEMA = "xar.project-exe-three-settings-readback/v1";

    /** This version permits only the one actual injector, not a caller-selected executable family. */
    public record CurrentNativeBuild(String schema, String sourceRoot, String buildRoot,
            ControlBuild.FileRef frozenSourceActualRef, ControlBuild.FileRef environmentActualRef,
            ControlBuild.FileRef buildActualRef, ControlBuild.FileRef runtimeInventoryRef,
            ControlBuild.FileRef qualifiedToolsBuildRef, ControlBuild.FileRef injector) {
        public CurrentNativeBuild {
            boolean legacy = "xar.current-native-build-uac-input/v1".equals(schema);
            if ((!legacy && !CURRENT_PROVIDER_INPUT_SCHEMA.equals(schema))
                    || sourceRoot == null || buildRoot == null
                    || !Path.of(sourceRoot).isAbsolute() || !Path.of(buildRoot).isAbsolute()
                    || !Path.of(sourceRoot).equals(Path.of(sourceRoot).toAbsolutePath().normalize())
                    || !Path.of(buildRoot).equals(Path.of(buildRoot).toAbsolutePath().normalize())
                    || (Path.of(sourceRoot).startsWith(Path.of(buildRoot)) || Path.of(buildRoot).startsWith(Path.of(sourceRoot)))
                    || injector == null || injector.bytes() < 64 || injector.bytes() > (64L << 20)
                    || !normalizedPath(Path.of(buildRoot).resolve("xar_ck3_bridge_injector.exe").toString()).equals(normalizedPath(injector.path()))
                    || qualifiedToolsBuildRef == null || qualifiedToolsBuildRef.bytes() < 1 || qualifiedToolsBuildRef.bytes() > (4 << 20)
                    || (legacy && (!normalizedPath(CURRENT_SOURCE_ROOT).equals(normalizedPath(sourceRoot))
                        || !normalizedPath(CURRENT_BUILD_ROOT).equals(normalizedPath(buildRoot))
                        || injector.bytes() != 39936 || !CURRENT_INJECTOR_SHA256.equals(injector.sha256())
                        || qualifiedToolsBuildRef.bytes() != 202195 || !S26_BUILD_SHA256.equals(qualifiedToolsBuildRef.sha256())))
                    || (!legacy && S26_BUILD_SHA256.equals(qualifiedToolsBuildRef.sha256())))
                throw new IllegalArgumentException("exact versioned source/build/injector required; current provider evidence is verified before review");
            Objects.requireNonNull(frozenSourceActualRef); Objects.requireNonNull(environmentActualRef);
            Objects.requireNonNull(buildActualRef); Objects.requireNonNull(runtimeInventoryRef);
        }
    }
    public record CurrentNativeBuildPlan(String schema, String machineId, String observedAtUtc, String deadlineAtUtc,
            String owner, String expectedOwnerSid, int waitSeconds, CurrentNativeBuild currentNativeBuild,
            ControlBuild.FileRef invocationRef, ControlBuild.FileRef nativeStageSpecRef, ControlBuild.FileRef uacCapacityRef,
            ControlBuild.FileRef parentToolsBuildRef, List<ControlBuild.FileRef> parentSourceRefs,
            List<ControlBuild.FileRef> parentRuntime, String jdkRoot, List<ControlBuild.FileRef> jdkFiles,
            String outputRoot, String intentPath, String launchObservationPath, String resultPath,
            String adminChildIntentPath, String adminChildOutcomePath, String sharedStdoutPath, String sharedStderrPath) {
        public CurrentNativeBuildPlan {
            parentSourceRefs = List.copyOf(parentSourceRefs); parentRuntime = List.copyOf(parentRuntime);
            jdkFiles = List.copyOf(jdkFiles);
            Objects.requireNonNull(currentNativeBuild); Objects.requireNonNull(invocationRef);
            Objects.requireNonNull(nativeStageSpecRef); Objects.requireNonNull(uacCapacityRef); Objects.requireNonNull(parentToolsBuildRef);
            if (!((CURRENT_PLAN_SCHEMA.equals(schema) && "xar.current-native-build-uac-input/v1".equals(currentNativeBuild.schema()))
                    || (CURRENT_PROVIDER_PLAN_SCHEMA.equals(schema) && CURRENT_PROVIDER_INPUT_SCHEMA.equals(currentNativeBuild.schema()))))
                throw new IllegalArgumentException("Exact paired legacy or current-provider UAC plan/input versions required");
        }
    }
    public record ManagedRegisterInvocation(String schema, String machineId, ControlBuild.FileRef executable,
            List<String> arguments, String cwd, java.util.Map<String,String> environment, List<String> unsetEnvironment,
            ControlBuild.FileRef bindingRef, ControlBuild.FileRef specRef) {
        public ManagedRegisterInvocation {
            arguments=List.copyOf(arguments); environment=java.util.Map.copyOf(environment);
            unsetEnvironment=List.copyOf(unsetEnvironment); Objects.requireNonNull(executable);
            Objects.requireNonNull(bindingRef); Objects.requireNonNull(specRef);
        }
    }
    public record CurrentNativeStageSpec(String schema, String machineId, NativeBridgeBuild.Stage expectedStage,
            ControlBuild.FileRef frozenSourceActualRef, ControlBuild.FileRef requestRef, NativeBridgeRootGate.Limits limits) { }
    public record CurrentNativeBuildReview(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef planRef, CurrentNativeBuild currentNativeBuild,
            ControlBuild.FileRef invocationRef, ControlBuild.FileRef nativeStageSpecRef,
            String expectedOwnerSid, String lpVerb, String lpFile, String lpParameters, String lpDirectory,
            int nShow, int waitSeconds, String deadlineAtUtc, List<ControlBuild.FileRef> guardedInputRefs) {
        public CurrentNativeBuildReview { guardedInputRefs=uniqueLeaseInputs(guardedInputRefs); }
    }
    public record CurrentNativeBuildIntent(String schema, String machineId, String observedAtUtc,
            CurrentNativeBuildReview review, List<GuardedInput> guardedInputs, String unresolvedActionPolicy) {
        public CurrentNativeBuildIntent { guardedInputs=List.copyOf(guardedInputs); }
    }
    public record CurrentNativeBuildLaunch(String schema, String machineId, String observedAtUtc, boolean shellAcknowledged,
            ProcessIdentity processIdentity, Boolean tokenElevated, String tokenUserSid) { }
    public record CurrentAdminChildIntent(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef planRef, ControlBuild.FileRef originalParentIntentRef,
            ProcessIdentity processIdentity, boolean tokenElevated, String tokenUserSid,
            List<GuardedInput> guardedInputs, String unresolvedActionPolicy) {
        public CurrentAdminChildIntent { guardedInputs=List.copyOf(guardedInputs); }
    }
    public record DefenderSettings(
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionPath") List<String> exclusionPath,
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionExtension") List<String> exclusionExtension,
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionProcess") List<String> exclusionProcess) implements SettingsSnapshot {
        public DefenderSettings {
            exclusionPath=List.copyOf(exclusionPath); exclusionExtension=List.copyOf(exclusionExtension);
            exclusionProcess=List.copyOf(exclusionProcess);
        }
    }
    public sealed interface SettingsSnapshot permits DefenderSettings, NullableDefenderSettings {
        List<String> exclusionPath(); List<String> exclusionExtension(); List<String> exclusionProcess();
    }
    public record NullableDefenderSettings(
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionPath") List<String> exclusionPath,
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionExtension") List<String> exclusionExtension,
            @com.fasterxml.jackson.annotation.JsonProperty("ExclusionProcess") List<String> exclusionProcess) implements SettingsSnapshot {
        public NullableDefenderSettings {
            exclusionPath = List.copyOf(exclusionPath);
            exclusionExtension = exclusionExtension == null ? null : List.copyOf(exclusionExtension);
            exclusionProcess = exclusionProcess == null ? null : List.copyOf(exclusionProcess);
        }
    }
    public enum DefenderPropertyName { ExclusionPath, ExclusionExtension, ExclusionProcess }
    public enum PropertyValueState { STRING_ARRAY, OBSERVED_NULLABLE_VALUE }
    public record ProviderPropertyObservation(DefenderPropertyName name, int cimType, boolean isArray, PropertyValueState valueState) {
        public ProviderPropertyObservation {
            if (name == null || cimType != 8 || !isArray || valueState == null)
                throw new IllegalArgumentException("Exact existing CIM string-array property observation required");
        }
    }
    private static final String NULLABLE_SETTINGS_SCHEMA = "xar.project-exe-three-settings-readback/v2";
    private static final String NULLABLE_OBSERVATION_SCOPE =
            "Same administrative WMI client, one MSFT_MpPreference instance and existing Name/CIMType8/IsArray=true properties. "
            + "Python None is retained as an observed nullable CIM value, distinct from an empty array; raw VARIANT is not remeasured by this reader. "
            + "No assertion that effective exclusions are empty or unconfigured.";
    @com.fasterxml.jackson.databind.annotation.JsonDeserialize(using = ThreeSettingsReadbackCodec.class)
    public sealed interface ThreeSettingsReadback permits ArraySettingsReadback, NullableSettingsReadback {
        String schema(); SettingsSnapshot before(); SettingsSnapshot after();
        String tokenUserSid(); String processIdDecimal();
    }
    public record ArraySettingsReadback(String schema, DefenderSettings before, DefenderSettings after,
            String tokenUserSid, String processIdDecimal) implements ThreeSettingsReadback {
        public ArraySettingsReadback {
            if (!SETTINGS_SCHEMA.equals(schema) || before == null || after == null)
                throw new IllegalArgumentException("Exact array-only readback version1 required");
            settingsProofIdentity(tokenUserSid, processIdDecimal);
        }
    }
    public record NullableSettingsReadback(String schema, NullableDefenderSettings before, NullableDefenderSettings after,
            String tokenUserSid, String processIdDecimal, List<ProviderPropertyObservation> beforePropertyObservations,
            List<ProviderPropertyObservation> afterPropertyObservations, String nullableObservationScope) implements ThreeSettingsReadback {
        public NullableSettingsReadback {
            if (!NULLABLE_SETTINGS_SCHEMA.equals(schema) || before == null || after == null
                    || !NULLABLE_OBSERVATION_SCOPE.equals(nullableObservationScope))
                throw new IllegalArgumentException("Exact observed nullable readback version2 and scope required");
            settingsProofIdentity(tokenUserSid, processIdDecimal);
            beforePropertyObservations = List.copyOf(beforePropertyObservations);
            afterPropertyObservations = List.copyOf(afterPropertyObservations);
            propertyObservations(before, beforePropertyObservations); propertyObservations(after, afterPropertyObservations);
            if (before.exclusionExtension() != null && before.exclusionProcess() != null
                    && after.exclusionExtension() != null && after.exclusionProcess() != null)
                throw new IllegalArgumentException("Version2 must retain an actual observed nullable value");
        }
    }
    private static void settingsProofIdentity(String sid, String pid) {
        try { requireCanonicalSid(sid); }
        catch (IOException invalid) { throw new IllegalArgumentException("Canonical original TokenUser SID required", invalid); }
        canonicalUnsigned(pid, 32, true, "helper PID");
    }
    private static void propertyObservations(SettingsSnapshot settings, List<ProviderPropertyObservation> observations) {
        var names = List.of(DefenderPropertyName.ExclusionPath, DefenderPropertyName.ExclusionExtension, DefenderPropertyName.ExclusionProcess);
        if (!observations.stream().map(ProviderPropertyObservation::name).toList().equals(names))
            throw new IllegalArgumentException("Exactly one ordered observation per original Defender property required");
        for (var observation : observations) {
            List<String> value = switch (observation.name()) {
                case ExclusionPath -> settings.exclusionPath();
                case ExclusionExtension -> settings.exclusionExtension();
                case ExclusionProcess -> settings.exclusionProcess();
            };
            if (observation.valueState() != (value == null ? PropertyValueState.OBSERVED_NULLABLE_VALUE : PropertyValueState.STRING_ARRAY))
                throw new IllegalArgumentException("Property observation does not preserve the original nullable/array distinction");
        }
    }
    public static final class ThreeSettingsReadbackCodec extends com.fasterxml.jackson.databind.JsonDeserializer<ThreeSettingsReadback> {
        @Override public ThreeSettingsReadback deserialize(com.fasterxml.jackson.core.JsonParser input,
                com.fasterxml.jackson.databind.DeserializationContext context) throws IOException {
            JsonNode node = context.readTree(input); String schema = text(node, "schema");
            Set<String> fields = new HashSet<>(Set.of("schema", "before", "after", "token_user_sid", "process_id_decimal"));
            boolean nullable = NULLABLE_SETTINGS_SCHEMA.equals(schema);
            if (nullable) fields.addAll(Set.of("before_property_observations", "after_property_observations", "nullable_observation_scope"));
            require((nullable || SETTINGS_SCHEMA.equals(schema)) && keys(node).equals(fields), "Exact versioned persisted three-settings fields required");
            try {
                if (!nullable) return new ArraySettingsReadback(schema,
                        input.getCodec().treeToValue(node.get("before"), DefenderSettings.class),
                        input.getCodec().treeToValue(node.get("after"), DefenderSettings.class),
                        text(node, "token_user_sid"), text(node, "process_id_decimal"));
                return new NullableSettingsReadback(schema,
                        input.getCodec().treeToValue(node.get("before"), NullableDefenderSettings.class),
                        input.getCodec().treeToValue(node.get("after"), NullableDefenderSettings.class),
                        text(node, "token_user_sid"), text(node, "process_id_decimal"),
                        List.of(input.getCodec().treeToValue(array(node.get("before_property_observations")), ProviderPropertyObservation[].class)),
                        List.of(input.getCodec().treeToValue(array(node.get("after_property_observations")), ProviderPropertyObservation[].class)),
                        text(node, "nullable_observation_scope"));
            } catch (IllegalArgumentException | NullPointerException invalid) {
                throw new IOException("Invalid versioned three-settings proof", invalid);
            }
        }
    }
    public record CurrentNativeBuildCompletion(ControlBuild.FileRef sharedOriginalTerminalRef,
            ControlBuild.FileRef nativeActualRef, ControlBuild.FileRef manifestRef, ControlBuild.FileRef helperReceiptRef,
            WindowsJobProcess.ProcessIdentity sharedProcess, WindowsJobProcess.ProcessIdentity helperProcess,
            ThreeSettingsReadback settings) { }
    public record CurrentAdminChildOutcome(String schema, String machineId, String observedAtUtc, Status status,
            ControlBuild.FileRef planRef, ControlBuild.FileRef originalParentIntentRef, ControlBuild.FileRef adminChildIntentRef,
            ProcessIdentity processIdentity, boolean tokenElevated, String tokenUserSid,
            WindowsJobProcess.CommandResult sharedProcess, CurrentNativeBuildCompletion completion,
            List<String> diagnostics) {
        public CurrentAdminChildOutcome { diagnostics=List.copyOf(diagnostics); }
    }
    public record CurrentNativeBuildResult(String schema, String machineId, String observedAtUtc, Status status,
            ProofScope proofScope, CurrentNativeBuildReview review, boolean launchCallEntered, boolean shellAcknowledged,
            Integer launchWin32Error, ProcessIdentity processIdentity, Boolean tokenElevated, String tokenUserSid,
            String processExitCodeDecimal, boolean waitTimedOut, ControlBuild.FileRef adminChildOutcomeRef,
            CurrentNativeBuildCompletion completion, List<String> diagnostics, boolean automaticallyRetried,
            boolean elevatedProcessTerminated, TerminalProof terminalProof) {
        public CurrentNativeBuildResult { diagnostics=List.copyOf(diagnostics); }
    }
    private record CurrentPrepared(CurrentNativeBuildPlan plan, CurrentNativeBuildReview review,
            ManagedRegisterInvocation invocation, SharedOwnedCommandBinding binding, SharedOwnedCommand.Request shared,
            CurrentNativeStageSpec stage, NativeBridgeBuild.Request request, List<ControlBuild.FileRef> inputs) {
        private CurrentPrepared { inputs=uniqueLeaseInputs(inputs); }
    }
    /** Original S26 v2 Java terminal: exactly its 26 fields, with no v3/v4 relabelling. */
    record CurrentSharedJavaTerminal(String schema, String machineId, String observedAtUtc, SharedOwnedCommand.Status status,
            String owner, String slotId, String borrowedSlotId, ControlBuild.FileRef requestRef, ControlBuild.FileRef standingRef,
            ControlBuild.FileRef launcherSourceRef, List<ControlBuild.FileRef> completeRuntime, SharedOwnedCommand.Outer outer,
            boolean childStarted, WindowsJobProcess.CommandResult child, WindowsJobProcess.JobDiagnosticOutcome diagnostic,
            SharedOwnedCommand.Check inputPrecheck, SharedOwnedCommand.Check inputPostcheck, SharedOwnedCommand.Check runtimePostcheck,
            String failure, List<SharedSourceFiles.Witness> inputBefore, List<String> effectiveArguments, ControlBuild.FileRef stdoutRef,
            ControlBuild.FileRef stderrRef, long outputNativeBytesWithDirectoryGuard, int gameRpcCalls, int actualDriverOrSaveBodyReads) {
        CurrentSharedJavaTerminal {
            completeRuntime=List.copyOf(completeRuntime); inputBefore=List.copyOf(inputBefore); effectiveArguments=List.copyOf(effectiveArguments);
        }
    }

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
        LaunchOperation operation = new LaunchOperation() {
            public String deadlineAtUtc() { return plan.deadlineAtUtc(); }
            public int waitSeconds() { return WAIT_SECONDS; }
            public ControlBuild.FileRef image() { return plan.pythonRef(); }
            public String parameters() { return review.lpParameters(); }
            public String directory() { return review.lpDirectory(); }
            public String expectedOwnerSid() { return null; }
            public Apis nativeApis() throws IOException { return apis(); }
            public List<ControlBuild.FileRef> inputs() throws IOException { return NativeProjectExeUac.inputs(plan, review.planRef()); }
            public void revalidate() throws IOException { validate(plan); }
            public void claim(List<GuardedInput> inputs) throws IOException {
                claimIntent(Path.of(plan.intentPath()), new Intent("xar.exact-two-exe-uac-intent/v2", MACHINE,
                        Instant.now().toString(), review, inputs, NO_RETRY));
            }
            public void observe(ProcessIdentity child, boolean elevated, String ownerSid) throws IOException {
                writeNew(Path.of(plan.launchObservationPath()), new LaunchObservation(
                        "xar.exact-two-exe-uac-launch/v1", MACHINE, Instant.now().toString(), true, child, elevated));
            }
            public CompletedRegistration complete(TerminalProof terminal) throws IOException {
                Path path = Path.of(plan.helperReceiptPath());
                require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "fresh administrator receipt missing");
                require(Files.size(path) <= LIMIT, "administrator receipt exceeded approved byte ceiling");
                ControlBuild.FileRef receipt = ControlBuild.FileRef.measure(path.toRealPath());
                byte[] bytes = read(path, LIMIT);
                JsonNode raw = object(JSON.readTree(bytes));
                if (!"0".equals(terminal.processExitCodeDecimal()) || !"verified".equals(text(raw, "status")))
                    return new CompletedRegistration(Status.SETTINGS_FAILED, null, receipt, null);
                qualifyCompletion(terminal, plan.pythonRef().path(),
                        receiptExpectation(plan.nativeBuildRoot(), tree(Path.of(plan.manifestRef().path()))), bytes, receipt);
                receipt.verify();
                return new CompletedRegistration(Status.VERIFIED, ProofScope.DIRECT_ADMIN_EXCLUSION_PATH, receipt, null);
            }
        };
        LaunchOutcome outcome = launch(operation);
        Result result = new Result("xar.exact-two-exe-uac-result/v4", MACHINE, outcome.observedAtUtc(), outcome.status(),
                outcome.status() == Status.VERIFIED ? ProofScope.DIRECT_ADMIN_EXCLUSION_PATH : null,
                review, outcome.launchCallEntered(), outcome.shellAcknowledged(), outcome.launchWin32Error(),
                outcome.processIdentity(), outcome.tokenElevated(), outcome.processExitCodeDecimal(), outcome.waitTimedOut(),
                outcome.completion() == null ? null : outcome.completion().helperReceiptRef(),
                outcome.diagnostics(), false, false, outcome.terminalProof());
        writeNew(Path.of(plan.resultPath()), result);
        return result;
    }

    private static final String NO_RETRY =
            "No automatic resubmission. Timeout/crash/missing receipt requires original process and settings resolution.";
    private interface LaunchOperation {
        String deadlineAtUtc();
        int waitSeconds();
        ControlBuild.FileRef image();
        String parameters();
        String directory();
        String expectedOwnerSid();
        Apis nativeApis() throws IOException;
        List<ControlBuild.FileRef> inputs() throws IOException;
        void revalidate() throws IOException;
        void claim(List<GuardedInput> inputs) throws IOException;
        void observe(ProcessIdentity child, boolean elevated, String ownerSid) throws IOException;
        CompletedRegistration complete(TerminalProof terminal) throws IOException;
        default ControlBuild.FileRef claimedIntentRef() { return null; }
    }
    private record CompletedRegistration(Status status, ProofScope proofScope, ControlBuild.FileRef helperReceiptRef,
            CurrentNativeBuildCompletion currentNativeBuild) { }
    private record LaunchOutcome(String observedAtUtc, Status status, boolean launchCallEntered, boolean shellAcknowledged,
            Integer launchWin32Error, ProcessIdentity processIdentity, Boolean tokenElevated, String ownerSid,
            String processExitCodeDecimal, boolean waitTimedOut, List<String> diagnostics, TerminalProof terminalProof,
            CompletedRegistration completion) {
        private LaunchOutcome { diagnostics = List.copyOf(diagnostics); }
    }

    /** The two versioned contracts share this sole native runas and process-handle implementation. */
    private static LaunchOutcome launch(LaunchOperation operation) throws IOException {
        Apis apis = operation.nativeApis();
        List<Guard> guards = new ArrayList<>();
        List<String> diagnostics = new ArrayList<>();
        List<ControlBuild.FileRef> inputs = operation.inputs();
        WinNT.HANDLE child = null;
        ProcessIdentity identity = null;
        Boolean elevated = null;
        String ownerSid = null;
        Integer win32Error = null;
        String exitCode = null;
        CompletedRegistration completion = null;
        boolean entered = false, acknowledged = false, timedOut = false, comInitialized = false, signalled = false;
        Status status = Status.UNKNOWN;
        boolean intentWritten = false;
        try {
            for (ControlBuild.FileRef ref : inputs) guards.add(Guard.open(apis.kernel(), ref));
            operation.revalidate(); verifyGuards(guards);
            if (operation.expectedOwnerSid() != null)
                require(operation.expectedOwnerSid().equals(tokenUserSid(apis, apis.kernel().GetCurrentProcess())),
                        "current parent is not the approved same-owner account");
            operation.claim(guards.stream().map(Guard::evidence).toList());
            intentWritten = true;
            ControlBuild.FileRef claimedIntent = operation.claimedIntentRef();
            if (claimedIntent != null) guards.add(Guard.open(apis.kernel(), claimedIntent));
            int initialized = apis.ole().CoInitializeEx(Pointer.NULL, 0x2 | 0x4).intValue();
            require(initialized == 0 || initialized == 1, "COM STA initialization failed: " + initialized);
            comInitialized = true;
            ShellAPI.SHELLEXECUTEINFO info = new ShellAPI.SHELLEXECUTEINFO();
            info.fMask = 0x40 | 0x100;
            info.lpVerb = "runas"; info.lpFile = operation.image().path(); info.lpParameters = operation.parameters();
            info.lpDirectory = operation.directory(); info.nShow = 0;
            require(Instant.now().isBefore(Instant.parse(operation.deadlineAtUtc())), "lease expired before launch");
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
                require(Path.of(identity.executable()).toRealPath().equals(Path.of(operation.image().path()).toRealPath()),
                        "native child image differs from approved interpreter");
                elevated = tokenElevated(apis, child);
                require(elevated, "native child token is not elevated");
                if (operation.expectedOwnerSid() != null) {
                    ownerSid = tokenUserSid(apis, child);
                    require(operation.expectedOwnerSid().equals(ownerSid), "elevated child changed the approved account");
                }
                operation.observe(identity, elevated, ownerSid);
                long bound = Duration.ofSeconds(operation.waitSeconds()).toNanos();
                while (true) {
                    int state = apis.kernel().WaitForSingleObject(child, 0);
                    if (state == 0) break;
                    require(state == WAIT_TIMEOUT, "native process wait failed: " + state);
                    if (System.nanoTime() - started >= bound || !Instant.now().isBefore(Instant.parse(operation.deadlineAtUtc()))) {
                        timedOut = true; break;
                    }
                    state = apis.kernel().WaitForSingleObject(child, 250);
                    require(state == 0 || state == WAIT_TIMEOUT, "native bounded process wait failed: " + state);
                }
                if (timedOut) diagnostics.add("Elevated child may still be live. No kill and no resubmission; retain original identity and receipt path.");
                else {
                    signalled = true;
                    IntByReference code = new IntByReference();
                    require(apis.kernel().GetExitCodeProcess(child, code), "native child exit unavailable");
                    exitCode = Integer.toUnsignedString(code.getValue());
                    verifySourceRefs(inputs); verifyGuards(guards);
                    completion = operation.complete(new TerminalProof(acknowledged, identity, elevated, true, false, exitCode));
                    if (completion.status() == Status.VERIFIED || operation.expectedOwnerSid() != null)
                        require(Instant.now().isBefore(Instant.parse(operation.deadlineAtUtc())), "terminal arrived outside lease");
                    status = completion.status();
                }
            }
        } catch (IOException | RuntimeException failure) {
            diagnostics.add(failure.getClass().getName() + ": " + failure.getMessage()); status = Status.UNKNOWN;
        } finally {
            if (valid(child) && !apis.kernel().CloseHandle(child)) {
                diagnostics.add("native child handle close failed: " + Native.getLastError()); status = Status.UNKNOWN;
            }
            if (comInitialized) apis.ole().CoUninitialize();
            for (int i = guards.size() - 1; i >= 0; i--)
                try { guards.get(i).close(); } catch (IOException failure) { diagnostics.add(failure.getMessage()); status = Status.UNKNOWN; }
        }
        if (!intentWritten) throw new IOException("No UAC submitted; append-only intent could not be established: " + diagnostics);
        return new LaunchOutcome(Instant.now().toString(), status, entered, acknowledged, win32Error, identity, elevated,
                ownerSid, exitCode, timedOut, diagnostics,
                new TerminalProof(acknowledged, identity, elevated, signalled, timedOut, exitCode), completion);
    }

    private static boolean isCurrentPlanSchema(String schema) {
        return CURRENT_PLAN_SCHEMA.equals(schema) || CURRENT_PROVIDER_PLAN_SCHEMA.equals(schema);
    }

    private static boolean currentPlanRoute(JsonNode envelope) throws IOException {
        String schema = text(envelope, "schema");
        if (isCurrentPlanSchema(schema)) return true;
        require("xar.exact-two-exe-uac-plan/v2".equals(schema), "unsupported versioned UAC plan schema");
        return false;
    }

    public static CurrentNativeBuildPlan parseCurrentNativeBuildPlan(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= CURRENT_LIMIT, "bounded current native plan required");
        return JSON.readValue(raw, CurrentNativeBuildPlan.class);
    }
    private static final int CURRENT_LIMIT = 32 << 20;

    /** Read-only exact command review. The new parent runtime never becomes part of the S26 classpath. */
    public static CurrentNativeBuildReview reviewCurrentNativeBuild(Path path) throws IOException {
        ControlBuild.FileRef pin = ControlBuild.FileRef.measure(path.toRealPath());
        CurrentNativeBuildPlan plan = parseCurrentNativeBuildPlan(currentRead(pin));
        return prepareCurrent(plan, pin, Instant.now().toString(), true).review();
    }

    private static CurrentPrepared prepareCurrent(CurrentNativeBuildPlan plan, ControlBuild.FileRef planRef,
            String reviewedAt, boolean requireFresh) throws IOException {
        require(isCurrentPlanSchema(plan.schema())
                && MACHINE.equals(plan.machineId()) && MACHINE.equals(WindowsJobProcess.currentMachineId()),
                "current native plan schema/machine differs");
        require("/root/native_execution".equals(plan.owner()), "only the original current Native owner is permitted");
        requireCanonicalSid(plan.expectedOwnerSid());
        CurrentNativeBuild build = plan.currentNativeBuild();
        build.injector().verify(); build.qualifiedToolsBuildRef().verify();
        require(plan.waitSeconds() > 0 && plan.waitSeconds() <= 7200, "finite original whole-stage wait required");
        require(!plan.parentSourceRefs().isEmpty() && !plan.parentRuntime().isEmpty() && !plan.jdkFiles().isEmpty()
                && plan.parentSourceRefs().size() <= 16000 && plan.jdkFiles().size() <= 16000,
                "complete bounded parent code and JDK input closure required");

        ControlBuild.BuildReceipt parent = ControlBuild.verifiedCompletedReceipt(plan.parentToolsBuildRef());
        require(parent.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && sameRefs(parent.completeDeployment(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(NativeProjectExeUac.class), plan.parentRuntime())
                && sameRefs(parent.sourcePins(), plan.parentSourceRefs()),
                "the actual approved parent source and deployed class closure differ");
        if (!usesCurrentProvider(build))
            require(!sameRefs(plan.parentRuntime(), ControlBuild.verifiedCompletedReceipt(build.qualifiedToolsBuildRef()).completeDeployment()),
                    "the legacy UAC parent must not relabel the frozen S26 runtime");
        Path jdk = Path.of(plan.jdkRoot()).toRealPath();
        require(jdk.equals(Path.of("C:/jdk-21").toRealPath())
                && jdk.equals(Path.of(System.getProperty("java.home")).toRealPath())
                && sameRefs(NativeBridgeBuild.inventory(jdk), plan.jdkFiles()),
                "exact complete actual JDK dependency closure differs");
        ControlBuild.FileRef javaExecutable = selectedJava(plan.jdkFiles());
        require(javaExecutable.bytes() == 50344 && CURRENT_JAVA_SHA256.equals(javaExecutable.sha256()), "the actual current JDK executable differs");

        ManagedRegisterInvocation invocation = JSON.readValue(currentRead(plan.invocationRef()), ManagedRegisterInvocation.class);
        require("xar.shared-owned-command-invocation/v2".equals(invocation.schema())
                && MACHINE.equals(invocation.machineId()) && invocation.executable().equals(javaExecutable),
                "original whole S26 invocation required");
        SharedOwnedCommandBinding binding = SharedOwnedCommandBinding.read(invocation.bindingRef());
        SharedOwnedCommand.Request shared = SharedOwnedCommand.parseRequest(object(JSON.readTree(currentRead(invocation.specRef()))));
        JsonNode standing = object(JSON.readTree(currentRead(binding.standingRef())));
        SharedOwnedCommand.StandingPreflight allowance;
        try { allowance = SharedOwnedCommand.validateStanding(shared, binding, standing); }
        catch (Exception failure) { throw new IOException("original Shared standing does not admit this exact command", failure); }
        require(shared.owner().equals(plan.owner()) && shared.coordinator().equals(plan.owner()) && shared.borrowedSlotId() == null
                && shared.javaInvocation() == null && shared.msvcAuxiliaryBinding() == null && shared.preparedRoot() == null
                && shared.executable().equals(javaExecutable) && plan.waitSeconds() >= shared.timeoutSeconds()
                && plan.waitSeconds() <= allowance.primary().timeoutSeconds(),
                "whole-stage owner, command, or original wait budget differs");
        require(Instant.parse(plan.deadlineAtUtc()).equals(allowance.deadline()), "current UAC deadline cannot renew the original Shared standing");
        require(invocation.cwd().equals(shared.cwd().toString())
                && (usesCurrentProvider(build) || Path.of(invocation.cwd()).toRealPath().equals(Path.of(CURRENT_STATE_ROOT).toRealPath())),
                "the original admitted Native working directory differs");
        ControlBuild.BuildReceipt selectedCarrier = qualifyCurrentCarrier(build.qualifiedToolsBuildRef(),
                ref(object(standing.get("qualified_tools_ref")), "bytes"), readRefs(standing.get("runtime_closure")));
        List<ControlBuild.FileRef> s26 = selectedCarrier.completeDeployment();
        require(s26.size() == 6, "the exact complete qualified six-piece carrier closure differs");
        String s26Classpath = s26.stream().map(ControlBuild.FileRef::path).collect(java.util.stream.Collectors.joining(";"));
        List<String> expectedOuter = new ArrayList<>(List.of("-Xms32m", "-Xmx128m", "-XX:+ExitOnOutOfMemoryError",
                "-Djava.io.tmpdir=" + binding.nativeTemporaryRoot(), "-Djna.tmpdir=" + binding.nativeTemporaryRoot(),
                "-cp", s26Classpath, SharedOwnedCommand.class.getName(), "run"));
        appendTriple(expectedOuter, invocation.bindingRef()); appendTriple(expectedOuter, invocation.specRef());
        require(invocation.arguments().equals(expectedOuter), "only the exact original whole S26 Shared run is permitted");
        require(invocation.environment().equals(java.util.Map.of("TMP", binding.nativeTemporaryRoot().toString(),
                "TEMP", binding.nativeTemporaryRoot().toString()))
                && invocation.unsetEnvironment().equals(JAVA_OPTION_ENVIRONMENT),
                "the original S26 invocation environment differs");

        CurrentNativeStageSpec stage = CURRENT_NATIVE_JSON.readValue(currentRead(plan.nativeStageSpecRef()), CurrentNativeStageSpec.class);
        require("xar.native-bridge-stage-command/v1".equals(stage.schema()) && MACHINE.equals(stage.machineId())
                && stage.expectedStage() == NativeBridgeBuild.Stage.REGISTER
                && stage.frozenSourceActualRef().equals(build.frozenSourceActualRef())
                && stage.limits().ownerTask().equals(plan.owner())
                && stage.limits().deadline().equals(Instant.parse(plan.deadlineAtUtc())),
                "the original current REGISTER stage/owner/deadline differs");
        NativeBridgeBuild.Request request = NativeBridgeBuild.readRequest(stage.requestRef());
        require(request.stage() == NativeBridgeBuild.Stage.REGISTER
                && (NativeBridgeBuild.REGISTER_REQUEST_SCHEMA.equals(request.schema()) || NativeBridgeBuild.BOUND_REQUEST_SCHEMA.equals(request.schema()))
                && normalizedPath(request.sourceRoot().toString()).equals(normalizedPath(build.sourceRoot()))
                && normalizedPath(request.buildRoot().toString()).equals(normalizedPath(build.buildRoot()))
                && request.canonicalRepository().equals(REPO.toRealPath())
                && request.qualifiedToolsBuild().equals(build.qualifiedToolsBuildRef())
                && request.environmentActual().equals(build.environmentActualRef())
                && request.buildActual().equals(build.buildActualRef())
                && request.defender() instanceof NativeBridgeDefender.ManifestRuntime,
                "current exact REGISTER request/source/build causal chain differs");
        NativeBridgeDefender.ManifestRuntime helper = (NativeBridgeDefender.ManifestRuntime) request.defender();
        NativeBridgeDefender.requireDirectHelperRuntime(helper);
        require(NativeBridgeDefender.directBaseRuntime(request.canonicalRepository(),helper.inventoryRef()).equals(helper),
                "current helper differs from the actual direct-base inventory producer");
        require(helper.inventoryRef().equals(build.runtimeInventoryRef()), "the fresh full helper inventory differs");
        helper.python().verify(); helper.helper().verify();
        require(shared.inputs().containsAll(List.of(plan.nativeStageSpecRef(), stage.requestRef(),
                build.frozenSourceActualRef(), build.environmentActualRef(), build.buildActualRef(),
                build.runtimeInventoryRef(), build.qualifiedToolsBuildRef())),
                "the original Shared input closure omitted a current Native source");
        requireCurrentInnerCommand(shared, javaExecutable, s26, plan.nativeStageSpecRef(), usesCurrentProvider(build));
        requireCurrentBuildEvidence(build, request);
        Path output = Path.of(plan.outputRoot()).toRealPath();
        require(output.startsWith(allowance.primary().outputRoot())
                && output.startsWith(Path.of(invocation.cwd()).toRealPath()),
                "current UAC outputs lie outside the actual original slot and state root");
        requireCurrentUacCapacity(plan, shared, stage, binding);
        Set<Path> outputs = new HashSet<>();
        for (String name : currentOutputPaths(plan)) {
            Path target = Path.of(name).toAbsolutePath().normalize();
            require(target.getParent().toRealPath().equals(output) && outputs.add(target), "fresh distinct current UAC output paths required");
            if (requireFresh) require(Files.notExists(target, LinkOption.NOFOLLOW_LINKS), "current UAC output already exists; UNKNOWN never permits replay");
        }
        if (requireFresh) {
            require(Files.notExists(shared.outputRoot(), LinkOption.NOFOLLOW_LINKS)
                    && Files.notExists(request.stageRoot(), LinkOption.NOFOLLOW_LINKS), "original Shared/REGISTER stage was already claimed");
            Instant now = Instant.now(), observed = Instant.parse(plan.observedAtUtc()), deadline = Instant.parse(plan.deadlineAtUtc());
            ControlBuild.CapacityRelease release = JSON.readValue(currentRead(plan.uacCapacityRef()), ControlBuild.CapacityRelease.class);
            require(!observed.isBefore(Instant.parse(release.observedAtUtc())) && !observed.isAfter(now)
                    && Duration.between(now, deadline).compareTo(Duration.ofSeconds(plan.waitSeconds())) >= 0,
                    "current plan must lie inside its original Root capacity window with the complete whole-stage wait remaining");
        }
        List<ControlBuild.FileRef> inputs = currentInputs(plan, planRef, invocation, binding, shared, stage, request, parent);
        verifySourceRefs(inputs);
        String parentClasspath = plan.parentRuntime().stream().map(ControlBuild.FileRef::path)
                .collect(java.util.stream.Collectors.joining(";"));
        List<String> child = new ArrayList<>(List.of("-Xms32m", "-Xmx128m", "-XX:+ExitOnOutOfMemoryError",
                "-Djava.io.tmpdir=" + binding.nativeTemporaryRoot(), "-Djna.tmpdir=" + binding.nativeTemporaryRoot(),
                "-cp", parentClasspath, NativeProjectExeUac.class.getName(), ADMIN_CHILD_ROLE));
        appendTriple(child, planRef); child.add(plan.deadlineAtUtc());
        CurrentNativeBuildReview review = new CurrentNativeBuildReview("xar.current-native-build-uac-review/v1", MACHINE,
                reviewedAt, planRef, build, plan.invocationRef(), plan.nativeStageSpecRef(), plan.expectedOwnerSid(),
                "runas", javaExecutable.path(), child.stream().map(NativeProjectExeUac::quote).collect(java.util.stream.Collectors.joining(" ")),
                invocation.cwd(), 0, plan.waitSeconds(), plan.deadlineAtUtc(), inputs);
        return new CurrentPrepared(plan, review, invocation, binding, shared, stage, request, inputs);
    }

    private static final List<String> JAVA_OPTION_ENVIRONMENT = List.of("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVAC_OPTIONS");
    private static ControlBuild.FileRef selectedJava(List<ControlBuild.FileRef> jdk) throws IOException {
        List<ControlBuild.FileRef> selected = jdk.stream().filter(pin -> normalizedPath(pin.path()).equals(normalizedPath("C:/jdk-21/bin/java.exe"))).toList();
        require(selected.size() == 1, "one exact current JDK executable required"); return selected.getFirst();
    }
    private static boolean sameRefs(List<ControlBuild.FileRef> left, List<ControlBuild.FileRef> right) {
        return left.size() == right.size() && new HashSet<>(left).size() == left.size() && new HashSet<>(left).equals(new HashSet<>(right));
    }
    private static void appendTriple(List<String> arguments, ControlBuild.FileRef ref) {
        arguments.add(ref.path()); arguments.add(Long.toString(ref.bytes())); arguments.add(ref.sha256());
    }
    private static byte[] currentRead(ControlBuild.FileRef pin) throws IOException {
        require(pin != null && pin.bytes() > 0 && pin.bytes() <= CURRENT_LIMIT, "bounded exact current input required");
        pin.verify(); byte[] raw = read(Path.of(pin.path()), CURRENT_LIMIT);
        require(raw.length == pin.bytes() && sha(raw).equals(pin.sha256()), "current input bytes changed"); return raw;
    }
    private static List<ControlBuild.FileRef> readRefs(JsonNode rows) throws IOException {
        List<ControlBuild.FileRef> result=new ArrayList<>(); for(JsonNode row:array(rows))result.add(ref(row,"bytes")); return List.copyOf(result);
    }
    private static List<String> currentOutputPaths(CurrentNativeBuildPlan plan) {
        return List.of(plan.intentPath(), plan.launchObservationPath(), plan.resultPath(), plan.adminChildIntentPath(),
                plan.adminChildOutcomePath(), plan.sharedStdoutPath(), plan.sharedStderrPath());
    }

    private static final String PROFILE14_PATH = "D:/codex-ck3-demos/2026-10-26-java-tools-s-isolated-r4-resume61/build/java-tools-s26-local-resume61/profile14-s26.jar";
    private static ControlBuild.FileRef profile14() {
        return new ControlBuild.FileRef(Path.of(PROFILE14_PATH).toAbsolutePath().normalize().toString(), 18271,
                "53e797cb90f7b7127356422690a14ebec205a21eab3d1f97c2d4ce818e811e31");
    }
    static void requireCurrentInnerCommand(SharedOwnedCommand.Request shared, ControlBuild.FileRef javaExecutable,
            List<ControlBuild.FileRef> s26, ControlBuild.FileRef stageSpec) throws IOException {
        requireCurrentInnerCommand(shared, javaExecutable, s26, stageSpec, false);
    }
    static void requireCurrentInnerCommand(SharedOwnedCommand.Request shared, ControlBuild.FileRef javaExecutable,
            List<ControlBuild.FileRef> s26, ControlBuild.FileRef stageSpec, boolean currentProvider) throws IOException {
        require(shared.executable().equals(javaExecutable), "Exact Java input required");
        String classpath = s26.stream().map(ControlBuild.FileRef::path).collect(java.util.stream.Collectors.joining(";"));
        if (!currentProvider) {
            ControlBuild.FileRef profile = profile14(); profile.verify();
            require(shared.inputs().contains(profile), "Original historical Profile14 input required");
            classpath = profile.path() + ";" + classpath;
        }
        List<String> expected = new ArrayList<>(List.of("-Xms32m", "-Xmx384m", "-XX:+UseSerialGC",
                "-XX:ActiveProcessorCount=2", "-cp", classpath,
                currentProvider ? NativeBridgeBuild.class.getName() : "org.xar.ck3.control.build.NativeBridgeStageCommand", "execute"));
        appendTriple(expected, stageSpec);
        require(shared.arguments().equals(expected), "only the frozen Profile14 and S26 whole REGISTER command may run");
    }
    private static boolean usesCurrentProvider(CurrentNativeBuild build) {
        return CURRENT_PROVIDER_INPUT_SCHEMA.equals(build.schema());
    }

    static ControlBuild.BuildReceipt qualifyCurrentCarrier(ControlBuild.FileRef selected, ControlBuild.FileRef standingSelected,
            List<ControlBuild.FileRef> standingRuntime) throws IOException {
        ControlBuild.BuildReceipt tools = ControlBuild.verifiedCompletedReceipt(selected);
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME && MACHINE.equals(tools.machineId())
                && tools.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND
                && selected.equals(standingSelected) && sameRefs(tools.completeDeployment(), standingRuntime),
                "actual complete qualified carrier and exact current standing binding required");
        return tools;
    }

    static void requireCurrentProviderExecution(CurrentNativeBuildPlan plan) throws IOException {
        require(CURRENT_PROVIDER_PLAN_SCHEMA.equals(plan.schema()) && usesCurrentProvider(plan.currentNativeBuild()),
                "legacy S26 current-plan data is historical only; new execution requires the current qualified provider plan");
    }

    private static void requireCurrentBuildEvidence(CurrentNativeBuild build, NativeBridgeBuild.Request request) throws IOException {
        if (usesCurrentProvider(build)) NativeCombinedSourceCut.readAcceptedSource(build.frozenSourceActualRef());
        else require(build.frozenSourceActualRef().bytes() == 6890947
                && build.frozenSourceActualRef().sha256().equals("578a3d6fa81c265dbdb72d54e0fbc154e88e3d8065b4277900ce82c6a43b4fc6"),
                "the exact accepted legacy Native source cut is required");
        JsonNode source = object(JSON.readTree(currentRead(build.frozenSourceActualRef())));
        if (NativeBridgeBuild.BOUND_REQUEST_SCHEMA.equals(request.schema())) {
            var binding = NativeBridgeBuild.sourceBinding(request);
            require(usesCurrentProvider(build) && binding.retainedSourceActualRef().equals(build.frozenSourceActualRef())
                    && binding.compileSourceRoot().equals(Path.of(build.sourceRoot()))
                    && CompileSourceBinding.sourceActual(binding).producerToolsBuildRef().equals(build.qualifiedToolsBuildRef()),
                    "Current REGISTER must bind the exact retained source cut to its real reused compile root");
        } else {
        require("xar.native-combined-source-cut-actual/v1".equals(text(source, "schema"))
                && MACHINE.equals(text(source, "machine_id")) && bool(source, "source_unchanged")
                && normalizedPath(text(source, "native_source_root")).equals(normalizedPath(build.sourceRoot()))
                && ref(source.get("producer_tools_build_ref"), "bytes").equals(build.qualifiedToolsBuildRef())
                && readRefs(source.get("complete_native_sources")).equals(request.completeSources()),
                "the exact source cut does not describe this REGISTER source and producer");        }
        NativeBridgeBuild.Actual environment = NativeBridgeBuild.readAccepted(build.environmentActualRef(), NativeBridgeBuild.Stage.ENV);
        NativeBridgeBuild.Actual compiled = NativeBridgeBuild.readAccepted(build.buildActualRef(), NativeBridgeBuild.Stage.BUILD);
        require(NativeBridgeBuild.ACTUAL_SCHEMA.equals(environment.schema()) && NativeBridgeBuild.ACTUAL_SCHEMA.equals(compiled.schema())
                && NativeBridgeBuild.sameBuild(request, NativeBridgeBuild.readRequest(environment.requestRef()))
                && NativeBridgeBuild.sameBuild(request, NativeBridgeBuild.readRequest(compiled.requestRef()))
                && NativeBridgeBuild.readRequest(compiled.requestRef()).environmentActual().equals(build.environmentActualRef())
                && compiled.outputRefs().contains(build.injector()),
                "the original actual ENV and BUILD do not form the current injector lineage");
        NativeBridgeDefender.Graph graph = NativeBridgeDefender.readGraph(request);
        require(graph.injector().equals(build.injector()), "actual fresh BUILD selected injector differs");
    }
    private static List<ControlBuild.FileRef> currentInputs(CurrentNativeBuildPlan plan, ControlBuild.FileRef planRef,
            ManagedRegisterInvocation invocation, SharedOwnedCommandBinding binding, SharedOwnedCommand.Request shared,
            CurrentNativeStageSpec stage, NativeBridgeBuild.Request request, ControlBuild.BuildReceipt parent) throws IOException {
        var refs = new ArrayList<ControlBuild.FileRef>();
        refs.addAll(List.of(planRef, plan.invocationRef(), plan.nativeStageSpecRef(), plan.uacCapacityRef(), plan.parentToolsBuildRef(),
                invocation.bindingRef(), invocation.specRef(), binding.launcherSourceRef(), binding.standingRef(), binding.deliveryRef(),
                stage.frozenSourceActualRef(), stage.requestRef(), stage.limits().capacityEvidence()));
        ControlBuild.CapacityRelease uacCapacity = JSON.readValue(currentRead(plan.uacCapacityRef()), ControlBuild.CapacityRelease.class);
        refs.add(uacCapacity.policyRef());
        for (var override : uacCapacity.quotaOverrides().values())
            refs.add(new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()));
        refs.addAll(plan.parentSourceRefs()); refs.addAll(plan.parentRuntime()); refs.addAll(plan.jdkFiles());
        addBuildInputs(refs, parent);
        var frozenTools = ControlBuild.verifiedCompletedReceipt(plan.currentNativeBuild().qualifiedToolsBuildRef());
        addBuildInputs(refs, frozenTools);
        refs.addAll(shared.inputs()); refs.add(shared.executable());
        JsonNode standing = object(JSON.readTree(currentRead(binding.standingRef())));
        for (String field : List.of("qualified_tools_ref", "qualified_own_readback_ref", "source_grant_ref", "capacity_release_ref"))
            refs.add(ref(standing.get(field), "bytes"));
        JsonNode delivery = object(JSON.readTree(currentRead(binding.deliveryRef())));
        SharedOwnedCommandBinding.verifyAuthority(delivery, binding.deliveryExpectation(), MACHINE);
        require(sameRefs(readRefs(delivery.get("complete_runtime")), frozenTools.completeDeployment()),
                "original S26 delivery runtime differs");
        refs.addAll(readRefs(delivery.get("complete_runtime")));
        collectLeaseReferences(standing, refs, 0); collectLeaseReferences(delivery, refs, 0);
        refs.addAll(request.completeSources()); refs.addAll(request.tools().references()); refs.add(request.qualifiedToolsBuild());
        CurrentNativeBuild build = plan.currentNativeBuild();
        refs.addAll(List.of(build.frozenSourceActualRef(), build.environmentActualRef(), build.buildActualRef(),
                build.runtimeInventoryRef(), build.qualifiedToolsBuildRef(), build.injector()));
        if (!usesCurrentProvider(build)) refs.add(profile14());
        JsonNode source = object(JSON.readTree(currentRead(build.frozenSourceActualRef())));
        for (String field : List.of("request_ref", "capacity_ref")) refs.add(ref(source.get(field), "bytes"));
        refs.addAll(readRefs(source.get("complete_package_sources")));
        if (request.compileSourceBindingRef() == null)
            for (JsonNode row : array(source.get("input_witnesses"))) refs.add(ref(row.get("source"), "bytes"));
        else refs.add(request.compileSourceBindingRef());
        for (ControlBuild.FileRef actualPin : List.of(build.environmentActualRef(), build.buildActualRef())) {
            NativeBridgeBuild.Actual actual = NativeBridgeBuild.readActualEnvelope(actualPin);
            NativeBridgeBuild.Request original = NativeBridgeBuild.readRequest(actual.requestRef());
            refs.add(actual.requestRef()); refs.addAll(NativeBridgeRootGate.evidenceReferences(actual.grant()));
            refs.add(ControlBuild.FileRef.measure(original.stageRoot().resolve("INTENT.json")));
            refs.addAll(actual.runtimeRefs()); refs.addAll(actual.toolRefs()); refs.addAll(actual.graphRefs());
            refs.addAll(actual.dependencyRefs()); refs.addAll(actual.outputRefs());
            var sourceBinding = original.compileSourceBindingRef() == null ? null : NativeBridgeBuild.sourceBinding(original);
            refs.addAll(NativeBridgeBuild.sourceReferences(original, sourceBinding,
                    actual.sourceWitnesses().stream().map(witness -> Path.of(witness.source().path())).toList()));
            for (ControlBuild.FileRef optional : new ControlBuild.FileRef[]{actual.snapshotRef(), actual.manifestRef(), actual.helperReceiptRef()})
                if (optional != null) refs.add(optional);
            for (NativeBridgeBuild.Command command : actual.commands()) { refs.add(command.stdout()); refs.add(command.stderr()); }
            for (NativeBridgeBuild.AuxiliaryCommand auxiliary : actual.auxiliaryCommands())
                for (var image : List.of(auxiliary.outcome().binding().toolchain().vctip(),
                        auxiliary.outcome().binding().toolchain().mspdbsrv()))
                    refs.add(new ControlBuild.FileRef(image.canonicalPath(), image.bytes(), image.sha256()));
        }
        addCompleteHelperInputs(refs, (NativeBridgeDefender.ManifestRuntime) request.defender());
        refs.addAll(NativeBridgeDefender.readGraph(request).graphRefs());
        return mergeLeaseInputs(refs);
    }
    private static final int MAX_LEASE_FILES = 65536;
    /** Full source/JDK/Python launch leases have a separate bound from Native source inventories. */
    static List<ControlBuild.FileRef> mergeLeaseInputs(List<ControlBuild.FileRef> refs) throws IOException {
        Objects.requireNonNull(refs);
        LinkedHashMap<String,ControlBuild.FileRef> unique = new LinkedHashMap<>();
        for (ControlBuild.FileRef pin : refs) {
            String key = normalizedPath(pin.path());
            ControlBuild.FileRef prior = unique.putIfAbsent(key, pin);
            require(prior == null || prior.equals(pin), "conflicting current input pin");
            require(unique.size() <= MAX_LEASE_FILES, "finite source/JDK/full Python input lease extent exceeded");
        }
        return List.copyOf(unique.values());
    }
    private static List<ControlBuild.FileRef> uniqueLeaseInputs(List<ControlBuild.FileRef> refs) {
        Objects.requireNonNull(refs); var result = List.copyOf(refs);
        if (result.size() > MAX_LEASE_FILES
                || result.stream().map(pin -> normalizedPath(pin.path())).distinct().count() != result.size())
            throw new IllegalArgumentException("Finite unique exact launch lease pins required");
        return result;
    }
    /** Same complete original runtime file lease for all three exact UAC families. */
    private static void addCompleteHelperInputs(List<ControlBuild.FileRef> refs, NativeBridgeDefender.ManifestRuntime runtime) throws IOException {
        refs.addAll(runtime.references());
        NativeRegistrationRuntimeInventory.Manifest inventory = JSON.readValue(currentRead(runtime.inventoryRef()),
                NativeRegistrationRuntimeInventory.Manifest.class);
        collectLeaseReferences(object(JSON.readTree(currentRead(inventory.capacityRef()))), refs, 0);
        int index = 0, fileCount = 0;
        for (ControlBuild.FileRef pin : inventory.chunks()) {
            NativeRegistrationRuntimeInventory.Chunk chunk = JSON.readValue(currentRead(pin), NativeRegistrationRuntimeInventory.Chunk.class);
            require(chunk.index() == index++ && MACHINE.equals(chunk.machineId()), "runtime chunk chronology differs");
            for (SharedSourceFiles.Witness witness : chunk.files()) { refs.add(witness.source()); fileCount++; }
        }
        require(fileCount == inventory.fileCount(), "all actual Python helper dependency files must be leased");
    }
    private static void addBuildInputs(List<ControlBuild.FileRef> refs, ControlBuild.BuildReceipt build) throws IOException {
        refs.addAll(build.sourcePins()); refs.addAll(build.compiledSourcePins()); refs.addAll(build.completeDeployment());
        refs.addAll(build.producerRuntimePins()); refs.add(build.capacityReleaseRef()); refs.add(build.javaExecutableRef());
        refs.add(build.mavenToolchain().distributionLauncherRef());
        if (build.mavenToolchain().explicitOverrideRef() != null) refs.add(build.mavenToolchain().explicitOverrideRef());
        if (build.workpackageAccountingRef() != null) refs.add(build.workpackageAccountingRef());
        collectLeaseReferences(object(JSON.readTree(currentRead(build.capacityReleaseRef()))), refs, 0);
    }
    private static void requireCurrentUacCapacity(CurrentNativeBuildPlan plan, SharedOwnedCommand.Request shared,
            CurrentNativeStageSpec stage, SharedOwnedCommandBinding binding) throws IOException {
        ControlBuild.CapacityRelease release = JSON.readValue(currentRead(plan.uacCapacityRef()), ControlBuild.CapacityRelease.class);
        Instant opened = Instant.parse(release.observedAtUtc()), deadline = Instant.parse(release.reviewAtUtc()), now = Instant.now();
        long memory = Math.addExact(shared.memoryLimitBytes(), 3L * CURRENT_JVM_RESERVE);
        require(plan.uacCapacityRef().equals(stage.limits().capacityEvidence()),
                "one original joint Root release must cover the complete tree; no second charge or borrowed old inner hold");
        JsonNode standing = object(JSON.readTree(currentRead(binding.standingRef())));
        JsonNode resource = object(JSON.readTree(currentRead(ref(standing.get("capacity_release_ref"), "bytes"))));
        require("xar.root.resume61.actual-slot-resource/v1".equals(text(resource, "schema"))
                && "xar.current-native-build-uac-resource/v1".equals(text(resource, "uac_scope_schema"))
                && MACHINE.equals(text(resource, "machine_id")) && plan.owner().equals(text(resource, "owner"))
                && Instant.parse(plan.deadlineAtUtc()).equals(Instant.parse(text(resource, "actual_deadline_utc")))
                && ref(resource.get("REGISTER_typed_release_ref"), "bytes").equals(plan.uacCapacityRef())
                && ref(resource.get("uac_capacity_ref"), "bytes").equals(plan.uacCapacityRef())
                && integer(resource, "inner_job_hard_bytes") == shared.memoryLimitBytes()
                && integer(resource, "native_nested_job_hard_bytes") == stage.limits().memoryLimitBytes()
                && integer(resource, "outer_reservation_bytes") == CURRENT_JVM_RESERVE
                && integer(resource, "uac_parent_reservation_bytes") == CURRENT_JVM_RESERVE
                && integer(resource, "uac_admin_child_reservation_bytes") == CURRENT_JVM_RESERVE
                && integer(resource, "uac_total_memory_reservation_bytes") == memory,
                "fresh original slot must explicitly account for both current wrappers and one complete original S26 tree");
        long output = Math.addExact(stage.limits().outputAllocationLimitBytes(), 4L * CURRENT_LIMIT);
        require(MACHINE.equals(release.machineId()) && plan.owner().equals(release.ownerTask())
                && !now.isBefore(opened) && now.isBefore(deadline)
                && Instant.parse(plan.deadlineAtUtc()).equals(deadline) && release.memoryLimitBytes() >= memory
                && release.parts().getOrDefault("artifacts", 0L) >= output,
                "fresh same-owner whole UAC/Shared/REGISTER capacity is missing; original 1GiB worker is insufficient");
        List<Path> scopes = release.approvedOutputRoots().stream().map(Path::of).map(Path::toAbsolutePath).map(Path::normalize).toList();
        for (Path scope : scopes)
            require(!scope.equals(scope.getRoot()) && !scope.startsWith(Path.of(plan.currentNativeBuild().sourceRoot()))
                    && !Path.of(plan.currentNativeBuild().sourceRoot()).startsWith(scope), "whole-volume or immutable-source UAC scope rejected");
        for (Path target : List.of(Path.of(plan.outputRoot()), shared.outputRoot(), Path.of(plan.currentNativeBuild().buildRoot()),
                NativeBridgeBuild.readRequest(stage.requestRef()).scratchRoot(), binding.nativeTemporaryRoot(),
                Path.of(release.temporaryRoot()))) {
            require(scopes.stream().anyMatch(target::startsWith)
                    && release.volumes().keySet().stream().map(Path::of).anyMatch(volume -> volume.equals(target.getRoot())),
                    "whole UAC output and private temporary scopes need an actual explicit volume reservation");
        }
        require(binding.nativeTemporaryRoot().startsWith(Path.of(release.temporaryRoot()).toAbsolutePath().normalize()),
                "same approved native temporary root required");
        var policy = CiBootstrap.readPolicy(currentRead(release.policyRef()));
        for (var entry : release.volumes().entrySet()) {
            var volume = entry.getValue(); var override = release.quotaOverrides().get(entry.getKey());
            if (override != null) {
                require(override.task().equals(release.ownerTask()) && !Instant.parse(override.reviewAtUtc()).isAfter(deadline),
                        "UAC quota override owner/window differs");
                new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
            }
            require(volume.equals(CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(),
                    volume.thisWritePeak(), volume.otherUnspentReservations(), volume.systemGrowthReserve(),
                    volume.currentProjectUsageConservativeUpper(), override, opened, deadline))
                    && volume.thisWritePeak() >= output, "whole UAC capacity does not follow the shared storage policy");
        }
    }
    /** Conservative lease expansion only; each actual consumer above remains the qualification authority. */
    private static void collectLeaseReferences(JsonNode value, List<ControlBuild.FileRef> refs, int depth) throws IOException {
        require(depth <= 64 && refs.size() <= 131072, "bounded authority reference body required");
        if (value.isObject()) {
            if (keys(value).equals(Set.of("path", "bytes", "sha256"))) { refs.add(ref(value, "bytes")); return; }
            for (JsonNode child : value) collectLeaseReferences(child, refs, depth + 1);
        } else if (value.isArray()) {
            for (JsonNode child : value) collectLeaseReferences(child, refs, depth + 1);
        }
    }
    private static CurrentNativeBuildCompletion qualifyCurrentCompletion(CurrentPrepared prepared,
            WindowsJobProcess.CommandResult sharedProcess) throws IOException {
        require(sharedProcess != null && sharedProcess.passed()
                && normalizedPath(sharedProcess.identity().executable()).equals(normalizedPath(prepared.invocation().executable().path()))
                && sharedProcess.accounting().memoryLimitBytes() == Math.addExact(prepared.shared().memoryLimitBytes(), CURRENT_JVM_RESERVE),
                "original S26 Shared Java must exit naturally with its whole Job empty");
        ControlBuild.FileRef terminalRef = ControlBuild.FileRef.measure(prepared.shared().outputRoot().resolve("terminal.json"));
        CurrentSharedJavaTerminal terminal = parseCurrentSharedJavaTerminal(currentRead(terminalRef));
        require("xar.shared-owned-command-terminal/v2".equals(terminal.schema())
                && MACHINE.equals(terminal.machineId()) && terminal.status() == SharedOwnedCommand.Status.PASS
                && prepared.plan().owner().equals(terminal.owner()) && prepared.shared().slotId().equals(terminal.slotId())
                && terminal.borrowedSlotId() == null && prepared.invocation().specRef().equals(terminal.requestRef())
                && prepared.binding().standingRef().equals(terminal.standingRef())
                && prepared.binding().launcherSourceRef().equals(terminal.launcherSourceRef())
                && sameRefs(terminal.completeRuntime(), ControlBuild.verifiedCompletedReceipt(prepared.plan().currentNativeBuild().qualifiedToolsBuildRef()).completeDeployment())
                && terminal.outer() != null && terminal.outer().pidDecimal().equals(Long.toString(sharedProcess.identity().pid()))
                && terminal.outer().reservedMemoryBytes() == CURRENT_JVM_RESERVE && !terminal.outer().hardJobEnforced()
                && terminal.childStarted() && terminal.child() != null && terminal.child().passed()
                && normalizedPath(terminal.child().identity().executable()).equals(normalizedPath(prepared.invocation().executable().path()))
                && terminal.child().accounting().memoryLimitBytes() == prepared.shared().memoryLimitBytes()
                && terminal.inputPrecheck() == SharedOwnedCommand.Check.MATCH
                && terminal.inputPostcheck() == SharedOwnedCommand.Check.MATCH && terminal.runtimePostcheck() == SharedOwnedCommand.Check.MATCH
                && terminal.failure() == null && terminal.gameRpcCalls() == 0 && terminal.actualDriverOrSaveBodyReads() == 0,
                "exact original S26 v2 Java terminal, original source and all three MATCH checks required");
        require(Instant.parse(terminal.observedAtUtc()).isBefore(Instant.parse(prepared.plan().deadlineAtUtc()))
                && terminal.effectiveArguments().equals(currentEffectiveArguments(prepared))
                && terminal.outputNativeBytesWithDirectoryGuard() >= 0,
                "original Shared effective command, completion window or output facts differ");
        require(terminal.stdoutRef() != null && terminal.stderrRef() != null
                && Path.of(terminal.stdoutRef().path()).equals(prepared.shared().outputRoot().resolve("stdout.log"))
                && Path.of(terminal.stderrRef().path()).equals(prepared.shared().outputRoot().resolve("stderr.log")),
                "original Profile14 output binding differs");
        terminal.stdoutRef().verify(); terminal.stderrRef().verify();
        var witnessed = new ArrayList<ControlBuild.FileRef>();
        for (SharedSourceFiles.Witness witness : terminal.inputBefore()) { SharedSourceFiles.assertUnchanged(witness); witnessed.add(witness.source()); }
        var expected = new ArrayList<ControlBuild.FileRef>(prepared.shared().inputs());
        expected.add(prepared.invocation().bindingRef()); expected.add(prepared.invocation().executable());
        require(sameRefs(witnessed, expected), "original Shared complete input witnesses differ");
        ControlBuild.FileRef actualRef = ControlBuild.FileRef.measure(prepared.request().stageRoot().resolve("ACTUAL.json"));
        NativeBridgeBuild.Actual actual = NativeBridgeBuild.readAccepted(actualRef, NativeBridgeBuild.Stage.REGISTER);
        CurrentNativeStageSpec stage = prepared.stage();
        require(NativeBridgeBuild.ACTUAL_SCHEMA.equals(actual.schema()) && actual.requestRef().equals(stage.requestRef())
                && actual.grant().ownerTask().equals(prepared.plan().owner())
                && actual.grant().capacityEvidence().equals(stage.limits().capacityEvidence())
                && actual.grant().deadline().equals(stage.limits().deadline())
                && actual.grant().timeoutSeconds() == stage.limits().timeoutSeconds()
                && actual.grant().memoryLimitBytes() == stage.limits().memoryLimitBytes()
                && actual.grant().outputAllocationLimitBytes() == stage.limits().outputAllocationLimitBytes()
                && actual.outputRefs().equals(List.of(prepared.plan().currentNativeBuild().injector()))
                && actual.commands().size() == 1 && actual.commands().getFirst().kind() == NativeBridgeBuild.CommandKind.DEFENDER_HELPER,
                "completed original REGISTER source/request/grant or exact injector differs");
        NativeBridgeBuild.Command helper = actual.commands().getFirst();
        require(helper.owner() != null && helper.terminal() != null && helper.owner().equals(helper.terminal().identity())
                && helper.terminal().passed() && helper.owner().pid() != sharedProcess.identity().pid()
                && helper.owner().pid() != terminal.child().identity().pid(),
                "the actual helper is its original Python process, not either Java wrapper");
        JsonNode receipt = object(JSON.readTree(currentRead(actual.helperReceiptRef())));
        ThreeSettingsReadback settings = qualifyThreeSettings(receipt, prepared.plan().expectedOwnerSid(), helper.owner());
        terminalRef.verify(); actualRef.verify(); actual.manifestRef().verify(); actual.helperReceiptRef().verify();
        return new CurrentNativeBuildCompletion(terminalRef, actualRef, actual.manifestRef(), actual.helperReceiptRef(),
                sharedProcess.identity(), helper.owner(), settings);
    }
    private static List<String> currentEffectiveArguments(CurrentPrepared prepared) {
        Path temporary = prepared.binding().privateTemporaryAggregateRoot().resolve(prepared.shared().slotId().replace('/', '_'))
                .resolve(prepared.shared().owner().substring(6).replace('/', '_')).resolve(prepared.shared().runId());
        var result = new ArrayList<>(List.of("-Djava.io.tmpdir=" + temporary, "-Djna.tmpdir=" + prepared.binding().nativeTemporaryRoot(),
                "-XX:ErrorFile=" + prepared.shared().outputRoot().resolve("hs_err_pid%p.log"),
                "-XX:ReplayDataFile=" + prepared.shared().outputRoot().resolve("replay_pid%p.log"),
                "-XX:HeapDumpPath=" + prepared.shared().outputRoot()));
        result.addAll(prepared.shared().arguments()); return List.copyOf(result);
    }
    /** Pure extra readback gate. Existing original Native reader separately checks the exact manifest/path result. */
    static ThreeSettingsReadback qualifyThreeSettings(JsonNode receipt, String expectedOwnerSid,
            WindowsJobProcess.ProcessIdentity helper) throws IOException {
        return qualifyThreeSettings(receipt, expectedOwnerSid, helper.pid());
    }
    private static ThreeSettingsReadback qualifyThreeSettings(JsonNode receipt, String expectedOwnerSid, long helperPid) throws IOException {
        require(!receipt.has("broker_schema"), "Direct same-owner helper cannot import a SYSTEM broker receipt");
        return qualifyThreeSettingsPayload(receipt, expectedOwnerSid, helperPid);
    }
    /** Typed DATA gate used only after the independent protected-broker manifest/proof reader. */
    static ThreeSettingsReadback qualifyProtectedBrokerSettings(JsonNode receipt) throws IOException {
        require(NativeBridgeDefender.BROKER_NULLABLE_SCHEMA.equals(text(receipt, "broker_schema"))
                && NULLABLE_SETTINGS_SCHEMA.equals(text(receipt, "settings_readback_schema"))
                && "S-1-5-18".equals(text(receipt, "system_token_sid")),
                "Explicit nullable SYSTEM broker version2 required");
        long workerPid = integer(receipt, "settings_readback_process_id");
        require(workerPid > 0 && workerPid <= 0xffff_ffffL, "Actual bounded SYSTEM worker PID required");
        return qualifyThreeSettingsPayload(receipt, "S-1-5-18", workerPid);
    }
    private static ThreeSettingsReadback qualifyThreeSettingsPayload(JsonNode receipt, String expectedOwnerSid, long helperPid) throws IOException {
        require("verified".equals(text(receipt, "status"))
                && bool(receipt, "admin_token") && !bool(receipt, "settings_success_is_runtime_trust")
                && bool(receipt, "settings_readback_complete") && receipt.has("settings_readback_error")
                && receipt.get("settings_readback_error").isNull()
                && bool(receipt, "observed_extensions_unchanged") && bool(receipt, "observed_processes_unchanged")
                && integer(receipt, "settings_readback_process_id") == helperPid,
                "same-helper complete three-settings readback with no latched error required");
        requireSameOwnerSid(expectedOwnerSid, text(receipt, "settings_readback_token_user_sid"));
        String schema = text(receipt, "settings_readback_schema");
        ThreeSettingsReadback proof;
        if (SETTINGS_SCHEMA.equals(schema)) {
            require(!receipt.has("before_property_observations") && !receipt.has("after_property_observations")
                    && !receipt.has("nullable_observation_scope"), "Version1 cannot acquire nullable property evidence");
            var before = JSON.treeToValue(object(receipt.get("before_settings")), DefenderSettings.class);
            var after = JSON.treeToValue(object(receipt.get("after_settings")), DefenderSettings.class);
            proof = new ArraySettingsReadback(schema, before, after, expectedOwnerSid, Long.toString(helperPid));
        } else {
            require(NULLABLE_SETTINGS_SCHEMA.equals(schema), "Unknown three-settings readback version");
            try {
                proof = new NullableSettingsReadback(schema,
                        JSON.treeToValue(object(receipt.get("before_settings")), NullableDefenderSettings.class),
                        JSON.treeToValue(object(receipt.get("after_settings")), NullableDefenderSettings.class),
                        expectedOwnerSid, Long.toString(helperPid),
                        List.of(JSON.treeToValue(array(receipt.get("before_property_observations")), ProviderPropertyObservation[].class)),
                        List.of(JSON.treeToValue(array(receipt.get("after_property_observations")), ProviderPropertyObservation[].class)),
                        text(receipt, "nullable_observation_scope"));
            } catch (IllegalArgumentException | NullPointerException invalid) {
                throw new IOException("Invalid original observed nullable property evidence", invalid);
            }
        }
        var before = proof.before(); var after = proof.after();
        require(before.exclusionPath().equals(strings(receipt.get("before")))
                && after.exclusionPath().equals(strings(receipt.get("after")))
                && sameNonpath(before.exclusionExtension(), after.exclusionExtension())
                && sameNonpath(before.exclusionProcess(), after.exclusionProcess())
                && pathSet(after.exclusionPath()).containsAll(pathSet(before.exclusionPath())),
                "before/after three-settings payload changed non-Path settings or the original path receipt");
        return proof;
    }
    private static boolean sameNonpath(List<String> before, List<String> after) {
        return before == null || after == null ? before == null && after == null : new HashSet<>(before).equals(new HashSet<>(after));
    }
    static CurrentSharedJavaTerminal parseCurrentSharedJavaTerminal(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= CURRENT_LIMIT, "bounded original S26 Java terminal required");
        CurrentSharedJavaTerminal terminal = JSON.readValue(raw, CurrentSharedJavaTerminal.class);
        require("xar.shared-owned-command-terminal/v2".equals(terminal.schema()), "original v2 Java terminal required; no relabelled v3/v4 evidence");
        return terminal;
    }
    /** Executes only the exact current plan whose bytes and original deadline Root reviewed. */
    public static CurrentNativeBuildResult executeCurrentNativeBuildReviewed(Path path, String reviewedPlanSha256,
            String actualSharedStageDeadlineUtc) throws IOException {
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(path.toRealPath());
        requireReviewedPlan(planRef, reviewedPlanSha256);
        CurrentNativeBuildPlan plan = parseCurrentNativeBuildPlan(currentRead(planRef));
        requireSharedStageDeadline(plan.deadlineAtUtc(), actualSharedStageDeadlineUtc);
        requireCurrentProviderExecution(plan);
        CurrentPrepared prepared = prepareCurrent(plan, planRef, Instant.now().toString(), true);
        CurrentLaunchOperation operation = new CurrentLaunchOperation(prepared);
        LaunchOutcome observed = launch(operation);
        ControlBuild.FileRef outcomeRef = Files.isRegularFile(Path.of(plan.adminChildOutcomePath()), LinkOption.NOFOLLOW_LINKS)
                ? ControlBuild.FileRef.measure(Path.of(plan.adminChildOutcomePath())) : null;
        CurrentNativeBuildResult result = new CurrentNativeBuildResult("xar.current-native-build-uac-result/v1", MACHINE,
                observed.observedAtUtc(), observed.status(),
                observed.status() == Status.VERIFIED ? ProofScope.SAME_OWNER_ADMIN_SHARED_REGISTER_THREE_SETTINGS : null,
                prepared.review(), observed.launchCallEntered(), observed.shellAcknowledged(), observed.launchWin32Error(),
                observed.processIdentity(), observed.tokenElevated(), observed.ownerSid(), observed.processExitCodeDecimal(),
                observed.waitTimedOut(), outcomeRef,
                observed.completion() == null ? null : observed.completion().currentNativeBuild(),
                observed.diagnostics(), false, false, observed.terminalProof());
        writeNew(Path.of(plan.resultPath()), result); return result;
    }
    private static final class CurrentLaunchOperation implements LaunchOperation {
        private final CurrentPrepared prepared;
        private ControlBuild.FileRef intentRef;
        private CurrentLaunchOperation(CurrentPrepared prepared) { this.prepared=prepared; }
        public String deadlineAtUtc() { return prepared.plan().deadlineAtUtc(); }
        public int waitSeconds() { return prepared.plan().waitSeconds(); }
        public ControlBuild.FileRef image() { return prepared.invocation().executable(); }
        public String parameters() { return prepared.review().lpParameters(); }
        public String directory() { return prepared.review().lpDirectory(); }
        public String expectedOwnerSid() { return prepared.plan().expectedOwnerSid(); }
        public Apis nativeApis() throws IOException { return currentApis(prepared.binding()); }
        public List<ControlBuild.FileRef> inputs() { return prepared.inputs(); }
        public void revalidate() throws IOException {
            require(Instant.now().isBefore(Instant.parse(deadlineAtUtc())), "current same-owner UAC original deadline expired");
            requireCurrentJvm(prepared.binding());
            for (String name : currentOutputPaths(prepared.plan()))
                require(Files.notExists(Path.of(name), LinkOption.NOFOLLOW_LINKS), "current attempt already claimed; no replay");
            require(Files.notExists(prepared.shared().outputRoot(), LinkOption.NOFOLLOW_LINKS)
                    && Files.notExists(prepared.request().stageRoot(), LinkOption.NOFOLLOW_LINKS),
                    "original S26 REGISTER already claimed; no replay");
        }
        public void claim(List<GuardedInput> guards) throws IOException {
            writeNew(Path.of(prepared.plan().intentPath()), new CurrentNativeBuildIntent("xar.current-native-build-uac-intent/v1",
                    MACHINE, Instant.now().toString(), prepared.review(), guards, NO_RETRY));
            intentRef=ControlBuild.FileRef.measure(Path.of(prepared.plan().intentPath()));
        }
        public ControlBuild.FileRef claimedIntentRef() { return intentRef; }
        public void observe(ProcessIdentity child, boolean elevated, String sid) throws IOException {
            writeNew(Path.of(prepared.plan().launchObservationPath()), new CurrentNativeBuildLaunch(
                    "xar.current-native-build-uac-launch/v1", MACHINE, Instant.now().toString(), true, child, elevated, sid));
        }
        public CompletedRegistration complete(TerminalProof terminal) throws IOException {
            CurrentAdminChildOutcome outcome = JSON.readValue(currentRead(ControlBuild.FileRef.measure(
                    Path.of(prepared.plan().adminChildOutcomePath()))), CurrentAdminChildOutcome.class);
            require("xar.current-native-build-admin-child-outcome/v1".equals(outcome.schema())
                    && MACHINE.equals(outcome.machineId()) && outcome.planRef().equals(prepared.review().planRef())
                    && outcome.originalParentIntentRef().equals(intentRef)
                    && terminal.processIdentity().equals(outcome.processIdentity()) && outcome.tokenElevated(),
                    "same actual admin-child outcome and original parent intent required");
            requireSameOwnerSid(expectedOwnerSid(), outcome.tokenUserSid());
            ControlBuild.FileRef childIntent = ControlBuild.FileRef.measure(Path.of(prepared.plan().adminChildIntentPath()));
            require(childIntent.equals(outcome.adminChildIntentRef()), "original admin-child one-shot intent differs");
            CurrentAdminChildIntent claim = JSON.readValue(currentRead(childIntent), CurrentAdminChildIntent.class);
            require("xar.current-native-build-admin-child-intent/v1".equals(claim.schema())
                    && MACHINE.equals(claim.machineId()) && claim.planRef().equals(prepared.review().planRef())
                    && claim.originalParentIntentRef().equals(intentRef) && claim.processIdentity().equals(terminal.processIdentity())
                    && claim.tokenElevated() && NO_RETRY.equals(claim.unresolvedActionPolicy()),
                    "admin-child must have checked actual identity before claiming its sole original command");
            requireSameOwnerSid(expectedOwnerSid(), claim.tokenUserSid());
            if (!"0".equals(terminal.processExitCodeDecimal()) || outcome.status() != Status.VERIFIED)
                return new CompletedRegistration(Status.UNKNOWN, null, null, null);
            require(outcome.diagnostics().isEmpty() && outcome.sharedProcess() != null && outcome.sharedProcess().passed(),
                    "actual original S26 process terminal unavailable");
            CurrentNativeBuildCompletion completed = qualifyCurrentCompletion(prepared, outcome.sharedProcess());
            require(completed.equals(outcome.completion()), "admin-child and parent independently read different original completion data");
            return new CompletedRegistration(Status.VERIFIED, ProofScope.SAME_OWNER_ADMIN_SHARED_REGISTER_THREE_SETTINGS,
                    completed.helperReceiptRef(), completed);
        }
    }

    /** Restricted role in this existing class: never accepts an executable or command from CLI arguments. */
    private static CurrentAdminChildOutcome executeCurrentAdminChild(ControlBuild.FileRef planRef, String actualDeadline) throws IOException {
        CurrentNativeBuildPlan plan = parseCurrentNativeBuildPlan(currentRead(planRef));
        requireSharedStageDeadline(plan.deadlineAtUtc(), actualDeadline);
        requireCurrentProviderExecution(plan);
        CurrentPrepared prepared = prepareCurrent(plan, planRef, Instant.now().toString(), false);
        Apis apis = currentApis(prepared.binding());
        List<Guard> guards = new ArrayList<>();
        List<String> diagnostics = new ArrayList<>();
        ControlBuild.FileRef parentIntentRef = null, childIntentRef = null;
        ProcessIdentity self = null;
        String sid = null;
        boolean elevated = false;
        WindowsJobProcess.CommandResult sharedResult = null;
        CurrentNativeBuildCompletion completion = null;
        Status status = Status.UNKNOWN;
        try {
            for (ControlBuild.FileRef pin : prepared.inputs()) guards.add(Guard.open(apis.kernel(), pin));
            parentIntentRef = ControlBuild.FileRef.measure(Path.of(plan.intentPath()));
            guards.add(Guard.open(apis.kernel(), parentIntentRef));
            CurrentNativeBuildIntent parent = JSON.readValue(currentRead(parentIntentRef), CurrentNativeBuildIntent.class);
            require("xar.current-native-build-uac-intent/v1".equals(parent.schema()) && MACHINE.equals(parent.machineId())
                    && parent.review().planRef().equals(planRef) && NO_RETRY.equals(parent.unresolvedActionPolicy())
                    && parent.review().lpFile().equals(prepared.review().lpFile())
                    && parent.review().lpParameters().equals(prepared.review().lpParameters())
                    && parent.review().guardedInputRefs().equals(prepared.inputs())
                    && parent.review().deadlineAtUtc().equals(plan.deadlineAtUtc()),
                    "original same-plan parent intent and exact reviewed command required");
            verifyGuards(guards);
            require(parent.guardedInputs().equals(guards.subList(0, prepared.inputs().size()).stream().map(Guard::evidence).toList()),
                    "admin-child physical source/JDK inputs differ from the held parent input identities");
            requireCurrentJvm(prepared.binding());
            WinNT.HANDLE current = apis.kernel().GetCurrentProcess(); // Pseudo-handle is valid for these APIs and is never closed.
            self = identity(apis.kernel(), current);
            elevated = tokenElevated(apis, current);
            sid = tokenUserSid(apis, current);
            require(elevated && normalizedPath(self.executable()).equals(normalizedPath(prepared.invocation().executable().path())),
                    "actual admin-child must be the approved elevated Java image");
            requireSameOwnerSid(plan.expectedOwnerSid(), sid);
            require(Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc())), "original admin-child deadline expired");
            require(Files.notExists(Path.of(plan.adminChildOutcomePath()), LinkOption.NOFOLLOW_LINKS)
                    && Files.notExists(prepared.shared().outputRoot(), LinkOption.NOFOLLOW_LINKS)
                    && Files.notExists(prepared.request().stageRoot(), LinkOption.NOFOLLOW_LINKS),
                    "original managed command was already attempted; UNKNOWN cannot be replayed");
            writeNew(Path.of(plan.adminChildIntentPath()), new CurrentAdminChildIntent(
                    "xar.current-native-build-admin-child-intent/v1", MACHINE, Instant.now().toString(), planRef,
                    parentIntentRef, self, elevated, sid, guards.stream().map(Guard::evidence).toList(), NO_RETRY));
            childIntentRef = ControlBuild.FileRef.measure(Path.of(plan.adminChildIntentPath()));
            guards.add(Guard.open(apis.kernel(), childIntentRef));
            verifyGuards(guards);
            java.util.Map<String,String> environment = currentSharedEnvironment(prepared.invocation());
            WindowsJobProcess.CommandSpec command = new WindowsJobProcess.CommandSpec(
                    Path.of(prepared.invocation().executable().path()), prepared.invocation().arguments(),
                    Path.of(prepared.invocation().cwd()), environment, Path.of(plan.sharedStdoutPath()),
                    Path.of(plan.sharedStderrPath()), Math.addExact(prepared.shared().memoryLimitBytes(), CURRENT_JVM_RESERVE));
            try (WindowsJobProcess original = WindowsJobProcess.start(command)) {
                sharedResult = original.await(Duration.ofSeconds(prepared.shared().timeoutSeconds()),
                        Instant.parse(plan.deadlineAtUtc()), () -> {
                            try {
                                require(Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc())), "original UAC deadline expired");
                                planRef.verify(); prepared.binding().standingRef().verify(); plan.uacCapacityRef().verify();
                            } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
                        });
            }
            verifyGuards(guards);
            completion = qualifyCurrentCompletion(prepared, sharedResult);
            require(Instant.now().isBefore(Instant.parse(plan.deadlineAtUtc())), "original same-owner terminal arrived after deadline");
            status = Status.VERIFIED;
        } catch (InterruptedException failure) {
            Thread.currentThread().interrupt(); diagnostics.add("Interrupted: original managed Job cleanup follows its existing owner; no retry");
        } catch (IOException | RuntimeException failure) {
            diagnostics.add(failure.getClass().getName() + ": " + failure.getMessage());
        } finally {
            for (int index = guards.size() - 1; index >= 0; index--)
                try { guards.get(index).close(); }
                catch (IOException failure) { diagnostics.add(failure.getMessage()); status=Status.UNKNOWN; }
        }
        CurrentAdminChildOutcome outcome = new CurrentAdminChildOutcome("xar.current-native-build-admin-child-outcome/v1",
                MACHINE, Instant.now().toString(), status, planRef, parentIntentRef, childIntentRef, self, elevated, sid,
                sharedResult, completion, diagnostics);
        // A failure before the prewrite identity gate has no child intent and never launches Shared.
        writeNew(Path.of(plan.adminChildOutcomePath()), outcome); return outcome;
    }
    private static Apis currentApis(SharedOwnedCommandBinding binding) throws IOException {
        requireCurrentJvm(binding);
        return readOnlyApis();
    }
    private static void requireCurrentJvm(SharedOwnedCommandBinding binding) throws IOException {
        Path temporary = binding.nativeTemporaryRoot().toRealPath();
        require(temporary.startsWith(Path.of(CURRENT_STATE_ROOT).resolve("tmp").toRealPath()),
                "current admitted native temporary root required");
        require(Path.of(System.getProperty("jna.tmpdir", "")).toRealPath().equals(temporary)
                && Path.of(System.getProperty("java.io.tmpdir", "")).toRealPath().equals(temporary),
                "actual current parent/admin JVM temporary properties differ from approved command");
        List<String> expected = List.of("-Xms32m", "-Xmx128m", "-XX:+ExitOnOutOfMemoryError",
                "-Djava.io.tmpdir=" + binding.nativeTemporaryRoot(), "-Djna.tmpdir=" + binding.nativeTemporaryRoot());
        require(java.lang.management.ManagementFactory.getRuntimeMXBean().getInputArguments().equals(expected),
                "current parent/admin JVM options must exactly match the reviewed input-closed invocation");
        for (String key : System.getenv().keySet())
            require(JAVA_OPTION_ENVIRONMENT.stream().noneMatch(blocked -> blocked.equalsIgnoreCase(key)),
                    "inherited Java option variables are outside the reviewed current command");
    }
    private static java.util.Map<String,String> currentSharedEnvironment(ManagedRegisterInvocation invocation) {
        java.util.TreeMap<String,String> environment = new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        for (String key : invocation.unsetEnvironment()) environment.remove(key);
        environment.putAll(invocation.environment()); return java.util.Map.copyOf(environment);
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
    private static String tokenUserSid(Apis apis, WinNT.HANDLE process) throws IOException {
        WinNT.HANDLEByReference token = new WinNT.HANDLEByReference();
        require(apis.security().OpenProcessToken(process, 0x8, token), "actual TokenUser token query unavailable");
        try {
            IntByReference required = new IntByReference();
            boolean first = apis.security().GetTokenInformation(token.getValue(), 1, Pointer.NULL, 0, required);
            int firstError = Native.getLastError();
            int headerBytes = new WinNT.TOKEN_USER().size();
            require(!first && firstError == 122 && headerBytes == 16
                    && required.getValue() >= headerBytes && required.getValue() <= 65536,
                    "actual TokenUser buffer extent unavailable");
            try (Memory information = new Memory(required.getValue())) {
                IntByReference returned = new IntByReference();
                require(apis.security().GetTokenInformation(token.getValue(), 1, information,
                        Math.toIntExact(information.size()), returned)
                        && returned.getValue() >= headerBytes && returned.getValue() <= information.size(),
                        "actual TokenUser data unavailable");
                Pointer sid = information.getPointer(0);
                long base = Pointer.nativeValue(information), address = Pointer.nativeValue(sid);
                long offset = address - base;
                require(sid != null && offset >= headerBytes && offset <= returned.getValue() - 8L,
                        "actual TokenUser SID header lies outside its returned buffer");
                int count = Byte.toUnsignedInt(information.getByte(offset + 1));
                long sidBytes = 8L + 4L * count;
                require(count >= 1 && count <= 15 && sidBytes <= returned.getValue() - offset
                        && Byte.toUnsignedInt(information.getByte(offset)) == 1,
                        "actual TokenUser SID extent/revision unavailable");
                com.sun.jna.ptr.PointerByReference converted = new com.sun.jna.ptr.PointerByReference();
                require(apis.security().ConvertSidToStringSidW(sid, converted)
                        && converted.getValue() != null && Pointer.nativeValue(converted.getValue()) != 0,
                        "actual TokenUser SID string unavailable");
                try {
                    String value = converted.getValue().getWideString(0);
                    requireCanonicalSid(value);
                    return value;
                } finally {
                    require(apis.kernel().LocalFree(converted.getValue()) == null, "native SID string release failed");
                }
            }
        } finally { require(apis.kernel().CloseHandle(token.getValue()), "actual TokenUser token handle close failed"); }
    }
    static void requireCanonicalSid(String sid) throws IOException {
        require(sid != null && sid.length() <= 184 && sid.matches("S-1-[0-9]+(?:-[0-9]+){1,15}"),
                "full canonical Windows SID required");
        String[] words = sid.substring(4).split("-");
        for (int index = 0; index < words.length; index++) {
            String word = words[index];
            require(word.equals("0") || word.matches("[1-9][0-9]*"), "noncanonical Windows SID component");
            require(new BigInteger(word).bitLength() <= (index == 0 ? 48 : 32), "Windows SID component exceeds its native width");
        }
    }
    static void requireSameOwnerSid(String expected, String observed) throws IOException {
        requireCanonicalSid(expected); requireCanonicalSid(observed);
        require(expected.equals(observed), "actual TokenUser differs from the full approved owner SID");
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
                Native.load(system.resolve("advapi32.dll").toString(), TokenAdvapi32.class, W32APIOptions.UNICODE_OPTIONS));
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


    private static final String DECLARED_PLAN_SCHEMA = "xar.native-declared-exe-uac-plan/v1";
    public record DeclaredPathCard(String schema, String machineId, String owner, String observedAtUtc, String deadlineAtUtc,
            String sourceRoot, String buildRoot, String exactOutputPath, String outputRoot, String temporaryRoot,
            int timeoutSeconds, long memoryReservationBytes, long outputAllocationLimitBytes, ControlBuild.FileRef capacityReleaseRef) {
        public DeclaredPathCard {
            if (!"xar.native-declared-exe-uac-resource/v1".equals(schema) || timeoutSeconds < 1 || timeoutSeconds > 7200
                    || memoryReservationBytes < (256L << 20) || outputAllocationLimitBytes < (4L << 20))
                throw new IllegalArgumentException("Finite dedicated declared-path capacity required");
            Objects.requireNonNull(capacityReleaseRef);
        }
    }
    public record DeclaredPathPlan(String schema, String machineId, String observedAtUtc, String deadlineAtUtc,
            String owner, String expectedOwnerSid, int waitSeconds, ControlBuild.FileRef sourceDeclarationRef,
            ControlBuild.FileRef declarationRequestRef, ControlBuild.FileRef resourceCardRef,
            ControlBuild.FileRef parentToolsBuildRef, List<ControlBuild.FileRef> parentSourceRefs,
            List<ControlBuild.FileRef> parentRuntime, NativeBridgeDefender.ManifestRuntime defenderRuntime,
            ControlBuild.FileRef manifestRef, String outputRoot, String helperReceiptPath,
            String intentPath, String launchObservationPath, String resultPath) {
        public DeclaredPathPlan {
            if (!DECLARED_PLAN_SCHEMA.equals(schema)) throw new IllegalArgumentException("Declared-path plan version required");
            parentSourceRefs = NativeBridgeBuild.unique(parentSourceRefs); parentRuntime = NativeBridgeBuild.unique(parentRuntime);
            Objects.requireNonNull(sourceDeclarationRef); Objects.requireNonNull(declarationRequestRef);
            Objects.requireNonNull(resourceCardRef); Objects.requireNonNull(parentToolsBuildRef);
            Objects.requireNonNull(defenderRuntime); Objects.requireNonNull(manifestRef);
        }
    }
    public record DeclaredPathReview(String schema, String machineId, String observedAtUtc, ControlBuild.FileRef planRef,
            ControlBuild.FileRef sourceDeclarationRef, ControlBuild.FileRef manifestRef, String manifestSemanticSha256,
            NativeBridgeDefender.DeclaredOutput output, String expectedOwnerSid, String lpVerb, String lpFile,
            String lpParameters, String lpDirectory, int nShow, int waitSeconds, String deadlineAtUtc,
            List<ControlBuild.FileRef> guardedInputRefs) {
        public DeclaredPathReview { guardedInputRefs = uniqueLeaseInputs(guardedInputRefs); }
    }
    public record DeclaredPathIntent(String schema, String machineId, String observedAtUtc, DeclaredPathReview review,
            List<GuardedInput> guardedInputs, String unresolvedActionPolicy) {
        public DeclaredPathIntent { guardedInputs = List.copyOf(guardedInputs); }
    }
    public record DeclaredPathResult(String schema, String machineId, String observedAtUtc, Status status, ProofScope proofScope,
            DeclaredPathReview review, boolean launchCallEntered, boolean shellAcknowledged, Integer launchWin32Error,
            ProcessIdentity processIdentity, Boolean tokenElevated, String tokenUserSid, String processExitCodeDecimal,
            boolean waitTimedOut, ControlBuild.FileRef helperReceiptRef, ThreeSettingsReadback settings,
            List<String> diagnostics, boolean automaticallyRetried, boolean elevatedProcessTerminated, TerminalProof terminalProof) {
        public DeclaredPathResult { diagnostics = List.copyOf(diagnostics); }
    }
    private record DeclaredPrepared(DeclaredPathPlan plan, DeclaredPathReview review, NativeBridgeBuild.Request request,
            NativeBridgeDefender.ConfiguredGraph graph, DeclaredPathCard card, List<ControlBuild.FileRef> inputs,
            List<SharedSourceFiles.Witness> sourceBefore) {
        private DeclaredPrepared { inputs = uniqueLeaseInputs(inputs); sourceBefore = List.copyOf(sourceBefore); }
    }
    public static DeclaredPathPlan parseDeclaredPathPlan(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= CURRENT_LIMIT, "Bounded exact declared path plan required");
        return CURRENT_NATIVE_JSON.readValue(raw, DeclaredPathPlan.class);
    }
    /** Writes a candidate and fully reviews it; no settings action or Native qualification is issued. */
    public static ControlBuild.FileRef writeDeclaredPathPlan(DeclaredPathPlan plan, Path output) throws IOException {
        NativeBridgeBuild.absolute(output); SharedSourceFiles.plainAncestors(output.getParent());
        require(output.getParent().toRealPath().equals(Path.of(plan.outputRoot()).toRealPath()), "Candidate plan must use its exact control root");
        writeNew(output, plan); var pin = ControlBuild.FileRef.measure(output);
        prepareDeclared(plan, pin, true); return pin;
    }
    public static DeclaredPathReview reviewDeclaredPath(Path path) throws IOException {
        var pin = ControlBuild.FileRef.measure(path.toRealPath());
        return prepareDeclared(parseDeclaredPathPlan(currentRead(pin)), pin, true).review();
    }
    private static DeclaredPrepared prepareDeclared(DeclaredPathPlan plan, ControlBuild.FileRef planPin, boolean fresh) throws IOException {
        require(DECLARED_PLAN_SCHEMA.equals(plan.schema()) && MACHINE.equals(plan.machineId())
                && MACHINE.equals(WindowsJobProcess.currentMachineId()) && "/root/native_execution".equals(plan.owner()),
                "Current machine and exact Native declaration owner required");
        requireCanonicalSid(plan.expectedOwnerSid());
        require(plan.waitSeconds() > 0 && plan.waitSeconds() <= 7200, "Finite whole declared-path wait required");
        ControlBuild.BuildReceipt parent = ControlBuild.verifiedCompletedReceipt(plan.parentToolsBuildRef());
        require(parent.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && sameRefs(parent.completeDeployment(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(NativeProjectExeUac.class), plan.parentRuntime())
                && sameRefs(parent.sourcePins(), plan.parentSourceRefs()), "Exact completed current producer source/runtime required");
        NativeBridgeBuild.Request request = NativeBridgeBuild.readRequest(plan.declarationRequestRef());
        require((NativeBridgeBuild.REQUEST_SCHEMA.equals(request.schema()) || NativeBridgeBuild.BOUND_REQUEST_SCHEMA.equals(request.schema())) && request.stage() == NativeBridgeBuild.Stage.ENV
                && MACHINE.equals(request.machineId()) && request.qualifiedToolsBuild().equals(plan.parentToolsBuildRef())
                && request.canonicalRepository().equals(REPO.toRealPath()) && request.defender() == null,
                "Declaration uses exact current source inputs, not an invented accepted ENV/BUILD");
        NativeBridgeBuild.validateSources(request);
        var sourceBefore = NativeBridgeBuild.observeRequestSources(request);
        NativeBridgeDefender.requireDirectHelperRuntime(plan.defenderRuntime());
        require(NativeBridgeDefender.directBaseRuntime(request.canonicalRepository(), plan.defenderRuntime().inventoryRef())
                .equals(plan.defenderRuntime()), "declared helper differs from the actual direct-base inventory producer");
        var declaration = CURRENT_NATIVE_JSON.readValue(currentRead(plan.sourceDeclarationRef()), NativeBridgeDefender.DeclaredSource.class);
        require(MACHINE.equals(declaration.machineId()) && declaration.declarationRequestRef().equals(plan.declarationRequestRef())
                && declaration.producerToolsBuildRef().equals(plan.parentToolsBuildRef()), "Reviewed source declaration causal identity differs");
        requireConfiguredDeclaration(declaration.configureActualRef(), request);
        var graph = NativeBridgeDefender.readDeclaredGraph(request);
        require(sameRefs(graph.graphRefs(), declaration.configuredGraphRefs()), "Actual declaration graph witnesses changed");
        var manifest = NativeBridgeDefender.declaredManifest(request, graph, plan.sourceDeclarationRef());
        var observedManifest = CURRENT_NATIVE_JSON.readValue(currentRead(plan.manifestRef()), NativeBridgeDefender.DeclaredManifest.class);
        require(manifest.equals(observedManifest), "Original Java declaration producer and exact manifest differ");
        DeclaredPathCard card = CURRENT_NATIVE_JSON.readValue(currentRead(plan.resourceCardRef()), DeclaredPathCard.class);
        requireDeclaredCapacity(plan, request, graph.output(), card);
        Path output = Path.of(plan.outputRoot()).toRealPath(); NativeBridgeBuild.plainDirectory(output);
        var outputs = new HashSet<Path>();
        for (String name : List.of(plan.helperReceiptPath(), plan.intentPath(), plan.launchObservationPath(), plan.resultPath())) {
            Path target = Path.of(name).toAbsolutePath().normalize();
            require(target.getParent().equals(output) && outputs.add(target), "Distinct exact declared-path result names required");
            if (fresh) require(Files.notExists(target, LinkOption.NOFOLLOW_LINKS), "Original intent/output exists; UNKNOWN never permits replay");
        }
        require(!output.startsWith(request.sourceRoot()) && !request.sourceRoot().startsWith(output)
                && !output.startsWith(request.buildRoot()) && !request.buildRoot().startsWith(output), "Declaration controls must be disjoint from source/build");
        Instant now = Instant.now(), observed = Instant.parse(plan.observedAtUtc()), deadline = Instant.parse(plan.deadlineAtUtc());
        require(!observed.isAfter(now) && !observed.isBefore(Instant.parse(card.observedAtUtc())) && now.isBefore(deadline)
                && !observed.plusSeconds(900).isBefore(now), "Fresh finite declaration review required");
        var inputs = new ArrayList<ControlBuild.FileRef>(List.of(planPin, plan.sourceDeclarationRef(), plan.declarationRequestRef(),
                plan.resourceCardRef(), plan.parentToolsBuildRef(), plan.manifestRef(), declaration.configureActualRef(), card.capacityReleaseRef()));
        inputs.addAll(request.completeSources()); inputs.addAll(request.tools().references()); inputs.addAll(graph.graphRefs());
        for (var witness : sourceBefore) inputs.add(witness.source());
        addCompleteHelperInputs(inputs, plan.defenderRuntime()); inputs.addAll(plan.parentSourceRefs()); inputs.addAll(plan.parentRuntime());
        var release = JSON.readValue(currentRead(card.capacityReleaseRef()), ControlBuild.CapacityRelease.class);
        inputs.add(release.policyRef()); addBuildInputs(inputs, parent);
        for (var override : release.quotaOverrides().values())
            inputs.add(new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()));
        inputs = new ArrayList<>(mergeLeaseInputs(inputs));
        verifySourceRefs(inputs);
        String parameters = String.join(" ", List.of("-E", "-s", "-B", "-X", "utf8", plan.defenderRuntime().helper().path(),
                "--manifest", plan.manifestRef().path(), "--receipt", plan.helperReceiptPath()).stream()
                .map(NativeProjectExeUac::quote).toList());
        var review = new DeclaredPathReview("xar.native-declared-exe-uac-review/v1", MACHINE, now.toString(), planPin,
                plan.sourceDeclarationRef(), plan.manifestRef(), semanticSha(JSON.valueToTree(manifest)), graph.output(),
                plan.expectedOwnerSid(), "runas", plan.defenderRuntime().python().path(), parameters,
                REPO.toRealPath().toString(), 0, plan.waitSeconds(), plan.deadlineAtUtc(), inputs);
        return new DeclaredPrepared(plan, review, request, graph, card, inputs, sourceBefore);
    }
    static void requireConfiguredDeclaration(ControlBuild.FileRef ref, NativeBridgeBuild.Request request) throws IOException {
        JsonNode actual = object(JSON.readTree(currentRead(ref)));
        List<String> argv = strings(actual.get("argv"));
        require(MACHINE.equals(text(actual, "machine_id")) && integer(actual, "exit_code") == 0
                && integer(actual, "actual_active_processes") == 0 && integer(actual, "uac_calls") == 0
                && integer(actual, "settings_calls") == 0 && integer(actual, "game_starts") == 0
                && actual.has("stopped_reason") && actual.get("stopped_reason").isNull()
                && argv.contains("--configure") && !argv.contains("--build"), "Actual successful configure-only metadata required");
        requireExactOption(argv, "--source-dir", request.sourceRoot().toString());
        requireExactOption(argv, "--build-dir", request.buildRoot().toString());
        requireExactOption(argv, "--configuration", "Release");
    }
    private static void requireExactOption(List<String> argv, String key, String expected) throws IOException {
        int index = argv.indexOf(key);
        require(index >= 0 && index == argv.lastIndexOf(key) && index + 1 < argv.size(), "Unique configured option required: " + key);
        if (key.equals("--configuration")) require(expected.equals(argv.get(index + 1)), "Configured release differs");
        else require(normalizedPath(expected).equals(normalizedPath(argv.get(index + 1))), "Configured exact path differs: " + key);
    }
    private static void requireDeclaredCapacity(DeclaredPathPlan plan, NativeBridgeBuild.Request request,
            NativeBridgeDefender.DeclaredOutput output, DeclaredPathCard card) throws IOException {
        var release = JSON.readValue(currentRead(card.capacityReleaseRef()), ControlBuild.CapacityRelease.class);
        require(System.getenv("TMP") != null && System.getenv("TEMP") != null
                && normalizedPath(card.temporaryRoot()).equals(normalizedPath(System.getenv("TMP")))
                && normalizedPath(card.temporaryRoot()).equals(normalizedPath(System.getenv("TEMP"))),
                "Same explicit admitted TMP/TEMP must be inherited by the one RunAs helper");
        Instant now = Instant.now(), opened = Instant.parse(release.observedAtUtc()), deadline = Instant.parse(release.reviewAtUtc());
        require(MACHINE.equals(card.machineId()) && MACHINE.equals(release.machineId()) && plan.owner().equals(card.owner())
                && plan.owner().equals(release.ownerTask()) && plan.deadlineAtUtc().equals(card.deadlineAtUtc())
                && Instant.parse(plan.deadlineAtUtc()).equals(deadline)
                && !Instant.parse(card.observedAtUtc()).isBefore(opened) && !now.isBefore(opened) && now.isBefore(deadline)
                && !Instant.parse(card.observedAtUtc()).plusSeconds(900).isBefore(now)
                && card.timeoutSeconds() == plan.waitSeconds() && release.memoryLimitBytes() >= card.memoryReservationBytes()
                && release.parts().getOrDefault("artifacts", 0L) >= card.outputAllocationLimitBytes()
                && normalizedPath(card.sourceRoot()).equals(normalizedPath(request.sourceRoot().toString()))
                && normalizedPath(card.buildRoot()).equals(normalizedPath(request.buildRoot().toString()))
                && normalizedPath(card.exactOutputPath()).equals(normalizedPath(output.path()))
                && normalizedPath(card.outputRoot()).equals(normalizedPath(plan.outputRoot()))
                && Path.of(card.temporaryRoot()).toRealPath().startsWith(Path.of(release.temporaryRoot()).toRealPath()),
                "Fresh one-owner exact-path preregistration scope/capacity required");
        List<Path> scopes = release.approvedOutputRoots().stream().map(Path::of).map(Path::toAbsolutePath).map(Path::normalize).toList();
        for (Path scope : scopes)
            require(!scope.equals(scope.getRoot()) && !scope.startsWith(request.sourceRoot()) && !request.sourceRoot().startsWith(scope),
                    "Whole volume or source directory exclusion scope rejected");
        for (Path target : List.of(Path.of(plan.outputRoot()), request.buildRoot(), Path.of(card.temporaryRoot()))) {
            require(scopes.stream().anyMatch(target::startsWith)
                    && release.volumes().keySet().stream().map(Path::of).anyMatch(volume -> volume.equals(target.getRoot())),
                    "Exact output/temp volume is not admitted");
            var system = Path.of(System.getenv().getOrDefault("SystemRoot", "C:/Windows")).toRealPath().getRoot();
            require(!target.toRealPath().getRoot().equals(system), "No system-volume project bulk output permitted");
        }
        var policy = CiBootstrap.readPolicy(currentRead(release.policyRef()));
        for (var entry : release.volumes().entrySet()) {
            var volume = entry.getValue(); var override = release.quotaOverrides().get(entry.getKey());
            if (override != null) {
                require(override.task().equals(plan.owner()) && !Instant.parse(override.reviewAtUtc()).isAfter(deadline), "Quota override differs");
                new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
            }
            require(volume.equals(CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(), volume.thisWritePeak(),
                    volume.otherUnspentReservations(), volume.systemGrowthReserve(), volume.currentProjectUsageConservativeUpper(), override, opened, deadline))
                    && volume.thisWritePeak() >= card.outputAllocationLimitBytes(), "Declared capacity policy proof differs");
            require(Files.getFileStore(Path.of(entry.getKey())).getUsableSpace() >= Math.addExact(volume.thisWritePeak(),
                    Math.addExact(volume.otherUnspentReservations(), volume.systemGrowthReserve())), "Actual free volume below reserved finite requirement");
        }
    }
    /** One same-owner admin helper; the existing launcher owns all runas and UNKNOWN semantics. */
    public static DeclaredPathResult executeDeclaredPathReviewed(Path path, String reviewedSha, String actualDeadline) throws IOException {
        var planPin = ControlBuild.FileRef.measure(path.toRealPath());
        DeclaredPrepared prepared = prepareDeclared(parseDeclaredPathPlan(currentRead(planPin)), planPin, true);
        DeclaredPathPlan plan = prepared.plan(); DeclaredPathReview review = prepared.review();
        requireReviewedPlan(planPin, reviewedSha); requireSharedStageDeadline(plan.deadlineAtUtc(), actualDeadline);
        final ThreeSettingsReadback[] settings = new ThreeSettingsReadback[1];
        LaunchOutcome outcome = launch(new LaunchOperation() {
            public String deadlineAtUtc() { return plan.deadlineAtUtc(); }
            public int waitSeconds() { return plan.waitSeconds(); }
            public ControlBuild.FileRef image() { return plan.defenderRuntime().python(); }
            public String parameters() { return review.lpParameters(); }
            public String directory() { return review.lpDirectory(); }
            public String expectedOwnerSid() { return plan.expectedOwnerSid(); }
            public Apis nativeApis() throws IOException { return apis(); }
            public List<ControlBuild.FileRef> inputs() { return prepared.inputs(); }
            public void revalidate() throws IOException { prepareDeclared(plan, planPin, true); }
            public void claim(List<GuardedInput> inputs) throws IOException {
                writeNew(Path.of(plan.intentPath()), new DeclaredPathIntent("xar.native-declared-exe-uac-intent/v1",
                        MACHINE, Instant.now().toString(), review, inputs, NO_RETRY));
            }
            public void observe(ProcessIdentity child, boolean elevated, String sid) throws IOException {
                writeNew(Path.of(plan.launchObservationPath()), new CurrentNativeBuildLaunch(
                        "xar.native-declared-exe-uac-launch/v1", MACHINE, Instant.now().toString(), true, child, elevated, sid));
            }
            public CompletedRegistration complete(TerminalProof terminal) throws IOException {
                var receipt = ControlBuild.FileRef.measure(Path.of(plan.helperReceiptPath()).toRealPath());
                settings[0] = qualifyDeclaredCompletion(terminal, plan.defenderRuntime().python().path(), plan.expectedOwnerSid(),
                        review.output(), plan.manifestRef(), receipt);
                NativeBridgeDefender.requireAbsent(review.output()); verifySourceRefs(prepared.inputs());
                NativeBridgeBuild.assertLiveSourceBinding(prepared.request(), prepared.sourceBefore());
                require(sameRefs(NativeBridgeDefender.readDeclaredGraph(prepared.request()).graphRefs(), prepared.graph().graphRefs()),
                        "Configured/source identity changed during settings operation");
                return new CompletedRegistration(Status.VERIFIED, ProofScope.DECLARED_PROJECT_EXE_PATH_ONLY, receipt, null);
            }
        });
        var result = new DeclaredPathResult("xar.native-declared-exe-uac-result/v1", MACHINE, outcome.observedAtUtc(),
                outcome.status(), outcome.status() == Status.VERIFIED ? ProofScope.DECLARED_PROJECT_EXE_PATH_ONLY : null, review,
                outcome.launchCallEntered(), outcome.shellAcknowledged(), outcome.launchWin32Error(), outcome.processIdentity(),
                outcome.tokenElevated(), outcome.ownerSid(), outcome.processExitCodeDecimal(), outcome.waitTimedOut(),
                outcome.completion() == null ? null : outcome.completion().helperReceiptRef(), settings[0],
                outcome.diagnostics(), false, false, outcome.terminalProof());
        writeNew(Path.of(plan.resultPath()), result); return result;
    }
    static ThreeSettingsReadback qualifyDeclaredCompletion(TerminalProof terminal, String expectedInterpreter,
            String expectedSid, NativeBridgeDefender.DeclaredOutput expected, ControlBuild.FileRef manifest,
            ControlBuild.FileRef receipt) throws IOException {
        require(terminal != null && terminal.shellAcknowledged() && terminal.processIdentity() != null
                && Boolean.TRUE.equals(terminal.tokenElevated()) && terminal.nativeSignalled() && !terminal.timedOut()
                && "0".equals(terminal.processExitCodeDecimal())
                && normalizedPath(terminal.processIdentity().executable()).equals(normalizedPath(expectedInterpreter)),
                "Actual completed elevated canonical helper required");
        NativeBridgeDefender.readDeclaredVerified(receipt, manifest, expected);
        JsonNode raw = object(JSON.readTree(currentRead(receipt)));
        return qualifyThreeSettings(raw, expectedSid, Long.parseLong(terminal.processIdentity().pidDecimal()));
    }


    public static final String BUILT_FIXTURE_PLAN_SCHEMA = "xar.native-built-fixture-uac-plan/v1";
    public static final String BUILT_FIXTURE_RESULT_SCHEMA = "xar.native-built-fixture-uac-result/v1";
    public record BuiltFixturePlan(String schema, String machineId, String observedAtUtc, String deadlineAtUtc,
            String owner, String expectedOwnerSid, int waitSeconds, ControlBuild.FileRef fixturePlanRef,
            ControlBuild.FileRef resourceCardRef, ControlBuild.FileRef buildActualRef,
            ControlBuild.FileRef parentToolsBuildRef, List<ControlBuild.FileRef> parentSourceRefs,
            List<ControlBuild.FileRef> parentRuntime, NativeBridgeDefender.ManifestRuntime defenderRuntime,
            ControlBuild.FileRef manifestRef, String outputRoot, String helperReceiptPath,
            String intentPath, String launchObservationPath, String resultPath) {
        public BuiltFixturePlan {
            if (!BUILT_FIXTURE_PLAN_SCHEMA.equals(schema) || !MACHINE.equals(machineId)
                    || !"/root/native_fixtures63".equals(owner) || waitSeconds < 1 || waitSeconds > 7200)
                throw new IllegalArgumentException("Exact finite current fixture plan required");
            Instant.parse(observedAtUtc); Instant.parse(deadlineAtUtc);
            parentSourceRefs = NativeBridgeBuild.unique(parentSourceRefs); parentRuntime = NativeBridgeBuild.unique(parentRuntime);
            Objects.requireNonNull(fixturePlanRef); Objects.requireNonNull(resourceCardRef); Objects.requireNonNull(buildActualRef);
            Objects.requireNonNull(parentToolsBuildRef); Objects.requireNonNull(defenderRuntime); Objects.requireNonNull(manifestRef);
        }
    }
    public record BuiltFixtureReview(String schema, String machineId, String observedAtUtc, ControlBuild.FileRef planRef,
            ControlBuild.FileRef fixturePlanRef, ControlBuild.FileRef resourceCardRef, ControlBuild.FileRef buildActualRef,
            ControlBuild.FileRef manifestRef, String manifestSemanticSha256, ControlBuild.FileRef executableRef,
            String expectedOwnerSid, String lpVerb, String lpFile, String lpParameters, String lpDirectory,
            int nShow, int waitSeconds, String deadlineAtUtc, List<ControlBuild.FileRef> guardedInputRefs) {
        public BuiltFixtureReview { guardedInputRefs = uniqueLeaseInputs(guardedInputRefs); }
    }
    public record BuiltFixtureIntent(String schema, String machineId, String observedAtUtc, BuiltFixtureReview review,
            List<GuardedInput> guardedInputs, String unresolvedActionPolicy) {
        public BuiltFixtureIntent { guardedInputs = List.copyOf(guardedInputs); }
    }
    public record BuiltFixtureRegistrationResult(String schema, String machineId, String observedAtUtc,
            Status status, ProofScope proofScope, ControlBuild.FileRef planRef, ControlBuild.FileRef fixturePlanRef,
            ControlBuild.FileRef buildActualRef, ControlBuild.FileRef executableRef, BuiltFixtureReview review,
            boolean launchCallEntered, boolean shellAcknowledged, Integer launchWin32Error, ProcessIdentity processIdentity,
            Boolean tokenElevated, String tokenUserSid, String processExitCodeDecimal, boolean waitTimedOut,
            ControlBuild.FileRef helperReceiptRef, ThreeSettingsReadback settings, List<String> diagnostics,
            boolean automaticallyRetried, boolean elevatedProcessTerminated, TerminalProof terminalProof,
            ControlBuild.FileRef intentRef, ControlBuild.FileRef launchObservationRef) {
        public BuiltFixtureRegistrationResult {
            if (!BUILT_FIXTURE_RESULT_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact built-fixture result version required");
            if (status == Status.VERIFIED && (intentRef == null || launchObservationRef == null))
                throw new IllegalArgumentException("Verified fixture result requires original intent/launch pins");
            diagnostics = List.copyOf(diagnostics);
        }
    }
    private record BuiltFixturePrepared(BuiltFixturePlan plan, BuiltFixtureReview review,
            NativeFixtureBuild.CurrentFixtureRegistrationInputs fixture, List<ControlBuild.FileRef> inputs,
            CompileSourceBinding.Binding binding, List<SharedSourceFiles.Witness> compileBefore) {
        private BuiltFixturePrepared { inputs = uniqueLeaseInputs(inputs); compileBefore = List.copyOf(compileBefore); }
    }
    public static BuiltFixturePlan parseBuiltFixturePlan(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= CURRENT_LIMIT, "Bounded exact built-fixture plan required");
        return CURRENT_NATIVE_JSON.readValue(raw, BuiltFixturePlan.class);
    }
    public static ControlBuild.FileRef writeBuiltFixturePlan(BuiltFixturePlan plan, Path output) throws IOException {
        NativeBridgeBuild.absolute(output); SharedSourceFiles.plainAncestors(output.getParent());
        require(output.getParent().toRealPath().equals(Path.of(plan.outputRoot()).toRealPath()), "Exact fixture control root required");
        writeNew(output, plan); var pin = ControlBuild.FileRef.measure(output);
        prepareBuiltFixture(plan, pin); return pin;
    }
    public static BuiltFixtureReview reviewBuiltFixture(Path path) throws IOException {
        var pin = ControlBuild.FileRef.measure(path.toRealPath());
        return prepareBuiltFixture(parseBuiltFixturePlan(currentRead(pin)), pin).review();
    }
    private static void requireBuiltFixtureProducer(BuiltFixturePlan plan,
            NativeFixtureBuild.CurrentFixtureRegistrationInputs fixture) throws IOException {
        var sourcePlan = fixture.plan();
        require(MACHINE.equals(WindowsJobProcess.currentMachineId()) && sourcePlan.machineId().equals(plan.machineId())
                && sourcePlan.ownerTask().equals(plan.owner()) && sourcePlan.canonicalRepository().equals(REPO.toRealPath())
                && sourcePlan.qualifiedToolsBuildRef().equals(plan.parentToolsBuildRef()), "Current exact fixture producer identity differs");
        requireCanonicalSid(plan.expectedOwnerSid());
        var parent = ControlBuild.verifiedCompletedReceipt(plan.parentToolsBuildRef());
        require(parent.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && sameRefs(parent.completeDeployment(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(), plan.parentRuntime())
                && sameRefs(ControlBuild.producerClosure(NativeProjectExeUac.class), plan.parentRuntime())
                && sameRefs(parent.sourcePins(), plan.parentSourceRefs()), "Exact completed fixture registration producer runtime/source required");
        NativeBridgeDefender.requireDirectHelperRuntime(plan.defenderRuntime());
        require(NativeBridgeDefender.directBaseRuntime(sourcePlan.canonicalRepository(), plan.defenderRuntime().inventoryRef())
                .equals(plan.defenderRuntime()), "Fixture helper differs from the complete direct-base inventory producer");
        NativeFixtureBuild.requireCurrentFixtureManifest(fixture, plan.manifestRef());
    }
    private static BuiltFixturePrepared prepareBuiltFixture(BuiltFixturePlan plan, ControlBuild.FileRef planPin) throws IOException {
        var fixture = NativeFixtureBuild.currentRegistrationInputs(plan.fixturePlanRef(), plan.resourceCardRef(), plan.buildActualRef());
        requireBuiltFixtureProducer(plan, fixture);
        var sourcePlan = fixture.plan(); var card = NativeFixtureBuild.currentFixtureCard(plan.resourceCardRef());
        Instant now = Instant.now(), observed = Instant.parse(plan.observedAtUtc()), deadline = Instant.parse(plan.deadlineAtUtc());
        require(card.allowedStage() == NativeFixtureBuild.Stage.REGISTER && card.owner().equals(plan.owner())
                && !observed.isBefore(Instant.parse(card.observedAtUtc())) && !observed.isAfter(now)
                && !observed.plusSeconds(900).isBefore(now) && now.isBefore(deadline)
                && !deadline.isAfter(Instant.parse(card.reviewAtUtc())) && plan.waitSeconds() <= card.timeoutSeconds()
                && Duration.between(now, deadline).getSeconds() >= plan.waitSeconds(),
                "Fresh same-owner REGISTER card and full remaining helper budget required");
        Path output = Path.of(plan.outputRoot()).toRealPath(); NativeBridgeBuild.plainDirectory(output);
        require(output.startsWith(sourcePlan.scratchRoot()) && !output.equals(sourcePlan.scratchRoot())
                && !(output.startsWith(sourcePlan.compileSourceRoot()) || sourcePlan.compileSourceRoot().startsWith(output))
                && !(output.startsWith(sourcePlan.buildRoot()) || sourcePlan.buildRoot().startsWith(output))
                && card.outputRoots().stream().map(Path::of).anyMatch(output::startsWith),
                "Fixture registration controls must be inside the exact admitted scratch scope");
        Set<Path> outputs = new HashSet<>();
        for (String name : List.of(plan.helperReceiptPath(), plan.intentPath(), plan.launchObservationPath(), plan.resultPath())) {
            Path path = NativeBridgeBuild.absolute(Path.of(name));
            require(path.getParent().equals(output) && outputs.add(path) && Files.notExists(path, LinkOption.NOFOLLOW_LINKS),
                    "Distinct fresh exact fixture controls required; UNKNOWN is never repeated");
        }
        var release = JSON.readValue(currentRead(card.releaseRef()), ControlBuild.CapacityRelease.class);
        require(System.getenv("TMP") != null && System.getenv("TEMP") != null
                && normalizedPath(System.getenv("TMP")).equals(normalizedPath(System.getenv("TEMP"))),
                "One actual admitted TMP/TEMP required");
        Path temporary = Path.of(System.getenv("TMP")).toRealPath();
        require(temporary.startsWith(Path.of(release.temporaryRoot()).toRealPath()), "Fixture helper TMP/TEMP is outside the admitted release");
        var binding = CompileSourceBinding.readHistorical(sourcePlan.compileSourceBindingRef());
        var compileBefore = CompileSourceBinding.observeLive(binding);
        var inputs = new ArrayList<ControlBuild.FileRef>(fixture.inputs());
        inputs.addAll(List.of(planPin, plan.manifestRef(), plan.parentToolsBuildRef(), sourcePlan.compileSourceBindingRef()));
        inputs.addAll(CompileSourceBinding.compileSources(binding)); inputs.addAll(plan.parentSourceRefs());
        inputs.addAll(plan.parentRuntime()); addCompleteHelperInputs(inputs, plan.defenderRuntime());
        inputs = new ArrayList<>(mergeLeaseInputs(inputs)); verifySourceRefs(inputs);
        String parameters = fixtureHelperParameters(plan);
        var review = new BuiltFixtureReview("xar.native-built-fixture-uac-review/v1", MACHINE, now.toString(), planPin,
                plan.fixturePlanRef(), plan.resourceCardRef(), plan.buildActualRef(), plan.manifestRef(),
                semanticSha(JSON.readTree(currentRead(plan.manifestRef()))), fixture.executableRef(), plan.expectedOwnerSid(),
                "runas", plan.defenderRuntime().python().path(), parameters, REPO.toRealPath().toString(), 0,
                plan.waitSeconds(), plan.deadlineAtUtc(), inputs);
        return new BuiltFixturePrepared(plan, review, fixture, inputs, binding, compileBefore);
    }
    private static String fixtureHelperParameters(BuiltFixturePlan plan) {
        return String.join(" ", List.of("-E", "-s", "-B", "-X", "utf8", plan.defenderRuntime().helper().path(),
                "--manifest", plan.manifestRef().path(), "--receipt", plan.helperReceiptPath()).stream()
                .map(NativeProjectExeUac::quote).toList());
    }
    static ThreeSettingsReadback qualifyBuiltFixtureCompletion(TerminalProof terminal, String interpreter, String sid,
            ControlBuild.FileRef executable, String exactTarget, ControlBuild.FileRef manifest, ControlBuild.FileRef receipt) throws IOException {
        return qualifyBuiltFixtureCompletion(terminal, interpreter, sid, executable, exactTarget, manifest, receipt, executable);
    }
    static ThreeSettingsReadback qualifyBuiltFixtureCompletion(TerminalProof terminal, String interpreter, String sid,
            ControlBuild.FileRef executable, String exactTarget, ControlBuild.FileRef manifest, ControlBuild.FileRef receipt,
            ControlBuild.FileRef retainedExecutable) throws IOException {
        require(terminal != null && terminal.shellAcknowledged() && terminal.processIdentity() != null
                && Boolean.TRUE.equals(terminal.tokenElevated()) && terminal.nativeSignalled() && !terminal.timedOut()
                && "0".equals(terminal.processExitCodeDecimal())
                && normalizedPath(terminal.processIdentity().executable()).equals(normalizedPath(interpreter)),
                "Actual completed elevated direct-base fixture helper required");
        NativeBridgeDefender.requireDirectBuiltFixtureReceipt(receipt, manifest, executable, exactTarget, retainedExecutable);
        return qualifyThreeSettings(object(JSON.readTree(currentRead(receipt))), sid, Long.parseLong(terminal.processIdentity().pidDecimal()));
    }
    public static BuiltFixtureRegistrationResult executeBuiltFixtureReviewed(Path path, String reviewedSha, String actualDeadline) throws IOException {
        var planPin = ControlBuild.FileRef.measure(path.toRealPath());
        var prepared = prepareBuiltFixture(parseBuiltFixturePlan(currentRead(planPin)), planPin);
        var plan = prepared.plan(); var review = prepared.review();
        requireReviewedPlan(planPin, reviewedSha); requireSharedStageDeadline(plan.deadlineAtUtc(), actualDeadline);
        final ThreeSettingsReadback[] settings = new ThreeSettingsReadback[1];
        final ControlBuild.FileRef[] observations = new ControlBuild.FileRef[2];
        LaunchOutcome outcome = launch(new LaunchOperation() {
            public String deadlineAtUtc() { return plan.deadlineAtUtc(); }
            public int waitSeconds() { return plan.waitSeconds(); }
            public ControlBuild.FileRef image() { return plan.defenderRuntime().python(); }
            public String parameters() { return review.lpParameters(); }
            public String directory() { return review.lpDirectory(); }
            public String expectedOwnerSid() { return plan.expectedOwnerSid(); }
            public Apis nativeApis() throws IOException { return apis(); }
            public List<ControlBuild.FileRef> inputs() { return prepared.inputs(); }
            public void revalidate() throws IOException { prepareBuiltFixture(plan, planPin); }
            public void claim(List<GuardedInput> inputs) throws IOException {
                observations[0] = writeBuiltFixtureIntent(Path.of(plan.intentPath()), new BuiltFixtureIntent("xar.native-built-fixture-uac-intent/v1",
                        MACHINE, Instant.now().toString(), review, inputs, NO_RETRY));
            }
            public ControlBuild.FileRef claimedIntentRef() { return observations[0]; }
            public void observe(ProcessIdentity child, boolean elevated, String sid) throws IOException {
                observations[1] = writeBuiltFixtureLaunch(Path.of(plan.launchObservationPath()), new CurrentNativeBuildLaunch(
                        "xar.native-built-fixture-uac-launch/v1", MACHINE, Instant.now().toString(), true, child, elevated, sid));
            }
            public CompletedRegistration complete(TerminalProof terminal) throws IOException {
                var receipt = ControlBuild.FileRef.measure(Path.of(plan.helperReceiptPath()).toRealPath());
                settings[0] = qualifyBuiltFixtureCompletion(terminal, plan.defenderRuntime().python().path(), plan.expectedOwnerSid(),
                        prepared.fixture().executableRef(), prepared.fixture().plan().target().targetName(), plan.manifestRef(), receipt);
                NativeFixtureBuild.revalidateCurrentRegistration(prepared.fixture());
                CompileSourceBinding.assertLiveUnchanged(prepared.binding(), prepared.compileBefore()); verifySourceRefs(prepared.inputs());
                return new CompletedRegistration(Status.VERIFIED, ProofScope.SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS, receipt, null);
            }
        });
        if (outcome.status() == Status.VERIFIED) {
            require(observations[0] != null && observations[1] != null, "Original fixture observations missing after completed launch");
            observations[0].verify(); observations[1].verify();
        }
        var result = new BuiltFixtureRegistrationResult(BUILT_FIXTURE_RESULT_SCHEMA, MACHINE, outcome.observedAtUtc(),
                outcome.status(), outcome.status() == Status.VERIFIED ? ProofScope.SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS : null,
                planPin, plan.fixturePlanRef(), plan.buildActualRef(), prepared.fixture().executableRef(), review,
                outcome.launchCallEntered(), outcome.shellAcknowledged(), outcome.launchWin32Error(), outcome.processIdentity(),
                outcome.tokenElevated(), outcome.ownerSid(), outcome.processExitCodeDecimal(), outcome.waitTimedOut(),
                outcome.completion() == null ? null : outcome.completion().helperReceiptRef(), settings[0],
                outcome.diagnostics(), false, false, outcome.terminalProof(), observations[0], observations[1]);
        writeNew(Path.of(plan.resultPath()), result); return result;
    }
    static ControlBuild.FileRef writeBuiltFixtureIntent(Path path, BuiltFixtureIntent intent) throws IOException {
        return writeBuiltFixtureObservation(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(intent));
    }
    static ControlBuild.FileRef writeBuiltFixtureLaunch(Path path, CurrentNativeBuildLaunch launch) throws IOException {
        return writeBuiltFixtureObservation(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(launch));
    }
    private static ControlBuild.FileRef writeBuiltFixtureObservation(Path path, byte[] serialized) throws IOException {
        SharedSourceFiles.plainAncestors(path); Files.write(path, serialized, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var pin = ControlBuild.FileRef.measure(path);
        require(pin.bytes() == serialized.length && pin.sha256().equals(sha(serialized)), "Original fixture observation changed while captured");
        return pin;
    }
    static byte[] readBuiltFixtureObservation(ControlBuild.FileRef pin, Path expectedPath) throws IOException {
        require(pin != null && Path.of(pin.path()).equals(expectedPath), "Exact original fixture observation pin/path required");
        return currentRead(pin);
    }
    /** Original terminal and source/build lineage are read without reopening the mutable compile tree. */
    public static BuiltFixtureRegistrationResult readCurrentFixtureRegistrationResult(ControlBuild.FileRef planRef,
            ControlBuild.FileRef resultRef) throws IOException {
        var plan = parseBuiltFixturePlan(currentRead(planRef));
        var result = CURRENT_NATIVE_JSON.readValue(currentRead(resultRef), BuiltFixtureRegistrationResult.class);
        var fixture = NativeFixtureBuild.readHistoricalCurrentRegistrationInputs(plan.fixturePlanRef(), plan.resourceCardRef(), plan.buildActualRef());
        requireBuiltFixtureProducer(plan, fixture);
        var review = result.review();
        require(result.status() == Status.VERIFIED && result.proofScope() == ProofScope.SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS
                && MACHINE.equals(result.machineId()) && result.planRef().equals(planRef) && result.fixturePlanRef().equals(plan.fixturePlanRef())
                && result.buildActualRef().equals(plan.buildActualRef()) && result.executableRef().equals(fixture.executableRef())
                && Path.of(resultRef.path()).equals(Path.of(plan.resultPath())) && review != null && review.planRef().equals(planRef)
                && review.fixturePlanRef().equals(plan.fixturePlanRef()) && review.resourceCardRef().equals(plan.resourceCardRef())
                && review.buildActualRef().equals(plan.buildActualRef()) && review.manifestRef().equals(plan.manifestRef())
                && review.executableRef().equals(fixture.executableRef()) && review.expectedOwnerSid().equals(plan.expectedOwnerSid())
                && review.manifestSemanticSha256().equals(semanticSha(JSON.readTree(currentRead(plan.manifestRef()))))
                && "runas".equals(review.lpVerb()) && review.lpFile().equals(plan.defenderRuntime().python().path())
                && review.lpParameters().equals(fixtureHelperParameters(plan)) && review.lpDirectory().equals(REPO.toRealPath().toString())
                && review.nShow() == 0 && review.waitSeconds() == plan.waitSeconds() && review.deadlineAtUtc().equals(plan.deadlineAtUtc())
                && result.launchCallEntered() && result.shellAcknowledged() && result.launchWin32Error() == null
                && Boolean.TRUE.equals(result.tokenElevated()) && !result.waitTimedOut() && "0".equals(result.processExitCodeDecimal())
                && !result.automaticallyRetried() && !result.elevatedProcessTerminated() && result.diagnostics().isEmpty(),
                "Exact original verified fixture registration result/command required");
        var binding = CompileSourceBinding.readHistorical(fixture.plan().compileSourceBindingRef());
        var expectedInputs = new ArrayList<ControlBuild.FileRef>(fixture.inputs());
        expectedInputs.addAll(List.of(planRef, plan.manifestRef(), plan.parentToolsBuildRef(), fixture.plan().compileSourceBindingRef()));
        expectedInputs.addAll(CompileSourceBinding.compileSources(binding)); expectedInputs.addAll(plan.parentSourceRefs());
        expectedInputs.addAll(plan.parentRuntime()); addCompleteHelperInputs(expectedInputs, plan.defenderRuntime());
        require(sameRefs(mergeLeaseInputs(expectedInputs), review.guardedInputRefs()),
                "Original fixture input lease omitted or acquired a source/runtime file");
        var card = NativeFixtureBuild.currentFixtureCard(plan.resourceCardRef());
        Instant observed = Instant.parse(result.observedAtUtc()), opened = Instant.parse(plan.observedAtUtc());
        require(!observed.isBefore(opened) && observed.isBefore(Instant.parse(plan.deadlineAtUtc()))
                && !opened.isBefore(Instant.parse(card.observedAtUtc())) && !Instant.parse(plan.deadlineAtUtc()).isAfter(Instant.parse(card.reviewAtUtc())),
                "Original fixture registration exceeded its finite card window");
        var intent = CURRENT_NATIVE_JSON.readValue(readBuiltFixtureObservation(result.intentRef(), Path.of(plan.intentPath())), BuiltFixtureIntent.class);
        var launch = CURRENT_NATIVE_JSON.readValue(readBuiltFixtureObservation(result.launchObservationRef(), Path.of(plan.launchObservationPath())), CurrentNativeBuildLaunch.class);
        require("xar.native-built-fixture-uac-intent/v1".equals(intent.schema()) && MACHINE.equals(intent.machineId())
                && intent.review().equals(review) && NO_RETRY.equals(intent.unresolvedActionPolicy())
                && intent.guardedInputs().stream().map(GuardedInput::requestedPath).toList().equals(review.guardedInputRefs().stream().map(ControlBuild.FileRef::path).toList())
                && "xar.native-built-fixture-uac-launch/v1".equals(launch.schema()) && MACHINE.equals(launch.machineId())
                && launch.shellAcknowledged() && Boolean.TRUE.equals(launch.tokenElevated())
                && Objects.equals(launch.processIdentity(), result.processIdentity()) && Objects.equals(launch.tokenUserSid(), result.tokenUserSid())
                && result.terminalProof() != null && Objects.equals(result.terminalProof().processIdentity(), result.processIdentity())
                && Objects.equals(result.terminalProof().tokenElevated(), result.tokenElevated())
                && Objects.equals(result.terminalProof().processExitCodeDecimal(), result.processExitCodeDecimal()),
                "Original claimed inputs, elevated launch identity and terminal differ");
        Instant reviewAt = Instant.parse(review.observedAtUtc()), intentAt = Instant.parse(intent.observedAtUtc()),
                launchAt = Instant.parse(launch.observedAtUtc());
        require(!reviewAt.isBefore(opened) && !intentAt.isBefore(reviewAt) && !launchAt.isBefore(intentAt)
                && !observed.isBefore(launchAt), "Original fixture review/intent/launch/result chronology is not monotonic");
        Set<String> retainedIds = binding.rows().stream().map(row -> row.retainedWitness().nativeFile())
                .map(file -> file.legacyVolumeSerialDecimal() + ":" + new BigInteger(file.legacyFileIdHex(), 16))
                .collect(java.util.stream.Collectors.toSet());
        Set<String> compilePaths = CompileSourceBinding.compileSources(binding).stream().map(ControlBuild.FileRef::path)
                .collect(java.util.stream.Collectors.toSet());
        for (int index = 0; index < intent.guardedInputs().size(); index++) {
            var guarded = intent.guardedInputs().get(index); var expected = review.guardedInputRefs().get(index);
            var identity = guarded.identity(); require(identity != null && !identity.directory(), "Original regular input identity required");
            canonicalUnsigned(identity.volumeSerialDecimal(), 32, false, "input volume");
            canonicalUnsigned(identity.fileIdDecimal(), 64, false, "input file ID");
            canonicalUnsigned(identity.sizeDecimal(), 64, false, "input size");
            require(identity.sizeDecimal().equals(Long.toString(expected.bytes())) && identity.nativeFinalPath() != null
                    && !identity.nativeFinalPath().isBlank(), "Original native input size/final path evidence differs");
            if (compilePaths.contains(expected.path()))
                require(!retainedIds.contains(identity.volumeSerialDecimal() + ":" + identity.fileIdDecimal()),
                        "Original compile input lease aliases immutable retained input");
        }
        requireSameOwnerSid(plan.expectedOwnerSid(), result.tokenUserSid());
        require(result.helperReceiptRef() != null && Path.of(result.helperReceiptRef().path()).equals(Path.of(plan.helperReceiptPath())),
                "Original fixture helper receipt path differs");
        var settings = qualifyBuiltFixtureCompletion(result.terminalProof(), plan.defenderRuntime().python().path(), plan.expectedOwnerSid(),
                fixture.executableRef(), fixture.plan().target().targetName(), plan.manifestRef(), result.helperReceiptRef(),
                NativeFixtureBuild.currentFixtureRetainedExecutable(fixture));
        require(settings.equals(result.settings()), "Persisted fixture settings differ from original actual helper readback");
        resultRef.verify(); planRef.verify(); return result;
    }

    public static void main(String[] args) throws IOException {
        if (args.length == 5 && args[0].equals("prepare-built-fixture-manifest")) {
            var inputs = NativeFixtureBuild.currentRegistrationInputs(
                    ControlBuild.FileRef.measure(Path.of(args[1]).toRealPath()),
                    ControlBuild.FileRef.measure(Path.of(args[2]).toRealPath()),
                    ControlBuild.FileRef.measure(Path.of(args[3]).toRealPath()));
            var manifest = NativeFixtureBuild.prepareCurrentFixtureManifest(inputs, Path.of(args[4]));
            System.out.println(JSON.writeValueAsString(manifest));
        } else if (args.length == 2 && args[0].equals("review")) {
            Path path = Path.of(args[1]);
            JsonNode envelope = object(JSON.readTree(read(path, CURRENT_LIMIT)));
            Object review = BUILT_FIXTURE_PLAN_SCHEMA.equals(envelope.path("schema").asText()) ? reviewBuiltFixture(path)
                    : DECLARED_PLAN_SCHEMA.equals(envelope.path("schema").asText()) ? reviewDeclaredPath(path)
                    : currentPlanRoute(envelope) ? reviewCurrentNativeBuild(path) : review(path);
            System.out.println(JSON.writeValueAsString(review));
        } else if (args.length == 4 && args[0].equals("execute-approved-plan")) {
            Path path = Path.of(args[1]);
            JsonNode envelope = object(JSON.readTree(read(path, CURRENT_LIMIT)));
            if (BUILT_FIXTURE_PLAN_SCHEMA.equals(envelope.path("schema").asText())) {
                var result = executeBuiltFixtureReviewed(path, args[2], args[3]);
                System.out.println(JSON.writeValueAsString(result)); if (result.status() != Status.VERIFIED) System.exit(1);
            } else if (DECLARED_PLAN_SCHEMA.equals(envelope.path("schema").asText())) {
                DeclaredPathResult result = executeDeclaredPathReviewed(path, args[2], args[3]);
                System.out.println(JSON.writeValueAsString(result)); if (result.status() != Status.VERIFIED) System.exit(1);
            } else if (currentPlanRoute(envelope)) {
                CurrentNativeBuildResult result = executeCurrentNativeBuildReviewed(path, args[2], args[3]);
                System.out.println(JSON.writeValueAsString(result)); if (result.status() != Status.VERIFIED) System.exit(1);
            } else {
                Result result = executeReviewed(path, args[2], args[3]);
                System.out.println(JSON.writeValueAsString(result)); if (result.status() != Status.VERIFIED) System.exit(1);
            }
        } else if (args.length == 5 && args[0].equals(ADMIN_CHILD_ROLE)) {
            CurrentAdminChildOutcome result = executeCurrentAdminChild(SharedOwnedCommand.cliRef(args[1], args[2], args[3]), args[4]);
            if (result.status() != Status.VERIFIED) System.exit(1);
        } else throw new IllegalArgumentException(
                "prepare-built-fixture-manifest <fixture-plan.json> <register-card.json> <build-actual.json> <manifest-output.json> | review <exact-plan.json> | execute-approved-plan <same-plan.json> <Root-reviewed-SHA256> <actual-shared-stage-deadline-UTC>");
    }
}

