package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.PrintWriter;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;
import org.xar.ck3.control.build.SdkSourceIntent.*;

final class ControlCiSdkPlanWriterTest {
    /** Explicit bounded regression uses the real Platform engine and the same persistent test class. */
    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("This entry runs exactly the three persistent SDK plan tests");
        var request = LauncherDiscoveryRequestBuilder.request()
                .selectors(DiscoverySelectors.selectClass(ControlCiSdkPlanWriterTest.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled", "false").build();
        var listener = new SummaryGeneratingListener();
        LauncherFactory.create().execute(request, listener);
        var summary = listener.getSummary();
        summary.printTo(new PrintWriter(System.out, true));
        summary.printFailuresTo(new PrintWriter(System.err, true));
        if (summary.getTestsFoundCount() != 3 || summary.getTestsStartedCount() != 3
                || summary.getTestsSucceededCount() != 3 || summary.getTestsFailedCount() != 0
                || summary.getTestsSkippedCount() != 0 || summary.getTestsAbortedCount() != 0
                || summary.getContainersFailedCount() != 0 || summary.getTotalFailureCount() != 0)
            throw new IllegalStateException("Expected exactly three successful persistent tests without failures, skips or aborts");
        System.out.println("PASS_CONTROL_CI_SDK_PLAN_JUNIT_3");
    }
    @TempDir Path root;
    private static final String PRODUCER = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
    private static final String SAMPLE = "ck3_autonomous_player/src/sample.py";
    private static final String EXPORTER = "tools/g2_saved_campaign/export_immutable_sdk_views_v1.py";
    private record Fixture(FileRef configurationRef, ControlCi.SdkPlanConfiguration configuration,
            PreparedIntents prepared, FileRef mutableOriginal, List<RequiredReactorSource> requirements) { }

    private static FileRef json(Path path, Object value) throws IOException {
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value)); return FileRef.measure(path);
    }
    private static FileRef text(Path path, String value) throws IOException {
        Files.writeString(path, value, StandardCharsets.UTF_8); return FileRef.measure(path);
    }
    private static FileRef actualReviewedExporter() throws IOException {
        String explicit = System.getenv("XAR_REPO_ROOT");
        Path repository = explicit == null || explicit.isBlank() ? Path.of("").toAbsolutePath().normalize() : Path.of(explicit);
        if (explicit == null || explicit.isBlank()) {
            while (repository != null && !Files.isRegularFile(repository.resolve(EXPORTER))) repository = repository.getParent();
        }
        if (repository == null || !Files.isRegularFile(repository.resolve(EXPORTER)))
            throw new IOException("The actual reviewed repository Source32 exporter is required; no synthetic replacement or skip");
        return FileRef.measure(repository.resolve(EXPORTER));
    }

    private Fixture fixture(Path directory) throws Exception {
        Files.createDirectories(directory);
        String machine = WindowsJobProcess.currentMachineId(), review = Instant.now().plusSeconds(300).toString();
        Path repository = Files.createDirectory(directory.resolve("repository"));
        Path sdk = Files.createDirectories(repository.resolve("ck3_autonomous_player/src"));
        FileRef sample = text(sdk.resolve("sample.py"), "original = 1\n");
        Path producerPath = repository.resolve(PRODUCER); Files.createDirectories(producerPath.getParent());
        FileRef producer = text(producerPath, "def compose_v1(): pass\n");
        var original = new Source(SAMPLE, SourceRole.SDK_SOURCE, InputOrigin.CURRENT_CANONICAL, sample, List.of());
        var template = new Request(SdkSourceAssembly.REQUEST_SCHEMA, machine, repository.toString(), "a".repeat(40),
                repository.toString(), directory.resolve("future-view").toString(), sdk.toString(), "ck3_autonomous_player/src",
                List.of(".", "ck3_autonomous_player/src"), List.of(repository.toString()),
                List.of(new ProtectedRoot(ProtectedRole.FROZEN_SDK, sdk.toString()),
                        new ProtectedRoot(ProtectedRole.FROZEN_HOST, directory.resolve("host").toString()),
                        new ProtectedRoot(ProtectedRole.FROZEN_RUNTIME, directory.resolve("runtime").toString())),
                List.of(original, new Source(PRODUCER, SourceRole.PRODUCER, InputOrigin.CURRENT_CANONICAL, producer, List.of())),
                List.of(new ImportRoute("tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", PRODUCER,
                        ImportSourceLocation.FRESH_GRAPH, true)),
                List.of(new Deployment("software-test-only", producer, ControlBuild.TargetKind.SERVICE_FAST_JAR)),
                new ProducerReuse(PRODUCER, "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1",
                        "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1"), 1 << 20);
        FileRef templateRef = json(directory.resolve("template.json"), template);
        FileRef selected = text(directory.resolve("selected.py"), "original = 2\n");
        var selection = new Selection(SelectionKind.REPLACE_CONTENT, "software-test", SAMPLE, SourceRole.SDK_SOURCE,
                original, selected, List.of(), List.of());
        var cohort = new Cohort("software-test", List.of(PRODUCER), List.of(SAMPLE), List.of(SAMPLE), List.of(templateRef));
        var requirements = List.of(new RequiredReactorSource("module/Actual.java", Digest.of("paired Java source\n".getBytes(StandardCharsets.UTF_8))));
        var sourcePlan = new Plan(SdkSourceIntent.PLAN_SCHEMA, machine, review, templateRef, templateRef, templateRef,
                new ReferenceInputs(List.of(), List.of()), List.of(selection), List.of(cohort), requirements);
        FileRef sourcePlanRef = json(directory.resolve("source-plan.json"), sourcePlan);
        Path intentOutput = directory.resolve("intents");
        SdkSourceIntent.main(new String[] { sourcePlanRef.path(), Long.toString(sourcePlanRef.bytes()), sourcePlanRef.sha256(),
                intentOutput.toString(), "1048576" });
        FileRef preparedRef = FileRef.measure(intentOutput.resolve("prepared-intents.json"));
        var prepared = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(preparedRef.path())), PreparedIntents.class);
        FileRef fixtureOnly = text(directory.resolve("software-only-source-input.txt"), "SOFTWARE_TEST_ONLY_NO_RUNTIME_ADMISSION");
        FileRef golden = RootSoftwareFixtureInputsProducerTest.goldenPlanFixture(directory.resolve("golden"));
        var declaration = new ControlCi.SdkPlanConfiguration(ControlCi.SDK_PLAN_CONFIGURATION_SCHEMA, preparedRef,
                new LegacyConstraint(SAMPLE, new Digest(sample.bytes(), sample.sha256()), SAMPLE, new Digest(sample.bytes(), sample.sha256())),
                new Source32Reuse(fixtureOnly, actualReviewedExporter()), 1 << 20, NativeStorageGeometry.read(directory).clusterBytes(), 4096, golden,
                new SdkStageConfigurationProducer.InterpreterInputs(fixtureOnly, fixtureOnly, List.of(directory.toString()), List.of(fixtureOnly)),
                new SdkStageConfigurationProducer.FreshInputs(fixtureOnly, List.of(fixtureOnly), fixtureOnly, List.of(), 64L << 20, 30),
                new SdkStageConfigurationProducer.CanonicalInputs(fixtureOnly, fixtureOnly, fixtureOnly, List.of(fixtureOnly), fixtureOnly, 64L << 20, 30),
                List.of());
        return new Fixture(json(directory.resolve("source-configuration.json"), declaration), declaration, prepared, selected, requirements);
    }
    private static String[] arguments(FileRef configuration, Path destination, String maximum) {
        return new String[] { "--write-sdk-production-plan", configuration.path(), Long.toString(configuration.bytes()),
                configuration.sha256(), "--output", destination.toString(), "--max-native-bytes", maximum };
    }

    @Test void actualIntentCliAndPlanCliRetainOriginalsThroughTheExistingSdkReader() throws Exception {
        var fixture = fixture(root.resolve("positive")); Path output = root.resolve("actual-sdk-plan.json");
        var invocation = ControlCi.sdkPlanWriterInvocation(arguments(fixture.configurationRef(), output, "1048576"));
        assertEquals(fixture.configurationRef(), invocation.configurationRef()); assertEquals(output, invocation.destination());
        ControlCi.main(arguments(fixture.configurationRef(), output, "1048576"));
        FileRef result = FileRef.measure(output); var plan = SdkStageConfigurationProducer.readPlan(result);
        assertEquals(SdkStageConfigurationProducer.PLAN_SCHEMA, plan.schema());
        assertEquals(WindowsJobProcess.currentMachineId(), plan.machineId());
        assertEquals(fixture.prepared().baselineIntentRef(), plan.baselineIntentRef());
        assertEquals(fixture.prepared().legacyIntentRef(), plan.legacyIntentRef());
        assertEquals(fixture.prepared().consumerIntentRef(), plan.consumerIntentRef());
        assertEquals(fixture.requirements(), plan.requiredReactorSources());
        assertEquals(fixture.configuration().source32Reuse(), plan.source32Reuse());
        assertTrue(SdkStageConfigurationProducer.planInputRefs(plan).contains(fixture.mutableOriginal()));
        var fields = (ObjectNode) ControlBuild.strictMapper().readTree(Files.readAllBytes(output));
        assertEquals(17, fields.size()); assertFalse(fields.has("qualified_tools_build_ref")); assertFalse(fields.has("reactor_build_ref"));
        assertEquals(plan, SdkStageConfigurationProducer.decodePlan(Files.readAllBytes(output)));
        Path work = Files.createDirectory(root.resolve("gate-work"));
        Path artifacts = Files.createDirectory(work.resolve("artifacts"));
        Path stage = Files.createDirectory(artifacts.resolve("sdk-stage"));
        Path group = Files.createDirectory(stage.resolve("views"));
        var inputs = new SdkStageConfigurationProducer.ProductionInputs(SdkStageConfigurationProducer.SCHEMA,
                plan.machineId(), plan.reviewAtUtc(), plan.baselineIntentRef(), plan.legacyIntentRef(), plan.consumerIntentRef(),
                plan.legacyConstraint(), plan.source32Reuse(), plan.sharedViewPhysicalHardBytes(), plan.allocationUnitBytes(),
                plan.perDirectoryGuardBytes(), plan.producerGoldenPlanRef(), result, plan.requiredReactorSources(),
                plan.interpreter(), plan.fresh(), plan.canonical(), plan.bootstrapEnvironment());
        var pin = new CiBootstrap.FilePin(result.path(), result.bytes(), result.sha256());
        var resources = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, plan.machineId(), Instant.now().toString(),
                plan.reviewAtUtc(), root.toString(), work.toString(), root.toString(), "mvn", result.path(), "sdk-plan-gate-test",
                pin, java.util.Map.of(), java.util.Map.of(), java.util.Map.of("artifacts", 8L << 20), List.of(pin), List.of(pin), false, false);
        var gate = ControlCi.sdkCapacityGate(resources, Path.of(result.path()), result, inputs, stage, pending -> {
            result.verify(); fixture.configurationRef().verify(); assertTrue(pending >= 0 && pending <= 1 << 20);
        });
        var quote = new SharedQuote(plan.machineId(), group.toString(),
                0L, // baselineCopyLogicalBytes
                0,  // reusedBaselineSourceFiles
                0L, // reusedBaselineLogicalBytes
                0L, // privateChangedLogicalBytes
                0L, // allViewLogicalBytes
                0,  // sourcePathCount
                1,  // directories
                4096L, // metadataHardBytes
                plan.sharedViewPhysicalHardBytes());
        var permit = gate.acquire(quote, result); gate.revalidate(permit, 0);
        assertEquals(NativeStorageGeometry.read(group).clusterBytes(), permit.allocationUnitBytes());
        assertEquals(plan.allocationUnitBytes(), permit.allocationUnitBytes()); permit.freshStorageEvidence().verify();
        // The gate fixture does not pass these in-memory inputs through qualifiedToolsInputs or claim a completed build.
        byte[] retained = Files.readAllBytes(output);
        assertThrows(IOException.class, () -> ControlCi.main(arguments(fixture.configurationRef(), output, "1048576")));
        assertArrayEquals(retained, Files.readAllBytes(output));
        // These retained fixture inputs validate source-plan production only, never Views, a qualified build, or Python business results.
    }

    @Test void sourceConfigurationRejectsFutureResultFieldsMissingValuesAndWrongScalars() throws Exception {
        var fixture = fixture(root.resolve("shape")); var mapper = ControlBuild.strictMapper();
        byte[] bytes = Files.readAllBytes(Path.of(fixture.configurationRef().path()));
        assertEquals(fixture.configuration(), mapper.readValue(bytes, ControlCi.SdkPlanConfiguration.class));
        var original = (ObjectNode) mapper.readTree(bytes); assertEquals(12, original.size());
        var malformed = new ArrayList<ObjectNode>();
        for (String field : List.of("prepared_intents_ref", "legacy_constraint", "source32_reuse", "producer_golden_plan_ref", "interpreter", "fresh", "canonical", "bootstrap_environment")) {
            var missing = original.deepCopy(); missing.remove(field); malformed.add(missing);
            var nil = original.deepCopy(); nil.putNull(field); malformed.add(nil);
        }
        for (String field : List.of("qualified_tools_build_ref", "reactor_build_ref", "sdk_production_plan_ref", "machine_id", "review_at_utc", "required_reactor_sources")) {
            var future = original.deepCopy(); future.put(field, "cannot override the actual producer"); malformed.add(future);
        }
        var bool = original.deepCopy(); bool.put("shared_view_physical_hard_bytes", true); malformed.add(bool);
        var floating = original.deepCopy(); floating.put("allocation_unit_bytes", 4096.0); malformed.add(floating);
        var wrong = original.deepCopy(); wrong.put("schema", SdkStageConfigurationProducer.PLAN_SCHEMA); malformed.add(wrong);
        for (int index = 0; index < malformed.size(); index++) {
            FileRef bad = json(root.resolve("invalid-" + index + ".json"), malformed.get(index));
            Path output = root.resolve("refused-" + index + ".json");
            assertThrows(IOException.class, () -> ControlCi.main(arguments(bad, output, "1048576")));
            assertFalse(Files.exists(output));
        }
    }

    @Test void receiptViewsDeadlinesChangedOriginalsAndNativeLimitsFailBeforePublication() throws Exception {
        var fixture = fixture(root.resolve("guards"));
        Path bounded = root.resolve("native-refused.json");
        Path observed = root.resolve("native-size-observation.json");
        ControlCi.main(arguments(fixture.configurationRef(), observed, "1048576"));
        long unit = NativeStorageGeometry.read(root).clusterBytes();
        long maximum = Math.addExact(unit, SharedSourceFiles.nativeFile(observed).allocatedBytes()) - 1;
        assertThrows(IOException.class, () -> ControlCi.main(arguments(fixture.configurationRef(), bounded, Long.toString(maximum))));
        assertFalse(Files.exists(bounded));
        var mapper = ControlBuild.strictMapper();
        var declaration = (ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(fixture.configurationRef().path())));
        var exchanged = new PreparedIntents(fixture.prepared().consumerIntentRef(), fixture.prepared().legacyIntentRef(),
                fixture.prepared().baselineIntentRef(), fixture.prepared().generatedRefs(), fixture.prepared().inputRefs());
        FileRef exchangedRef = json(root.resolve("exchanged-receipt.json"), exchanged);
        var crossed = declaration.deepCopy(); crossed.set("prepared_intents_ref", mapper.valueToTree(exchangedRef));
        FileRef crossedRef = json(root.resolve("exchanged-configuration.json"), crossed); Path crossedOutput = root.resolve("exchanged-plan.json");
        assertThrows(IOException.class, () -> ControlCi.main(arguments(crossedRef, crossedOutput, "1048576")));
        assertFalse(Files.exists(crossedOutput));
        var baseline = (ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(fixture.prepared().baselineIntentRef().path())));
        baseline.put("review_at_utc", Instant.now().minusSeconds(1).toString());
        FileRef expired = json(root.resolve("expired-intent.json"), baseline);
        var generated = new ArrayList<>(fixture.prepared().generatedRefs()); generated.remove(fixture.prepared().baselineIntentRef()); generated.add(expired);
        FileRef expiredReceipt = json(root.resolve("expired-receipt.json"), new PreparedIntents(expired,
                fixture.prepared().legacyIntentRef(), fixture.prepared().consumerIntentRef(), generated, fixture.prepared().inputRefs()));
        var expiredDeclaration = declaration.deepCopy(); expiredDeclaration.set("prepared_intents_ref", mapper.valueToTree(expiredReceipt));
        FileRef expiredConfiguration = json(root.resolve("expired-configuration.json"), expiredDeclaration); Path expiredOutput = root.resolve("expired-plan.json");
        assertThrows(IOException.class, () -> ControlCi.main(arguments(expiredConfiguration, expiredOutput, "1048576")));
        assertFalse(Files.exists(expiredOutput));
        Files.writeString(Path.of(fixture.mutableOriginal().path()), "changed original source\n");
        Path drifted = root.resolve("changed-source-plan.json");
        assertThrows(IOException.class, () -> ControlCi.main(arguments(fixture.configurationRef(), drifted, "1048576")));
        assertFalse(Files.exists(drifted));
        var malformed = arguments(fixture.configurationRef(), root.resolve("bad-args.json"), "true");
        assertThrows(IllegalArgumentException.class, () -> ControlCi.sdkPlanWriterInvocation(malformed));
        malformed[7] = "1048576"; malformed[5] = "relative.json";
        assertThrows(IllegalArgumentException.class, () -> ControlCi.sdkPlanWriterInvocation(malformed));
    }
}
