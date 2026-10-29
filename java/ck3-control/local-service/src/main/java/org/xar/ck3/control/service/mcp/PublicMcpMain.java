package org.xar.ck3.control.service.mcp;

import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.time.Duration;

/** Stdio runner invoked only by the one build-selected RootApplicationMain. */
public final class PublicMcpMain {
    private PublicMcpMain() { }
    public static int run(PublicMcpHost host) {
        PublicMcpDirectory directory = host.current().orElse(null);
        if (directory == null) {
            System.err.println("MCP unavailable: Root has not installed the actual complete application directory"); return 78;
        }
        PublicMcpStdio.Exit actual = PublicMcpStdio.run(directory, System.in, new FileOutputStream(FileDescriptor.out), Duration.ofSeconds(30));
        System.err.println("MCP stdio exit=" + actual.code() + " completed=" + actual.completedCalls() + " unresolved=" + actual.unresolvedCalls() + " reason=" + actual.reason());
        return actual.code();
    }
}
