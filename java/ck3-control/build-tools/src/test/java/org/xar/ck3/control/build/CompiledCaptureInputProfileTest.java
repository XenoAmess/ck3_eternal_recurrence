package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Shape/command tests only. Actual receipt/provenance/Job qualification requires the separate full integration gate. */
class CompiledCaptureInputProfileTest {
    @TempDir Path temporary;

    @Test void typedProfileSurvivesStrictJsonRoundTrip() throws Exception {
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_PENDING_READERS);
        var mapper = ControlBuild.strictMapper();
        JsonNode json = mapper.readTree(mapper.writeValueAsBytes(value));
        assertEquals(value, CompiledCaptureInputProfile.parse(json));
        assertEquals(6, value.runtimeClassRefs().size());
        assertEquals(4, value.launcher().argumentCount());
    }

    @Test void unknownMissingNullAndCoercedProfileFieldsAreRejected() throws Exception {
        ObjectNode good = json(profile(CompiledCaptureInputProfile.Launcher.GIFT_READ));
        ObjectNode unknown = good.deepCopy(); unknown.put("unexpected", true);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(unknown));
        ObjectNode missing = good.deepCopy(); missing.remove("caller_tools_receipt_ref");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(missing));
        ObjectNode nil = good.deepCopy(); nil.putNull("launcher");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(nil));
        ObjectNode booleanBytes = good.deepCopy(); ((ObjectNode) booleanBytes.path("capture_receipt_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(booleanBytes));
        ObjectNode floatBytes = good.deepCopy(); ((ObjectNode) floatBytes.path("capture_receipt_ref")).put("bytes", 1.0);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(floatBytes));
        ObjectNode stringBytes = good.deepCopy(); ((ObjectNode) stringBytes.path("capture_receipt_ref")).put("bytes", "1");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(stringBytes));
        ObjectNode numericEnum = good.deepCopy(); numericEnum.put("profile", 0);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(numericEnum));
        ObjectNode invalidEnum = good.deepCopy(); invalidEnum.put("profile", "FULL_VERIFY");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.parse(invalidEnum));
    }

    @Test void enclosingStrictParserRejectsDuplicateKeysBeforeTreeConversion() {
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readTree("{\"profile\":\"QUALIFIED_TEST_CLASSES_V1\",\"profile\":\"QUALIFIED_TEST_CLASSES_V1\"}"));
    }

    @Test void missingRepeatedReorderedAndForeignRuntimeClassReferencesAreRejected() {
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_READ);
        var five = value.runtimeClassRefs().subList(0, 5);
        assertThrows(IllegalArgumentException.class, () -> withClasses(value, five));
        var repeated = new ArrayList<>(value.runtimeClassRefs()); repeated.set(1, repeated.getFirst());
        assertThrows(IllegalArgumentException.class, () -> withClasses(value, repeated));
        var reordered = new ArrayList<>(value.runtimeClassRefs());
        var first = reordered.getFirst(); reordered.set(0, reordered.get(1)); reordered.set(1, first);
        assertThrows(IllegalArgumentException.class, () -> withClasses(value, reordered));
        var foreign = new ArrayList<>(value.runtimeClassRefs());
        foreign.set(0, ref(temporary.resolve("foreign/Main.class")));
        assertThrows(IllegalArgumentException.class, () -> withClasses(value, foreign));
    }

    @Test void lexicalAliasesAndNonFiniteMetadataCannotAcquireProfileAdmission() throws Exception {
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_READ);
        // G2-sized receipt metadata survives strict serialization; provenance is still required.
        var g2Capture = new ControlBuild.FileRef(value.captureReceiptRef().path(), 1_201_708, "0".repeat(64));
        var g2Caller = new ControlBuild.FileRef(value.callerToolsReceiptRef().path(), 1_201_708, "0".repeat(64));
        var g2Compiler = new ControlBuild.FileRef(value.producerToolsReceiptRef().path(), 1_201_708, "0".repeat(64));
        var g2Sized = new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(),
                g2Capture, value.testCompilationRef(), g2Caller, g2Compiler, value.classRoot(), value.runtimeClassRefs());
        assertEquals(g2Sized, CompiledCaptureInputProfile.parse(json(g2Sized)));
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.validate(g2Sized, temporary.toString(),
                List.of(), temporary.resolve("output.json").toString(), List.of(), g2Sized.runtimeClassRefs()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(),
                value.captureReceiptRef(), value.testCompilationRef(), value.callerToolsReceiptRef(), value.producerToolsReceiptRef(),
                temporary.resolve("aliased/../classes").toString(), value.runtimeClassRefs()));
        var tooLarge = new ControlBuild.FileRef(value.captureReceiptRef().path(), ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES + 1, "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(),
                tooLarge, value.testCompilationRef(), value.callerToolsReceiptRef(), value.producerToolsReceiptRef(),
                value.classRoot(), value.runtimeClassRefs()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(),
                value.captureReceiptRef(), value.testCompilationRef(), tooLarge, value.producerToolsReceiptRef(),
                value.classRoot(), value.runtimeClassRefs()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(),
                value.captureReceiptRef(), value.testCompilationRef(), value.callerToolsReceiptRef(), tooLarge,
                value.classRoot(), value.runtimeClassRefs()));
    }

    @Test void resumedEnvelopeShapeAndProfileBoundaryDoNotGrantCompletedCaptureQualification() throws Exception {
        assertEquals(2 << 20, ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        assertEquals(4 << 20, ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES);
        ObjectNode envelope = ControlBuild.strictMapper().createObjectNode();
        envelope.put("source_limit_profile", ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2.name());
        envelope.put("padding", "x".repeat((2 << 20) + 256));
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(envelope);
        Path resumedPath = temporary.resolve("resumed-envelope-only.json");
        Files.write(resumedPath, raw);
        var resumed = ControlBuild.FileRef.measure(resumedPath);
        assertTrue(resumed.bytes() > ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        assertArrayEquals(raw, ControlBuild.readReceiptEnvelope(resumed));
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_READ);
        var shape = new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(), resumed,
                value.testCompilationRef(), value.callerToolsReceiptRef(), value.producerToolsReceiptRef(),
                value.classRoot(), value.runtimeClassRefs());
        assertEquals(shape, CompiledCaptureInputProfile.parse(json(shape)));
        // The envelope helper admits bytes only. This deliberately incomplete object is never an accepted capture.
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedCaptureReceipt(resumed));
        envelope.put("source_limit_profile", ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024.name());
        Path legacyPath = temporary.resolve("oversized-legacy-envelope.json");
        Files.write(legacyPath, ControlBuild.strictMapper().writeValueAsBytes(envelope));
        var legacy = ControlBuild.FileRef.measure(legacyPath);
        assertThrows(IOException.class, () -> ControlBuild.readReceiptEnvelope(legacy));
        envelope.put("source_limit_profile", true);
        Path invalidPath = temporary.resolve("wrong-type-envelope.json");
        Files.write(invalidPath, ControlBuild.strictMapper().writeValueAsBytes(envelope));
        var wrongType = ControlBuild.FileRef.measure(invalidPath);
        assertThrows(IOException.class, () -> ControlBuild.readReceiptEnvelope(wrongType));
    }

    @Test void compiledArtifactsRemainForbiddenInSourceRefsBeforeReceiptReads() {
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_PENDING_READERS);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.validate(value, temporary.toString(), List.of(), temporary.resolve("output.json").toString(),
                List.of(value.runtimeClassRefs().getFirst()), value.runtimeClassRefs()));
    }

    @Test void exactCompiledCommandBindsJavaRootAndLauncherWithoutLaunchingAnything() throws Exception {
        var value = profile(CompiledCaptureInputProfile.Launcher.GIFT_PENDING_READERS);
        Path fakeExecutable = temporary.resolve("fixture-no-execution.exe"); Files.write(fakeExecutable, new byte[] {1, 2, 3});
        var executable = ControlBuild.FileRef.measure(fakeExecutable);
        List<String> command = command(value, executable);
        CompiledCaptureInputProfile.requireExactCommand(value, command, executable);
        var withOutput = new ArrayList<>(command); withOutput.set(withOutput.size() - 1, temporary.resolve("output.json").toString());
        CompiledCaptureInputProfile.requireRowOutput(withOutput, temporary.resolve("output.json").toString());
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireRowOutput(withOutput, temporary.resolve("other.json").toString()));
        var extraRoot = new ArrayList<>(command); extraRoot.set(5, value.classRoot() + java.io.File.pathSeparator + temporary);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireExactCommand(value, extraRoot, executable));
        var property = new ArrayList<>(command); property.set(3, "-Dxar.capture.classRoot=" + temporary);
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireExactCommand(value, property, executable));
        var sourceLaunch = new ArrayList<>(command); sourceLaunch.set(6, "GiftPendingReaders.java");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireExactCommand(value, sourceLaunch, executable));
        var wildcard = new ArrayList<>(command); wildcard.set(5, value.classRoot() + "/*");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireExactCommand(value, wildcard, executable));
        var option = new ArrayList<>(command); option.add(3, "-javaagent:foreign.jar");
        assertThrows(IOException.class, () -> CompiledCaptureInputProfile.requireExactCommand(value, option, executable));
    }

    @Test void eachLauncherSelectsExactlyItsOwnMainPlusFiveSharedHelperBinaries() {
        for (var launcher : CompiledCaptureInputProfile.Launcher.values()) {
            var value = profile(launcher);
            assertEquals(launcher.binaryName(), launcher.runtimeBinaryNames().getFirst());
            assertEquals(6, launcher.runtimeBinaryNames().stream().distinct().count());
            assertEquals(6, value.runtimeClassRefs().stream().map(ControlBuild.FileRef::path).distinct().count());
        }
    }

    private ObjectNode json(CompiledCaptureInputProfile.Profile value) throws IOException {
        var mapper = ControlBuild.strictMapper();
        return mapper.readValue(mapper.writeValueAsBytes(value), ObjectNode.class);
    }

    private CompiledCaptureInputProfile.Profile profile(CompiledCaptureInputProfile.Launcher launcher) {
        Path root = temporary.toAbsolutePath().normalize().resolve("classes");
        List<ControlBuild.FileRef> classes = launcher.runtimeBinaryNames().stream()
                .map(name -> ref(root.resolve(name.replace('.', '/') + ".class"))).toList();
        return new CompiledCaptureInputProfile.Profile(CompiledCaptureInputProfile.Kind.QUALIFIED_TEST_CLASSES_V1, launcher,
                ref(temporary.resolve("capture.json")), ref(temporary.resolve("test-compilation.json")),
                ref(temporary.resolve("caller-tools.json")), ref(temporary.resolve("producer-tools.json")), root.toString(), classes);
    }

    private static CompiledCaptureInputProfile.Profile withClasses(CompiledCaptureInputProfile.Profile value,
            List<ControlBuild.FileRef> classes) {
        return new CompiledCaptureInputProfile.Profile(value.profile(), value.launcher(), value.captureReceiptRef(),
                value.testCompilationRef(), value.callerToolsReceiptRef(), value.producerToolsReceiptRef(), value.classRoot(), classes);
    }

    private static ControlBuild.FileRef ref(Path path) {
        return new ControlBuild.FileRef(path.toAbsolutePath().normalize().toString(), 1, "0".repeat(64));
    }

    private static List<String> command(CompiledCaptureInputProfile.Profile value, ControlBuild.FileRef executable) {
        var command = new ArrayList<>(List.of(executable.path(), "-Xms16m", "-Xmx64m", "-Dxar.capture.classRoot=" + value.classRoot(),
                "-cp", value.classRoot(), value.launcher().binaryName()));
        for (int index = 0; index < value.launcher().argumentCount(); index++) command.add("argument" + index);
        return List.copyOf(command);
    }
}
