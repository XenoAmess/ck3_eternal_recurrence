package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.runtime.HostMode;

/** Actual legacy QuarkusApplication.run refusal paths; no Quarkus, transport, Root or Game is started. */
final class PublicMcpRootMainModeTest {
    @Test void completeCompositionRejectsBeforeAccessingOrInstallingALegacyHost() {
        var actual=new RootApplicationMain();actual.mode=HostMode.COMPLETE_MIGRATION;
        assertNull(actual.host,"the complete-composition refusal must not depend on a legacy host");
        assertEquals(78,actual.run());
        var uninstalled=new PublicMcpHost();actual.host=uninstalled;
        assertEquals(78,actual.run());
        assertTrue(uninstalled.mode().isEmpty());assertTrue(uninstalled.current().isEmpty());
    }

    @Test void bothExistingLegacyModesStillRequireTheirActualInstalledGraph() {
        for(var mode:new HostMode[]{HostMode.HTTP,HostMode.MCP_STDIO}) {
            var actual=new RootApplicationMain();var uninstalled=new PublicMcpHost();
            actual.mode=mode;actual.host=uninstalled;
            assertEquals(78,actual.run());
            assertTrue(uninstalled.mode().isEmpty());assertTrue(uninstalled.current().isEmpty());
        }
    }

    @Test void clientArgumentsStillRefuseBeforeAnyGraphOrStartupForEveryExactMode() {
        for(var mode:HostMode.values())for(int count:new int[]{1,3,4,6}) {
            var actual=new RootApplicationMain();actual.mode=mode;
            assertNull(actual.host);
            var arguments=new String[count];java.util.Arrays.fill(arguments,"unqualified-client-argument");
            assertEquals(64,actual.run(arguments));
        }
    }
}
