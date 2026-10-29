package org.xar.ck3.control.service.mcp;

import jakarta.enterprise.context.ApplicationScoped;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.runtime.HostMode;

/** Installed once by the existing Root assembly. An incoming MCP request cannot supply or replace authority. */
@ApplicationScoped
public class PublicMcpHost {
    private record Installation(HostMode mode, PublicMcpDirectory directory) { }
    private final AtomicReference<Installation> installed = new AtomicReference<>();
    public void install(HostMode exactManifestMode, PublicMcpDirectory actualDirectory) {
        McpJson.require(Objects.requireNonNull(actualDirectory).scope() == PublicMcpDirectory.Scope.COMPLETE_MIGRATION,
                "software-only MCP directory cannot install ordinary Root authority");
        Installation next = new Installation(Objects.requireNonNull(exactManifestMode), Objects.requireNonNull(actualDirectory));
        if (!installed.compareAndSet(null, next))
            throw new IllegalStateException("original MCP application directory already installed; replacement is forbidden");
    }
    public Optional<PublicMcpDirectory> current() { return Optional.ofNullable(installed.get()).map(Installation::directory); }
    public Optional<HostMode> mode() { return Optional.ofNullable(installed.get()).map(Installation::mode); }
}
