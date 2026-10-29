package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.file.Path;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

/** Argument metadata only; these tests do not qualify a capture or create a child. */
final class CaptureTimelineOwnerArgumentsTest {
    private static String path(String name) {
        return Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().resolve(name).toString();
    }
    private static String[] golden() {
        return new String[] {path("python.exe"), path("graph"), path("inputs.json"), path("new.json"),
                path("REFERENCE-ACTUAL.json"), "1", "a".repeat(64)};
    }
    @Test void originalGoldenRetainsAllThreeSelectedActualFields() {
        var input = CaptureTimelineOwnerGolden.invocation(golden());
        assertEquals(CaptureTimelineOwnerGolden.CaptureMode.GOLDEN, input.mode());
        assertEquals(Arrays.asList(golden()).subList(1, 7),
                CaptureTimelineOwnerGolden.programArguments(input, path("java.exe"), "qualified-classpath"));
    }
    @Test void differentialAppendsRuntimeAfterTheCompleteSelectedActual() {
        String[] args = Arrays.copyOf(golden(), 8); args[7] = "DIFFERENTIAL";
        var input = CaptureTimelineOwnerGolden.invocation(args);
        var python = CaptureTimelineOwnerGolden.programArguments(input, path("java.exe"), "qualified-classpath");
        assertEquals(CaptureTimelineOwnerGolden.CaptureMode.DIFFERENTIAL, input.mode());
        assertEquals(Arrays.asList(golden()).subList(1, 7), python.subList(0, 6));
        assertEquals(path("java.exe"), python.get(6)); assertEquals("qualified-classpath", python.get(7));
    }
    @Test void ambiguousMissingOrUnboundedArgumentsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> CaptureTimelineOwnerGolden.invocation(Arrays.copyOf(golden(), 6)));
        String[] unknown = Arrays.copyOf(golden(), 8); unknown[7] = "GOLDEN";
        assertThrows(IllegalArgumentException.class, () -> CaptureTimelineOwnerGolden.invocation(unknown));
        for (String bytes : new String[] {"true", "1.0", "01", "2097153"}) {
            String[] args = golden(); args[5] = bytes;
            assertThrows(IllegalArgumentException.class, () -> CaptureTimelineOwnerGolden.invocation(args));
        }
        String[] relative = golden(); relative[4] = "REFERENCE-ACTUAL.json";
        assertThrows(IllegalArgumentException.class, () -> CaptureTimelineOwnerGolden.invocation(relative));
    }
}
