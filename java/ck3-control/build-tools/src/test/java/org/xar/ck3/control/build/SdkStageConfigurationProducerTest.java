package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class SdkStageConfigurationProducerTest {
    @TempDir Path root;
    private FileRef pin(String name) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, "synthetic metadata source, never a host proof"); return FileRef.measure(path);
    }
    private SdkSourceAssembly.ProducerReuse reuse() {
        return new SdkSourceAssembly.ProducerReuse("tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py",
                "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1",
                "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1");
    }
    private SdkSourceAssembly.Request template(FileRef source, FileRef priorReceipt) {
        String producer = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
        var protectedRoots = List.of(new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_SDK, root.resolve("frozen-sdk").toString()),
                new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_HOST, root.resolve("frozen-host").toString()),
                new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_RUNTIME, root.resolve("frozen-runtime").toString()));
        return new SdkSourceAssembly.Request(SdkSourceAssembly.REQUEST_SCHEMA, "fixture-machine", root.toString(), "a".repeat(40), root.toString(),
                root.resolve("old-output").toString(), root.resolve("frozen-sdk").toString(), "ck3_autonomous_player/src",
                List.of(".", "ck3_autonomous_player/src"), List.of(root.toString()), protectedRoots,
                List.of(new SdkSourceAssembly.Source(producer, SdkSourceAssembly.SourceRole.PRODUCER, SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, source, List.of()),
                        new SdkSourceAssembly.Source("ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py", SdkSourceAssembly.SourceRole.SDK_SOURCE,
                                SdkSourceAssembly.InputOrigin.FROZEN_SDK_SOURCE, source, List.of())),
                List.of(new SdkSourceAssembly.ImportRoute("tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", producer,
                        SdkSourceAssembly.ImportSourceLocation.FRESH_GRAPH, true)),
                List.of(new SdkSourceAssembly.Deployment("old-service", priorReceipt, ControlBuild.TargetKind.SERVICE_FAST_JAR)), reuse(), 8L << 20);
    }
    private SdkStageConfigurationProducer.ProductionInputs inputs() throws IOException {
        var ref = pin("inputs.pin");
        var frozen = new SdkSourceAssembly.Source32Reuse(ref, new FileRef(root.resolve("exact-source32-exporter.java").toString(), 1,
                "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432"));
        var constraint = new SdkSourceAssembly.LegacyConstraint("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                new SdkSourceAssembly.Digest(ref.bytes(), ref.sha256()), "tools/g2_saved_campaign/test_current_saved_basis_v1.py",
                new SdkSourceAssembly.Digest(ref.bytes(), ref.sha256()));
        var interpreter = new SdkStageConfigurationProducer.InterpreterInputs(ref, ref, List.of(root.toString()), List.of(ref));
        var fresh = new SdkStageConfigurationProducer.FreshInputs(ref, List.of(ref), ref,
                List.of(new SdkStageConfigurationProducer.ModulePath("xar_autoplayer.campaign_development_score_v1",
                        "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py")), 64L << 20, 60);
        var canonical = new SdkStageConfigurationProducer.CanonicalInputs(ref, ref, ref, List.of(ref), ref, 64L << 20, 60);
        return new SdkStageConfigurationProducer.ProductionInputs(SdkStageConfigurationProducer.SCHEMA, "fixture-machine",
                Instant.now().plusSeconds(300).toString(), ref, ref, ref, constraint, frozen, 32L << 20, 4096, 4096,
                ref, ref, List.of(), interpreter, fresh, canonical, List.of());
    }
    @Test void postReactorRebindingChangesOnlyNewOutputAndActualDeployment() throws Exception {
        var source = pin("source.py"); var old = pin("old-receipt.json"); var actual = pin("new-receipt.json");
        var original = template(source, old);
        for (String view : List.of("baseline", "legacy", "consumer")) {
            Path output = root.resolve("new-views").resolve(view);
            var rebound = SdkStageConfigurationProducer.rebind(original, output, actual, ControlBuild.TargetKind.SERVICE_FAST_JAR);
            assertEquals(output.toString(), rebound.outputRoot()); assertEquals(original.sources(), rebound.sources());
            assertEquals(original.importRoutes(), rebound.importRoutes()); assertEquals(original.protectedRoots(), rebound.protectedRoots());
            assertEquals(original.producerReuse(), rebound.producerReuse()); assertEquals(original.sdkInputRoot(), rebound.sdkInputRoot());
            assertEquals(List.of(new SdkSourceAssembly.Deployment("current-reactor", actual, ControlBuild.TargetKind.SERVICE_FAST_JAR)), rebound.deployments());
            assertEquals(SdkSourceAssembly.SourceRole.SDK_SOURCE, rebound.sources().getLast().role());
        }
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.requireIndependentOutput(root.resolve("artifacts/new-output"), List.of(original), List.of()));
        assertEquals(old, original.deployments().getFirst().actualBuildReceipt()); assertFalse(Files.exists(root.resolve("new-views")));
        Path sources = Files.createDirectory(root.resolve("reactor-source")), compiled = Files.createDirectory(root.resolve("reactor-snapshot"));
        String relative = "g2-research/M0ResearchV1.java"; byte[] raw = "synthetic Java ABI, not a running program".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var required = List.of(new SdkSourceIntent.RequiredReactorSource(relative, SdkSourceAssembly.Digest.of(raw)));
        List<FileRef> actuals = new ArrayList<>();
        for (Path tree : List.of(sources, compiled)) {
            Path file = tree.resolve(relative); Files.createDirectories(file.getParent()); Files.write(file, raw);
            FileRef ref = FileRef.measure(file); actuals.add(ref); SdkStageConfigurationProducer.requireReactorSources(required, tree, List.of(ref));
        }
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.requireReactorSources(required, sources, List.of()));
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.requireReactorSources(required, compiled, List.of(actuals.getFirst())));
        var nativeSource = new SdkSourceAssembly.Source("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                SdkSourceAssembly.SourceRole.SDK_SOURCE, SdkSourceAssembly.InputOrigin.FROZEN_SDK_SOURCE, source, List.of());
        var intent = SdkStageConfigurationProducer.nativeDriverIntent(List.of(nativeSource), source);
        assertEquals(intent.parentContent(), intent.selectedContent());
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.nativeDriverIntent(List.of(nativeSource), old));
        Files.writeString(Path.of(actuals.getLast().path()), "different compiled Java ABI");
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.requireReactorSources(required, compiled, List.of(actuals.getLast())));
    }
    @Test void productionIntentJsonIsClosedTypedAndPreservesNineteenPlanReference() throws Exception {
        var value = inputs(); var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(value);
        assertEquals(value, mapper.readValue(raw, SdkStageConfigurationProducer.ProductionInputs.class));
        for (String wrong : List.of(raw.replace("\"allocation_unit_bytes\":4096", "\"allocation_unit_bytes\":true"),
                raw.replace("\"allocation_unit_bytes\":4096", "\"allocation_unit_bytes\":4096.0"),
                raw.replace("\"allocation_unit_bytes\":4096", "\"allocation_unit_bytes\":\"4096\""),
                raw.replace("\"producer_golden_plan_ref\"", "\"optional_old_plan_ref\""),
                raw.replace("\"qualified_tools_build_ref\"", "\"optional_old_tools_ref\""),
                raw.replace("\"qualified_tools_build_ref\":{", "\"qualified_tools_build_ref\":null,\"unknown\":{"),
                raw.replace("\"producer_golden_plan_ref\":{", "\"producer_golden_plan_ref\":null,\"unknown\":{"),
                raw.replace(SdkStageConfigurationProducer.SCHEMA, "old-producer/v0"))) {
            assertNotEquals(raw, wrong); Path path = root.resolve("wrong.json"); Files.writeString(path, wrong);
            assertThrows(IOException.class, () -> SdkStageConfigurationProducer.readInputs(FileRef.measure(path)));
        }
        assertThrows(IllegalArgumentException.class, () -> new SdkStageConfigurationProducer.ModulePath("xar_autoplayer.score", "../score.py"));
        Path rejected = root.resolve("wrong-machine-input.json");
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.writeInputs(value, rejected, pending -> { }));
        assertFalse(Files.exists(rejected));
        assertEquals(value.producerGoldenPlanRef(), value.qualifiedToolsBuildRef());
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.qualifiedToolsInputs(value.qualifiedToolsBuildRef(), value.machineId()));
        assertFalse(Files.exists(root.resolve("metadata")));
        var originalBinding = new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32,
                value.source32Reuse().baseFreezeRef(), null);
        assertEquals(originalBinding, mapper.readValue(mapper.writeValueAsBytes(originalBinding), RootSoftwareChildBootstrap.SdkLineageBinding.class));
        var derivedBinding = new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32,
                value.source32Reuse().baseFreezeRef(), value.qualifiedToolsBuildRef());
        assertEquals(derivedBinding, mapper.readValue(mapper.writeValueAsBytes(derivedBinding), RootSoftwareChildBootstrap.SdkLineageBinding.class));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareChildBootstrap.SdkLineageBinding(
                RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32, value.source32Reuse().baseFreezeRef(), null));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareChildBootstrap.SdkLineageBinding(
                RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32, value.source32Reuse().baseFreezeRef(), value.qualifiedToolsBuildRef()));
        assertEquals("xar_autoplayer.campaign_development_score_v1", value.fresh().additionalModules().getFirst().module());
    }
    @Test void beforeImportEnvironmentUsesActualSelectedGraphAndRejectsOldOrMissingFixtures() throws Exception {
        Path graph = Files.createDirectory(root.resolve("consumer")), wire = Files.createDirectory(root.resolve("wire"));
        var client = pin("client.py");
        var environment = SdkStageConfigurationProducer.environment(List.of(new RootSoftwareChildBootstrap.Environment("CK3_M7_FORMAL_NATIVE_WIRE_DIR", wire.toString())),
                graph.toString(), root.toString(), client);
        assertEquals(7, environment.size());
        assertEquals(graph.toString(), environment.stream().filter(row -> row.name().equals("XAR_CROWN_JAVA_RUNTIME_SOURCE_ROOT")).findFirst().orElseThrow().value());
        assertEquals(client.path(), environment.stream().filter(row -> row.name().equals("XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE")).findFirst().orElseThrow().value());
        assertEquals(3, environment.stream().filter(row -> row.name().startsWith("XAR_CURRENT_SAVED_") && row.value().equals(graph.toString())).count());
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.environment(List.of(), graph.toString(), root.toString(), client));
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.environment(List.of(
                new RootSoftwareChildBootstrap.Environment("XAR_CROWN_JAVA_RUNTIME_SOURCE_ROOT", root.resolve("old-graph").toString())), graph.toString(), root.toString(), client));
    }
    @Test void liveCapacityPortPreservesExplicitUnitsDeadlineAndResourceFailure() throws Exception {
        var inputs = inputs(); var evidence = pin("storage.json"); var checks = new AtomicInteger();
        var permit = new SdkSourceAssembly.WritePermit(inputs.machineId(), root.toString(), Instant.now().plusSeconds(60).toString(),
                inputs.sharedViewPhysicalHardBytes(), 4096, 4096, evidence);
        var gate = new SdkSourceAssembly.SharedCapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.SharedQuote quote, FileRef request) { return permit; }
            @Override public void revalidate(SdkSourceAssembly.WritePermit value, long consumed) { assertSame(permit, value); assertEquals(123, consumed); checks.incrementAndGet(); }
        };
        var wrapped = SdkStageConfigurationProducer.boundedGate(inputs, gate, pending -> checks.incrementAndGet());
        assertSame(permit, wrapped.acquire(null, evidence)); wrapped.revalidate(permit, 123); assertEquals(3, checks.get());
        var wrongUnits = new SdkSourceAssembly.SharedCapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.SharedQuote quote, FileRef request) {
                return new SdkSourceAssembly.WritePermit(inputs.machineId(), root.toString(), inputs.reviewAtUtc(), inputs.sharedViewPhysicalHardBytes(), 8192, 4096, evidence);
            }
            @Override public void revalidate(SdkSourceAssembly.WritePermit value, long consumed) { fail("Rejected permit cannot be reused"); }
        };
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.boundedGate(inputs, wrongUnits, pending -> { }).acquire(null, evidence));
        assertThrows(IOException.class, () -> SdkStageConfigurationProducer.boundedGate(inputs, gate, pending -> { throw new IOException("actual Root guard failed"); }).acquire(null, evidence));
    }

    @Test void coldParentCountSelectionUsesTheWholeSelectedSourceDigest() throws IOException {
        assertEquals(63, FreshSdkFixtureStage.coldParents(new SdkSourceAssembly.Digest(238249,
                "854e3788d3fd22211dc5bba41dc7cf6c36554c95535d55055da3bd107047594c")));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.coldParents(new SdkSourceAssembly.Digest(238250,
                "854e3788d3fd22211dc5bba41dc7cf6c36554c95535d55055da3bd107047594c")));
    }
}
