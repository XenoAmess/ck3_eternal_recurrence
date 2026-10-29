package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.sway.SwayRuntimeInstaller;
import org.xar.ck3.control.service.mcp.*;

/** Pre-Core registration; every invocation resolves the identical current installed Sway and original read authority. */
public final class RootSwaySuppliedPublicProducts {
    private RootSwaySuppliedPublicProducts() { }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        var thisSource=context.source(RootSwaySuppliedPublicProducts.class);
        var decoder=context.source(RootRuntimeSelectedSources.Module.APPLICATION,SwayObservationReads.class);
        var producer=context.source(RootRuntimeSelectedSources.Module.APPLICATION,SwaySelectedObservation.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,SwayPublicCodec.class);context.source(SwayRuntimeInstaller.class);
        var handler=new Handler(context,decoder,producer);
        register(registry,thisSource,handler::query);
        var driverDecoder=context.source(RootRuntimeSelectedSources.Module.APPLICATION,SwayDriverCodec.class);
        var driverProducer=context.source(RootRuntimeSelectedSources.Module.APPLICATION,SwaySelectedStart.class);
        var driver=new DriverHandler(context,driverDecoder,driverProducer);
        var bindings=new java.util.ArrayList<McpExecutableDirectory.DirectBinding<?,?>>(driverBindings(thisSource,driver::target,driver::start,driver::receipt));
        var selected=RootSwaySourcesFactory.readExact(context.inputs().data(RootRuntimeDefinitionModel.DataRole.SWAY_CONFIGURATION));
        if(selected.invalidationReasonQuery()) {
            var notification=new InvalidationHandler(context,decoder,context.source(SwayRuntimeInstaller.class));
            bindings.add(invalidationBinding(thisSource,notification::query));
        }
        return new RootPublicHandlerProductsFactory.Contribution(bindings,List.of(),List.of());
    }
    @FunctionalInterface interface ObservationPort {RawJson query(SwayPublicCodec.DirectRequest request)throws InterruptedException;}
    /** Same concrete binder used by install; software tests replace only the final invocation port, never Root authority. */
    static void register(PublicBindings registry,ExactRef thisSource,ObservationPort handler) {
        registry.register(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_PRIVATE_V1,SwayPublicCodec.DirectRequest.class,RawJson.class,handler::query,
                arguments->SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.COMPLETION,required(arguments)),value->value,
                new PublicRoutes.Target(Handler.class.getName(),"query",thisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual full native Sway instance observation; only a real retained episode consumes lifecycle facts, no inferred terminal cause");
        registry.register(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_V1,SwayPublicCodec.DirectRequest.class,RawJson.class,handler::query,
                arguments->SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.OPINION,required(arguments)),value->value,
                new PublicRoutes.Target(Handler.class.getName(),"query",thisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual current actor/target named opinion observation without a fabricated action or instance identity");
    }
    private record Handler(RootPublicHandlerProductsFactory.Context context,ExactRef decoder,ExactRef producer) {
        private RawJson query(SwayPublicCodec.DirectRequest request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{
                var installed=context.installed(root);var sway=installed.remainingDomains().sway();sway.requireOwner(root);sway.requirePublicObservationSources(decoder,producer);
                return root.executePublicDecision(deadline,(frame,known,same)->{
                    StrictJson.require(frame.identity().frame().revision().equals(request.expectedRevision()),"public Sway observation expected revision is stale");
                    long actor=frame.identity().frame().identity().player().longValueExact();SwayObservationReads.DirectSubject subject;
                    if(request.kind()==SwayObservationReads.Kind.COMPLETION){long id=request.schemeInstanceId().orElseThrow();subject=new SwayObservationReads.CompletionSubject(new NativeSubject(actor,request.targetCharacterId(),id,(int)(id>>24)));}
                    else subject=new SwayObservationReads.OpinionSubject(new SwayObservationReads.Actors(actor,request.targetCharacterId()));
                    var batch=sway.readDirectObservation(same,frame,new SwayObservationReads.DirectQuery(request.kind(),subject),deadline);
                    return new RootApplicationSession.RetainPublicResult<RawJson>(SwayPublicCodec.publicNormalized(batch));
                },(actual,archive,same)->{throw new IOException("read-only Sway observation cannot select an action result");});
            });}catch(IOException unavailable){throw new UncheckedIOException("actual supplied Sway observation unavailable",unavailable);}
        }
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> driverBindings(ExactRef source,PublicRoutes.Handler<SwayDriverCodec.TargetRequest,RawJson> target,PublicRoutes.Handler<SwayDriverCodec.StartRequest,RawJson> start,PublicRoutes.Handler<SwayDriverCodec.ReceiptRequest,RawJson> receipt) {
        return List.of(new McpExecutableDirectory.DirectBinding<>("ck3_query_active_scheme_sway_target_private_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,SwayDriverCodec.TargetRequest.class,RawJson.class,target,call->SwayDriverCodec.decodeTarget(required(call.arguments())),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(DriverHandler.class.getName(),"target",source)),
                new McpExecutableDirectory.DirectBinding<>("ck3_start_active_scheme_sway_private_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,SwayDriverCodec.StartRequest.class,RawJson.class,start,call->SwayDriverCodec.decodeStart(required(call.arguments())),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(DriverHandler.class.getName(),"start",source)),
                new McpExecutableDirectory.DirectBinding<>("ck3_query_active_scheme_sway_receipt_private_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,SwayDriverCodec.ReceiptRequest.class,RawJson.class,receipt,call->SwayDriverCodec.decodeReceipt(required(call.arguments())),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(DriverHandler.class.getName(),"receipt",source)));
    }
    static McpExecutableDirectory.DirectBinding<SwayPublicCodec.InvalidationRequest,RawJson> invalidationBinding(ExactRef source,PublicRoutes.Handler<SwayPublicCodec.InvalidationRequest,RawJson> query) {
        return new McpExecutableDirectory.DirectBinding<>("ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1",PublicMcpBindings.Kind.DRIVER_DIRECT,
                SwayPublicCodec.InvalidationRequest.class,RawJson.class,query,call->SwayPublicCodec.decodeInvalidation(required(call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(InvalidationHandler.class.getName(),"query",source));
    }
    private record InvalidationHandler(RootPublicHandlerProductsFactory.Context context,ExactRef decoder,ExactRef producer) {
        private RawJson query(SwayPublicCodec.InvalidationRequest request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{
                var sway=context.installed(root).remainingDomains().sway();sway.requireOwner(root);sway.requirePublicObservationSources(decoder,producer);
                return root.executePublicDecision(deadline,(frame,known,same)->{
                    StrictJson.require(frame.identity().frame().revision().equals(request.expectedRevision()),"selected notification public revision is stale");
                    long actor=frame.identity().frame().identity().player().longValueExact();
                    var subject=new NativeSubject(actor,request.targetCharacterId(),request.schemeInstanceId(),(int)(request.schemeInstanceId()>>24));
                    var observed=sway.readInvalidation(same,frame,new SwayObservationReads.InvalidationQuery(subject,request.afterSequence()),deadline);
                    return new RootApplicationSession.RetainPublicResult<RawJson>(SwayPublicCodec.publicNormalized(observed));
                },(actual,archive,same)->{throw new IOException("selected notification observation cannot select any action result");});
            });}catch(IOException unavailable){throw new UncheckedIOException("actual selected Sway notification input unavailable",unavailable);}
        }
    }
    private record DriverHandler(RootPublicHandlerProductsFactory.Context context,ExactRef decoder,ExactRef producer) {
        private SwayRuntimeInstaller installed(RootApplicationSession root)throws IOException {var sway=context.installed(root).remainingDomains().sway();sway.requireOwner(root);sway.requirePublicDriverSources(decoder,producer);return sway;}
        private RawJson target(SwayDriverCodec.TargetRequest request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{var sway=installed(root);return root.executePublicDecision(deadline,(frame,known,same)->new RootApplicationSession.RetainPublicResult<RawJson>(sway.readPublicTarget(same,frame,request,deadline)),(actual,archive,same)->{throw new IOException("target query cannot choose an action");});});}
            catch(IOException unavailable){throw new UncheckedIOException("actual Sway target unavailable",unavailable);}
        }
        private RawJson receipt(SwayDriverCodec.ReceiptRequest request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{var sway=installed(root);return root.executePublicDecision(deadline,(frame,known,same)->new RootApplicationSession.RetainPublicResult<RawJson>(sway.readPublicReceipt(same,frame,request,deadline)),(actual,archive,same)->{throw new IOException("receipt query cannot choose an action");});});}
            catch(IOException unavailable){throw new UncheckedIOException("actual Sway receipt unavailable",unavailable);}
        }
        private RawJson start(SwayDriverCodec.StartRequest request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.actionTimeout());
            try{return context.withCurrent(root->{var sway=installed(root);return root.executePublicDecision(deadline,(frame,known,same)->{
                var decision=sway.prepareStart(same,frame,request,deadline);
                if(decision instanceof SwaySelectedStart.NewStart submit)return new RootApplicationSession.SubmitPublicAction<RawJson>(submit.command());
                if(decision instanceof SwaySelectedStart.ExistingStart original)return new RootApplicationSession.ReconcilePublicAction<RawJson>(original.actionId(),original.canonicalReceipt());
                if(decision instanceof SwaySelectedStart.Retained retained)return new RootApplicationSession.RetainPublicResult<RawJson>(retained.result());
                throw new IllegalStateException("unhandled actual Sway Start decision");
            },(actual,archive,same)->SwayDriverCodec.startResult(actual,archive));});}
            catch(IOException unavailable){throw new UncheckedIOException("actual Sway Start unavailable; do not replace its original action ID",unavailable);}
        }
    }
    private static RawJson required(PublicMcpDirectory.Arguments arguments){StrictJson.require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,"original Sway Driver arguments must be a present non-null object");return arguments.original().orElseThrow();}
    private static RawJson required(PublicBindings.Arguments arguments){if(arguments instanceof PublicBindings.Value value)return value.original();throw new IllegalArgumentException("original Sway observation arguments must be a present non-null object");}
}
