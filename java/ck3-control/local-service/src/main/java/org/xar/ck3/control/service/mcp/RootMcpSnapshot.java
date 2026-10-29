package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootSessionAccess;
import org.xar.ck3.control.service.root.RootApplicationSession;

/** Original snapshot tool/resource producer on the same current source and actual Root callback. */
public final class RootMcpSnapshot {
    public record Request(boolean includeNativeCommandHistory) { }
    private final RootSessionAccess sessions;private final Clock clock;private final Duration timeout;
    public RootMcpSnapshot(RootSessionAccess sessions,Clock clock,Duration timeout){this.sessions=Objects.requireNonNull(sessions);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        McpJson.require(!timeout.isZero() && !timeout.isNegative() && timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive snapshot timeout required");}
    public RawJson snapshot(Request request) throws InterruptedException {
        Objects.requireNonNull(request);
        try{return sessions.withCurrent(root -> root.withPublicSnapshot(clock.instant().plus(timeout),new RootApplicationSession.SnapshotWork<RawJson>() {
            @Override public RawJson ordinary(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
                    org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                    org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
                return PublicSnapshotCodec.encode(PublicSnapshotCodec.export(frame,request.includeNativeCommandHistory()));
            }
            @Override public RawJson terminal(org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot frame,
                    org.xar.ck3.control.application.action.LifecycleIdentity actualIdentity,
                    org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                    org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
                return PublicSnapshotCodec.encodeTerminal(frame,actualIdentity,request.includeNativeCommandHistory());
            }
        }));}
        catch(IOException failure){throw new UncheckedIOException("actual same-session snapshot unavailable",failure);}
    }
    public PublicBindings.TypedBinding<Request,RawJson> register(PublicBindings registry,ExactRef actualThisSource){return registry.register(PublicMethod.SNAPSHOT,Request.class,RawJson.class,this::snapshot,
            arguments -> {if(!(arguments instanceof PublicBindings.Value value))return new Request(false);var row=McpJson.object(McpJson.parse(value.original().bytes()));McpJson.fields(row,java.util.Set.of("include_native_command_history"),java.util.Set.of());
                if(!row.has("include_native_command_history"))return new Request(false);McpJson.require(row.get("include_native_command_history").isBoolean(),"include_native_command_history must be a boolean");return new Request(row.get("include_native_command_history").booleanValue());},
            result->result,new PublicRoutes.Target(getClass().getName(),"snapshot",actualThisSource),PublicRoutes.Status.DELEGATED,"one actual Root snapshot source capture; ordinary Complete or terminal FullSnapshot with exact lifecycle identity; unique public codec; unknown unsafe numeric roles reject");}
}
