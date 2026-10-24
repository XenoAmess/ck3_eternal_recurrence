package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Winner;

/** Real shared generation chain, final retirement, exact gzip export and closed SDK wire boundary. */
final class SourceGraphSdkIndexProducerTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-10-24T00:00:00Z"), ZoneOffset.UTC);
    @TempDir Path temporary;

    private record Generated(Source08Assembly.Input input, FileRef inputRef,
            CompleteSourceGraph.Plan plan, FileRef planRef, FileRef currentRevision) { }

    private Generated generated() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var original = fixture.input();
        var move = original.relocations().getFirst();
        FileRef revised = SourceRelocationTestSupport.write(temporary.resolve("current-Retained.java"),
                "package org.example; final class Retained { int currentDestinationRevision; }\n");
        FileRef authority = SourceRelocationTestSupport.json(temporary.resolve("current-destination-owner.json"),
                new SourceRelocationTestSupport.Owner("xar.java.effective-source-selection/v1", original.machineId(),
                        "/root/campaign_goals", List.of(new SelectedFile(move.newTargetRelative(), revised)), List.of()));
        FileRef empty = SourceRelocationTestSupport.write(temporary.resolve("empty-resource.fixture"), "");
        FileRef resourceMap = SourceRelocationTestSupport.json(temporary.resolve("resource-owner.json"),
                new SourceRelocationTestSupport.Owner("xar.java.effective-source-selection/v1", original.machineId(),
                        "/root/source_graph", List.of(new SelectedFile("local-service/src/test/resources/empty.fixture", empty)), List.of()));
        List<Source08Assembly.OwnerInput> owners = new ArrayList<>(original.owners());
        owners.add(new Source08Assembly.OwnerInput("current-destination-owner", "/root/campaign_goals",
                CompleteSourceGraph.Component.COMMON, Source08Assembly.TargetScope.REACTOR_ONLY, authority));
        owners.add(new Source08Assembly.OwnerInput("resource-owner", "/root/source_graph",
                CompleteSourceGraph.Component.COMMON, Source08Assembly.TargetScope.REACTOR_ONLY, resourceMap));
        List<Relocation> moves = new ArrayList<>(original.relocations());
        moves.set(0, new Relocation(move.oldTargetRelative(), move.newTargetRelative(), move.sourceRef(),
                move.selectionRef(), revised, authority, move.newTargetRelative()));
        var input = new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA, original.machineId(),
                original.observedAtUtc(), original.plan16RequestRef(), original.source07RequestRef(),
                original.profile(), original.modules(), owners,
                List.of(new Winner(move.newTargetRelative(), "current-destination-owner")), moves);
        FileRef inputRef = SourceRelocationTestSupport.json(temporary.resolve("sdk-input.json"), input);
        var request = Source08Assembly.prepare(input);
        FileRef requestRef = SourceRelocationTestSupport.json(temporary.resolve("sdk-actual-request.json"), request);
        var plan = SourceGraphPlanProducer.produce(requestRef);
        FileRef planRef = SourceRelocationTestSupport.json(temporary.resolve("sdk-actual-plan.json"), plan);
        return new Generated(input, inputRef, plan, planRef, revised);
    }

    private FileRef request(Generated generated, Path root) throws IOException {
        return SourceRelocationTestSupport.json(temporary.resolve("sdk-export-request.json"),
                new SourceGraphSdkIndexProducer.Request(SourceGraphSdkIndexProducer.REQUEST_SCHEMA,
                        generated.input().machineId(), generated.inputRef(), generated.planRef(), root.toString()));
    }

    @Test void actualAssemblyRequestPlanRetirementExportsLatestJavaWinnersAndStrictSdkGzip() throws IOException {
        Generated generated = generated();
        var expected = SourceGraphSdkIndexProducer.produce(generated.inputRef(), generated.planRef(), CLOCK);
        Path root = temporary.resolve("exported-index");
        var result = SourceGraphSdkIndexProducer.export(request(generated, root),
                generated.input().machineId(), CLOCK);
        var actual = SourceGraphSdkIndexProducer.readIndex(result.receipt().index(),
                generated.input().machineId(), CLOCK);
        assertEquals(expected, actual);
        assertEquals(8, ControlBuild.strictMapper().readTree(actual.encode()).size());
        assertFalse(actual.parentPomOrderOnlySupersedesInput02());
        assertEquals(generated.inputRef(), actual.inputRef());
        assertEquals(SourceGraphSdkIndexProducer.STATUS, actual.status());
        var proof = CompleteSourceGraph.resolve(generated.plan());
        assertEquals(proof.files().stream().filter(file -> file.targetRelative().endsWith(".java"))
                .map(file -> new SelectedFile(file.targetRelative(), file.sourceRef())).toList(), actual.selectedFiles());
        assertEquals(generated.currentRevision(), actual.selectedFiles().stream()
                .filter(row -> row.targetRelative().equals(SourceRelocationTestSupport.BASE_NEW))
                .findFirst().orElseThrow().sourceRef());
        for (Relocation move : generated.plan().relocations())
            assertFalse(actual.selectedFiles().stream().anyMatch(row -> row.targetRelative().equals(move.oldTargetRelative())));
        assertTrue(proof.files().stream().anyMatch(row -> row.sourceRef().bytes() == 0));
        assertTrue(actual.selectedFiles().stream().allMatch(row -> row.sourceRef().bytes() > 0));
        assertEquals(proof.files().size(), result.receipt().finalFiles());
        assertEquals(actual.selectedFiles().size(), result.receipt().javaWinnerFiles());
        assertEquals(4, result.receipt().retiredTargets());
        assertEquals(result.receipt(), ControlBuild.strictMapper().readValue(
                Files.readAllBytes(Path.of(result.receiptRef().path())), SourceGraphSdkIndexProducer.Receipt.class));
        ObjectNode receiptWire = (ObjectNode) ControlBuild.strictMapper().readTree(
                Files.readAllBytes(Path.of(result.receiptRef().path())));
        ObjectNode requestWire = (ObjectNode) ControlBuild.strictMapper().valueToTree(
                new SourceGraphSdkIndexProducer.Request(SourceGraphSdkIndexProducer.REQUEST_SCHEMA,
                        generated.input().machineId(), generated.inputRef(), generated.planRef(), root.toString()));
        for (String invalidMachine : List.of("-bad", "a".repeat(129))) {
            ObjectNode invalidReceipt = receiptWire.deepCopy(); invalidReceipt.put("machine_id", invalidMachine);
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                    ControlBuild.strictMapper().writeValueAsBytes(invalidReceipt), SourceGraphSdkIndexProducer.Receipt.class));
            ObjectNode invalidRequest = requestWire.deepCopy(); invalidRequest.put("machine_id", invalidMachine);
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                    ControlBuild.strictMapper().writeValueAsBytes(invalidRequest), SourceGraphSdkIndexProducer.Request.class));
        }
        try (var entries = Files.list(root)) { assertEquals(2L, entries.count()); }
    }

    @Test void indexDecoderRejectsMissingUnknownNullCoercedBytesAndCaseAliasedTargets() throws IOException {
        Generated generated = generated();
        var index = SourceGraphSdkIndexProducer.produce(generated.inputRef(), generated.planRef(), CLOCK);
        ObjectNode original = (ObjectNode) ControlBuild.strictMapper().readTree(index.encode());
        ObjectNode badMachine = original.deepCopy(); badMachine.put("machine_id", "Different_MACHINE");
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(badMachine)));
        ObjectNode unknownMachine = original.deepCopy(); unknownMachine.put("machine_id", "unknown");
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(unknownMachine)));
        for (String invalidMachine : List.of("-bad", "a".repeat(129))) {
            ObjectNode invalid = original.deepCopy(); invalid.put("machine_id", invalidMachine);
            assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(
                    ControlBuild.strictMapper().writeValueAsBytes(invalid)));
        }
        ObjectNode maximumMachine = original.deepCopy(); maximumMachine.put("machine_id", "a".repeat(128));
        assertEquals("a".repeat(128), SingleWinnerSourceIndex.decode(
                ControlBuild.strictMapper().writeValueAsBytes(maximumMachine)).machineId());
        ObjectNode missing = original.deepCopy(); missing.remove("parent_pom_order_only_supersedes_input02");
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(missing)));
        ObjectNode unknown = original.deepCopy(); unknown.put("runtime_qualified", true);
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(unknown)));
        ObjectNode nullFlag = original.deepCopy(); nullFlag.putNull("parent_pom_order_only_supersedes_input02");
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(nullFlag)));
        ObjectNode booleanBytes = original.deepCopy();
        ((ObjectNode) booleanBytes.withArray("selected_files").get(0).get("source_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(booleanBytes)));
        ObjectNode floatBytes = original.deepCopy();
        ((ObjectNode) floatBytes.withArray("selected_files").get(0).get("source_ref")).put("bytes", 3.0);
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(floatBytes)));
        ObjectNode aliased = original.deepCopy();
        ObjectNode row = ((ObjectNode) aliased.withArray("selected_files").get(0)).deepCopy();
        String target = row.get("target_relative").textValue();
        row.put("target_relative", target.substring(0, target.lastIndexOf('/') + 1)
                + target.substring(target.lastIndexOf('/') + 1).toUpperCase(java.util.Locale.ROOT));
        aliased.withArray("selected_files").add(row);
        assertThrows(IOException.class, () -> SingleWinnerSourceIndex.decode(ControlBuild.strictMapper().writeValueAsBytes(aliased)));
    }

    @Test void mismatchedExactInputCannotBorrowAnActualPlanOrCreateExportOutput() throws IOException {
        Generated generated = generated();
        var original = generated.input();
        var changed = new Source08Assembly.Input(original.schema(), original.machineId(),
                "2026-10-23T01:00:00Z", original.plan16RequestRef(), original.source07RequestRef(),
                original.profile(), original.modules(), original.owners(), original.replacementWinners(), original.relocations());
        FileRef input = SourceRelocationTestSupport.json(temporary.resolve("different-input.json"), changed);
        Path output = temporary.resolve("must-not-exist");
        FileRef request = SourceRelocationTestSupport.json(temporary.resolve("wrong-input-request.json"),
                new SourceGraphSdkIndexProducer.Request(SourceGraphSdkIndexProducer.REQUEST_SCHEMA,
                        original.machineId(), input, generated.planRef(), output.toString()));
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.export(request, original.machineId(), CLOCK));
        assertFalse(Files.exists(output));
    }

    @Test void handcraftedTypedPlanCannotBypassTheRealRequestProducer() throws IOException {
        Generated generated = generated();
        var plan = generated.plan();
        var changed = new CompleteSourceGraph.Plan(plan.schema(), plan.machineId(), "2026-10-23T01:00:00Z",
                plan.status(), plan.profile(), plan.baseline(), plan.modules(), plan.selections(),
                plan.overlays(), plan.relocations());
        FileRef changedRef = SourceRelocationTestSupport.json(temporary.resolve("handcrafted-plan.json"), changed);
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.produce(generated.inputRef(), changedRef, CLOCK));
    }

    @Test void actualCompressedIndexRequiresExactMachineTimeRawBytesAndSha() throws IOException {
        Generated generated = generated();
        var result = SourceGraphSdkIndexProducer.export(request(generated, temporary.resolve("exact-index")),
                generated.input().machineId(), CLOCK);
        var artifact = result.receipt().index();
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.readIndex(artifact, "different-machine", CLOCK));
        Clock earlier = Clock.fixed(Instant.parse("2026-10-23T23:59:59Z"), ZoneOffset.UTC);
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.readIndex(artifact, generated.input().machineId(), earlier));
        var wrong = new SourceGraphSdkIndexProducer.IndexArtifact(artifact.compressedRef(),
                artifact.uncompressedBytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.readIndex(wrong, generated.input().machineId(), CLOCK));
        var wrongBytes = new SourceGraphSdkIndexProducer.IndexArtifact(artifact.compressedRef(),
                artifact.uncompressedBytes() + 1, artifact.uncompressedSha256());
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.readIndex(wrongBytes, generated.input().machineId(), CLOCK));
    }

    @Test void exportedMetadataNeverOverwritesExistingOutputOrWritesInsideProtectedBaseline() throws IOException {
        Generated generated = generated();
        Path existing = Files.createDirectory(temporary.resolve("existing"));
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.export(
                request(generated, existing), generated.input().machineId(), CLOCK));
        // request() intentionally reuses one path; keep the next exact request in a distinct original file.
        Path inside = Path.of(generated.plan().baseline().root()).resolve("forbidden-index");
        FileRef request = SourceRelocationTestSupport.json(temporary.resolve("inside-request.json"),
                new SourceGraphSdkIndexProducer.Request(SourceGraphSdkIndexProducer.REQUEST_SCHEMA,
                        generated.input().machineId(), generated.inputRef(), generated.planRef(), inside.toString()));
        assertThrows(IOException.class, () -> SourceGraphSdkIndexProducer.export(request, generated.input().machineId(), CLOCK));
        assertFalse(Files.exists(inside));
    }
}
