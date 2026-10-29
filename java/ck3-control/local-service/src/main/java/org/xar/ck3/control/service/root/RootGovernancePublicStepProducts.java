package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.development.DevelopmentCodec;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** The five exact original generic driver READ branches. No action/default command or alternate contract is created. */
public final class RootGovernancePublicStepProducts {
    private RootGovernancePublicStepProducts() { }
    public static final String ROOT="query-campaign-root-context-v1";
    public static final String FEATURES="query-loaded-feature-manifest-v1";
    private static final Set<String> FEATURE_MIRRORS=Set.of("schema","schema_version","date_raw","unavailable_reason","build",
            "effective_feature_flags","script_dlc_keys","entitlements","readiness","provenance");
    private static final BigInteger SAFE=BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        var root=context.finance().definitions().contract(FinanceReadContracts.Query.ROOT);
        var council=actual.nativeGovernance().publicReads().council();
        var development=actual.nativeGovernance().publicReads().development();
        var features=actual.frontend().rules().definitions().loadedFeatures();
        var factions=actual.definitions().finance().factionContracts();
        StrictJson.require(root.operation().value().equals(ROOT)&&features.operation().value().equals(FEATURES)
                &&council.operation().value().equals(GovernanceNativeReads.COUNCIL_STEP)
                &&development.operation().value().equals(GovernanceNativeReads.DEVELOPMENT_STEP),"actual governance READ getter changed its original exact operation");

