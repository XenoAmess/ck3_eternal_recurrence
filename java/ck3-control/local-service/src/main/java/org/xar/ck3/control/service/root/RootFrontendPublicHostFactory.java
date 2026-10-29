package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.util.Objects;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Actual pre-Game menu host join; the sole public catalog still owns registration and its once-only attempt. */
public final class RootFrontendPublicHostFactory {
    private RootFrontendPublicHostFactory() { }
    private record Originals(RootMenuSession menu, String head) { }

    public static McpExecutableDirectory.Complete install(RootApplicationAssembly.Core core, RootInstalledCatalog actual,
            RootRuntimePublicCatalog publicCatalog, RootRuntimeCatalogFactory catalogs, PublicMcpHost host, Clock clock)
            throws IOException, InterruptedException {
        Objects.requireNonNull(core); Objects.requireNonNull(actual); Objects.requireNonNull(publicCatalog);
        Objects.requireNonNull(catalogs); Objects.requireNonNull(host); Objects.requireNonNull(clock);
        Originals retained = requireActual(core, actual, catalogs, clock);
        // This is the same catalog/host used after gameplay admission, never a second registry or backend.
        McpExecutableDirectory.Complete complete = publicCatalog.installFrontend(core, catalogs, actual, host);
        if (host.current().orElseThrow(() -> new IOException("actual frontend public host was not installed")) != complete.directory()
                || host.mode().orElseThrow() != core.configuration().mode())
            throw new IOException("frontend host did not retain the actual sole complete directory and manifest mode");
        Originals after = requireActual(core, actual, catalogs, clock);
        if (retained.menu() != after.menu() || !retained.head().equals(after.head()))
            throw new IOException("frontend host installation changed its actual menu or canonical writer");
        return Objects.requireNonNull(complete, "actual public catalog returned no complete executable directory");
    }

    /** Same real objects are revalidated before and after installation; no caller-supplied frontend DTO grants admission. */
    private static Originals requireActual(RootApplicationAssembly.Core core, RootInstalledCatalog actual,
            RootRuntimeCatalogFactory catalogs, Clock clock) throws IOException {
        core.configuration().requireCurrent(clock);
        if (!core.clock().equals(clock)) throw new IOException("frontend host uses another actual Core clock");
        return actual.context().withSession(same -> {
            if (catalogs.requireFrontendCatalog(core) != actual || actual.context().core() != core
                    || actual.context().writer() != core.writer() || core.archive().writer() != core.writer())
                throw new IOException("frontend host belongs to another actual Core, writer or installed catalog");
            actual.context().requireCurrent(core.configuration().reviewAt());
            RootMenuSession menu = core.requireFrontendMenu(actual.context());
            if (menu.publicPhase() != RootMenuSession.PublicPhase.FRONTEND || menu.writer != core.writer()
                    || menu.game != actual.context().game() || !menu.source.equals(actual.context().source())
                    || menu.bindings != actual.bindings() || menu.frontend != actual.frontend().authority()
                    || actual.frontend() != actual.context().frontend())
                throw new IOException("frontend host lost its identical private menu, Native authority or source");
            menu.frontend.requireOutsideSourceBoundFrontendRead();
            return new Originals(menu, same.head().digest());
        });
    }
}
