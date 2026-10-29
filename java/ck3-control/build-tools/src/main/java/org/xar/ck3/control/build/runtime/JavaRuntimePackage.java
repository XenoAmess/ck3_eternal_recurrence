package org.xar.ck3.control.build.runtime;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.BuildReceipt;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ContractPin;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Layout;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Manifest;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.OutputFile;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.PackageStatus;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Quote;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;

/** One Java-only package producer. It neither starts a process nor grants Game/ledger authority. */
public final class JavaRuntimePackage {
    public static final String MANIFEST_FILE = "runtime-manifest.json";
    public static final String HOST_CONFIGURATION_FILE = "application.json";
    private JavaRuntimePackage() { }

    /** Root implements this using its real typed configuration/native-source qualification readers.
     * A JSON status flag, SDK Python qualification or no-op substitute is not an implementation.
     * It must validate the complete Native source set/artifacts and installed Java-only composition.
     */
    @FunctionalInterface public interface NativeAuthorityVerifier {
        NativeProof verify(Request request, FileRef actualHostConfiguration) throws IOException;
    }
    public record WritePermit(String machineId, String exactOutputRoot, String expiresAtUtc,
            long allocationUpperBytes, long allocationUnitBytes, long perDirectoryGuardBytes,
            FileRef actualStorageEvidence) {
        public WritePermit {
            JavaRuntimePackageModel.machine(machineId); JavaRuntimePackageModel.absolute(exactOutputRoot);
            Instant.parse(expiresAtUtc); Objects.requireNonNull(actualStorageEvidence);
            if (allocationUpperBytes < 1 || allocationUpperBytes > JavaRuntimePackageModel.MAX_PACKAGE_BYTES
                    || allocationUnitBytes < 1 || allocationUnitBytes > (1L << 20) || perDirectoryGuardBytes < 4096)
                throw new IllegalArgumentException("finite same-machine native allocation permit required");
        }
    }
    public interface CapacityGate {
        WritePermit acquire(Request request, Quote exactQuote) throws IOException;
        void revalidate(WritePermit permit, long consumedAllocationUpperBytes) throws IOException;
    }
    public enum Stage { BUILD_OR_INPUT_UNAVAILABLE, PACKAGE_UNAVAILABLE, MATERIALIZATION_FAILED }
    public sealed interface ReviewResult permits ReviewAvailable, Unavailable { }
    public sealed interface CapturedReviewResult permits CapturedReviewAvailable, Unavailable { }
    public sealed interface ReadResult permits PackageAvailable, Unavailable { }
    public sealed interface ProductionResult permits PackageAvailable, Unavailable { }
    public record Unavailable(Stage stage, String reason) implements ReviewResult, CapturedReviewResult, ReadResult, ProductionResult {
        public Unavailable { Objects.requireNonNull(stage); JavaRuntimePackageModel.text(reason); }
    }
    public record PackageAvailable(VerifiedPackage value) implements ReadResult, ProductionResult {
        public PackageAvailable { Objects.requireNonNull(value); }
    }
    /** Minted only after real accepted Maven/deployment/source readers and actual native FileIDs. */
    public static final class ReviewAvailable implements ReviewResult {
        private final Prepared prepared;
        private ReviewAvailable(Prepared prepared) { this.prepared = prepared; }
        public Request request() { return prepared.request(); }
        public Quote quote() { return prepared.quote(); }
        public Layout layout() { return prepared.layout(); }
    }
    /** Review of real compiled service/test originals only. This is neither a package nor software admission. */
    public static final class CapturedReviewAvailable implements CapturedReviewResult {
        private final Prepared prepared;
        private final ControlBuild.CaptureBuildReceipt build;
        private final NativeAuthorityVerifier authority;
        private CapturedReviewAvailable(Prepared prepared, NativeAuthorityVerifier authority) {
            if (!(prepared.build() instanceof CapturedServiceBuild captured))
                throw new IllegalArgumentException("actual capture-only service review required");
            this.prepared = prepared; this.build = captured.actual(); this.authority = authority;
        }
        public Request request() { return prepared.request(); }
        public ControlBuild.CaptureBuildReceipt build() { return build; }
        public ControlBuild.CaptureQualification qualification() { return build.qualification(); }
        public ControlBuild.CaptureTestState tests() { return build.tests(); }
        public Layout layout() { return prepared.layout(); }
        public Quote quote() { return prepared.quote(); }
        public List<FileRef> completePins() { return prepared.inputs().stream().map(Witness::source).toList(); }
        public void verifyCurrent() throws IOException {
            Prepared fresh = prepare(request(), authority, false, true);
            if (!(fresh.build() instanceof CapturedServiceBuild captured) || !captured.actual().equals(build)
                    || !fresh.inputs().equals(prepared.inputs()) || !fresh.layout().equals(layout())
                    || !fresh.quote().equals(quote()) || !fresh.inputDigest().equals(prepared.inputDigest()))
                throw new IOException("capture-only service review changed from its actual originals");
        }
    }
    /** A caller DTO cannot construct this object. Startup obtains it via readAccepted/produce. */
    public static final class VerifiedPackage {
        private final FileRef manifestRef;
        private final Manifest manifest;
        private final NativeAuthorityVerifier authority;
        private VerifiedPackage(FileRef manifestRef, Manifest manifest, NativeAuthorityVerifier authority) {
            this.manifestRef = manifestRef; this.manifest = manifest; this.authority = authority;
        }
        public FileRef manifestRef() { return manifestRef; }
        public Manifest manifest() { return manifest; }
        public void verifyCurrent() throws IOException { validatePublished(manifestRef, manifest, authority); }
        public FileRef hostConfiguration() throws IOException {
            return manifest.outputFiles().stream().filter(row -> row.relativePath().equals(HOST_CONFIGURATION_FILE))
                    .findFirst().orElseThrow(() -> new IOException("actual host configuration absent")).actual().source();
        }
    }
    private sealed interface ServiceBuild permits VerifiedServiceBuild, CapturedServiceBuild {
        String machineId();
        ControlBuild.TargetKind targetKind();
        FileRef javaExecutableRef();
        String deploymentRoot();
        List<FileRef> sourcePins();
        List<FileRef> compiledSourcePins();
        List<FileRef> producerRuntimePins();
        List<FileRef> completeDeployment();
        FileRef capacityReleaseRef();
        ControlBuild.MavenToolchain mavenToolchain();
        List<FileRef> supplementalInputs() throws IOException;
    }
    private record VerifiedServiceBuild(BuildReceipt actual) implements ServiceBuild {
        public String machineId() { return actual.machineId(); }
        public ControlBuild.TargetKind targetKind() { return actual.targetKind(); }
        public FileRef javaExecutableRef() { return actual.javaExecutableRef(); }
        public String deploymentRoot() { return actual.deploymentRoot(); }
        public List<FileRef> sourcePins() { return actual.sourcePins(); }
        public List<FileRef> compiledSourcePins() { return actual.compiledSourcePins(); }
        public List<FileRef> producerRuntimePins() { return actual.producerRuntimePins(); }
        public List<FileRef> completeDeployment() { return actual.completeDeployment(); }
        public FileRef capacityReleaseRef() { return actual.capacityReleaseRef(); }
        public ControlBuild.MavenToolchain mavenToolchain() { return actual.mavenToolchain(); }
        public List<FileRef> supplementalInputs() { return List.of(); }
    }
    private record CapturedServiceBuild(ControlBuild.CaptureBuildReceipt actual) implements ServiceBuild {
        public String machineId() { return actual.machineId(); }
        public ControlBuild.TargetKind targetKind() { return actual.targetKind(); }
        public FileRef javaExecutableRef() { return actual.javaExecutableRef(); }
        public String deploymentRoot() { return actual.deploymentRoot(); }
        public List<FileRef> sourcePins() { return actual.sourcePins(); }
        public List<FileRef> compiledSourcePins() { return actual.compiledSourcePins(); }
        public List<FileRef> producerRuntimePins() { return actual.producerRuntimePins(); }
        public List<FileRef> completeDeployment() { return actual.completeDeployment(); }
        public FileRef capacityReleaseRef() { return actual.capacityReleaseRef(); }
        public ControlBuild.MavenToolchain mavenToolchain() { return actual.mavenToolchain(); }
        public List<FileRef> supplementalInputs() throws IOException {
            FileRef compilation = actual.testCompilationRef();
            if (compilation.bytes() < 1 || compilation.bytes() > (4 << 20))
                throw new IOException("bounded actual capture test-compilation manifest required");
            var manifest = ControlBuild.strictMapper().readValue(JavaRuntimePackageCodec.read(compilation),
                    ControlBuild.TestCompilationManifest.class);
            if (!manifest.machineId().equals(machineId()) || manifest.tests() != ControlBuild.CaptureTestState.NOT_RUN)
                throw new IOException("capture test-compilation manifest changed its machine or NOT_RUN state");
            List<FileRef> result = new ArrayList<>(List.of(actual.mavenCommandRef(), actual.mavenStdoutRef(),
                    actual.mavenStderrRef(), actual.versionStdoutRef(), compilation));
            for (var module : manifest.modules())
                result.addAll(List.of(module.modulePomRef(), module.compilerInputsRef(), module.compilerCreatedFilesRef()));
            for (var test : manifest.notRunTests()) {
                result.add(test.sourceRef()); result.addAll(test.compiledClassRefs());
            }
            return List.copyOf(result);
        }
    }
    private record Prepared(Request request, ServiceBuild build, List<Witness> inputs,
            List<FileRef> deployment, Layout layout, Quote quote, String inputDigest, NativeProof nativeProof) { }

