package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Source configuration for the existing original GUI oracle, independent of unmaterialized SDK views. */
public final class SdkGuiOracleConfiguration {
    public static final String SCHEMA = "xar.sdk-gui-original-configuration-request/v1";
    private SdkGuiOracleConfiguration() { }

    public record Request(String schema, String machineId, String repositoryRoot, FileRef python,
            long timeoutSeconds, long memoryLimitBytes, String reviewAtUtc, FileRef reviewAuthorityRef) {
        public Request {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact GUI configuration producer schema required");
            Objects.requireNonNull(machineId); Objects.requireNonNull(repositoryRoot); Objects.requireNonNull(python);
            Instant.parse(reviewAtUtc); Objects.requireNonNull(reviewAuthorityRef);
            Path root = Path.of(repositoryRoot);
            if (!root.isAbsolute() || !root.equals(root.normalize())) throw new IllegalArgumentException("Canonical actual original repository required");
        }
    }

    public static GuiEightOracleFixture.Config configuration(Request request) throws IOException {
        Objects.requireNonNull(request); Path root = Path.of(request.repositoryRoot());
        SharedSourceFiles.plainAncestors(root); root = root.toRealPath(); request.python().verify();
        var sources = new ArrayList<GuiEightOracleFixture.Source>();
        for (GuiEightOracleFixture.SourceSpec expected : GuiEightOracleFixture.requiredSources()) {
            Path logical = root.resolve(expected.relativePath()).normalize();
            if (!logical.startsWith(root)) throw new IOException("Original GUI source escaped its declared repository");
            SharedSourceFiles.plainAncestors(logical); Path actual = logical.toRealPath();
            if (!actual.startsWith(root)) throw new IOException("Original GUI source resolved outside its repository");
            FileRef source = FileRef.measure(actual);
            if (!source.sha256().equals(expected.sha256())) throw new IOException("Original GUI source differs: " + expected.relativePath());
            sources.add(new GuiEightOracleFixture.Source(expected.moduleName(), expected.relativePath(), source));
        }
        return new GuiEightOracleFixture.Config(GuiEightOracleFixture.CONFIG_SCHEMA, request.machineId(), root.toString(), request.python(),
                sources, request.timeoutSeconds(), request.memoryLimitBytes(), request.reviewAtUtc());
    }

    public static List<FileRef> inputRefs(Request request) throws IOException {
        var values = new ArrayList<FileRef>(); values.add(request.python()); values.add(request.reviewAuthorityRef());
        var authority = read(request.reviewAuthorityRef(), SdkSourceIntentSuccessor.DataReviewScope.class);
        values.add(authority.parentMetadataScopeRef()); values.add(authority.sourceGrantRef());
        for (GuiEightOracleFixture.Source source : configuration(request).sources()) values.add(source.original());
        return List.copyOf(values);
    }

    public static FileRef produce(FileRef requestRef, Path destination, SdkSourceIntent.MetadataGuard guard) throws IOException {
        Objects.requireNonNull(guard); Request request = read(requestRef, Request.class);
        var authority = read(request.reviewAuthorityRef(), SdkSourceIntentSuccessor.DataReviewScope.class);
        SdkSourceIntentSuccessor.requireReview(request.machineId(), Instant.parse(request.reviewAtUtc()), authority, Instant.now());
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Actual GUI configuration machine differs");
        List<FileRef> inputs = inputRefs(request); for (FileRef input : inputs) input.verify();
        GuiEightOracleFixture.Config configuration = configuration(request);
        byte[] bytes = GuiEightOracleFixture.encodeConfiguration(configuration);
        if (bytes.length > 65536) throw new IOException("Bounded eighteen-source GUI configuration required");
        if (!destination.isAbsolute() || !destination.equals(destination.normalize()) || destination.getParent() == null
                || !Files.isDirectory(destination.getParent()) || Files.exists(destination)) throw new IOException("New canonical GUI configuration path required");
        ProjectStoragePolicy.requireBulkOutput(destination.getParent()); SharedSourceFiles.plainAncestors(destination);
        guard.revalidate(bytes.length); requestRef.verify(); Files.write(destination, bytes, StandardOpenOption.CREATE_NEW);
        FileRef actual = FileRef.measure(destination);
        if (!GuiEightOracleFixture.readConfiguration(actual).equals(configuration)) throw new IOException("Original GUI configuration persisted roundtrip differs");
        for (FileRef input : inputs) input.verify(); requestRef.verify(); guard.revalidate(0);
        SdkSourceIntentSuccessor.requireReview(request.machineId(), Instant.parse(request.reviewAtUtc()), authority, Instant.now());
        return actual;
    }

    public static List<String> properties(FileRef configuration) throws IOException {
        GuiEightOracleFixture.readConfiguration(configuration);
        return List.of("-D" + GuiEightOracleFixture.PROPERTY + "=" + configuration.path(),
                "-D" + GuiEightOracleFixture.PROPERTY + ".bytes=" + configuration.bytes(),
                "-D" + GuiEightOracleFixture.PROPERTY + ".sha256=" + configuration.sha256());
    }

    /** The parent keeps the complete existing dependency pins; this only exports their ordered interpreter search roots. */
    public static Map<String, String> interpreterEnvironment(SdkStageConfigurationProducer.InterpreterInputs interpreter) {
        Objects.requireNonNull(interpreter); var roots = new ArrayList<String>();
        for (String value : interpreter.dependencyRoots()) {
            Path root = Path.of(value);
            if (!root.isAbsolute() || !root.equals(root.normalize())) throw new IllegalArgumentException("Exact interpreter dependency roots required");
            roots.add(root.toString());
        }
        return Map.of("PYTHONPATH", String.join(java.io.File.pathSeparator, roots), "PYTHONDONTWRITEBYTECODE", "1");
    }

    private static <T> T read(FileRef ref, Class<T> type) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > 65536) throw new IOException("Bounded exact GUI metadata required");
        ref.verify(); T result = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), type); ref.verify(); return result;
    }
}
