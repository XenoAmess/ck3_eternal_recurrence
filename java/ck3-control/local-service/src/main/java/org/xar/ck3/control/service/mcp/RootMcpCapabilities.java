package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Both public endpoints use the one Root runtime and actual collector capabilities in its original held scope. */
public final class RootMcpCapabilities {
    public record Request() { }
    private final RootSessionAccess sessions;private final Clock clock;private final Duration timeout;
    public RootMcpCapabilities(RootSessionAccess sessions,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        McpJson.require(!timeout.isNegative() && !timeout.isZero() && timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive public capability timeout required");
    }
    public DynamicCapabilities.Result capabilities(Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        try {return sessions.withCurrent(root -> root.withPublicCapabilitiesObservation(clock.instant().plus(timeout),(frame,known,borrowed,received) -> root.capabilityRuntime().read(frame,known,borrowed,received)));}
        catch(IOException failure){throw new UncheckedIOException("actual same-session capabilities unavailable",failure);}
    }
    public PublicBindings.TypedBinding<Request,DynamicCapabilities.Result> register(PublicBindings registry,ExactRef actualThisSource) {
        return registry.register(PublicMethod.CAPABILITIES,Request.class,DynamicCapabilities.Result.class,this::capabilities,
                arguments -> {if(arguments instanceof PublicBindings.Value value)McpJson.fields(McpJson.object(McpJson.parse(value.original().bytes())),java.util.Set.of(),java.util.Set.of());return new Request();},
                result -> new RawJson(OpportunityJson.encode(DynamicCapabilities.toJson(result))),new PublicRoutes.Target(getClass().getName(),"capabilities",actualThisSource),PublicRoutes.Status.DELEGATED,"same Root singleton runtime and actual received capabilities; no caller-created protocol claims");
    }
}
