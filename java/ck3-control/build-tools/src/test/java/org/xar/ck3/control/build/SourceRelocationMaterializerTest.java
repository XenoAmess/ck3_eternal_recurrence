package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class SourceRelocationMaterializerTest {
    @TempDir Path temporary;

    @Test void finalMaterializerAndCanonicalMavenProducerAgreeOnRelocatedTree() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var plan = SourceRelocationTestSupport.produce(fixture);
        Path root = temporary.resolve("materialized");
        var pins = SourceRelocationTestSupport.copyFinal(plan, root);
        CompleteSourceGraphMaterializer.verifyCanonical(plan, root, pins);
        assertEquals(pins, CompleteSourceGraph.verifyMaterialized(plan, root).sourcePins());
        for (var move : plan.relocations()) assertFalse(Files.exists(root.resolve(move.oldTargetRelative())));
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
    }
    @Test void retainedOldTargetAndEqualCountSubstitutionBothFailActualVerifier() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var plan = SourceRelocationTestSupport.produce(fixture);
        Path root = temporary.resolve("materialized");
        var pins = SourceRelocationTestSupport.copyFinal(plan, root);
        var move = plan.relocations().getFirst();
        Path forbidden = root.resolve(move.oldTargetRelative()); Files.createDirectories(forbidden.getParent());
        Files.copy(Path.of(move.sourceRef().path()), forbidden);
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.verifyCanonical(plan, root, pins));
        Files.delete(root.resolve(move.newTargetRelative()));
        var equalCount = ControlBuild.sourceManifest(root, plan.profile().sourceLimitProfile());
        assertEquals(pins.size(), equalCount.size());
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.verifyCanonical(plan, root, equalCount));
    }
    @Test void survivingDestinationMutationCannotPassTheSharedPostcheck() throws IOException {
        var fixture = SourceRelocationTestSupport.fixture(temporary);
        var plan = SourceRelocationTestSupport.produce(fixture);
        Path root = temporary.resolve("materialized");
        var pins = SourceRelocationTestSupport.copyFinal(plan, root);
        Path survivor = root.resolve(plan.relocations().getFirst().newTargetRelative());
        Files.writeString(survivor, "package org.example; final class Retained { int changed; }");
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.verifyCanonical(plan, root, pins));
        assertEquals(fixture.originals(), CompleteSourceGraph.baselineFiles(plan));
    }
}
