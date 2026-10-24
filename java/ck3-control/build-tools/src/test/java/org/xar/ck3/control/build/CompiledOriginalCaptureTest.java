package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CompiledOriginalCaptureTest {
    @TempDir Path temporary;

    @Test void typedOriginalRequestStrictRoundTripPreservesInvocationRoles() throws Exception {
        var request = request("unit-machine"); var mapper = ControlBuild.strictMapper();
        assertEquals(request, CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(request)));
        ObjectNode unknown = mapper.valueToTree(request); unknown.put("class_allowlist", "anything");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(unknown)));
        ObjectNode wrong = mapper.valueToTree(request);
        ((ObjectNode) wrong.path("profile").path("capture_receipt_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(wrong)));
        ObjectNode missing = mapper.valueToTree(request); missing.remove("profile");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(missing)));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void typedArgvRejectsUnboundInputsAndSourceExportCannotBecomeASecondBootstrap() {
        var file = ref(temporary.resolve("input.json"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(
                CompiledOriginalCaptureProfile.ArgumentKind.INPUT_FILE, temporary.resolve("other.json").toString(), file));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(
                CompiledOriginalCaptureProfile.ArgumentKind.LITERAL, file.path(), null));
        var good = request("unit-machine").profile();
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Profile(good.captureReceiptRef(),
                good.testCompilationRef(), good.callerToolsReceiptRef(), good.producerToolsReceiptRef(), good.selection(),
                CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, file, List.of(), List.of(), List.of(), null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Profile(good.captureReceiptRef(),
                good.testCompilationRef(), good.callerToolsReceiptRef(), good.producerToolsReceiptRef(), good.selection(),
                CompiledOriginalCaptureProfile.InvocationKind.MAIN, file, List.of(), List.of(), List.of(), null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureProcess.Environment("JAVA_TOOL_OPTIONS", "-javaagent:x"));
    }

    @Test void actualJavaCompilerInventoryIncludesNestedClassesAndCopiedResources() throws Exception {
        Fixture fixture = fixture(); var inventory = inventory(fixture);
        assertEquals(2, inventory.runtimeClasses().size()); assertEquals(1, inventory.runtimeResources().size());
        assertEquals("fixture.CaptureFixture", inventory.entrypoint().binaryName());
        assertEquals(fixture.source(), inventory.entrypoint().sourceRef());
        assertEquals(inventory, inventory(fixture));
        Path injected = fixture.root().resolve("injected.class");
        Files.copy(Path.of(inventory.runtimeClasses().getFirst().path()), injected);
        assertThrows(IOException.class, () -> inventory(fixture));
    }

    @Test void actualCompilerSourceAndClasspathResourceDriftAreRejected() throws Exception {
        Fixture fixture = fixture(); inventory(fixture);
        Files.writeString(fixture.root().resolve("data.txt"), "changed");
        assertThrows(IOException.class, () -> inventory(fixture));
        Files.writeString(fixture.root().resolve("data.txt"), "resource");
        Files.writeString(Path.of(fixture.source().path()), "changed");
        assertThrows(IOException.class, () -> inventory(fixture));
    }

    @Test void originalPublicSourceExportAndMainRunUnchangedWithoutInferringAnUnavailableEntry() throws Exception {
        Fixture fixture = fixture();
        try (var loader = new URLClassLoader(new java.net.URL[] { fixture.root().toUri().toURL() }, getClass().getClassLoader())) {
            Class<?> target = Class.forName("fixture.CaptureFixture", false, loader);
            Path text = temporary.resolve("source.txt");
            OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], text);
            assertEquals("ORIGINAL_SOURCE\n", Files.readString(text));
            Path main = temporary.resolve("main.txt");
            OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.MAIN, new String[] {main.toString()}, main);
            assertEquals("ORIGINAL_MAIN\n", Files.readString(main));
            assertThrows(IOException.class, () -> OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], text));
            Class<?> noEntry = Class.forName("fixture.CaptureFixture$Nested", false, loader);
            assertThrows(NoSuchMethodException.class, () -> OriginalCaptureInvoker.invoke(noEntry, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], temporary.resolve("absent.txt")));
            assertThrows(IllegalArgumentException.class, () -> OriginalCaptureInvoker.invoke(target, temporary.toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.MAIN, new String[] {main.toString()}, main));
        }
    }

    @Test void missingGenuineReceiptTraversesRealProducerAndConsumerWithoutStartingAChild() throws Exception {
        var request = request(WindowsJobProcess.currentMachineId()); Path requestPath = temporary.resolve("request.json");
        Files.write(requestPath, ControlBuild.strictMapper().writeValueAsBytes(request));
        var spec = new CompiledOriginalCapture.RunSpec(ControlBuild.FileRef.measure(requestPath),
                temporary.resolve("receipt.json").toString(), limits(), CompiledOriginalCapture.Mode.EXECUTE);
        var result = CompiledOriginalCapture.execute(spec);
        assertEquals(CompiledOriginalCapture.Status.RED, result.status()); assertFalse(result.childStarted());
        assertTrue(result.error().contains("capture.json")); assertFalse(Files.exists(Path.of(request.outputPath())));
        assertEquals(result, ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(spec.receiptPath())), CompiledOriginalCapture.Receipt.class));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(ControlBuild.FileRef.measure(Path.of(spec.receiptPath())),
                CompiledOriginalCapture.Mode.EXECUTE));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.execute(spec));
    }

    @Test void passAndUnknownCannotBeManufacturedFromAnAckOrUnstartedCommand() {
        var request = ref(temporary.resolve("request.json"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCapture.Receipt(CompiledOriginalCapture.RECEIPT_SCHEMA,
                "unit-machine", Instant.now().toString(), CompiledOriginalCapture.Mode.EXECUTE, CompiledOriginalCapture.Status.PASS,
                CompiledOriginalCapture.Scope.ORIGINAL_SOURCE_EXPORT_ONLY, request, limits(), false, null, request, true, null, null, null, null, List.of(), List.of(), null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCapture.Receipt(CompiledOriginalCapture.RECEIPT_SCHEMA,
                "unit-machine", Instant.now().toString(), CompiledOriginalCapture.Mode.EXECUTE, CompiledOriginalCapture.Status.UNKNOWN,
                CompiledOriginalCapture.Scope.ORIGINAL_SOURCE_EXPORT_ONLY, request, limits(), false, null, null, false, null, null, null, null, List.of(), List.of(), "unavailable"));
    }

    @Test void finiteCanonicalModuleSelectionsRejectDuplicatesAliasesAndNonCaptureSources() {
        var source = ref(temporary.resolve("CaptureFixture.java")); var pom = ref(temporary.resolve("module/pom.xml"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", source,
                List.of(pom, pom), List.of()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Selection("fixture.Main",
                ref(temporary.resolve("Main.java")), List.of(pom), List.of()));
        assertThrows(IllegalArgumentException.class, () -> CompiledOriginalCaptureProfile.canonical(temporary.resolve("a/../b").toString()));
    }

    @Test void sharedNativeEngineConsumesActualExitAndJobZero() throws Exception {
        Path root = temporary.resolve("engine"), tmp = root.resolve("tmp"); Files.createDirectories(tmp);
        Path java = Path.of(System.getProperty("java.home")).resolve("bin/java.exe");
        var state = new CompiledCaptureProcess.StartState();
        var plan = new CompiledCaptureProcess.Plan(List.of(java.toString(), "-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-version"),
                root.toString(), tmp.toString(), root.toString(), root.resolve("stdout.log").toString(),
                root.resolve("stderr.log").toString(), root.resolve("not-produced.json").toString(), 1024, 1 << 20,
                15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertTrue(result.passed()); assertEquals(0, result.accounting().activeProcesses());
    }

    private record Fixture(Path snapshot, Path root, ControlBuild.FileRef source,
            List<ControlBuild.FileRef> inputs, ControlBuild.TestCompilationManifest manifest,
            CompiledOriginalCaptureProfile.Selection selection) { }

    /** Real javac bytes exercise only the inventory sub-boundary, never a fabricated accepted Maven/build receipt. */
    private Fixture fixture() throws Exception {
        Path snapshot = temporary.resolve("snapshot"), module = snapshot.resolve("module");
        Path source = module.resolve("src/test/java/fixture/CaptureFixture.java"), root = module.resolve("test-classes");
        Files.createDirectories(source.getParent()); Files.createDirectories(root);
        Files.writeString(source, "package fixture; public final class CaptureFixture {"
                + "public static String source(){ return \"ORIGINAL_SOURCE\\n\"; }"
                + "public static void main(String[] a)throws Exception{ if(a[0].equals(\"directory\")){"
                + "var scratch=java.nio.file.Path.of(a[1]).toRealPath();var input=java.nio.file.Path.of(a[2]).toRealPath();var out=java.nio.file.Path.of(a[3]);"
                + "java.nio.file.Files.createDirectory(out);java.nio.file.Files.copy(input.resolve(\"input.txt\"),out.resolve(\"result.txt\"));"
                + "java.nio.file.Files.writeString(scratch.resolve(\"side.txt\"),\"owned output\");Thread.sleep(1000);"
                + "}else java.nio.file.Files.writeString(java.nio.file.Path.of(a[0]),\"ORIGINAL_MAIN\\n\"); }"
                + "public static final class Nested{} }");
        var compiler = ToolProvider.getSystemJavaCompiler(); var errors = new ByteArrayOutputStream();
        assertEquals(0, compiler.run(null, errors, errors, "--release", "21", "-Xlint:all", "-Werror", "-d", root.toString(), source.toString()),
                errors.toString(StandardCharsets.UTF_8));
        Path pom = module.resolve("pom.xml"); Files.writeString(pom, "<project/>");
        Path resource = module.resolve("src/test/resources/data.txt"); Files.createDirectories(resource.getParent());
        Files.writeString(resource, "resource"); Files.copy(resource, root.resolve("data.txt"));
        Path inputs = module.resolve("inputs.lst"), created = module.resolve("created.lst");
        Files.writeString(inputs, source.toString()); Files.writeString(created, "fixture/CaptureFixture.class\nfixture/CaptureFixture$Nested.class\n");
        var classes = new ArrayList<ControlBuild.FileRef>();
        try (var walk = Files.walk(root)) {
            for (Path file : walk.filter(path -> path.toString().endsWith(".class")).sorted().toList()) classes.add(ControlBuild.FileRef.measure(file));
        }
        var sourceRef = ControlBuild.FileRef.measure(source); var pomRef = ControlBuild.FileRef.measure(pom);
        var manifest = new ControlBuild.TestCompilationManifest(ControlBuild.TEST_COMPILATION_SCHEMA, "unit-machine",
                Instant.now().toString(), ControlBuild.CaptureTestState.NOT_RUN,
                List.of(new ControlBuild.ModuleTestCompilation(pomRef, root.toString(), ControlBuild.FileRef.measure(inputs), ControlBuild.FileRef.measure(created))),
                List.of(new ControlBuild.NotRunTestCompilation(sourceRef, classes, ControlBuild.CaptureTestState.NOT_RUN)));
        return new Fixture(snapshot, root, sourceRef, List.of(pomRef, sourceRef, ControlBuild.FileRef.measure(resource)), manifest,
                new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", sourceRef, List.of(pomRef), List.of()));
    }
    private CompiledOriginalCaptureProfile.Inventory inventory(Fixture fixture) throws IOException {
        return CompiledOriginalCaptureProfile.inventory(fixture.snapshot(), fixture.inputs(), fixture.manifest(), fixture.selection());
    }
    private CompiledOriginalCapture.Request request(String machine) {
        var profile = new CompiledOriginalCaptureProfile.Profile(ref(temporary.resolve("capture.json")), ref(temporary.resolve("manifest.json")),
                ref(temporary.resolve("caller.json")), ref(temporary.resolve("producer.json")),
                new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", ref(temporary.resolve("CaptureFixture.java")),
                        List.of(ref(temporary.resolve("module/pom.xml"))), List.of()),
                CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, null, List.of(), List.of(), List.of(), null);
        return new CompiledOriginalCapture.Request(CompiledOriginalCapture.REQUEST_SCHEMA, "original-fixture", machine, temporary.toString(),
                profile, List.of(ref(temporary.resolve("CaptureFixture.java"))), List.of(ref(temporary.resolve("CaptureFixture.class"))),
                temporary.resolve("original.source.txt").toString(), CompiledOriginalCapture.OutputKind.FILE, 65536, 1 << 20, List.of());
    }
    private CompiledGoldenCapture.Limits limits() {
        return new CompiledGoldenCapture.Limits(temporary.toString(), temporary.toString(), Instant.now().plusSeconds(60).toString(), 60, 128L << 20);
    }
    private static ControlBuild.FileRef ref(Path path) { return new ControlBuild.FileRef(path.toString(), 1, "0".repeat(64)); }

    @Test void originalInnerJvmCarriesOwnedTemporaryPropertiesThroughActualNativeIdentity() throws Exception {
        Path owned = temporary.resolve("owned temporary directory"); Files.createDirectory(owned);
        var arguments = new ArrayList<String>(List.of(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString(), "-Xms8m", "-Xmx32m", "-XX:+UseSerialGC"));
        arguments.addAll(CompiledOriginalCapture.childTemporaryArguments(owned));
        arguments.addAll(List.of("-cp", System.getProperty("java.class.path"), TemporaryIdentityChild.class.getName(), owned.toString()));
        var state = new CompiledCaptureProcess.StartState();
        Path stdout = temporary.resolve("native-identity.stdout"), stderr = temporary.resolve("native-identity.stderr");
        var plan = new CompiledCaptureProcess.Plan(arguments, temporary.toString(), owned.toString(), temporary.toString(),
                stdout.toString(), stderr.toString(), temporary.resolve("unused-artifact").toString(), 1024, 1 << 20,
                15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertTrue(result.passed(), Files.readString(stderr));
        assertEquals(0, result.accounting().activeProcesses());
        assertTrue(Files.readString(stdout).contains(WindowsJobProcess.currentMachineId()));
    }
    private CompiledOriginalCaptureProfile.Profile directoryProfile(Path owned, Path input, Path output) throws IOException {
        var old = request("unit-machine").profile();
        return new CompiledOriginalCaptureProfile.Profile(old.captureReceiptRef(), old.testCompilationRef(), old.callerToolsReceiptRef(), old.producerToolsReceiptRef(),
                old.selection(), CompiledOriginalCaptureProfile.InvocationKind.JAVA_MAIN, null, List.of(
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.LITERAL, "directory", null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY, owned.toString(), null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.OUTPUT, output.toString(), null)), List.of(
                    new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY, owned.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.CREATE_EMPTY, null),
                    new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.EXISTING,
                        CompiledOriginalCaptureProfile.DirectoryManifest.measure(input, 65536))), List.of(), null);
    }
    private CompiledOriginalCapture.Request directoryRequest(CompiledOriginalCaptureProfile.Profile profile, Path output) {
        var old = request("unit-machine");
        return new CompiledOriginalCapture.Request(CompiledOriginalCapture.REQUEST_SCHEMA, "directory-fixture", old.machineId(), old.cwd(), profile,
                old.sourceRefs(), old.inputRefs(), output.toString(), CompiledOriginalCapture.OutputKind.DIRECTORY, 4L << 20, 8L << 20, List.of());
    }
    @Test void javaMainAndDirectoryInventoriesHaveOneStrictVersionedWireContract() throws Exception {
        Path input = temporary.resolve("input"); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "original");
        var request = directoryRequest(directoryProfile(temporary.resolve("owned"), input, temporary.resolve("output")), temporary.resolve("output"));
        var mapper = ControlBuild.strictMapper(); byte[] raw = mapper.writeValueAsBytes(request);
        assertEquals(request, CompiledOriginalCapture.parseRequest(raw));
        var missing = (ObjectNode) mapper.valueToTree(request); missing.remove("output_kind");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(missing)));
        var old = (ObjectNode) mapper.valueToTree(request); old.put("schema", "xar.compiled-original-capture-request/v1");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(old)));
        var bad = (ObjectNode) mapper.valueToTree(request); ((ObjectNode) bad.path("profile")).remove("directories");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(bad)));
        var identity = (ObjectNode) mapper.valueToTree(request);
        ((ObjectNode) identity.path("profile").path("directories").get(1).path("input_manifest").path("identity")).put("file_id_decimal", true);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(identity)));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY,
                input.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.CREATE_EMPTY, request.profile().directories().getLast().inputManifest()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), ref(input)));
    }
    @Test void actualDirectoryPreparationOriginalJavaMainAndOutputConsumerCloseTheLoop() throws Exception {
        Fixture fixture = fixture(); Path input = temporary.resolve("input"); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "original bytes");
        Path owned = temporary.resolve("owned"), output = temporary.resolve("output"); var request = directoryRequest(directoryProfile(owned, input, output), output);
        var initial = new ArrayList<ControlBuild.FileRef>(); CompiledOriginalCapture.prepareDirectories(request, temporary, initial);
        assertEquals(1, initial.size()); assertTrue(Files.isDirectory(owned));
        try (var loader = new URLClassLoader(new java.net.URL[] {fixture.root().toUri().toURL()}, getClass().getClassLoader())) {
            OriginalCaptureInvoker.invoke(Class.forName("fixture.CaptureFixture", false, loader), fixture.root().toString(),
                    request.profile().invocation(), request.profile().arguments().stream().map(CompiledOriginalCaptureProfile.Argument::value).toArray(String[]::new), output);
        }
        var manifest = CompiledOriginalCapture.writeDirectoryManifest(temporary.resolve("directory.json"), output, request.maxOutputBytes());
        CompiledOriginalCapture.requireOutput(request, null, manifest);
        Path metadata = temporary.resolve("cli-directory.json");
        String[] arguments = {"directory-manifest", output.toString(), metadata.toString(), "65536", temporary.toString()};
        CompiledOriginalCapture.main(arguments);
        assertTrue(CompiledOriginalCapture.readDirectoryManifest(manifest).sameInventory(CompiledOriginalCapture.readDirectoryManifest(ControlBuild.FileRef.measure(metadata))));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.main(arguments));
        CompiledOriginalCapture.readDirectoryManifest(initial.getFirst()).verifyRetained();
        assertEquals("original bytes", Files.readString(output.resolve("result.txt")));
        Files.createDirectory(output.resolve("extra-empty-directory"));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.requireOutput(request, null, manifest));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.prepareDirectories(request, temporary, new ArrayList<>()));
    }
    @Test void immutableDirectoryAndOwnedRetentionRejectChangesAndNativeReplacement() throws Exception {
        Path input = temporary.resolve("input"); Files.createDirectory(input); Files.createDirectory(input.resolve("empty")); Files.writeString(input.resolve("input.txt"), "same bytes");
        var initial = CompiledOriginalCaptureProfile.DirectoryManifest.measure(input, 65536); initial.verify();
        Files.writeString(input.resolve("new.txt"), "new owned output"); initial.verifyRetained(); assertThrows(IOException.class, initial::verify);
        Files.move(input.resolve("input.txt"), input.resolve("previous.txt")); Files.writeString(input.resolve("input.txt"), "same bytes");
        assertThrows(IOException.class, initial::verifyRetained);
        Path outside = temporary.resolveSibling("outside-owned"); var output = temporary.resolve("output");
        var request = directoryRequest(directoryProfile(outside, input, output), output);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.prepareDirectories(request, temporary, new ArrayList<>()));
        assertFalse(Files.exists(outside));
    }
    @Test void actualManagedDirectoryOutputOverflowKeepsFailureAndJobZero() throws Exception {
        Fixture fixture = fixture(); Path owned = temporary.resolve("owned"), input = temporary.resolve("input"), output = temporary.resolve("output");
        Files.createDirectory(owned); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "larger than one byte");
        var command = new ArrayList<String>(List.of(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString(), "-Xms8m", "-Xmx32m", "-XX:+UseSerialGC"));
        command.addAll(CompiledOriginalCapture.childTemporaryArguments(owned)); command.addAll(List.of("-cp", fixture.root().toString(), "fixture.CaptureFixture", "directory", owned.toString(), input.toString(), output.toString()));
        var state = new CompiledCaptureProcess.StartState();
        var plan = new CompiledCaptureProcess.Plan(command, temporary.toString(), owned.toString(), temporary.toString(), temporary.resolve("out.log").toString(), temporary.resolve("err.log").toString(),
                output.toString(), 1, 1 << 20, 15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertFalse(result.passed()); assertEquals(0, result.accounting().activeProcesses()); assertTrue(result.stopReason() != null);
        assertTrue(Files.isRegularFile(output.resolve("result.txt")));
    }
    public static final class TemporaryIdentityChild {
        private TemporaryIdentityChild() { }
        public static void main(String[] args) throws Exception {
            Path expected = Path.of(args[0]).toRealPath();
            for (String key : List.of("java.io.tmpdir", "jna.tmpdir"))
                if (!Path.of(System.getProperty(key)).toRealPath().equals(expected)) throw new IllegalStateException("Wrong owned temporary property");
            System.out.println(WindowsJobProcess.currentMachineId());
        }
    }
}
