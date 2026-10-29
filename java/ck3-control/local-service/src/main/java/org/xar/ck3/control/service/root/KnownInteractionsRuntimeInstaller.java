package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.time.Instant;
import java.math.BigInteger;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** One real InteractionCapabilities instance shared by known pending, Family, guardian and public consumers. */
public final class KnownInteractionsRuntimeInstaller {
    public record Sources(InteractionCapabilities.Sources nativeDefinitions,InteractionCapabilities.ReadPlan readPlan,
            InteractionModels.Build qualifiedBuild,ExactRef readDecoder,ExactRef policy,ExactRef effects,
            ExactRef effectsDecoder) {
        public Sources {
            Objects.requireNonNull(nativeDefinitions);Objects.requireNonNull(readPlan);Objects.requireNonNull(qualifiedBuild);
            for(var ref:List.of(readDecoder,policy,effects,effectsDecoder))StrictJson.require(ref.bytes()>0,"actual selected interaction producer/consumer sources required");
        }
    }
    private final RootRuntimeContext context;
    private final PrisonersRuntimeInstaller actualPrisoners;
    private final RootTurnBundleReadSource actualTurnBundle;
    private final PrisonerPlanningPorts.TurnBundlePort turnBundle;
    private final Sources sources;
    private final RootInteractionContextProjection projection;
    private final RootFamilyCampaignRead campaign;
    private final RootFamilyHeirSource heir;
    private final InteractionCapabilities.Installation definitions;
    private final InteractionCapabilities capabilities;
    private final KnownPendingInteractionPolicy policy;
    private final KnownPendingInteractionEffects effects;
    private final RootDomainInstallation installation;
    private OrdinaryCorePolicy core;
    public KnownInteractionsRuntimeInstaller(RootRuntimeContext context,Sources sources,
            PrisonersRuntimeInstaller actualPrisoners) {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);
        this.actualPrisoners=Objects.requireNonNull(actualPrisoners);actualPrisoners.requireContext(context);
        actualTurnBundle=new RootTurnBundleReadSource(context);
        turnBundle=this::readCurrentTurnBundle;
        projection=new RootInteractionContextProjection(sources.qualifiedBuild());
        campaign=new RootFamilyCampaignRead(context);heir=new RootFamilyHeirSource(context,campaign);
        definitions=new InteractionCapabilities.Installation(sources.nativeDefinitions(),sources.readPlan(),heir);
        capabilities=new InteractionCapabilities(definitions,context.reads(),new CurrentActions(context));
        var snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader());
        effects=new KnownPendingInteractionEffects(snapshots,context.reads(),actualPrisoners.collectionContract());
        var prisoner=KnownPendingInteractionPolicy.prisonerRead(actualPrisoners.collectionContract());
        var root=published(context.finance().definitions().contract(FinanceReadContracts.Query.ROOT),
                request->FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY));
        var marriage=published(definitions.marriageChoices(),request->FamilyMarriageChoicesProjection.applicationArguments(current(request)));
        KnownPendingInteractionPolicy.ReadCatalog supplemental=operation->{
            if(operation.equals(prisoner.operation()))return Optional.of(prisoner);
            if(operation.equals(root.operation()))return Optional.of(root);
            if(operation.equals(marriage.operation()))return Optional.of(marriage);
            return Optional.empty();
        };
        policy=new KnownPendingInteractionPolicy(sources.policy(),this::current,context.finance().readPort(),definitions.pendingQuery(),supplemental,this::chooseSameCore);
        var actions=effects.bindings(sources.effects()).stream().map(binding->new RootExecutableBindings.ActionBinding(binding,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of("game.command."+binding.operation().value()),sources.effectsDecoder())).toList();
        installation=new RootDomainInstallation("shared-known-interactions",List.of(),
                definitions.contracts().stream().map(read->new RootReadContractCatalog.InstalledRead(read,sources.readDecoder())).toList(),
                List.of(),actions,List.of(),KnownPendingInteractionEffects.archivedVerifiers(sources.effects(),context.frameLoader()),
                List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),
                actions.stream().map(binding->new RootDomainInstallation.FixedDomain(binding,Domain.diplomacy)).toList(),List.of(),List.of());
    }
    public RootDomainInstallation installation() { requireLiveBinding();return installation; }
    public KnownPendingInteractionEffects actualEffects() { requireLiveBinding();return effects; }
    public Sources sources() { return sources; }
    /** Select only when the central registry installs the actual shared pending-effect mux. */
    public RootDomainInstallation readAndPolicyInstallation() {
        requireLiveBinding();
        return new RootDomainInstallation("shared-known-interactions-with-central-pending-mux",installation.domainRegistrations(),
                installation.reads(),installation.readFamilies(),List.of(),List.of(),List.of(),List.of(),List.of(),
                installation.frontendAdmissions(),installation.pending(),installation.requiredPending(),installation.policies(),
                installation.completions(),List.of(),List.of(),List.of());
    }
    public InteractionCapabilities.Installation definitions() { return definitions; }
    public InteractionCapabilities capabilities() { requireLiveBinding();return capabilities; }
    public RootInteractionContextProjection projection() { return projection; }
    public RootFamilyCampaignRead campaign() { return campaign; }
    public RootFamilyHeirSource heir() { return heir; }
    public KnownPendingInteractionPolicy policy() { requireLiveBinding();return policy; }
    void bindIncidents(RootIncidentRuntime actual) {
        Objects.requireNonNull(actual).requireContext(context);policy.bindIncidentCapture(actual.capturePort());
    }
    public List<WarCorePlanner.Leaf> leaves() { requireLiveBinding();return policy.leaves(sources.policy()); }
    /** Actual service aggregate, never a manufactured Native read contract. Reading it still requires live binding. */
    public PrisonerPlanningPorts.TurnBundlePort turnBundleFor(RootRuntimeContext actual) {
        requireContext(actual);return turnBundle;
    }
    /** Both the public aggregate and Prisoner service consume this identical concrete source instance. */
    public RootTurnBundleReadSource turnBundleSourceFor(RootRuntimeContext actual) {
        requireContext(actual);actualTurnBundle.requireOwner(actual);return actualTurnBundle;
    }
    private void requireLiveBinding() {
        actualPrisoners.requireContext(context);actualPrisoners.requireKnown(this);
    }
    private PrisonerPlanningPorts.TurnBundleRead readCurrentTurnBundle(PlanningRequest original)throws IOException {
        requireLiveBinding();Objects.requireNonNull(original);context.requireCurrent(original.deadline());
        var same=context.borrowedSession();context.writer().requireSession(same);
        return context.collector().currentPlanning(same,original,original.deadline(),(retained,lease)->{
            var actual=actualTurnBundle.read(same,retained,lease.frame());
            return new PrisonerPlanningPorts.ObservedTurnBundle(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),
                    actual.internalJson(),actual.original().receipt(),actual.original().originalReceipt());
        });
    }
    /** This link only resolves a composition cycle; no substitute core or scheduler is created. */
    public synchronized void bindCore(OrdinaryCorePolicy actual) {
        Objects.requireNonNull(actual);StrictJson.require(core==null && actual.implementationSource().bytes()>0,"actual same core binds once");
        core=actual;
    }
    private OrdinaryPolicy.Decision chooseSameCore(PlanningRequest actual,OrdinaryPolicy.Draft previous) {
        OrdinaryCorePolicy selected;synchronized(this){selected=core;}
        StrictJson.require(selected!=null,"actual shared ordinary core has not been installed");return selected.evaluate(actual,previous);
    }
    public InteractionModels.Context current(PlanningRequest original) {
        requireLiveBinding();
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);
            return context.collector().currentPlanning(same,original,original.deadline(),
                    (retained,lease)->projection.project(lease.frame(),retained.deadline()));
        } catch(IOException failure) {throw new UncheckedIOException("actual interaction full Driver/readiness projection unavailable",failure);}
    }
    /** Installation-time identity guard before a Root application session is bound. */
    public void requireContext(RootRuntimeContext actual) {
        StrictJson.require(context==Objects.requireNonNull(actual),"interactions belong to another original Root context");
    }
    public void requireOwner(RootApplicationSession actual) {
        requireLiveBinding();
        Objects.requireNonNull(actual);StrictJson.require(context.actions()==actual&&actual.writer()==context.writer()&&actual.archive()==context.archive()
                &&actual.identity().game().equals(context.game().generation())&&actual.identity().sessionId().equals(context.game().sessionId()),
                "public interactions require this same original Root runtime");
    }
    public sealed interface PublicPendingDecision permits NewPending,RetainedPending {
        InteractionModels.PendingSummary pending();KnownPendingInteractionRules.Action requested();
    }
    public record NewPending(ActionCommand command,InteractionModels.PendingSummary pending,KnownPendingInteractionRules.Action requested) implements PublicPendingDecision {
        public NewPending {Objects.requireNonNull(command);Objects.requireNonNull(pending);Objects.requireNonNull(requested);}
    }
    public record RetainedPending(ActionReceipt original,InteractionModels.PendingSummary pending,KnownPendingInteractionRules.Action requested) implements PublicPendingDecision {
        public RetainedPending {Objects.requireNonNull(original);Objects.requireNonNull(pending);Objects.requireNonNull(requested);StrictJson.require(!original.settled(),"only an unresolved original is retained without replay");}
    }
    /** Pure preparation inside Root's current physical lease. The existing Facade remains the sole command producer. */
    public PublicPendingDecision preparePublicPending(ContinuityStorePort.Session same,Complete frame,
            PendingInteractionPublicCodec.Request request,Instant deadline)throws IOException {
        requireLiveBinding();
        context.writer().requireSession(same);context.requireCurrent(deadline);Objects.requireNonNull(frame);Objects.requireNonNull(request);
        StrictJson.require(frame.identity().game().equals(context.game().generation())&&frame.source().equals(context.source())
                &&frame.sessionId().equals(context.game().sessionId()),"pending public preparation crossed physical Game/source/session");
        request.expectedRevision().optional().ifPresent(expected->StrictJson.require(expected.equals(frame.identity().frame().revision()),"pending public expected revision is stale"));
        InteractionModels.Context current=projection.project(frame,deadline);var pending=current.controls().pending();
        StrictJson.require(pending!=null,"CK3 has no actual pending character interaction");
        request.requestedInstance().ifPresent(instance->StrictJson.require(instance.equals(pending.instance()),"pending public instance differs from actual current instance"));
        StrictJson.require(pending.autoAcceptNotification()==(request.action()==KnownPendingInteractionRules.Action.ACKNOWLEDGE),"ordinary reply and auto-accept acknowledgement are distinct actual native channels");
        var archive=context.archive().withSession(same);
        Optional<ActionReceipt> retained=retainedPending(ContinuityActionJournal.receipts(same.head().state(),archive),current);
        if(retained.isPresent())return new RetainedPending(retained.orElseThrow(),pending,request.action());
        OperationKey operation=new OperationKey(request.action().step());
        StrictJson.require(context.bindings().actualActionBinding(operation).isPresent(),"the requested pending primitive is not installed in this runtime");
        String actionId=ActionIds.forDecision(current.sessionId(),current.before(),"public-pending:"+request.action().step()+":"+pending.instance().value());
        var characters=new java.util.HashSet<BigInteger>();characters.add(current.actor());characters.add(BigInteger.valueOf(pending.sender().value()));
        var action=new InteractionModels.ActionContext(current,actionId,KnownPendingInteractionCommands.expected(current,request.action()),
                new Claims(Set.of(),Set.of(),characters,Set.of("foreground-window")));
        ActionCommand prepared=request instanceof PendingInteractionPublicCodec.Reply reply
                ?capabilities.prepareReplyPendingCharacterInteraction(action,reply.accept(),reply.requestedInstance())
                :capabilities.prepareAcknowledgePendingCharacterInteraction(action,((PendingInteractionPublicCodec.Acknowledge)request).instance());
        context.writer().requireSession(same);return new NewPending(prepared,pending,request.action());
    }
    /** Pure selector over the actual canonical list; the caller retains all writer/source admission responsibility. */
    public static Optional<ActionReceipt> retainedPending(List<ActionReceipt> canonical,InteractionModels.Context current) {
        Objects.requireNonNull(canonical);Objects.requireNonNull(current);var pending=current.controls().pending();
        StrictJson.require(pending!=null,"actual pending summary required");
        Optional<ActionReceipt> retained=Optional.empty();
        for(ActionReceipt original:List.copyOf(canonical)) {
            if(original.settled()||!PendingInteractionPublicCodec.supports(original.command().operation()))continue;
            ActionCommand command=original.command();
            if(command.before().game().equals(current.before().game())&&command.source().equals(current.source())&&command.sessionId().equals(current.sessionId())
                    &&command.before().frame().identity().player().equals(current.actor())
                    &&PendingInteractionPublicCodec.originalInstance(command).equals(pending.instance())) {
                StrictJson.require(retained.isEmpty(),"multiple unresolved canonical actions claim the same pending instance");retained=Optional.of(original);
            }
        }
        return retained;
    }
    /** Canonical archived material and original replay, with no native dispatch, live observation or ACK inference. */
    public RawJson publicPendingResult(ContinuityStorePort.Session same,ActionReceipt actual,
            InteractionModels.PendingSummary pending,KnownPendingInteractionRules.Action requested)throws IOException {
        requireLiveBinding();
        context.writer().requireSession(same);var archive=context.archive().withSession(same);Objects.requireNonNull(actual);
        StrictJson.require(actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                &&actual.command().sessionId().equals(context.game().sessionId())&&PendingInteractionPublicCodec.originalInstance(actual.command()).equals(pending.instance()),
                "pending public result crossed its actual original runtime/instance");
        ExactRef reference=archive.receiptReferenceOf(actual);StrictJson.require(archive.loadReceipt(reference).equals(actual),"pending original canonical receipt changed");
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
        Optional<RawJson> material=Optional.empty();
        if(actual.applied().isPresent()) {
            var verifier=context.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow(()->new IllegalStateException("pending action original verifier is not installed"));
            verifier.verifier().verify(same.head(),actual,archive);material=Optional.of(NativeEffectEvidence.load(actual,archive,context.frameLoader()).compatibleResult());
        }
        return PendingInteractionPublicCodec.result(actual,archive,material,pending,requested);
    }
    private InteractionModels.Context publicContext(ContinuityStorePort.Session same,Complete frame,BigInteger expected,Instant deadline)throws IOException {
        requireLiveBinding();context.writer().requireSession(same);context.requireCurrent(deadline);Objects.requireNonNull(frame);
        context.collector().requireHeldFrame(same,frame);
        StrictJson.require(frame.identity().game().equals(context.game().generation())&&frame.source().equals(context.source())
                &&frame.sessionId().equals(context.game().sessionId()),"interaction public request crossed its actual physical source/session");
        StrictJson.require(frame.identity().frame().revision().equals(expected),"interaction public expected revision is stale");
        return projection.project(frame,deadline);
    }
    public InteractionDirectPublicCodec.Reply queryPublicPending(ContinuityStorePort.Session same,Complete frame,
            InteractionDirectPublicCodec.PendingQuery request,Instant deadline)throws IOException {
        var current=publicContext(same,frame,request.expectedRevision(),deadline);
        StrictJson.require(current.controls().paused(),"pending query requires an actual paused snapshot");
        StrictJson.require(current.controls().pending()!=null&&current.controls().pending().instance().equals(request.instance()),"pending query does not match the actual native instance");
        var contract=definitions.pendingQuery();StrictJson.require(context.readCatalog().containsIdentity(contract),"actual pending query producer is not installed");
        var result=capabilities.queryPendingCharacterInteractionContextV1(current,request.instance());
        if(result instanceof PlanningReadResult.Unavailable<PendingContext> unavailable)throw new IOException("actual pending context unavailable: "+unavailable.reason());
        var actual=(PlanningReadResult.Known<PendingContext>)result;NativeRecordedEvidenceVerifier.requireRead(actual.receipt(),context.archive().withSession(same));
        StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"pending context differs from its sole installed native decoder");
        return InteractionDirectPublicCodec.pending(actual,current,frame);
    }
    public InteractionDirectPublicCodec.Reply queryPublicOrdinary(ContinuityStorePort.Session same,Complete frame,
            InteractionDirectPublicCodec.Ordinary request,Instant deadline)throws IOException {
        var current=publicContext(same,frame,request.expectedRevision(),deadline);
        var contract=definitions.ordinaryQuery();StrictJson.require(context.readCatalog().containsIdentity(contract),"actual ordinary query producer is not installed");
        var result=capabilities.queryCharacterInteractionOrdinaryV1(current,request.nativeRequest());
        if(result instanceof PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext> unavailable)throw new IOException("actual ordinary context unavailable: "+unavailable.reason());
        var actual=(PlanningReadResult.Known<InteractionModels.OrdinaryContext>)result;NativeRecordedEvidenceVerifier.requireRead(actual.receipt(),context.archive().withSession(same));
        StrictJson.require(contract.replay(actual.receipt()).equals(actual.value()),"ordinary context differs from its sole installed native decoder");
        return InteractionDirectPublicCodec.ordinary(actual,current,request);
    }
    public sealed interface PublicOrdinaryDecision permits NewOrdinary,RetainedOrdinary { }
    public record NewOrdinary(ActionCommand command) implements PublicOrdinaryDecision { public NewOrdinary { Objects.requireNonNull(command); } }
    public record RetainedOrdinary(ActionReceipt original) implements PublicOrdinaryDecision { public RetainedOrdinary { Objects.requireNonNull(original);StrictJson.require(!original.settled(),"only original unresolved ordinary request is retained"); } }
    public PublicOrdinaryDecision preparePublicOrdinary(ContinuityStorePort.Session same,Complete frame,
            InteractionDirectPublicCodec.Ordinary request,Instant deadline)throws IOException {
        var current=publicContext(same,frame,request.expectedRevision(),deadline);
        // Same original source input/control validation. No economic/strategy selection is added to this public call.
        OrdinaryInteractionCodec.request(current,request.nativeRequest(),true);
        var archive=context.archive().withSession(same);
        Optional<ActionReceipt> old=retainedOrdinary(ContinuityActionJournal.receipts(same.head().state(),archive),current,request.nativeRequest());
        if(old.isPresent())return new RetainedOrdinary(old.orElseThrow());
        StrictJson.require(context.bindings().actualActionBinding(new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP)).isPresent(),"the actual ordinary native preparer is not installed");
        String id=ActionIds.forDecision(current.sessionId(),current.before(),"public-ordinary:"+request.interaction().value()+":"+request.recipient().value());
        var characters=new java.util.HashSet<BigInteger>();characters.add(current.actor());characters.add(BigInteger.valueOf(request.recipient().value()));
        var action=new InteractionModels.ActionContext(current,id,OrdinaryPendingPublication.requestExpectation(current),new Claims(Set.of(),Set.of(),characters,Set.of("foreground-window")));
        return new NewOrdinary(capabilities.prepareInitiateCharacterInteractionOrdinaryV1(action,request.nativeRequest()));
    }
    public static Optional<ActionReceipt> retainedOrdinary(List<ActionReceipt> canonical,InteractionModels.Context current,InteractionModels.OrdinaryRequest request) {
        Optional<ActionReceipt> retained=Optional.empty();
        for(ActionReceipt old:List.copyOf(canonical)){
            ActionCommand command=old.command();if(old.settled()||!command.operation().value().equals(OrdinaryInteractionCodec.INITIATE_STEP))continue;
            if(!command.before().game().equals(current.before().game())||!command.source().equals(current.source())||!command.sessionId().equals(current.sessionId())
                    ||!command.before().frame().identity().player().equals(current.actor()))continue;
            var intent=org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent.fromJson(command.arguments());
            if(intent.interactionKey().equals(request.interaction().value())&&intent.recipientId()==request.recipient().value()){
                StrictJson.require(retained.isEmpty(),"multiple unresolved canonical ordinary requests share the actual intent");retained=Optional.of(old);
            }
        }
        return retained;
    }
    public InteractionDirectPublicCodec.Reply publicOrdinaryResult(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException {
        requireLiveBinding();context.writer().requireSession(same);var archive=context.archive().withSession(same);
        StrictJson.require(actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                &&actual.command().sessionId().equals(context.game().sessionId()),"ordinary public result crossed its original runtime");
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
        var value=OrdinaryPendingPublication.load(actual,archive,context.frameLoader(),sources.qualifiedBuild());
        return value.isPresent()?InteractionDirectPublicCodec.initiation(actual,archive,value.orElseThrow().value()):InteractionDirectPublicCodec.unknown(actual,archive);
    }
    private static <T> KnownPendingInteractionPolicy.ReadRoute<T> published(ReadContract<T> actual,
            KnownPendingInteractionPolicy.ReadArguments arguments) {
        return new KnownPendingInteractionPolicy.ReadRoute<>(actual,arguments,
                known->new KnownPendingInteractionPolicy.ReadPublication(InteractionReadPublications.publish(known.receipt()),Optional.empty()));
    }
    private static final class CurrentActions implements ActionCoordinatorPort {
        private final RootRuntimeContext context;
        private CurrentActions(RootRuntimeContext actual) {context=actual;}
        @Override public ActionReceipt execute(ActionCommand command) {return context.actions().execute(command);}
        @Override public ActionReceipt execute(ContinuityStorePort.Session same,ActionCommand command) {return context.actions().execute(same,command);}
        @Override public ActionReceipt reconcile(String id) {return context.actions().reconcile(id);}
        @Override public ActionReceipt reconcile(ContinuityStorePort.Session same,String id) {return context.actions().reconcile(same,id);}
    }
}


