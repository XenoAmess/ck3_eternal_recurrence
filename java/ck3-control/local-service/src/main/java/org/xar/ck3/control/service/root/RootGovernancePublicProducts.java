package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceNativeReads;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pre-Core governance registration. Each query or original unsupported-service invocation resolves the current Root again. */
public final class RootGovernancePublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootGovernancePublicProducts(RootPublicHandlerProductsFactory.Context context) {this.context=Objects.requireNonNull(context);}

    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        var source=context.source(RootGovernancePublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GovernanceNativeReads.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GovernancePublicService.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,GovernancePublicWire.class);
        var actual=new RootGovernancePublicProducts(context);
        register(registry,actual::query_council_composition_candidates_v1,actual::query_steward_develop_county_candidates_v1,source);
        context.source(org.xar.ck3.control.service.mcp.PublicServiceFailure.class);
        var action=RootStewardDevelopmentPublicAction.factory(context);
        registerAction(registry,action::invoke,context.source(RootStewardDevelopmentPublicAction.class),action.nativeQualificationGap());
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }

    public CouncilReply query_council_composition_candidates_v1(CouncilRequest input)throws InterruptedException {
        Objects.requireNonNull(input);Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {return context.withCurrent(root->root.withPublicObservation(deadline,(frame,driver,same)->{
            var installed=context.installed(root);var runtime=installed.context();runtime.writer().requireSession(same);
            var contract=installed.nativeGovernance().publicReads().council();
            var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
            StrictJson.require(GovernanceNativeReads.frame(request).equals(input.requested()),"public Council request differs from the actual complete current frame");
            var result=known(runtime.reads().read(same,contract,request),contract,request,runtime,same);
            return new CouncilReply(result.value(),result);
        }));}catch(IOException failure){throw new UncheckedIOException("actual current-Root public Council query unavailable",failure);}
    }

    public DevelopmentReply query_steward_develop_county_candidates_v1(DevelopmentRequest input)throws InterruptedException {
        Objects.requireNonNull(input);Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {return context.withCurrent(root->root.withPublicObservation(deadline,(frame,driver,same)->{
            var installed=context.installed(root);var runtime=installed.context();runtime.writer().requireSession(same);
            StrictJson.require(frame.identity().frame().revision().equals(input.expectedRevision()),"public development revision differs from the actual current public revision");
            var contract=installed.nativeGovernance().publicReads().development();
            var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
            var result=known(runtime.reads().read(same,contract,request),contract,request,runtime,same);
            var backend=frame.semantic().get("backend_id");
            StrictJson.require(backend==null||backend==OpportunityJson.Nil.INSTANCE||backend instanceof OpportunityJson.Text,"actual native backend identity is malformed");
            Optional<String> originalBackend=backend instanceof OpportunityJson.Text text?Optional.of(text.value()):Optional.empty();
            return new DevelopmentReply(result.value(),result,originalBackend);
        }));}catch(IOException failure){throw new UncheckedIOException("actual current-Root public development query unavailable",failure);}
    }

    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result,ReadContract<T> contract,PlanningReadRequest request,
            RootRuntimeContext runtime,ContinuityStorePort.Session same)throws IOException {
        if(result instanceof PlanningReadResult.Unavailable<T> missing)throw new IOException("actual installed governance read unavailable: "+missing.reason());
        var known=(PlanningReadResult.Known<T>)result;
        StrictJson.require(known.receipt().request().equals(request)&&known.receipt().contractId().equals(contract.contractId())
                &&runtime.archive().withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt()),
                "public governance result lost its actual installed contract or archived original");
        GovernanceNativeReads.verifyGuards(known.receipt());return known;
    }

    /** The same typed boundary used by production registration and retained-producer protocol regressions. */
    static List<PublicBindings.BoundBinding> register(PublicBindings registry,PublicRoutes.Handler<CouncilRequest,CouncilReply> council,
            PublicRoutes.Handler<DevelopmentRequest,DevelopmentReply> development,ExactRef source) {
        Objects.requireNonNull(registry);Objects.requireNonNull(council);Objects.requireNonNull(development);Objects.requireNonNull(source);
        return List.of(
            registry.register(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1,CouncilRequest.class,CouncilReply.class,council,
                arguments->GovernancePublicService.decodeCouncil(value(arguments)),GovernancePublicService::encodeCouncil,
                new PublicRoutes.Target(RootGovernancePublicProducts.class.getName(),"query_council_composition_candidates_v1",source),PublicRoutes.Status.IMPLEMENTED,
                "actual current Root complete frame, installed Council contract, original native receipt and shared public codec; Steward-only"),
            registry.register(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1,DevelopmentRequest.class,DevelopmentReply.class,development,
                arguments->GovernancePublicService.decodeDevelopment(value(arguments)),GovernancePublicService::encodeDevelopment,
                new PublicRoutes.Target(RootGovernancePublicProducts.class.getName(),"query_steward_develop_county_candidates_v1",source),PublicRoutes.Status.IMPLEMENTED,
                "actual current Root complete public revision, installed development contract and original native material; material is not action legality"));
    }
    /** The native executor remains unavailable; the current source-bound service behavior is a concrete public product. */
    static PublicBindings.BoundBinding registerAction(PublicBindings registry,PublicRoutes.Handler<ChangeRequest,RawJson> action,
            ExactRef source,String nativeQualificationGap) {
        Objects.requireNonNull(registry);Objects.requireNonNull(action);Objects.requireNonNull(source);StrictJson.text(nativeQualificationGap);
        return registry.register(PublicMethod.CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1,ChangeRequest.class,RawJson.class,action,
                arguments->GovernancePublicService.decodeChange(value(arguments)),result->result,
                new PublicRoutes.Target(RootStewardDevelopmentPublicAction.Factory.class.getName(),"invoke",source),PublicRoutes.Status.IMPLEMENTED,
                "actual original source-bound paused/revision/candidate/HELLO-capability checks and original unsupported-service errors; NativeReady=false. "+nativeQualificationGap);
    }
    private static RawJson value(PublicBindings.Arguments arguments) {
        if(arguments instanceof PublicBindings.Value present)return present.original();
        throw new IllegalArgumentException("public governance method requires its exact named JSON object; missing and null are distinct unsupported inputs");
    }
}
