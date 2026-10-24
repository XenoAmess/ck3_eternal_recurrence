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
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Layer;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Request;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Winner;

final class SourceGraphPlanProducerTest {
    @TempDir Path temporary;
    private record Fixture(Baseline baseline, List<Layer> layers, SelectedFile contested, FileRef owner) { }
    private Fixture fixture() throws IOException {
        Path root = Files.createDirectory(temporary.resolve("source"));
        StringBuilder roster = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023)) {
            roster.append("<module>").append(module).append("</module>");
            Path directory = Files.createDirectory(root.resolve(module));
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools"
                    : module.equals("local-service") ? "ck3-control-local-service" : module;
            Files.writeString(directory.resolve("pom.xml"), "<project><artifactId>" + artifact + "</artifactId></project>");
        }
        Files.writeString(root.resolve("pom.xml"), "<project><artifactId>ck3-control-parent</artifactId><modules>" + roster + "</modules></project>");
        Path owner = temporary.resolve("owner-map.json"); Files.writeString(owner, "{\"source_only\":true}");
        FileRef ownerRef = FileRef.measure(owner);
        List<Layer> layers = new ArrayList<>(); SelectedFile contested = null;
        for (Component component : Component.values()) {
            String target = (component == Component.BUILD_TOOLS ? "build-tools" : "g2-research")
                    + "/src/test/resources/" + component.name() + ".json";
            Path file = root.resolve(target); Files.createDirectories(file.getParent()); Files.writeString(file, "{\"value\":1}");
            SelectedFile selected = new SelectedFile(target, FileRef.measure(file));
            layers.add(new Layer(component.name().toLowerCase(java.util.Locale.ROOT), component, ownerRef, List.of(selected)));
            if (component == Component.M2) contested = selected;
        }
        Path inventory = temporary.resolve("inventory.json.gz");
        try (var output = new GZIPOutputStream(Files.newOutputStream(inventory))) {
            output.write(ControlBuild.strictMapper().writeValueAsBytes(ControlBuild.sourceManifest(root,
                    ControlBuild.SourceLimitProfile.valueOf("G2_RESEARCH_20261023"))));
        }
        return new Fixture(new Baseline(root.toString(), FileRef.measure(inventory)), List.copyOf(layers), contested, ownerRef);
    }
    private FileRef request(Fixture fixture, List<Layer> layers, List<Winner> winners) throws IOException {
        Request request = new Request(SourceGraphPlanProducer.REQUEST_SCHEMA, "test-machine", "2026-10-23T00:00:00Z",
                Profile.G2_RESEARCH_20261023, fixture.baseline(), CompleteSourceGraph.modules(Profile.G2_RESEARCH_20261023), layers, winners);
        Path path = temporary.resolve("request.json"); Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(request));
        return FileRef.measure(path);
    }
    @Test void actualRequestProducerEmitsAWholeSourceSelectionPlan() throws IOException {
        Fixture fixture = fixture();
        var plan = SourceGraphPlanProducer.produce(request(fixture, fixture.layers(), List.of()));
        assertEquals(CompleteSourceGraph.SelectionStatus.SOURCE_SELECTION_ONLY, plan.status());
        assertEquals(Component.values().length, plan.selections().size());
        assertEquals(0, plan.overlays().size());
        assertEquals(plan, ControlBuild.strictMapper().readValue(CompleteSourceGraph.encodePlan(plan), CompleteSourceGraph.Plan.class));
    }
    @Test void producerConflictCannotUseLastWriterOrEqualContentAliases() throws IOException {
        Fixture fixture = fixture();
        List<Layer> layers = new ArrayList<>(fixture.layers());
        layers.add(new Layer("later-m2", Component.M2, fixture.owner(), List.of(fixture.contested())));
        assertThrows(IOException.class, () -> SourceGraphPlanProducer.produce(request(fixture, layers, List.of())));
        var plan = SourceGraphPlanProducer.produce(request(fixture, layers, List.of(new Winner(fixture.contested().targetRelative(), "m2"))));
        assertEquals(0, plan.overlays().size());
    }
    @Test void staleExplicitWinnerAndCrossComponentToolRelocationAreRejected() throws IOException {
        Fixture fixture = fixture();
        assertThrows(IOException.class, () -> SourceGraphPlanProducer.produce(request(fixture, fixture.layers(),
                List.of(new Winner(fixture.contested().targetRelative(), "m2")))));
        assertThrows(IllegalArgumentException.class, () -> new Layer("bad-tools", Component.BUILD_TOOLS,
                fixture.owner(), List.of(fixture.contested())));
    }
}
