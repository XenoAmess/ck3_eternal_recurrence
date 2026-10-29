package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Real Windows file/identity guards, not fabricated qualified SourceCut or process terminals. */
final class CompileSourceBindingTest {
    @TempDir Path directory;

    private CompileSourceBinding.Binding binding() throws IOException {
        Path retained = Files.createDirectory(directory.resolve("retained"));
        Path compile = Files.createDirectory(directory.resolve("compile"));
        Files.createDirectory(retained.resolve("src")); Files.createDirectory(compile.resolve("src"));
        for (String name : List.of("CMakeLists.txt", "src/one.cpp")) {
            Files.writeString(retained.resolve(name), "source " + name + "\n");
            Files.copy(retained.resolve(name), compile.resolve(name));
        }
        return mechanicalBinding(retained, compile);
    }

    private CompileSourceBinding.Binding mechanicalBinding(Path retained, Path compile) throws IOException {
        Path metadata = directory.resolve("unqualified-metadata.json");
        if (!Files.exists(metadata)) Files.writeString(metadata, "{}");
        FileRef unqualified = FileRef.measure(metadata);
        return CompileSourceBinding.captureFiles(unqualified, List.of(unqualified), "software-machine",
                unqualified, retained, NativeBridgeBuild.inventory(retained), compile);
    }

