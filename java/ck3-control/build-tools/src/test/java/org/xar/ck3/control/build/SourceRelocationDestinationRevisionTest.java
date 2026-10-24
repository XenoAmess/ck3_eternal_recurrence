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
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Winner;

/** The actual NEXT preview updates a moved test at its destination while retaining the old move authority. */
final class SourceRelocationDestinationRevisionTest {
    @TempDir Path temporary;

    @Test void actualCanonicalSourceProducerStillRejectsAnUnrelatedParentWithTheSameModuleRoster() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        Path pom = fixture.root().resolve("pom.xml");
        Files.writeString(pom, Files.readString(pom).replace(SourceRelocationTestSupport.CONTROL_PARENT, "unrelated-parent"));
        IOException failure = assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                SourceRelocationTestSupport.PROFILE.sourceLimitProfile()));
        assertTrue(failure.getMessage().contains("Finite migration profile requires the existing control parent"));
    }

    @Test void currentDestinationRevisionWinsWhileOriginalAuthorityAndBaselineRemainExact() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var original = fixture.input();
        var first = original.relocations().getFirst();
        FileRef revised = SourceRelocationTestSupport.write(temporary.resolve("current-Retained.java"),
                "package org.example; final class Retained { int destinationRevision; }\n");
        FileRef authority = SourceRelocationTestSupport.json(temporary.resolve("current-destination-owner.json"),
                new SourceRelocationTestSupport.Owner("xar.java.effective-source-selection/v1", original.machineId(),
                        "/root/campaign_goals", List.of(new SelectedFile(first.newTargetRelative(), revised)), List.of()));
        List<Source08Assembly.OwnerInput> owners = new ArrayList<>(original.owners());
        owners.add(new Source08Assembly.OwnerInput("current-destination-owner", "/root/campaign_goals",
                CompleteSourceGraph.Component.COMMON, Source08Assembly.TargetScope.REACTOR_ONLY, authority));
        List<Relocation> moves = new ArrayList<>(original.relocations());
        moves.set(0, new Relocation(first.oldTargetRelative(), first.newTargetRelative(), first.sourceRef(), first.selectionRef(),
                revised, authority, first.newTargetRelative()));
        var input = new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA, original.machineId(), original.observedAtUtc(),
                original.plan16RequestRef(), original.source07RequestRef(), original.profile(), original.modules(), owners,
                List.of(new Winner(first.newTargetRelative(), "current-destination-owner")), moves);
        var request = Source08Assembly.prepare(input);
        var plan = SourceGraphPlanProducer.produce(SourceRelocationTestSupport.json(temporary.resolve("destination-request.json"), request));
        var proof = CompleteSourceGraph.resolve(plan);
        assertEquals(revised, proof.files().stream().filter(file -> file.targetRelative().equals(first.newTargetRelative()))
                .findFirst().orElseThrow().sourceRef());
        assertFalse(proof.files().stream().anyMatch(file -> file.targetRelative().equals(first.oldTargetRelative())));
        assertEquals(first.sourceRef(), plan.relocations().getFirst().sourceRef());
        assertEquals(first.selectionRef(), plan.relocations().getFirst().selectionRef());
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
        assertEquals(plan, ControlBuild.strictMapper().readValue(CompleteSourceGraph.encodePlan(plan), CompleteSourceGraph.Plan.class));
        Path root = temporary.resolve("destination-materialized");
        var pins = SourceRelocationTestSupport.copyFinal(plan, root);
        CompleteSourceGraphMaterializer.verifyCanonical(plan, root, pins);
        assertEquals(Files.readString(Path.of(revised.path())), Files.readString(root.resolve(first.newTargetRelative())));
        var wrong = new ArrayList<>(moves);
        wrong.set(0, new Relocation(first.oldTargetRelative(), first.newTargetRelative(), first.sourceRef(), first.selectionRef(),
                revised, authority, first.oldTargetRelative()));
        assertThrows(IOException.class, () -> CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan, wrong)));
    }
}
