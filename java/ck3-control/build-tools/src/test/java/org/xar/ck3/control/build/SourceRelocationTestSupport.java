package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.build.CompleteSourceGraph.Baseline;
import org.xar.ck3.control.build.CompleteSourceGraph.Component;
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Layer;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Request;

/** Real bounded file producers used by the complete Assembly -> Request -> Plan -> final-tree regressions. */
final class SourceRelocationTestSupport {
    static final String MACHINE = "relocation-test-machine";
    static final String WHEN = "2026-10-23T00:00:00Z";
    static final String CONTROL_PARENT = "ck3-control-parent";
    static final String MAVEN_PROJECT = "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion>";
    static final Profile PROFILE = Profile.G2_RESEARCH_20261023;
    static final String BASE_OLD = "wave2-runtime/src/main/java/org/example/Retained.java";
    static final String BASE_NEW = "local-service/src/main/java/org/example/Retained.java";
    static final String CURRENT_OLD = "wave2-events/src/test/java/org/example/Consumer.java";
    static final String CURRENT_NEW = "local-service/src/test/java/org/example/Consumer.java";
    static final String DUP_OLD = "g2-research/src/main/java/org/example/Duplicate.java";
    static final String DUP_NEW = "wave3-planning/src/main/java/org/example/Duplicate.java";
    static final String HISTORY_OLD = "wave2-runtime/src/main/java/org/example/Historical.java";
    static final String HISTORY_NEW = "local-service/src/main/java/org/example/Historical.java";
    record Move(String oldTargetRelative, String newTargetRelative, FileRef sourceRef) { }
    record Owner(String schema, String machineId, String owner, List<SelectedFile> selectedFiles, List<Move> relocations) { }
    record Fixture(Path workspace, Path root, Baseline baseline, List<FileRef> originals, List<Layer> history,
                   FileRef authority, List<SelectedFile> currentFiles, Source08Assembly.Input input) { }
    private SourceRelocationTestSupport() { }

