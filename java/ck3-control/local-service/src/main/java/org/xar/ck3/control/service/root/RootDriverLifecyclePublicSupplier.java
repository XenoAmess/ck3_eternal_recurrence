package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.service.root.RootDriverLifecyclePublicCodec.*;

/** Exact original three names over the same installed lifecycle product; no second controller or writer. */
public final class RootDriverLifecyclePublicSupplier {
    /** The same encoder used by the actual registered Close tool. This pure DATA call grants no Root custody. */
    public static RawJson closeResponse(Payload actual){return RootDriverLifecyclePublicCodec.encodeClose(actual);}
    @FunctionalInterface public interface ResumeCall {RootDriverLifecycleResumeCodec.ResumeResult resume(Resume request)throws InterruptedException;}
    /** Shared production binder for request/result DATA tests; supplying a callable grants no Root authority. */
    public static McpExecutableDirectory.DirectBinding<Resume,RootDriverLifecycleResumeCodec.ResumeResult> resumeBinding(ExactRef source,ResumeCall actual){
        Objects.requireNonNull(actual);return new McpExecutableDirectory.DirectBinding<>("ck3_resume_successor_ui_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Resume.class,RootDriverLifecycleResumeCodec.ResumeResult.class,actual::resume,call->RootDriverLifecyclePublicCodec.resume(arguments(call.arguments())),result->PublicMcpDirectory.CallResult.fromBusinessJson(RootDriverLifecycleResumeCodec.encode(result)),new PublicRoutes.Target(RootDriverLifecyclePublicSupplier.class.getName(),"resume",Objects.requireNonNull(source)));
    }
    @FunctionalInterface public interface CloseCall {Payload close(Close request)throws InterruptedException;}
    /** The actual installed Close binder; supplying a callable grants no lifecycle or action authority. */
    public static McpExecutableDirectory.DirectBinding<Close,Payload> closeBinding(ExactRef source,CloseCall actual){
        Objects.requireNonNull(actual);return new McpExecutableDirectory.DirectBinding<>("ck3_continue_death_succession_modal_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Close.class,Payload.class,actual::close,call->RootDriverLifecyclePublicCodec.close(arguments(call.arguments())),result->PublicMcpDirectory.CallResult.fromBusinessJson(closeResponse(result)),new PublicRoutes.Target(RootDriverLifecyclePublicSupplier.class.getName(),"close",Objects.requireNonNull(source)));
    }
    private final RootPublicHandlerProductsFactory.Context context;
    private final ExactRef originalMcp;
    private RootDriverLifecyclePublicSupplier(RootPublicHandlerProductsFactory.Context actual)throws IOException{context=Objects.requireNonNull(actual);originalMcp=context.originalMcp(org.xar.ck3.control.build.OriginalMcpCapture.OriginalModule.MCP_SERVER);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);var source=context.source(RootDriverLifecyclePublicSupplier.class);
        context.source(RootDriverLifecyclePublicCodec.class);context.source(RootDriverLifecycleResumeCodec.class);context.source(RootLifeAdvancePublicResult.class);context.source(RootPendingUiRuntime.class);context.source(RootDriverLifecycleRuntimeInstaller.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicSnapshotCodec.class);context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicDataJson.class);
        var actual=new RootDriverLifecyclePublicSupplier(context);
        var query=new McpExecutableDirectory.DirectBinding<Query,Payload>("ck3_query_current_timeline_blocker_context_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,Payload.class,actual::query,call->RootDriverLifecyclePublicCodec.query(arguments(call.arguments())),result->PublicMcpDirectory.CallResult.fromBusinessJson(RootDriverLifecyclePublicCodec.encode(result)),new PublicRoutes.Target(RootDriverLifecyclePublicSupplier.class.getName(),"query",source));
        var resume=resumeBinding(source,actual::resume);
        var close=closeBinding(source,actual::close);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(query,resume,close),List.of(),List.of());
    }
    private static PublicBindings.Arguments arguments(PublicMcpDirectory.Arguments actual){
        Objects.requireNonNull(actual);return switch(actual.presence()){
            case MISSING->new PublicBindings.Missing();case NULL->new PublicBindings.Null();case VALUE->new PublicBindings.Value(actual.original().orElseThrow());
        };
    }
    private RootPendingUiRuntime runtime(RootApplicationSession root)throws IOException {
        StrictJson.require(originalMcp.equals(context.originalMcp(org.xar.ck3.control.build.OriginalMcpCapture.OriginalModule.MCP_SERVER)),"original three-tool MCP surface source changed");var catalog=context.installed(root);var result=catalog.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.LIFECYCLE,RootPendingUiRuntime.class);result.requireContext(catalog.context());return result;
    }
    private Instant deadline(){return context.clock().instant().plus(context.observationTimeout());}
    public Payload query(Query input)throws InterruptedException {
        try{return context.withCurrent(root->{var actual=runtime(root);if(actual.hasPending())return actual.publicTimeline(input,deadline());
            var terminal=root.withPublicSnapshot(deadline(),new RootApplicationSession.SnapshotWork<Optional<Payload>>(){
                public Optional<Payload> ordinary(DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same){return Optional.empty();}
                public Optional<Payload> terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{return Optional.of(actual.publicTerminalTimeline(identity,input,deadline()));}
            });if(terminal.isPresent())return terminal.orElseThrow();
            var result=root.readCurrent(actual.timelineContract(),Optional.of(input.expectedRevision()),new OpportunityJson.Obj(Map.of()),deadline());
            return actual.publicTimelineResult(RootNaturalSuccessionOriginals.known(result));});}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public RootDriverLifecycleResumeCodec.ResumeResult resume(Resume input)throws InterruptedException {
        try{return context.withCurrent(root->{var actual=runtime(root);if(actual.hasPending())return actual.publicResumeMaterial(input,deadline());
            return root.withPublicSnapshot(deadline(),new RootApplicationSession.SnapshotWork<RootDriverLifecycleResumeCodec.ResumeResult>(){
                public RootDriverLifecycleResumeCodec.ResumeResult ordinary(DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same){input.original().expected().ifPresent(value->StrictJson.require(value.equals(frame.identity().frame().revision()),"successor UI resume revision changed"));return RootDriverLifecycleResumeCodec.clear(RawJson.fullMaterial(DriverJson.encode(frame.semantic())));}
                public RootDriverLifecycleResumeCodec.ResumeResult terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same){input.original().expected().ifPresent(value->StrictJson.require(value.equals(identity.frame().revision()),"successor UI resume revision changed"));return RootDriverLifecycleResumeCodec.clear(RawJson.fullMaterial(DriverJson.encode(frame.semantic())));}
            });});}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public Payload close(Close input)throws InterruptedException {
        try{return context.withCurrent(root->{var actual=runtime(root);var limit=deadline();
            var retained=actual.publicRetainedClose(input,limit);if(retained.isPresent())return retained.orElseThrow();
            return actual.withPublicCloseRequest(input,limit,()->{
            boolean anySubmitted=false;
            // The same finite Root entry performs at most Close, its date child, then finalization. No ordinary turn is used.
            for(int phase=0;phase<3&&context.clock().instant().isBefore(limit)&&actual.refreshPendingStatus(limit);phase++){
                var report=root.pendingSuccessorUiTurn(limit);
                anySubmitted|=report.execution().lifecycleTurns().stream().flatMap(turn->turn.successorUiContinuation().stream()).anyMatch(value->value.actual().disposition()==CompositeContinuationReport.Disposition.NEW_CHILD_ATTEMPT);
            }
            final boolean submitted=anySubmitted;
            if(actual.refreshPendingStatus(deadline()))return actual.presentPendingClose(deadline(),submitted);
            return root.withPublicSnapshot(deadline(),new RootApplicationSession.SnapshotWork<Payload>(){
                public Payload ordinary(DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{return actual.presentClose(frame,submitted);}
                public Payload terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException{return actual.presentClose(PublicSnapshotCodec.exportSemanticOnly(frame,identity),identity.machineId(),frame.actual().observedAt(),submitted);}
            });
        });});}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
}