    /** Software-only request DATA; no historical binding or native stage is admitted by this fixture. */
    private NativeBridgeBuild.Request dependencyRequest(CompileSourceBinding.Binding binding, List<FileRef> sources) throws IOException {
        Path tools = directory.resolve("tools"); Files.createDirectories(tools);
        var pins = new java.util.ArrayList<FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe")) {
            Path tool = tools.resolve(name); if (!Files.exists(tool)) Files.writeString(tool, "software fixture only");
            pins.add(FileRef.measure(tool));
        }
        var toolchain = new NativeBridgeBuild.Toolchain(pins.get(0), pins.get(1), pins.get(2), pins.get(3), pins.get(4), pins.get(5), pins.get(6));
        return new NativeBridgeBuild.Request(NativeBridgeBuild.BOUND_REQUEST_SCHEMA, binding.machineId(), NativeBridgeBuild.Stage.ENV,
                directory, binding.compileSourceRoot(), sources, directory.resolve("build"), directory.resolve("scratch"),
                binding.producerToolsBuildRef(), toolchain, List.of(), 1, null, null, null, binding.retainedSourceActualRef());
    }
    private FileRef dependencies(String text) throws IOException {
        Path raw = directory.resolve("dependencies.txt"); Files.writeString(raw, text); return FileRef.measure(raw);
    }

    @Test void bulkDependenciesReuseOnlyTheirBoundRetainedReferencesAfterDevelopmentMoves() throws Exception {
        var binding = binding(); var sources = CompileSourceBinding.compileSources(binding);
        var request = dependencyRequest(binding, sources); var text = new StringBuilder("ignored non-dependency row\n");
        for (int index = 0; index < 1024; index++)
            for (FileRef source : sources)
                text.append("    ").append(request.buildRoot().relativize(Path.of(source.path()))).append('\n');
        FileRef raw = dependencies(text.toString());
        Files.move(binding.compileSourceRoot(), directory.resolve("later-development"));
        var expected = new java.util.ArrayList<FileRef>();
        for (FileRef source : sources) expected.add(CompileSourceBinding.retainedFor(binding, source));
        expected.sort(java.util.Comparator.comparing(FileRef::path));
        assertEquals(expected, NativeBridgeBuild.readDependencies(raw, request, binding));
        CompileSourceBinding.verifyRetainedFiles(binding);
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
    }

    @Test void bulkDependenciesStillRejectMissingBoundPathsAndChangedOriginalContent() throws Exception {
        var binding = binding(); var sources = CompileSourceBinding.compileSources(binding);
        var request = dependencyRequest(binding, sources);
        FileRef missing = dependencies("    " + binding.compileSourceRoot().resolve("unlisted.cpp") + "\n");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readDependencies(missing, request, binding));
        FileRef one = sources.getFirst();
        var changed = new java.util.ArrayList<>(sources);
        changed.set(0, new FileRef(one.path(), one.bytes() + 1, one.sha256()));
        var forged = dependencyRequest(binding, changed);
        FileRef actual = dependencies("    " + one.path() + "\n    " + one.path() + "\n");
        IOException mismatch = assertThrows(IOException.class, () -> NativeBridgeBuild.readDependencies(actual, forged, binding));
        assertEquals("Original compile reference content differs from retained source", mismatch.getMessage());
        assertThrows(IOException.class, () -> NativeBridgeBuild.readDependencies(actual, request, null));
    }

    @Test void externalDependenciesAreMeasuredAgainAndCannotBorrowTheBoundLookup() throws Exception {
        var binding = binding(); var request = dependencyRequest(binding, CompileSourceBinding.compileSources(binding));
        Path external = directory.resolve("external.hpp"); Files.writeString(external, "first external content");
        FileRef raw = dependencies("    " + external + "\n    " + external + "\n");
        FileRef first = FileRef.measure(external);
        assertEquals(List.of(first), NativeBridgeBuild.readDependencies(raw, request, binding));
        Files.writeString(external, "changed external content");
        FileRef changed = FileRef.measure(external); assertNotEquals(first, changed);
        assertEquals(List.of(changed), NativeBridgeBuild.readDependencies(raw, request, binding));
        Files.delete(external); Files.createDirectory(external);
        assertThrows(IOException.class, () -> NativeBridgeBuild.readDependencies(raw, request, binding));
    }

    @Test void witnessAndCompleteSourceClosuresKeepTheirExactRetainedMappingAndMultiplicity() throws Exception {
        var binding = binding(); var sources = CompileSourceBinding.compileSources(binding);
        var request = dependencyRequest(binding, sources);
        List<Path> witnesses = CompileSourceBinding.observeCurrentFiles(binding).stream()
                .map(witness -> Path.of(witness.source().path())).toList();
        var paths = new java.util.ArrayList<Path>();
        for (int index = 0; index < 1024; index++) paths.addAll(witnesses);
        Files.move(binding.compileSourceRoot(), directory.resolve("later-development"));
        var expected = new java.util.ArrayList<FileRef>();
        for (Path path : witnesses)
            expected.add(CompileSourceBinding.retainedFor(binding, sources.stream().filter(row -> Path.of(row.path()).equals(path)).findFirst().orElseThrow()));
        List<FileRef> complete = NativeBridgeBuild.sourceReferences(request, binding, sources.stream().map(row -> Path.of(row.path())).toList());
        assertEquals(sources.size(), complete.size());
        List<FileRef> actual = NativeBridgeBuild.sourceReferences(request, binding, paths);
        assertEquals(paths.size(), actual.size());
        for (int index = 0; index < actual.size(); index++) assertEquals(expected.get(index % expected.size()), actual.get(index));
        assertEquals(complete.stream().sorted(java.util.Comparator.comparing(FileRef::path)).toList(),
                expected.stream().sorted(java.util.Comparator.comparing(FileRef::path)).toList());
        assertThrows(IOException.class, () -> NativeBridgeBuild.sourceReferences(request, binding,
                List.of(binding.compileSourceRoot().resolve("unlisted.cpp"))));
    }

    @Test void realFilesHaveOneFullBijectionAndExactRoundTrip() throws Exception {
        var binding = binding();
        List<Witness> before = CompileSourceBinding.observeCurrentFiles(binding);
        List<Witness> after = CompileSourceBinding.observeCurrentFiles(binding);
        assertEquals(2, before.size());
        assertEquals(before, CompileSourceBinding.requireSameObservation(binding, before, after));
        for (Witness witness : before) {
            FileRef retained = CompileSourceBinding.retainedFor(binding, witness.source());
            assertEquals(witness.source().bytes(), retained.bytes());
            assertEquals(witness.source().sha256(), retained.sha256());
            assertTrue(Path.of(retained.path()).startsWith(binding.retainedSourceRoot()));
            assertNotEquals(witness.nativeFile().identityKey(), SharedSourceFiles.observe(Path.of(retained.path())).nativeFile().identityKey());
        }
        var mapper = RootNativePlanJson.mapper();
        assertEquals(binding, mapper.readValue(mapper.writeValueAsBytes(binding), CompileSourceBinding.Binding.class));
    }

    @Test void historicalRetainedGuardDoesNotReopenChangedOrAbsentDevelopmentTree() throws Exception {
        var binding = binding();
        List<Witness> before = CompileSourceBinding.observeCurrentFiles(binding);
        Files.writeString(binding.compileSourceRoot().resolve("src/one.cpp"), "later development");
        CompileSourceBinding.verifyRetainedFiles(binding);
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        Files.move(binding.compileSourceRoot(), directory.resolve("later-development"));
        CompileSourceBinding.verifyRetainedFiles(binding);
        assertEquals(before.getFirst().source().sha256(),
                CompileSourceBinding.retainedFor(binding, before.getFirst().source()).sha256());
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
    }

    @Test void newMissingRenamedOrChangedFilesCannotBorrowTheOldDomain() throws Exception {
        var binding = binding();
        Path extra = binding.compileSourceRoot().resolve("unlisted.cpp");
        Files.writeString(extra, "extra");
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        Files.delete(extra);
        Path source = binding.compileSourceRoot().resolve("src/one.cpp");
        Path renamed = source.resolveSibling("other.cpp");
        Files.move(source, renamed);
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        Files.move(renamed, source);
        Files.writeString(source, "wrong bytes");
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        Files.delete(source);
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
    }

    @Test void sameByteFileReplacementIsRejectedByOriginalNativeIdentity() throws Exception {
        var binding = binding();
        List<Witness> before = CompileSourceBinding.observeCurrentFiles(binding);
        Path source = binding.compileSourceRoot().resolve("src/one.cpp");
        Path replacement = source.resolveSibling("private-replacement.cpp");
        Files.copy(source, replacement);
        Files.move(replacement, source, StandardCopyOption.REPLACE_EXISTING);
        List<Witness> after = CompileSourceBinding.observeCurrentFiles(binding);
        assertEquals(before.stream().map(Witness::source).toList(), after.stream().map(Witness::source).toList());
        assertNotEquals(before, after);
        assertThrows(IOException.class, () -> CompileSourceBinding.requireSameObservation(binding, before, after));
    }

    @Test void identicalRecreatedCompileDirectoryCannotBorrowTheOriginalRootIdentity() throws Exception {
        var binding = binding();
        Path old = directory.resolve("old-compile");
        Files.move(binding.compileSourceRoot(), old);
        Files.createDirectory(binding.compileSourceRoot());
        Files.createDirectory(binding.compileSourceRoot().resolve("src"));
        for (String name : List.of("CMakeLists.txt", "src/one.cpp"))
            Files.copy(old.resolve(name), binding.compileSourceRoot().resolve(name));
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        CompileSourceBinding.verifyRetainedFiles(binding);
    }

    @Test void hardlinkFromMutableToRetainedIsRejectedEvenWhenAllBytesMatch() throws Exception {
        var binding = binding();
        Path source = binding.compileSourceRoot().resolve("src/one.cpp");
        Files.delete(source);
        Files.createLink(source, binding.retainedSourceRoot().resolve("src/one.cpp"));
        assertThrows(IOException.class, () -> CompileSourceBinding.observeCurrentFiles(binding));
        assertThrows(IOException.class, () -> CompileSourceBinding.verifyRetainedFiles(binding));
    }

    @Test void retainedMutationAndForgedQualificationStillFail() throws Exception {
        var binding = binding();
        var mapper = RootNativePlanJson.mapper();
        Path artifact = directory.resolve("binding.json");
        Files.write(artifact, mapper.writeValueAsBytes(binding));
        assertThrows(IOException.class, () -> CompileSourceBinding.readHistorical(FileRef.measure(artifact)));
        Files.writeString(binding.retainedSourceRoot().resolve("src/one.cpp"), "tampered retained source");
        assertThrows(IOException.class, () -> CompileSourceBinding.verifyRetainedFiles(binding));
    }

    @Test void incompleteOrForgedRelativeContentAndWrongJsonTypesAreRejected() throws Exception {
        var binding = binding();
        for (String invalid : List.of("", ".", "..", "../src", "src//one.cpp", "src/../one.cpp", "src\\one.cpp", "/src", "C:/src"))
            assertThrows(IllegalArgumentException.class, () -> new CompileSourceBinding.Row(invalid, binding.rows().getFirst().retainedWitness()));
        FileRef one = CompileSourceBinding.compileSources(binding).getFirst();
        assertThrows(IOException.class, () -> CompileSourceBinding.retainedFor(binding,
                new FileRef(one.path(), one.bytes() + 1, one.sha256())));
        assertThrows(IOException.class, () -> CompileSourceBinding.retainedFor(binding,
                new FileRef(directory.resolve("outside.cpp").toString(), one.bytes(), one.sha256())));
        assertThrows(IOException.class, () -> CompileSourceBinding.requireSameObservation(binding, List.of(), List.of()));
        var mapper = RootNativePlanJson.mapper();
        for (String field : List.of("retained_source_actual_ref", "rows", "compile_root_identity")) {
            var tree = mapper.valueToTree(binding);
            ((com.fasterxml.jackson.databind.node.ObjectNode) tree).remove(field);
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(tree), CompileSourceBinding.Binding.class));
        }
        for (String invalid : List.of("true", "1.0", "\"1\"")) {
            var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(binding);
            ((com.fasterxml.jackson.databind.node.ObjectNode) tree.withArray("rows").get(0).get("retained_witness").get("source"))
                    .set("bytes", mapper.readTree(invalid));
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(tree), CompileSourceBinding.Binding.class));
        }
    }
    @Test void duplicateCaseCollisionAndEmptyDomainsAreRejected() throws Exception {
        var b = binding();
        var row = b.rows().getFirst();
        var caseAlias = new CompileSourceBinding.Row(row.relativePath().toUpperCase(java.util.Locale.ROOT), row.retainedWitness());
        for (var rows : List.of(List.<CompileSourceBinding.Row>of(), List.of(row, row), List.of(row, caseAlias)))
            assertThrows(IllegalArgumentException.class, () -> new CompileSourceBinding.Binding(
                    b.schema(), b.machineId(), b.producerToolsBuildRef(), b.completeToolsRuntime(),
                    b.retainedSourceActualRef(), b.retainedSourceActualWitness(), b.retainedSourceRoot(),
                    b.retainedRootIdentity(), b.compileSourceRoot(), b.compileRootIdentity(), rows));
    }

    @Test void hardlinkToSourceActualManifestIsRejectedByRetainedMetadata() throws Exception {
        var binding = binding();
        Witness before = binding.retainedSourceActualWitness();
        Path original = Path.of(before.source().path());
        Files.createLink(directory.resolve("source-actual-hardlink.json"), original);
        Witness after = SharedSourceFiles.observe(original);
        assertEquals(before.source(), after.source());
        assertEquals(before.nativeFile().identityKey(), after.nativeFile().identityKey());
        assertEquals(Math.addExact(before.nativeFile().linkCount(), 1), after.nativeFile().linkCount());
        assertThrows(IOException.class, () -> CompileSourceBinding.verifyRetainedFiles(binding));
    }

    @Test void sameByteSourceActualManifestReplacementStillChangesItsOriginalFileId() throws Exception {
        var b = binding();
        Path original = Path.of(b.retainedSourceActualRef().path()), replacement = directory.resolve("replacement.json");
        Files.copy(original, replacement);
        Files.move(replacement, original, StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class, () -> CompileSourceBinding.verifyRetainedFiles(b));
    }

}
