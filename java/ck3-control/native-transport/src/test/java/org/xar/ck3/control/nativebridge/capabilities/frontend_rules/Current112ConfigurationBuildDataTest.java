package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;

final class Current112ConfigurationBuildDataTest {
    private static final String CURRENT="859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28";

    @Test void exactCurrentTupleHasAConfigurationValue() {
        var build=FrontendRulesData.Build.require("1.21.0.3",CURRENT);
        assertEquals("1.21.0.3",build.version());
        assertEquals(CURRENT,build.sha256().toLowerCase(java.util.Locale.ROOT));
        assertEquals(FrontendRulesData.Build.CK3_121003_STEAM_26785313,build);
    }

    @Test void mixedAndUnknownTuplesRemainRejected() {
        assertThrows(IllegalArgumentException.class,()->FrontendRulesData.Build.require("1.21.0",CURRENT));
        assertThrows(IllegalArgumentException.class,()->FrontendRulesData.Build.require("1.21.0.3",ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256()));
        assertThrows(IllegalArgumentException.class,()->FrontendRulesData.Build.require("1.21.0.4",CURRENT));
    }

    @Test void configurationDataDoesNotGrantFrontendRulesOrLoadedFeatures() {
        var build=FrontendRulesData.Build.require("1.21.0.3",CURRENT);
        assertThrows(IllegalArgumentException.class,build::requireFrontend);
        assertThrows(IllegalArgumentException.class,build::requireRules);
        assertThrows(IllegalArgumentException.class,build::requireLoadedFeatures);
        assertThrows(IllegalArgumentException.class,()->new FrontendRulesData.Source(
                new FrontendRulesData.Binding(42,BigInteger.ONE),build));
    }

    @Test void dataAdapterKeepsCoreIdentitySeparateFromIndependentFullSelection() {
        var build=FrontendRulesData.Build.require("1.21.0.3",CURRENT);
        assertEquals(ExactCk3Build.CK3_121003_STEAM_26785313.coreFrameAdapterId(),build.adapterId());
        assertNotEquals(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.coreFullAdapterId(),build.adapterId());
        assertTrue(ExactCk3Build.florinCoreFullBuild(build.version(),build.sha256()).isEmpty());
    }
}
