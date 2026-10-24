package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Baseline;
import org.xar.ck3.control.build.CompleteSourceGraph.Component;
import org.xar.ck3.control.build.CompleteSourceGraph.ComponentSelection;
import org.xar.ck3.control.build.CompleteSourceGraph.Overlay;
import org.xar.ck3.control.build.CompleteSourceGraph.Plan;
import org.xar.ck3.control.build.CompleteSourceGraph.Preimage;
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectionStatus;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class CompleteSourceGraphTest {
    @TempDir Path temporary;
    private static final String PRODUCER = "g2-research/src/main/resources/producer.json";
    private static final String CONSUMER = "g2-research/src/test/resources/consumer.json";

    private record Fixture(Path root, FileRef inventory, FileRef provenance, FileRef producer, FileRef consumer) { }
    private Fixture fixture(String name, Profile profile) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name));
        StringBuilder moduleXml = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(profile)) {
            moduleXml.append("<module>").append(module).append("</module>");
            Path path = Files.createDirectory(root.resolve(module));
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools"
                    : module.equals("local-service") ? "ck3-control-local-service" : module;
            Files.writeString(path.resolve("pom.xml"), "<project xmlns='http://maven.apache.org/POM/4.0.0'>"
                    + "<modelVersion>4.0.0</modelVersion><artifactId>" + artifact + "</artifactId></project>");
        }
        Files.writeString(root.resolve("pom.xml"), "<project xmlns='http://maven.apache.org/POM/4.0.0'>"
                + "<modelVersion>4.0.0</modelVersion><artifactId>ck3-control-parent</artifactId><modules>"
                + moduleXml + "</modules></project>");
        String producerTarget = profile.completeG2() ? PRODUCER : "contracts/src/main/resources/producer.json";
        String consumerTarget = profile.completeG2() ? CONSUMER : "contracts/src/test/resources/consumer.json";
        Path producer = root.resolve(producerTarget), consumer = root.resolve(consumerTarget);
        Files.createDirectories(producer.getParent()); Files.createDirectories(consumer.getParent());
        Files.writeString(producer, "{\"value\":1}"); Files.writeString(consumer, "{\"value\":1}");
        Path inventory = temporary.resolve(name + ".json.gz");
        List<FileRef> pins = ControlBuild.sourceManifest(root, profile.sourceLimitProfile());
        try (var output = new GZIPOutputStream(Files.newOutputStream(inventory))) {
            output.write(ControlBuild.strictMapper().writeValueAsBytes(pins));
        }
        Path provenance = temporary.resolve(name + ".owner.json");
        Files.writeString(provenance, "{\"kind\":\"test-owner-source-selection\"}");
        return new Fixture(root, FileRef.measure(inventory), FileRef.measure(provenance),
                FileRef.measure(producer), FileRef.measure(consumer));
    }
    private List<ComponentSelection> selections(Fixture fixture) {
        List<ComponentSelection> selections = new ArrayList<>();
        for (Component component : Component.values()) {
            List<SelectedFile> files = component == Component.BUILD_TOOLS
                    ? List.of(new SelectedFile("build-tools/pom.xml", measure(fixture.root().resolve("build-tools/pom.xml"))))
                    : component == Component.M2
                            ? List.of(new SelectedFile(PRODUCER, fixture.producer()), new SelectedFile(CONSUMER, fixture.consumer()))
                            : List.of(new SelectedFile(CONSUMER, fixture.consumer()));
            selections.add(new ComponentSelection(component, fixture.provenance(), files));
        }
        return List.copyOf(selections);
    }
    private static FileRef measure(Path path) {
        try { return FileRef.measure(path); } catch (IOException error) { throw new IllegalStateException(error); }
    }
    private Plan plan(Fixture fixture, List<ComponentSelection> selections, List<Overlay> overlays) {
        return new Plan(CompleteSourceGraph.PLAN_SCHEMA, "test-machine", "2026-10-23T00:00:00Z",
                SelectionStatus.SOURCE_SELECTION_ONLY, Profile.G2_RESEARCH_20261023,
                new Baseline(fixture.root().toString(), fixture.inventory()),
                CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023), selections, overlays);
    }
    @Test void actualMavenSourceProducerAndAllSelectedConsumersRoundtrip() throws IOException {
        // Exact retained production parent, rather than the synthetic fixture, supplies canonical order.
        try (var original = CompleteSourceGraphTest.class.getResourceAsStream("/complete-source-graph/retained-parent-pom.xml")) {
            if (original == null) throw new IOException("retained production parent fixture is required");
            byte[] bytes = original.readAllBytes();
            assertEquals(4037, bytes.length);
            try {
                var document = javax.xml.parsers.DocumentBuilderFactory.newInstance().newDocumentBuilder()
                        .parse(new java.io.ByteArrayInputStream(bytes));
                List<String> actual = new ArrayList<>();
                var modules = document.getElementsByTagName("module");
                for (int index = 0; index < modules.getLength(); index++) actual.add(modules.item(index).getTextContent().strip());
                assertEquals(actual, CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023));
            } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException error) {
                throw new IOException("retained production parent is invalid", error);
            }
        }
        Fixture fixture = fixture("complete", Profile.G2_RESEARCH_20261023);
        List<CompleteSourceGraph.ComponentInput> components = new ArrayList<>();
        for (ComponentSelection selection : selections(fixture)) {
            var component = new CompleteSourceGraph.ComponentInput(CompleteSourceGraph.COMPONENT_SCHEMA,
                    "test-machine", "2026-10-23T00:00:00Z", selection, List.of());
            Path componentPath = temporary.resolve(selection.component().name() + ".json");
            Files.write(componentPath, ControlBuild.strictMapper().writeValueAsBytes(component));
            components.add(CompleteSourceGraph.readComponent(FileRef.measure(componentPath)));
        }
        Plan plan = CompleteSourceGraph.combine("test-machine", "2026-10-23T00:00:00Z", Profile.G2_RESEARCH_20261023,
                new Baseline(fixture.root().toString(), fixture.inventory()), components);
        byte[] encoded = CompleteSourceGraph.encodePlan(plan);
        Path path = temporary.resolve("plan.json"); Files.write(path, encoded);
        Plan decoded = CompleteSourceGraph.readPlan(FileRef.measure(path));
        assertEquals(plan, decoded);
        assertEquals(SelectionStatus.SOURCE_SELECTION_ONLY, CompleteSourceGraph.resolve(decoded).status());
        assertEquals(ControlBuild.sourceManifest(fixture.root(), ControlBuild.SourceLimitProfile.valueOf("G2_RESEARCH_20261023")),
                CompleteSourceGraph.verifyMaterialized(decoded, fixture.root()).sourcePins());
    }
    @Test void stabilizationProducerConsumerAndStrictWirePreserveAllOlderProfiles() throws IOException {
        Profile profile = Profile.G2_STABILIZATION_20261023;
        assertEquals(29, CompleteSourceGraph.modules(Profile.JAVA29_REPAIR_20261023).size());
        assertEquals(30, CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023).size());
        assertEquals(31, CompleteSourceGraph.modules(profile).size());
        assertEquals("continuity-core", CompleteSourceGraph.modules(profile).get(1));
        assertEquals(32, profile.reactorProjects());
        Fixture fixture = fixture("stabilization", profile);
        Plan selected = new Plan(CompleteSourceGraph.PLAN_SCHEMA, "test-machine", "2026-10-23T00:00:00Z",
                SelectionStatus.SOURCE_SELECTION_ONLY, profile, new Baseline(fixture.root().toString(), fixture.inventory()),
                CompleteSourceGraph.modules(profile), selections(fixture), List.of());
        byte[] encoded = CompleteSourceGraph.encodePlan(selected);
        assertEquals(selected, ControlBuild.strictMapper().readValue(encoded, Plan.class));
        assertEquals(ControlBuild.sourceManifest(fixture.root(), profile.sourceLimitProfile()),
                CompleteSourceGraph.verifyMaterialized(selected, fixture.root()).sourcePins());
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(), Profile.G2_RESEARCH_20261023.sourceLimitProfile()));
        String json = new String(encoded, java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                json.replace("G2_STABILIZATION_20261023", "G2_RESEARCH_20261023"), Plan.class));
        assertThrows(IllegalArgumentException.class, () -> new Plan(selected.schema(), selected.machineId(),
                selected.observedAtUtc(), selected.status(), profile, selected.baseline(),
                CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023), selected.selections(), selected.overlays()));
        Path continuity = fixture.root().resolve("continuity-core/pom.xml");
        Files.writeString(continuity, Files.readString(continuity) + "\n");
        assertThrows(IOException.class, () -> CompleteSourceGraph.verifyMaterialized(selected, fixture.root()));
    }
    @Test void equalInventoryCountCannotHideAChangedConsumer() throws IOException {
        Fixture baseline = fixture("original", Profile.G2_RESEARCH_20261023);
        Fixture materialized = fixture("copy", Profile.G2_RESEARCH_20261023);
        Files.writeString(materialized.root().resolve(CONSUMER), "{\"value\":2}");
        Plan plan = plan(baseline, selections(baseline), List.of());
        assertEquals(ControlBuild.sourceManifest(baseline.root(), ControlBuild.SourceLimitProfile.valueOf("G2_RESEARCH_20261023")).size(),
                ControlBuild.sourceManifest(materialized.root(), ControlBuild.SourceLimitProfile.valueOf("G2_RESEARCH_20261023")).size());
        assertThrows(IOException.class, () -> CompleteSourceGraph.verifyMaterialized(plan, materialized.root()));
    }
    @Test void missingFinalM2SelectionCannotQualifyACompleteGraph() throws IOException {
        Fixture fixture = fixture("missingM2", Profile.G2_RESEARCH_20261023);
        List<ComponentSelection> selections = selections(fixture).stream().filter(item -> item.component() != Component.M2).toList();
        assertThrows(IllegalArgumentException.class, () -> plan(fixture, selections, List.of()));
    }
    @Test void ownerDeclaredConsumerCannotBeDroppedFromTheCompleteTargetSet() throws IOException {
        Fixture fixture = fixture("consumer", Profile.G2_RESEARCH_20261023);
        Path external = temporary.resolve("required-consumer.json"); Files.writeString(external, "{\"value\":3}");
        List<ComponentSelection> selected = new ArrayList<>(selections(fixture));
        selected.removeIf(item -> item.component() == Component.RECOVERY22);
        selected.add(new ComponentSelection(Component.RECOVERY22, fixture.provenance(),
                List.of(new SelectedFile("wave2-runtime/src/test/resources/required-consumer.json", FileRef.measure(external)))));
        Plan plan = plan(fixture, selected, List.of());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(plan));
    }
    @Test void overlaysRequireExactBaselinePreimageAndFinalOwnerSelection() throws IOException {
        Fixture fixture = fixture("overlay", Profile.G2_RESEARCH_20261023);
        Path external = temporary.resolve("replacement.json"); Files.writeString(external, "{\"value\":4}");
        FileRef post = FileRef.measure(external);
        List<ComponentSelection> selected = new ArrayList<>(selections(fixture));
        selected.removeIf(item -> item.component() == Component.M2);
        selected.add(new ComponentSelection(Component.M2, fixture.provenance(), List.of(new SelectedFile(PRODUCER, post))));
        Overlay absent = new Overlay(PRODUCER, Preimage.absent(), post, Component.M2, fixture.provenance());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(plan(fixture, selected, List.of(absent))));
        // A stale same-size preimage from another path is not the exact baseline source.
        Overlay wrongPath = new Overlay(PRODUCER, Preimage.exact(fixture.consumer()), post, Component.M2, fixture.provenance());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(plan(fixture, selected, List.of(wrongPath))));
    }
    @Test void exactFinalProducerFlowsThroughMaterializedConsumerVerification() throws IOException {
        Fixture fixture = fixture("overlayOriginal", Profile.G2_RESEARCH_20261023);
        Fixture materialized = fixture("overlayMaterialized", Profile.G2_RESEARCH_20261023);
        Path external = temporary.resolve("final-producer.json"); Files.writeString(external, "{\"value\":5}");
        FileRef post = FileRef.measure(external);
        List<ComponentSelection> selected = new ArrayList<>(selections(fixture));
        selected.removeIf(item -> item.component() == Component.M2);
        selected.add(new ComponentSelection(Component.M2, fixture.provenance(),
                List.of(new SelectedFile(PRODUCER, post), new SelectedFile(CONSUMER, fixture.consumer()))));
        Overlay overlay = new Overlay(PRODUCER, Preimage.exact(fixture.producer()), post, Component.M2, fixture.provenance());
        Plan plan = plan(fixture, selected, List.of(overlay));
        Files.writeString(materialized.root().resolve(PRODUCER), "{\"value\":5}");
        assertEquals(CompleteSourceGraph.VerificationStatus.EXACT_MATERIALIZED_SOURCES_ONLY,
                CompleteSourceGraph.verifyMaterialized(plan, materialized.root()).status());
    }
    @Test void duplicateFinalProducersAreRejected() throws IOException {
        Fixture fixture = fixture("duplicate", Profile.G2_RESEARCH_20261023);
        Overlay row = new Overlay(PRODUCER, Preimage.exact(fixture.producer()), fixture.producer(), Component.M2, fixture.provenance());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(plan(fixture, selections(fixture), List.of(row, row))));
    }
    @Test void toolRowsAreRelocatedExactlyOnce() {
        assertEquals("build-tools/src/main/java/Producer.java", CompleteSourceGraph.buildToolsTarget("src/main/java/Producer.java"));
        assertEquals("build-tools/pom.xml", CompleteSourceGraph.buildToolsTarget("pom.xml"));
        assertThrows(IllegalArgumentException.class, () -> CompleteSourceGraph.buildToolsTarget("build-tools/pom.xml"));
        assertThrows(IllegalArgumentException.class, () -> CompleteSourceGraph.buildToolsTarget("../pom.xml"));
        assertThrows(IllegalArgumentException.class, () -> new ComponentSelection(Component.BUILD_TOOLS,
                new FileRef(temporary.resolve("p").toString(), 0, "0".repeat(64)),
                List.of(new SelectedFile("src/main/java/Producer.java", new FileRef(temporary.resolve("s").toString(), 0, "0".repeat(64))))));
    }
    @Test void explicitLargerG2ProfileAccepts1540ButOldProfileRemainsBounded() throws IOException {
        Fixture old = fixture("oldProfile", Profile.JAVA29_REPAIR_20261023);
        addEmptyResources(old.root().resolve("contracts/src/main/resources"), 1540 - 32);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(old.root(), ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
        Fixture g2 = fixture("largerProfile", Profile.G2_RESEARCH_20261023);
        addEmptyResources(g2.root().resolve("g2-research/src/main/resources"), 1540 - 33);
        assertEquals(1540, ControlBuild.sourceManifest(g2.root(), ControlBuild.SourceLimitProfile.valueOf("G2_RESEARCH_20261023")).size());
    }
    private static void addEmptyResources(Path root, int count) throws IOException {
        for (int index = 0; index < count; index++) Files.createFile(root.resolve("retained-" + index + ".json"));
    }
    @Test void missingNullWrongTypeAndDuplicateJsonFieldsAreRejected() throws IOException {
        Fixture fixture = fixture("wire", Profile.G2_RESEARCH_20261023);
        Plan plan = plan(fixture, selections(fixture), List.of());
        String encoded = new String(CompleteSourceGraph.encodePlan(plan), java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(encoded.replace("\"status\":\"SOURCE_SELECTION_ONLY\",", ""), Plan.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(encoded.replace("\"status\":\"SOURCE_SELECTION_ONLY\"", "\"status\":null"), Plan.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(encoded.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":true"), Plan.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(encoded.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":1.0"), Plan.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(encoded.replaceFirst("\\{", "{\"schema\":\"duplicate\","), Plan.class));
    }
}
