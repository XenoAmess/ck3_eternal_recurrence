package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Identity DATA tests only. No packet oracle, Native proof, running process or live role is supplied. */
final class ExactCk3BuildHotfixProfileTest {
    private static final String ORIGINAL="2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc";
    private static final String HOTFIX="bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79";
    @Test void originalMatchesRetainsItsExactFrozenShaAndDoesNotAliasTheHotfix(){
        assertTrue(ExactCk3Build.CK3_1210.matches("1.21.0",ORIGINAL));
        assertFalse(ExactCk3Build.CK3_1210.matches("1.21.0",HOTFIX));
        assertEquals(ORIGINAL,ExactCk3Build.CK3_1210.executableSha256());
        assertFalse(ExactCk3Build.CK3_1210_STEAM_26757580.matches("1.21.0",ORIGINAL));
        assertTrue(ExactCk3Build.CK3_1210_STEAM_26757580.matches("1.21.0",HOTFIX));
    }
    @Test void theTwoCoreFullProfilesKeepDistinctAdapterIdentities(){
        var original=ExactCk3Build.florinCoreFullBuild("1.21.0",ORIGINAL).orElseThrow();
        var hotfix=ExactCk3Build.florinCoreFullBuild("1.21.0",HOTFIX).orElseThrow();
        assertSame(ExactCk3Build.CK3_1210,original);
        assertSame(ExactCk3Build.CK3_1210_STEAM_26757580,hotfix);
        assertEquals("ck3-1.21.0-msvc-x64",original.coreFullAdapterId());
        assertEquals("ck3-1.21.0-26757580-msvc-x64",hotfix.coreFullAdapterId());
        assertNotEquals(original.coreFullAdapterId(),hotfix.coreFullAdapterId());
    }
    @Test void unknownShaWrongVersionAndLegacyBuildCannotSelectTheFlorinCoreFullScope(){
        assertEquals(Optional.empty(),ExactCk3Build.florinCoreFullBuild("1.21.0","0".repeat(64)));
        assertEquals(Optional.empty(),ExactCk3Build.florinCoreFullBuild("1.21.0.0",HOTFIX));
        assertEquals(Optional.empty(),ExactCk3Build.florinCoreFullBuild("1.21.0",null));
        assertEquals(Optional.empty(),ExactCk3Build.florinCoreFullBuild(null,HOTFIX));
        assertEquals(Optional.empty(),ExactCk3Build.florinCoreFullBuild(ExactCk3Build.CK3_12004.version(),ExactCk3Build.CK3_12004.executableSha256()));
    }
}
