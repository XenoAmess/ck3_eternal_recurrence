package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.MarriageChoices;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootFamilyRuntimeFactory;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** The live Service query uses the current physical Game's sole installed candidate producer. */
public final class RootMcpMarriage {
    @FunctionalInterface public interface Resolver {RootFamilyRuntimeFactory.Installed current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;
    private final Resolver currentFamily;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpMarriage(RootSessionAccess sessions,Resolver currentFamily,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.currentFamily=Objects.requireNonNull(currentFamily);
        this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isZero()&&!timeout.isNegative(),"positive public marriage query timeout required");
    }
    public MarriageChoicesPublicCodec.Response query(MarriageChoicesPublicCodec.Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->{
            var family=Objects.requireNonNull(currentFamily.current(root));var reads=family.nativeReads();reads.requireOwner(root);
            return root.executePublicDecision(deadline,(frame,known,same)->{
                request.requireCurrent(frame.identity().frame().revision());
                var actual=reads.publicRulerChoices(same,frame,deadline);
                if(actual instanceof PlanningReadResult.Known<MarriageChoices> complete)
                    return new RootApplicationSession.RetainPublicResult<>(new MarriageChoicesPublicCodec.Response(complete));
                if(actual instanceof PlanningReadResult.Unavailable<MarriageChoices> unavailable)throw new IOException("actual marriage candidates unavailable: "+unavailable.reason());
                throw new IllegalStateException("unhandled marriage read result");
            },(actual,archive,same)->{throw new IOException("marriage candidate query cannot select an action result");});
        });}catch(IOException unavailable){throw new UncheckedIOException("actual Root marriage candidate query unavailable",unavailable);}
    }
    /** Root's sole catalog adds this binding before its one complete freeze. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef actualThisSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(actualThisSource);
        return List.of(registry.register(PublicMethod.QUERY_ARRANGE_MARRIAGE_CHOICES,MarriageChoicesPublicCodec.Request.class,MarriageChoicesPublicCodec.Response.class,
                this::query,MarriageChoicesPublicCodec::decode,MarriageChoicesPublicCodec::encode,
                new PublicRoutes.Target(RootMcpMarriage.class.getName(),"query",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual held-frame marriage candidate enumeration from the identical installed Family producer; original source retained through read publication"));
    }
}
