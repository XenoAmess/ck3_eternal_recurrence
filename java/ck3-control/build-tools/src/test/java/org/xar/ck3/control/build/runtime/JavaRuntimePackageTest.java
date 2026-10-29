package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ContractPin;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.JavaHome;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.LaunchSettings;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeInputs;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;

/** Real file/JAR producers exercise the same complete-tree importer used by package production/readback.
 * These are software fixtures, not a completed Maven build or Native/Game qualification.
 */
final class JavaRuntimePackageTest {
    @TempDir Path temporary;
    private static final String REQUIRED = "org.xar.fixture.Required";

    @Test void realJarAndPrivateCopyProducersRoundTripThroughWholeTreeAndClassImporter() throws Exception {
        Path source = fastJar(temporary.resolve("original"));
        List<FileRef> originals = JavaRuntimePackageFiles.inventory(source, 1L << 20);
        var layout = JavaRuntimePackageFiles.inspectFastJar(source, originals, List.of(REQUIRED));
        assertTrue(layout.applicationClasses().stream().anyMatch(value -> value.binaryName().equals("org.xar.fixture.package-info")));
        Path copied = Files.createDirectory(temporary.resolve("private-package"));
        List<FileRef> outputs = new ArrayList<>();
        for (FileRef original : originals) {
            Path target = copied.resolve(source.relativize(Path.of(original.path())));
            var result = JavaRuntimePackageFiles.copyNew(original, target);
            outputs.add(result.source());
            assertFalse(SharedSourceFiles.observe(Path.of(original.path())).nativeFile().identityKey().equals(result.nativeFile().identityKey()));
        }
        outputs.sort(Comparator.comparing(FileRef::path));
        JavaRuntimePackageFiles.verifyCompleteTree(copied, outputs, 1L << 20);
        assertEquals(layout, JavaRuntimePackageFiles.inspectFastJar(copied, outputs, List.of(REQUIRED)));
    }

