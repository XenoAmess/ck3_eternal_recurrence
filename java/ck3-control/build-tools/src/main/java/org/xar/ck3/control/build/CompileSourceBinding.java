package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.DirectoryIdentity;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** One retained source contract for a reusable compile tree. It never copies or builds source. */
public final class CompileSourceBinding {
    public static final String SCHEMA = "xar.native-compile-source-binding/v1";
    private static final ObjectMapper JSON = RootNativePlanJson.mapper();
    private static final int MAX_BYTES = 16 << 20;
    private static final int MAX_FILES = 16000;

    private CompileSourceBinding() { }

    public record Row(String relativePath, Witness retainedWitness) {
        public Row {
            relative(relativePath);
            Objects.requireNonNull(retainedWitness);
            Objects.requireNonNull(retainedWitness.source());
            Objects.requireNonNull(retainedWitness.nativeFile());
            if (retainedWitness.source().bytes() != retainedWitness.nativeFile().logicalBytes())
                throw new IllegalArgumentException("Retained content and original native witness disagree");
        }
    }

    public record Binding(String schema, String machineId, FileRef producerToolsBuildRef,
            List<FileRef> completeToolsRuntime, FileRef retainedSourceActualRef, Witness retainedSourceActualWitness,
            Path retainedSourceRoot, DirectoryIdentity retainedRootIdentity,
            Path compileSourceRoot, DirectoryIdentity compileRootIdentity, List<Row> rows) {
        public Binding {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                    || machineId.equals("unknown"))
                throw new IllegalArgumentException("Versioned exact-machine compile-source binding required");
            Objects.requireNonNull(producerToolsBuildRef);
            Objects.requireNonNull(retainedSourceActualRef);
            Objects.requireNonNull(retainedSourceActualWitness);
            Objects.requireNonNull(retainedSourceActualWitness.nativeFile());
            if (!retainedSourceActualWitness.source().equals(retainedSourceActualRef)
                    || retainedSourceActualRef.bytes() != retainedSourceActualWitness.nativeFile().logicalBytes())
                throw new IllegalArgumentException("Original retained Source Actual manifest witness required");
            completeToolsRuntime = List.copyOf(completeToolsRuntime);
            if (completeToolsRuntime.isEmpty() || new HashSet<>(completeToolsRuntime).size() != completeToolsRuntime.size())
                throw new IllegalArgumentException("Original complete producer runtime required");
            retainedSourceRoot = absolute(retainedSourceRoot);
            compileSourceRoot = absolute(compileSourceRoot);
            Objects.requireNonNull(retainedRootIdentity);
            Objects.requireNonNull(compileRootIdentity);
            if (retainedSourceRoot.startsWith(compileSourceRoot) || compileSourceRoot.startsWith(retainedSourceRoot)
                    || retainedRootIdentity.equals(compileRootIdentity))
                throw new IllegalArgumentException("Separate retained and compile source trees required");
            rows = List.copyOf(rows);
            if (rows.isEmpty() || rows.size() > MAX_FILES)
                throw new IllegalArgumentException("Complete finite source domain required");
            Set<String> names = new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
            String previous = null;
            for (Row row : rows) {
                String name = row.relativePath();
                if (!names.add(name) || previous != null && previous.compareTo(row.relativePath()) >= 0
                        || !Path.of(row.retainedWitness().source().path()).equals(
                                retainedSourceRoot.resolve(row.relativePath())))
                    throw new IllegalArgumentException("Canonical unique retained relative-source mapping required");
                previous = row.relativePath();
            }
        }
    }

    /** Historical acceptance reads only retained source, its exact producer and its immutable witnesses. */
    public static Binding readHistorical(FileRef ref) throws IOException {
        require(ref.bytes() > 0 && ref.bytes() <= MAX_BYTES, "Finite compile-source binding required");
        Witness manifestBefore = SharedSourceFiles.observe(Path.of(ref.path()));
        require(manifestBefore.source().equals(ref), "Original binding manifest content differs");
        byte[] raw;
        try (var stream = Files.newInputStream(Path.of(ref.path()))) { raw = stream.readNBytes(MAX_BYTES + 1); }
        require(raw.length == ref.bytes() && raw.length <= MAX_BYTES, "Compile-source binding size changed");
        Binding binding = JSON.readValue(raw, Binding.class);
        verifyHistorical(binding);
        SharedSourceFiles.assertUnchanged(manifestBefore);
        return binding;
    }

    public record LiveRead(Binding binding, List<Witness> compileBefore) {
        public LiveRead {
            Objects.requireNonNull(binding);
            compileBefore = List.copyOf(compileBefore);
            if (!compileBefore.stream().map(Witness::source).toList().equals(compileSources(binding)))
                throw new IllegalArgumentException("Complete actual compile preimage required");
        }
    }

    /** Caller holds the original writer lock before entering and until its stage has settled. */
    public static LiveRead readForLiveStage(FileRef ref) throws IOException {
        Binding binding = readHistorical(ref);
        List<Witness> before = observeCurrentFiles(binding);
        ref.verify();
        return new LiveRead(binding, before);
    }

    /** Called by the existing SourceCut producer after one retained snapshot, never a development clone. */
    public static Binding create(FileRef qualifiedToolsBuildRef, FileRef retainedSourceActualRef,
            Path compileSourceRoot) throws IOException {
        var producer = ControlBuild.verifiedCompletedReceipt(qualifiedToolsBuildRef);
        require(producer.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && producer.completeDeployment().equals(ControlBuild.producerClosure()),
                "Exact current binding producer runtime required");
        var source = NativeCombinedSourceCut.readAcceptedSource(retainedSourceActualRef);
        Binding binding = captureFiles(qualifiedToolsBuildRef, producer.completeDeployment(), source.machineId(),
                retainedSourceActualRef, Path.of(source.nativeSourceRoot()), source.completeNativeSources(), compileSourceRoot);
        verifyHistorical(binding);
        return binding;
    }

    /** Mechanical capture used by the qualified producer; candidates alone grant no source authority. */
    static Binding captureFiles(FileRef producerRef, List<FileRef> runtime, String machineId,
            FileRef sourceActualRef, Path retained, List<FileRef> retainedRefs, Path compileSourceRoot) throws IOException {
        retained = absolute(retained);
        Path compile = absolute(compileSourceRoot);
        plainRoot(retained); plainRoot(compile);
        DirectoryIdentity retainedIdentity = SharedSourceFiles.nativeDirectory(retained);
        DirectoryIdentity compileIdentity = SharedSourceFiles.nativeDirectory(compile);
        var rows = new ArrayList<Row>();
        require(retainedRefs.equals(NativeBridgeBuild.inventory(retained)),
                "Capture must consume the actual complete retained file domain");
        for (FileRef ref : retainedRefs) {
            Path path = absolute(Path.of(ref.path()));
            require(path.startsWith(retained) && !path.equals(retained), "Retained reference escapes its source root");
            Witness witness = SharedSourceFiles.observe(path);
            require(witness.source().equals(ref), "Retained SourceCut input changed");
            rows.add(new Row(retained.relativize(path).toString().replace('\\', '/'), witness));
        }
        rows.sort(Comparator.comparing(Row::relativePath));
        Witness sourceActualWitness = SharedSourceFiles.observe(Path.of(sourceActualRef.path()));
        require(sourceActualWitness.source().equals(sourceActualRef), "Source Actual manifest changed while binding");
        Binding binding = new Binding(SCHEMA, machineId, producerRef, runtime, sourceActualRef, sourceActualWitness,
                retained, retainedIdentity, compile, compileIdentity, rows);
        verifyRetainedFiles(binding);
        observeCurrentFiles(binding);
        return binding;
    }

    public static NativeCombinedSourceCut.Actual sourceActual(Binding binding) throws IOException {
        var source = NativeCombinedSourceCut.readAcceptedSource(binding.retainedSourceActualRef());
        assertRetainedUnchanged(binding.retainedSourceActualWitness());
        require("FROZEN_SOURCE_ONLY_NOT_ENV_BUILD_REGISTER_NATIVE_TEST_OR_GAME".equals(source.qualification())
                && source.machineId().equals(binding.machineId())
                && Path.of(source.nativeSourceRoot()).equals(binding.retainedSourceRoot())
                && source.completeNativeSources().equals(retainedSources(binding)),
                "Binding is not the complete retained SourceCut native domain");
        return source;
    }

    /** Pure mapping; callers must enter through readHistorical or create before using this contract. */
    public static List<FileRef> retainedSources(Binding binding) {
        return binding.rows().stream().map(row -> row.retainedWitness().source())
                .sorted(Comparator.comparing(FileRef::path)).toList();
    }

    /** Exact logical compile refs. Historical readers must not verify these mutable paths. */
    public static List<FileRef> compileSources(Binding binding) {
        return binding.rows().stream().map(row -> compileRef(binding, row))
                .sorted(Comparator.comparing(FileRef::path)).toList();
    }

    /** Resolve original graph/dependency spelling without opening a mutable development file. */
    public static FileRef retainedFor(Binding binding, FileRef originalCompileRef) throws IOException {
        Path original = absolute(Path.of(originalCompileRef.path()));
        require(original.startsWith(binding.compileSourceRoot()) && !original.equals(binding.compileSourceRoot()),
                "Original compile reference escapes its actual compile root");
        String relative = binding.compileSourceRoot().relativize(original).toString().replace('\\', '/');
        for (Row row : binding.rows()) {
            if (row.relativePath().equals(relative)) {
                require(compileRef(binding, row).equals(originalCompileRef),
                        "Original compile reference content differs from retained source");
                return row.retainedWitness().source();
            }
        }
        throw new IOException("Original compile reference is absent from the complete binding");
    }

    /** Fresh stage-only check; the original writer must hold its own lock throughout the live stage. */
    public static List<Witness> observeLive(Binding binding) throws IOException {
        verifyHistorical(binding);
        return observeCurrentFiles(binding);
    }

    /** Fresh original identities, content and full set at stage end; returns the actual recorded after image. */
    public static List<Witness> assertLiveUnchanged(Binding binding, List<Witness> before) throws IOException {
        require(before != null && before.stream().map(Witness::source).toList().equals(compileSources(binding)),
                "Complete original compile preimage required");
        return requireSameObservation(binding, before, observeLive(binding));
    }

    private static void verifyHistorical(Binding binding) throws IOException {
        var producer = ControlBuild.verifiedCompletedReceipt(binding.producerToolsBuildRef());
        require(producer.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && producer.machineId().equals(binding.machineId())
                && producer.completeDeployment().equals(binding.completeToolsRuntime()),
                "Historical binding producer runtime differs");
        for (FileRef ref : binding.completeToolsRuntime()) ref.verify();
        sourceActual(binding);
        verifyRetainedFiles(binding);
    }

    /** Mechanical checks are separately tested with real files; they grant no SourceCut qualification. */
    static void verifyRetainedFiles(Binding binding) throws IOException {
        assertRetainedUnchanged(binding.retainedSourceActualWitness());
        plainRoot(binding.retainedSourceRoot());
        require(SharedSourceFiles.nativeDirectory(binding.retainedSourceRoot()).equals(binding.retainedRootIdentity()),
                "Original retained source root identity changed");
        require(NativeBridgeBuild.inventory(binding.retainedSourceRoot()).equals(retainedSources(binding)),
                "Complete retained source set/content changed");
        for (Row row : binding.rows()) assertRetainedUnchanged(row.retainedWitness());
        require(SharedSourceFiles.nativeDirectory(binding.retainedSourceRoot()).equals(binding.retainedRootIdentity()),
                "Retained source root changed during observation");
    }

    private static void assertRetainedUnchanged(Witness original) throws IOException {
        require(original.equals(SharedSourceFiles.observe(Path.of(original.source().path()))),
                "Original retained source content, native identity or link metadata changed");
    }

    /** No historical receipt is fabricated here: this is the same mechanical live guard used after acceptance. */
    static List<Witness> observeCurrentFiles(Binding binding) throws IOException {
        plainRoot(binding.compileSourceRoot());
        require(SharedSourceFiles.nativeDirectory(binding.compileSourceRoot()).equals(binding.compileRootIdentity()),
                "Original compile source root identity changed");
        List<FileRef> expected = compileSources(binding);
        require(NativeBridgeBuild.inventory(binding.compileSourceRoot()).equals(expected),
                "Complete relative path/bytes/SHA compile-to-retained bijection differs");
        Set<String> retainedIdentities = new HashSet<>();
        for (Row row : binding.rows()) retainedIdentities.add(row.retainedWitness().nativeFile().identityKey());
        var current = new ArrayList<Witness>();
        for (FileRef ref : expected) {
            Witness witness = SharedSourceFiles.observe(Path.of(ref.path()));
            require(witness.source().equals(ref), "Compile file changed during native identity observation");
            require(!retainedIdentities.contains(witness.nativeFile().identityKey()),
                    "Mutable compile file aliases an immutable retained source");
            current.add(witness);
        }
        require(NativeBridgeBuild.inventory(binding.compileSourceRoot()).equals(expected),
                "Compile source set/content changed while observing its native identities");
        for (Witness witness : current) SharedSourceFiles.assertUnchanged(witness);
        require(SharedSourceFiles.nativeDirectory(binding.compileSourceRoot()).equals(binding.compileRootIdentity()),
                "Compile source root changed during observation");
        return List.copyOf(current);
    }

    static List<Witness> requireSameObservation(Binding binding, List<Witness> before,
            List<Witness> after) throws IOException {
        require(before != null && after != null
                && before.stream().map(Witness::source).toList().equals(compileSources(binding))
                && after.stream().map(Witness::source).toList().equals(compileSources(binding))
                && before.equals(after), "Actual complete original compile witnesses differ");
        return List.copyOf(after);
    }

    private static FileRef compileRef(Binding binding, Row row) {
        FileRef retained = row.retainedWitness().source();
        return new FileRef(binding.compileSourceRoot().resolve(row.relativePath()).toString(),
                retained.bytes(), retained.sha256());
    }
    private static void plainRoot(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path),
                "Ordinary exact source root required");
    }
    private static Path absolute(Path path) {
        if (path == null || !path.isAbsolute() || !path.normalize().equals(path))
            throw new IllegalArgumentException("Normalized absolute source root required");
        return path;
    }
    private static void relative(String value) {
        if (value == null || value.isBlank() || value.startsWith("/") || value.indexOf('\\') >= 0
                || value.indexOf(':') >= 0 || value.indexOf('\0') >= 0
                || java.util.Arrays.stream(value.split("/", -1)).anyMatch(
                        part -> part.isBlank() || part.equals(".") || part.equals("..")))
            throw new IllegalArgumentException("Plain complete relative source path required");
    }
    private static void require(boolean value, String message) throws IOException {
        if (!value) throw new IOException(message);
    }
}
