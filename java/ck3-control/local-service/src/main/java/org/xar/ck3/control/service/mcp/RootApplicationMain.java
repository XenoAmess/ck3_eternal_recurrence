package org.xar.ck3.control.service.mcp;

import io.quarkus.runtime.Quarkus;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.xar.ck3.control.build.runtime.HostMode;

/** Legacy HTTP/stdio entry; complete Root composition requires its explicit reviewed startup entry. */
@QuarkusMain(name = "root")
public final class RootApplicationMain implements QuarkusApplication {
    @Inject PublicMcpHost host;
    @ConfigProperty(name = "xar.application.mode", defaultValue = "HTTP") HostMode mode;

    public static void main(String... arguments) {
        System.setOut(System.err);
        System.setProperty("quarkus.log.console.stderr", "true");
        System.setProperty("quarkus.banner.enabled", "false");
        Quarkus.run(RootApplicationMain.class, arguments);
    }

    @Override public int run(String... arguments) {
        if (arguments.length != 0) {
            System.err.println("Root application accepts no client-selected configuration arguments");
            return 64;
        }
        if (mode != HostMode.COMPLETE_MIGRATION
                && (host.mode().isEmpty() || host.mode().orElseThrow() != mode)) {
            System.err.println("Root has not installed the graph for this exact package mode");
            return 78;
        }
        return switch (mode) {
            case MCP_STDIO -> PublicMcpMain.run(host);
            case HTTP -> { Quarkus.waitForExit(); yield 0; }
            case COMPLETE_MIGRATION -> {
                System.err.println("Complete migration requires its explicit reviewed Root startup entry");
                yield 78;
            }
        };
    }
}
