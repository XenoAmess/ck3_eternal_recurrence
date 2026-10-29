package org.xar.ck3.control.build.runtime;

import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Map;
import java.util.TreeMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Versioned deployment data. None of these DTOs is a running-host or Native authority. */
public final class JavaRuntimePackageModel {
    public static final String REQUEST_SCHEMA = "xar.java-only-runtime-package-request/v3";
    public static final String MANIFEST_SCHEMA = "xar.java-only-runtime-package/v3";
    public static final int MAX_METADATA_BYTES = 16 * 1024 * 1024;
    public static final int MAX_HOST_CONFIGURATION_BYTES = 1024 * 1024;
    public static final int MAX_FILES = 30_000;
    public static final long MAX_PACKAGE_BYTES = 2L << 30;
    public static final List<String> CORE_CLASSES = List.of(
            "org.xar.ck3.control.build.runtime.HostMode",
            "org.xar.ck3.control.build.runtime.JavaRuntimePackage",
            "org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec",
            "org.xar.ck3.control.build.runtime.JavaRuntimePackageModel",
            "org.xar.ck3.control.application.planning.OrdinaryPlanner",
            "org.xar.ck3.control.application.action.ActionCoordinator",
            "org.xar.ck3.control.application.session.SessionController",
            "org.xar.ck3.control.application.checkpoint.CheckpointService",
            "org.xar.ck3.control.application.checkpoint.RestoreCheckpointService",
            "org.xar.ck3.control.nativebridge.NativeGameTransport",
            "org.xar.ck3.control.continuity.writer.ContinuityStore",
            "org.xar.ck3.control.service.root.RootApplicationAssembly",
            "org.xar.ck3.control.service.mcp.RootApplicationMain",
            "org.xar.ck3.control.service.mcp.PublicMcpMain");

    private JavaRuntimePackageModel() { }

    public record JavaHome(String root, FileRef executable, List<FileRef> completeRuntimeFiles) {
        public JavaHome {
            absolute(root); Objects.requireNonNull(executable);
            completeRuntimeFiles = bounded(completeRuntimeFiles);
            if (!Path.of(executable.path()).equals(Path.of(root).resolve("bin/java.exe")))
                throw new IllegalArgumentException("actual selected Java executable required");
            for (FileRef file : completeRuntimeFiles) inside(root, file);
            if (!completeRuntimeFiles.contains(executable)) throw new IllegalArgumentException("Java image absent from runtime closure");
        }
    }

    public record NativeInputs(FileRef environmentActual, FileRef buildActual, FileRef registrationActual,
            String sourceRoot, List<FileRef> completeSources, FileRef bridgeDll, FileRef injector,
            FileRef gameExecutable, FileRef launcherSettings, String bridgeVersion, String adapterId) {
        public NativeInputs {
            Objects.requireNonNull(environmentActual); Objects.requireNonNull(buildActual); Objects.requireNonNull(registrationActual);
            uniqueReferences(List.of(environmentActual, buildActual, registrationActual));
            for (FileRef actual : List.of(environmentActual, buildActual, registrationActual))
                if (actual.bytes() < 1) throw new IllegalArgumentException("three nonempty actual native stages required");
            absolute(sourceRoot); completeSources = uniqueReferences(completeSources);
            for (FileRef source : completeSources) inside(sourceRoot, source);
            name(bridgeDll, "xar_ck3_bridge.dll"); name(injector, "xar_ck3_bridge_injector.exe");
            name(gameExecutable, "ck3.exe"); name(launcherSettings, "launcher-settings.json");
            for (FileRef artifact : List.of(bridgeDll, injector, gameExecutable, launcherSettings))
                if (artifact.bytes() < 1) throw new IllegalArgumentException("nonempty selected native/Game artifacts required");
            text(bridgeVersion); text(adapterId);
        }
        public List<FileRef> stageActuals() { return List.of(environmentActual, buildActual, registrationActual); }
        public List<FileRef> mandatoryEvidence() {
            List<FileRef> result = new ArrayList<>(stageActuals()); result.addAll(completeSources);
            result.addAll(List.of(bridgeDll, injector, gameExecutable, launcherSettings)); return List.copyOf(result);
        }
    }

