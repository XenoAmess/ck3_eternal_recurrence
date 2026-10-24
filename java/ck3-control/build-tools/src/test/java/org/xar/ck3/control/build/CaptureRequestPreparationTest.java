package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** The three actual metadata failures; this suite grants no caller/capture qualification. */
final class CaptureRequestPreparationTest {
    @TempDir Path temporary;

    private ControlBuild.FileRef file(String name, String text) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, text); return ControlBuild.FileRef.measure(path);
    }
    private ControlBuild.FileRef binding(String observed, String review) throws IOException {
        var mapper = ControlBuild.strictMapper();
        var standing = mapper.createObjectNode();
        standing.put("schema", "unit.standing/v1"); standing.put("status", "UNIT_PREPARATION_ONLY");
        standing.put("machine_id", "unit-machine"); standing.put("observed_at_utc", observed); standing.put("review_at_utc", review);
        var standingRef = file("standing-" + review.hashCode() + ".json", mapper.writeValueAsString(standing));
        var pin = file("unit-source.java", "unit source");
        var b = new SharedOwnedCommandBinding(SharedOwnedCommandBinding.SCHEMA, "unit-machine", pin, standingRef, pin,
                temporary, temporary, new SharedOwnedCommandBinding.AuthorityExpectation("unit.standing/v1", "UNIT_PREPARATION_ONLY"),
                new SharedOwnedCommandBinding.AuthorityExpectation("unit.delivery/v1", "UNIT_PREPARATION_ONLY"));
        return file("binding-" + review.hashCode() + ".json", mapper.writeValueAsString(b.toJson()));
    }
    @Test void reviewComesFromPinnedStandingNotItsPastObservation() throws Exception {
        var deadline = Instant.now().plusSeconds(120);
        var binding = binding("2000-01-01T00:00:00Z", deadline.toString());
        var executable = file("java.exe", "executable identity");
        Path parent = temporary.resolve("family"); Files.createDirectory(parent);
        var p = CaptureRequestPreparation.prepare(parent, "SIX03", binding, executable, List.of());
        assertEquals(deadline, p.reviewDeadline());
        var expired = binding("1999-01-01T00:00:00Z", "2000-01-01T00:00:00Z");
        assertThrows(IOException.class, () -> CaptureRequestPreparation.prepare(parent, "SIX04", expired, executable, List.of()));
    }
    @Test void freshParentProjectsRecipeRequestAndResultTogether() throws Exception {
        var binding = binding("2000-01-01T00:00:00Z", Instant.now().plusSeconds(120).toString());
        var executable = file("java.exe", "executable identity");
        Path oldParent = temporary.resolve("old01"), newParent = temporary.resolve("new03");
        Files.createDirectory(oldParent); Files.createDirectory(newParent);
        Path oldRecipe = oldParent.resolve("SIX-SELECTION01.json"); Files.writeString(oldRecipe, "unchanged selection bytes");
        var p = CaptureRequestPreparation.prepare(newParent, "SIX03", binding, executable, List.of(ControlBuild.FileRef.measure(oldRecipe)));
        assertEquals(newParent, p.recipePath().getParent());
        assertEquals(newParent, p.requestPath().getParent());
        assertEquals(newParent, p.resultPath().getParent());
        assertEquals(3, List.of(p.recipePath(), p.requestPath(), p.resultPath()).stream().distinct().count());
        Files.copy(oldRecipe, p.recipePath());
        assertArrayEquals(Files.readAllBytes(oldRecipe), Files.readAllBytes(p.recipePath()));
        assertThrows(java.nio.file.FileAlreadyExistsException.class, () -> Files.copy(oldRecipe, p.recipePath()));
        assertEquals(List.of(ControlBuild.FileRef.measure(oldRecipe)), p.explicitInputs());
    }
    @Test void implicitExecutableIsRemovedWithoutTrimmingAnyOtherInput() throws Exception {
        var binding = binding("2000-01-01T00:00:00Z", Instant.now().plusSeconds(120).toString());
        var executable = file("java.exe", "executable identity");
        var source = file("source.java", "original source"); var data = file("fixture.json", "producer fixture");
        Path parent = temporary.resolve("family"); Files.createDirectory(parent);
        var p = CaptureRequestPreparation.prepare(parent, "MAIN02", binding, executable, List.of(executable, source, data, executable));
        assertEquals(List.of(source, data), p.explicitInputs());
        var conflicting = new ControlBuild.FileRef(executable.path(), executable.bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> CaptureRequestPreparation.prepare(parent, "MAIN03", binding, executable, List.of(conflicting, source)));
        assertThrows(IOException.class, () -> CaptureRequestPreparation.prepare(parent, "MAIN04", binding, executable, List.of(source, source)));
    }
}

