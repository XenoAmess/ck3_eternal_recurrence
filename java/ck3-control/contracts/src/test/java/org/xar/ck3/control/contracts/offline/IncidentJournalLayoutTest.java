package org.xar.ck3.control.contracts.offline;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

final class IncidentJournalLayoutTest {
    @TempDir Path temporary;
    @Test void completeGameSessionEpisodeAndExactSourceEachBindTheDerivedPair() {
        Path incidents = temporary.resolve("incidents"), scans = temporary.resolve("scans");
        var game = new GameGeneration(999, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var source = new ExactRef(temporary.resolve("source.json").toString(), 1, "a".repeat(64));
        var original = IncidentJournalLayout.scope(incidents, scans, "fixture-machine", game, "session", "episode", source);
        assertEquals(original, IncidentJournalLayout.scope(incidents, scans, "fixture-machine", game, "session", "episode", source));
        assertTrue(original.incidentRoot().getFileName().toString().matches("[0-9a-f]{64}")); assertEquals(original.incidentRoot().getFileName(), original.scanRoot().getFileName());
        assertNotEquals(original, IncidentJournalLayout.scope(incidents, scans, "other-machine", game, "session", "episode", source));
        assertNotEquals(original, IncidentJournalLayout.scope(incidents, scans, "fixture-machine", new GameGeneration(999, new PythonOnlyUInt64(new BigInteger("134000000000000002"))), "session", "episode", source));
        assertNotEquals(original, IncidentJournalLayout.scope(incidents, scans, "fixture-machine", game, "another-session", "episode", source));
        assertNotEquals(original, IncidentJournalLayout.scope(incidents, scans, "fixture-machine", game, "session", "another-episode", source));
        assertNotEquals(original, IncidentJournalLayout.scope(incidents, scans, "fixture-machine", game, "session", "episode", new ExactRef(source.path(), 1, "b".repeat(64))));
    }
    @Test void rootsAreCanonicalSeparateServerBasesAndNeverArbitraryRelativeParents() {
        var game = new GameGeneration(1, new PythonOnlyUInt64(BigInteger.ONE));
        var source = new ExactRef(temporary.resolve("source").toString(), 1, "a".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> IncidentJournalLayout.scope(Path.of("relative"), temporary.resolve("s"), "fixture", game, "s", "e", source));
        assertThrows(IllegalArgumentException.class, () -> IncidentJournalLayout.scope(temporary, temporary.resolve("nested"), "fixture", game, "s", "e", source));
        assertThrows(IllegalArgumentException.class, () -> IncidentJournalLayout.scope(temporary.resolve("i"), temporary.resolve("s"), "unknown", game, "s", "e", source));
        assertThrows(IllegalArgumentException.class, () -> IncidentJournalLayout.scope(temporary.resolve("i"), temporary.resolve("s"), "fixture", game, "s", "e", new ExactRef("relative-source", 1, "a".repeat(64))));
    }
}
