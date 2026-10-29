package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.CompleteSourceGraphMaterializer.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.*;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Software-only source/profile tests; bounded private input data is never an actual Host source census. */
final class ResumedParityR7PipelineTest {
    private static final Profile R6 = Profile.G2_FULL_PARITY_20261024_R6;
    private static final Profile R7 = Profile.G2_FULL_PARITY_20261025_R7;
    private static final String MACHINE = "r7-software-fixture", OBSERVED = "2026-10-25T00:00:00Z";
    @TempDir Path temporary;
    private record Fixture(Path root, Plan plan, FileRef planRef) {}

    @Test void realModuleInventoryKeepsR6AndEnforcesBothR7Boundaries() throws Exception {
        Path root = reactor();
        for (String module : List.of("local-service", "application")) {
            Path source = root.resolve(module + "/src/test/resources/finite-boundary.bin");
            Files.createDirectories(source.getParent());
            // Actual capture01 failed at these source extents; only this bounded private software input is created.
            long observed = module.equals("local-service") ? 19355136L : 13969242L;
            long maximum = module.equals("local-service") ? 19L << 20 : 14L << 20;
            resize(source, observed);
            assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, R6.sourceLimitProfile()));
            var accepted = ControlBuild.sourceManifest(root, R7.sourceLimitProfile());
            assertEquals(observed, accepted.stream().filter(ref -> Path.of(ref.path()).equals(source)).findFirst().orElseThrow().bytes());
            resize(source, maximum);
            assertDoesNotThrow(() -> { ControlBuild.sourceManifest(root, R7.sourceLimitProfile()); });
            resize(source, maximum + 1);
            assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, R7.sourceLimitProfile()));
            Files.delete(source); // The next module must reach its own boundary, not fail at the preceding module.
        }
        assertEquals(16L << 20, R6.sourceLimitProfile().moduleSourceBytes("local-service", "src"));
        assertEquals(13L << 20, R6.sourceLimitProfile().moduleSourceBytes("application", "src"));
        assertEquals(19L << 20, R7.sourceLimitProfile().moduleSourceBytes("local-service", "src"));
        assertEquals(14L << 20, R7.sourceLimitProfile().moduleSourceBytes("application", "src"));
    }

    @Test void actualOwnerProducerPlanCopyAuditAndCompilerConsumersKeepR7() throws Exception {
        Fixture f = fixture();
        Plan plan = CompleteSourceGraph.readPlan(f.planRef());
        assertEquals(f.plan(), plan);
        var selected = CompleteSourceGraph.resolve(plan);
        Path copied = Files.createDirectory(temporary.resolve("copied"));
        List<CopyRow> rows = new ArrayList<>();
        for (var file : selected.files()) {
            Path target = copied.resolve(file.targetRelative()); Files.createDirectories(target.getParent());
            rows.add(copy(file.targetRelative(), SharedSourceFiles.observe(Path.of(file.sourceRef().path())), target));
        }
        var verified = CompleteSourceGraph.verifyMaterialized(plan, copied);
        assertEquals(R7, verified.profile());
        NativeSize size = measure(copied, verified.sourcePins()); requireSize(size, R7);
        FileRef ref = f.planRef();
        var card = new Card("xar.complete-source-graph-operation-card/v1", MACHINE, "/root/source03_audit",
                OBSERVED, "2026-10-25T01:00:00Z", Operation.MATERIALIZE,
                ref, ref, ref, ref, ref, ref, null, temporary.resolve("not-admitted-copy").toString(),
                temporary.resolve("not-admitted-metadata").toString(), 112L << 20, 4L << 20,
                "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
        FileRef cardRef = json("card.json", card);
        assertEquals(card, read(cardRef, Card.class)); requireProfileBudget(R7, card.maxSourceNativeBytes());
        // Domain DTO roundtrips grant no completed tools receipt or operation authority.
        var receipt = new Receipt("xar.complete-source-materialization-actual/v1", MACHINE, OBSERVED,
                Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME, R7, copied.toString(),
                34, 35, size.files(), size, ref, cardRef, ref, ref, ref, ref, ref, Check.MATCH, Check.MATCH, Check.MATCH);
        FileRef receiptRef = json("receipt-domain-only.json", receipt);
        assertEquals(receipt, read(receiptRef, Receipt.class));
        var audit = new CompleteSourceGraphAudit.Manifest("xar.complete-source-independent-manifest/v1", MACHINE, OBSERVED,
                CompleteSourceGraphAudit.Verification.COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE,
                Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME, R7, copied.toString(),
                size.files(), 34, 35, size, ref, receiptRef, cardRef, cardRef, ref, ref, ref, ref, ref, ref,
                plan.selections(), Check.MATCH, Check.MATCH, Check.MATCH);
        var mapper = ControlBuild.strictMapper();
        byte[] wire = mapper.writeValueAsBytes(audit);
        assertEquals(audit, mapper.readValue(wire, CompleteSourceGraphAudit.Manifest.class));
        assertTrue(CompleteSourceGraphAudit.negativeCases(wire, rows.getFirst()) > 0);
        assertEquals(R7.sourceLimitProfile(), Full35CompileOnly.sourceProfile(plan));
        assertEquals(ReactorTestClosure.g2FullParityCurrentRequirements(), ControlCi.httpRequirements(R7.sourceLimitProfile()));
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(R7.sourceLimitProfile(), null));
    }

    @Test void r7OnlyChangesLocalServiceAndApplicationAndRetainsTotalSnapshotAndOldEnumWire() throws Exception {
        assertEquals(6144, R7.maxFiles()); assertEquals(96L << 20, R7.maxLogicalBytes());
        assertEquals(112L << 20, R7.maxNativeBytes()); assertEquals(34, R7.childModules()); assertEquals(35, R7.reactorProjects());
        assertEquals(6144, R7.sourceLimitProfile().maxFiles()); assertEquals(96L << 20, R7.sourceLimitProfile().maxBytes());
        assertEquals(14L << 20, R7.sourceLimitProfile().moduleSourceBytes("application", "src"));
        for (String module : CompleteSourceGraph.modules(R7))
            for (String directory : List.of("src", ".mvn"))
                if (!(directory.equals("src") && (module.equals("local-service") || module.equals("application"))))
                    assertEquals(R6.sourceLimitProfile().moduleSourceBytes(module, directory),
                            R7.sourceLimitProfile().moduleSourceBytes(module, directory));
        assertThrows(IllegalArgumentException.class, () -> requireSize(new NativeSize(1, 1, (96L << 20) + 1,
                (112L << 20) - 4096, 4096, 112L << 20), R7));
        assertThrows(IllegalArgumentException.class, () -> requireSize(new NativeSize(6145, 1, 1, 4096, 4096, 8192), R7));
        assertThrows(IllegalArgumentException.class, () -> requireSize(new NativeSize(1, 1, 1,
                (112L << 20) - 4095, 4096, (112L << 20) + 1), R7));
        var mapper = ControlBuild.strictMapper();
        assertEquals(R6, mapper.readValue(mapper.writeValueAsBytes(R6), Profile.class));
        assertEquals(R7, mapper.readValue(mapper.writeValueAsBytes(R7), Profile.class));
        assertEquals(R7.sourceLimitProfile(), mapper.readValue(mapper.writeValueAsBytes(R7.sourceLimitProfile()), ControlBuild.SourceLimitProfile.class));
        Fixture f = fixture(); ObjectNode missing = mapper.valueToTree(f.plan()); missing.remove("profile");
        assertThrows(IOException.class, () -> mapper.treeToValue(missing, Plan.class));
        ObjectNode unknown = mapper.valueToTree(f.plan()); unknown.put("profile", "G2_FULL_PARITY_20261024_R7");
        assertThrows(IOException.class, () -> mapper.treeToValue(unknown, Plan.class));
        ObjectNode numeric = mapper.valueToTree(f.plan()); numeric.put("profile", 7);
        assertThrows(IOException.class, () -> mapper.treeToValue(numeric, Plan.class));
    }

    @Test void completeCurrentRouteSelectsR7AndLegacyRouteRetainsR6() {
        Instant start = Instant.parse(OBSERVED); String review = start.plus(Duration.ofHours(6)).toString();
        var pin = new CiBootstrap.FilePin(temporary.resolve("software-policy.json").toAbsolutePath().toString(), 1, "0".repeat(64));
        var current = new CiBootstrap.Plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, MACHINE, OBSERVED, review,
                "software-repo", "software-work", "software-java", null, "software-python", "/root/software-test",
                pin, Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
        var legacy = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, MACHINE, OBSERVED, review,
                current.repoRoot(), current.workRoot(), current.javaHome(), null, current.pythonExecutable(), current.ownerTask(),
                pin, Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
        assertEquals(R7.sourceLimitProfile(), ControlCi.reactorSourceProfile(current));
        assertEquals(R6.sourceLimitProfile(), ControlCi.reactorSourceProfile(legacy));
    }

    private Path reactor() throws IOException {
        Path root = Files.createDirectory(temporary.resolve("reactor")); StringBuilder modules = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(R7)) {
            modules.append("<module>").append(module).append("</module>");
            Path child = Files.createDirectory(root.resolve(module));
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools" : module.equals("local-service") ? "ck3-control-local-service" : module;
            file(child.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><artifactId>" + artifact + "</artifactId></project>");
        }
        file(root.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><artifactId>ck3-control-parent</artifactId><modules>"
                + modules + "</modules></project>");
        return root;
    }

    private Fixture fixture() throws Exception {
        Path root = reactor(); List<Source08Assembly.OwnerInput> owners = new ArrayList<>();
        for (Component component : Component.values()) {
            String target = (component == Component.BUILD_TOOLS ? "build-tools" : "contracts") + "/src/test/resources/r7/" + component + ".txt";
            Path source = root.resolve(target); Files.createDirectories(source.getParent()); FileRef pin = file(source, "software source for " + component);
            ObjectNode owner = ControlBuild.strictMapper().createObjectNode(); owner.put("machine_id", MACHINE).put("owner", "/root/r7_fixture");
            ObjectNode row = owner.putArray("selected_files").addObject(); row.put("target_relative", target);
            row.set("source_ref", ControlBuild.strictMapper().valueToTree(pin));
            owners.add(new Source08Assembly.OwnerInput("r7_" + component.name().toLowerCase(java.util.Locale.ROOT),
                    "/root/r7_fixture", component, Source08Assembly.TargetScope.ALL, json("owner-" + component + ".json", owner)));
        }
        Path inventory = temporary.resolve("inventory.json.gz");
        try (var stream = new GZIPOutputStream(Files.newOutputStream(inventory, StandardOpenOption.CREATE_NEW))) {
            stream.write(ControlBuild.strictMapper().writeValueAsBytes(ControlBuild.sourceManifest(root, R7.sourceLimitProfile())));
        }
        var baseline = new Baseline(root.toString(), FileRef.measure(inventory));
        var prior = new SourceGraphPlanProducer.Request(SourceGraphPlanProducer.REQUEST_SCHEMA, MACHINE, OBSERVED, R6,
                baseline, CompleteSourceGraph.modules(R6), List.of(), List.of());
        FileRef original = json("original-r6.json", prior);
        var input = new Source08Assembly.Input(Source08Assembly.INPUT_SCHEMA, MACHINE, OBSERVED, original, original,
                R7, CompleteSourceGraph.modules(R7), owners, List.of());
        FileRef inputRef = json("input.json", input);
        var decoded = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(inputRef.path())), Source08Assembly.Input.class);
        Plan plan = SourceGraphPlanProducer.produce(json("prepared-request.json", Source08Assembly.prepare(decoded)));
        Path planPath = temporary.resolve("plan.json"); Files.write(planPath, CompleteSourceGraph.encodePlan(plan), StandardOpenOption.CREATE_NEW);
        return new Fixture(root, plan, FileRef.measure(planPath));
    }

    private static void resize(Path path, long bytes) throws IOException {
        try (var channel = FileChannel.open(path, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            channel.truncate(0); channel.position(bytes - 1); channel.write(ByteBuffer.wrap(new byte[] {0}));
        }
    }
    private FileRef json(String name, Object value) throws IOException {
        Path path = temporary.resolve(name); Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW);
        return FileRef.measure(path);
    }
    private static FileRef file(Path path, String value) throws IOException {
        Files.writeString(path, value, StandardOpenOption.CREATE_NEW); return FileRef.measure(path);
    }
}
