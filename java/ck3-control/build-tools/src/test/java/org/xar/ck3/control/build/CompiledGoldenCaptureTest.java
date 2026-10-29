package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CompiledGoldenCaptureTest {
    @TempDir Path temporary;

    @Test void completeBatchRoundTripsThroughActualStrictProducerAndConsumerContract() throws Exception {
        var batch = batch("fixture-machine");
        assertEquals(batch, CompiledGoldenCapture.parseBatch(ControlBuild.strictMapper().writeValueAsBytes(batch)));
        ObjectNode json = json(batch);
        ObjectNode row = (ObjectNode) json.path("captures").get(0);
        assertEquals(7, row.size());
        assertEquals(9, batch.compiledInputProfiles().stream().flatMap(binding -> binding.inputProfile().runtimeClassRefs().stream())
                .map(ControlBuild.FileRef::path).distinct().count());
    }

    @Test void duplicateTrailingUnknownAndMissingBatchFieldsAreRejected() throws Exception {
        ObjectNode unknown = json(batch("fixture-machine")); unknown.put("unexpected", 1);
        assertThrows(IOException.class, () -> parse(unknown));
        ObjectNode missing = json(batch("fixture-machine")); missing.remove("compiled_input_profiles");
        assertThrows(IOException.class, () -> parse(missing));
        ObjectNode nil = json(batch("fixture-machine")); nil.putNull("compiled_input_profiles");
        assertThrows(IOException.class, () -> parse(nil));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.parseBatch("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        byte[] valid = ControlBuild.strictMapper().writeValueAsBytes(batch("fixture-machine"));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.parseBatch((new String(valid, StandardCharsets.UTF_8) + " {}").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void captureRowPrimitiveCoercionExtraFieldAndMissingOutputAreRejected() throws Exception {
        for (int variant = 0; variant < 5; variant++) {
            ObjectNode document = json(batch("fixture-machine"));
            ObjectNode row = (ObjectNode) document.path("captures").get(0);
            switch (variant) {
                case 0 -> row.put("max_output_bytes", true);
                case 1 -> row.put("max_output_bytes", 1.0);
                case 2 -> row.put("max_output_bytes", "1");
                case 3 -> row.put("profile", "QUALIFIED_TEST_CLASSES_V1");
                case 4 -> row.remove("output_path");
                default -> throw new AssertionError();
            }
            assertThrows(IOException.class, () -> parse(document));
        }
    }

    @Test void unusedDuplicateMissingAndCrossRequestProfilesCannotAdmitClasses() {
        var good = batch("fixture-machine");
        var bindings = new ArrayList<>(good.compiledInputProfiles());
        bindings.set(0, new CompiledGoldenCapture.ProfileBinding("unknown", bindings.getFirst().inputProfile()));
        assertThrows(IllegalArgumentException.class, () -> withBindings(good, bindings));
        var duplicate = new ArrayList<>(good.compiledInputProfiles()); duplicate.set(1, duplicate.getFirst());
        assertThrows(IllegalArgumentException.class, () -> withBindings(good, duplicate));
        assertThrows(IllegalArgumentException.class, () -> withBindings(good, good.compiledInputProfiles().subList(0, 3)));
        var crossed = new ArrayList<>(good.compiledInputProfiles());
        crossed.set(0, new CompiledGoldenCapture.ProfileBinding(good.captures().getFirst().id(), crossed.get(1).inputProfile()));
        assertThrows(IllegalArgumentException.class, () -> withBindings(good, crossed));
    }

    @Test void duplicateCaptureIdsAndReferencePathsAreRejected() {
        var good = batch("fixture-machine");
        var requests = new ArrayList<>(good.captures()); requests.set(1, requests.getFirst());
        assertThrows(IllegalArgumentException.class, () -> new CompiledGoldenCapture.Batch(good.schema(), good.machineId(), requests, good.compiledInputProfiles()));
        var row = good.captures().getFirst(); var inputs = new ArrayList<>(row.inputRefs()); inputs.add(inputs.getFirst());
        assertThrows(IllegalArgumentException.class, () -> request(row.id(), good.profileFor(row.id()), inputs));
        var oversized = new ArrayList<>(row.inputRefs());
        var first = oversized.getFirst(); oversized.set(0, new ControlBuild.FileRef(first.path(), (8L << 20) + 1, first.sha256()));
        assertThrows(IllegalArgumentException.class, () -> request(row.id(), good.profileFor(row.id()), oversized));
    }

    @Test void artifactsCannotEnterSourceReferencesAndLexicalAliasesRemainRejected() {
        var row = batch("fixture-machine").captures().getFirst();
        assertThrows(IllegalArgumentException.class, () -> new CompiledGoldenCapture.Request(row.id(), row.command(), row.cwd(),
                List.of(row.inputRefs().getFirst()), row.inputRefs(), row.outputPath(), row.maxOutputBytes()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledGoldenCapture.Request(row.id(), row.command(),
                temporary.resolve("x/../repo").toString(), row.sourceRefs(), row.inputRefs(), row.outputPath(), row.maxOutputBytes()));
    }

    @Test void parsedBytesMustMatchThePinActuallyConsumed() throws Exception {
        Path file = temporary.resolve("actual.json"); Files.writeString(file, "{\"original\":1}");
        var pin = ControlBuild.FileRef.measure(file);
        assertEquals("{\"original\":1}", new String(CompiledGoldenCapture.readPinned(pin, 128), StandardCharsets.UTF_8));
        Files.writeString(file, "{\"original\":2}");
        assertThrows(IOException.class, () -> CompiledGoldenCapture.readPinned(pin, 128));
    }

    @Test void missingGenuineCompilerReceiptTraversesRealCliBoundaryAndPreservesRedWithoutAChild() throws Exception {
        String machine = WindowsJobProcess.currentMachineId();
        var all = batch(machine); var first = all.captures().getFirst();
        var one = new CompiledGoldenCapture.Batch(all.schema(), machine, List.of(first), List.of(all.compiledInputProfiles().getFirst()));
        Path batchPath = temporary.resolve("batch.json"); Files.write(batchPath, ControlBuild.strictMapper().writeValueAsBytes(one));
        Path receiptPath = temporary.resolve("receipt.json");
        var result = CompiledGoldenCapture.execute(ControlBuild.FileRef.measure(batchPath), receiptPath, limits(), CompiledGoldenCapture.Mode.QUALIFY_ONLY);
        assertEquals(CompiledGoldenCapture.Status.RED, result.status()); assertEquals(0, result.childrenStarted());
        assertEquals(1, result.observations().size()); assertTrue(result.error().contains("caller.json"));
        assertFalse(Files.exists(Path.of(first.outputPath())));
        var parsed = CompiledGoldenCapture.parseReceipt(Files.readAllBytes(receiptPath));
        assertEquals(result, parsed);
        assertThrows(IOException.class, () -> CompiledGoldenCapture.acceptedReceipt(ControlBuild.FileRef.measure(receiptPath), CompiledGoldenCapture.Mode.QUALIFY_ONLY));
        Path captureReceipt = temporary.resolve("capture-rejected.json");
        var capture = CompiledGoldenCapture.execute(ControlBuild.FileRef.measure(batchPath), captureReceipt, limits(), CompiledGoldenCapture.Mode.CAPTURE);
        assertEquals(CompiledGoldenCapture.Status.RED, capture.status()); assertEquals(0, capture.childrenStarted());
        assertTrue(capture.error().contains("caller.json"));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.acceptedReceipt(ControlBuild.FileRef.measure(captureReceipt), CompiledGoldenCapture.Mode.CAPTURE));
    }

    @Test void realMachineMismatchAndMultipleCaptureRunAreRejectedBeforeAnyLaunch() throws Exception {
        Path file = temporary.resolve("wrong-machine.json"); Files.write(file, ControlBuild.strictMapper().writeValueAsBytes(batch("a-different-machine")));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.execute(ControlBuild.FileRef.measure(file), temporary.resolve("wrong-receipt.json"),
                limits(), CompiledGoldenCapture.Mode.QUALIFY_ONLY));
        Files.write(file, ControlBuild.strictMapper().writeValueAsBytes(batch(WindowsJobProcess.currentMachineId())));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.execute(ControlBuild.FileRef.measure(file), temporary.resolve("multi-receipt.json"),
                limits(), CompiledGoldenCapture.Mode.CAPTURE));
        assertFalse(Files.exists(temporary.resolve("multi-receipt.json")));
    }

    @Test void actualCaptureReceiptCannotClaimPassFromZeroChildOrIncompleteObservation() {
        var good = batch("fixture-machine");
        assertThrows(IllegalArgumentException.class, () -> new CompiledGoldenCapture.Receipt(CompiledGoldenCapture.RECEIPT_SCHEMA,
                good.machineId(), Instant.now().toString(), CompiledGoldenCapture.Mode.CAPTURE, CompiledGoldenCapture.Status.PASS,
                ref(temporary.resolve("batch.json")), good, limits(), 0, List.of(), null));
    }

    @Test void actualLegacyNoChildReceiptRemainsHistoricalAndCannotBeRelabelledCurrent() throws Exception {
        var all = batch(WindowsJobProcess.currentMachineId());
        var one = new CompiledGoldenCapture.Batch(all.schema(), all.machineId(), List.of(all.captures().getFirst()),
                List.of(all.compiledInputProfiles().getFirst()));
        Path input = temporary.resolve("actual-missing-compiler-batch.json");
        Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(one));
        Path current = temporary.resolve("actual-red-current.json");
        var produced = CompiledGoldenCapture.execute(ControlBuild.FileRef.measure(input), current, limits(), CompiledGoldenCapture.Mode.QUALIFY_ONLY);
        assertEquals(CompiledGoldenCapture.Status.RED, produced.status()); assertEquals(0, produced.childrenStarted());
        assertEquals(null, produced.observations().getFirst().invocationEvidence());
        ObjectNode legacy = ControlBuild.strictMapper().readValue(Files.readAllBytes(current), ObjectNode.class);
        legacy.put("schema", CompiledGoldenCapture.HISTORICAL_RECEIPT_SCHEMA);
        ((ObjectNode) legacy.path("observations").get(0)).remove("invocation_evidence");
        Path historical = temporary.resolve("explicit-v1-historical.json");
        Files.write(historical, ControlBuild.strictMapper().writeValueAsBytes(legacy));
        var pin = ControlBuild.FileRef.measure(historical);
        var metadata = CompiledGoldenCapture.historicalReceiptMetadata(pin);
        assertEquals(CompiledGoldenCapture.HISTORICAL_RECEIPT_SCHEMA, metadata.schema());
        assertEquals(produced.error(), metadata.error());
        assertEquals(produced.observations().getFirst().before(), metadata.observations().getFirst().before());
        assertEquals(null, metadata.observations().getFirst().invocationEvidence());
        IOException rejection = assertThrows(IOException.class,
                () -> CompiledGoldenCapture.acceptedReceipt(pin, CompiledGoldenCapture.Mode.CAPTURE));
        assertTrue(rejection.getMessage().contains("Historical capture")); pin.verify();
        Path roundtrip = temporary.resolve("historical-versioned-roundtrip.json");
        Files.write(roundtrip, CompiledGoldenCapture.encodeReceipt(metadata));
        assertEquals(metadata, CompiledGoldenCapture.historicalReceiptMetadata(ControlBuild.FileRef.measure(roundtrip)));
        assertFalse(ControlBuild.strictMapper().readTree(Files.readAllBytes(roundtrip)).path("observations").get(0).has("invocation_evidence"));

        // Adding a new-schema field to a v1 record never retroactively mints invocation custody.
        ((ObjectNode) legacy.path("observations").get(0)).putNull("invocation_evidence");
        Path relabelled = temporary.resolve("rejected-v1-new-field.json");
        Files.write(relabelled, ControlBuild.strictMapper().writeValueAsBytes(legacy));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.historicalReceiptMetadata(ControlBuild.FileRef.measure(relabelled)));

        // v2 records retain their actual argv field shape but cannot claim the new preparation custody.
        ObjectNode unprepared = ControlBuild.strictMapper().readValue(Files.readAllBytes(current), ObjectNode.class);
        unprepared.put("schema", CompiledGoldenCapture.UNPREPARED_RECEIPT_SCHEMA);
        Path v2 = temporary.resolve("explicit-v2-unprepared-metadata.json");
        Files.write(v2, ControlBuild.strictMapper().writeValueAsBytes(unprepared));
        var v2Pin = ControlBuild.FileRef.measure(v2);
        var v2Metadata = CompiledGoldenCapture.historicalReceiptMetadata(v2Pin);
        assertEquals(CompiledGoldenCapture.UNPREPARED_RECEIPT_SCHEMA, v2Metadata.schema());
        Path v2Roundtrip = temporary.resolve("unprepared-v2-roundtrip.json");
        Files.write(v2Roundtrip, CompiledGoldenCapture.encodeReceipt(v2Metadata));
        assertEquals(v2Metadata, CompiledGoldenCapture.historicalReceiptMetadata(ControlBuild.FileRef.measure(v2Roundtrip)));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.acceptedReceipt(v2Pin, CompiledGoldenCapture.Mode.CAPTURE));

        // The genuine no-child RED producer also preserves v3's null original invocation.
        // It never acquires a new native witness merely because the reader now understands v4.
        ObjectNode jdkOnly = ControlBuild.strictMapper().readValue(Files.readAllBytes(current), ObjectNode.class);
        jdkOnly.put("schema", CompiledGoldenCapture.JDK_ONLY_RECEIPT_SCHEMA);
        Path v3 = temporary.resolve("explicit-v3-jdk-only-metadata.json");
        Files.write(v3, ControlBuild.strictMapper().writeValueAsBytes(jdkOnly));
        var v3Pin = ControlBuild.FileRef.measure(v3);
        var v3Metadata = CompiledGoldenCapture.historicalReceiptMetadata(v3Pin);
        assertEquals(CompiledGoldenCapture.JDK_ONLY_RECEIPT_SCHEMA, v3Metadata.schema());
        assertEquals(produced.error(), v3Metadata.error());
        assertEquals(null, v3Metadata.observations().getFirst().invocationEvidence());
        assertEquals(null, v3Metadata.observations().getFirst().historicalInvocationEvidence());
        Path v3Roundtrip = temporary.resolve("jdk-only-v3-roundtrip.json");
        Files.write(v3Roundtrip, CompiledGoldenCapture.encodeReceipt(v3Metadata));
        assertEquals(v3Metadata, CompiledGoldenCapture.historicalReceiptMetadata(ControlBuild.FileRef.measure(v3Roundtrip)));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.acceptedReceipt(v3Pin, CompiledGoldenCapture.Mode.CAPTURE));

        ((ObjectNode) jdkOnly.path("observations").get(0)).putNull("historical_invocation_evidence");
        Path memorySlot = temporary.resolve("rejected-wire-memory-slot.json");
        Files.write(memorySlot, ControlBuild.strictMapper().writeValueAsBytes(jdkOnly));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.historicalReceiptMetadata(ControlBuild.FileRef.measure(memorySlot)));
    }

    @Test void actualUtf8EnvelopeProducerAndInspectorPreserveUnicodeAndRejectChangedArgvAndBody() throws Exception {
        Path classes = Files.createDirectories(temporary.resolve("原始编译类-\uD83D\uDE80"));
        String binaryName = CompiledGoldenCapture.class.getName();
        String resource = binaryName.replace('.', '/') + ".class";
        Path originalClass = classes.resolve(resource); Files.createDirectories(originalClass.getParent());
        try (var input = CompiledGoldenCapture.class.getClassLoader().getResourceAsStream(resource)) {
            if (input == null) throw new IOException("Actual compiled production main resource required");
            Files.copy(input, originalClass);
        }
        var original = ControlBuild.FileRef.measure(originalClass);
        var classpath = CiBootstrap.JavaUtf8Invocation.captureClasspath(classes);
        var root = CiBootstrap.JavaUtf8Invocation.captureOutputRoot(temporary);
        var request = new CiBootstrap.JavaUtf8Invocation.Request(
                new CiBootstrap.JavaUtf8Invocation.ClassTarget(binaryName, classpath, List.of(classpath)),
                List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.capture.classRoot", classes.toString())),
                List.of("实际 Unicode 参数-\uD83D\uDE80", "space quote \" and slash \\"), root);
        Path preparation = CiBootstrap.JavaUtf8Invocation.preparationPath(request);
        assertThrows(IOException.class, () -> CompiledGoldenCapture.requireOutputDisjoint(preparation, request));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.requireOutputDisjoint(preparation.resolve("nested-golden.json"), request));
        assertThrows(IOException.class, () -> CompiledGoldenCapture.requireOutputDisjoint(preparation.getParent(), request));
        CompiledGoldenCapture.requireOutputDisjoint(temporary.resolve("actual-independent-golden.json"), request);
        var publication = CiBootstrap.JavaUtf8Invocation.publish(request, root, "actual-utf8-envelope.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(temporary, 8L << 20, pending));
        Path actualCarrier = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        var carrier = new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(CiBootstrap.JavaUtf8Invocation.captureClasspath(actualCarrier)));
        List<String> vmOptions = List.of("-Xms16m", "-Xmx64m");
        var launch = CiBootstrap.JavaUtf8Invocation.launch(publication, carrier, vmOptions);
        assertEquals(request, CiBootstrap.JavaUtf8Invocation.inspect(launch.physicalArguments(), carrier, vmOptions));
        assertTrue(launch.physicalArguments().stream().allMatch(value -> value.codePoints().allMatch(point -> point >= 32 && point <= 126)));
        var changed = new ArrayList<>(launch.physicalArguments()); changed.set(0, "-Xms17m");
        assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.inspect(changed, carrier, vmOptions));
        Path envelope = Path.of(publication.envelope().path()); byte[] raw = Files.readAllBytes(envelope);
        byte[] substituted = raw.clone(); substituted[substituted.length - 1] ^= 1;
        try {
            Files.write(envelope, substituted);
            assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.inspect(launch.physicalArguments(), carrier, vmOptions));
        } finally { Files.write(envelope, raw); }
        // Restoring bytes does not restore the immutable publication metadata.
        Files.setLastModifiedTime(envelope, java.nio.file.attribute.FileTime.fromMillis(
                Math.addExact(Files.getLastModifiedTime(envelope).toMillis(), 2000L)));
        assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.inspect(launch.physicalArguments(), carrier, vmOptions));
        var replacementPublication = CiBootstrap.JavaUtf8Invocation.publish(request, root, "actual-utf8-envelope-restored.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(temporary, 8L << 20, pending));
        var replacementLaunch = CiBootstrap.JavaUtf8Invocation.launch(replacementPublication, carrier, vmOptions);
        assertEquals(request, CiBootstrap.JavaUtf8Invocation.inspect(replacementLaunch.physicalArguments(), carrier, vmOptions));
        original.verify();
        // This checks the actual binary transport only. No process identity or current capture is invented.
        assertThrows(IOException.class, () -> CompiledGoldenCapture.requireCurrentInvocation(
                batch("fixture-machine").captures().getFirst(), null, limits(), null, null));
    }

    private CompiledGoldenCapture.Limits limits() {
        return new CompiledGoldenCapture.Limits(temporary.toAbsolutePath().normalize().toString(), temporary.toAbsolutePath().normalize().toString(),
                Instant.now().plusSeconds(30).toString(), 30, 128L << 20);
    }
    private CompiledGoldenCapture.Batch batch(String machine) {
        List<CompiledGoldenCapture.Request> requests = new ArrayList<>(); List<CompiledGoldenCapture.ProfileBinding> bindings = new ArrayList<>();
        for (var launcher : CompiledCaptureInputProfile.Launcher.values()) {
            String id = launcher.name().toLowerCase(java.util.Locale.ROOT).replace('_', '-'); var profile = profile(launcher);
            requests.add(request(id, profile, profile.runtimeClassRefs())); bindings.add(new CompiledGoldenCapture.ProfileBinding(id, profile));
        }
        return new CompiledGoldenCapture.Batch(CompiledGoldenCapture.BATCH_SCHEMA, machine, requests, bindings);
    }
    private CompiledGoldenCapture.Request request(String id, CompiledCaptureInputProfile.Profile profile, List<ControlBuild.FileRef> inputs) {
        List<String> command = new ArrayList<>(List.of(temporary.resolve("never-run.exe").toString(), "-Xms16m", "-Xmx64m",
                "-Dxar.capture.classRoot=" + profile.classRoot(), "-cp", profile.classRoot(), profile.launcher().binaryName()));
        for (int index = 0; index < profile.launcher().argumentCount() - 1; index++) command.add(temporary.resolve(id + "-arg" + index).toString());
        Path output = temporary.resolve(id + "-output.json"); command.add(output.toString());
        return new CompiledGoldenCapture.Request(id, command, temporary.toString(), List.of(ref(temporary.resolve("source.java"))), inputs, output.toString(), 65536);
    }
    private CompiledCaptureInputProfile.Profile profile(CompiledCaptureInputProfile.Launcher launcher) {
        Path root = temporary.toAbsolutePath().normalize().resolve("classes");
        return new CompiledCaptureInputProfile.Profile(CompiledCaptureInputProfile.Kind.QUALIFIED_TEST_CLASSES_V1, launcher,
                ref(temporary.resolve("capture.json")), ref(temporary.resolve("compilation.json")), ref(temporary.resolve("caller.json")),
                ref(temporary.resolve("compiler.json")), root.toString(), launcher.runtimeBinaryNames().stream()
                        .map(name -> ref(root.resolve(name.replace('.', '/') + ".class"))).toList());
    }
    private static CompiledGoldenCapture.Batch withBindings(CompiledGoldenCapture.Batch batch, List<CompiledGoldenCapture.ProfileBinding> bindings) {
        return new CompiledGoldenCapture.Batch(batch.schema(), batch.machineId(), batch.captures(), bindings);
    }
    private static ControlBuild.FileRef ref(Path path) { return new ControlBuild.FileRef(path.toAbsolutePath().normalize().toString(), 1, "0".repeat(64)); }
    private static ObjectNode json(CompiledGoldenCapture.Batch value) throws IOException {
        return ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(value), ObjectNode.class);
    }
    private static CompiledGoldenCapture.Batch parse(ObjectNode value) throws IOException {
        return CompiledGoldenCapture.parseBatch(ControlBuild.strictMapper().writeValueAsBytes(value));
    }
}
