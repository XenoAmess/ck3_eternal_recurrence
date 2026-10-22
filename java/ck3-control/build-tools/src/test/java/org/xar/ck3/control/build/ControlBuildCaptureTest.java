package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real javac class origins plus deliberately synthetic compiler-list fixtures; no Maven success is invented. */
class ControlBuildCaptureTest {
    @TempDir Path temporary;
    private record Fixture(Path snapshot, Path module, Path build, Path output, Path inputList,
            Path createdList, Path source, List<ControlBuild.FileRef> sources) { }

    @Test void captureArgumentsCompileTestsPackageAndNeverRunVerify() {
        Path root = temporary.toAbsolutePath();
        var config = new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "capture-fixture", "/root/build", null, Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        List<String> arguments = ControlBuild.reactorCaptureArguments(config, root.resolve("settings.xml"), root.resolve("snapshot"), root.resolve("build"));
        assertEquals("package", arguments.getLast()); assertTrue(arguments.contains("-DskipTests=true"));
        assertTrue(arguments.contains("-Dmaven.test.skip=false")); assertFalse(arguments.contains("verify"));
        assertFalse(arguments.stream().anyMatch(arg -> arg.equals("-Dmaven.test.skip=true")));
        assertEquals("verify", ControlBuild.reactorVerifyArguments(config, root.resolve("settings.xml"), root.resolve("snapshot"), root.resolve("build")).getLast());
    }

    @Test void explicitMavenOverrideIsRefusedBeforeCaptureStartsAnyProcess() {
        Path root = temporary.toAbsolutePath();
        var config = new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "capture-fixture", "/root/build", root.resolve("mvn.cmd"), Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        assertThrows(IOException.class, () -> ControlBuild.buildCapture(config));
        assertFalse(Files.exists(root.resolve("work")));
    }

    @Test void actualOuterAndInnerClassSourceFilesBindToOneExactModuleTestSource() throws Exception {
        Fixture f = fixture(); var manifest = collect(f, f.sources());
        assertEquals(ControlBuild.CaptureTestState.NOT_RUN, manifest.tests()); assertEquals(1, manifest.modules().size());
        assertEquals(1, manifest.notRunTests().size()); assertEquals(2, manifest.notRunTests().getFirst().compiledClassRefs().size());
        assertEquals(ControlBuild.FileRef.measure(f.source()), manifest.notRunTests().getFirst().sourceRef());
        assertEquals(ControlBuild.CaptureTestState.NOT_RUN, manifest.notRunTests().getFirst().state());
        assertEquals(f.output().toRealPath().toString(), manifest.modules().getFirst().classOutputRoot());
        manifest.modules().getFirst().compilerInputsRef().verify(); manifest.modules().getFirst().compilerCreatedFilesRef().verify();
    }

    @Test void missingCompilerInputAndPinnedSourceWithNoBinaryAreRejected() throws Exception {
        Fixture f = fixture(); Files.writeString(f.inputList(), f.module().resolve("src/test/java/sample/Other.java") + "\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
        Path empty = f.source().resolveSibling("Empty.java"); Files.writeString(empty, "package sample;\n");
        Files.writeString(f.inputList(), f.source() + "\n" + empty + "\n");
        List<ControlBuild.FileRef> sources = new ArrayList<>(f.sources()); sources.add(ControlBuild.FileRef.measure(empty));
        assertThrows(IOException.class, () -> collect(f, sources));
    }

    @Test void compilerCreatedPathOutsideModuleClassRootIsRejected() throws Exception {
        Fixture f = fixture(); Files.writeString(f.createdList(), "../foreign/FixtureTest.class\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void unlistedActualBinaryCannotBeBorrowedFromAnOutputDirectory() throws Exception {
        Fixture f = fixture(); Files.copy(f.output().resolve("sample/FixtureTest.class"), f.output().resolve("sample/Unlisted.class"));
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void duplicatedCompilerInputCannotMaskMissingSourceOrInflateOrigins() throws Exception {
        Fixture f = fixture(); Files.writeString(f.inputList(), f.source() + "\n" + f.source() + "\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void normalAndCaptureReadersRejectEachOthersSchemasAndMissingEvidence() throws Exception {
        Path capture = temporary.resolve("capture.json");
        Files.writeString(capture, "{\"schema\":\"" + ControlBuild.CAPTURE_SCHEMA + "\"}");
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(capture));
        Path normal = temporary.resolve("normal.json");
        Files.writeString(normal, "{\"schema\":\"" + ControlBuild.SCHEMA + "\"}");
        assertThrows(IOException.class, () -> ControlBuild.acceptedCaptureReceipt(normal));
    }

    private ControlBuild.TestCompilationManifest collect(Fixture f, List<ControlBuild.FileRef> refs) throws IOException {
        return ControlBuild.collectTestCompilation("synthetic-compiler-fixture", f.snapshot(), f.build(), refs);
    }

    private Fixture fixture() throws Exception {
        Path root = Files.createTempDirectory(temporary, "compiler-fixture-").toAbsolutePath();
        Path snapshot = Files.createDirectories(root.resolve("source")), module = Files.createDirectory(snapshot.resolve("module"));
        Path pom = module.resolve("pom.xml"); Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>fixture</artifactId></project>");
        Path source = module.resolve("src/test/java/sample/FixtureTest.java"); Files.createDirectories(source.getParent());
        Files.writeString(source, "package sample; class FixtureTest { static class Inner {} }\n");
        Path build = root.resolve("build"), output = Files.createDirectories(build.resolve("fixture/test-classes"));
        var compiler = ToolProvider.getSystemJavaCompiler(); if (compiler == null) throw new IllegalStateException("Actual JDK compiler required");
        assertEquals(0, compiler.run(null, null, null, "-g:source", "-d", output.toString(), source.toString()));
        Path status = Files.createDirectories(build.resolve("fixture/maven-status/maven-compiler-plugin/testCompile/default-testCompile"));
        Path inputs = status.resolve("inputFiles.lst"), created = status.resolve("createdFiles.lst");
        Files.writeString(inputs, source + "\n");
        List<String> binaries;
        try (var walk = Files.walk(output)) { binaries = walk.filter(Files::isRegularFile).map(file -> output.relativize(file).toString()).sorted(Comparator.naturalOrder()).toList(); }
        assertEquals(2, binaries.size()); Files.writeString(created, String.join("\n", binaries) + "\n");
        return new Fixture(snapshot, module, build, output, inputs, created, source,
                List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(source)));
    }
}