    @Test void wholeTreeImporterRejectsExtraMissingAndChangedResourcesIncludingNonJarLeaves() throws Exception {
        Path root = fastJar(temporary.resolve("complete"));
        List<FileRef> accepted = JavaRuntimePackageFiles.inventory(root, 1L << 20);
        Path extra = root.resolve("extra-resource.json"); Files.writeString(extra, "{}");
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.verifyCompleteTree(root, accepted, 1L << 20));
        Files.delete(extra);
        Path resource = root.resolve("quarkus/quarkus-application.dat"); Files.writeString(resource, "changed");
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.verifyCompleteTree(root, accepted, 1L << 20));
        Files.delete(resource);
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of(REQUIRED)));
    }

    @Test void bootDependencyAndApplicationClassMustBothBePresent() throws Exception {
        Path root = fastJar(temporary.resolve("missing"));
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of("org.xar.fixture.Absent")));
        Files.delete(root.resolve("lib/boot/boot.jar"));
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of(REQUIRED)));
    }

    @Test void executablePayloadAndWrongRunnerCannotEnterAJavaOnlyFastJar() throws Exception {
        Path root = fastJar(temporary.resolve("executable"));
        Path script = root.resolve("launcher.py"); Files.writeString(script, "raise RuntimeError()");
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of(REQUIRED)));
        Files.delete(script);
        jar(root.resolve("quarkus-run.jar"), List.of(), "org.example.UnreviewedMain", "lib/boot/boot.jar");
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of(REQUIRED)));
    }

    @Test void generatedAliasCannotSubstituteForARealApplicationClass() throws Exception {
        Path root = fastJar(temporary.resolve("alias"));
        jar(root.resolve("quarkus/generated-bytecode.jar"), List.of("org/xar/fixture/Required.class"), null, null);
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.inspectFastJar(root,
                JavaRuntimePackageFiles.inventory(root, 1L << 20), List.of(REQUIRED)));
    }

    @Test void immutableCopyRejectsSourceDriftExistingDestinationAndLaterOutputTampering() throws Exception {
        Path source = temporary.resolve("original.txt"); Files.writeString(source, "one");
        FileRef original = FileRef.measure(source); Path copied = temporary.resolve("copy.txt");
        var witness = JavaRuntimePackageFiles.copyNew(original, copied);
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.copyNew(original, copied));
        Files.writeString(source, "two");
        assertThrows(IOException.class, () -> JavaRuntimePackageFiles.copyNew(original, temporary.resolve("stale.txt")));
        Files.writeString(copied, "two");
        assertThrows(IOException.class, () -> SharedSourceFiles.assertUnchanged(witness));
    }

    @Test void forgedOrIncompleteBuildIsUnavailableBeforeAnyNativeAuthorityOrOutputWrite() throws Exception {
        Request request = request(temporary, HostMode.HTTP);
        var result = JavaRuntimePackage.review(request, (ignored, configuration) -> {
            throw new AssertionError("Native authority must not be consulted for an unaccepted build");
        });
        assertEquals(JavaRuntimePackage.Stage.BUILD_OR_INPUT_UNAVAILABLE,
                assertInstanceOf(JavaRuntimePackage.Unavailable.class, result).stage());
        var captured = JavaRuntimePackage.reviewCapturedService(request, (ignored, configuration) -> {
            throw new AssertionError("Capture review must also reject an unaccepted receipt before native authority");
        });
        assertEquals(JavaRuntimePackage.Stage.BUILD_OR_INPUT_UNAVAILABLE,
                assertInstanceOf(JavaRuntimePackage.Unavailable.class, captured).stage());
        assertFalse(Files.exists(Path.of(request.outputRoot())));
    }

    @Test void actualReviewRejectsSystemVolumeBeforeReadingBuildOrCreatingPackage()throws Exception {
        String systemRoot=System.getenv("SystemRoot");
        org.junit.jupiter.api.Assumptions.assumeTrue(systemRoot!=null&&!systemRoot.isBlank(),"Windows physical system-volume regression requires actual SystemRoot; skipped is not a pass");
        Path forbidden=Path.of(systemRoot).toAbsolutePath().getRoot().resolve("xar-package-policy-must-not-create-"+java.util.UUID.randomUUID());
        Request original=request(temporary,HostMode.HTTP);
        ObjectNode body=(ObjectNode)ControlBuild.strictMapper().readTree(JavaRuntimePackageCodec.encodeRequest(original));
        body.put("output_root",forbidden.toString());Request blocked=JavaRuntimePackageCodec.decodeRequest(JavaRuntimePackageCodec.encode(body));
        String before=System.getProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        try {
            System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,"true");
            var result=JavaRuntimePackage.review(blocked,(ignored,configuration)->{throw new AssertionError("Native authority cannot precede the actual storage guard");});
            var unavailable=assertInstanceOf(JavaRuntimePackage.Unavailable.class,result);
            assertEquals(JavaRuntimePackage.Stage.BUILD_OR_INPUT_UNAVAILABLE,unavailable.stage());
            assertTrue(unavailable.reason().toLowerCase(java.util.Locale.ROOT).contains("system"),unavailable.reason());
            var captured=JavaRuntimePackage.reviewCapturedService(blocked,(ignored,configuration)->{throw new AssertionError("Capture review cannot precede the actual storage guard");});
            var captureUnavailable=assertInstanceOf(JavaRuntimePackage.Unavailable.class,captured);
            assertEquals(JavaRuntimePackage.Stage.BUILD_OR_INPUT_UNAVAILABLE,captureUnavailable.stage());
            assertTrue(captureUnavailable.reason().toLowerCase(java.util.Locale.ROOT).contains("system"),captureUnavailable.reason());
            assertFalse(Files.exists(forbidden));
        } finally {
            if(before==null)System.clearProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
            else System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,before);
        }
    }

    @Test void threeActualStagesRoundTripAndRejectMissingWrongTypedOrAliasedProducerFields() throws Exception {
        Request request = request(temporary, HostMode.HTTP);
        byte[] produced = JavaRuntimePackageCodec.encodeRequest(request);
        assertEquals(request, JavaRuntimePackageCodec.decodeRequest(produced));
        ObjectNode body = (ObjectNode) ControlBuild.strictMapper().readTree(produced);
        for (String field : List.of("environment_actual", "build_actual", "registration_actual")) {
            ObjectNode missing = body.deepCopy(); ((ObjectNode) missing.get("native_inputs")).remove(field);
            assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(JavaRuntimePackageCodec.encode(missing)));
            ObjectNode scalar = body.deepCopy(); ((ObjectNode) scalar.get("native_inputs")).put(field, true);
            assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(JavaRuntimePackageCodec.encode(scalar)));
            ObjectNode nil = body.deepCopy(); ((ObjectNode) nil.get("native_inputs")).putNull(field);
            assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(JavaRuntimePackageCodec.encode(nil)));
        }
        ObjectNode aliased = body.deepCopy(); ObjectNode nativeInputs = (ObjectNode) aliased.get("native_inputs");
        nativeInputs.set("environment_actual", nativeInputs.get("build_actual"));
        assertThrows(IOException.class, () -> JavaRuntimePackageCodec.decodeRequest(JavaRuntimePackageCodec.encode(aliased)));
    }

    @Test void threeStageProofRejectsMissingSourcesArtifactsAndDuplicateEvidencePaths() throws Exception {
        Request request = request(temporary, HostMode.HTTP); NativeInputs expected = request.nativeInputs();
        NativeProof complete = proof(request, request.hostConfiguration());
        for (FileRef required : expected.mandatoryEvidence()) {
            List<FileRef> missing = complete.completeEvidenceClosure().stream().filter(value -> !value.equals(required)).toList();
            assertThrows(IllegalArgumentException.class, () -> new NativeProof(request.machineId(), request.launch().mode(),
                    request.hostConfiguration(), expected, missing));
        }
        List<FileRef> duplicate = new ArrayList<>(complete.completeEvidenceClosure());
        duplicate.add(complete.completeEvidenceClosure().get(0));
        assertThrows(IllegalArgumentException.class, () -> new NativeProof(request.machineId(), request.launch().mode(),
                request.hostConfiguration(), expected, duplicate));
    }

    @Test void exactNativeProofConsumerBindsOriginalAndPrivateHostAndRejectsStageFileDrift() throws Exception {
        Request request = request(temporary, HostMode.HTTP);
        NativeProof original = proof(request, request.hostConfiguration());
        assertEquals(original, JavaRuntimePackage.verifyNativeAuthority(request, request.hostConfiguration(), new FixedNativeReader(original)));
        FileRef privateHost = JavaRuntimePackageFiles.copyNew(request.hostConfiguration(), temporary.resolve("private/application.json")).source();
        NativeProof imported = proof(request, privateHost);
        assertEquals(imported, JavaRuntimePackage.verifyNativeAuthority(request, privateHost, new FixedNativeReader(imported)));
        assertEquals(original.completeEvidenceClosure(), imported.completeEvidenceClosure());
        Files.writeString(Path.of(request.nativeInputs().registrationActual().path()), "changed stage evidence");
        assertThrows(IOException.class, () -> JavaRuntimePackage.verifyNativeAuthority(request, privateHost, new FixedNativeReader(imported)));
        assertFalse(Files.exists(Path.of(request.outputRoot())));
    }

    @Test void exactNativeProofConsumerRejectsWrongMachineModeConfigurationAndNativeSelection() throws Exception {
        Request request = request(temporary, HostMode.HTTP); NativeProof expected = proof(request, request.hostConfiguration());
        FileRef privateHost = JavaRuntimePackageFiles.copyNew(request.hostConfiguration(), temporary.resolve("other/application.json")).source();
        NativeInputs old = request.nativeInputs();
        NativeInputs changed = new NativeInputs(old.environmentActual(), old.buildActual(), old.registrationActual(), old.sourceRoot(),
                old.completeSources(), old.bridgeDll(), old.injector(), old.gameExecutable(), old.launcherSettings(),
                old.bridgeVersion() + "-other", old.adapterId());
        for (NativeProof wrong : List.of(
                new NativeProof("another-machine", expected.mode(), expected.actualHostConfiguration(), old, expected.completeEvidenceClosure()),
                new NativeProof(expected.machineId(), HostMode.MCP_STDIO, expected.actualHostConfiguration(), old, expected.completeEvidenceClosure()),
                new NativeProof(expected.machineId(), expected.mode(), privateHost, old, expected.completeEvidenceClosure()),
                new NativeProof(expected.machineId(), expected.mode(), expected.actualHostConfiguration(), changed, expected.completeEvidenceClosure()))) {
            assertThrows(IOException.class, () -> JavaRuntimePackage.verifyNativeAuthority(request, request.hostConfiguration(), new FixedNativeReader(wrong)));
        }
        assertThrows(IOException.class, () -> JavaRuntimePackage.verifyNativeAuthority(request, request.hostConfiguration(), new FixedNativeReader(null)));
        assertThrows(IOException.class, () -> JavaRuntimePackage.verifyNativeAuthority(request, request.hostConfiguration(), (a, b) -> expected));
    }

    private static NativeProof proof(Request request, FileRef actualHost) {
        return new NativeProof(request.machineId(), request.launch().mode(), actualHost, request.nativeInputs(),
                request.nativeInputs().mandatoryEvidence());
    }
    private static final class FixedNativeReader implements JavaRuntimePackage.NativeAuthorityVerifier {
        private final NativeProof proof;
        private FixedNativeReader(NativeProof proof) { this.proof = proof; }
        @Override public NativeProof verify(Request request, FileRef actualHostConfiguration) { return proof; }
    }

    static Request request(Path temporary, HostMode mode) throws IOException {
        Path root = temporary.toAbsolutePath();
        Path javaRoot = Files.createDirectories(root.resolve("jdk"));
        FileRef java = leaf(javaRoot.resolve("bin/java.exe"), "fixture-not-a-jvm");
        Path nativeRoot = Files.createDirectories(root.resolve("native-source"));
        FileRef source = leaf(nativeRoot.resolve("src/bridge.cpp"), "fixture native source");
        FileRef build = leaf(root.resolve("service-actual.json"), "{\"status\":\"PASS\"}");
        FileRef nativeEnvironment = leaf(root.resolve("native-environment-actual.json"), "{}");
        FileRef nativeActual = leaf(root.resolve("native-build-actual.json"), "{}");
        FileRef nativeRegistration = leaf(root.resolve("native-registration-actual.json"), "{}");
        FileRef dll = leaf(root.resolve("native/xar_ck3_bridge.dll"), "fixture dll");
        FileRef injector = leaf(root.resolve("native/xar_ck3_bridge_injector.exe"), "fixture injector");
        FileRef game = leaf(root.resolve("game/ck3.exe"), "fixture game");
        FileRef settings = leaf(root.resolve("game/launcher-settings.json"), "{}");
        FileRef configuration = leaf(root.resolve("root-config.json"), "{}");
        Path scratch = Files.createDirectories(root.resolve("scratch"));
        Path nativeScratch = Files.createDirectories(scratch.resolve("jna"));
        Instant now = Instant.now();
        return new Request(JavaRuntimePackageModel.REQUEST_SCHEMA, WindowsJobProcess.currentMachineId(), "test-generation",
                now.minusSeconds(1).toString(), now.plusSeconds(60).toString(), root.resolve("package").toString(), build,
                new JavaHome(javaRoot.toString(), java, List.of(java)),
                new NativeInputs(nativeEnvironment, nativeActual, nativeRegistration, nativeRoot.toString(), List.of(source), dll, injector, game, settings,
                        "fixture-not-qualified", "fixture-adapter"), List.of(new ContractPin("fixture-contract", source)), configuration,
                new LaunchSettings(mode, 18080, 32L << 20, 256L << 20, scratch.toString(), nativeScratch.toString()),
                List.of(), 64L << 20);
    }

    private static FileRef leaf(Path path, String body) throws IOException {
        Files.createDirectories(path.getParent()); Files.writeString(path, body, StandardCharsets.UTF_8); return FileRef.measure(path);
    }

    private static Path fastJar(Path root) throws IOException {
        Files.createDirectories(root);
        jar(root.resolve("quarkus-run.jar"), List.of(), "io.quarkus.bootstrap.runner.QuarkusEntryPoint", "lib/boot/boot.jar");
        jar(root.resolve("app/application.jar"), List.of("org/xar/fixture/Required.class", "org/xar/fixture/package-info.class"), null, null);
        jar(root.resolve("lib/boot/boot.jar"), List.of(), null, null);
        jar(root.resolve("lib/main/dependency.jar"), List.of(), null, null);
        leaf(root.resolve("quarkus/quarkus-application.dat"), "fixture application data");
        leaf(root.resolve("quarkus-app-dependencies.txt"), "fixture dependencies"); return root;
    }

    private static void jar(Path path, List<String> entries, String mainClass, String bootClassPath) throws IOException {
        Files.createDirectories(path.getParent()); Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        if (mainClass != null) manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, mainClass);
        if (bootClassPath != null) manifest.getMainAttributes().put(Attributes.Name.CLASS_PATH, bootClassPath);
        try (JarOutputStream output = new JarOutputStream(Files.newOutputStream(path), manifest)) {
            for (String entry : entries) { output.putNextEntry(new JarEntry(entry)); output.write(new byte[]{1}); output.closeEntry(); }
        }
    }
}
