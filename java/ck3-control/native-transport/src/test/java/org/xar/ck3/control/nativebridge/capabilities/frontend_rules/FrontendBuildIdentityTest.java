package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

final class FrontendBuildIdentityTest {
    @Test void recognizedFlorinIdentityDoesNotGrantAnUnmigratedFrontendOrRulesRole() {
        var identity = ExactCk3Build.CK3_1210;
        var build = Build.require(identity.version(), identity.executableSha256());
        assertSame(Build.CK3_1210, build);
        assertEquals("ck3-1.21.0-msvc-x64", build.adapterId());
        assertThrows(IllegalArgumentException.class, build::requireFrontend);
        assertThrows(IllegalArgumentException.class, build::requireRules);
        assertThrows(IllegalArgumentException.class, build::requireLoadedFeatures);
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(
                new org.xar.ck3.control.application.action.RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                build, BigInteger.ONE, 0));
        assertThrows(IllegalArgumentException.class, () -> new Source(new Binding(42, BigInteger.ONE), build));
        assertThrows(IllegalArgumentException.class, () -> Build.require("1.21.0.0", identity.executableSha256()));
        assertThrows(IllegalArgumentException.class, () -> Build.require("1.21.0", Build.CK3_12004.sha256()));
    }

    @Test void previouslyAdmittedFrontendRolesAndTheExplicitOldRefusalRemainUnchanged() {
        for (Build build : new Build[]{Build.CK3_11906, Build.CK3_12003, Build.CK3_12004}) {
            assertSame(build, Build.require(build.version(), build.sha256()));
            assertDoesNotThrow(() -> new Source(new Binding(42, BigInteger.ONE), build));
        }
        assertThrows(IllegalArgumentException.class, Build.CK3_12002::requireFrontend);
        assertThrows(IllegalArgumentException.class, Build.CK3_11906::requireRules);
        assertDoesNotThrow(Build.CK3_12003::requireRules);
        assertDoesNotThrow(Build.CK3_12004::requireRules);
        for (Build build : new Build[]{Build.CK3_11906, Build.CK3_12002, Build.CK3_12003, Build.CK3_12004}) {
            assertDoesNotThrow(build::requireLoadedFeatures);
        }
    }
}