    static FileRef write(Path path, String text) throws IOException {
        Files.createDirectories(path.getParent()); Files.writeString(path, text);
        return FileRef.measure(path);
    }
    static FileRef json(Path path, Object value) throws IOException {
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value)); return FileRef.measure(path);
    }
    static Fixture fixture(Path directory) throws IOException {
        return fixture(directory, PROFILE, 0);
    }
    static Fixture fixture(Path directory, Profile profile, int extraEmptyResources) throws IOException {
        if (extraEmptyResources < 0 || extraEmptyResources > profile.maxFiles())
            throw new IllegalArgumentException("Finite fixture source count required");
        Path root = Files.createDirectory(directory.resolve("baseline"));
        List<String> modules = CompleteSourceGraph.modules(profile);
        StringBuilder roster = new StringBuilder();
        for (String module : modules) {
            roster.append("<module>").append(module).append("</module>");
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools"
                    : module.equals("local-service") ? "ck3-control-local-service" : module;
            write(root.resolve(module + "/pom.xml"), MAVEN_PROJECT
                    + "<parent><groupId>org.xar.ck3.control</groupId><artifactId>" + CONTROL_PARENT
                    + "</artifactId><version>1.0.0-SNAPSHOT</version><relativePath>../pom.xml</relativePath></parent><artifactId>"
                    + artifact + "</artifactId></project>");
        }
        write(root.resolve("pom.xml"), MAVEN_PROJECT + "<groupId>org.xar.ck3.control</groupId><artifactId>" + CONTROL_PARENT
                + "</artifactId><version>1.0.0-SNAPSHOT</version><packaging>pom</packaging><modules>"
                + roster + "</modules></project>");
        FileRef retained = write(root.resolve(BASE_OLD), "package org.example; final class Retained { }\n");
        FileRef duplicate = write(root.resolve(DUP_OLD), "package org.example; final class Duplicate { }\n");
        write(root.resolve(DUP_NEW), "package org.example; final class Duplicate { }\n");
        if (extraEmptyResources > 0) {
            Path resources = Files.createDirectories(root.resolve("application/src/test/resources/r4-count"));
            for (int i = 0; i < extraEmptyResources; i++) Files.createFile(resources.resolve("source-" + i + ".json"));
        }
        List<FileRef> originals = ControlBuild.sourceManifest(root, profile.sourceLimitProfile());
        Path inventory = directory.resolve("baseline.json.gz");
        try (var output = new GZIPOutputStream(Files.newOutputStream(inventory))) {
            output.write(ControlBuild.strictMapper().writeValueAsBytes(originals));
        }
        Baseline baseline = new Baseline(root.toString(), FileRef.measure(inventory));
        FileRef historicalAuthority = write(directory.resolve("historical-owner.json"), "{\"kind\":\"original\"}");
        FileRef historical = write(directory.resolve("Historical.java"), "package org.example; final class Historical { }\n");
        List<Layer> history = new ArrayList<>();
        int index = 0;
        List<String> otherModules = modules.stream().filter(module -> !module.equals("build-tools")).toList();
        for (Component component : Component.values()) {
            String module = component == Component.BUILD_TOOLS ? "build-tools" : otherModules.get(index++);
            List<SelectedFile> historicalFiles = new ArrayList<>();
            historicalFiles.add(new SelectedFile(module + "/pom.xml", FileRef.measure(root.resolve(module + "/pom.xml"))));
            if (component == Component.COMMON) historicalFiles.add(new SelectedFile(HISTORY_OLD, historical));
            history.add(new Layer("historical-" + component.name().toLowerCase(java.util.Locale.ROOT), component,
                    historicalAuthority, historicalFiles));
        }
        FileRef first = json(directory.resolve("plan16-request.json"), new Request(SourceGraphPlanProducer.REQUEST_SCHEMA,
                MACHINE, WHEN, profile, baseline, modules, history, List.of()));
        FileRef original = json(directory.resolve("source07-request.json"), new Request(SourceGraphPlanProducer.REQUEST_SCHEMA,
                MACHINE, WHEN, profile, baseline, modules, history, List.of()));
        FileRef consumer = write(directory.resolve("Consumer.java"), "package org.example; final class Consumer { }\n");
        List<Move> moves = List.of(new Move(BASE_OLD, BASE_NEW, retained), new Move(CURRENT_OLD, CURRENT_NEW, consumer),
                new Move(DUP_OLD, DUP_NEW, duplicate), new Move(HISTORY_OLD, HISTORY_NEW, historical));
        List<SelectedFile> files = List.of(new SelectedFile(BASE_NEW, retained), new SelectedFile(CURRENT_OLD, consumer),
                new SelectedFile(CURRENT_NEW, consumer), new SelectedFile(DUP_NEW, duplicate), new SelectedFile(HISTORY_NEW, historical));
        FileRef authority = json(directory.resolve("owner.json"), new Owner("xar.java.effective-source-selection/v1", MACHINE,
                "/root/planner_owner", files, moves));
        List<Relocation> relocations = moves.stream().map(move -> new Relocation(move.oldTargetRelative(),
                move.newTargetRelative(), move.sourceRef(), authority)).toList();
        Source08Assembly.Input input = new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA, MACHINE,
                WHEN, first, original, profile, modules, List.of(new Source08Assembly.OwnerInput("current-owner",
                "/root/planner_owner", Component.COMMON, Source08Assembly.TargetScope.REACTOR_ONLY, authority)), List.of(), relocations);
        return new Fixture(directory, root, baseline, originals, List.copyOf(history), authority, files, input);
    }
    static CompleteSourceGraph.Plan produce(Fixture fixture) throws IOException {
        Request request = Source08Assembly.prepare(fixture.input());
        return SourceGraphPlanProducer.produce(json(fixture.workspace().resolve("actual-request.json"), request));
    }
    static CompleteSourceGraph.Plan withMoves(CompleteSourceGraph.Plan plan, List<Relocation> moves) {
        return new CompleteSourceGraph.Plan(CompleteSourceGraph.RELOCATION_PLAN_SCHEMA, plan.machineId(), plan.observedAtUtc(),
                plan.status(), plan.profile(), plan.baseline(), plan.modules(), plan.selections(), plan.overlays(), moves);
    }
    static List<FileRef> copyFinal(CompleteSourceGraph.Plan plan, Path destination) throws IOException {
        Files.createDirectory(destination);
        for (CompleteSourceGraph.ResolvedFile file : CompleteSourceGraph.resolve(plan).files()) {
            Path output = destination.resolve(file.targetRelative()); Files.createDirectories(output.getParent());
            Files.copy(Path.of(file.sourceRef().path()), output);
        }
        return ControlBuild.sourceManifest(destination, plan.profile().sourceLimitProfile());
    }
}
