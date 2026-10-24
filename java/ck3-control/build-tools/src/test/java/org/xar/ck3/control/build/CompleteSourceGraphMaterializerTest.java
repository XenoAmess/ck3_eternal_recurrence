package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.CompleteSourceGraphMaterializer.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class CompleteSourceGraphMaterializerTest {
    @TempDir Path temporary;

    @Test void copiesRealNativeFileAndRoundtripsExactProof() throws Exception {
        Path original = temporary.resolve("resource.json");
        Files.writeString(original, "{\"id_decimal\":\"18446744073709551615\",\"empty\":[]}");
        var before = SharedSourceFiles.observe(original);
        Path output = temporary.resolve("resource-copy.json");
        CopyRow result = copy("g2-research/src/test/resources/resource.json", before, output);
        assertEquals(Files.readString(original), Files.readString(output));
        assertEquals(before, SharedSourceFiles.observe(original));
        assertNotEquals(before.nativeFile().identityKey(), result.destination().nativeFile().identityKey());
        assertEquals(1, result.destination().nativeFile().linkCount());
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(result);
        assertEquals(result, ControlBuild.strictMapper().readValue(encoded, CopyRow.class));
    }
    @Test void refusesExistingOutputAndKeepsBothOriginals() throws Exception {
        Path source = temporary.resolve("source"); Path output = temporary.resolve("existing");
        Files.writeString(source, "source"); Files.writeString(output, "protected");
        var original = SharedSourceFiles.observe(source); var destination = SharedSourceFiles.observe(output);
        assertThrows(IOException.class, () -> copy("contracts/src/main/resources/x", original, output));
        assertEquals(original, SharedSourceFiles.observe(source));
        assertEquals(destination, SharedSourceFiles.observe(output));
    }
    @Test void rejectsOriginalChangedAfterSnapshotBeforeCreatingOutput() throws Exception {
        Path source = temporary.resolve("mutable"); Path output = temporary.resolve("never-created");
        Files.writeString(source, "before"); var before = SharedSourceFiles.observe(source);
        Files.writeString(source, "after changed size");
        assertThrows(IOException.class, () -> copy("contracts/src/test/resources/x", before, output));
        assertFalse(Files.exists(output));
    }
    @Test void rejectsActualHardlinkAndAliasRelations() throws Exception {
        Path source = temporary.resolve("single"); Files.writeString(source, "real");
        var before = SharedSourceFiles.observe(source);
        assertThrows(IOException.class, () -> relation(new CopyRow("contracts/src/main/resources/x", before, before, before)));
        Path link = temporary.resolve("hardlink"); Files.createLink(link, source);
        var current = SharedSourceFiles.observe(source); var linked = SharedSourceFiles.observe(link);
        assertTrue(linked.nativeFile().linkCount() > 1);
        assertThrows(IOException.class, () -> relation(new CopyRow("contracts/src/main/resources/x", current, current, linked)));
    }
    @Test void refusesEscapesReplayAndOverBudgetMetadataBeforeWrite() throws Exception {
        assertThrows(IOException.class, () -> target(temporary, "../outside"));
        assertThrows(IOException.class, () -> fresh(temporary));
        Path metadata = Files.createDirectory(temporary.resolve("metadata"));
        Path result = metadata.resolve("must-not-exist.gz");
        assertThrows(IOException.class, () -> gzipBounded(result, List.of("small typed input"), metadata, 4096));
        assertFalse(Files.exists(result));
    }
    @Test void keepsIndependentG2LimitsAndOldProfileExtent() throws Exception {
        assertEquals(1536, CompleteSourceGraph.Profile.JAVA29_REPAIR_20261023.maxFiles());
        assertEquals(24L << 20, CompleteSourceGraph.Profile.JAVA29_REPAIR_20261023.maxLogicalBytes());
        assertEquals(29L << 20, CompleteSourceGraph.Profile.JAVA29_REPAIR_20261023.maxNativeBytes());
        assertEquals(2304, CompleteSourceGraph.Profile.G2_RESEARCH_20261023.maxFiles());
        assertEquals(36L << 20, CompleteSourceGraph.Profile.G2_RESEARCH_20261023.maxNativeBytes());
        assertEquals(2304, CompleteSourceGraph.Profile.G2_STABILIZATION_20261023.maxFiles());
        assertEquals(32L << 20, CompleteSourceGraph.Profile.G2_STABILIZATION_20261023.maxLogicalBytes());
        assertEquals(44L << 20, CompleteSourceGraph.Profile.G2_STABILIZATION_20261023.maxNativeBytes());
        assertThrows(IllegalArgumentException.class, () -> requireSize(
                new NativeSize(1, 1, 1, 44L << 20, 4096, (44L << 20) + 4096),
                CompleteSourceGraph.Profile.G2_STABILIZATION_20261023));
        assertThrows(IllegalArgumentException.class, () -> requireSize(
                new NativeSize(2305, 1, 2305, 4096, 4096, 8192), CompleteSourceGraph.Profile.G2_RESEARCH_20261023));
        assertThrows(IllegalArgumentException.class, () -> requireSize(
                new NativeSize(1, 1, 33554433, 4096, 4096, 8192), CompleteSourceGraph.Profile.G2_RESEARCH_20261023));
        assertThrows(IllegalArgumentException.class, () -> requireSize(
                new NativeSize(1, 1, 1, 37748736, 4096, 37752832), CompleteSourceGraph.Profile.G2_RESEARCH_20261023));
    }
    @Test void rejectsWrongNativeIdentityTokenTypeAndIncompleteBaselineProof() throws Exception {
        Path source = temporary.resolve("native-source"); Files.writeString(source, "native");
        var nativeWitness = SharedSourceFiles.observe(source);
        ObjectNode bad = ControlBuild.strictMapper().valueToTree(nativeWitness);
        ((ObjectNode) bad.get("native_file")).put("file_id_decimal", 42);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(bad, SharedSourceFiles.Witness.class));
        assertThrows(IllegalArgumentException.class, () -> new NativeProof("xar.complete-source-native-copy-proof/v1",
                WindowsJobProcess.currentMachineId(), java.time.Instant.now().toString(), List.of(nativeWitness), List.of(), List.of()));
        assertNotNull(FileRef.measure(source));
    }

    /** Synthetic source-only DTO metadata; no materialization or software qualification is claimed. */
    @Test void profileSpecificMaterializationAndAuditCountsRoundtripWithoutChangingResearch() throws Exception {
        Path input = temporary.resolve("profile-count-contract.json");
        Files.writeString(input, "synthetic source-only count contract");
        FileRef ref = FileRef.measure(input);
        List<CompleteSourceGraph.ComponentSelection> selections = new ArrayList<>();
        for (CompleteSourceGraph.Component component : CompleteSourceGraph.Component.values()) {
            selections.add(new CompleteSourceGraph.ComponentSelection(component, ref, List.of(
                    new CompleteSourceGraph.SelectedFile(component == CompleteSourceGraph.Component.BUILD_TOOLS
                            ? "build-tools/pom.xml" : "contracts/pom.xml", ref))));
        }
        for (CompleteSourceGraph.Profile profile : List.of(CompleteSourceGraph.Profile.G2_RESEARCH_20261023,
                CompleteSourceGraph.Profile.G2_STABILIZATION_20261023)) {
            int children = profile.childModules(), reactor = profile.reactorProjects();
            Card card = new Card("xar.complete-source-graph-operation-card/v1", "synthetic-count-machine",
                    "/root/source03_audit", "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z",
                    Operation.MATERIALIZE, ref, ref, ref, ref, ref, ref, null,
                    temporary.resolve("new-source").toString(), temporary.resolve("new-metadata").toString(),
                    profile.maxNativeBytes(), 4L << 20, "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
            var cardMapper = ControlBuild.strictMapper();
            assertEquals(card, cardMapper.readValue(cardMapper.writeValueAsBytes(card), Card.class));
            requireProfileBudget(profile, card.maxSourceNativeBytes());
            long otherProfileBudget = profile == CompleteSourceGraph.Profile.G2_RESEARCH_20261023 ? 44L << 20 : 36L << 20;
            assertThrows(IOException.class, () -> requireProfileBudget(profile, otherProfileBudget));
            assertEquals(profile == CompleteSourceGraph.Profile.G2_RESEARCH_20261023 ? 30 : 31, children);
            NativeSize size = new NativeSize(1, 1, ref.bytes(), 4096, 4096, 8192);
            var receipt = new Receipt("xar.complete-source-materialization-actual/v1", "synthetic-count-machine",
                    "2026-10-23T00:00:00Z", Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME,
                    profile, temporary.toString(), children, reactor, 1, size,
                    ref, ref, ref, ref, ref, ref, ref, Check.MATCH, Check.MATCH, Check.MATCH);
            var mapper = ControlBuild.strictMapper();
            assertEquals(receipt, mapper.readValue(mapper.writeValueAsBytes(receipt), Receipt.class));
            ObjectNode wrong = mapper.valueToTree(receipt);
            wrong.put("child_modules", children == 30 ? 31 : 30);
            assertThrows(IOException.class, () -> mapper.treeToValue(wrong, Receipt.class));
            ObjectNode fractional = mapper.valueToTree(receipt); fractional.put("reactor_projects", (double) reactor);
            assertThrows(IOException.class, () -> mapper.treeToValue(fractional, Receipt.class));
            var audit = new CompleteSourceGraphAudit.Manifest("xar.complete-source-independent-manifest/v1",
                    "synthetic-count-machine", "2026-10-23T00:00:00Z",
                    CompleteSourceGraphAudit.Verification.COMPLETE_PLAN_ORIGINS_AND_MATERIALIZED_TREE,
                    Qualification.SOURCE_ONLY_NOT_COMPILED_NOT_TESTED_NOT_GAME, profile, temporary.toString(),
                    1, children, reactor, size, ref, ref, ref, ref, ref, ref, ref, ref, ref, ref,
                    selections, Check.MATCH, Check.MATCH, Check.MATCH);
            assertEquals(audit, mapper.readValue(mapper.writeValueAsBytes(audit), CompleteSourceGraphAudit.Manifest.class));
            var original = SharedSourceFiles.observe(input);
            CopyRow copied = copy("contracts/src/main/resources/counts.json", original,
                    temporary.resolve("counts-" + profile.name() + ".json"));
            assertTrue(CompleteSourceGraphAudit.negativeCases(mapper.writeValueAsBytes(audit), copied) > 0);
            ObjectNode wrongAudit = mapper.valueToTree(audit); wrongAudit.put("reactor_projects", reactor == 31 ? 32 : 31);
            assertThrows(IOException.class, () -> mapper.treeToValue(wrongAudit, CompleteSourceGraphAudit.Manifest.class));
        }
    }

    /** Actual archive/card boundary; these tiny fixtures never qualify a production runtime or graph. */
    @Test void expiredBuildWindowKeepsHistoricalQualificationWithAFreshCard() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("historical"), Operation.MATERIALIZE, false);
        String originalReview = ControlBuild.strictMapper().readTree(Files.readAllBytes(fixture.archive().releasePath()))
                .get("review_at_utc").textValue();
        assertTrue(Instant.now().isAfter(Instant.parse(originalReview)));
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(fixture.archive().receiptPath()));
        ControlBuild.BuildReceipt accepted = completedReceipt(fixture.card(), fixture.card().planRef(), fixture.cardRef());
        assertEquals("PASS", accepted.status());
        assertEquals(fixture.archive().receipt().observedAtUtc(), accepted.observedAtUtc());
        assertNoOperationOutputs(fixture);
    }

    @Test void expiredCurrentMaterializeCardRejectsBeforeAnyOutput() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("expired-copy"), Operation.MATERIALIZE, true);
        IOException failure = assertThrows(IOException.class,
                () -> materialize(fixture.plan(), fixture.card().planRef(), fixture.card(), fixture.cardRef()));
        assertTrue(failure.getMessage().contains("operation card expired"));
        assertNoOperationOutputs(fixture);
    }

    @Test void expiredCurrentAuditCardRejectsBeforeProducerReadOrAnyOutput() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("expired-audit"), Operation.INDEPENDENT_AUDIT, true);
        IOException failure = assertThrows(IOException.class,
                () -> CompleteSourceGraphAudit.audit(fixture.plan(), fixture.card(), fixture.cardRef()));
        assertTrue(failure.getMessage().contains("operation card expired"));
        assertNoOperationOutputs(fixture);
    }

    @Test void forgedCompletionOutsideTheOriginalWindowCannotAdmitAFreshCard() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("forged-completion"), Operation.MATERIALIZE, false);
        ObjectNode changed = ControlBuild.strictMapper().valueToTree(fixture.archive().receipt());
        changed.put("observed_at_utc", Instant.now().plusSeconds(3600).toString());
        assertCompletedReceiptRejected(fixture, changed);
    }

    @Test void redHistoricalBuildCannotAdmitAFreshCard() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("red-archive"), Operation.MATERIALIZE, false);
        ObjectNode changed = ControlBuild.strictMapper().valueToTree(fixture.archive().receipt());
        changed.put("status", "RED"); changed.put("error", "synthetic negative archive fixture");
        assertCompletedReceiptRejected(fixture, changed);
    }

    @Test void changedHistoricalSourceCannotAdmitAFreshCard() throws Exception {
        AdmissionFixture fixture = admissionFixture(temporary.resolve("changed-archive"), Operation.MATERIALIZE, false);
        Path source = fixture.archive().sourceRoot().resolve("pom.xml");
        Files.writeString(source, Files.readString(source) + "\n");
        assertThrows(IOException.class,
                () -> completedReceipt(fixture.card(), fixture.card().planRef(), fixture.cardRef()));
        assertNoOperationOutputs(fixture);
    }

    @Test void changedStandingOrAllocationCannotReuseAFreshOperationCard() throws Exception {
        for (boolean standing : List.of(true, false)) {
            AdmissionFixture fixture = admissionFixture(temporary.resolve(standing ? "changed-standing" : "changed-allocation"),
                    Operation.MATERIALIZE, false);
            FileRef reference = standing ? fixture.card().sourceStandingRef() : fixture.card().rootAllocationRef();
            Files.writeString(Path.of(reference.path()), "changed exact live-authority fixture");
            assertThrows(IOException.class,
                    () -> completedReceipt(fixture.card(), fixture.card().planRef(), fixture.cardRef()));
            assertNoOperationOutputs(fixture);
        }
    }

    private record AdmissionFixture(ControlBuildTest.CompletedReceiptFixture archive, CompleteSourceGraph.Plan plan,
                                    Card card, FileRef cardRef) { }

    private static AdmissionFixture admissionFixture(Path root, Operation operation, boolean expired) throws Exception {
        Files.createDirectories(root);
        ControlBuildTest.CompletedReceiptFixture archive = ControlBuildTest.completedReceiptFixture(root.resolve("archive"));
        String machine = WindowsJobProcess.currentMachineId();
        Instant now = Instant.now();
        FileRef seed = fixtureFile(root.resolve("selection.json"), "{}");
        List<CompleteSourceGraph.ComponentSelection> selections = new ArrayList<>();
        for (CompleteSourceGraph.Component component : CompleteSourceGraph.Component.values()) {
            selections.add(new CompleteSourceGraph.ComponentSelection(component, seed,
                    List.of(new CompleteSourceGraph.SelectedFile("build-tools/fixture-" + component.name() + ".txt", seed))));
        }
        CompleteSourceGraph.Profile profile = CompleteSourceGraph.Profile.G2_RESEARCH_20261023;
        CompleteSourceGraph.Plan plan = new CompleteSourceGraph.Plan("xar.complete-java-source-graph-plan/v1", machine,
                now.toString(), CompleteSourceGraph.SelectionStatus.SOURCE_SELECTION_ONLY, profile,
                new CompleteSourceGraph.Baseline(archive.sourceRoot().toString(), seed),
                CompleteSourceGraph.modules(profile), selections, List.of());
        Path planPath = root.resolve("source-plan.json");
        Files.write(planPath, ControlBuild.strictMapper().writeValueAsBytes(plan));
        FileRef planRef = FileRef.measure(planPath);
        FileRef standing = fixtureFile(root.resolve("source-standing.json"),
                "{\"schema\":\"xar.java-phase1.resume56-standing-source/v1\",\"machine_id\":\"" + machine
                + "\",\"owner\":\"/root\",\"status\":\"SOURCE_WRITES_ADMITTED_CURRENT56_WINDOW02\","
                + "\"observed_at_utc\":\"" + now + "\",\"review_at_utc\":\"" + now.plusSeconds(60) + "\"}");
        FileRef allocation = fixtureFile(root.resolve("root-allocation.json"),
                "{\"schema\":\"xar.java-phase1.g2-full-source-financial-reservation/v1\",\"machine_id\":\"" + machine
                + "\",\"owner\":\"/root\",\"status\":\"FINANCIAL_RESERVED_OPERATION_NOT_YET_ADMITTED\","
                + "\"observed_at_utc\":\"" + now + "\",\"review_at_utc\":\"" + now.plusSeconds(60) + "\"}");
        FileRef materializer = fixtureFile(root.resolve("materializer-source.java"), "// synthetic source reference only\n");
        FileRef contract = fixtureFile(root.resolve("contract-source.java"), "// synthetic source reference only\n");
        FileRef producer = operation == Operation.INDEPENDENT_AUDIT
                ? fixtureFile(root.resolve("unread-producer.json"), "intentionally invalid; expired card must reject before reading") : null;
        Card card = new Card("xar.complete-source-graph-operation-card/v1", machine, "/root/source03_audit",
                now.minusSeconds(expired ? 60 : 1).toString(), now.plusSeconds(expired ? -1 : 60).toString(),
                operation, planRef, archive.receiptRef(), standing, allocation, materializer, contract, producer,
                root.resolve("new-source").toString(), root.resolve("new-metadata").toString(), 36L << 20, 4L << 20,
                "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
        Path cardPath = root.resolve("operation-card.json");
        Files.write(cardPath, ControlBuild.strictMapper().writeValueAsBytes(card));
        return new AdmissionFixture(archive, plan, card, FileRef.measure(cardPath));
    }

    private static FileRef fixtureFile(Path path, String contents) throws IOException {
        Files.writeString(path, contents); return FileRef.measure(path);
    }

    private static void assertCompletedReceiptRejected(AdmissionFixture fixture, ObjectNode changed) throws Exception {
        Path negativePath = Path.of(fixture.cardRef().path()).resolveSibling("negative-build.json");
        Files.write(negativePath, ControlBuild.strictMapper().writeValueAsBytes(changed));
        Card old = fixture.card();
        Card changedCard = new Card(old.schema(), old.machineId(), old.owner(), old.observedAtUtc(), old.reviewAtUtc(),
                old.operation(), old.planRef(), FileRef.measure(negativePath), old.sourceStandingRef(), old.rootAllocationRef(),
                old.materializerSourceRef(), old.graphContractSourceRef(), old.producerActualRef(), old.sourceRoot(),
                old.metadataRoot(), old.maxSourceNativeBytes(), old.maxMetadataNativeBytes(), old.status());
        Path changedCardPath = Path.of(fixture.cardRef().path()).resolveSibling("negative-card.json");
        Files.write(changedCardPath, ControlBuild.strictMapper().writeValueAsBytes(changedCard));
        FileRef changedCardRef = FileRef.measure(changedCardPath);
        assertThrows(IOException.class, () -> completedReceipt(changedCard, changedCard.planRef(), changedCardRef));
        assertNoOperationOutputs(fixture);
    }

    private static void assertNoOperationOutputs(AdmissionFixture fixture) {
        assertTrue(Files.notExists(Path.of(fixture.card().sourceRoot())));
        assertTrue(Files.notExists(Path.of(fixture.card().metadataRoot())));
    }
}

