package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy;
import org.xar.ck3.control.application.planning.military.WarDeclarationContinuity;
import org.xar.ck3.control.application.planning.military.OrdinaryWarAdmissionRules;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.RaiktorExitPostwarEvidence;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads;
import org.xar.ck3.control.nativebridge.capabilities.interactions.TitleClaimsPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineCodec;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineAdapter;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original generic War/Route/Retreat EXECUTE branches, retaining their installed domain producers. */
public final class RootWarPublicStepProducts {
    private RootWarPublicStepProducts(){ }
    private static final String ID="(0|[1-9][0-9]*)";
    private static final Pattern PREVIEW=Pattern.compile("preview-move-army-"+ID+"-to-"+ID);
    private static final Pattern HORIZON=Pattern.compile("query-route-contact-horizon-v1-"+ID+"-to-"+ID+"-h-"+ID+"-([0-9-]+)");
    private static final Pattern RETREAT_PREVIEW=Pattern.compile("preview-active-combat-retreat-v1-"+ID+"-to-"+ID);
    private static final Pattern RETREAT_ORDER=Pattern.compile("order-active-combat-retreat-v1-"+ID
            +"-revision-"+ID+"-combat-(-?(?:0|[1-9][0-9]*))-side-([01])-scope-(owner_subset|full_side)-to-"+ID+"-token-([A-Za-z0-9_-]{32,128})");
    private static final Obj EMPTY=new Obj(Map.of());
    private static final java.util.Set<PublicMethod> ORDINARY_ACTIONS=EnumSet.of(PublicMethod.MOVE_ARMY,PublicMethod.START_ASSAULT,
            PublicMethod.STOP_ASSAULT,PublicMethod.DECLARE_WAR,PublicMethod.ENFORCE_DEMANDS,PublicMethod.OFFER_WHITE_PEACE,PublicMethod.SURRENDER_WAR);
    enum ReadKind { CONTACT,TITLE,WAR,WAR_ENTRY,ROUTE,RETREAT_PREVIEW,CLOSED,SPECIAL,SUPPLEMENTAL,MERCENARY,DISABLED_EXIT_PREVIEW }
    record Route(MilitaryReadObservation.Kind kind,int subject,int target,List<Integer> hostiles) {
        Route {Objects.requireNonNull(kind);new PublicUnitId(subject);new PositiveId(target);hostiles=List.copyOf(hostiles);}
        String step(){return kind==MilitaryReadObservation.Kind.ROUTE_PREVIEW?"preview-move-army-"+subject+"-to-"+target
                :MilitaryRouteAudit.horizonStep(subject,target,hostiles);}
    }
    /** Same installed instances only; no registry, observation authority or native producer is created here. */
    record Reads(RootReadContractCatalog catalog,ArmyWarReads wars,ArmyForecastReads forecasts,
            ArmyPlanningReads planning,ContactScopeReads contacts,ArmyClosedReadContracts closed,ArmySpecialWarReads special,
            ArmyWarSupplementalReads supplemental,FinanceReadContracts finance,PlanningReadPort physical,
            NativeEffectEvidence.FrameLoader frames) {
        Reads {Objects.requireNonNull(catalog);Objects.requireNonNull(wars);Objects.requireNonNull(forecasts);
            Objects.requireNonNull(planning);Objects.requireNonNull(contacts);Objects.requireNonNull(closed);Objects.requireNonNull(special);
            Objects.requireNonNull(supplemental);Objects.requireNonNull(finance);Objects.requireNonNull(physical);Objects.requireNonNull(frames);
            StrictJson.require(catalog.containsIdentity(finance.contract(FinanceReadContracts.Query.MERCENARIES)),"Market READ requires the identical installed Finance contract");
            for(var family:families(wars,forecasts,planning,contacts,closed,special,supplemental))StrictJson.require(catalog.families().stream().anyMatch(installed -> installed == family),
                    "War EXECUTE requires the identical installed read families");}
    }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        var army=actual.army();var products=army.products();var military=actual.military();
        var contact=actual.contactScopes();var titles=actual.additionalDomains().driverRegistry().titleClaims();
        StrictJson.require(contact.context()==context,"Contact EXECUTE must retain its same physical Root");titles.requireContext(context);
        var remaining=actual.remainingDomains();var ordinary=remaining.armyOrdinary().service();
        Reads reads=new Reads(actual.bindings().readCatalog(),military.warReads(),military.forecasts(),
                military.planning(),contact.reads(),products.closedContracts(),products.specialWarReads(),products.supplementalWarReads(),
                context.finance().definitions(),context.reads(),context.frameLoader());
        RootPublicStepExecution.OwnerGuard owner=identical->{
            if(identical!=context||actual.context()!=context||actual.army()!=army||army.products()!=products
                    ||actual.military()!=military||actual.contactScopes()!=contact||contact.context()!=identical||contact.reads()!=reads.contacts()
                    ||actual.remainingDomains()!=remaining||remaining.armyOrdinary().service()!=ordinary
                    ||identical.readCatalog()!=reads.catalog()||identical.reads()!=reads.physical()||identical.finance().definitions()!=reads.finance()
                    ||actual.additionalDomains().driverRegistry().titleClaims()!=titles)
                throw new IOException("War EXECUTE crossed its installed physical Root/domain owners");
            titles.requireContext(identical);
            identical.game().verify();
        };
        List<ExactRef> sources=sources(actual,reads);var result=new ArrayList<RootPublicStepExecution.Product>();
        for(ReadKind kind:ReadKind.values())result.add(new RootPublicStepExecution.Read("original-war-read-"+kind.name().toLowerCase(Locale.ROOT),
                operation->readKind(operation).filter(kind::equals).isPresent(),owner,
                (original,frame,known,same,caller,archive)->{
                    owner.requireContext(context);context.writer().requireSession(same);
                    if(kind==ReadKind.DISABLED_EXIT_PREVIEW)throw unsupported("native exit-terms v2 is disabled after the reproducible loaded-effect preview crash at CK3 RVA 0x334C668");
                    if(kind==ReadKind.SPECIAL)requireSpecialCapability(original,caller.step());
                    if(kind==ReadKind.SUPPLEMENTAL)requireSupplementalCapability(original,caller.step());
                    requireHeld(original,frame,known);caller.requireCurrent(original);RawJson value;
                    if(kind==ReadKind.TITLE){
                        var selector=titleSelector(caller.step()).orElseThrow();
                        value=titles.read(same,frame,new TitleClaimsPublicCodec.Request(frame.identity().frame().revision(),selector),original.deadline());
                    }else if(kind==ReadKind.RETREAT_PREVIEW){
                        requireRetreatCapabilities(original);
                        var before=new ArmyRetreatFrames.Current(frame,original.deadline());
                        ArmyCalls.RetreatPreview input=retreatPreview(caller.step(),revision(frame)).orElseThrow();
                        var captured=products.retreatReads().previewBorrowed(same,input,before);
                        value=ArmyPublicWire.encodeExactSourceBound(ArmyRetreatPublicPresenter.preview(captured.captured().value()),before.context());
                    }else value=read(reads,original,frame,same,caller,archive);
                    context.writer().requireSession(same);owner.requireContext(context);return value;
                },sources,kind==ReadKind.DISABLED_EXIT_PREVIEW||kind==ReadKind.SPECIAL||kind==ReadKind.SUPPLEMENTAL?RootPublicStepExecution.ReadValidation.OWNER_ORDERED:RootPublicStepExecution.ReadValidation.CENTRAL_BEFORE));
        result.add(new RootPublicStepExecution.Action("original-active-retreat-order",
                operation->retreatOrder(operation,new ArmyCalls.Revision(new Missing<>())).isPresent(),owner,
                (original,frame,known,same,caller)->{
                    owner.requireContext(context);context.writer().requireSession(same);requireHeld(original,frame,known);caller.requireCurrent(original);
                    requireRetreatCapabilities(original);
                    var before=new ArmyRetreatFrames.Current(frame,original.deadline());
                    var input=retreatOrder(caller.step(),revision(frame)).orElseThrow();
                    return army.prepareRetreatCommand(same,input,before,RootPublicStepExecution.actionId(original,caller));
                },(receipt,archive,same,caller)->{
                    owner.requireContext(context);context.writer().requireSession(same);requireCanonical(receipt,archive,same,caller);
                    var reply=products.retreatOrders().presentCommitted(same,receipt);
                    Obj presented=ArmyRetreatPublicPresenter.order(reply.order(),receipt.command().operation(),
                            reply.nativeSubmission().orElseThrow(()->new IOException("original retreat result is UNKNOWN; the consumed token cannot be replayed")),reply.actualAfter());
                    return ArmyPublicWire.encodeExactSourceBound(presented,reply.source());
                },sources));
        result.add(new RootPublicStepExecution.Action("original-generic-war-action",
                operation->ordinaryCall(operation,BigInteger.ONE).isPresent(),owner,
                (original,frame,known,same,caller)->{
                    owner.requireContext(context);context.writer().requireSession(same);requireHeld(original,frame,known);caller.requireCurrent(original);
                    ArmyCalls.Call call=ordinaryCall(caller.step(),frame.identity().frame().revision()).orElseThrow();
                    requireActionAdvertised(original,caller.step());
                    var source=new Context(frame.identity(),frame.source(),frame.sessionId(),original.deadline());
                    String actionId=RootPublicStepExecution.actionId(original,caller);
                    return call.method()==PublicMethod.SURRENDER_WAR
                            ?ordinary.prepareGenericAutomaticSurrenderCommand(same,(ArmyCalls.War)call,source,actionId)
                            :ordinary.prepareCommand(same,call,source,actionId);
                },(receipt,archive,same,caller)->{
                    owner.requireContext(context);context.writer().requireSession(same);requireCanonical(receipt,archive,same,caller);
                    return RootWarActionExecutionResult.present(receipt,archive,same,caller,context.frameLoader());
                },sources));
        return List.copyOf(result);
    }

    /** Only the exact already-owned ordinary parser can create calls; unrelated Army/hire/clock operations are excluded. */
    static Optional<ArmyCalls.Call> ordinaryCall(OperationKey operation,BigInteger actualRevision){
        if(!ArmyOrdinaryPlannerCalls.supports(operation))return Optional.empty();
        try{
            ArmyCalls.Call call=ArmyOrdinaryPlannerCalls.decode(operation,EMPTY,actualRevision);
            return ORDINARY_ACTIONS.contains(call.method())?Optional.of(call):Optional.empty();
        }catch(IllegalArgumentException invalid){return Optional.empty();}
    }

    static Optional<ReadKind> readKind(OperationKey operation){
        Objects.requireNonNull(operation);
        if(contactQuery(operation).isPresent())return Optional.of(ReadKind.CONTACT);
        if(titleSelector(operation).isPresent())return Optional.of(ReadKind.TITLE);
        if(warCall(operation,new ArmyCalls.Revision(new Missing<>())).isPresent())return Optional.of(ReadKind.WAR);
        if(WarEntryAssessmentCodec.parseStep(operation.value()).isPresent())return Optional.of(ReadKind.WAR_ENTRY);
        if(route(operation).isPresent())return Optional.of(ReadKind.ROUTE);
        if(retreatPreview(operation,new ArmyCalls.Revision(new Missing<>())).isPresent())return Optional.of(ReadKind.RETREAT_PREVIEW);
        if(closedCall(operation,new ArmyCalls.Revision(new Missing<>())).isPresent())return Optional.of(ReadKind.CLOSED);
        if(ArmySpecialWarReads.supports(operation))return Optional.of(ReadKind.SPECIAL);
        if(ArmyWarSupplementalReads.supports(operation))return Optional.of(ReadKind.SUPPLEMENTAL);
        if(operation.value().equals("query-player-mercenary-context-v1"))return Optional.of(ReadKind.MERCENARY);
        if(disabledExit(operation))return Optional.of(ReadKind.DISABLED_EXIT_PREVIEW);
        return Optional.empty();
    }
    static Optional<ContactScopeObservation.Query> contactQuery(OperationKey operation){
        try{return Optional.of(ContactScopeObservation.parseQuery(operation.value()));}
        catch(IllegalArgumentException invalid){return Optional.empty();}
    }
    static Optional<InteractionTitleSelectorReads.Selector> titleSelector(OperationKey operation){
        String step=operation.value();
        try{
            InteractionTitleSelectorReads.Selector selector;
            if(step.startsWith("query-title-own-laws-v1-"))selector=new InteractionTitleSelectorReads.LawSelector(
                    new InteractionModels.FullId(decimal(step.substring("query-title-own-laws-v1-".length()),new BigInteger("4294967294")).longValueExact()));
            else if(step.startsWith("query-title-holder-v1-"))selector=new InteractionTitleSelectorReads.HolderSelector(
                    new InteractionModels.Int32Id(decimal(step.substring("query-title-holder-v1-".length()),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact()));
            else if(step.startsWith("query-player-claims-v1-")){
                var claims = org.xar.ck3.control.application.action.NativeStepDiscriminator.ClaimsIdentity.parse(operation).orElseThrow();
                List<InteractionModels.Int32Id> ids = claims.titles().stream().map(id -> new InteractionModels.Int32Id(id)).toList();
                selector=new InteractionTitleSelectorReads.ClaimsSelector(ids);
            }else return Optional.empty();
            StrictJson.require(InteractionTitleSelectorReads.operation(selector).equals(operation),"title selector changed the original literal");return Optional.of(selector);
        }catch(IllegalArgumentException|ArithmeticException invalid){return Optional.empty();}
    }
    static Optional<ArmyCalls.War> warCall(OperationKey operation,ArmyCalls.Revision revision){
        String step=operation.value();
        for(PublicMethod method:List.of(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
                PublicMethod.QUERY_WAR_TERMINATION_TERMS,PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS)){
            String prefix=switch(method){
                case QUERY_WAR_OCCUPATION_TARGETS_V1->"query-war-occupation-targets-v1-";
                case QUERY_WAR_TERMINATION_OPTIONS->"query-war-termination-options-";
                case QUERY_WAR_TERMINATION_TERMS->"query-war-termination-terms-v1-";
                case QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS->"query-outbound-war-white-peace-status-v1-";
                default->throw new IllegalStateException();};
            if(step.startsWith(prefix))try{return Optional.of(new ArmyCalls.War(method,revision,decimal(step.substring(prefix.length()),BigInteger.valueOf(Integer.MAX_VALUE))));}
            catch(IllegalArgumentException invalid){return Optional.empty();}
        }return Optional.empty();
    }
    static Optional<ArmyCalls.Call> closedCall(OperationKey operation,ArmyCalls.Revision revision){
        if(operation.value().equals("query-player-default-raise-v1"))return Optional.of(new ArmyCalls.Frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,revision));
        String prefix="query-raiktor-actual-truce-expiry-v1-";
        if(!operation.value().startsWith(prefix))return Optional.empty();
        try{return Optional.of(new ArmyCalls.Truce(revision,new PositiveId(decimal(operation.value().substring(prefix.length()),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact())));}
        catch(IllegalArgumentException invalid){return Optional.empty();}
    }
    static boolean disabledExit(OperationKey operation){
        String prefix="query-war-termination-exit-terms-v2-";
        if(!operation.value().startsWith(prefix))return false;
        try{return decimal(operation.value().substring(prefix.length()),BigInteger.valueOf(Integer.MAX_VALUE)).signum()>0;}
        catch(IllegalArgumentException invalid){return false;}
    }
    static Optional<Route> route(OperationKey operation){
        try{
            var preview=PREVIEW.matcher(operation.value());
            if(preview.matches())return Optional.of(new Route(MilitaryReadObservation.Kind.ROUTE_PREVIEW,Integer.parseInt(preview.group(1)),Integer.parseInt(preview.group(2)),List.of()));
            var horizon=HORIZON.matcher(operation.value());if(!horizon.matches())return Optional.empty();
            List<Integer> ids=java.util.Arrays.stream(horizon.group(4).split("-",-1)).map(token->decimal(token,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact()).toList();
            StrictJson.require(ids.size()==Integer.parseInt(horizon.group(3)),"exact original hostile count required");
            Route result=new Route(MilitaryReadObservation.Kind.CONTACT_HORIZON,Integer.parseInt(horizon.group(1)),Integer.parseInt(horizon.group(2)),ids);
            StrictJson.require(result.step().equals(operation.value()),"canonical ordered complete hostile scope required");return Optional.of(result);
        }catch(IllegalArgumentException|ArithmeticException invalid){return Optional.empty();}
    }
    static Optional<ArmyCalls.RetreatPreview> retreatPreview(OperationKey operation,ArmyCalls.Revision revision){
        var match=RETREAT_PREVIEW.matcher(operation.value());if(!match.matches())return Optional.empty();
        try{return Optional.of(new ArmyCalls.RetreatPreview(revision,new PublicUnitId(Integer.parseInt(match.group(1))),new PositiveId(Integer.parseInt(match.group(2)))));}
        catch(IllegalArgumentException invalid){return Optional.empty();}
    }
    static Optional<ArmyCalls.RetreatOrder> retreatOrder(OperationKey operation,ArmyCalls.Revision current){
        var match=RETREAT_ORDER.matcher(operation.value());if(!match.matches())return Optional.empty();
        try{
            BigInteger revision=decimal(match.group(2),StrictJson.UINT64_MAX);UInt64.positive(revision);
            if(current.value() instanceof Present<BigInteger> actual)StrictJson.require(actual.value().equals(revision),"retreat step revision differs from its actual held frame");
            var input=new ArmyCalls.RetreatOrder(new ArmyCalls.Revision(new Present<>(revision)),new PublicUnitId(Integer.parseInt(match.group(1))),
                    new ArmyTypes.FullId(Integer.parseInt(match.group(3))),Integer.parseInt(match.group(4)),Scope.valueOf(match.group(5).toUpperCase(Locale.ROOT)),
                    new PositiveId(Integer.parseInt(match.group(6))),match.group(7));
            StrictJson.require(ArmyRetreatPreview.orderStep(input.selected(),revision,input.combat(),input.sideIndex(),input.scope(),input.target(),input.token()).equals(operation.value()),"retreat step changed its canonical typed arguments");
            return Optional.of(input);
        }catch(IllegalArgumentException invalid){return Optional.empty();}
    }

    static RawJson read(Reads reads,PlanningRequest original,Complete frame,Session same,
            PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive)throws IOException {
        try{return readOriginal(reads,original,frame,same,caller,archive);}
        catch(IllegalArgumentException|IllegalStateException unavailable){
            throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "original War READ unavailable: "+unavailable.getMessage(),Optional.empty());
        }
    }
    private static RawJson readOriginal(Reads reads,PlanningRequest original,Complete frame,Session same,
            PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive)throws IOException {
        var before=new ArmyRetreatFrames.Current(frame,original.deadline());var context=before.context();
        if(caller.step().value().equals("query-player-mercenary-context-v1")){
            // The original Driver acquires this six-field M5 source before sending the market query.
            Obj source=mercenarySourceFrame(frame.semantic());
            var actual=known(reads.finance().read(same,FinanceReadContracts.Query.MERCENARIES,reads.physical(),original));
            requireOriginal(frame,same,caller,actual,archive,reads.frames());
            var replay=reads.finance().decodeOriginal(FinanceReadContracts.Query.MERCENARIES,actual.receipt(),frame.semantic());
            StrictJson.require(replay.receipt().equals(actual.receipt())&&replay.originalResult().equals(actual.value().originalResult()),"Market cold decoder changed its actual original packet");
            Obj raw=actual.value().originalResult();
            return ArmyPublicWire.encodeExactSourceBound(raw.with("backend_id",new OpportunityJson.Text("native-headless"))
                    .with("mercenary_query_source_frame_v1",source),context);
        }
        if(ArmyWarSupplementalReads.supports(caller.step())){
            requireSupplementalCapability(original,caller.step());var selected=new ArmyWarSupplementalReads.Selection(original,caller.step());
            var actual=known(reads.supplemental().collect(same,reads.catalog(),selected));requireOriginal(frame,same,caller,actual,archive,reads.frames());
            StrictJson.require(reads.supplemental().replayArchived(reads.catalog(),selected,actual.originalReceipt(),archive).equals(actual.value()),
                    "supplemental War READ cold archived replay changed its original");
            return ArmyWarSupplementalReadCodec.fullDriverResult(actual.value());
        }
        if(ArmySpecialWarReads.supports(caller.step())){
            requireSpecialCapability(original,caller.step());var selected=specialSelection(original,caller);
            var actual=known(reads.special().collect(same,reads.catalog(),selected));requireOriginal(frame,same,caller,actual,archive,reads.frames());
            StrictJson.require(reads.special().replayArchived(reads.catalog(),selected,actual.originalReceipt(),archive).equals(actual.value()),
                    "special War READ cold archived replay changed its actual original");
            return ArmySpecialWarReadCodec.fullDriverResult(actual.value());
        }
        Optional<ArmyCalls.Call> closed=closedCall(caller.step(),revision(frame));
        if(closed.isPresent()){
            var selected=new ArmyClosedReadContracts.Selection(closed.orElseThrow(),context);
            var contract=reads.closed().issue(reads.catalog(),selected);var actual=known(reads.physical().read(same,contract,reads.closed().request(selected)));
            requireOriginal(frame,same,caller,actual,archive,reads.frames());StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"Closed decoder replay changed its original");
            return encode(ArmyClosedOriginalResultCodec.encode(closed.orElseThrow(),context,actual.receipt(),actual.value(),frame.semantic()),context);
        }
        Optional<ContactScopeObservation.Query> query=contactQuery(caller.step());
        if(query.isPresent()){
            var selected=ContactScopeReads.Selection.current(query.orElseThrow(),frame,original.deadline());
            var contract=reads.contacts().contract(reads.catalog(),selected);var actual=known(reads.contacts().collect(same,reads.catalog(),selected));
            requireOriginal(frame,same,caller,actual,archive,reads.frames());StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"Contact decoder replay changed its actual original");
            return ContactScopePublicCodec.encodeOriginal(actual.value());
        }
        Optional<ArmyCalls.War> war=warCall(caller.step(),revision(frame));
        if(war.isPresent()){
            var selected=reads.wars().selection(same,reads.catalog(),war.orElseThrow(),before);var contract=reads.wars().contract(reads.catalog(),selected);
            var actual=known(reads.wars().read(same,contract,selected));requireOriginal(frame,same,caller,actual,archive,reads.frames());
            StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"War decoder replay changed its actual original");
            return encode(ArmyWarOriginalResultCodec.encode(ArmyWarReads.scope(selected,actual.receipt().request()),actual.receipt(),actual.value()),context);
        }
        var targets=WarEntryAssessmentCodec.parseStep(caller.step().value());
        if(targets.isPresent()){
            var call=new ArmyCalls.WarEntry(revision(frame),targets.orElseThrow().stream().map(PositiveId::new).toList());
            var selected=new ArmyForecastReads.Selection(call,context);var contract=reads.forecasts().contract(reads.catalog(),selected);
            var actual=known(reads.forecasts().collect(same,reads.catalog(),selected));requireOriginal(frame,same,caller,actual,archive,reads.frames());
            StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"WarEntry decoder replay changed its actual original");
            var after=new ArmyRetreatFrames.Current(RootGuardEvidence.loadFrame(actual.receipt().after().binding(),archive,reads.frames()),original.deadline());
            return ArmyForecastService.encode(PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS,new ArmyForecastService.Reply(before,after,actual));
        }
        var route=route(caller.step()).orElseThrow(()->new IOException("UnsupportedStepError: no original War READ matched"));
        var selected=new ArmyPlanningReads.Selection(original,route.kind(),route.subject(),route.target(),route.hostiles());
        StrictJson.require(selected.step().equals(caller.step().value()),"Route selector changed the exact original literal");
        var actual=known(reads.planning().collect(same,reads.catalog(),selected));requireOriginal(frame,same,caller,actual,archive,reads.frames());
        StrictJson.require(reads.planning().decode(selected,actual.receipt()).equals(actual.value()),"Route decoder replay changed its actual original");
        return ArmyPublicWire.encodeExactSourceBound(actual.value().normalizedResult(),context);
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> actual)throws IOException {
        if(actual instanceof PlanningReadResult.Known<T> known)return known;
        throw new IOException("BridgeUnavailableError: "+((PlanningReadResult.Unavailable<T>)actual).reason());
    }
    private static <T> void requireOriginal(Complete held,Session same,PublicPlanningCodec.ExecuteRequest caller,
            PlanningReadResult.Known<T> actual,OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames)throws IOException {
        var receipt=actual.receipt();var ref=archive.readReferenceOf(receipt);
        StrictJson.require(actual.originalReceipt().equals(ref)&&archive.loadRead(ref).equals(receipt)
                &&receipt.request().operation().equals(caller.step()),"War READ must retain its original central request/receipt");
        for(var guard:List.of(receipt.before(),receipt.after())){
            RootGuardEvidence.requireHistory(guard.binding(),archive,same);Complete loaded=RootGuardEvidence.loadFrame(guard.binding(),archive,frames);
            StrictJson.require(guard.originalBindingSha256().equals(held.fullBindingSha256())&&loaded.identity().equals(held.identity())
                    &&loaded.source().equals(held.source())&&loaded.sessionId().equals(held.sessionId())
                    &&loaded.connectionGeneration().equals(held.connectionGeneration())&&loaded.fullBindingSha256().equals(held.fullBindingSha256())
                    &&loaded.semantic().equals(held.semantic()),"War READ crossed the complete held public planning frame");
        }
    }
    private static void requireHeld(PlanningRequest original,Complete frame,Known known){
        Objects.requireNonNull(known);StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())
                &&original.sessionId().equals(frame.sessionId())&&original.observations().snapshot().equals(frame.semantic()),"War EXECUTE changed the original held planning frame");
    }
    private static void requireRetreatCapabilities(PlanningRequest original){
        if(!original.observations().bridgeCapabilities().containsAll(List.of("game.command.query-battle-control-snapshot-v1-N",
                "game.command.preview-move-army-N-to-N","game.command.move-army-N-to-N")))
            throw unsupported("native DLL lacks the battle query, exact move preview, or player move capability required for active retreat");
    }
    private static void requireActionAdvertised(PlanningRequest original,OperationKey step){
        if(original.observations().actionSteps().contains(step))return;
        ArmyCalls.Call call=ordinaryCall(step,original.before().frame().revision()).orElseThrow();
        if(call.method()==PublicMethod.OFFER_WHITE_PEACE)throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                "native white_peace submission lacks fresh same-frame white-peace decision readiness",Optional.empty());
        if(call.method()==PublicMethod.SURRENDER_WAR)throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                "native surrender submission lacks fresh same-frame de-jure emergency or exact WAR31 one-shot readiness",Optional.empty());
        throw unsupported("native DLL does not implement gameplay step "+step.value());
    }
    static ArmySpecialWarReads.Selection specialSelection(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller){
        Optional<ArmySpecialWarReads.H2743Claim> claim=Optional.empty();
        if(ArmySpecialWarReads.kind(caller.step())==ArmySpecialWarReads.Kind.H2743){
            var source=((PublicPlanningCodec.FrameValue)caller.expectedH2743Frame()).value();
            claim=Optional.of(new ArmySpecialWarReads.H2743Claim(source.snapshotId(),source.revision(),source.nativeRevision(),source.dateRaw(),
                    source.actorCharacterId(),source.episodeRunId(),source.warId(),source.connectionGeneration()));
        }
        return new ArmySpecialWarReads.Selection(original,caller.step(),claim);
    }
    private static void requireSpecialCapability(PlanningRequest original,OperationKey operation){
        var kind=ArmySpecialWarReads.kind(operation);
        if(!original.observations().bridgeCapabilities().contains(ArmySpecialWarReads.capability(kind)))throw unsupported(switch(kind){
            case H2743->"native DLL cannot query the exact H2743 existing truce slot";
            case PRISONERS->"native DLL cannot query war prisoner release pairs";
            case BOUND_LOSS->"native DLL cannot query exact-store war-bound cleanup";});
    }
    private static void requireSupplementalCapability(PlanningRequest original,OperationKey operation){
        if(!original.observations().bridgeCapabilities().contains(ArmyWarSupplementalReads.capability(ArmyWarSupplementalReads.kind(operation))))
            throw unsupported(operation.value().startsWith("query-province-local-siege-v1-")
                    ?"native DLL cannot query local Province siege state":"native DLL cannot query the defender de-jure exit baseline");
    }
    private static void requireCanonical(ActionReceipt receipt,OutcomeArchive archive,Session same,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        StrictJson.require(receipt.command().operation().equals(caller.step())
                &&ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive).filter(receipt::equals).isPresent(),"War EXECUTE result lacks its actual canonical writer receipt");
    }
    private static ArmyCalls.Revision revision(Complete frame){return new ArmyCalls.Revision(new Present<>(frame.identity().frame().revision()));}
    static Obj mercenarySourceFrame(Obj actualSemantic){
        return DriverJson.object(ObservedOpportunitySelector.observedFrame(DriverJson.encode(Objects.requireNonNull(actualSemantic))),65536);
    }
    private static BigInteger decimal(String text,BigInteger maximum){
        StrictJson.require(text.matches("0|[1-9][0-9]*")&&text.length()<=20,"canonical bounded decimal identity required");
        BigInteger result=new BigInteger(text);StrictJson.require(result.signum()>=0&&result.compareTo(maximum)<=0,"identity exceeds its original integer domain");return result;
    }
    private static RawJson encode(RawJson actual,Context context){return ArmyPublicWire.encodeExactSourceBound(DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES),context);}
    private static PublicServiceFailure unsupported(String message){return new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,message,Optional.empty());}
    private static List<RootReadContractCatalog.Family<?,?>> families(ArmyWarReads wars,ArmyForecastReads forecasts,ArmyPlanningReads planning,ContactScopeReads contacts,ArmyClosedReadContracts closed,ArmySpecialWarReads special,ArmyWarSupplementalReads supplemental){
        var result=new ArrayList<RootReadContractCatalog.Family<?,?>>();result.addAll(wars.families());result.addAll(forecasts.families());result.addAll(planning.families());result.addAll(contacts.families());result.addAll(closed.families());result.addAll(special.families());result.addAll(supplemental.families());return List.copyOf(result);
    }
    private static List<ExactRef> sources(RootInstalledCatalog actual,Reads reads)throws IOException {
        var sources=new LinkedHashSet<ExactRef>();
        for(Class<?> type:List.of(RootWarPublicStepProducts.class,RootPublicStepExecution.class,RootWarActionExecutionResult.class,RootArmyReadPacketVerifier.class,RootTitleClaimsRuntime.class,RootContactRuntime.class))
            sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,type));
        for(Class<?> type:List.of(ArmyWarReadCodec.class,ArmyWarOriginalResultCodec.class,ArmyTypes.class,ArmyCalls.class,ArmyCallCodec.class,ArmyNativeReadEvidence.class,
                ArmyRetreatFrames.class,ArmyRetreatTokens.class,ArmyRetreatPublicPresenter.class,ArmyPublicWire.class,ArmyLegacyTruceResultCodec.class,
                ArmySpecialWarReads.class,ArmySpecialWarReadCodec.class,ArmyWarSupplementalReads.class,ArmyWarSupplementalReadCodec.class,
                OrdinaryAutomaticSurrenderPolicy.class,ArmyOrdinaryActionArguments.class,ArmyAssaultSelection.class,ArmyWarOccupationCodec.class,
                WarDeclarationContinuity.class,OrdinaryWarAdmissionRules.class,OrdinaryWhitePeacePolicy.class,NativeEffectEvidence.class,
                NativeRecordedEvidenceVerifier.class,FinanceReadContracts.class,RootGuardEvidence.class))
            sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,type));
        for(Class<?> type:List.of(ArmyWarReads.class,ArmyForecastReads.class,ArmyPlanningReads.class,ContactScopeReads.class,
                ContactScopePublicCodec.class,ArmyForecastService.class,ArmyForecastPublicResultCodec.class,ArmyRetreatPreview.class,
                ArmyRetreatService.class,ArmyRetreatOrderService.class,ArmyRetreatOrders.class,ArmyRetreatDomain.class,ArmyRetreatComposite.class,ArmyRuntimeInstaller.class,WarEntryAssessmentCodec.class,
                ArmyClosedOriginalResultCodec.class,ArmyClosedReadContracts.class,ArmyClosedReadCodec.class,
                ArmyOrdinaryActionService.class,ArmyOrdinaryActionPreparation.class,ArmyOrdinaryPlannerCalls.class,NativeOrdinaryWarAdmission.class,
                InteractionTitleSelectorReads.class,InteractionModels.class,TitleClaimsPublicCodec.class))
            sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,type));
        sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.G2_RESEARCH,RaiktorExitPostwarEvidence.class));
        for(Class<?> type:List.of(DeJureExitBaseline.class,DeJureExitBaselineCodec.class,DeJureExitBaselineAdapter.class,
                OrdinaryWarExitObservationCodec.class,DeclarationContract.class))
            sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.WAVE2_MILITARY,type));
        sources.add(actual.publicStepSourceAt("wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/military/MilitaryRouteAudit.java",MilitaryRouteAudit.class));
        sources.add(actual.publicStepSourceAt("planning-runtime/src/main/java/org/xar/ck3/control/planning/opportunity/ObservedOpportunitySelector.java",ObservedOpportunitySelector.class));
        sources.add(reads.special().sources().h2743Native());sources.add(reads.special().sources().prisonerNative());sources.add(reads.special().sources().boundLossNative());
        sources.add(reads.supplemental().sources().provinceNative());sources.add(reads.supplemental().sources().deJureNative());
        sources.add(reads.finance().definitionSource(FinanceReadContracts.Query.MERCENARIES));
        for(var family:families(reads.wars(),reads.forecasts(),reads.planning(),reads.contacts(),reads.closed(),reads.special(),reads.supplemental())){sources.add(family.definitionSource());sources.add(family.decoderSource());}
        return List.copyOf(sources);
    }
}