    public static ReviewResult review(Request request, NativeAuthorityVerifier authority) {
        try { return new ReviewAvailable(prepare(request, authority, false)); }
        catch (IOException | IllegalArgumentException failure) { return unavailable(Stage.BUILD_OR_INPUT_UNAVAILABLE, failure); }
    }

    /** Explicit compile-only review; ordinary review/produce/readAccepted never dispatch to this branch. */
    public static CapturedReviewResult reviewCapturedService(Request request, NativeAuthorityVerifier authority) {
        try { return new CapturedReviewAvailable(prepare(request, authority, false, true), authority); }
        catch (IOException | IllegalArgumentException failure) { return unavailable(Stage.BUILD_OR_INPUT_UNAVAILABLE, failure); }
    }

    /** CREATE_NEW only. A failure retains its partial directory and cannot yield a verified package. */
    public static ProductionResult produce(ReviewAvailable acceptedReview, NativeAuthorityVerifier authority, CapacityGate capacity) {
        Objects.requireNonNull(acceptedReview); Objects.requireNonNull(capacity); Objects.requireNonNull(authority);
        try {
            Prepared fresh = prepare(acceptedReview.request(), authority, false);
            if (!fresh.inputs().equals(acceptedReview.prepared.inputs()) || !fresh.layout().equals(acceptedReview.layout())
                    || !fresh.quote().equals(acceptedReview.quote())) throw new IOException("accepted package inputs changed; request a new review");
            WritePermit permit = capacity.acquire(fresh.request(), fresh.quote());
            validatePermit(fresh.request(), permit);
            if (allocationUpper(fresh, permit) > permit.allocationUpperBytes()) throw new IOException("complete package forecast exceeds live native allocation permit");
            capacity.revalidate(permit, 0); Path root = Path.of(fresh.request().outputRoot());
            if (Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("fresh immutable package output must be absent");
            SharedSourceFiles.plainAncestors(root); ProjectStoragePolicy.requireBulkOutput(root); Files.createDirectory(root);
            List<OutputFile> outputs = new ArrayList<>(); long allocated = 0;
            Set<Path> directories = new HashSet<>(); directories.add(root);
            Path deployment = Path.of(fresh.build().deploymentRoot());
            for (FileRef source : fresh.deployment()) {
                String relative = "quarkus-app/" + deployment.relativize(Path.of(source.path())).toString().replace('\\', '/');
                Path destination = root.resolve(relative); addParents(root, destination.getParent(), directories);
                long forecast = Math.addExact(allocated, round(source.bytes(), permit.allocationUnitBytes()));
                guard(capacity, permit, Math.addExact(forecast, directoryGuard(directories, permit)));
                Witness actual = JavaRuntimePackageFiles.copyNew(source, destination);
                allocated = Math.addExact(allocated, actual.nativeFile().allocatedBytes());
                outputs.add(new OutputFile(relative, source, actual));
                guard(capacity, permit, Math.addExact(allocated, directoryGuard(directories, permit)));
            }
            guard(capacity, permit, Math.addExact(allocated, round(fresh.request().hostConfiguration().bytes(), permit.allocationUnitBytes())));
            Witness host = JavaRuntimePackageFiles.copyNew(fresh.request().hostConfiguration(), root.resolve(HOST_CONFIGURATION_FILE));
            allocated = Math.addExact(allocated, host.nativeFile().allocatedBytes());
            outputs.add(new OutputFile(HOST_CONFIGURATION_FILE, fresh.request().hostConfiguration(), host));
            outputs.sort(Comparator.comparing(OutputFile::relativePath));
            for (Witness input : fresh.inputs()) SharedSourceFiles.assertUnchanged(input);
            requireSameNativeQualification(fresh.nativeProof(), verifyNativeAuthority(fresh.request(), host.source(), authority));
            Manifest manifest = new Manifest(JavaRuntimePackageModel.MANIFEST_SCHEMA, fresh.request().machineId(), Instant.now().toString(),
                    PackageStatus.COMPLETE_PACKAGE_NOT_STARTED, fresh.request(), fresh.inputs(), outputs, fresh.layout(), fresh.inputDigest(), permit.actualStorageEvidence());
            byte[] raw = JavaRuntimePackageCodec.encodeManifest(manifest);
            guard(capacity, permit, Math.addExact(Math.addExact(allocated, round(raw.length, permit.allocationUnitBytes())), directoryGuard(directories, permit)));
            Path target = root.resolve(MANIFEST_FILE); writeNew(target, raw);
            Witness manifestFile = SharedSourceFiles.observe(target);
            allocated = Math.addExact(allocated, manifestFile.nativeFile().allocatedBytes());
            guard(capacity, permit, Math.addExact(allocated, directoryGuard(directories, permit)));
            return readAccepted(manifestFile.source(), authority) instanceof PackageAvailable available
                    ? available : new Unavailable(Stage.MATERIALIZATION_FAILED, "published package readback did not establish complete current closure");
        } catch (IOException | IllegalArgumentException failure) { return unavailable(Stage.MATERIALIZATION_FAILED, failure); }
    }

    public static ReadResult readAccepted(FileRef actualManifest, NativeAuthorityVerifier authority) {
        Objects.requireNonNull(authority);
        try {
            Manifest manifest = JavaRuntimePackageCodec.readManifest(actualManifest);
            validatePublished(actualManifest, manifest, authority);
            return new PackageAvailable(new VerifiedPackage(actualManifest, manifest, authority));
        } catch (IOException | IllegalArgumentException failure) { return unavailable(Stage.PACKAGE_UNAVAILABLE, failure); }
    }

    private static Prepared prepare(Request request, NativeAuthorityVerifier authority, boolean existingOutput) throws IOException {
        return prepare(request, authority, existingOutput, false);
    }

    private static Prepared prepare(Request request, NativeAuthorityVerifier authority, boolean existingOutput,
            boolean capturedService) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(authority); requireCurrent(request);
        Path root = Path.of(request.outputRoot()); SharedSourceFiles.plainAncestors(root);
        ProjectStoragePolicy.requireBulkOutput(root);
        if (!existingOutput && Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("fresh package output already exists; immutable generations cannot be overwritten");
        request.serviceBuildActual().verify();
        // Historical completed software evidence does not renew its old execution/storage card.
        // This operation still needs the fresh request, same-machine native authority and CapacityGate.
        ServiceBuild build = capturedService
                ? new CapturedServiceBuild(ControlBuild.verifiedCompletedCaptureReceipt(request.serviceBuildActual()))
                : new VerifiedServiceBuild(ControlBuild.verifiedCompletedReceipt(request.serviceBuildActual()));
        if (build.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR || !build.machineId().equals(request.machineId())
                || !build.javaExecutableRef().equals(request.javaHome().executable())) throw new IOException("actual same-machine Java service build/runtime image mismatch");
        JavaRuntimePackageFiles.verifyCompleteTree(Path.of(build.deploymentRoot()), build.completeDeployment(), 512L << 20);
        List<FileRef> deployment = build.completeDeployment();
        JavaRuntimePackageFiles.verifyCompleteTree(Path.of(request.javaHome().root()), request.javaHome().completeRuntimeFiles(), 4L << 30);
        Map<String, FileRef> javaFiles = JavaRuntimePackageFiles.relativeIndex(Path.of(request.javaHome().root()), request.javaHome().completeRuntimeFiles());
        for (String required : List.of("bin/java.exe", "bin/server/jvm.dll", "lib/modules", "release", "conf/security/java.security"))
            if (!javaFiles.containsKey(required) || javaFiles.get(required).bytes() == 0) throw new IOException("actual selected Java runtime component missing: " + required);
        for (ContractPin contract : request.contracts()) if (!build.sourcePins().contains(contract.source())) throw new IOException("contract source was not part of the actual compiled source graph");
        for (FileRef file : deployment) if (Path.of(file.path()).startsWith(root) || root.startsWith(Path.of(file.path()))) throw new IOException("package output aliases a frozen deployment input");
        List<String> required = new ArrayList<>(JavaRuntimePackageModel.CORE_CLASSES); required.addAll(request.additionalRequiredClasses());
        Layout layout = JavaRuntimePackageFiles.inspectFastJar(Path.of(build.deploymentRoot()), deployment, required);
        NativeProof nativeProof = verifyNativeAuthority(request, request.hostConfiguration(), authority);
        Map<String, FileRef> all = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        add(all, request.serviceBuildActual()); add(all, request.hostConfiguration());
        for (List<FileRef> group : List.of(build.sourcePins(), build.compiledSourcePins(), build.producerRuntimePins(), request.javaHome().completeRuntimeFiles(), request.nativeInputs().completeSources(), deployment))
            for (FileRef file : group) add(all, file);
        for (FileRef file : build.supplementalInputs()) add(all, file);
        var nativeInputs = request.nativeInputs();
        for (FileRef file : List.of(build.capacityReleaseRef(), build.mavenToolchain().distributionLauncherRef(), nativeInputs.bridgeDll(),
                nativeInputs.injector(), nativeInputs.gameExecutable(), nativeInputs.launcherSettings())) add(all, file);
        for (FileRef file : nativeProof.completeEvidenceClosure()) add(all, file);
        if (build.mavenToolchain().explicitOverrideRef() != null) add(all, build.mavenToolchain().explicitOverrideRef());
        for (ContractPin contract : request.contracts()) add(all, contract.source());
        List<Witness> witnesses = new ArrayList<>();
        for (FileRef file : all.values()) {
            if (Path.of(file.path()).startsWith(root)) throw new IOException("an original runtime input aliases the new output");
            Witness witness = SharedSourceFiles.observe(Path.of(file.path()));
            if (!witness.source().equals(file)) throw new IOException("runtime input differs from exact source reference"); witnesses.add(witness);
        }
        requireSameNativeQualification(nativeProof, verifyNativeAuthority(request, request.hostConfiguration(), authority));
        for (Witness witness : witnesses) SharedSourceFiles.assertUnchanged(witness);
        long bytes = request.hostConfiguration().bytes(); Set<String> directories = new LinkedHashSet<>(); directories.add("."); directories.add("quarkus-app");
        for (FileRef file : deployment) {
            bytes = Math.addExact(bytes, file.bytes()); String relative = "quarkus-app/" + Path.of(build.deploymentRoot()).relativize(Path.of(file.path())).toString().replace('\\', '/');
            while (relative.contains("/")) { relative = relative.substring(0, relative.lastIndexOf('/')); directories.add(relative); }
        }
        Quote quote = new Quote(bytes, deployment.size() + 2, directories.size(), JavaRuntimePackageModel.MAX_METADATA_BYTES);
        if (Math.addExact(bytes, quote.metadataReserveBytes()) > request.maximumOutputBytes()) throw new IOException("complete package and metadata exceed explicit maximum output bytes");
        return new Prepared(request, build, List.copyOf(witnesses), deployment, layout, quote,
                JavaRuntimePackageCodec.digest(JavaRuntimePackageCodec.encode(witnesses)), nativeProof);
    }

    private static void validatePublished(FileRef reference, Manifest manifest, NativeAuthorityVerifier authority) throws IOException {
        Path root = Path.of(manifest.request().outputRoot());
        if (!Path.of(reference.path()).equals(root.resolve(MANIFEST_FILE))) throw new IOException("manifest must be its actual package root leaf");
        if (!JavaRuntimePackageCodec.readManifest(reference).equals(manifest)) throw new IOException("manifest body differs from its exact original");
        Prepared fresh = prepare(manifest.request(), authority, true);
        if (!manifest.originalInputs().equals(fresh.inputs()) || !manifest.inputClosureSha256().equals(fresh.inputDigest()) || !manifest.layout().equals(fresh.layout()))
            throw new IOException("actual original source/runtime identity or closure differs");
        List<FileRef> expected = new ArrayList<>(); expected.add(reference);
        List<FileRef> actualDeployment = new ArrayList<>(); Set<String> names = new HashSet<>();
        Map<String, FileRef> originals = new TreeMap<>(JavaRuntimePackageFiles.relativeIndex(Path.of(fresh.build().deploymentRoot()), fresh.deployment()));
        FileRef actualHost = null;
        for (OutputFile output : manifest.outputFiles()) {
            if (!names.add(output.relativePath()) || !Path.of(output.actual().source().path()).equals(root.resolve(output.relativePath()))) throw new IOException("duplicate or misplaced package output");
            SharedSourceFiles.assertUnchanged(output.actual());
            if (output.actual().source().bytes() != output.original().bytes() || !output.actual().source().sha256().equals(output.original().sha256())) throw new IOException("packaged output bytes differ from original");
            if (output.relativePath().equals(HOST_CONFIGURATION_FILE)) {
                if (!output.original().equals(manifest.request().hostConfiguration())) throw new IOException("packaged configuration is not the actual Root configuration");
                actualHost = output.actual().source();
            } else if (output.relativePath().startsWith("quarkus-app/")) {
                FileRef original = originals.remove(output.relativePath().substring("quarkus-app/".length()));
                if (original == null || !original.equals(output.original())) throw new IOException("unlisted or wrong-source packaged dependency");
                actualDeployment.add(output.actual().source());
            } else throw new IOException("unexpected package payload role");
            expected.add(output.actual().source());
        }
        if (!originals.isEmpty() || actualHost == null) throw new IOException("package omits actual dependencies or Root configuration");
        expected.sort(Comparator.comparing(FileRef::path));
        JavaRuntimePackageFiles.verifyCompleteTree(root, expected, manifest.request().maximumOutputBytes());
        if (!JavaRuntimePackageFiles.inspectFastJar(root.resolve("quarkus-app"), actualDeployment, requiredClasses(manifest.request())).equals(manifest.layout())) throw new IOException("actual copied fast-jar class/boot closure differs");
        requireSameNativeQualification(fresh.nativeProof(), verifyNativeAuthority(manifest.request(), actualHost, authority));
        manifest.actualStorageEvidence().verify(); requireCurrent(manifest.request());
    }

    /** The exact same proof reader is used before private copies and after published-package import.
     * Returned stage/tool/source references enter Prepared.originalInputs and the persisted witness closure.
     */
    static NativeProof verifyNativeAuthority(Request request, FileRef actualHostConfiguration,
            NativeAuthorityVerifier authority) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(actualHostConfiguration); Objects.requireNonNull(authority);
        if (authority.getClass().isSynthetic() || authority.getClass().isAnonymousClass())
            throw new IOException("fixed named source-reviewed Root native reader required");
        Witness host = SharedSourceFiles.observe(Path.of(actualHostConfiguration.path()));
        if (!host.source().equals(actualHostConfiguration)
                || actualHostConfiguration.bytes() != request.hostConfiguration().bytes()
                || !actualHostConfiguration.sha256().equals(request.hostConfiguration().sha256()))
            throw new IOException("actual Root configuration differs from the reviewed original");
        NativeProof proof = authority.verify(request, actualHostConfiguration);
        if (proof == null || !proof.machineId().equals(request.machineId()) || proof.mode() != request.launch().mode()
                || !proof.actualHostConfiguration().equals(actualHostConfiguration) || !proof.expected().equals(request.nativeInputs()))
            throw new IOException("real Native reader proof differs from exact Root/native package inputs");
        for (FileRef evidence : proof.completeEvidenceClosure()) evidence.verify();
        SharedSourceFiles.assertUnchanged(host); return proof;
    }

