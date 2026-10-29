package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.sway.SwayObservationReads;
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.application.planning.sway.SwaySelectedFinish;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootSessionAccess;
import org.xar.ck3.control.service.sway.SwayRuntimeInstaller;

/** Concrete Sway services installed into Root's sole public registry. No private primitive dispatch lives here. */
public final class RootMcpSway {
    @FunctionalInterface public interface Resolver {SwayRuntimeInstaller current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;
    private final Resolver currentInstaller;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpSway(RootSessionAccess sessions,Resolver currentInstaller,
            Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.currentInstaller=Objects.requireNonNull(currentInstaller);
        this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isNegative()&&!timeout.isZero(),"positive current public Sway timeout required");
    }
    public RawJson finish(SwaySelectedFinish.Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);var reconciliation=new AtomicBoolean();
        try {return sessions.withCurrent(root->{
            var installer=Objects.requireNonNull(currentInstaller.current(root));installer.requireOwner(root);
            return root.executePublicDecision(deadline,(frame,known,same)->{
                var decision=installer.prepareFinish(same,frame,request,deadline);
                if(decision instanceof SwaySelectedFinish.NewStop submit)return new RootApplicationSession.SubmitPublicAction<RawJson>(submit.command());
                if(decision instanceof SwaySelectedFinish.ExistingStop original) {
                    reconciliation.set(true);return new RootApplicationSession.ReconcilePublicAction<RawJson>(original.actionId(),original.canonicalReceipt());
                }
                if(decision instanceof SwaySelectedFinish.Retained retained)return new RootApplicationSession.RetainPublicResult<RawJson>(SwayPublicCodec.retained(retained));
                throw new IllegalStateException("unhandled typed Sway Finish decision");
            },(actual,archive,same)->SwayPublicCodec.finishResult(actual,reconciliation.get()));
        });}catch(IOException unavailable){throw new UncheckedIOException("actual Root Sway Finish unavailable",unavailable);}
    }
    public RawJson journal(SwayPublicCodec.JournalRequest request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->{
            var installer=Objects.requireNonNull(currentInstaller.current(root));installer.requireOwner(root);
            return root.executePublicDecision(deadline,(frame,known,same)->{
                StrictJson.require(frame.identity().frame().revision().equals(request.expectedRevision()),"public Sway journal expected revision is stale");
                var subject=new NativeSubject(frame.identity().frame().identity().player().longValueExact(),request.targetCharacterId(),request.schemeInstanceId(),(int)(request.schemeInstanceId()>>24));
                return new RootApplicationSession.RetainPublicResult<RawJson>(SwayPublicCodec.publicNormalized(installer.readJournalBatch(same,frame,new SwayObservationReads.JournalQuery(request.kind(),subject,request.afterSequence()),deadline)));
            },(actual,archive,same)->{throw new IOException("read-only Sway journal cannot select an action result");});
        });}catch(IOException unavailable){throw new UncheckedIOException("actual Root Sway journal unavailable",unavailable);}
    }
    /** Root composes these three real Service bindings with its other handlers and freezes once. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef actualThisSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(actualThisSource);
        var finish=registry.register(PublicMethod.FINISH_ACTIVE_SCHEME_SWAY_PRIVATE_V1,SwaySelectedFinish.Request.class,RawJson.class,this::finish,
                arguments->SwayPublicCodec.decodeFinish(required(arguments)),value->value,
                new PublicRoutes.Target(RootMcpSway.class.getName(),"finish",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual current original Sway Finish; Root alone submits a new Stop or reconciles its exact retained receipt");
        var execution=registry.register(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_EXECUTION_PRIVATE_V1,SwayPublicCodec.JournalRequest.class,RawJson.class,this::journal,
                arguments->SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.EXECUTION,required(arguments)),value->value,
                new PublicRoutes.Target(RootMcpSway.class.getName(),"journal",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual guarded native execution journal with exact uint64 after_sequence cursor; no action identity is invented");
        var termination=registry.register(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_TERMINATION_PRIVATE_V1,SwayPublicCodec.JournalRequest.class,RawJson.class,this::journal,
                arguments->SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.TERMINATION,required(arguments)),value->value,
                new PublicRoutes.Target(RootMcpSway.class.getName(),"journal",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual guarded native termination journal with exact uint64 after_sequence cursor; observations do not grant terminal causation");
        return List.of(finish,execution,termination);
    }
    private static RawJson required(PublicBindings.Arguments arguments) {
        if(arguments instanceof PublicBindings.Value value)return value.original();
        throw new IllegalArgumentException("original public Sway arguments must be a present non-null object");
    }
}
