package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootLifecycleAuthority;
import org.xar.ck3.control.service.root.RootLifecycleRuntimeFactory;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Original settlement services. Root retains the sole terminal submit, seed replacement and Host CAS authority. */
public final class RootMcpLifecycle {
    @FunctionalInterface public interface Resolver {RootLifecycleRuntimeFactory.Installed current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;private final Resolver resolver;private final Clock clock;private final Duration timeout;
    public RootMcpLifecycle(RootSessionAccess sessions,Resolver resolver,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);this.resolver=Objects.requireNonNull(resolver);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isNegative()&&!timeout.isZero()&&timeout.compareTo(Duration.ofMinutes(30))<=0,"finite public lifecycle deadline required");
    }
    public LifecyclePublicCodec.Payload settlement(LifecyclePublicCodec.NoArguments request)throws InterruptedException {
        Objects.requireNonNull(request);Instant deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->{
            RootLifecycleRuntimeFactory.Installed actual=Objects.requireNonNull(resolver.current(root));
            return root.withPublicSnapshot(deadline,new RootApplicationSession.SnapshotWork<LifecyclePublicCodec.Payload>() {
                @Override public LifecyclePublicCodec.Payload ordinary(DriverObservationAssembler.Complete frame,Known known,Session same)throws IOException {
                    return actual.physical().withSnapshot(same,deadline,lease->{
                        StrictJson.require(lease.ordinary().orElseThrow(()->new IOException("same actual ordinary physical frame is unavailable"))==frame&&lease.factsKnown()==known,
                                "settlement inspection crossed its actual Root/catalog physical frame");
                        return inspect(root,lease,same);
                    });
                }
                @Override public LifecyclePublicCodec.Payload terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,Known known,Session same)throws IOException {
                    return actual.physical().current(same,identity,deadline,lease->{
                        StrictJson.require(lease.snapshot().actual()==frame.actual()&&lease.snapshot().facts()==known&&lease.identity().equals(identity),
                                "settlement inspection crossed its original terminal Root/catalog frame");
                        lease.assertCurrent(same);
                        var result=inspectData(root,lease.snapshot().semantic(),lease.snapshot().actual(),lease.bridgeCapabilities());
                        lease.assertCurrent(same);return result;
                    });
                }
            });
        });}catch(IOException failure){throw new UncheckedIOException("actual one-life settlement observation unavailable",failure);}
    }
    private static LifecyclePublicCodec.Inspection inspect(RootApplicationSession root,RootLifecycleAuthority.SnapshotLease lease,Session same)throws IOException {
        lease.assertCurrent(same);var full=lease.fullSnapshot();
        var result=inspectData(root,full.semantic(),full.actual(),lease.bridgeCapabilities());lease.assertCurrent(same);return result;
    }
    private static LifecyclePublicCodec.Inspection inspectData(RootApplicationSession root,OpportunityJson.Obj semantic,ObservedFrame actual,Set<String> capabilities) {
        var identity=root.identity();StrictJson.require(actual.session().machineId().equals(identity.machineId())&&actual.session().game().equals(identity.game())
                &&actual.session().sessionId().equals(identity.sessionId()),"settlement inspection belongs to another current Game");
        return LifecyclePublicCodec.inspect(semantic,capabilities,identity.machineId(),actual.observedAt());
    }
    public LifecyclePublicCodec.Payload settle(LifecyclePublicCodec.Request request)throws InterruptedException {return execute(Operation.DEATH_TERMINAL,request);}
    public LifecyclePublicCodec.Payload next(LifecyclePublicCodec.Request request)throws InterruptedException {return execute(Operation.START_NEXT_EPISODE,request);}
    private LifecyclePublicCodec.Payload execute(Operation operation,LifecyclePublicCodec.Request request)throws InterruptedException {
        Objects.requireNonNull(request);Instant deadline=clock.instant().plus(timeout);
        try {return sessions.withCurrent(root->{
            RootLifecycleRuntimeFactory.Installed actual=Objects.requireNonNull(resolver.current(root));
            return root.executePublicLifecycle(actual,operation,request.expected(),deadline,
                    (receipt,scopedArchive,same)->LifecyclePublicCodec.present(operation,receipt,scopedArchive));
        });}catch(IOException failure){throw new UncheckedIOException("actual Root lifecycle operation unavailable; original outcome must be inspected and never resubmitted from this error",failure);}
    }
    /** Original inspection and DEATH bindings. Root/Controller own terminal selection and submission; NEXT has its sole separate installer. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef actualThisSource) {
        Objects.requireNonNull(registry);Objects.requireNonNull(actualThisSource);
        var inspect=registry.register(PublicMethod.ONE_LIFE_SETTLEMENT,LifecyclePublicCodec.NoArguments.class,LifecyclePublicCodec.Payload.class,this::settlement,
                LifecyclePublicCodec::decodeNoArguments,LifecyclePublicCodec::encode,new PublicRoutes.Target(getClass().getName(),"settlement",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "same current Root physical ordinary/terminal snapshot and actual original hello capabilities; inspection grants no settlement or successor authority");
        return List.of(inspect,registerSettlement(registry,this::settle,actualThisSource));
    }
    static PublicBindings.BoundBinding registerSettlement(PublicBindings registry,
            PublicRoutes.Handler<LifecyclePublicCodec.Request,LifecyclePublicCodec.Payload> actual,ExactRef source) {
        return registry.register(PublicMethod.SETTLE_ONE_LIFE,LifecyclePublicCodec.Request.class,LifecyclePublicCodec.Payload.class,actual,
                LifecyclePublicCodec::decodeRequest,LifecyclePublicCodec::encode,
                new PublicRoutes.Target(RootMcpLifecycle.class.getName(),"settle",source),PublicRoutes.Status.IMPLEMENTED,
                "actual Root terminal Controller verifies DEATH operation/public revision before submission; original canonical receipt/UNKNOWN preserved");
    }
}
