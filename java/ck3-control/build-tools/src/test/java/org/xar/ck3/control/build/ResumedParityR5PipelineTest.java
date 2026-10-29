package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.CompleteSourceGraphMaterializer.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.*;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real small pipeline; synthetic limit arithmetic never represents a measured production census. */
final class ResumedParityR5PipelineTest {
    private static final Profile R4 = Profile.G2_FULL_PARITY_20261024_R4;
    private static final Profile R5 = Profile.G2_FULL_PARITY_20261024_R5;
    private static final Profile R6 = Profile.G2_FULL_PARITY_20261024_R6;
    private static final String MACHINE = "r5-source-fixture-machine", OBSERVED = "2026-10-24T12:00:00Z";
    @TempDir Path temporary;
    private record Fixture(Path root, Plan plan, FileRef planRef, FileRef seed) { }

    @Test void actualOwnerAssemblyPlanCopyAndAuditConsumersRetainTheSameR5() throws Exception {
        actualOwnerAssemblyPlanCopyAndAuditConsumersRetainProfile(R5);
    }

    @Test void actualR6AssemblyCopyAuditSerdeAndAllProfileConsumersRetainR6() throws Exception {
        actualOwnerAssemblyPlanCopyAndAuditConsumersRetainProfile(R6);
    }

    private void actualOwnerAssemblyPlanCopyAndAuditConsumersRetainProfile(Profile profile) throws Exception {
        Fixture fixture = fixture(profile);
        Plan plan = CompleteSourceGraph.readPlan(fixture.planRef());
        assertEquals(fixture.plan(), plan);
        var selected = CompleteSourceGraph.resolve(plan);
        Path copied = Files.createDirectory(temporary.resolve("materialized"));
        List<CopyRow> rows = new ArrayList<>();
        for (var file : selected.files()) {
            Path output = copied.resolve(file.targetRelative()); Files.createDirectories(output.getParent());
            rows.add(copy(file.targetRelative(), SharedSourceFiles.observe(Path.of(file.sourceRef().path())), output));
        }
        var verified = CompleteSourceGraph.verifyMaterialized(plan, copied);
        assertEquals(profile, verified.profile()); assertEquals(selected.files().size(), verified.sourcePins().size());
        NativeSize actual = measure(copied, verified.sourcePins()); requireSize(actual, profile);
        Card card = card(fixture, profile.maxNativeBytes()); FileRef cardRef = json("card.json", card);
        assertEquals(card, read(cardRef, Card.class)); requireProfileBudget(plan.profile(), card.maxSourceNativeBytes());
        // These finite DTO roundtrips grant no operation authority: no completed tools receipt is forged.
        FileRef ref = fixture.planRef();
        var receipt = new Receipt("xar.complete-source-materialization-actual/v1", MACHINE, OBSERVED,
                Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME, profile, copied.toString(),
                profile.childModules(), profile.reactorProjects(), actual.files(), actual,
                ref, cardRef, ref, ref, ref, ref, ref, Check.MATCH, Check.MATCH, Check.MATCH);
        FileRef receiptRef = json("receipt-domain-only.json", receipt);
        assertEquals(receipt, read(receiptRef, Receipt.class));
        var audit = new CompleteSourceGraphAudit.Manifest("xar.complete-source-independent-manifest/v1", MACHINE, OBSERVED,
                CompleteSourceGraphAudit.Verification.COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE,
                Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME, profile, copied.toString(),
                actual.files(), profile.childModules(), profile.reactorProjects(), actual,
                ref, receiptRef, cardRef, cardRef, ref, ref, ref, ref, ref, ref, plan.selections(),
                Check.MATCH, Check.MATCH, Check.MATCH);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(audit);
        assertEquals(audit, ControlBuild.strictMapper().readValue(encoded, CompleteSourceGraphAudit.Manifest.class));
        assertTrue(CompleteSourceGraphAudit.negativeCases(encoded, rows.getFirst()) > 0);
        assertEquals(profile.sourceLimitProfile(), Full35CompileOnly.sourceProfile(plan));
        assertEquals(ReactorTestClosure.g2FullParityCurrentRequirements(), ControlCi.httpRequirements(profile.sourceLimitProfile()));
        requireFixtureBound();
    }

