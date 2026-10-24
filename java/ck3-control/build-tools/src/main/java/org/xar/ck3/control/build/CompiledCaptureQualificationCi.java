package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Post-build integration checks against a genuine accepted four-row qualification.
 * Negative fixtures derive from the accepted producer's real bytes and never
 * alter any original source, class, manifest, receipt or release. Starts no child.
 */
public final class CompiledCaptureQualificationCi {
    public record Rejection(String name, String actualException) {
        public Rejection { Objects.requireNonNull(name); Objects.requireNonNull(actualException); }
    }
    public record Report(String schema, String machineId, String observedAtUtc,
            ControlBuild.FileRef acceptedQualificationRef, int actualRequestsValidated,
            int distinctFinanceRuntimeClasses, int childrenStarted, List<Rejection> rejections,
            List<ControlBuild.FileRef> negativeFixtureRefs, String scope) {
        public Report {
            if (!"xar.compiled-capture-actual-integration/v1".equals(schema) || actualRequestsValidated != 4
                    || distinctFinanceRuntimeClasses != 9 || childrenStarted != 0 || rejections.size() != 9) {
                throw new IllegalArgumentException("Complete genuine four-request/nine-class integration checks required");
            }
            rejections = List.copyOf(rejections); negativeFixtureRefs = List.copyOf(negativeFixtureRefs);
        }
    }
    @FunctionalInterface private interface Check { void run() throws IOException; }
    private CompiledCaptureQualificationCi() { }

