package org.xar.ck3.control.build;

import java.io.IOException;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** The same software regressions can run before Maven, then run again in ordinary persistent CI. */
final class BootstrapArchiveTest {
    @TempDir Path temporary;
    private static final String OWNER = "/root/tools_c15";
    private static final String SOURCE = "package org.example; public final class SourceMain {"
            + " private SourceMain() {} public record Nested(String value) {} }";
    record Selection(String schema, String machineId, String owner, List<BootstrapArchive.Selected> selectedFiles) { }
    record Fixture(Path directory, Path source, Path resource, BootstrapArchive.Request request, ControlBuild.FileRef requestRef) { }
    record RegressionActual(String schema, String machineId, String observedAtUtc, int tests,
            String scope, String Maven, String nativeOperations, String game) { }
    record DerivedCopyRetirement(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef retainedActualRef, List<SharedSourceFiles.Witness> removedCopies,
            String reason, String physicalReleaseCredit) { }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Fresh software regression directory required");
        Path root = Path.of(args[0]);
        if (!root.isAbsolute() || !Files.isDirectory(root.getParent())) throw new IOException("Existing parent and absolute fresh test root required");
        Files.createDirectory(root);
        var test = new BootstrapArchiveTest(); test.temporary = root;
        test.completeSourcesCompileToClosedArchiveWithIndependentLibraryCopies();
        retireSuccessfulSoftwareCopies(root.resolve("complete/output"));
        test.realEntrypointRoundTripAndExistingOutputNeverOverwrites();
        retireSuccessfulSoftwareCopies(root.resolve("entry/output"));
        test.compilerFailureAndClassLimitCannotCreateAnyOutputRoot();
        test.peakAndIncompleteGuardRejectBeforeCreatingAnOutput();
        test.originalRequestAndActualSourceBodyCannotBeSubstituted();
        test.compilerLibraryCustodyRejectsActualWriteAndRenameUntilClosed();
        test.existingParentCustodyRejectsActualRenameAndReleasesOnlyItsHandles();
        byte[] actual = ControlBuild.strictMapper().writeValueAsBytes(new RegressionActual(
                "xar.java-bootstrap-software-regression/v1", WindowsJobProcess.currentMachineId(),
                Instant.now().toString(), 7, "SOURCE_BOOTSTRAP_SOFTWARE_ONLY", "NOT_RUN", "NOT_RUN", "NOT_RUN"));
        Files.write(root.resolve("actual.json"), actual, StandardOpenOption.CREATE_NEW);
        System.out.println("BOOTSTRAP_SOFTWARE_REGRESSIONS 7 PASS; Maven/Native/Game NOT_RUN");
    }
    @Test void completeSourcesCompileToClosedArchiveWithIndependentLibraryCopies() throws Exception {
        Fixture fixture = fixture("complete", SOURCE, 64, 12L << 20, false);
        BootstrapArchive.Actual actual = BootstrapArchive.create(fixture.request(), fixture.requestRef());
        check(actual.status() == BootstrapArchive.Status.STRICT_COMPILE_AND_ARCHIVE_READBACK_SOURCE_BOOTSTRAP_ONLY,
                "Only source bootstrap scope is valid");
        check(actual.mainSources() == 1 && actual.completeBootstrapRuntime().size() == 6, "Complete runtime required");
        List<String> names = actual.completeArchiveEntries().stream().map(BootstrapArchive.ArchiveEntry::path).toList();
        check(names.equals(List.of("META-INF/MANIFEST.MF", "fixture/data.txt", "org/example/SourceMain$Nested.class",
                "org/example/SourceMain.class")), "Exact closed class/resource inventory");
        check(actual.compilerOptions().containsAll(List.of("--release", "21", "-Xlint:all", "-Werror", "-proc:none", "-implicit:none")),
                "Strict actual compiler options");
        for (ControlBuild.FileRef original : fixture.request().compileLibraries()) {
            Path copied = Path.of(fixture.request().outputRoot()).resolve("lib").resolve(Path.of(original.path()).getFileName());
            var source = SharedSourceFiles.observe(Path.of(original.path())); var target = SharedSourceFiles.observe(copied);
            check(source.source().bytes() == target.source().bytes() && source.source().sha256().equals(target.source().sha256()),
                    "Original and copied library bytes differ");
            check(!source.nativeFile().identityKey().equals(target.nativeFile().identityKey()), "Copy must have independent actual file identity");
            check(source.nativeFile().linkCount() == 1 && target.nativeFile().linkCount() == 1, "No hardlink mutation");
        }
        Path jar = Path.of(fixture.request().outputRoot()).resolve("ck3-control-bootstrap-tools.jar");
        try (JarFile archive = new JarFile(jar.toFile())) {
            check(new String(archive.getInputStream(archive.getJarEntry("fixture/data.txt")).readAllBytes(), StandardCharsets.UTF_8)
                    .equals("exact-bootstrap-resource"), "Resource body differs");
        }
        try (var loader = new URLClassLoader(new java.net.URL[] { jar.toUri().toURL() }, ClassLoader.getPlatformClassLoader())) {
            Class<?> type = Class.forName("org.example.SourceMain", false, loader);
            check(type.getProtectionDomain().getCodeSource().getLocation().equals(jar.toUri().toURL()), "Archive class has another origin");
        }
        for (var witness : actual.createdRuntimeWitnesses()) SharedSourceFiles.assertUnchanged(witness);
        check(Files.isRegularFile(Path.of(fixture.request().outputRoot()).resolve("input-guard.actual.json")), "Closed source guard missing");
    }
    @Test void realEntrypointRoundTripAndExistingOutputNeverOverwrites() throws Exception {
        Fixture fixture = fixture("entry", SOURCE, 64, 12L << 20, false);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(fixture.request());
        check(ControlBuild.strictMapper().readValue(encoded, BootstrapArchive.Request.class).equals(fixture.request()),
                "Typed request serialization roundtrip differs");
        BootstrapArchive.main(new String[] { fixture.requestRef().path(), Long.toString(fixture.requestRef().bytes()), fixture.requestRef().sha256() });
        Path actualPath = Path.of(fixture.request().outputRoot()).resolve("actual.json");
        var before = SharedSourceFiles.observe(actualPath);
        rejects(() -> BootstrapArchive.main(new String[] { fixture.requestRef().path(), Long.toString(fixture.requestRef().bytes()), fixture.requestRef().sha256() }));
        SharedSourceFiles.assertUnchanged(before);
    }
    @Test void compilerFailureAndClassLimitCannotCreateAnyOutputRoot() throws Exception {
        Fixture invalid = fixture("invalid-java", "package org.example; public final class SourceMain { broken syntax }", 64, 12L << 20, false);
        rejects(() -> BootstrapArchive.create(invalid.request(), invalid.requestRef()));
        check(!Files.exists(Path.of(invalid.request().outputRoot())), "Invalid compilation created an output root");
        Fixture limited = fixture("class-limit", SOURCE, 1, 12L << 20, false);
        rejects(() -> BootstrapArchive.create(limited.request(), limited.requestRef()));
        check(!Files.exists(Path.of(limited.request().outputRoot())), "Class overflow created an output root");
    }
    @Test void peakAndIncompleteGuardRejectBeforeCreatingAnOutput() throws Exception {
        Fixture small = fixture("small-peak", SOURCE, 64, BootstrapArchive.METADATA_RESERVE_BYTES, false);
        rejects(() -> BootstrapArchive.create(small.request(), small.requestRef()));
        check(!Files.exists(Path.of(small.request().outputRoot())), "Precharged root cap overflow created output");
        Fixture incomplete = fixture("incomplete-manifest", SOURCE, 64, 12L << 20, true);
        rejects(() -> BootstrapArchive.create(incomplete.request(), incomplete.requestRef()));
        check(!Files.exists(Path.of(incomplete.request().outputRoot())), "Incomplete original source closure created output");
    }
    @Test void originalRequestAndActualSourceBodyCannotBeSubstituted() throws Exception {
        Fixture source = fixture("changed-source", SOURCE, 64, 12L << 20, false);
        Files.writeString(source.source(), SOURCE + " ", StandardOpenOption.TRUNCATE_EXISTING);
        rejects(() -> BootstrapArchive.create(source.request(), source.requestRef()));
        check(!Files.exists(Path.of(source.request().outputRoot())), "Changed source created output");
        Fixture original = fixture("changed-request", SOURCE, 64, 12L << 20, false);
        rejects(() -> BootstrapArchive.exact(ControlBuild.FileRef.measure(original.source()), (long) Integer.MAX_VALUE + 1));
        var request = original.request();
        var changed = new BootstrapArchive.Request(request.schema(), request.machineId(), request.taskOwner(), request.reviewAtUtc(),
                request.completeSelectionRef(), request.inputManifestRef(), request.compileLibraries(),
                original.directory().resolve("different-output").toString(), request.expectedMainSources(),
                request.maximumSourceBytes(), request.maximumClasses(), request.maximumClassBytes(),
                request.maximumArchiveBytes(), request.maximumNewRootBytes());
        rejects(() -> BootstrapArchive.create(changed, original.requestRef()));
        check(!Files.exists(Path.of(changed.outputRoot())), "Unbound typed request created output");
    }
    @Test void compilerLibraryCustodyRejectsActualWriteAndRenameUntilClosed() throws Exception {
        Path source = temporary.resolve("held-library-marker.jar");
        Files.writeString(source, "synthetic custody DATA marker; never executed", StandardOpenOption.CREATE_NEW);
        var original = SharedSourceFiles.observe(source);
        try (var custody = new BootstrapArchive.Libraries()) {
            custody.retain(source);
            rejects(() -> { try (var writer = java.nio.channels.FileChannel.open(source, StandardOpenOption.WRITE)) {
                throw new AssertionError("Held compiler source allowed a new write handle: " + writer.isOpen());
            } });
            rejects(() -> Files.move(source, source.resolveSibling("renamed-held-marker.jar")));
            custody.requireCurrent(); SharedSourceFiles.assertUnchanged(original);
        }
        try (var writer = java.nio.channels.FileChannel.open(source, StandardOpenOption.WRITE)) {
            check(writer.isOpen(), "Custody close did not release its own read handle");
        }
        SharedSourceFiles.assertUnchanged(original);
    }
    @Test void existingParentCustodyRejectsActualRenameAndReleasesOnlyItsHandles() throws Exception {
        Path parent = temporary.resolve("held-parent-marker"); Files.createDirectory(parent);
        var original = SharedSourceFiles.nativeDirectory(parent);
        Path moved = temporary.resolve("moved-parent-marker");
        try (var custody = new BootstrapArchive.Directories()) {
            custody.retainAncestors(parent);
            var deletion = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(
                    SharedSourceFiles.nativePath(parent), 0x10000, 7, null, 3, 0x02200000, null);
            if (!com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(deletion)) {
                com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(deletion);
                throw new AssertionError("Directory read custody allowed a DELETE-access handle");
            }
            check(com.sun.jna.Native.getLastError() == 32, "Expected actual sharing violation for directory DELETE access");
            rejects(() -> Files.move(parent, moved));
            custody.requireCurrent();
            check(SharedSourceFiles.nativeDirectory(parent).equals(original), "Original parent identity changed");
        }
        Files.move(parent, moved); check(SharedSourceFiles.nativeDirectory(moved).equals(original), "Parent custody did not release cleanly");
        Files.move(moved, parent);
    }
    private Fixture fixture(String name, String body, int classes, long peak, boolean omitResource) throws Exception {
        Path root = temporary.resolve(name); Files.createDirectory(root);
        Path source = root.resolve("SourceMain.java"); Files.writeString(source, body, StandardOpenOption.CREATE_NEW);
        Path resource = root.resolve("data.txt"); Files.writeString(resource, "exact-bootstrap-resource", StandardOpenOption.CREATE_NEW);
        List<ControlBuild.FileRef> libraries = new ArrayList<>();
        for (Class<?> type : List.of(com.fasterxml.jackson.annotation.JsonAlias.class, com.fasterxml.jackson.core.JsonParser.class,
                com.fasterxml.jackson.databind.JsonNode.class, com.sun.jna.Native.class, com.sun.jna.platform.win32.Kernel32.class)) {
            libraries.add(ControlBuild.FileRef.measure(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI())));
        }
        List<BootstrapArchive.Selected> rows = List.of(
                new BootstrapArchive.Selected(BootstrapArchive.Group.TOOLS, "build-tools/src/main/java/org/example/SourceMain.java", ControlBuild.FileRef.measure(source)),
                new BootstrapArchive.Selected(BootstrapArchive.Group.TOOLS, "build-tools/src/main/resources/fixture/data.txt", ControlBuild.FileRef.measure(resource)));
        String machine = WindowsJobProcess.currentMachineId();
        Path selected = root.resolve("selected.json");
        Files.write(selected, ControlBuild.strictMapper().writeValueAsBytes(new Selection("xar.java-source-effective-selection/v1", machine, OWNER, rows)),
                StandardOpenOption.CREATE_NEW);
        List<ControlBuild.FileRef> inputs = new ArrayList<>(); inputs.add(ControlBuild.FileRef.measure(selected));
        inputs.add(ControlBuild.FileRef.measure(source)); if (!omitResource) inputs.add(ControlBuild.FileRef.measure(resource)); inputs.addAll(libraries);
        Path manifest = root.resolve("input-manifest.json"); Instant now = Instant.now(), review = now.plusSeconds(600);
        Files.write(manifest, ControlBuild.strictMapper().writeValueAsBytes(new BoundedSourceInputGuard.Manifest(
                BoundedSourceInputGuard.SCHEMA, machine, OWNER, now.toString(), review.toString(), inputs)), StandardOpenOption.CREATE_NEW);
        var request = new BootstrapArchive.Request(BootstrapArchive.REQUEST_SCHEMA, machine, OWNER, review.toString(),
                ControlBuild.FileRef.measure(selected), ControlBuild.FileRef.measure(manifest), libraries,
                root.resolve("output").toString(), 1, 1 << 20, classes, 1 << 20, 1 << 20, peak);
        Path requestFile = root.resolve("request.json");
        Files.write(requestFile, ControlBuild.strictMapper().writeValueAsBytes(request), StandardOpenOption.CREATE_NEW);
        return new Fixture(root, source, resource, request, ControlBuild.FileRef.measure(requestFile));
    }
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    private static void retireSuccessfulSoftwareCopies(Path root) throws Exception {
        var actualRef = ControlBuild.FileRef.measure(root.resolve("actual.json"));
        var actual = ControlBuild.strictMapper().readValue(BootstrapArchive.exact(actualRef, 1 << 20), BootstrapArchive.Actual.class);
        if (actual.status() != BootstrapArchive.Status.STRICT_COMPILE_AND_ARCHIVE_READBACK_SOURCE_BOOTSTRAP_ONLY)
            throw new IOException("Only completed software-only derived copies may be reclaimed");
        for (var witness : actual.createdRuntimeWitnesses()) {
            Path path = Path.of(witness.source().path());
            if (!path.normalize().startsWith(root.normalize()) || !path.equals(root.resolve("ck3-control-bootstrap-tools.jar"))
                    && !path.getParent().equals(root.resolve("lib"))) throw new IOException("Derived copy left its exact test root");
            SharedSourceFiles.assertUnchanged(witness);
        }
        for (var witness : actual.createdRuntimeWitnesses()) Files.delete(Path.of(witness.source().path()));
        Files.delete(root.resolve("lib"));
        byte[] receipt = ControlBuild.strictMapper().writeValueAsBytes(new DerivedCopyRetirement(
                "xar.bootstrap-software-derived-copies-retired/v1", actual.machineId(), Instant.now().toString(),
                actualRef, actual.createdRuntimeWitnesses(),
                "Successful software-only copies superseded by retained exact actual/source/class-entry witnesses; reproducible from retained original inputs",
                "NONE_CLAIMED"));
        Files.write(root.resolve("retention.actual.json"), receipt, StandardOpenOption.CREATE_NEW);
        actualRef.verify();
    }
    @FunctionalInterface private interface Checked { void run() throws Exception; }
    private static void rejects(Checked action) throws Exception {
        try { action.run(); }
        catch (IOException | IllegalArgumentException expected) { return; }
        throw new AssertionError("Actual producer did not reject the invalid input");
    }
}
