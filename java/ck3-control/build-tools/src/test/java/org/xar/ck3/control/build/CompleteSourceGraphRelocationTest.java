package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Plan;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class CompleteSourceGraphRelocationTest {
    @TempDir Path temporary;

    @Test void baselineCurrentAndAlreadyExistingDestinationsRelocateWithAllOriginalsPreserved() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        Plan plan = SourceRelocationTestSupport.produce(fixture);
        assertEquals(CompleteSourceGraph.RELOCATION_PLAN_SCHEMA, plan.schema());
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
        var proof = CompleteSourceGraph.resolve(plan);
        var targets = proof.files().stream().map(CompleteSourceGraph.ResolvedFile::targetRelative).toList();
        for (Relocation move : plan.relocations()) {
            assertFalse(targets.contains(move.oldTargetRelative())); assertTrue(targets.contains(move.newTargetRelative()));
            assertTrue(Files.exists(Path.of(move.sourceRef().path())));
            assertTrue(proof.selections().stream().flatMap(selection -> selection.files().stream())
                    .noneMatch(file -> file.targetRelative().equals(move.oldTargetRelative())));
        }
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
        Path encoded = temporary.resolve("plan.json"); Files.write(encoded, CompleteSourceGraph.encodePlan(plan));
        assertEquals(plan, CompleteSourceGraph.readPlan(FileRef.measure(encoded)));
        assertEquals(proof, CompleteSourceGraph.resolve(CompleteSourceGraph.readPlan(FileRef.measure(encoded))));
    }
    @Test void v1WireAndProtectedBaselineRemainUnchangedAndCannotSmuggleRelocations() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        Plan moved = SourceRelocationTestSupport.produce(fixture);
        Plan old = new Plan(CompleteSourceGraph.PLAN_SCHEMA, moved.machineId(), moved.observedAtUtc(), moved.status(),
                moved.profile(), moved.baseline(), moved.modules(), moved.selections(), moved.overlays());
        byte[] encoded = CompleteSourceGraph.encodePlan(old);
        String json = new String(encoded, java.nio.charset.StandardCharsets.UTF_8);
        assertFalse(json.contains("\"relocations\""));
        assertEquals(old, ControlBuild.strictMapper().readValue(encoded, Plan.class));
        assertTrue(CompleteSourceGraph.resolve(old).files().stream().anyMatch(file -> file.targetRelative().equals(SourceRelocationTestSupport.BASE_OLD)));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                json.substring(0, json.length() - 1) + ",\"relocations\":[]}", Plan.class));
        assertThrows(IllegalArgumentException.class, () -> new Plan(CompleteSourceGraph.PLAN_SCHEMA,
                moved.machineId(), moved.observedAtUtc(), moved.status(), moved.profile(), moved.baseline(), moved.modules(),
                moved.selections(), moved.overlays(), moved.relocations()));
    }
    @Test void duplicateCycleMissingOldAndDifferentSourceMovesFail() throws IOException {
        Plan plan = SourceRelocationTestSupport.produce(SourceRelocationTestSupport.fixture(temporary));
        Relocation first = plan.relocations().getFirst();
        List<Relocation> duplicate = new ArrayList<>(plan.relocations()); duplicate.add(first);
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, duplicate)));
        Relocation reverse = new Relocation(first.newTargetRelative(), first.oldTargetRelative(), first.sourceRef(), first.selectionRef());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, List.of(first, reverse))));
        Relocation missing = new Relocation("wave2-runtime/src/main/java/org/absent/Retained.java", first.newTargetRelative(),
                first.sourceRef(), first.selectionRef());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, List.of(missing))));
        FileRef alien = SourceRelocationTestSupport.write(temporary.resolve("alien.java"), "package org.example; final class Retained { int changed; }");
        Relocation wrong = new Relocation(first.oldTargetRelative(), first.newTargetRelative(), alien, first.selectionRef());
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, List.of(wrong))));
        assertThrows(IllegalArgumentException.class, () -> new Relocation("contracts/pom.xml", "local-service/pom.xml", first.sourceRef(), first.selectionRef()));
        assertThrows(IllegalArgumentException.class, () -> new Relocation(first.oldTargetRelative(),
                "local-service/src/test/java/org/example/Retained.java", first.sourceRef(), first.selectionRef()));
    }
    @Test void authorityMachineAndCompleteDeclaredSetAreMandatory() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        Plan plan = SourceRelocationTestSupport.produce(fixture);
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, plan.relocations().subList(0, 1))));
        String old = Files.readString(Path.of(fixture.authority().path()));
        FileRef foreign = SourceRelocationTestSupport.write(temporary.resolve("foreign.json"), old.replace(SourceRelocationTestSupport.MACHINE, "another-machine"));
        List<Relocation> foreignMoves = plan.relocations().stream().map(move -> new Relocation(move.oldTargetRelative(),
                move.newTargetRelative(), move.sourceRef(), foreign)).toList();
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, foreignMoves)));
        Files.writeString(Path.of(fixture.authority().path()), old + " ");
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(plan));
    }
    @Test void v2StrictWireRejectsMissingNullWrongTypeAndUnknownMoveFields() throws IOException {
        Plan plan = SourceRelocationTestSupport.produce(SourceRelocationTestSupport.fixture(temporary));
        var mapper = ControlBuild.strictMapper();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(CompleteSourceGraph.encodePlan(plan));
        tree.remove("relocations"); assertThrows(IOException.class, () -> mapper.treeToValue(tree, Plan.class));
        tree.set("relocations", com.fasterxml.jackson.databind.node.NullNode.instance); assertThrows(IOException.class, () -> mapper.treeToValue(tree, Plan.class));
        tree.set("relocations", mapper.valueToTree(plan.relocations()));
        var move = (com.fasterxml.jackson.databind.node.ObjectNode) tree.path("relocations").get(0);
        move.put("old_target_relative", true); assertThrows(IOException.class, () -> mapper.treeToValue(tree, Plan.class));
        move.put("old_target_relative", plan.relocations().getFirst().oldTargetRelative()); move.put("old_alias", "ignored");
        assertThrows(IOException.class, () -> mapper.treeToValue(tree, Plan.class));
    }

    @Test void latestOwnerRevisionAtOldTargetMovesWithoutChangingOriginalMoveAuthority() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        FileRef updated = SourceRelocationTestSupport.write(temporary.resolve("Retained-revision.java"),
                "package org.example; final class Retained { int actualNewBehavior; }\n");
        FileRef revision = SourceRelocationTestSupport.json(temporary.resolve("revision-owner.json"),
                new SourceRelocationTestSupport.Owner("xar.java.effective-source-selection/v1", SourceRelocationTestSupport.MACHINE,
                        "/root/save_restore", List.of(new SelectedFile(SourceRelocationTestSupport.BASE_OLD, updated)), List.of()));
        var original = fixture.input();
        List<Source08Assembly.OwnerInput> owners = new ArrayList<>(original.owners());
        owners.add(new Source08Assembly.OwnerInput("revision-owner", "/root/save_restore", CompleteSourceGraph.Component.COMMON,
                Source08Assembly.TargetScope.REACTOR_ONLY, revision));
        var first = original.relocations().getFirst();
        List<Relocation> moves = new ArrayList<>(original.relocations());
        moves.set(0, new Relocation(first.oldTargetRelative(), first.newTargetRelative(), first.sourceRef(), first.selectionRef(),
                updated, revision, SourceRelocationTestSupport.BASE_OLD));
        var input = new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA, original.machineId(), original.observedAtUtc(),
                original.plan16RequestRef(), original.source07RequestRef(), original.profile(), original.modules(), owners,
                original.replacementWinners(), moves);
        var request = Source08Assembly.prepare(input);
        Plan plan = SourceGraphPlanProducer.produce(SourceRelocationTestSupport.json(temporary.resolve("revision-request.json"), request));
        var proof = CompleteSourceGraph.resolve(plan);
        assertEquals(updated, proof.files().stream().filter(file -> file.targetRelative().equals(first.newTargetRelative()))
                .findFirst().orElseThrow().sourceRef());
        assertTrue(proof.files().stream().noneMatch(file -> file.targetRelative().equals(first.oldTargetRelative())));
        assertEquals(first.sourceRef(), plan.relocations().getFirst().sourceRef());
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
        assertEquals(plan, ControlBuild.strictMapper().readValue(CompleteSourceGraph.encodePlan(plan), Plan.class));
        assertTrue(proof.selections().stream().flatMap(selection -> selection.files().stream())
                .anyMatch(file -> file.targetRelative().equals(first.newTargetRelative()) && file.sourceRef().equals(updated)));
        var wrong = new ArrayList<>(moves);
        wrong.set(0, new Relocation(first.oldTargetRelative(), first.newTargetRelative(), first.sourceRef(), first.selectionRef(),
                updated, first.selectionRef(), SourceRelocationTestSupport.BASE_OLD));
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, wrong)));
        Path root = temporary.resolve("revision-materialized");
        var pins = SourceRelocationTestSupport.copyFinal(plan, root);
        CompleteSourceGraphMaterializer.verifyCanonical(plan, root, pins);
        assertEquals(Files.readString(Path.of(updated.path())), Files.readString(root.resolve(first.newTargetRelative())));
    }

    @Test void v2RequiresAllCurrentRevisionFieldsAndRejectsUnrelatedOwnerTarget() throws IOException {
        Plan plan = SourceRelocationTestSupport.produce(SourceRelocationTestSupport.fixture(temporary));
        var mapper = ControlBuild.strictMapper();
        for (String field : List.of("final_source_ref", "final_selection_ref", "final_owner_target_relative")) {
            var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(plan);
            ((com.fasterxml.jackson.databind.node.ObjectNode) tree.path("relocations").get(0)).remove(field);
            assertThrows(IOException.class, () -> mapper.treeToValue(tree, Plan.class));
        }
        var move = plan.relocations().getFirst();
        assertThrows(IllegalArgumentException.class, () -> new Relocation(move.oldTargetRelative(), move.newTargetRelative(),
                move.sourceRef(), move.selectionRef(), move.finalSourceRef(), move.finalSelectionRef(),
                "application/src/main/java/org/example/Unrelated.java"));
    }
}