    /** Data returned by the fixed Root reader. This DTO never grants process, Game or ledger authority. */
    public record NativeProof(String machineId, HostMode mode, FileRef actualHostConfiguration,
            NativeInputs expected, List<FileRef> completeEvidenceClosure) {
        public NativeProof {
            machine(machineId); Objects.requireNonNull(mode); Objects.requireNonNull(actualHostConfiguration);
            Objects.requireNonNull(expected); completeEvidenceClosure = uniqueReferences(completeEvidenceClosure);
            if (actualHostConfiguration.bytes() < 1 || !completeEvidenceClosure.containsAll(expected.mandatoryEvidence()))
                throw new IllegalArgumentException("complete three-stage native source/artifact evidence closure required");
        }
    }

    public record ContractPin(String contractId, FileRef source) {
        public ContractPin { text(contractId); Objects.requireNonNull(source); }
    }

    public record LaunchSettings(HostMode mode, int httpPort, long minimumHeapBytes, long maximumHeapBytes,
            String temporaryRoot, String nativeScratchRoot) {
        public LaunchSettings {
            Objects.requireNonNull(mode);
            absolute(temporaryRoot); absolute(nativeScratchRoot);
            if (httpPort < 1 || httpPort > 65_535 || minimumHeapBytes < (32L << 20)
                    || maximumHeapBytes < minimumHeapBytes || maximumHeapBytes > (16L << 30)
                    || !Path.of(nativeScratchRoot).startsWith(Path.of(temporaryRoot))
                    || Path.of(nativeScratchRoot).equals(Path.of(temporaryRoot)))
                throw new IllegalArgumentException("finite heap, loopback port and explicit child JNA scratch required");
        }
    }