    @Test void exactR5CardAndProductionExtentAcceptWhatR4CannotWithoutLargeFiles() throws Exception {
        Fixture f = fixture(R5);
        // Boundary DATA only, not a fabricated native witness or a 96MiB/6144-file filler fixture.
        NativeSize boundary = size(R5.maxFiles(), R5.maxLogicalBytes(), R5.maxNativeBytes());
        requireSize(boundary, R5); assertThrows(IllegalArgumentException.class, () -> requireSize(boundary, R4));
        Card r5 = card(f, R5.maxNativeBytes()); assertEquals(r5, read(json("r5-card.json", r5), Card.class));
        requireProfileBudget(R5, r5.maxSourceNativeBytes());
        assertThrows(IOException.class, () -> requireProfileBudget(R4, r5.maxSourceNativeBytes()));
        Card r4 = card(f, R4.maxNativeBytes()); requireProfileBudget(R4, r4.maxSourceNativeBytes());
        assertThrows(IOException.class, () -> requireProfileBudget(R5, r4.maxSourceNativeBytes()));
        assertThrows(IllegalArgumentException.class, () -> card(f, 79L << 20));
        assertThrows(IllegalArgumentException.class, () -> card(f, R5.maxNativeBytes() + 1));
        assertThrows(IllegalArgumentException.class, () -> card(f, 1)); requireFixtureBound();
    }