        for(var contract:List.of(root,council,development,features))requireInstalled(context,contract);
        var owner=(RootPublicStepExecution.OwnerGuard)identical->{
            if(identical!=context||actual.context()!=context)throw new IOException("original governance READ product crossed its installed physical Root");
        };
        var self=actual.publicStepSource(LOCAL_SERVICE,RootGovernancePublicStepProducts.class);
        var wire=actual.publicStepSource(NATIVE_TRANSPORT,NativeWire.class);
        var result=new ArrayList<RootPublicStepExecution.Product>();
        result.add(new RootPublicStepExecution.Read("execute.campaign-root.v1",step->step.value().equals(ROOT),owner,
            (original,frame,known,same,caller,archive)->{
                scope(original,frame,known,caller,ROOT,root.requiredCapability().orElseThrow(),"native DLL cannot query the campaign root context");
                context.writer().requireSession(same);requireInstalled(context,root);
                var finance=context.finance();
                StrictJson.require(finance.game().equals(frame.identity().game())&&finance.sessionId().equals(frame.sessionId())
                        &&finance.source().equals(frame.source()),"execute campaign ROOT crossed actual finance ownership");
                var request=request(frame,root,FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),original);
                var read=finance.readPort().read(same,root,request);
                var retained=requireKnown(read,root,archive);
                StrictJson.require(retained.value().receipt().equals(retained.receipt()),"actual ROOT packet lost its original receipt");
                // Canonical ROOT reuse is qualified by the sole installed finance port, then checked by its original formatter.
                return CampaignRootPublicCodec.executeFromActual(frame,frame.identity().frame().revision(),retained.value());
            },sources(self,wire,root.sourceRef(),actual.publicStepSource(LOCAL_SERVICE,CampaignRootPublicCodec.class),
                actual.publicStepSource(APPLICATION,FinanceReadContracts.class),actual.publicStepSource(APPLICATION,CampaignRootContextJson.class))));
        result.add(new RootPublicStepExecution.Read("execute.council-composition.v1",step->step.equals(council.operation()),owner,
            (original,frame,known,same,caller,archive)->{
                scope(original,frame,known,caller,council.operation().value(),council.requiredCapability().orElseThrow(),"native DLL cannot query council composition candidates");
                var read=read(context,same,council,frame,original,archive);
                return GovernancePublicService.encodeCouncilExecution(new GovernancePublicService.CouncilReply(read.value(),read));
            },sources(self,wire,council.sourceRef(),actual.publicStepSource(NATIVE_TRANSPORT,GovernanceNativeReads.class),
                actual.publicStepSource(NATIVE_TRANSPORT,GovernancePublicService.class),actual.publicStepSource(NATIVE_TRANSPORT,GovernancePublicWire.class),
                actual.publicStepSourceAt("governance-policy/src/main/java/org/xar/ck3/control/governance/council/CouncilCodec.java",CouncilCodec.class),
                actual.publicStepSourceAt("governance-policy/src/main/java/org/xar/ck3/control/governance/council/CouncilModels.java",CouncilModels.class))));
        result.add(new RootPublicStepExecution.Read("execute.steward-development.v1",step->step.equals(development.operation()),owner,
            (original,frame,known,same,caller,archive)->{
                scope(original,frame,known,caller,development.operation().value(),development.requiredCapability().orElseThrow(),"native DLL cannot query steward Develop County candidates");
                var read=read(context,same,development,frame,original,archive);
                return GovernancePublicService.encodeDevelopmentExecution(new GovernancePublicService.DevelopmentReply(read.value(),read,backend(frame)));
            },sources(self,wire,development.sourceRef(),actual.publicStepSource(NATIVE_TRANSPORT,GovernanceNativeReads.class),
                actual.publicStepSource(NATIVE_TRANSPORT,GovernancePublicService.class),actual.publicStepSource(NATIVE_TRANSPORT,GovernancePublicWire.class),
                actual.publicStepSourceAt("governance-policy/src/main/java/org/xar/ck3/control/governance/development/DevelopmentCodec.java",DevelopmentCodec.class),
                actual.publicStepSourceAt("governance-policy/src/main/java/org/xar/ck3/control/governance/development/DevelopmentModels.java",DevelopmentModels.class))));
        StrictJson.require(factions.families().size()==1,"one finance-owned faction READ family required");
        var family=factions.families().getFirst();
        StrictJson.require(context.readCatalog().families().stream().anyMatch(registered->registered==family)
                &&family.id().equals("player-faction-alerts-v1")&&family.requiredCapability().equals(Optional.of(FactionAlertReadService.CAPABILITY)),
                "original faction READ requires the identical installed advertised finance family");
        result.add(new RootPublicStepExecution.Read("execute.player-faction-alerts.v1",step->step.value().equals(FactionAlertReadService.STEP),owner,
            (original,frame,known,same,caller,archive)->{
                scope(original,frame,known,caller,FactionAlertReadService.STEP,FactionAlertReadService.CAPABILITY,"native DLL cannot query player faction alerts");
                StrictJson.require(actual.definitions().finance().factionContracts()==factions,"execute faction READ lost its identical finance Prepared family");
                var reply=RootFactionAlertPublicProducts.queryCurrent(new FactionAlertReadService.Query(frame.identity().frame().revision()),frame,
                        original.deadline(),new BorrowedReads(context,same,archive),context.readCatalog(),factions);
                return FactionAlertReadService.encodeExecution(reply);
            },sources(self,wire,family.definitionSource(),family.decoderSource(),actual.publicStepSource(LOCAL_SERVICE,RootFactionAlertPublicProducts.class),
                actual.publicStepSource(NATIVE_TRANSPORT,FactionAlertReadService.class),
                actual.publicStepSourceAt("wave2-finance/src/main/java/org/xar/ck3/control/wave2/finance/factionalerts/FactionAlertsBoundary.java",FactionAlertsBoundary.class),
                actual.publicStepSourceAt("wave2-finance/src/main/java/org/xar/ck3/control/wave2/finance/factionalerts/FactionAlertsCodec.java",FactionAlertsCodec.class))));
        result.add(new RootPublicStepExecution.Read("execute.loaded-features.v1",step->step.equals(features.operation()),owner,
            (original,frame,known,same,caller,archive)->{
                scope(original,frame,known,caller,FEATURES,features.requiredCapability().orElseThrow(),"native DLL cannot query the loaded feature manifest");
                return featureResult(read(context,same,features,frame,original,archive));
            },sources(self,wire,features.sourceRef(),actual.publicStepSource(NATIVE_TRANSPORT,FrontendRulesDefinitions.class),
                actual.publicStepSource(NATIVE_TRANSPORT,LoadedFeaturesCodec.class),actual.publicStepSource(NATIVE_TRANSPORT,LoadedFeaturesData.class),actual.publicStepSource(NATIVE_TRANSPORT,FrontendRulesData.class))));
        return List.copyOf(result);
    }
    private static List<ExactRef> sources(ExactRef... actual) {return List.copyOf(new LinkedHashSet<>(List.of(actual)));}
    private static void requireInstalled(RootRuntimeContext context,ReadContract<?> contract)throws IOException {
        if(!context.readCatalog().containsIdentity(contract)||contract.guardMode()!=ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                ||contract.permissionMode()!=ReadContract.PermissionMode.ADVERTISED_CAPABILITY||contract.requiredCapability().isEmpty())
            throw new IOException("original generic READ requires its identical installed advertised gameplay contract");
    }
    private static Optional<String> backend(Complete frame) {
        var backend=frame.semantic().get("backend_id");
        StrictJson.require(backend==null||backend==OpportunityJson.Nil.INSTANCE||backend instanceof OpportunityJson.Text,"actual backend is malformed");
        return backend instanceof OpportunityJson.Text text?Optional.of(text.value()):Optional.empty();
    }
    private static void scope(PlanningRequest original,Complete frame,Known known,PublicPlanningCodec.ExecuteRequest caller,
            String step,String capability,String unsupported) {
        requireSelector(caller,step);caller.requireCurrent(original);requireCapability(original,capability,unsupported);
        StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())&&original.sessionId().equals(frame.sessionId())
                &&known.stamp().game().equals(frame.identity().game())&&known.stamp().episodeRunId().equals(frame.identity().frame().episodeRunId()),
                "generic governance READ crossed the actual held planning/Driver/frame/source/session");
    }
    /** Pure original argument/capability checks; no constructor or true result grants Root authority. */
    static void requireSelector(PublicPlanningCodec.ExecuteRequest caller,String step) {
        StrictJson.require(Objects.requireNonNull(caller).step().value().equals(step)&&!caller.h2743(),"generic governance READ received another exact step or H2743 branch");
    }
    static void requireCapability(PlanningRequest actual,String capability,String originalMessage) {
        if(!Objects.requireNonNull(actual).observations().bridgeCapabilities().contains(capability))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.exact("UnsupportedStepError"),originalMessage,Optional.empty());
    }
    private static PlanningReadRequest request(Complete frame,ReadContract<?> contract,OpportunityJson.Obj arguments,PlanningRequest original) {
        return new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),arguments,original.deadline());
    }
    private static <T> PlanningReadResult.Known<T> read(RootRuntimeContext context,Session same,ReadContract<T> contract,Complete frame,
            PlanningRequest original,ActionPorts.OutcomeArchive archive)throws IOException {
        context.writer().requireSession(same);requireInstalled(context,contract);
        var request=request(frame,contract,new OpportunityJson.Obj(java.util.Map.of()),original);
        var known=requireKnown(context.reads().read(same,contract,request),contract,archive);
        StrictJson.require(known.receipt().request().equals(request),"generic READ original differs from the exact requested held frame");
        GovernanceNativeReads.verifyGuards(known.receipt());return known;
    }
    private static <T> PlanningReadResult.Known<T> requireKnown(PlanningReadResult<T> result,ReadContract<T> contract,
            ActionPorts.OutcomeArchive archive)throws IOException {
        var known=requireAvailable(result);
        StrictJson.require(known.receipt().contractId().equals(contract.contractId())&&known.receipt().request().operation().equals(contract.operation())
                &&archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())&&archive.loadRead(known.originalReceipt()).equals(known.receipt()),
                "generic READ lost its installed contract or retained exact original archive");
        requirePacket(known.receipt());return known;
    }
    /** UNKNOWN and every unavailable READ terminate; this branch neither dispatches nor creates a replacement original. */
    static <T> PlanningReadResult.Known<T> requireAvailable(PlanningReadResult<T> actual) {
        Objects.requireNonNull(actual);
        if(actual instanceof PlanningReadResult.Known<T> known)return known;
        var missing=(PlanningReadResult.Unavailable<T>)actual;
        throw new PublicServiceFailure(PublicServiceFailure.Kind.exact("BridgeUnavailableError"),missing.reason(),Optional.empty());
    }
    private static void requirePacket(PlanningReadReceipt receipt)throws IOException {
        var ack=receipt.original();var packet=NativeWire.decode(ack.originalPacket());
        StrictJson.require(packet instanceof NativeWire.CommandResult,"generic READ requires its full original command_result packet");
        var full=(NativeWire.CommandResult)packet;
        StrictJson.require(full.nativeOk()&&ack.nativeOk()&&full.requestId().equals(receipt.requestId())&&ack.requestId().equals(receipt.requestId())
                &&full.result().presence()==NativeWire.Presence.VALUE&&ack.originalResultToken().isPresent()
                &&StrictJson.parse(full.payload().value()).equals(StrictJson.parse(ack.originalFrame().bytes()))
                &&StrictJson.parse(full.result().token().orElseThrow().value()).equals(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes())),
                "generic READ original packet/token/receipt correlation changed");
    }
    private static final class BorrowedReads implements PlanningReadPort {
        private final RootRuntimeContext context;private final Session same;private final ActionPorts.OutcomeArchive archive;
        private BorrowedReads(RootRuntimeContext context,Session same,ActionPorts.OutcomeArchive archive)throws IOException {
            this.context=context;this.same=same;this.archive=archive;context.writer().requireSession(same);
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            try {
                context.writer().requireSession(same);requireInstalled(context,contract);
                var result=context.reads().read(same,contract,request);
           
                if(result instanceof PlanningReadResult.Known<T>) {
                    var known=requireKnown(result,contract,archive);StrictJson.require(known.receipt().request().equals(request),"faction READ escaped its exact current request");
                }
                return result;
            }catch(IOException failed){throw new UncheckedIOException("actual generic faction READ original unavailable",failed);}
        }
        @Override public <T> PlanningReadResult<T> read(Session borrowed,ReadContract<T> contract,PlanningReadRequest request) {
            StrictJson.require(borrowed==same,"generic faction READ crossed its sole writer scope");return read(contract,request);
        }
    }
    /** Pure complete original driver projection. DATA use cannot create a ReadPermit or a private Root. */
    static RawJson featureResult(PlanningReadResult.Known<LoadedFeaturesData.Observation> actual)throws IOException {
        Objects.requireNonNull(actual);var receipt=actual.receipt();var before=receipt.request().before().frame();var value=actual.value();
        GovernanceNativeReads.verifyGuards(receipt);requirePacket(receipt);
        StrictJson.require(receipt.request().operation().value().equals(FEATURES)&&receipt.request().arguments().members().isEmpty()
                &&value.snapshotId().equals(before.snapshotId())&&value.revision().equals(before.revision())
                &&value.episodeRunId().equals(Optional.ofNullable(before.episodeRunId()))
                &&receipt.request().source().exactBuild().equals(value.manifest().build().version()),"loaded feature observation crossed its original step/frame/episode");
        var decoded=LoadedFeaturesCodec.decode(receipt.original().originalResultToken().orElseThrow(),value.manifest().build(),
                before.identity().nativeRevision(),before.identity().dateRaw().intValueExact());
        StrictJson.require(decoded.manifest().equals(value.manifest())&&decoded.querySequence().equals(value.querySequence()),
                "loaded feature projection differs from its actual installed typed decoder");
        var result=StrictJson.object(StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()),
                Set.of("step","accepted","status","query_sequence","snapshot_revision","loaded_feature_manifest","backend_id")).deepCopy();
        var manifest=(ObjectNode)result.get("loaded_feature_manifest");
        for(String field:FEATURE_MIRRORS)result.set(field,manifest.get(field).deepCopy());
        result.put("loaded_feature_manifest_ready",value.manifest().readiness().actionableReady());
        result.put("queried_snapshot_id",before.snapshotId()).put("queried_revision",before.revision().toString())
                .put("queried_native_revision",before.identity().nativeRevision().toString());
        decimal(result,"query_sequence");decimal(result,"snapshot_revision");decimal(manifest,"snapshot_revision");
        safeRemaining(result);return new RawJson(StrictJson.canonical(result));
    }
    private static void decimal(ObjectNode row,String field) {
        BigInteger value=StrictJson.integer(row.get(field),BigInteger.ONE,StrictJson.UINT64_MAX);row.put(field,value.toString());
    }
    private static void safeRemaining(JsonNode value) {
        if(value.isIntegralNumber())StrictJson.require(value.bigIntegerValue().abs().compareTo(SAFE)<=0,"undeclared unsafe integer in loaded-feature public output");
        if(value.isContainerNode())for(JsonNode child:value)safeRemaining(child);
    }
}
