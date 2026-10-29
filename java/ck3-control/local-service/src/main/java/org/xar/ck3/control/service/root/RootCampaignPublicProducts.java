package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;

/** Registers the original public campaign ROOT query against its identical per-Game installed finance reader. */
public final class RootCampaignPublicProducts {
    private RootCampaignPublicProducts(){ }
    private static final String IDENTITY="ck3_query_campaign_root_context_v1";
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        try {
            var selected=context.inputs().configuration().finance().reads().stream()
                    .filter(read->read.query()==RootRuntimeDefinitionModel.FinanceQuery.ROOT).findFirst().orElseThrow();
            var implementation=context.source(RootCampaignPublicProducts.class);context.source(CampaignRootPublicCodec.class);
            context.source(RootRuntimeSelectedSources.Module.APPLICATION,CampaignRootContextJson.class);
            ExactRef definition=selected.definition().sourceRef();
            StrictJson.require(selected.permission().mode().name().equals(ReadContract.PermissionMode.ADVERTISED_CAPABILITY.name())
                    &&"game.command.query-campaign-root-context-v1".equals(selected.permission().capability()),"actual public campaign-root capability definition required");
            registry.register(PublicMethod.QUERY_CAMPAIGN_ROOT_CONTEXT_V1,CampaignRootPublicCodec.Request.class,CampaignRootPublicCodec.Result.class,
                    request->query(context,definition,request),CampaignRootPublicCodec::decodeRequest,CampaignRootPublicCodec::encode,
                    new PublicRoutes.Target(RootCampaignPublicProducts.class.getName(),"query",implementation),PublicRoutes.Status.DELEGATED,
                    "Actual same-Root held frame -> identical installed public ROOT read/canonical witness -> complete original Service response");
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
        }catch(IOException unavailable){
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of(
                    new RootRuntimePublicCatalog.DefinitionGap(IDENTITY,"actual campaign-root Java/normalizer/definition source unavailable: "+unavailable.getMessage())));
        }
    }
    /** The original service validates paused/current/expected public revision before any ROOT read. */
    static void requirePublicRevision(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            CampaignRootPublicCodec.Request request) {
        if(!new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true).equals(frame.semantic().get("paused")))
            throw new org.xar.ck3.control.service.mcp.PublicServiceFailure(
                    org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "campaign-root queries require a paused CK3 snapshot",java.util.Optional.empty());
        var current=new org.xar.ck3.control.contracts.PublicRevision(frame.identity().frame().revision());
        if(!current.value().equals(request.expectedRevision()))
            throw new org.xar.ck3.control.service.mcp.PublicServiceFailure(
                    org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    "campaign-root revision mismatch: expected "+request.expectedRevision()+", current "+current.value(),
                    java.util.Optional.empty());
    }
    private static CampaignRootPublicCodec.Result query(RootPublicHandlerProductsFactory.Context context,ExactRef selectedDefinition,
            CampaignRootPublicCodec.Request request)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try{return context.withCurrent(root->{
            var installed=context.installed(root);var actualContext=installed.context();
            return root.withPublicObservation(deadline,(frame,known,same)->{
                actualContext.writer().requireSession(same);actualContext.requireCurrent(deadline);
                var finance=actualContext.finance();var contract=finance.definitions().contract(FinanceReadContracts.Query.ROOT);
                StrictJson.require(finance.game().equals(root.identity().game())&&finance.sessionId().equals(root.identity().sessionId())
                        &&finance.source().equals(frame.source())&&contract.sourceRef().equals(selectedDefinition)
                        &&contract.operation().equals(FinanceReadContracts.Query.ROOT.operation())
                        &&contract.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                        &&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&actualContext.readCatalog().containsIdentity(contract),
                        "public campaign-root provider is not this actual installed original Game/contract/source");
                requirePublicRevision(frame,request);
                var query=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),
                        FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),deadline);
                var read=finance.readPort().read(same,contract,query);
                if(!(read instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> original))
                    throw new IOException("actual public campaign-root read unavailable: "+((PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)read).reason());
                StrictJson.require(original.value().receipt().equals(original.receipt()),"public campaign-root packet lost its identical actual receipt");
                return CampaignRootPublicCodec.fromActual(frame,request,original.value());
            });
        });}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
}
