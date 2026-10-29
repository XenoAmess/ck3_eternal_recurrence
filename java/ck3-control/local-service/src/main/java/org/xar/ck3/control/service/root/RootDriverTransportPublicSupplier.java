package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer;
import org.xar.ck3.control.application.planning.finance.publicgift.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTransportPublicCodec.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;

    /** Seven exact original Driver methods over their actual installed writer and physical source. */
public final class RootDriverTransportPublicSupplier {
    private final RootPublicHandlerProductsFactory.Context context;
    private final IdentityHashMap<RootDriverTransportRuntimeFactory.Runtime,RootReturnedControlHistorySource.Installed> returnedSources=new IdentityHashMap<>();
    private RootDriverTransportPublicSupplier(RootPublicHandlerProductsFactory.Context context){this.context=context;}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source=context.source(RootDriverTransportPublicSupplier.class);
        for(Class<?> type:List.of(ArmyTransportPublicCodec.class,ArmyObserverSampling.class,ArmyPrivateScalarControl.class,ArmyStrengthsService.class))context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,type);
        for(Class<?> type:List.of(PublicSnapshotCodec.class,org.xar.ck3.control.application.driver.DriverActionHistoryCodec.class,org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverExecuteReadHistoryRegistry.class,org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial.class,DriverReadHistoryRowProducer.class,DriverReadHistoryRichMaterial.class,DriverObservedHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.class,org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.class,org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.class,org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.class,FactionGiftPublicCodec.class,FactionGiftPublicContract.class,FactionGiftPublicNumbers.class))context.source(RootRuntimeSelectedSources.Module.APPLICATION,type);context.source(RootDriverTransportRuntimeFactory.class);context.source(RootReturnedControlHistorySource.class);
        for(Class<?> type:List.of(RootRuntimeContext.class,RootPhysicalStatusReadAuthority.class,RootUnknownSentinelReadProfile.class,StatusCapabilityFailure.class,RootPublicStepFailureOriginals.class,PublicServiceFailure.class))context.source(type);
        for(Class<?> type:List.of(PhysicalStatusIdentity.class,org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority.class))context.source(RootRuntimeSelectedSources.Module.APPLICATION,type);
        var actual=new RootDriverTransportPublicSupplier(context);var direct=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>();
        // This is the actual explicit selected configuration profile, supplied before Core construction.
        var prepared=context.definitions().additionalDomains().driverRegistry().prepared(RootDriverRegistryPublicProducts.Kind.TRANSPORT,RootDriverTransportRuntimeFactory.Prepared.class);
        if(prepared.privateSemanticReadonly()){
            direct.add(binding("ck3_take_semantic_snapshot_private_v1",Empty.class,actual::semantic,ArmyTransportPublicCodec::empty,source));
            direct.add(binding("ck3_read_tactical_daily_sentinel_status_private_v1",Empty.class,actual::sentinel,ArmyTransportPublicCodec::empty,source));
        }
        direct.add(binding("ck3_set_army_observer_research_sampling_v1",SamplingSet.class,actual::setSampling,ArmyTransportPublicCodec::samplingSet,source));
        direct.add(binding("ck3_query_army_observer_research_sampling_v1",SamplingQuery.class,actual::querySampling,ArmyTransportPublicCodec::samplingQuery,source));
        direct.add(binding("ck3_set_army_private_auto_scalar_ab_v1",ScalarSet.class,actual::setScalar,ArmyTransportPublicCodec::scalarSet,source));
        direct.add(binding("ck3_query_army_private_auto_scalar_ab_v1",Revision.class,actual::queryScalar,ArmyTransportPublicCodec::revision,source));
        direct.add(binding("ck3_compare_army_private_auto_scalar_ab_v1",Revision.class,actual::compareScalar,ArmyTransportPublicCodec::revision,source));
        return new RootPublicHandlerProductsFactory.Contribution(direct,List.of(),List.of());
    }
    @FunctionalInterface private interface Call<Q>{RawJson invoke(Q request)throws InterruptedException;}
    @FunctionalInterface private interface Decode<Q>{Q decode(RawJson actual);}
    private static <Q> McpExecutableDirectory.DirectBinding<Q,RawJson> binding(String name,Class<Q> type,Call<Q> actual,Decode<Q> decode,ExactRef source){
        return new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,type,RawJson.class,actual::invoke,call->decode.decode(call.arguments().objectOrEmpty()),CallResult::fromBusinessJson,new PublicRoutes.Target(RootDriverTransportPublicSupplier.class.getName(),method(name),source));
    }
    private static String method(String name){return switch(name){case "ck3_take_semantic_snapshot_private_v1"->"semantic";case "ck3_read_tactical_daily_sentinel_status_private_v1"->"sentinel";case "ck3_set_army_observer_research_sampling_v1"->"setSampling";case "ck3_query_army_observer_research_sampling_v1"->"querySampling";case "ck3_set_army_private_auto_scalar_ab_v1"->"setScalar";case "ck3_query_army_private_auto_scalar_ab_v1"->"queryScalar";case "ck3_compare_army_private_auto_scalar_ab_v1"->"compareScalar";default->throw new IllegalArgumentException("fixed transport tool required");};}
    private RootDriverTransportRuntimeFactory.Runtime runtime(RootApplicationSession root)throws IOException {
        return runtime(context.installed(root));
    }
    private RootDriverTransportRuntimeFactory.Runtime runtime(RootInstalledCatalog installed)throws IOException {
        for(Class<?> type:List.of(RootRuntimeContext.class,RootPhysicalStatusReadAuthority.class,RootUnknownSentinelReadProfile.class,StatusCapabilityFailure.class,RootPublicStepFailureOriginals.class,PublicServiceFailure.class,PhysicalStatusIdentity.class,org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority.class))installed.context().game().launchPlan().sources().requireLoadedClass(type);
        var actual=installed.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,RootDriverTransportRuntimeFactory.Runtime.class);
        actual.requireContext(installed.context());for(Class<?> type:List.of(RootDriverTransportPublicSupplier.class,RootDriverTransportRuntimeFactory.class,PublicSnapshotCodec.class,org.xar.ck3.control.application.driver.DriverActionHistoryCodec.class,org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverExecuteReadHistoryRegistry.class,org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial.class,DriverReadHistoryRowProducer.class,DriverReadHistoryRichMaterial.class,DriverObservedHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.class,org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.class,org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.class,org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.class,org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.class,RootReturnedControlHistorySource.class,FactionGiftPublicCodec.class,FactionGiftPublicContract.class,FactionGiftPublicNumbers.class,ArmyPrivateScalarControl.class,ArmyTransportPublicCodec.class,ArmyObserverSampling.class,ArmyStrengthsService.class))installed.context().game().launchPlan().sources().requireLoadedClass(type);return actual;
    }
    private Instant deadline(){return context.clock().instant().plus(context.observationTimeout());}
    public RawJson semantic(Empty ignored)throws InterruptedException {
        try{return context.withCurrent(root->{var actual=runtime(root);StrictJson.require(actual.privateSemanticReadonly(),"private semantic registration flag is disabled");return root.withPublicSnapshot(deadline(),new RootApplicationSession.SnapshotWork<RawJson>() {
                public RawJson ordinary(DriverObservationAssembler.Complete frame,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) {
                    return ArmyTransportPublicCodec.bounded(PublicSnapshotCodec.exportSemanticOnly(frame));
                }
                public RawJson terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) {
                    return ArmyTransportPublicCodec.bounded(PublicSnapshotCodec.exportSemanticOnly(frame,identity));
                }
            });});}
        catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
    public RawJson sentinel(Empty ignored)throws InterruptedException {
        Instant until=deadline();
        try{return context.withInstalledData(until,(installed,same)->{
            var actual=runtime(installed);StrictJson.require(actual.privateSemanticReadonly(),"private sentinel registration flag is disabled");
            // The installed physical authority proves the complete current source before classifying missing support.
            var infrastructure=installed.remainingDomains().life().infrastructure();var contract=infrastructure.physicalStatuses();
            RootUnknownSentinelReadProfile.requireInstalled(contract,infrastructure.statuses());
            var authority=installed.context().physicalStatusReads();authority.requireContext(installed.context());
            return authority.withObserved(same,until,lease->{
                var request=PlanningReadRequest.newStatusOnly(lease.identity(),contract.operation(),new OpportunityJson.Obj(Map.of()),until);
                var result=installed.context().reads().read(same,contract,request);
                if(result instanceof PlanningReadResult.Known<org.xar.ck3.control.reconciliation.LateOutcome.Status> known)
                    return sentinelResult(known.receipt(),known.value());
                throw sentinelUnavailable((PlanningReadResult.Unavailable<?>)result,request,installed.context().archive().withSession(same));
            });
        });}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
    /** An actual false ACK keeps the original primitive error; other unavailable cases cannot impersonate native rejection. */
    static IOException sentinelUnavailable(PlanningReadResult.Unavailable<?> unavailable,PlanningReadRequest request,
            ActionPorts.OutcomeArchive archive)throws IOException {
        if(unavailable.original().orElse(null) instanceof NativeActionPort.AckReceived ack&&!ack.nativeOk()) {
            var identity=request.origin().requirePhysicalStatusOnly();var custody=ack.custody().orElseThrow(
                    ()->new IOException("sentinel native rejection lacks its original receive custody"));custody.verify(ack);
            StrictJson.require(custody.session().equals(identity.transport())
                    &&!custody.writeEntered().observedAt().isBefore(identity.observedAt())
                    &&custody.writeEntered().observedAt().isBefore(request.deadline())
                    &&!custody.responseReceived().observedAt().isAfter(request.deadline()),"sentinel rejection crossed its actual raw source/session/deadline");
            var decoded=NativeWire.decode(ack.originalPacket());StrictJson.require(decoded instanceof NativeWire.CommandResult,"actual sentinel command result required");
            var original=(NativeWire.CommandResult)decoded;var outbound=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            StrictJson.require(!original.nativeOk()&&original.requestId().equals(ack.requestId())
                    &&Arrays.equals(original.payload().value(),ack.originalFrame().bytes())&&outbound.requestId().equals(ack.requestId())
                    &&outbound.step().equals(ClockStatusRead.STEP)&&outbound.expectedRevision().equals(Optional.of(identity.nativeRevision()))
                    &&outbound.expectedSnapshotRevision().isEmpty()
                    &&NativeWire.object(NativeWire.parse(outbound.normalizedAdditionalFields().value())).isEmpty(),"sentinel native rejection changed its actual original request/ACK");
            var raw=NativeWire.object(NativeWire.parse(original.payload().value()));var error=raw.get("error");
            String message=error!=null&&error.isTextual()?error.textValue():"unknown error";
            // The exact sentinel C++ handler does not emit typed_query_failure_v1. No generic failure serializer is claimed here.
            throw new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,"native gameplay step failed: "+message,Optional.of(archive.preserve(ack)));
        }
        return new IOException(unavailable.reason());
    }
    public static RawJson sentinelResult(PlanningReadReceipt receipt,org.xar.ck3.control.reconciliation.LateOutcome.Status status)throws IOException {
        var ack=receipt.original();var original=NativeWire.decode(ack.originalPacket());StrictJson.require(original instanceof NativeWire.CommandResult,"original sentinel command result required");var frame=(NativeWire.CommandResult)original;
        StrictJson.require(frame.nativeOk()&&frame.requestId().equals(receipt.requestId())&&Arrays.equals(frame.payload().value(),ack.originalFrame().bytes())&&frame.result().presence()==NativeWire.Presence.VALUE&&Arrays.equals(frame.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"sentinel original ACK/token differs");
        var outbound=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());StrictJson.require(outbound.requestId().equals(receipt.requestId())&&outbound.step().equals(ClockStatusRead.STEP)&&outbound.expectedRevision().equals(Optional.of(receipt.request().origin().expectedRevision()))&&NativeWire.object(NativeWire.parse(outbound.normalizedAdditionalFields().value())).isEmpty(),"actual sentinel outbound request changed");
        StrictJson.require(ClockStatusRead.decode(ack).equals(status),"sentinel typed status differs from its actual token");
        var row=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));var typed=org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation.toJson(status);
        typed.put("generation",status.generation().decimal());row.set("tactical_daily_sentinel",typed);row.put("backend_id","native-headless");return ArmyTransportPublicCodec.bounded(new RawJson(row.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    public RawJson querySampling(SamplingQuery input)throws InterruptedException {
        Instant deadline=deadline();
        try{return context.withCurrent(root->{var actual=runtime(root);var selected=new ArmyObserverSampling.Selection(input.family(),Optional.empty());var contract=actual.contract(selected);
            return root.withPublicObservation(deadline,(frame,knownDriver,same)->{
                actual.context().writer().requireSession(same);StrictJson.require(frame.identity().frame().revision().equals(input.revision().value()),"sampling public source revision changed");
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),OpportunityJson.object(OpportunityJson.parse(ArmyObserverSampling.fields(selected).bytes()),"sampling public query"),deadline);
                var result=actual.context().reads().read(same,contract,request);
                if(!(result instanceof PlanningReadResult.Known<ArmyObserverSampling.Result> known))throw new IOException("actual sampling original query unavailable");
                try {
                    actual.context().readHistoryPublisher().enqueueRich(contract,known,List.of(known));
                    return ArmyObserverSampling.publicResult(known.value(),known.receipt().request().before(),known.receipt().before().binding().connectionGeneration());
                }catch(RuntimeException failure){
                    try{actual.context().readHistoryPublisher().abandonRich(contract,known);}catch(RuntimeException cleanup){if(cleanup!=failure)failure.addSuppressed(cleanup);}throw failure;
                }
            });
        });}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
    public RawJson setSampling(SamplingSet input)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(context.actionTimeout());
        try{return context.withCurrent(root->{var actual=runtime(root);var strengths=context.installed(root).remainingDomains().strengths();
            var history=returnedSource(root,actual);var invocation=new SamplingInvocation();
            try{return root.executePublicAction(deadline,(frame,known,same)->{
                actual.context().readHistoryPublisher().armyCoreRefreshStarted();
                var command=actual.prepare(same,frame,input.enabled(),input.selection(),input.revision().value(),deadline);
                invocation.capture(history.prepare(same,frame,known,command,input,deadline));return command;
            },(receipt,archive,same)->{
                RawJson report=actual.result(receipt,archive);
                if(receipt.state() instanceof ActionState.Unknown){
                    var token=history.returned(same,invocation.require(),receipt,archive);
                    var outcome=actual.context().readHistoryPublisher().enqueueReturnedControl(same,token);
                    if(outcome instanceof org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.StorageDiagnostic){
                        // The sole publisher already sent this actual loss to its Root persistence-status outlet.
                        // Keep the complete original RETURNED report; a storage diagnostic is not ControlApplied.
                        return report;
                    }
                    StrictJson.require(outcome instanceof org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.Queued,
                            "actual returned control history outcome required");
                }
                return report;
            });}
            finally{strengths.cache().invalidate();}
        });}catch(IOException unavailable){throw new UncheckedIOException("original observer setter unresolved; do not replay",unavailable);}
    }
    private synchronized RootReturnedControlHistorySource.Installed returnedSource(RootApplicationSession root,RootDriverTransportRuntimeFactory.Runtime runtime)throws IOException {
        var previous=returnedSources.get(runtime);if(previous!=null)return previous;
        StrictJson.require(returnedSources.size()<64,"bounded actual returned-control source owners exhausted");
        var source=RootReturnedControlHistorySource.install(context,context.installed(root),runtime);
        runtime.context().readHistoryPublisher().bindReturnedControlHistorySource(source);returnedSources.put(runtime,source);return source;
    }
    private static final class SamplingInvocation {
        private RootReturnedControlHistorySource.Before original;
        void capture(RootReturnedControlHistorySource.Before actual){StrictJson.require(original==null,"one actual sampling preparation required");original=Objects.requireNonNull(actual);}
        RootReturnedControlHistorySource.Before require(){return Objects.requireNonNull(original,"actual sampling preparation was never captured");}
    }
    public RawJson setScalar(ScalarSet input)throws InterruptedException {return scalar(input.revision(),(runtime,strength)->ArmyTransportPublicCodec.scalar(strength.scalarControl().set(input.mode(),input.revision().value())));}
    public RawJson queryScalar(Revision input)throws InterruptedException {return scalar(input,(runtime,strength)->ArmyTransportPublicCodec.scalar(strength.scalarControl().query(input.value())));}
    public RawJson compareScalar(Revision input)throws InterruptedException {
        Instant until=deadline();
        try{return context.withCurrent(root->{var actual=runtime(root);var installed=context.installed(root);
            return root.withPublicObservation(until,(frame,known,same)->{
                actual.requireContext(installed.context());StrictJson.require(frame.identity().frame().revision().equals(input.value()),"scalar public source revision changed");
                installed.context().writer().requireSession(same);var runtime=installed.context();var strength=installed.remainingDomains().strengths();
                // compare_control's own preflight and final readback are outside query_army_strengths' catch.
                var before=strength.scalarControl().query(input.value());StrictJson.require(before.mode()==ArmyPrivateScalarControl.Mode.COMPARE,"private scalar comparison is not armed");
                var service=new ArmyStrengthsService(strength.current(),runtime.reads(),runtime.readCatalog(),strength.contracts(),strength.cache(),strength.pipeline(),strength.scalarControl(),runtime.readHistoryPublisher());
                ArmyStrengthsService.Reply reference;
                try {reference=RootPublicStepFailureOriginals.executeArmyComparisonQuery(root,installed,service,Optional.of(input.value()),until);}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("public scalar comparison query interrupted",interrupted);}
                var state=strength.scalarControl().query(input.value());return ArmyTransportPublicCodec.comparison(reference,state);
            });
        });}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
    @FunctionalInterface private interface ScalarWork {RawJson run(RootRuntimeContext actual,RootArmyStrengthsRuntimeFactory.Installed sameStrengths)throws IOException;}
    private RawJson scalar(Revision revision,ScalarWork work)throws InterruptedException {
        try{return context.withCurrent(root->{var actual=runtime(root);var installed=context.installed(root);return root.withPublicObservation(deadline(),(frame,known,same)->{
            actual.requireContext(installed.context());StrictJson.require(frame.identity().frame().revision().equals(revision.value()),"scalar public source revision changed");
            installed.context().writer().requireSession(same);return work.run(installed.context(),installed.remainingDomains().strengths());
        });});}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
}
