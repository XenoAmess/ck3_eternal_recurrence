package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.SnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.OrdinarySnapshotExport;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.WaitForChangePublicCodec;
import org.xar.ck3.control.service.mcp.WaitForChangePublicCodec.Request;

/** Source-bound pre-Core WAIT registration; every call resolves the same actual current Root and held receiver. */
public final class RootWaitForChangePublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootWaitForChangePublicProducts(RootPublicHandlerProductsFactory.Context context){this.context=Objects.requireNonNull(context);}

    public static RootPublicHandlerProductsFactory.Contribution install(
            RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source=context.source(RootWaitForChangePublicProducts.class);
        context.source(WaitForChangePublicCodec.class);
        context.source(RootWaitedSnapshotQualifier.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,NativeSnapshotWaitPort.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,HeldDriverObservationPort.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicSnapshotCodec.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NativeGameTransport.class);
        var actual=new RootWaitForChangePublicProducts(context);
        register(registry,actual::wait_for_change,source);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    public SnapshotExport wait_for_change(Request request)throws InterruptedException {
        Objects.requireNonNull(request);
        var deadlines=WaitForChangePublicCodec.deadlines(request,context.clock(),context.observationTimeout());
        StrictJson.require(deadlines.captureUntil().isBefore(context.inputs().application().reviewAt()),
                "requested WAIT and final capture exceed the actual Root review authority");
        try {
            return context.withCurrent(root->root.withPublicStandaloneRead(deadlines.captureUntil(),same->{
                var installed=context.installed(root);var runtime=installed.context();
                runtime.requireCurrent(deadlines.captureUntil());runtime.writer().requireSession(same);
                var adopted=runtime.adopted();
                StrictJson.require(runtime.actions()==root && adopted==root.driver() && runtime.writer()==root.writer()
                        && runtime.archive()==root.archive(),"WAIT crossed its identical actual Root/Driver/writer/archive");
                adopted.producer().requireSameTransport(runtime.transport(),runtime.source());
                var actual=adopted.observations().waitForChangeFull(request.afterRevision(),deadlines.waitUntil(),deadlines.captureUntil());
                var frame=actual.actual();
                StrictJson.require(frame.session().machineId().equals(root.identity().machineId())
                        && frame.session().game().equals(root.identity().game()) && frame.session().sessionId().equals(root.identity().sessionId())
                        && actual.facts().source().equals(runtime.source()) && frame.session().connectionGeneration().equals(adopted.session().connectionGeneration()),
                        "WAIT result crossed the actual current physical Game/session/source/connection");
                runtime.writer().requireSession(same);runtime.requireCurrent(deadlines.captureUntil());
                StrictJson.require(context.installed(root)==installed,"WAIT cannot publish a result through a replacement Root catalog");
                return RootWaitedSnapshotQualifier.withQualified(root,runtime,same,actual,deadlines.captureUntil(),qualified->
                        PublicSnapshotCodec.exportFull(qualified.originals(),true));
            }));
        } catch(IOException failure) {
            throw new UncheckedIOException("actual current-Root WAIT unavailable; no inferred timeout or action replay permission",failure);
        }
    }
    /** Ordinary consumer seam over the same full producer; the actual Root handler uses source-qualified full export. */
    static OrdinarySnapshotExport wait(HeldDriverObservationPort actual,Request request,WaitForChangePublicCodec.Deadlines deadlines)
            throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(request);Objects.requireNonNull(deadlines);
        // NativeDriver.wait_for_change calls take_snapshot() with its original default full history export.
        return actual.waitForChange(request.afterRevision(),deadlines.waitUntil(),deadlines.captureUntil(),true);
    }
    static PublicBindings.TypedBinding<Request,SnapshotExport> register(PublicBindings registry,
            PublicRoutes.Handler<Request,SnapshotExport> actual,ExactRef source) {
        return registry.register(PublicMethod.WAIT_FOR_CHANGE,Request.class,SnapshotExport.class,actual,
                WaitForChangePublicCodec::decode,PublicSnapshotCodec::encode,
                new PublicRoutes.Target(RootWaitForChangePublicProducts.class.getName(),"wait_for_change",source),
                PublicRoutes.Status.IMPLEMENTED,
                "same current Root/writer and identical held typed packet waiter; actual elapsed returns original current snapshot DATA including history; no action or resume authority");
    }
}