    public static Report verify(ControlBuild.FileRef qualificationRef, Path newOutputRoot) throws IOException {
        CompiledGoldenCapture.Receipt qualification = CompiledGoldenCapture.acceptedReceipt(qualificationRef,
                CompiledGoldenCapture.Mode.QUALIFY_ONLY);
        require(qualification.batch().captures().size() == 4 && qualification.childrenStarted() == 0,
                "Actual four-request qualification with no child required");
        Path root = newOutputRoot.toAbsolutePath().normalize();
        require(newOutputRoot.equals(root) && !Files.exists(root, LinkOption.NOFOLLOW_LINKS)
                && root.getParent() != null && root.getParent().toRealPath().equals(root.getParent()),
                "New canonical integration evidence root required");
        Files.createDirectory(root);
        var mapper = ControlBuild.strictMapper();
        CompiledGoldenCapture.Batch batch = qualification.batch();
        require(batch.equals(CompiledGoldenCapture.parseBatch(mapper.writeValueAsBytes(batch))),
                "Actual batch serialization roundtrip differs");
        List<ControlBuild.FileRef> nine = qualification.observations().getFirst().before().completeFinanceRuntimeClassRefs();
        require(nine.size() == 9 && nine.stream().map(ControlBuild.FileRef::path).distinct().count() == 9,
                "Actual complete finance runtime inventory required");
        for (CompiledGoldenCapture.Observation item : qualification.observations()) {
            require(item.before().equals(mapper.readValue(mapper.writeValueAsBytes(item.before()), CompiledCaptureInputProfile.Proof.class))
                    && item.before().completeFinanceRuntimeClassRefs().equals(nine),
                    "Every actual proof must survive serialization and bind the same complete nine-class compilation");
        }
        CompiledGoldenCapture.Request row = batch.captures().getFirst();
        CompiledCaptureInputProfile.Profile profile = batch.profileFor(row.id());
        List<Rejection> rejected = new ArrayList<>(); List<ControlBuild.FileRef> fixtures = new ArrayList<>();

        ObjectNode originalCapture = object(ControlBuild.readReceiptEnvelope(profile.captureReceiptRef()));
        ObjectNode wrongMachine = originalCapture.deepCopy(); wrongMachine.put("machine_id", "negative-fixture-other-machine");
        ControlBuild.FileRef wrongMachineRef = write(root.resolve("negative-wrong-machine.json"), wrongMachine, fixtures);
        rejected.add(reject("genuine-capture-copy-wrong-machine", () -> qualify(row, with(profile, wrongMachineRef, profile.testCompilationRef(),
                profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef(), profile.runtimeClassRefs()))));

        ControlBuild.FileRef actualReleaseRef = mapper.treeToValue(originalCapture.get("capacity_release_ref"), ControlBuild.FileRef.class);
        ObjectNode expiredRelease = object(CompiledGoldenCapture.readPinned(actualReleaseRef, 65536));
        expiredRelease.put("review_at_utc", originalCapture.get("observed_at_utc").asText());
        ControlBuild.FileRef expiredReleaseRef = write(root.resolve("negative-release-closed-at-completion.json"), expiredRelease, fixtures);
        ObjectNode expiredCapture = originalCapture.deepCopy(); expiredCapture.set("capacity_release_ref", mapper.valueToTree(expiredReleaseRef));
        ControlBuild.FileRef expiredCaptureRef = write(root.resolve("negative-completion-outside-release.json"), expiredCapture, fixtures);
        rejected.add(reject("genuine-capture-copy-completion-outside-original-release", () -> qualify(row, with(profile, expiredCaptureRef, profile.testCompilationRef(),
                profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef(), profile.runtimeClassRefs()))));

        ObjectNode changedSource = originalCapture.deepCopy();
        ((ObjectNode) changedSource.path("source_pins").get(0)).put("sha256", "0".repeat(64));
        ControlBuild.FileRef changedSourceRef = write(root.resolve("negative-source-pin.json"), changedSource, fixtures);
        rejected.add(reject("genuine-capture-copy-changed-source-pin", () -> qualify(row, with(profile, changedSourceRef, profile.testCompilationRef(),
                profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef(), profile.runtimeClassRefs()))));

        ControlBuild.CaptureBuildReceipt acceptedCompiler = ControlBuild.verifiedCompletedCaptureReceipt(profile.captureReceiptRef());
        Path module = Path.of(acceptedCompiler.compiledSourceRoot()).resolve("wave2-finance");
        ObjectNode manifest = object(CompiledGoldenCapture.readPinned(profile.testCompilationRef(), 4 << 20));
        String mainSource = module.resolve("src/test/java").resolve(profile.launcher().sourceRelativePath()).toString();
        int mainIndex = -1, moduleIndex = -1;
        for (int index = 0; index < manifest.path("not_run_tests").size(); index++) {
            if (manifest.path("not_run_tests").get(index).path("source_ref").path("path").asText().equals(mainSource)) mainIndex = index;
        }
        for (int index = 0; index < manifest.path("modules").size(); index++) {
            if (manifest.path("modules").get(index).path("module_pom_ref").path("path").asText().equals(module.resolve("pom.xml").toString())) moduleIndex = index;
        }
        require(mainIndex >= 0 && moduleIndex >= 0, "Actual accepted finance main/module entries required");
        ObjectNode missingEntry = manifest.deepCopy(); ((ArrayNode) missingEntry.path("not_run_tests")).remove(mainIndex);
        rejected.add(rejectManifest(root, "missing-actual-finance-compiler-entry", missingEntry, acceptedCompiler, module, profile, fixtures));
        ObjectNode changedClass = manifest.deepCopy();
        ObjectNode firstEntry = (ObjectNode) changedClass.path("not_run_tests").get(mainIndex);
        ((ObjectNode) firstEntry.path("compiled_class_refs").get(0)).put("sha256", "0".repeat(64));
        rejected.add(rejectManifest(root, "changed-actual-finance-class-pin", changedClass, acceptedCompiler, module, profile, fixtures));
        ObjectNode missingInventory = manifest.deepCopy();
        ObjectNode inventory = (ObjectNode) missingInventory.path("modules").get(moduleIndex).path("compiler_created_files_ref");
        inventory.put("path", root.resolve("missing-compiler-created-inventory.lst").toString());
        rejected.add(rejectManifest(root, "missing-actual-finance-created-inventory", missingInventory, acceptedCompiler, module, profile, fixtures));

        if (!profile.callerToolsReceiptRef().equals(profile.producerToolsReceiptRef())) {
            rejected.add(reject("compiler-closure-relabelled-as-current-caller", () -> qualify(row, with(profile,
                    profile.captureReceiptRef(), profile.testCompilationRef(), profile.producerToolsReceiptRef(), profile.producerToolsReceiptRef(), profile.runtimeClassRefs()))));
            rejected.add(reject("new-caller-closure-relabelled-as-original-compiler", () -> qualify(row, with(profile,
                    profile.captureReceiptRef(), profile.testCompilationRef(), profile.callerToolsReceiptRef(), profile.callerToolsReceiptRef(), profile.runtimeClassRefs()))));
        } else {
            ControlBuild.FileRef actual = profile.callerToolsReceiptRef();
            ControlBuild.FileRef changed = new ControlBuild.FileRef(actual.path(), actual.bytes(), "0".repeat(64));
            rejected.add(reject("same-deployment-independent-caller-receipt-pin-changed", () -> qualify(row, with(profile,
                    profile.captureReceiptRef(), profile.testCompilationRef(), changed, actual, profile.runtimeClassRefs()))));
            rejected.add(reject("same-deployment-independent-compiler-receipt-pin-changed", () -> qualify(row, with(profile,
                    profile.captureReceiptRef(), profile.testCompilationRef(), actual, changed, profile.runtimeClassRefs()))));
        }
        var wrongCommand = new ArrayList<>(row.command()); wrongCommand.set(5, profile.classRoot() + java.io.File.pathSeparator + root);
        var contaminated = new CompiledGoldenCapture.Request(row.id(), wrongCommand, row.cwd(), row.sourceRefs(), row.inputRefs(), row.outputPath(), row.maxOutputBytes());
        rejected.add(reject("actual-request-second-capture-classpath-root", () -> qualify(contaminated, profile)));

        // Full accepted readback after every negative, with original files untouched.
        CompiledGoldenCapture.acceptedReceipt(qualificationRef, CompiledGoldenCapture.Mode.QUALIFY_ONLY);
        for (ControlBuild.FileRef ref : fixtures) ref.verify();
        return new Report("xar.compiled-capture-actual-integration/v1", qualification.machineId(), Instant.now().toString(),
                qualificationRef, 4, 9, 0, rejected, fixtures,
                "Genuine producer/profile/serialization/consumer checks; three manifest negatives execute the shared production finance-inventory sub-boundary "
                + "after genuine whole-producer admission, without rebinding fixed manifest paths or claiming whole-receipt acceptance. Negative copies are explicitly not original receipts. "
                + "Same-deployment callers/compiler receipts are allowed and each pin is tested independently; distinct deployments exercise actual closure swaps. "
                + "No capture child, Game, service, SDK or writer admission. Actual extra caller-classpath JVM contamination remains a separate process case.");
    }

