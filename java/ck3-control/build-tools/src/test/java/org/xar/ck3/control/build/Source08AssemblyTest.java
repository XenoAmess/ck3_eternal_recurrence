package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
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

final class Source08AssemblyTest {
    private static final String MACHINE = "source08-fixture-machine";
    private static final String OWNER = "/root/source_fixture";
    private static final String OBSERVED = "2026-10-23T17:00:00Z";
    private static final String TARGET = "contracts/src/main/java/example/Shared.java";
    @TempDir Path directory;

    @Test void historicalLayerCannotBeDroppedOrRelabelled() throws IOException {
        FileRef inventory = text("inventory.json", "[]");
        FileRef original = text("original.java", "original");
        FileRef changed = text("changed.java", "changed");
        FileRef authority = text("authority.json", "{}");
        Layer historical = new Layer("historical", Component.COMMON, authority,
                List.of(new SelectedFile(TARGET, original)));
        Layer relabelled = new Layer("historical", Component.COMMON, authority,
                List.of(new SelectedFile(TARGET, changed)));
        Baseline baseline = new Baseline(directory.toString(), inventory);
        FileRef plan16 = request("plan16.json", baseline, List.of(historical));
        FileRef source07 = request("source07.json", baseline, List.of(relabelled));
        Source08Assembly.OwnerInput owner = owner(changed);
        Source08Assembly.Input input = input(plan16, source07, owner, List.of());
        assertThrows(IOException.class, () -> Source08Assembly.prepare(input));
    }

    @Test void explicitWinnerRequiredForRealInheritedTargetConflict() throws IOException {
        FileRef inventory = text("inventory.json", "[]");
        FileRef original = text("original.java", "original");
        FileRef changed = text("changed.java", "changed");
        FileRef authority = text("authority.json", "{}");
        Layer historical = new Layer("historical", Component.COMMON, authority,
                List.of(new SelectedFile(TARGET, original)));
        Baseline baseline = new Baseline(directory.toString(), inventory);
        FileRef plan16 = request("plan16.json", baseline, List.of(historical));
        FileRef source07 = request("source07.json", baseline, List.of(historical));
        Source08Assembly.OwnerInput owner = owner(changed);
        assertThrows(IOException.class, () -> Source08Assembly.prepare(input(plan16, source07, owner, List.of())));
        Request actual = Source08Assembly.prepare(input(plan16, source07, owner,
                List.of(new Winner(TARGET, "current"))));
        assertEquals(List.of(historical), actual.layers().subList(0, 1));
        assertEquals(List.of(new Winner(TARGET, "current")), actual.winners());
        byte[] json = ControlBuild.strictMapper().writeValueAsBytes(actual);
        assertEquals(actual, ControlBuild.strictMapper().readValue(json, Request.class));
    }

    @Test void ownerBoundaryRejectsWrongMachineNullCollectionAndBooleanByteCount() throws IOException {
        FileRef body = text("body.java", "body");
        ObjectNode root = ownerDocument(body);
        root.put("machine_id", "different-machine");
        assertThrows(IOException.class, () -> Source08Assembly.readOwner(ownerFrom("wrong-machine.json", root), MACHINE));
        ObjectNode nullCollection = ownerDocument(body);
        nullCollection.putNull("selected_files");
        assertThrows(IOException.class, () -> Source08Assembly.readOwner(ownerFrom("null-files.json", nullCollection), MACHINE));
        ObjectNode wrongBytes = ownerDocument(body);
        if (!(wrongBytes.path("selected_files").get(0).path("source_ref") instanceof ObjectNode ref)) {
            throw new IllegalStateException("fixture must create an object source_ref");
        }
        ref.put("bytes", true);
        assertThrows(IOException.class, () -> Source08Assembly.readOwner(ownerFrom("bool-bytes.json", wrongBytes), MACHINE));
    }

    @Test void toolsScopeDoesNotRelocateOrAbsorbHostTargets() throws IOException {
        FileRef body = text("body.java", "body");
        ObjectNode root = ownerDocument(body);
        ObjectNode tools = root.withArray("selected_files").addObject();
        tools.put("group", "TOOLS");
        tools.put("target_relative", "build-tools/src/main/java/example/Tool.java");
        tools.set("source_ref", ControlBuild.strictMapper().valueToTree(body));
        FileRef ref = json("tools-map.json", root);
        Source08Assembly.OwnerInput toolsOwner = new Source08Assembly.OwnerInput("current", OWNER,
                Component.BUILD_TOOLS, Source08Assembly.TargetScope.BUILD_TOOLS_ONLY, ref);
        List<SelectedFile> files = Source08Assembly.readOwner(toolsOwner, MACHINE);
        assertEquals(List.of(new SelectedFile("build-tools/src/main/java/example/Tool.java", body)), files);
    }

    private Source08Assembly.Input input(FileRef plan16, FileRef source07,
                                         Source08Assembly.OwnerInput owner, List<Winner> winners) {
        return new Source08Assembly.Input(Source08Assembly.INPUT_SCHEMA, MACHINE, OBSERVED, plan16,
                source07, Profile.G2_STABILIZATION_20261023,
                CompleteSourceGraph.modules(Profile.G2_STABILIZATION_20261023), List.of(owner), winners);
    }

    private Source08Assembly.OwnerInput owner(FileRef body) throws IOException {
        return ownerFrom("owner-map.json", ownerDocument(body));
    }

    private Source08Assembly.OwnerInput ownerFrom(String name, ObjectNode document) throws IOException {
        return new Source08Assembly.OwnerInput("current", OWNER, Component.COMMON,
                Source08Assembly.TargetScope.ALL, json(name, document));
    }

    private ObjectNode ownerDocument(FileRef body) {
        ObjectNode root = ControlBuild.strictMapper().createObjectNode();
        root.put("machine_id", MACHINE);
        root.put("owner", OWNER);
        ObjectNode row = root.putArray("selected_files").addObject();
        row.put("target_relative", TARGET);
        row.set("source_ref", ControlBuild.strictMapper().valueToTree(body));
        return root;
    }

    private FileRef request(String name, Baseline baseline, List<Layer> layers) throws IOException {
        Request request = new Request(SourceGraphPlanProducer.REQUEST_SCHEMA, MACHINE, OBSERVED,
                Profile.G2_STABILIZATION_20261023, baseline,
                CompleteSourceGraph.modules(Profile.G2_STABILIZATION_20261023), layers, List.of());
        return json(name, request);
    }

    private FileRef json(String name, Object value) throws IOException {
        Path target = directory.resolve(name);
        Files.write(target, ControlBuild.strictMapper().writeValueAsBytes(value));
        return FileRef.measure(target);
    }

    private FileRef text(String name, String value) throws IOException {
        Path target = directory.resolve(name);
        Files.writeString(target, value);
        return FileRef.measure(target);
    }
}