    @Test void everyR5LimitAndUnknownWrongOrAbsentProfileStillRejects() throws Exception {
        Fixture f = fixture(R5);
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(R5.maxFiles() + 1, 1, 8192), R5));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, R5.maxLogicalBytes() + 1, 8192), R5));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, 1, R5.maxNativeBytes() + 1), R5));
        var mapper = ControlBuild.strictMapper();
        for (String unknown : List.of("G2_FULL_PARITY_20261024_R7", "G2_FULL_PARITY_20261024_r5")) {
            ObjectNode wire = mapper.valueToTree(f.plan()); wire.put("profile", unknown);
            assertThrows(IOException.class, () -> mapper.treeToValue(wire, Plan.class));
        }
        ObjectNode missing = mapper.valueToTree(f.plan()); missing.remove("profile");
        assertThrows(IOException.class, () -> mapper.treeToValue(missing, Plan.class));
        ObjectNode nil = mapper.valueToTree(f.plan()); nil.putNull("profile");
        assertThrows(IOException.class, () -> mapper.treeToValue(nil, Plan.class));
        ObjectNode cardWire = mapper.valueToTree(card(f, R5.maxNativeBytes()));
        cardWire.put("max_source_native_bytes", (double) R5.maxNativeBytes());
        assertThrows(IOException.class, () -> mapper.treeToValue(cardWire, Card.class));
        ObjectNode wrongCount = mapper.valueToTree(size(1, 1, 8192)); wrongCount.put("files", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(wrongCount, NativeSize.class));
        assertFalse(Files.exists(Path.of(card(f, R5.maxNativeBytes()).sourceRoot()))); requireFixtureBound();
    }

    @Test void realR4PipelineAndCompilerLimitsStayIndependent() throws Exception {
        Fixture f = fixture(R4);
        assertEquals(R4, CompleteSourceGraph.readPlan(f.planRef()).profile());
        assertEquals(R4, CompleteSourceGraph.verifyMaterialized(f.plan(), f.root()).profile());
        assertEquals(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4, Full35CompileOnly.sourceProfile(f.plan()));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(R4.maxFiles() + 1, 1, 8192), R4));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, R4.maxLogicalBytes() + 1, 8192), R4));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, 1, R4.maxNativeBytes() + 1), R4));
        assertEquals(12L << 20, R4.sourceLimitProfile().moduleSourceBytes("local-service", "src"));
        assertEquals(8L << 20, R4.sourceLimitProfile().moduleSourceBytes("native-transport", "src"));
        assertEquals(16L << 20, R5.sourceLimitProfile().moduleSourceBytes("local-service", "src"));
        assertEquals(12L << 20, R5.sourceLimitProfile().moduleSourceBytes("native-transport", "src"));
        assertEquals(12L << 20, R5.sourceLimitProfile().moduleSourceBytes("application", "src"));
        assertEquals(8L << 20, R5.sourceLimitProfile().moduleSourceBytes("contracts", "src"));
        assertEquals(8L << 20, R5.sourceLimitProfile().moduleSourceBytes("local-service", ".mvn"));
        Plan rejected = new Plan(f.plan().schema(), f.plan().machineId(), f.plan().observedAtUtc(), f.plan().status(),
                Profile.G2_FULL_PARITY_20261024_R3, f.plan().baseline(), f.plan().modules(), f.plan().selections(), f.plan().overlays());
        assertThrows(IOException.class, () -> Full35CompileOnly.sourceProfile(rejected));
        requireFixtureBound();
    }

    @Test void r6OnlyRaisesApplicationSourceCeilingAndKeepsEveryOtherBoundAndRefusal() throws Exception {
        assertEquals(6144, R6.maxFiles()); assertEquals(96L << 20, R6.maxLogicalBytes());
        assertEquals(112L << 20, R6.maxNativeBytes());
        assertEquals(34, R6.childModules()); assertEquals(35, R6.reactorProjects());
        assertEquals(13L << 20, R6.sourceLimitProfile().moduleSourceBytes("application", "src"));
        assertEquals(12L << 20, R5.sourceLimitProfile().moduleSourceBytes("application", "src"));
        for (String module : List.of("local-service", "native-transport", "contracts", "application"))
            for (String directory : List.of("src", ".mvn"))
                if (!module.equals("application") || !directory.equals("src"))
                    assertEquals(R5.sourceLimitProfile().moduleSourceBytes(module, directory),
                            R6.sourceLimitProfile().moduleSourceBytes(module, directory));
        assertEquals(6144, R6.sourceLimitProfile().maxFiles());
        assertEquals(96L << 20, R6.sourceLimitProfile().maxBytes());
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(6145, 1, 8192), R6));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, (96L << 20) + 1, 8192), R6));
        assertThrows(IllegalArgumentException.class, () -> requireSize(size(1, 1, (112L << 20) + 1), R6));
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(R6.sourceLimitProfile(), null));
        Fixture f = fixture(R6);
        Files.writeString(Path.of(f.seed().path()), "changed R6 original consumer");
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(f.plan()));
        assertThrows(IOException.class, () -> CompleteSourceGraph.verifyMaterialized(f.plan(), f.root()));
        requireFixtureBound();
    }

    @Test void largerProfileDoesNotWaiveActualPinsOrRequiredFixtureProduction() throws Exception {
        Fixture f = fixture(R5);
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(R5.sourceLimitProfile(), null));
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(R4.sourceLimitProfile(), null));
        Files.writeString(Path.of(f.seed().path()), "changed original actual consumer");
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(f.plan()));
        assertThrows(IOException.class, () -> CompleteSourceGraph.verifyMaterialized(f.plan(), f.root()));
        requireFixtureBound();
    }

    private Fixture fixture(Profile profile) throws Exception {
        Path root = Files.createDirectory(temporary.resolve("baseline")); StringBuilder modules = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(profile)) {
            modules.append("<module>").append(module).append("</module>");
            Path child = Files.createDirectory(root.resolve(module));
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools"
                    : module.equals("local-service") ? "ck3-control-local-service" : module;
            file(child.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><artifactId>" + artifact + "</artifactId></project>");
        }
        file(root.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><artifactId>ck3-control-parent</artifactId>"
                + "<modules>" + modules + "</modules></project>");
        List<Source08Assembly.OwnerInput> owners = new ArrayList<>(); FileRef seed = null;
        for (Component component : Component.values()) {
            String target = (component == Component.BUILD_TOOLS ? "build-tools" : "contracts")
                    + "/src/test/resources/r5/" + component.name() + ".txt";
            Path path = root.resolve(target); Files.createDirectories(path.getParent());
            FileRef source = file(path, "actual finite source/consumer for " + component.name()); if (seed == null) seed = source;
            ObjectNode owner = ControlBuild.strictMapper().createObjectNode();
            owner.put("machine_id", MACHINE).put("owner", "/root/r5_source_fixture");
            ObjectNode row = owner.putArray("selected_files").addObject(); row.put("target_relative", target);
            row.set("source_ref", ControlBuild.strictMapper().valueToTree(source));
            owners.add(new Source08Assembly.OwnerInput("owner_" + component.name().toLowerCase(java.util.Locale.ROOT),
                    "/root/r5_source_fixture", component, Source08Assembly.TargetScope.ALL, json("owner-" + component.name() + ".json", owner)));
        }
        List<FileRef> pins = ControlBuild.sourceManifest(root, profile.sourceLimitProfile());
        Path inventory = temporary.resolve("baseline-inventory.json.gz");
        try (var output = new GZIPOutputStream(Files.newOutputStream(inventory, StandardOpenOption.CREATE_NEW))) {
            output.write(ControlBuild.strictMapper().writeValueAsBytes(pins));
        }
        Baseline baseline = new Baseline(root.toString(), FileRef.measure(inventory));
        // R4 ancestral request remains exact. Only the explicit current Input chooses the new profile.
        var prior = new SourceGraphPlanProducer.Request(SourceGraphPlanProducer.REQUEST_SCHEMA, MACHINE, OBSERVED,
                R4, baseline, CompleteSourceGraph.modules(R4), List.of(), List.of());
        FileRef original = json("original-r4-request.json", prior);
        var input = new Source08Assembly.Input(Source08Assembly.INPUT_SCHEMA, MACHINE, OBSERVED, original,
                original, profile, CompleteSourceGraph.modules(profile), owners, List.of());
        FileRef inputRef = json("owner-input.json", input);
        var decoded = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(inputRef.path())), Source08Assembly.Input.class);
        FileRef requestRef = json("actual-request.json", Source08Assembly.prepare(decoded));
        Plan plan = SourceGraphPlanProducer.produce(requestRef);
        FileRef planRef = file(temporary.resolve("actual-plan.json"), CompleteSourceGraph.encodePlan(plan));
        requireFixtureBound(); return new Fixture(root, plan, planRef, java.util.Objects.requireNonNull(seed));
    }

    private Card card(Fixture f, long maximum) {
        FileRef ref = f.planRef();
        return new Card("xar.complete-source-graph-operation-card/v1", MACHINE, "/root/source03_audit", OBSERVED,
                "2026-10-24T13:00:00Z", Operation.MATERIALIZE, ref, ref, ref, ref, ref, ref, null,
                temporary.resolve("never-admitted-copy").toString(), temporary.resolve("never-admitted-metadata").toString(),
                maximum, 4L << 20, "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
    }
    private static NativeSize size(int files, long logical, long nativeBytes) {
        return new NativeSize(files, 1, logical, nativeBytes - 4096, 4096, nativeBytes);
    }
    private FileRef json(String name, Object value) throws IOException {
        return file(temporary.resolve(name), ControlBuild.strictMapper().writeValueAsBytes(value));
    }
    private static FileRef file(Path path, String value) throws IOException {
        return file(path, value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    private static FileRef file(Path path, byte[] bytes) throws IOException {
        if (bytes.length > (64 << 10)) throw new IOException("small R5 fixture only; no giant limit filler");
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE); return FileRef.measure(path);
    }
    private void requireFixtureBound() throws IOException {
        long actual = 0;
        try (var paths = Files.walk(temporary)) {
            for (Path path : paths.toList())
                actual = Math.addExact(actual, Files.isDirectory(path) ? 4096 : SharedSourceFiles.nativeFile(path).allocatedBytes());
        }
        if (actual > (4L << 20)) throw new IOException("R5 fixture exceeded its serial four-MiB native allocation quote");
    }
}
