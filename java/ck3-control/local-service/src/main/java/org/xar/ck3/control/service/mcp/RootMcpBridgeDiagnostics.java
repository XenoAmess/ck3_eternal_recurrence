package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCapture;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootRuntimeContext;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Source-qualified transport diagnostics through Root's sole Service registry. No snapshot refresh or gameplay route. */
public final class RootMcpBridgeDiagnostics {
    @FunctionalInterface public interface Resolver {RootRuntimeContext current(RootApplicationSession actual)throws IOException;}
    /** A missing original producer is a startup definition gap; there is deliberately no default/noop resolver. */
    public interface SupplementResolver {
        ExactRef implementationSource();
        Set<BridgeDiagnostics.RequiredInput> inputs();
        BridgeDiagnostics.Supplement capture(RootRuntimeContext current,ContinuityStorePort.Session same,
                DriverSnapshotFacts.Known actualDriver,BridgeDiagnostics.Received actualReceived)throws IOException;
    }
    private final RootSessionAccess sessions;
    private final Resolver contexts;
    private final SupplementResolver supplements;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpBridgeDiagnostics(RootSessionAccess sessions,Resolver currentContext,SupplementResolver actualSupplements,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);contexts=Objects.requireNonNull(currentContext);supplements=Objects.requireNonNull(actualSupplements);
        this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isZero()&&!timeout.isNegative()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"bounded positive bridge diagnostic deadline required");
    }
    public ExactRef supplementSource(){return Objects.requireNonNull(supplements.implementationSource());}
    public void requireCompleteDefinitions()throws BridgeDiagnostics.MissingInputs {
        var missing=java.util.EnumSet.copyOf(BridgeDiagnostics.supplementInputs());missing.removeAll(Set.copyOf(supplements.inputs()));
        if(!missing.isEmpty())throw new BridgeDiagnostics.MissingInputs(missing,Optional.empty());
        StrictJson.require(supplementSource().bytes()>0,"actual selected diagnostic supplement source required");
    }
    public BridgeDiagnostics.Report diagnostics(BridgeDiagnostics.Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try {
            requireCompleteDefinitions();
            return sessions.withCurrent(root->{
                RootRuntimeContext context=Objects.requireNonNull(contexts.current(root));context.requireCurrent(deadline);
                StrictJson.require(context.actions()==root&&context.writer()==root.writer()&&context.archive()==root.archive()
                        &&context.adopted()==root.driver()&&context.game().generation().equals(root.identity().game())
                        &&context.game().sessionId().equals(root.identity().sessionId())&&context.source().machineId().equals(root.identity().machineId()),"diagnostic resolver crossed the actual current Root");
                NativeGameTransport transport=root.nativeTransport();StrictJson.require(transport==context.transport(),"diagnostics must use the actual current transport object");
                root.driver().producer().requireSameTransport(transport,context.source());
                return context.withSession(same->root.driver().authority().withFrozenFacts(same,frozen->{
                    if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw new IOException("actual bridge diagnostics unavailable: full Driver producer is incomplete");
                    var original=transport.diagnostics();var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),original,Optional.empty());
                    BridgeDiagnostics.requireNativeProduction(received);
                    var nativeSession=received.session().orElseThrow(()->new IOException("actual bridge diagnostics unavailable: original received HELLO/session absent"));
                    StrictJson.require(nativeSession.game().equals(root.identity().game())&&nativeSession.sessionId().equals(root.identity().sessionId())
                            &&nativeSession.machineId().equals(root.identity().machineId())&&known.stamp().game().equals(nativeSession.game()),"actual diagnostic Game birth/session differs");
                    known.observation().ifPresent(facts->StrictJson.require(facts.transport().equals(nativeSession),"diagnostic semantic availability crossed transport session"));
                    byte[] hello=original.originalHello().orElseThrow(()->new IOException("actual original diagnostic HELLO absent")).original().packet().value();
                    ExactRef originalHello=context.archive().preserveArtifact(same,hello,hello.length);
                    var source=context.sources().verifyPhysicalOrigin(same,nativeSession,context.source(),originalHello,original,deadline);
                    source.assertCurrent(same);
                    BridgeDiagnostics.Supplement supplement;
                    try {supplement=Objects.requireNonNull(supplements.capture(context,same,known,received));}
                    catch(BridgeDiagnostics.MissingInputs missing){throw new BridgeDiagnostics.MissingInputs(missing.missing(),Optional.of(received));}
                    var report=new BridgeDiagnostics.Report(received,known.observation().isPresent(),supplement);
                    BridgeDiagnosticsCodec.internal(report);
                    source.assertCurrent(same);context.requireCurrent(deadline);
                    requireSameReceived(original,transport.diagnostics());
                    return report;
                }));
            });
        }catch(IOException unavailable){throw new UncheckedIOException("actual source-qualified bridge diagnostics unavailable",unavailable);}
    }
    /** Catalog calls this only with complete actual products, then performs its one existing freeze. */
    public List<PublicBindings.BoundBinding> register(PublicBindings registry,ExactRef actualThisSource)throws IOException {
        requireCompleteDefinitions();Objects.requireNonNull(registry);Objects.requireNonNull(actualThisSource);
        return List.of(registry.register(PublicMethod.BRIDGE_DIAGNOSTICS,BridgeDiagnostics.Request.class,BridgeDiagnostics.Report.class,this::diagnostics,
                BridgeDiagnosticsCodec::decodeRequest,BridgeDiagnosticsCodec::encode,new PublicRoutes.Target(getClass().getName(),"diagnostics",actualThisSource),
                PublicRoutes.Status.IMPLEMENTED,"actual current held transport/private diagnostic originals; no gameplay capability or implicit fresh snapshot"));
    }
    /** One typed read-only guard for current owner helpers; comparing received DATA creates no source or freshness authority. */
    public static void requireSameReceived(NativeGameTransport.TransportDiagnostics before,NativeGameTransport.TransportDiagnostics after) {
        Objects.requireNonNull(before);Objects.requireNonNull(after);
        StrictJson.require(sameReceived(before,after),"actual received diagnostics changed during original producer capture");
    }
    private static boolean sameReceived(NativeGameTransport.TransportDiagnostics before,NativeGameTransport.TransportDiagnostics after) {
        return before.receivedState()==after.receivedState()&&before.session().equals(after.session())&&before.terminalFailure().equals(after.terminalFailure())&&before.production().equals(after.production())
                &&Arrays.equals(before.lastOriginalPacket().value(),after.lastOriginalPacket().value())
                &&packet(before.originalHello().map(v->v.original().packet().value()),after.originalHello().map(v->v.original().packet().value()))
                &&packet(before.latestHeartbeat().map(v->v.original().packet().value()),after.latestHeartbeat().map(v->v.original().packet().value()))
                &&packet(before.latestPong().map(v->v.original().packet().value()),after.latestPong().map(v->v.original().packet().value()))
                &&packet(before.latestError().map(v->v.original().packet().value()),after.latestError().map(v->v.original().packet().value()))
                &&packet(before.latestSnapshotDiagnostic().map(v->v.original().packet().value()),after.latestSnapshotDiagnostic().map(v->v.original().packet().value()));
    }
    private static boolean packet(Optional<byte[]> first,Optional<byte[]> second){return first.isPresent()==second.isPresent()&&(first.isEmpty()||Arrays.equals(first.orElseThrow(),second.orElseThrow()));}
}
