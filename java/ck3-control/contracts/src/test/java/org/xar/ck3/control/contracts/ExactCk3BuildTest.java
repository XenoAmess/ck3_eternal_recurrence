package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Locale;
import org.junit.jupiter.api.Test;

final class ExactCk3BuildTest {
    @Test void florinRetainsTheActualThreeComponentLauncherVersionAndExactExecutable() {
        var build = ExactCk3Build.CK3_1210;
        assertEquals("1.21.0", build.version());
        assertTrue(build.matches("1.21.0", build.executableSha256().toUpperCase(Locale.ROOT)));
        for (String foreignVersion : new String[]{"1.21.0.0", "1.21.0 (Florin)", "1.20.0.4", "1.21.1"}) {
            assertFalse(build.matches(foreignVersion, build.executableSha256()), foreignVersion);
        }
        assertFalse(build.matches("1.21.0", ExactCk3Build.CK3_12004.executableSha256()));
        assertFalse(build.matches("1.21.0", null));
        assertFalse(build.matches("1.21.0", "0".repeat(64)));
    }

    @Test void existingFrozenIdentityRemainsIndependentOfTheNewRegistration() {
        var previous = ExactCk3Build.CK3_12004;
        assertTrue(previous.matches("1.20.0.4", previous.executableSha256()));
        assertFalse(previous.matches("1.20.0.4", ExactCk3Build.CK3_1210.executableSha256()));
        assertFalse(previous.matches("1.21.0", previous.executableSha256()));
    }
}
