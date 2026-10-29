package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.PendingSummary;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.*;

/** Actual public reply/notification services. Root's original coordinator owns all submissions after the current lease exits. */
public final class RootMcpInteractions {
    @FunctionalInterface public interface Resolver {KnownInteractionsRuntimeInstaller current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;
    private final Resolver resolver;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpInteractions(RootSessionAccess sessions,Resolver resolver,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.resolver=Objects.requireNonNull(resolver);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isZero()&&!timeout.isNegative(),"positive public interaction timeout required");
    }
    public RawJson reply(PendingInteractionPublicCodec.Reply request)throws InterruptedException {return execute(Objects.requireNonNull(request));}
    public RawJson acknowledge(PendingInteractionPublicCodec.Acknowledge request)throws InterruptedException {return execute(Objects.requireNonNull(request));}
    public InteractionDirectPublicCodec.Reply queryPending(InteractionDirectPublicCodec.PendingQuery request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var installed=Objects.requireNonNull(resolver.current(root));installed.requireOwner(root);
            return root.withPublicObservation(deadline,(frame,driver,same)->installed.queryPublicPending(same,frame,request,deadline));
        });}catch(IOException failure){throw new UncheckedIOException("actual Root public pending context unavailable",failure);}
    }
    public InteractionDirectPublicCodec.Reply queryOrdinary(InteractionDirectPublicCodec.Ordinary request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var installed=Objects.requireNonNull(resolver.current(root));installed.requireOwner(root);
            return root.withPublicObservation(deadline,(frame,driver,same)->installed.queryPublicOrdinary(same,frame,request,deadline));
        });}catch(IOException failure){throw new UncheckedIOException("actual Root public ordinary context unavailable",failure);}
    }
    public InteractionDirectPublicCodec.Reply initiateOrdinary(InteractionDirectPublicCodec.Ordinary request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->{var installed=Objects.requireNonNull(resolver.current(root));installed.requireOwner(root);
            return root.executePublicDecision(deadline,(frame,driver,same)->{
                var decision=installed.preparePublicOrdinary(same,frame,request,deadline);
                if(decision instanceof KnownInteractionsRuntimeInstaller.NewOrdinary next)return new RootApplicationSession.SubmitPublicAction<InteractionDirectPublicCodec.Reply>(next.command());
                return new RootApplicationSession.RetainPublicResult<InteractionDirectPublicCodec.Reply>(installed.publicOrdinaryResult(same,((KnownInteractionsRuntimeInstaller.RetainedOrdinary)decision).original()));
            },(receipt,archive,same)->installed.publicOrdinaryResult(same,receipt));
        });}catch(IOException failure){throw new UncheckedIOException("actual Root public ordinary initiation unavailable",failure);}
    }
    private RawJson execute(PendingInteractionPublicCodec.Request request)throws InterruptedException {
        var deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->{
            KnownInteractionsRuntimeInstaller installed=Objects.requireNonNull(resolver.current(root));installed.requireOwner(root);
            var observed=new AtomicReference<PendingSummary>();
            return root.executePublicDecision(deadline,(frame,known,same)->{
                var decision=installed.preparePublicPending(same,frame,request,deadline);observed.set(decision.pending());
                if(decision instanceof KnownInteractionsRuntimeInstaller.NewPending submit)
                    return new RootApplicationSession.SubmitPublicAction<RawJson>(submit.command());
                var retained=(KnownInteractionsRuntimeInstaller.RetainedPending)decision;
                // An existing UNKNOWN retains its original identity and result; no reconciliation or replay is requested here.
                return new RootApplicationSession.RetainPublicResult<RawJson>(installed.publicPendingResult(same,retained.original(),retained.pending(),retained.requested()));
            },(actual,archive,same)->installed.publicPendingResult(same,actual,Objects.requireNonNull(observed.get()),request.action()));
        });}catch(IOException failure){throw new UncheckedIOException("actual Root pending interaction service unavailable",failure);}
    }
    /** Registers the five original Service methods; the caller owns the single final registry freeze. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef implementationSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(implementationSource);
        var reply=registry.register(PublicMethod.REPLY_PENDING_CHARACTER_INTERACTION,PendingInteractionPublicCodec.Reply.class,RawJson.class,this::reply,
                PendingInteractionPublicCodec::decodeReply,value->value,new PublicRoutes.Target(getClass().getName(),"reply",implementationSource),PublicRoutes.Status.IMPLEMENTED,
                "same current pending instance; original interaction command producer; Root alone dispatches; UNKNOWN never replayed");
        var acknowledge=registry.register(PublicMethod.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION,PendingInteractionPublicCodec.Acknowledge.class,RawJson.class,this::acknowledge,
                PendingInteractionPublicCodec::decodeAcknowledge,value->value,new PublicRoutes.Target(getClass().getName(),"acknowledge",implementationSource),PublicRoutes.Status.IMPLEMENTED,
                "exact signed notification instance; native ACK and independent advancement are separate facts");
        var pending=registry.register(PublicMethod.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1,InteractionDirectPublicCodec.PendingQuery.class,InteractionDirectPublicCodec.Reply.class,this::queryPending,
                InteractionDirectPublicCodec::pendingRequest,InteractionDirectPublicCodec::encode,new PublicRoutes.Target(getClass().getName(),"queryPending",implementationSource),PublicRoutes.Status.IMPLEMENTED,
                "original exact pending context; same held frame and sole native decoder, complete source/mirrors/readiness; no action");
        var query=registry.register(PublicMethod.QUERY_CHARACTER_INTERACTION_ORDINARY_V1,InteractionDirectPublicCodec.Ordinary.class,InteractionDirectPublicCodec.Reply.class,this::queryOrdinary,
                InteractionDirectPublicCodec::ordinaryRequest,InteractionDirectPublicCodec::encode,new PublicRoutes.Target(getClass().getName(),"queryOrdinary",implementationSource),PublicRoutes.Status.IMPLEMENTED,
                "actual original ordinary context; unavailable/not-ready remain factual results without planner selection");
        var initiation=registry.register(PublicMethod.INITIATE_CHARACTER_INTERACTION_ORDINARY_V1,InteractionDirectPublicCodec.Ordinary.class,InteractionDirectPublicCodec.Reply.class,this::initiateOrdinary,
                InteractionDirectPublicCodec::ordinaryRequest,InteractionDirectPublicCodec::encode,new PublicRoutes.Target(getClass().getName(),"initiateOrdinary",implementationSource),PublicRoutes.Status.IMPLEMENTED,
                "sole original ordinary native preparer/once-claim; queue DATA and same-control after replay; business UNKNOWN never resubmitted");
        return List.of(reply,acknowledge,pending,query,initiation);
    }
}