    private static Rejection rejectManifest(Path root, String name, ObjectNode manifest, ControlBuild.CaptureBuildReceipt compiler,
            Path module, CompiledCaptureInputProfile.Profile profile, List<ControlBuild.FileRef> fixtures) throws IOException {
        ControlBuild.FileRef manifestRef = write(root.resolve("negative-" + name + "-manifest.json"), manifest, fixtures);
        return reject(name, () -> CompiledCaptureInputProfile.validateFinanceCompilation(
                ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(manifestRef, 4 << 20), ControlBuild.TestCompilationManifest.class),
                Path.of(profile.classRoot()), module, compiler.compiledSourcePins()));
    }
    private static void qualify(CompiledGoldenCapture.Request row, CompiledCaptureInputProfile.Profile profile) throws IOException {
        CompiledGoldenCapture.qualify(row, profile);
    }
    private static CompiledCaptureInputProfile.Profile with(CompiledCaptureInputProfile.Profile profile,
            ControlBuild.FileRef capture, ControlBuild.FileRef manifest, ControlBuild.FileRef caller, ControlBuild.FileRef compiler,
            List<ControlBuild.FileRef> classes) {
        return new CompiledCaptureInputProfile.Profile(profile.profile(), profile.launcher(), capture, manifest, caller, compiler, profile.classRoot(), classes);
    }
    private static Rejection reject(String name, Check check) throws IOException {
        try { check.run(); } catch (IOException error) { return new Rejection(name, error.toString()); }
        throw new IOException("Genuine compiled capture negative unexpectedly admitted: " + name);
    }
    private static ObjectNode object(byte[] raw) throws IOException {
        return ControlBuild.strictMapper().readValue(raw, ObjectNode.class);
    }
    private static ControlBuild.FileRef write(Path path, ObjectNode value, List<ControlBuild.FileRef> refs) throws IOException {
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value); require(raw.length <= (4 << 20), "Finite negative evidence required");
        Files.write(path, raw, StandardOpenOption.CREATE_NEW); var ref = ControlBuild.FileRef.measure(path); refs.add(ref); return ref;
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
    public static void main(String[] args) throws IOException {
        require(args.length == 2, "Usage: CompiledCaptureQualificationCi ACCEPTED_QUALIFY_RECEIPT NEW_OUTPUT_ROOT");
        var result = verify(ControlBuild.FileRef.measure(Path.of(args[0])), Path.of(args[1]));
        byte[] json = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(result);
        Files.write(Path.of(args[1]).resolve("actual-integration.json"), json, StandardOpenOption.CREATE_NEW);
        System.out.println(ControlBuild.strictMapper().writeValueAsString(result));
    }
}