    private static void requireSameNativeQualification(NativeProof original, NativeProof packaged) throws IOException {
        if (!original.machineId().equals(packaged.machineId()) || original.mode() != packaged.mode()
                || !original.expected().equals(packaged.expected())
                || !original.completeEvidenceClosure().equals(packaged.completeEvidenceClosure()))
            throw new IOException("Native stage/tool/source closure changed across the package producer/import reader");
    }

    private static List<String> requiredClasses(Request request) {
        List<String> required = new ArrayList<>(JavaRuntimePackageModel.CORE_CLASSES); required.addAll(request.additionalRequiredClasses()); return List.copyOf(required);
    }
    private static void add(Map<String, FileRef> values, FileRef reference) throws IOException {
        if (values.size() >= JavaRuntimePackageModel.MAX_FILES) throw new IOException("full runtime input closure exceeds finite file envelope");
        FileRef previous = values.putIfAbsent(Path.of(reference.path()).normalize().toString(), reference);
        if (previous != null && !previous.equals(reference)) throw new IOException("conflicting exact references share one physical input path");
    }
    private static void requireCurrent(Request request) throws IOException {
        Instant now = Instant.now();
        if (!WindowsJobProcess.currentMachineId().equals(request.machineId()) || now.isBefore(Instant.parse(request.createdAtUtc())) || !now.isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("actual current machine and unexpired runtime-package binding required");
    }
    private static void validatePermit(Request request, WritePermit permit) throws IOException {
        if (!permit.machineId().equals(request.machineId()) || !permit.exactOutputRoot().equals(request.outputRoot())
                || permit.allocationUpperBytes() > request.maximumOutputBytes()) throw new IOException("live storage permit differs from exact runtime package");
        permit.actualStorageEvidence().verify();
        if (!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc()))) throw new IOException("runtime package storage permit expired");
    }
    /** DATA quote for the same genuine review used by produce; this does not issue a storage permit. */
    public static long allocationUpperBytes(ReviewAvailable reviewed, long allocationUnitBytes, long perDirectoryGuardBytes) {
        Objects.requireNonNull(reviewed);
        if (allocationUnitBytes < 1 || allocationUnitBytes > (1L << 20) || perDirectoryGuardBytes < 4096)
            throw new IllegalArgumentException("finite native geometry and directory guard required");
        return allocationUpper(reviewed.prepared, allocationUnitBytes, perDirectoryGuardBytes);
    }
    /** The same DATA estimate; this does not issue a write permit or convert capture-only qualification. */
    public static long allocationUpperBytes(CapturedReviewAvailable reviewed, long allocationUnitBytes, long perDirectoryGuardBytes) {
        Objects.requireNonNull(reviewed);
        if (allocationUnitBytes < 1 || allocationUnitBytes > (1L << 20) || perDirectoryGuardBytes < 4096)
            throw new IllegalArgumentException("finite native geometry and directory guard required");
        return allocationUpper(reviewed.prepared, allocationUnitBytes, perDirectoryGuardBytes);
    }
    private static long allocationUpper(Prepared value, WritePermit permit) {
        return allocationUpper(value, permit.allocationUnitBytes(), permit.perDirectoryGuardBytes());
    }
    private static long allocationUpper(Prepared value, long allocationUnitBytes, long perDirectoryGuardBytes) {
        long upper = round(value.request().hostConfiguration().bytes(), allocationUnitBytes);
        for (FileRef file : value.deployment()) upper = Math.addExact(upper, round(file.bytes(), allocationUnitBytes));
        return Math.addExact(Math.addExact(upper, round(value.quote().metadataReserveBytes(), allocationUnitBytes)), Math.multiplyExact(value.quote().outputDirectories(), perDirectoryGuardBytes));
    }
    private static long round(long bytes, long unit) { return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, unit - 1), unit), unit); }
    private static long directoryGuard(Set<Path> directories, WritePermit permit) { return Math.multiplyExact(directories.size(), permit.perDirectoryGuardBytes()); }
    private static void addParents(Path root, Path current, Set<Path> directories) {
        while (current != null && current.startsWith(root)) { directories.add(current); if (current.equals(root)) break; current = current.getParent(); }
    }
    private static void guard(CapacityGate gate, WritePermit permit, long upper) throws IOException {
        if (!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())) || upper > permit.allocationUpperBytes()) throw new IOException("live package storage boundary exceeded");
        gate.revalidate(permit, upper);
    }
    private static void writeNew(Path path, byte[] raw) throws IOException {
        try (FileChannel file = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer input = ByteBuffer.wrap(raw); while (input.hasRemaining()) file.write(input); file.force(true);
        }
    }
    private static Unavailable unavailable(Stage stage, Exception error) {
        String message = error.getClass().getSimpleName() + ": " + String.valueOf(error.getMessage());
        if (message.length() > 4000) message = message.substring(0, 4000);
        return new Unavailable(stage, message.replace('\0', '?'));
    }
}
