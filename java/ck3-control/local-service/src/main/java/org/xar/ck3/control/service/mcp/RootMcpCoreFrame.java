package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootCoreFrameRuntime;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Original Service1441 independent partial prefix, registered into the sole Root Service registry. */
public final class RootMcpCoreFrame {
    @FunctionalInterface public interface Resolver {RootCoreFrameRuntime current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;
    private final Resolver runtimes;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpCoreFrame(RootSessionAccess sessions,Resolver current,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);runtimes=Objects.requireNonNull(current);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive standalone core-frame timeout required");
    }
    public CoreFrame read(CoreFramePublicCodec.Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->root.withPublicStandaloneRead(deadline,same->{
            var runtime=Objects.requireNonNull(runtimes.current(root));return runtime.read(root,same,deadline);
        }));}catch(IOException unavailable) {throw new UncheckedIOException("actual same-session native core-frame unavailable",unavailable);}
    }
    /** Does not freeze: the unique public catalog composes every actual Service and freezes once. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef thisSource) {
        var binding=Objects.requireNonNull(registry).register(PublicMethod.QUERY_CORE_FRAME_V1,CoreFramePublicCodec.Request.class,CoreFrame.class,
                this::read,CoreFramePublicCodec::decodeArguments,CoreFramePublicCodec::encode,
                new PublicRoutes.Target(RootMcpCoreFrame.class.getName(),"read",Objects.requireNonNull(thisSource)),PublicRoutes.Status.IMPLEMENTED,
                "actual standalone .4 app-main core prefix; no complete Snapshot, world refresh, action, or fabricated profile");
        return List.of(binding);
    }
}
