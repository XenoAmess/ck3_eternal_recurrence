package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Public operations use the root's one read coordinator or prepare commands for its durable action coordinator. */
public final class InteractionCapabilities {
    public record Sources(ExactRef marriage, ExactRef laws, ExactRef claims, ExactRef holder,
            ExactRef appointment, ExactRef ordinary, ExactRef playerControl, ExactRef grant, ExactRef pending, ExactRef heir) {
        public Sources { for(ExactRef source:List.of(marriage,laws,claims,holder,appointment,ordinary,playerControl,grant,pending,heir)) need(source.bytes()>0,"actual original producer source required"); }
    }
    public record ReadPlan(List<FullId> lawTitles,List<List<Int32Id>> claimTitleSets,List<Int32Id> holderTitles) {
        public ReadPlan {
            lawTitles=List.copyOf(lawTitles); claimTitleSets=claimTitleSets.stream().map(List::copyOf).toList(); holderTitles=List.copyOf(holderTitles);
            unique(lawTitles,4096); unique(holderTitles,4096); unique(claimTitleSets,4096);
            for(List<Int32Id> ids:claimTitleSets) { need(!ids.isEmpty(),"claims require explicit ordered TitleIDs"); unique(ids,4096); }
        }
    }
    public record LawRoute(FullId title,ReadContract<TitleOwnLaws> contract) { }
    public record ClaimsRoute(List<Int32Id> titles,ReadContract<PlayerClaims> contract) { public ClaimsRoute { titles=List.copyOf(titles); } }
    public record HolderRoute(Int32Id title,ReadContract<TitleHolder> contract) { }
    /** Projection of the single installed Finance ROOT read; no second native root contract. */
    public interface RootHeirSource {
        PlanningReadResult<HeirSubject> read(Context context);
        PlanningReadResult<HeirSubject> read(Session borrowed,Context context);
        default HeirSubject requireSubject(Context context,PlanningReadResult.Known<HeirSubject> actual) {
            return FamilyHeirNativeProjection.requireSubject(actual,context);
        }
        default HeirSubject requireSubject(Session borrowed,Context context,PlanningReadResult.Known<HeirSubject> actual) {
            Objects.requireNonNull(borrowed);return requireSubject(context,actual);
        }
    }
    public static final class Installation {
        private final ReadContract<MarriageChoices> marriage;
        private final ReadContract<OrdinaryContext> ordinary;
        private final ReadContract<ControlObservation> control;
        private final ReadContract<GrantResult> grant;
        private final ReadContract<Appointment> appointment;
        private final ReadContract<PendingContext> pending;
        private final RootHeirSource heirSubject;
        private final ReadContract<HeirMarriageLegality> heirLegality;
        private final List<LawRoute> laws;
        private final List<ClaimsRoute> claims;
        private final List<HolderRoute> holders;
        public Installation(Sources sources,ReadPlan plan,RootHeirSource genuineRootSubject) {
            Objects.requireNonNull(sources); Objects.requireNonNull(plan); heirSubject=Objects.requireNonNull(genuineRootSubject);
            marriage=advertised("marriage-choices","query-arrange-marriage-choices","game.command.query-arrange-marriage-choices",sources.marriage(),
                req->empty(),r->InteractionReads.marriageChoices(r,InteractionArguments.context(r.request())));
            ordinary=advertised("ordinary-query",OrdinaryInteractionCodec.QUERY_STEP,OrdinaryInteractionCodec.QUERY_CAPABILITY,sources.ordinary(),
                req->OrdinaryInteractionCodec.request(InteractionArguments.context(req),InteractionArguments.ordinary(InteractionArguments.parseApp(req.arguments())),false),
                r->OrdinaryInteractionCodec.query(r.original().originalResultToken().orElseThrow(),InteractionArguments.context(r.request()),InteractionArguments.ordinary(InteractionArguments.parseApp(r.request().arguments()))));
            control=new ReadContract<>("interactions:control-context",new OperationKey("player-control-v1"),Optional.empty(),"player_control_source_inventory",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.playerControl(),
                (req,id)->new NativeRequest("player-control-v1",Optional.empty(),PlayerControlCodec.request(InteractionArguments.context(req),InteractionArguments.control(InteractionArguments.parseApp(req.arguments())),id)),
                r->PlayerControlCodec.decode(r.original().originalResultToken().orElseThrow(),InteractionArguments.context(r.request()),InteractionArguments.control(InteractionArguments.parseApp(r.request().arguments()))),
                r->PlayerControlCodec.decode(r.original().originalResultToken().orElseThrow(),InteractionArguments.context(r.request()),InteractionArguments.control(InteractionArguments.parseApp(r.request().arguments()))));
            grant=sourcePrivate("grant-query",GrantTitleCodec.step(GrantOperation.QUERY),"_grant_title_picker_private_enabled_v1",sources.grant(),
                req->GrantTitleCodec.request(InteractionArguments.context(req),InteractionArguments.grant(InteractionArguments.parseApp(req.arguments()))),
                r->GrantTitleCodec.decode(r.original().originalResultToken().orElseThrow(),InteractionArguments.context(r.request()),InteractionArguments.grant(InteractionArguments.parseApp(r.request().arguments()))));
            appointment=new ReadContract<>("interactions:current-appointment",org.xar.ck3.control.application.action.NativeStepDiscriminator.IngameWindow.TITLE_APPOINTMENT.operationKey(),Optional.of("game.command.query-current-title-appointment-v1"),"game.command.query-current-title-appointment-v1",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.appointment(),
                (req,id)->new NativeRequest("query-ingame-ui-window-v1","game.command.query-current-title-appointment-v1",InteractionArguments.appointmentNative(InteractionArguments.appointment(InteractionArguments.parseApp(req.arguments())))),
                r->InteractionReads.appointment(r,InteractionArguments.context(r.request()),InteractionArguments.appointment(InteractionArguments.parseApp(r.request().arguments()))),
                r->InteractionReads.appointment(r,InteractionArguments.context(r.request()),InteractionArguments.appointment(InteractionArguments.parseApp(r.request().arguments()))));
            pending=PendingInteractionContracts.pending(sources.pending());
            heirLegality=sourcePrivate("first-heir-legality",HeirMarriageCodec.STEP,"source_qualified_observed_first_heir_marriage_legality_v1",sources.heir(),req->empty(),
                r->{ JsonNode args=InteractionArguments.parseApp(r.request().arguments()); HeirSubject subject=new HeirSubject(new CharacterId(id(args,"first_heir_id")),positive64(args,"root_query_sequence"),InteractionArguments.ref(field(args,"root_evidence")));
                    return HeirMarriageCodec.decode(r.original().originalResultToken().orElseThrow(),InteractionArguments.context(r.request()),subject); });
            List<LawRoute> l=new ArrayList<>(); for(FullId title:plan.lawTitles()) {
                String step="query-title-own-laws-v1-"+title.value(); l.add(new LawRoute(title,advertised("laws:"+title.value(),step,"game.command.query-title-own-laws-v1-ID",sources.laws(),req->empty(),r->InteractionReads.titleOwnLaws(r,InteractionArguments.context(r.request()),title))));
            } laws=List.copyOf(l);
            List<ClaimsRoute> cs=new ArrayList<>(); for(List<Int32Id> titles:plan.claimTitleSets()) {
                var logicalKey = new org.xar.ck3.control.application.action.NativeStepDiscriminator.ClaimsIdentity(
                        titles.stream().map(Int32Id::value).toList()).operationKey().value();
                cs.add(new ClaimsRoute(titles,advertised("claims:"+logicalKey,logicalKey,"game.command.query-player-claims-v1-IDS",sources.claims(),req->empty(),r->InteractionReads.playerClaims(r,InteractionArguments.context(r.request()),titles))));
            } claims=List.copyOf(cs);
            List<HolderRoute> hs=new ArrayList<>(); for(Int32Id title:plan.holderTitles()) {
                String step="query-title-holder-v1-"+title.value(); hs.add(new HolderRoute(title,advertised("holder:"+title.value(),step,"game.command.query-title-holder-v1-N",sources.holder(),req->empty(),r->InteractionReads.titleHolder(r,InteractionArguments.context(r.request()),title))));
            } holders=List.copyOf(hs);
        }
        public ReadContract<OrdinaryContext> ordinaryQuery() { return ordinary; }
        public ReadContract<PendingContext> pendingQuery() { return pending; }
        /** This identical pre-Core contract accepts typed recipient/title selectors in its application arguments. */
        public ReadContract<GrantResult> grantQuery() { return grant; }
        public ReadContract<MarriageChoices> marriageChoices() { return marriage; }
        public ReadContract<HeirMarriageLegality> heirLegality() { return heirLegality; }
        public List<LawRoute> laws() { return laws; }
        public List<ClaimsRoute> claims() { return claims; }
        public List<HolderRoute> holders() { return holders; }
        public List<ReadContract<?>> contracts() {
            List<ReadContract<?>> out=new ArrayList<>(List.of(marriage,ordinary,control,grant,appointment,pending,heirLegality));
            for(LawRoute r:laws) out.add(r.contract()); for(ClaimsRoute r:claims) out.add(r.contract()); for(HolderRoute r:holders) out.add(r.contract()); return List.copyOf(out);
        }
        private static <T> ReadContract<T> advertised(String id,String step,String cap,ExactRef source,
                java.util.function.Function<PlanningReadRequest,org.xar.ck3.control.application.action.RawJson> fields,java.util.function.Function<org.xar.ck3.control.application.action.PlanningReadReceipt,T> decode) {
            return new ReadContract<>("interactions:"+id,new OperationKey(step),Optional.of(cap),cap,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(req,requestId)->new NativeRequest(org.xar.ck3.control.application.action.NativeStepDiscriminator.identity(new OperationKey(step)).nativeStep(),cap,fields.apply(req)),decode,decode);
        }
        private static <T> ReadContract<T> sourcePrivate(String id,String step,String permission,ExactRef source,
                java.util.function.Function<PlanningReadRequest,org.xar.ck3.control.application.action.RawJson> fields,java.util.function.Function<org.xar.ck3.control.application.action.PlanningReadReceipt,T> decode) {
            return new ReadContract<>("interactions:"+id,new OperationKey(step),Optional.empty(),permission,ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(req,requestId)->new NativeRequest(step,Optional.empty(),fields.apply(req)),decode,decode);
        }
    }
    /** Only this actual facade can mint a marriage original-failure source; no public DTO can. */
    static final class MarriageFailureSource {
        private final InteractionCapabilities owner;
        private MarriageFailureSource(InteractionCapabilities owner) { this.owner=owner; }
        void requireProducer(InteractionCapabilities identical) {
            need(owner==Objects.requireNonNull(identical),"marriage original failure crossed its actual producer");
        }
    }
    private final MarriageFailureSource marriageFailureSource=new MarriageFailureSource(this);
    private final Installation installed;
    private final PlanningReadPort reads;
    private final ActionCoordinatorPort actions;
    private PlanningReadResult.Known<MarriageChoices> latestMarriage;
    private PlanningReadResult.Known<ControlObservation> latestControl;
    public InteractionCapabilities(Installation installed,PlanningReadPort reads,ActionCoordinatorPort actions) {
        this.installed=Objects.requireNonNull(installed); this.reads=Objects.requireNonNull(reads); this.actions=Objects.requireNonNull(actions);
    }
    /** Root installs and reuses this one physical Game contract set by object identity. */
    public void requireInstallation(Installation actual) { need(installed==Objects.requireNonNull(actual),"interaction installation differs from the actual shared contracts"); }
    public ActionReceipt replyPendingCharacterInteraction(ActionContext action,boolean accept,Optional<PendingId> requested) {
        return actions.execute(prepareReplyPendingCharacterInteraction(action,accept,requested));
    }
    /** Builds the original reply command without submitting it; Root retains the one submit authority. */
    public ActionCommand prepareReplyPendingCharacterInteraction(ActionContext action,boolean accept,Optional<PendingId> requested) {
        PendingSummary pending=action.frame().controls().pending(); need(pending!=null && !pending.autoAcceptNotification(),"ordinary reply needs current ordinary pending instance");
        requested.ifPresent(id->need(id.equals(pending.instance()),"pending instance changed"));
        ObjectNode n=KnownPendingInteractionCommands.arguments(action,accept?KnownPendingInteractionRules.Action.ACCEPT:KnownPendingInteractionRules.Action.REJECT);
        return command(action,n,accept?"accept-pending-character-interaction":"reject-pending-character-interaction",null);
    }
    public ActionReceipt acknowledgePendingCharacterInteraction(ActionContext action,PendingId instance) {
        return actions.execute(prepareAcknowledgePendingCharacterInteraction(action,instance));
    }
    /** Builds the original exact-instance notification command without submitting it. */
    public ActionCommand prepareAcknowledgePendingCharacterInteraction(ActionContext action,PendingId instance) {
        PendingSummary pending=action.frame().controls().pending(); need(pending!=null && pending.instance().equals(instance) && pending.autoAcceptNotification(),"acknowledgement needs exact actual notification instance");
        ObjectNode n=KnownPendingInteractionCommands.arguments(action,KnownPendingInteractionRules.Action.ACKNOWLEDGE);
        return command(action,n,"acknowledge-pending-character-interaction",null);
    }
    public synchronized PlanningReadResult<MarriageChoices> queryArrangeMarriageChoices(Context c) {
        latestMarriage=null; PlanningReadResult<MarriageChoices> result=read(installed.marriage,c,InteractionArguments.body(c));
        if(result instanceof PlanningReadResult.Known<MarriageChoices> known) latestMarriage=known; return result;
    }
    public PlanningReadResult<HeirMarriageLegality> queryObservedFirstHeirMarriageLegalityV1(Context c) {
        return queryHeir(c,Optional.empty());
    }
    public PlanningReadResult<HeirMarriageLegality> queryObservedFirstHeirMarriageLegalityV1(Session borrowed,Context c) {
        return queryHeir(c,Optional.of(Objects.requireNonNull(borrowed)));
    }
    private PlanningReadResult<HeirMarriageLegality> queryHeir(Context c,Optional<Session> borrowed) {
        PlanningReadResult<HeirSubject> root=borrowed.isPresent()?installed.heirSubject.read(borrowed.orElseThrow(),c):installed.heirSubject.read(c);
        if(root instanceof PlanningReadResult.Unavailable<HeirSubject> unavailable) return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
        var known=(PlanningReadResult.Known<HeirSubject>)root;
        HeirSubject subject=borrowed.isPresent()?installed.heirSubject.requireSubject(borrowed.orElseThrow(),c,known)
                :installed.heirSubject.requireSubject(c,known);
        ObjectNode n=InteractionArguments.body(c).put("first_heir_id",subject.firstHeir().value()).put("root_query_sequence",subject.rootQuerySequence());
        InteractionArguments.ref(n.putObject("root_evidence"),subject.originalCampaignRoot());
        var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),installed.heirLegality.operation(),InteractionArguments.app(n),c.deadline());
        return borrowed.isPresent()?reads.read(borrowed.orElseThrow(),installed.heirLegality,request):reads.read(installed.heirLegality,request);
    }
    public synchronized ActionReceipt arrangeMarriage(ActionContext action,String choiceId) {
        try { return actions.execute(prepareArrangeMarriage(action.frame(),action.actionId(),action.claims(),choiceId)); }
        finally { latestMarriage=null; }
    }
    /** Consumes the exact latest native choices and builds their command for Root's sole submit authority. */
    public synchronized ActionCommand prepareArrangeMarriage(Context frame,String actionId,Claims originalClaims,String choiceId) {
        PlanningReadResult.Known<MarriageChoices> latest=latestMarriage; latestMarriage=null;
        if(latest==null) {
            if(originalMarriageChoice(choiceId))throw InteractionOriginalFailure.choiceMissing(marriageFailureSource,
                    frame,choiceId,InteractionOriginalFailure.CauseBranch.NO_RETAINED_QUERY,Optional.empty());
            throw new NullPointerException("latest actual marriage query required");
        }
        need(latest.receipt().request().before().equals(frame.before())
                && latest.receipt().request().source().equals(frame.source())
                && latest.receipt().request().sessionId().equals(frame.sessionId()),"marriage query source/session/frame changed");
        FamilyMarriageChoicesProjection.project(latest);
        Optional<MarriageChoice> selected=latest.value().choices().stream().filter(row->row.choiceId().equals(choiceId)).findFirst();
        if(selected.isEmpty()) {
            if(originalMarriageChoice(choiceId))throw InteractionOriginalFailure.choiceMissing(marriageFailureSource,
                    frame,choiceId,InteractionOriginalFailure.CauseBranch.CHOICE_ABSENT,Optional.of(latest.originalReceipt()));
            throw new IllegalArgumentException("choice absent from latest actual native query");
        }
        MarriageChoice choice=selected.orElseThrow();
        ObjectNode proof=F.objectNode().put("query_sequence",latest.value().frame().querySequence());
        InteractionArguments.ref(proof.putObject("original_query"),latest.originalReceipt());
        var intent=new RulerMarriageIntent(choice.choiceId(),choice.player(),choice.candidate(),Optional.of(InteractionArguments.app(proof)));
        var characters=new java.util.HashSet<>(originalClaims.characterIds());
        characters.add(BigInteger.valueOf(intent.actorId())); characters.add(BigInteger.valueOf(intent.candidateId()));
        var claims=new Claims(originalClaims.armyIds(),originalClaims.allyCharacterIds(),characters,originalClaims.commitmentKeys());
        try {
            // The same native preparer as the ordinary planner obtains fresh
            // choices, original terms and complete before-storage evidence.
            return new ActionCommand(actionId,frame.before(),frame.source(),frame.sessionId(),
                    new OperationKey(intent.step()),intent.toJson(),FamilyMarriageSendExpectation.expected(frame.before(),frame.source(),
                            intent.actorId(),intent.candidateId()),claims,frame.deadline());
        } finally { latestMarriage=null; }
    }
    private static boolean originalMarriageChoice(String choiceId) {
        return choiceId!=null&&choiceId.matches("[0-9]+-[0-9]+");
    }
    public synchronized void forgetMarriageChoices() { latestMarriage=null; }
    public PlanningReadResult<TitleOwnLaws> queryTitleOwnLawsV1(Context c,FullId title) {
        ReadContract<TitleOwnLaws> contract=installed.laws.stream().filter(r->r.title().equals(title)).findFirst().orElseThrow(()->new IllegalArgumentException("exact title law contract not installed by root")).contract(); return read(contract,c,InteractionArguments.body(c));
    }
    public PlanningReadResult<PlayerClaims> queryPlayerClaimsV1(Context c,List<Int32Id> titles) {
        List<Int32Id> exact=List.copyOf(titles); ReadContract<PlayerClaims> contract=installed.claims.stream().filter(r->r.titles().equals(exact)).findFirst().orElseThrow(()->new IllegalArgumentException("exact ordered claims contract not installed by root")).contract(); return read(contract,c,InteractionArguments.body(c));
    }
    public PlanningReadResult<TitleHolder> queryTitleHolderV1(Context c,Int32Id title) {
        ReadContract<TitleHolder> contract=installed.holders.stream().filter(r->r.title().equals(title)).findFirst().orElseThrow(()->new IllegalArgumentException("exact title holder contract not installed by root")).contract(); return read(contract,c,InteractionArguments.body(c));
    }
    public PlanningReadResult<Appointment> queryCurrentTitleAppointmentV1(Context c,AppointmentRequest request) {
        ObjectNode n=InteractionArguments.body(c); InteractionArguments.appointment(n,request); return read(installed.appointment,c,n);
    }
    public ActionReceipt setPlayerCharacterV1(ActionContext action,CharacterId target) {
        need(target.value()<=Integer.MAX_VALUE && action.frame().build()==Build.WANDERER6,"set-played-character original producer requires exact 1.19.0.6 and signed int32 target");
        ObjectNode n=InteractionArguments.body(action.frame()).put("mutation_kind","SET_PLAYER").put("target_id",target.value()); return execute(action,n,"set-played-character-v1-"+target.value(),null);
    }
    public PlanningReadResult<OrdinaryContext> queryCharacterInteractionOrdinaryV1(Context c,OrdinaryRequest request) {
        ObjectNode n=InteractionArguments.body(c); InteractionArguments.ordinary(n,request); return read(installed.ordinary,c,n);
    }
    public ActionReceipt initiateCharacterInteractionOrdinaryV1(ActionContext action,OrdinaryRequest request) {
        return actions.execute(prepareInitiateCharacterInteractionOrdinaryV1(action,request));
    }
    /** Preserves the original ordinary intent, expected observation and claims without submitting it. */
    public ActionCommand prepareInitiateCharacterInteractionOrdinaryV1(ActionContext action,OrdinaryRequest request) {
        var education=request.education().map(value -> new org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent.Education(
                value.child().orElseThrow().value(),value.guardian().orElseThrow().value(),value.options().orElseThrow().stream().map(InteractionKey::value).toList()));
        var intent=new org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent(request.interaction().value(),request.recipient().value(),education,Optional.empty());
        return new ActionCommand(action.actionId(),action.frame().before(),action.frame().source(),action.frame().sessionId(),
                new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP),intent.toJson(),action.expected(),action.claims(),action.frame().deadline());
    }
    public synchronized PlanningReadResult<ControlObservation> queryPlayerControlContextV1(Context c,ControlSource source) {
        latestControl=null; ObjectNode n=InteractionArguments.body(c); InteractionArguments.control(n,new ControlRequest(ControlAction.QUERY_CONTEXT,Optional.empty(),Optional.empty(),source));
        PlanningReadResult<ControlObservation> read=read(installed.control,c,n);
        if(read instanceof PlanningReadResult.Known<ControlObservation> known && known.value().status()==ControlStatus.CONTEXT_OBSERVED) latestControl=known; return read;
    }
    public synchronized ActionReceipt requestPlayerControlV1(ActionContext action,ControlRequest request) {
        PlanningReadResult.Known<ControlObservation> latest=Objects.requireNonNull(latestControl,"exact latest actual control query required");
        need(latest.receipt().request().before().equals(action.frame().before()) && latest.value().signature().equals(request.contextSignature().orElseThrow().value())
            && PlayerControlCodec.stageReady(latest.value(),request.action(),request.candidate().orElse(null)),"latest eligible actual backend flow/candidate required");
        latestControl=null; ObjectNode n=InteractionArguments.body(action.frame()).put("mutation_kind","PLAYER_CONTROL"); InteractionArguments.control(n,request); InteractionArguments.ref(n.putObject("preflight_read"),latest.originalReceipt());
        String identity=request.source().creationFiletime().decimal()+":"+request.source().inventorySha256().value()+":"+latest.value().flowId()+":"+request.action().wire();
        return execute(action,n,"player-control-v1","player-control-"+digest(identity).substring(0,32));
    }
    public GrantReply grantTitlePickerV1(Context c,GrantRequest request,Optional<ActionContext> action) {
        if(request.operation()==GrantOperation.QUERY) { ObjectNode n=InteractionArguments.body(c); InteractionArguments.grant(n,request); return new GrantRead(read(installed.grant,c,n)); }
        ActionContext a=action.orElseThrow(()->new IllegalArgumentException("grant mutation requires actual action context")); need(a.frame().equals(c),"grant action frame differs");
        return new GrantAction(actions.execute(prepareGrantTitlePickerV1(a,request)));
    }
    /** The original sole Grant command producer, exposed without dispatch so Root keeps its canonical once-claim. */
    public ActionCommand prepareGrantTitlePickerV1(ActionContext action,GrantRequest request) {
        Objects.requireNonNull(action);Objects.requireNonNull(request);need(request.operation()!=GrantOperation.QUERY,"grant query is not a mutation");
        ObjectNode n=InteractionArguments.body(action.frame()).put("mutation_kind","GRANT");InteractionArguments.grant(n,request);
        return command(action,n,GrantTitleCodec.step(request.operation()),null);
    }
    public PlanningReadResult<PendingContext> queryPendingCharacterInteractionContextV1(Context c,PendingId instance) {
        PendingSummary pending=c.controls().pending(); need(pending!=null && pending.instance().equals(instance),"pending query instance differs from native snapshot");
        return read(installed.pending,c,InteractionArguments.body(c).put("pending_id",instance.value()));
    }
    private <T> PlanningReadResult<T> read(ReadContract<T> contract,Context c,ObjectNode arguments) {
        return reads.read(contract,new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),InteractionArguments.app(arguments),c.deadline()));
    }
    private ActionReceipt execute(ActionContext a,ObjectNode args,String step,String durableId) {
        return actions.execute(command(a,args,step,durableId));
    }
    private static ActionCommand command(ActionContext a,ObjectNode args,String step,String durableId) {
        return new ActionCommand(durableId==null?a.actionId():durableId,a.frame().before(),a.frame().source(),a.frame().sessionId(),new OperationKey(step),InteractionArguments.app(args),a.expected(),a.claims(),a.frame().deadline());
    }
    private static String digest(String value) {
        try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
        catch(java.security.NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
}
