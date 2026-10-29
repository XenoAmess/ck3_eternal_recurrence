package org.xar.ck3.control.service.root;

import java.util.Objects;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;

/** Retains the already assembled directory; application and Native authority stay in its actual routes. */
public final class RootOriginalMcpInvocationDirectory {
    private RootOriginalMcpInvocationDirectory() { }

    public static McpExecutableDirectory.Complete bind(McpExecutableDirectory.Complete actualComplete) {
        return Objects.requireNonNull(actualComplete);
    }
}
