package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Root-only actual-Managed fixture adapter. It neither creates a Core/Game nor substitutes an endpoint or result. */
public final class RootFrontendPublicHostConsumer {
    private RootFrontendPublicHostConsumer() { }

    /** The Root fixture supplies an original, source-reviewed pure frontend tool call after the actual once installation. */
    public static PublicMcpDirectory.CallResult invokeActualRead(RootApplicationAssembly.Core core,
            RootInstalledCatalog installed, PublicMcpHost host, McpExecutableDirectory.Complete complete,
            PublicMcpDirectory.ToolCall reviewedOriginalRead) throws IOException,
            PublicMcpDirectory.ToolFailure, PublicMcpDirectory.RpcFailure {
        assertSame(complete.directory(), host.current().orElseThrow());
        assertEquals(PublicMcpDirectory.Scope.COMPLETE_MIGRATION, complete.directory().scope());
        String before = installed.context().withSession(same -> {
            assertSame(core, installed.context().core());
            assertEquals(RootMenuSession.PublicPhase.FRONTEND, core.requireFrontendMenu(installed.context()).publicPhase());
            return same.head().digest();
        });
        var matches = complete.directory().tools().stream().filter(tool -> tool.name().equals(reviewedOriginalRead.name())).toList();
        assertEquals(1, matches.size(), "actual original descriptor must have one installed dispatch identity");
        matches.getFirst().validateArguments(reviewedOriginalRead.arguments());
        // Invoke outside any borrowed writer: the real host worker/context establishes its own actual read scope.
        var result = complete.directory().invoke(reviewedOriginalRead);
        matches.getFirst().validateResult(result);
        installed.context().withSession(same -> {
            assertEquals(before, same.head().digest(), "reviewed pure menu read cannot submit a canonical action");
            assertEquals(RootMenuSession.PublicPhase.FRONTEND, core.requireFrontendMenu(installed.context()).publicPhase());
            assertSame(complete.directory(), host.current().orElseThrow()); return null;
        });
        return result;
    }
}
