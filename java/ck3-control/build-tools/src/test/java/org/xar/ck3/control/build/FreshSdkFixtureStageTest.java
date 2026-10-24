package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class FreshSdkFixtureStageTest {
    @TempDir Path root;
    private static final String COLD = "tools/g2_saved_campaign/test_current_saved_campaign_cold_v1.py";
    private static final String CONTINUITY = "tools/g2_saved_campaign/test_current_saved_continuity_v1.py";
    private static final String JAVA_CONTINUITY = "tools/g2_saved_campaign/test_java_saved_continuity_v1.py";
    private static final String CROWN = "ck3_autonomous_player/tests/unit/test_crown_java_policy_consumers_v1.py";
    private static final String CROWN_ORIGINAL = "tools/g2_saved_campaign/test_pending_material_crown_schema_adapter_v1.py";
    private static final String PROJECTION = "tools/g2_saved_campaign/test_java_projection_client_v1.py";

    private FreshSdkFixtureStage.Config config(long memory, int timeout, int parents, String work) throws IOException {
        return config(memory, timeout, parents, work, List.of());
    }
    private FreshSdkFixtureStage.Config config(long memory, int timeout, int parents, String work,
            List<FreshSdkFixtureStage.ExpectedModule> additional) throws IOException {
        Path source = root.resolve("source.pin");
        if (!Files.exists(source)) Files.writeString(source, "exact source");
        var ref = ControlBuild.FileRef.measure(source);
        return new FreshSdkFixtureStage.Config(FreshSdkFixtureStage.SCHEMA, "synthetic-sdk-fixture", Instant.now().plusSeconds(60).toString(),
                root.resolve("repository").toString(), work, ref, ref, ref, ref, ref, ref, List.of(ref),
                List.of(root.resolve("dependencies").toString()), List.of(ref), ref, additional, ref, ref, memory, timeout, parents);
    }
    private FreshSdkFixtureStage.ProducerGoldenPlan goldenPlan() throws IOException {
        var mapper = ControlBuild.strictMapper(); var refs = new java.util.ArrayList<ControlBuild.FileRef>();
        for (int index = 0; index < 19; index++) {
            Path file = root.resolve("golden-" + index + ".raw"); Files.writeString(file, "original producer bytes " + index); refs.add(ControlBuild.FileRef.measure(file));
        }
        Path client = root.resolve("client.py"), test = root.resolve("client-test.py"); Files.writeString(client, "exact client"); Files.writeString(test, "exact test");
        var clientRef = ControlBuild.FileRef.measure(client); var testRef = ControlBuild.FileRef.measure(test);
        var origin = mapper.createObjectNode();
        for (String field : List.of("observed_at_utc", "status", "existing_setup_spec_ref", "setup_source_field", "framework", "golden_install", "actual_config_seam", "authority")) origin.put(field, "synthetic original handoff");
        origin.put("schema", "xar.existing-python-producer-golden-install-map/v1"); origin.put("machine_id", "synthetic-sdk-fixture");
        origin.put("observed_at_utc", Instant.now().toString()); origin.set("existing_setup_spec_ref", mapper.valueToTree(clientRef));
        origin.put("status", "EXACT_EXISTING_SETUP_HANDOFF_NO_NEW_RUNNER");
        origin.put("logical_module", "tools.g2_saved_campaign.test_java_projection_client_v1"); origin.set("test_module_ref", mapper.valueToTree(testRef));
        var classes = origin.putObject("classes"); classes.put("ProjectionClientContractTests", 49); classes.put("ProjectionClientG2ProducerGoldenTests", 4); classes.put("ProjectionClientActualJavaTests", 2);
        var rows = origin.putArray("roles"); var roles = new java.util.ArrayList<>(List.of("context_input", "context_result", "evaluate_request"));
        var vectors = new java.util.ArrayList<FreshSdkFixtureStage.ProducerGoldenVector>();
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values()) {
            roles.add("G2-" + milestone.name() + ".request"); roles.add("G2-" + milestone.name() + ".result");
            int index = milestone.ordinal() * 2 + 3; vectors.add(new FreshSdkFixtureStage.ProducerGoldenVector(milestone, refs.get(index), refs.get(index + 1)));
        }
        for (int index = 0; index < roles.size(); index++) { var row = rows.addObject(); row.put("role", roles.get(index)); row.set("ref", mapper.valueToTree(refs.get(index))); }
        Path originPath = root.resolve("original-install-map.json"); Files.write(originPath, mapper.writeValueAsBytes(origin));
        return new FreshSdkFixtureStage.ProducerGoldenPlan("xar.sdk-producer-golden-plan/v1", "synthetic-sdk-fixture", ControlBuild.FileRef.measure(originPath),
                new SdkSourceAssembly.Digest(clientRef.bytes(), clientRef.sha256()), new SdkSourceAssembly.Digest(testRef.bytes(), testRef.sha256()), refs.get(0), refs.get(1), refs.get(2), vectors);
    }
    @Test void finiteTypedConfigurationRejectsOverlapAndInvalidResourceNumbers() throws IOException {
        var valid = config(512L << 20, 300, 59, root.resolve("work").toString());
        assertEquals(59, valid.expectedColdParents());
        var refs = FreshSdkFixtureStage.producerGoldenInputs(goldenPlan());
        // Metadata collection only: measured changed native bytes explicitly select software scope.
        Path parentNative = root.resolve("parent-native.py"), selectedNative = root.resolve("selected-native.py");
        Files.writeString(parentNative, "# synthetic parent native fixture\n");
        Files.writeString(selectedNative, "# synthetic derived software fixture\n");
        var parentRef = ControlBuild.FileRef.measure(parentNative); var selectedRef = ControlBuild.FileRef.measure(selectedNative);
        var parentDigest = new SdkSourceAssembly.Digest(parentRef.bytes(), parentRef.sha256());
        var selectedDigest = new SdkSourceAssembly.Digest(selectedRef.bytes(), selectedRef.sha256());
        assertNotEquals(parentDigest, selectedDigest);
        var lineage = new SdkDerivedSource32.Lineage(SdkDerivedSource32.SCHEMA, "synthetic-sdk-fixture", Instant.now().toString(),
                refs.get(0), refs.get(1), refs.get(2), root.toString(), SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE,
                new SdkDerivedSource32.NativeDriverIntent(parentDigest, selectedDigest),
                List.of(new SdkDerivedSource32.Row("xar_autoplayer/bridge/native_driver.py", selectedDigest, "b".repeat(40), "100644")),
                List.of(new SdkDerivedSource32.Delta("xar_autoplayer/bridge/native_driver.py", parentDigest, selectedDigest)), false);
        assertEquals(SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, lineage.sourcePurpose());
        assertFalse(lineage.runtimeAdmitted());
        Path path = root.resolve("derived-source32.json"); Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(lineage));
        var derivedRef = ControlBuild.FileRef.measure(path);
        var exporter = new ControlBuild.FileRef(root.resolve("exporter.py").toString(), 1,
                "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432");
        var reuse = new SdkSourceAssembly.Source32Reuse(refs.get(5), exporter);
        var view = new SdkSourceAssembly.Source32View(SdkSourceAssembly.SourceViewRole.CONSUMER, refs.get(3), root.toString(), derivedRef, refs.get(4));
        var baseline = new SdkSourceAssembly.Source32View(SdkSourceAssembly.SourceViewRole.BASELINE, refs.get(6), root.toString(), refs.get(7), refs.get(8));
        var legacy = new SdkSourceAssembly.Source32View(SdkSourceAssembly.SourceViewRole.LEGACY, refs.get(9), root.toString(), refs.get(10), refs.get(11));
        var views = List.of(baseline, legacy, view);
        assertTrue(FreshSdkFixtureStage.source32Metadata(reuse, views).containsAll(refs.subList(0, 12)));
        assertTrue(FreshSdkFixtureStage.source32Metadata(reuse, views).containsAll(List.of(derivedRef, exporter)));
        Files.writeString(path, Files.readString(path) + " ");
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.source32Metadata(reuse, views));
        assertThrows(IllegalArgumentException.class, () -> config(32L << 20, 300, 59, root.resolve("work").toString()));
        assertThrows(IllegalArgumentException.class, () -> config(2L << 30, 300, 59, root.resolve("work").toString()));
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 0, 59, root.resolve("work").toString()));
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 300, 0, root.resolve("work").toString()));
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 300, 59, root.resolve("repository/child").toString()));
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 300, 59, "relative"));
        var consumer = new FreshSdkFixtureStage.ExpectedModule("xar_autoplayer.strategy", valid.viewsActualRef());
        assertEquals(List.of(consumer), config(512L << 20, 300, 59, root.resolve("other-work").toString(), List.of(consumer)).additionalRequiredModules());
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 300, 59, root.resolve("other-work").toString(), List.of(consumer, consumer)));
    }
    @Test void configJsonRoundTripRejectsWrongMissingExtraAndNonIntegralFields() throws IOException {
        var source = config(512L << 20, 300, 59, root.resolve("work").toString());
        var value = config(512L << 20, 300, 59, root.resolve("work").toString(), List.of(
                new FreshSdkFixtureStage.ExpectedModule("xar_autoplayer.strategy", source.viewsActualRef())));
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(value);
        assertEquals(value, mapper.readValue(raw, FreshSdkFixtureStage.Config.class));
        var malformedBootstrap = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(value));
        malformedBootstrap.put("root_bootstrap_ref", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(malformedBootstrap, FreshSdkFixtureStage.Config.class));
        for (int version : List.of(1, 2, 3, 4, 5, 6)) {
            String oldSchema = raw.replace(FreshSdkFixtureStage.SCHEMA, "xar.fresh-sdk-fixture-stage/v" + version);
            assertNotEquals(raw, oldSchema);
            assertThrows(IOException.class, () -> mapper.readValue(oldSchema, FreshSdkFixtureStage.Config.class));
        }
        var missingPlan = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(value)); missingPlan.remove("producer_golden_plan_ref");
        assertThrows(IOException.class, () -> mapper.treeToValue(missingPlan, FreshSdkFixtureStage.Config.class));
        var golden = goldenPlan(); String goldenJson = mapper.writeValueAsString(golden);
        assertTrue(goldenJson.contains("\"milestone\":\"G2-M0\""));
        assertEquals(golden, mapper.readValue(goldenJson, FreshSdkFixtureStage.ProducerGoldenPlan.class));
        assertEquals(19, FreshSdkFixtureStage.producerGoldenInputs(golden).size());
        Path planPath = root.resolve("producer-plan.json"); Files.writeString(planPath, goldenJson);
        assertEquals(golden, FreshSdkFixtureStage.readProducerGoldenPlan(ControlBuild.FileRef.measure(planPath)));
        for (String token : List.of("true", "1.0", "\"1\"", "null")) {
            var bad = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(golden));
            assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, bad.get("context_input")).set("bytes", mapper.readTree(token));
            assertThrows(IOException.class, () -> mapper.treeToValue(bad, FreshSdkFixtureStage.ProducerGoldenPlan.class));
        }
        var badGolden = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(golden)); badGolden.put("unknown_fixture", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(badGolden, FreshSdkFixtureStage.ProducerGoldenPlan.class));
        var missingGolden = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(golden)); missingGolden.remove("context_input");
        assertThrows(IOException.class, () -> mapper.treeToValue(missingGolden, FreshSdkFixtureStage.ProducerGoldenPlan.class));
        var duplicateGolden = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(golden));
        assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, duplicateGolden.get("vectors").get(1)).put("milestone", "G2-M0");
        assertThrows(IOException.class, () -> mapper.treeToValue(duplicateGolden, FreshSdkFixtureStage.ProducerGoldenPlan.class));
        for (String wrong : List.of(raw.replace("\"expected_cold_parents\":59", "\"expected_cold_parents\":true"),
                raw.replace("\"expected_cold_parents\":59", "\"expected_cold_parents\":59.0"),
                raw.replace("\"expected_cold_parents\":59", "\"unexpected_count\":59"),
                raw.replace("\"expected_cold_parents\":59", "\"expected_cold_parents\":null"))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, FreshSdkFixtureStage.Config.class));
        }
        var unrun = new FreshSdkFixtureStage.Actual(FreshSdkFixtureStage.SCHEMA, value.machineId(),
                Instant.now().toString(), Instant.now().toString(), SupplementalFixtureCi.Status.RED,
                "Not executed", value.viewsActualRef(), List.of(), List.of(), List.of(), List.of(),
                "UNKNOWN", FreshSdkFixtureStage.StartupProbeScope.NOT_RUN,
                FreshSdkFixtureStage.CanonicalStepScope.NOT_RUN);
        String receipt = mapper.writeValueAsString(unrun);
        assertEquals(unrun, mapper.readValue(receipt, FreshSdkFixtureStage.Actual.class));
        String falseQualification = receipt.replace("\"canonical_thirty_command_step\":\"NOT_RUN\"",
                "\"canonical_thirty_command_step\":\"PASS\"");
        assertNotEquals(receipt, falseQualification);
        assertThrows(IOException.class, () -> mapper.readValue(falseQualification, FreshSdkFixtureStage.Actual.class));
    }
    @Test void actualOriginRequiresSelectedPathEvenWhenForeignBytesAreIdentical() throws IOException {
        Path selected = root.resolve("fresh.py"), foreign = root.resolve("foreign.py"); Files.writeString(selected, "same bytes"); Files.writeString(foreign, "same bytes");
        var source = ControlBuild.FileRef.measure(selected); var other = ControlBuild.FileRef.measure(foreign);
        assertEquals(source.sha256(), other.sha256());
        var expected = List.of(new FreshSdkFixtureStage.ExpectedModule("tools.example", source));
        var consumer = new FreshSdkFixtureStage.ExpectedModule("xar_autoplayer.strategy", source);
        assertEquals(2, FreshSdkFixtureStage.requiredModules(expected, List.of(source), List.of(consumer)).size());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requiredModules(expected, List.of(other), List.of(consumer)));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requiredModules(expected, List.of(source), expected));
        var good = new FreshSdkFixtureStage.ModuleOrigin("tools.example", FreshSdkFixtureStage.OriginKind.SOURCE, selected.toString(), List.of());
        FreshSdkFixtureStage.requireModuleOrigins(expected, List.of(good));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireModuleOrigins(expected, List.of(
                new FreshSdkFixtureStage.ModuleOrigin("tools.example", FreshSdkFixtureStage.OriginKind.SOURCE, foreign.toString(), List.of()))));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireModuleOrigins(expected, List.of(good, good)));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireModuleOrigins(expected, List.of()));
        Files.writeString(selected, "changed source");
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireModuleOrigins(expected, List.of(good)));
    }
    private static SupplementalFixtureCi.PytestCounts counts(int parents, int subtests) {
        return new SupplementalFixtureCi.PytestCounts(parents + subtests, parents, parents, 0, 0, 0, subtests, 0, 0, 0, 0,
                List.of(new SupplementalFixtureCi.ModuleCount(COLD, parents)));
    }
    private static void projectionXml(Path xml, int contract, int golden, int actual, String module) throws IOException {
        StringBuilder body = new StringBuilder("<testsuite>");
        var classes = List.of("ProjectionClientContractTests", "ProjectionClientG2ProducerGoldenTests", "ProjectionClientActualJavaTests");
        var counts = List.of(contract, golden, actual);
        for (int group = 0; group < classes.size(); group++) for (int index = 0; index < counts.get(group); index++)
            body.append("<testcase classname=\"").append(module).append('.').append(classes.get(group)).append("\" name=\"test_").append(index).append("\"/>");
        Files.writeString(xml, body.append("</testsuite>").toString());
    }
    @Test void completeColdAndIndependentContinuationKeepSeparateActualParentCounts() throws IOException {
        FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, counts(59, 3), 59);
        FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION, counts(1, 3), 59);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, counts(58, 0), 59));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION, counts(59, 0), 59));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.IMPORT_PROBE, counts(1, 0), 59));
        var warm = new SupplementalFixtureCi.PytestCounts(62, 62, 62, 0, 0, 0, 0, 0, 0, 0, 0,
                List.of(new SupplementalFixtureCi.ModuleCount(CROWN, 2), new SupplementalFixtureCi.ModuleCount(CROWN_ORIGINAL, 2),
                        new SupplementalFixtureCi.ModuleCount(CONTINUITY, 2), new SupplementalFixtureCi.ModuleCount(JAVA_CONTINUITY, 1), new SupplementalFixtureCi.ModuleCount(PROJECTION, 55)));
        FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, warm, 59);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, counts(3, 0), 59));
        var oldPair = new SupplementalFixtureCi.PytestCounts(3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0,
                List.of(new SupplementalFixtureCi.ModuleCount(CONTINUITY, 2), new SupplementalFixtureCi.ModuleCount(JAVA_CONTINUITY, 1)));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, oldPair, 59));
        var wrongOrder = new SupplementalFixtureCi.PytestCounts(62, 62, 62, 0, 0, 0, 0, 0, 0, 0, 0,
                List.of(warm.modules().get(1), warm.modules().get(0), warm.modules().get(2), warm.modules().get(3), warm.modules().get(4)));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, wrongOrder, 59));
        var truncated = new SupplementalFixtureCi.PytestCounts(60, 60, 60, 0, 0, 0, 0, 0, 0, 0, 0,
                List.of(warm.modules().get(0), warm.modules().get(1), warm.modules().get(2), warm.modules().get(3), new SupplementalFixtureCi.ModuleCount(PROJECTION, 53)));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, truncated, 59));
        var skipped = new SupplementalFixtureCi.PytestCounts(62, 62, 61, 0, 0, 1, 0, 0, 0, 0, 0, warm.modules());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, skipped, 59));
        Path graph = root.resolve("graph"), xml = root.resolve("pytest.xml"), temporary = root.resolve("temporary");
        assertEquals(graph.resolve(COLD).toString(), FreshSdkFixtureStage.pytestArguments(FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, graph, xml, temporary).getLast());
        assertEquals(graph.resolve(COLD) + "::CurrentSavedSdkPersistenceTests::test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations",
                FreshSdkFixtureStage.pytestArguments(FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION, graph, xml, temporary).getLast());
        var warmArguments = FreshSdkFixtureStage.pytestArguments(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, graph, xml, temporary);
        assertEquals(List.of(graph.resolve(CROWN).toString(), graph.resolve(CROWN_ORIGINAL).toString(), graph.resolve(CONTINUITY).toString(),
                graph.resolve(JAVA_CONTINUITY).toString(), graph.resolve(PROJECTION).toString()), warmArguments.subList(warmArguments.size() - 5, warmArguments.size()));
        assertTrue(warmArguments.contains("--rootdir=" + graph));
        String module = "tools.g2_saved_campaign.test_java_projection_client_v1";
        projectionXml(xml, 49, 4, 2, module); FreshSdkFixtureStage.requireProjectionClientClasses(xml);
        projectionXml(xml, 49, 4, 0, module); assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireProjectionClientClasses(xml));
        projectionXml(xml, 48, 5, 2, module); assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireProjectionClientClasses(xml));
        projectionXml(xml, 49, 4, 2, "foreign." + module); assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireProjectionClientClasses(xml));
        var sdk = root.resolve("sdk").toString(); var repository = root.resolve("repository").toString(); var dependencies = List.of(root.resolve("dependencies").toString());
        assertEquals(List.of(graph.toString(), sdk, graph.resolve("ck3_autonomous_player/tests/unit").toString(),
                graph.resolve("tools/g2_saved_campaign").toString(), repository, dependencies.getFirst()),
                FreshSdkFixtureStage.importRoots(FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, graph.toString(), sdk, repository, dependencies));
        for (var stage : List.of(FreshSdkFixtureStage.Stage.IMPORT_PROBE, FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION)) {
            assertEquals(List.of(graph.toString(), sdk, repository, dependencies.getFirst()),
                    FreshSdkFixtureStage.importRoots(stage, graph.toString(), sdk, repository, dependencies));
        }
        assertEquals(List.of(FreshSdkFixtureStage.Stage.IMPORT_PROBE, FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE,
                FreshSdkFixtureStage.Stage.COMPLETE_CONTINUITY_FILES, FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION), List.of(FreshSdkFixtureStage.Stage.values()));
    }

    @Test void wholeScoreReceiptRejectsNamedSubsetSkippedAndReferenceOnlyEvidence() throws IOException {
        Path file = root.resolve("selected-score.py"); Files.writeString(file, "exact selected fixture");
        var ref = ControlBuild.FileRef.measure(file); var module = new FreshSdkFixtureStage.ExpectedModule("xar_autoplayer.campaign_development_score_v1", ref);
        var expected = new FreshSdkFixtureStage.ScoreInputs(module, module, List.of(), ref, ref);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireScoreConsumers(null, expected));
        for (int found : List.of(7, 17, 19)) {
            var subset = new FreshSdkFixtureStage.ScoreConsumersObservation("xar.sdk-score-whole-consumers/v1", "FULL_SOFTWARE",
                    found, found, found, 0, 0, 0, 1, true, true, true, "MATCH", expected, null);
            assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireScoreConsumers(subset, expected));
        }
        var skipped = new FreshSdkFixtureStage.ScoreConsumersObservation("xar.sdk-score-whole-consumers/v1", "FULL_SOFTWARE",
                18, 18, 17, 0, 0, 1, 1, true, true, true, "MATCH", expected, null);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireScoreConsumers(skipped, expected));
        var reference = new FreshSdkFixtureStage.ScoreConsumersObservation("xar.sdk-score-whole-consumers/v1", "REFERENCE_ONLY",
                18, 18, 18, 0, 0, 0, 0, true, false, false, "MATCH", expected, null);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireScoreConsumers(reference, expected));
    }
    @Test void completeConsumerGroupsKeepSeparateWholeModuleCounts() throws IOException {
        var modules = java.util.stream.IntStream.range(0, 11).mapToObj(index -> "whole/test_" + index + ".py").toList();
        var input = new FreshSdkFixtureStage.ConsumerGroupInput(FreshSdkFixtureStage.ConsumerGroupKind.M7_WHOLE11,
                modules, List.of(), List.of(), "stdout", "stderr", "junit");
        var parents = modules.stream().map(path -> new SupplementalFixtureCi.ModuleCount(path, 1)).toList();
        var whole = new SupplementalFixtureCi.PytestCounts(11, 11, 11, 0, 0, 0, 0, 0, 0, 0, 0, parents);
        FreshSdkFixtureStage.requireConsumerCounts(input, whole);
        var missing = new SupplementalFixtureCi.PytestCounts(10, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, parents.subList(0, 10));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireConsumerCounts(input, missing));
        var m0 = new FreshSdkFixtureStage.ConsumerGroupInput(FreshSdkFixtureStage.ConsumerGroupKind.M0_CURRENT_WHOLE90,
                modules, List.of(), List.of(), "stdout", "stderr", "junit");
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireConsumerCounts(m0, whole));
    }

    @Test void canonicalCurrentClientExtendsAllFifteenSharedProducerImports() throws IOException {
        Path clientPath = root.resolve("current-client.py"), foreignPath = root.resolve("foreign-client.py");
        Files.writeString(clientPath, "same current client bytes"); Files.writeString(foreignPath, "same current client bytes");
        var current = ControlBuild.FileRef.measure(clientPath); var foreign = ControlBuild.FileRef.measure(foreignPath);
        var originals = java.util.stream.IntStream.range(0, 15)
                .mapToObj(index -> new FreshSdkFixtureStage.ExpectedModule("tools.original_" + index, current)).toList();
        var all = new java.util.ArrayList<>(originals);
        all.add(new FreshSdkFixtureStage.ExpectedModule("tools.g2_saved_campaign.java_map_admission_client_v1", current));
        assertEquals(all, FreshSdkFixtureStage.requireSharedProducerModules(all, current));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireSharedProducerModules(originals, current));
        var missingOriginal = new java.util.ArrayList<>(all); missingOriginal.removeFirst();
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireSharedProducerModules(missingOriginal, current));
        var foreignClient = new java.util.ArrayList<>(originals);
        foreignClient.add(new FreshSdkFixtureStage.ExpectedModule("tools.g2_saved_campaign.java_map_admission_client_v1", foreign));
        assertEquals(current.sha256(), foreign.sha256());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireSharedProducerModules(foreignClient, current));
        var duplicate = new java.util.ArrayList<>(all); duplicate.add(all.getLast());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireSharedProducerModules(duplicate, current));
    }

    @Test void wholeColdCountFollowsExactReviewedSourceIncludingFourInstalledSdkTests() throws IOException {
        var original = new SdkSourceAssembly.Digest(232879, "4f6f984f1c2d7b70c1a707491ef1d4fc3828f230a2e5bf0337a257562bd65ae0");
        var installed = new SdkSourceAssembly.Digest(238249, "854e3788d3fd22211dc5bba41dc7cf6c36554c95535d55055da3bd107047594c");
        assertEquals(59, FreshSdkFixtureStage.coldParents(original)); assertEquals(63, FreshSdkFixtureStage.coldParents(installed));
        FreshSdkFixtureStage.requireColdSourceCount(63, installed);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireColdSourceCount(59, installed));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireColdSourceCount(63, original));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.coldParents(new SdkSourceAssembly.Digest(238249, "a".repeat(64))));
        FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, counts(63, 0), 63);
        FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.INDEPENDENT_CONTINUATION, counts(1, 0), 63);
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireCounts(FreshSdkFixtureStage.Stage.COMPLETE_COLD_FILE, counts(59, 0), 63));
        assertEquals(63, config(512L << 20, 300, 63, root.resolve("work").toString()).expectedColdParents());
        assertThrows(IllegalArgumentException.class, () -> config(512L << 20, 300, 64, root.resolve("work").toString()));
    }

    @Test void budgetHttpReceiptCannotSubstituteForCompleteCurrentConsumers() throws IOException {
        Path file = root.resolve("budget-source.py"); Files.writeString(file, "selected source");
        var ref = ControlBuild.FileRef.measure(file); var module = new FreshSdkFixtureStage.ExpectedModule("xar_autoplayer.war_emergency_budget_v1", ref);
        var inputs = new FreshSdkFixtureStage.BudgetInputs(module, module, List.of(), ref, ref, ref, List.of());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireBudgetConsumers(null, inputs));
        var reference = new FreshSdkFixtureStage.BudgetConsumersObservation("xar.sdk-budget-whole-consumers/v1", "REFERENCE_ONLY",
                inputs, List.of(), true, false, "MATCH");
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireBudgetConsumers(reference, inputs));
        // Use the complete-file paths selected by the production budget consumer group.
        var paths = List.of(
                "ck3_autonomous_player/tests/unit/test_war_emergency_budget_v1.py",
                "ck3_autonomous_player/tests/unit/test_war_crisis_spend_down_v1.py",
                "ck3_autonomous_player/tests/unit/test_war_political_survival_stakes_v1.py");
        for (String invalid : List.of("unit/budget.py", paths.get(0) + "::test_selected")) {
            assertThrows(IllegalArgumentException.class, () -> new SupplementalFixtureCi.ModuleCount(invalid, 20));
        }
        var group = new FreshSdkFixtureStage.ConsumerGroupInput(FreshSdkFixtureStage.ConsumerGroupKind.BUDGET_COMPLETE_FILES,
                paths, List.of(), List.of(), "stdout", "stderr", "xml");
        // Synthetic counts check the inventory contract; they do not assert historical test execution.
        var whole = new SupplementalFixtureCi.PytestCounts(59, 59, 59, 0, 0, 0, 0, 0, 0, 0, 0,
                List.of(new SupplementalFixtureCi.ModuleCount(paths.get(0), 20), new SupplementalFixtureCi.ModuleCount(paths.get(1), 20), new SupplementalFixtureCi.ModuleCount(paths.get(2), 19)));
        FreshSdkFixtureStage.requireConsumerCounts(group, whole);
        var partial = new SupplementalFixtureCi.PytestCounts(40, 40, 40, 0, 0, 0, 0, 0, 0, 0, 0, whole.modules().subList(0, 2));
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireConsumerCounts(group, partial));
        var skipped = new SupplementalFixtureCi.PytestCounts(59, 59, 58, 0, 0, 1, 0, 0, 0, 0, 0, whole.modules());
        assertThrows(IOException.class, () -> FreshSdkFixtureStage.requireConsumerCounts(group, skipped));
    }
}
