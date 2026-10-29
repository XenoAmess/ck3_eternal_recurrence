package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Exactly one actual ordinary AUTO producer and its original held-writer public projection. */
public final class RootMcpAutoTurn {
    public record Request() { }
    private final RootSessionAccess sessions;private final Clock clock;private final Duration timeout;private final List<AutoFailureDiagnostic.Port> diagnostics;
    public RootMcpAutoTurn(RootSessionAccess sessions,Clock clock,Duration timeout,List<AutoFailureDiagnostic.Port> actualDiagnostics) {
        this.sessions=Objects.requireNonNull(sessions);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);diagnostics=List.copyOf(actualDiagnostics);
        McpJson.require(!timeout.isNegative() && !timeout.isZero() && timeout.compareTo(Duration.ofMinutes(30))<=0,"finite positive AUTO deadline required");
    }
    public McpAutoTurnEncoder.Payload autoTurn(Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        try{return sessions.withCurrent(root -> root.autoTurnPresented(clock.instant().plus(timeout),(actual,known,scopedArchive,borrowed) -> McpAutoTurnEncoder.parse(new org.xar.ck3.control.application.action.RawJson(McpJson.member(
                McpAutoTurnEncoder.encode(actual,known,scopedArchive,diagnostics).original().bytes(),"camera_follow",root.automaticCameraStatus().bytes())))));}
        catch(IOException failure){throw new UncheckedIOException("actual AUTO was called; public serialization unavailable; original outcome retained; do not resend",failure);}
    }
    public PublicBindings.TypedBinding<Request,McpAutoTurnEncoder.Payload> register(PublicBindings actualRegistry,ExactRef actualThisSource) {
        return actualRegistry.register(PublicMethod.AUTO_TURN,Request.class,McpAutoTurnEncoder.Payload.class,this::autoTurn,
                arguments -> {if(arguments instanceof PublicBindings.Value value)McpJson.fields(McpJson.object(McpJson.parse(value.original().bytes())),java.util.Set.of(),java.util.Set.of());return new Request();},
                McpAutoTurnEncoder.Payload::original,new PublicRoutes.Target(getClass().getName(),"autoTurn",actualThisSource),PublicRoutes.Status.DELEGATED,"actual one-turn Root application producer; same held writer original result projection; no HTTP report or alternate controller");
    }
}
