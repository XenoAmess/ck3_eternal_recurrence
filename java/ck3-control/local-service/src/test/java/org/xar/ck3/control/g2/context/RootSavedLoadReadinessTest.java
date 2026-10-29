package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Ordinary software log fixtures. No Game, injection, Steam or Driver/SAVE access. */
final class RootSavedLoadReadinessTest {
    @TempDir Path temporary;
    private static final String SETUP = "[12:34:56][D][gameapplication.cpp:123]: Setup completion (history loaded): 1.25 seconds\n";
    private static final String IN_GAME = "[12:34:57][D][gameapplication.cpp:124]: Setting idler 'In Game' with init options\n";
    private RootSavedLoadReadiness.Prepared prepared() throws IOException {
        return RootSavedLoadReadiness.prepare(Files.createDirectory(temporary.resolve("profile")),
                Files.createDirectory(temporary.resolve("evidence")));
    }
    @Test void originalThreeLogsAreRetainedBeforeFreshEpoch() throws Exception {
        Path profile = Files.createDirectory(temporary.resolve("profile"));
        Path logs = Files.createDirectory(profile.resolve("logs"));
        for (String name : java.util.List.of("debug.log", "error.log", "gui_warnings.log")) Files.writeString(logs.resolve(name), "old-" + name);
        var prepared = RootSavedLoadReadiness.prepare(profile, Files.createDirectory(temporary.resolve("evidence")));
        assertEquals(3, prepared.archived().size());
        for (var old : prepared.archived()) {
            assertFalse(Files.exists(Path.of(old.originalPath())));
            assertEquals("old-" + Path.of(old.originalPath()).getFileName(), Files.readString(Path.of(old.retained().path())));
            old.retained().verify();
        }
        assertNull(RootSavedLoadReadiness.readComplete(prepared));
        assertThrows(IOException.class, () -> RootSavedLoadReadiness.prepare(profile, temporary.resolve("evidence")));
    }
    @Test void bothCompleteOriginalMarkersAreRequiredAndEitherOrderIsAccepted() throws Exception {
        var prepared = prepared();
        Files.writeString(prepared.log(), IN_GAME + SETUP.stripTrailing());
        assertNull(RootSavedLoadReadiness.readComplete(prepared));
        Files.writeString(prepared.log(), IN_GAME + SETUP);
        var ready = RootSavedLoadReadiness.readComplete(prepared);
        assertNotNull(ready); assertEquals(1, ready.inGame().line()); assertEquals(2, ready.setup().line());
        ready.log().verify(); assertEquals(prepared.epoch(), ready.epoch());
    }
    @Test void oldEpochAndPartialSetupCannotGrantReadiness() throws Exception {
        var prepared = prepared(); Files.writeString(prepared.log(), SETUP + IN_GAME);
        Files.setLastModifiedTime(prepared.log(), FileTime.from(prepared.epoch().minusSeconds(1)));
        assertNull(RootSavedLoadReadiness.readComplete(prepared));
        Files.writeString(prepared.log(), SETUP.replace("1.25 seconds", "unknown") + IN_GAME);
        assertNull(RootSavedLoadReadiness.readComplete(prepared));
    }
    @Test void oversizedLineIsTerminalAndLogsCannotMasqueradeAsNativeProof() throws Exception {
        var prepared = prepared(); Files.writeString(prepared.log(), "x".repeat((32 << 10) + 1));
        assertThrows(IOException.class, () -> RootSavedLoadReadiness.readComplete(prepared));
        Files.writeString(prepared.log(), SETUP + IN_GAME);
        assertNotNull(RootSavedLoadReadiness.readComplete(prepared));
    }
}