    public record Request(String schema, String machineId, String generation, String createdAtUtc,
            String reviewAtUtc, String outputRoot, FileRef serviceBuildActual, JavaHome javaHome,
            NativeInputs nativeInputs, List<ContractPin> contracts, FileRef hostConfiguration,
            LaunchSettings launch, List<String> additionalRequiredClasses, long maximumOutputBytes) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema)) throw new IllegalArgumentException("runtime request version differs");
            machine(machineId); text(generation); instant(createdAtUtc); instant(reviewAtUtc); absolute(outputRoot);
            Objects.requireNonNull(serviceBuildActual); Objects.requireNonNull(javaHome); Objects.requireNonNull(nativeInputs);
            Objects.requireNonNull(hostConfiguration); Objects.requireNonNull(launch);
            contracts = List.copyOf(contracts); additionalRequiredClasses = List.copyOf(additionalRequiredClasses);
            if (contracts.isEmpty() || contracts.size() > 256 || hostConfiguration.bytes() < 1
                    || hostConfiguration.bytes() > MAX_HOST_CONFIGURATION_BYTES || additionalRequiredClasses.size() > 4096
                    || maximumOutputBytes < 1 || maximumOutputBytes > MAX_PACKAGE_BYTES
                    || !Instant.parse(createdAtUtc).isBefore(Instant.parse(reviewAtUtc))
                    || Instant.parse(reviewAtUtc).isAfter(Instant.parse(createdAtUtc).plusSeconds(86_400)))
                throw new IllegalArgumentException("actual bounded source/configuration closure and finite package window required");
            Set<String> ids = new HashSet<>();
            for (ContractPin contract : contracts) if (!ids.add(contract.contractId())) throw new IllegalArgumentException("duplicate contract ID");
            ids.clear(); ids.addAll(CORE_CLASSES);
            for (String type : additionalRequiredClasses) if (!binaryClass(type) || !ids.add(type)) throw new IllegalArgumentException("unique binary class names required");
            for (String external : List.of(javaHome.root(), nativeInputs.sourceRoot(), launch.temporaryRoot())) {
                Path output = Path.of(outputRoot), other = Path.of(external);
                if (output.startsWith(other) || other.startsWith(output)) throw new IllegalArgumentException("immutable output and external input/work roots must be disjoint");
            }
        }
    }

    public enum ProviderKind { ORIGINAL, GENERATED, TRANSFORMED }
    public record ClassProvider(String binaryName, String relativeJar, ProviderKind kind) {
        public ClassProvider { if (!binaryClass(binaryName)) throw new IllegalArgumentException("binary class name required"); relative(relativeJar); Objects.requireNonNull(kind); }
    }
    public record Layout(List<String> relativeJars, List<String> bootClassPath, List<ClassProvider> applicationClasses) {
        public Layout { relativeJars = List.copyOf(relativeJars); bootClassPath = List.copyOf(bootClassPath); applicationClasses = List.copyOf(applicationClasses); }
    }
    public record OutputFile(String relativePath, FileRef original, Witness actual) {
        public OutputFile { relative(relativePath); Objects.requireNonNull(original); Objects.requireNonNull(actual); }
    }
    public record Quote(long contentBytes, int outputFiles, int outputDirectories, long metadataReserveBytes) {
        public Quote {
            if (contentBytes < 1 || contentBytes > MAX_PACKAGE_BYTES || outputFiles < 2 || outputFiles > MAX_FILES
                    || outputDirectories < 1 || outputDirectories > MAX_FILES || metadataReserveBytes != MAX_METADATA_BYTES)
                throw new IllegalArgumentException("bounded complete physical output quote required");
        }
    }
    public enum PackageStatus { COMPLETE_PACKAGE_NOT_STARTED }
    public record Manifest(String schema, String machineId, String observedAtUtc, PackageStatus status,
            Request request, List<Witness> originalInputs, List<OutputFile> outputFiles,
            Layout layout, String inputClosureSha256, FileRef actualStorageEvidence) {
        public Manifest {
            if (!MANIFEST_SCHEMA.equals(schema)) throw new IllegalArgumentException("runtime manifest version differs");
            machine(machineId); instant(observedAtUtc); Objects.requireNonNull(status); Objects.requireNonNull(request);
            originalInputs = bounded(originalInputs); outputFiles = bounded(outputFiles);
            Objects.requireNonNull(layout); Objects.requireNonNull(actualStorageEvidence);
            if (!machineId.equals(request.machineId()) || inputClosureSha256 == null || !inputClosureSha256.matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("same-machine exact source closure digest required");
        }
    }

    private static List<FileRef> uniqueReferences(List<FileRef> values) {
        Map<String, FileRef> indexed = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (FileRef value : bounded(values)) {
            Objects.requireNonNull(value); absolute(value.path());
            if (indexed.putIfAbsent(Path.of(value.path()).toString(), value) != null)
                throw new IllegalArgumentException("unique exact paths without case aliases required");
        }
        return List.copyOf(indexed.values());
    }
    static <T> List<T> bounded(List<T> values) {
        List<T> result = List.copyOf(values);
        if (result.isEmpty() || result.size() > MAX_FILES) throw new IllegalArgumentException("nonempty bounded closure required");
        return result;
    }
    static void absolute(String value) {
        if (value == null || !Path.of(value).isAbsolute() || !Path.of(value).normalize().equals(Path.of(value)))
            throw new IllegalArgumentException("normalized absolute path required");
    }
    static void inside(String root, FileRef file) {
        if (!Path.of(file.path()).startsWith(Path.of(root)) || Path.of(file.path()).equals(Path.of(root)))
            throw new IllegalArgumentException("file is outside its complete input root");
    }
    static void relative(String value) {
        if (value == null || value.isBlank() || value.contains("\\") || value.contains(":") || value.indexOf('\0') >= 0
                || Path.of(value).isAbsolute() || !Path.of(value).normalize().equals(Path.of(value))
                || value.equals("..") || value.startsWith("../")) throw new IllegalArgumentException("canonical safe relative path required");
    }
    static boolean binaryClass(String value) {
        return value != null && (value.matches("[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)+")
                || value.matches("[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)*\\.package-info"));
    }
    static void text(String value) { if (value == null || value.isBlank() || value.length() > 4096 || value.indexOf('\0') >= 0) throw new IllegalArgumentException("bounded nonempty text required"); }
    static void machine(String value) { if (value == null || !value.matches("[a-z0-9][a-z0-9-]{0,63}") || value.equals("unknown")) throw new IllegalArgumentException("verified explicit machine ID required"); }
    static void instant(String value) { Instant.parse(value); }
    private static void name(FileRef file, String name) {
        Objects.requireNonNull(file);
        if (!Path.of(file.path()).getFileName().toString().equalsIgnoreCase(name)) throw new IllegalArgumentException("actual expected native artifact required: " + name);
    }
}
