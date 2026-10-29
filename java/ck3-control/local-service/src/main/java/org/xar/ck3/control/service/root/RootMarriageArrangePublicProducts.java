package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.MarriageArrangePublicCodec;
import org.xar.ck3.control.service.mcp.MarriageChoicesPublicCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Context;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Contribution;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** The original ARRANGE Service route. Only the actual Root dispatcher can submit its prepared primitive. */
public final class RootMarriageArrangePublicProducts {
    static final PublicMethod METHOD=PublicMethod.ARRANGE_MARRIAGE;
    @FunctionalInterface interface Current {MarriageArrangePublicCodec.Reply arrange(MarriageArrangePublicCodec.Request request)throws InterruptedException;}
    private final Current current;
    private RootMarriageArrangePublicProducts(Current current){this.current=Objects.requireNonNull(current);}
    public MarriageArrangePublicCodec.Reply arrangeMarriage(MarriageArrangePublicCodec.Request request)throws InterruptedException {
        return current.arrange(Objects.requireNonNull(request));
    }
    public static Contribution install(Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        try {
            ExactRef implementation=context.source(RootMarriageArrangePublicProducts.class);
            for(Class<?> type:List.of(MarriageArrangePublicCodec.class,MarriageChoicesPublicCodec.class,PublicServiceFailure.class,RootFamilyRuntimeFactory.class,
                    RootFamilyNativeReadProducts.class,RootApplicationSession.class,KnownInteractionsRuntimeInstaller.class,RootFamilyMarriageFreshPreparation.class,
                    RootFamilyMarriageSendRuntime.class,RootFamilyFreshRootAdmission.class))context.source(type);
            for(Class<?> type:List.of(InteractionCapabilities.class,InteractionOriginalFailure.class,FamilyMarriageChoicesProjection.class,FamilyMarriageNativeRequests.class))context.source(Module.NATIVE_TRANSPORT,type);
            for(Class<?> type:List.of(RulerMarriageIntent.class,ActionReceipt.class,ContinuityActionJournal.class))context.source(Module.APPLICATION,type);
            register(registry,implementation,new ActualCurrent(context));
            return new Contribution(List.of(),List.of(),List.of());
        }catch(IOException missing){return new Contribution(List.of(),List.of(),List.of(new RootRuntimePublicCatalog.DefinitionGap(METHOD.pythonName(),
                "actual public ARRANGE source/typed preparation/independent send result closure unavailable: "+missing.getMessage())));}
    }
    static void register(PublicBindings registry,ExactRef implementation,Current current) {
        StrictJson.require(registry.lookup(METHOD).isEmpty(),"public ARRANGE already has a producer");
        var actual=new RootMarriageArrangePublicProducts(current);
        registry.register(METHOD,MarriageArrangePublicCodec.Request.class,MarriageArrangePublicCodec.Reply.class,actual::arrangeMarriage,
                MarriageArrangePublicCodec::decode,MarriageArrangePublicCodec::encode,
                new PublicRoutes.Target(RootMarriageArrangePublicProducts.class.getName(),"arrangeMarriage",implementation),PublicRoutes.Status.IMPLEMENTED,
                "same actual Root/Family interaction facade; exact latest native choice and public revision; sole dispatcher submits or reconciles its original UNKNOWN; independent send confirmation grants no relationship or day credit");
    }
    /** Sole LS adapter for the actual native owner's finite original fault. No guard/message inference is allowed. */
    static ActionCommand prepareOriginal(InteractionCapabilities producer,InteractionModels.Context controls,String actionId,
            Claims claims,String choiceId) {
        try {return producer.prepareArrangeMarriage(controls,actionId,claims,choiceId);}
        catch(InteractionOriginalFailure original) {throw originalFailure(original,producer,controls,choiceId);}
    }
    static PublicServiceFailure originalFailure(InteractionOriginalFailure actual,InteractionCapabilities producer,
            InteractionModels.Context controls,String choiceId) {
        Objects.requireNonNull(actual).requireProducer(producer,controls,choiceId);
        var kind=switch(actual.kind()) {case MARRIAGE_CHOICE_NOT_IN_LATEST_QUERY->PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE;};
        StrictJson.require(kind.pythonClassName().equals(actual.originalErrorClass()),"actual original marriage fault class changed");
        // originalQuery is only READ provenance, never a persisted failure candidate or a submission permit.
        var mapped=new PublicServiceFailure(kind,actual.originalMessage(),Optional.empty());mapped.initCause(actual);return mapped;
    }
    /** Pure selection of an existing original, never a new identity or permission to dispatch. */
    static Optional<ActionReceipt> originalUnresolved(MarriageArrangePublicCodec.Request request,List<ActionReceipt> receipts,
            ObservationIdentity current,G2Source source,String sessionId) {
        var open=receipts.stream().filter(receipt->!receipt.settled()).toList();
        if(open.isEmpty())return Optional.empty();
        StrictJson.require(open.size()==1,"another unresolved canonical action isolates the sole public submit authority");
        var original=open.getFirst();var command=original.command();
        StrictJson.require(command.operation().value().equals(request.step())&&command.source().equals(source)&&command.sessionId().equals(sessionId)
                &&command.before().machineId().equals(current.machineId())&&command.before().game().equals(current.game())
                &&command.before().frame().episodeRunId().equals(current.frame().episodeRunId()),"unresolved canonical action belongs to another public choice, source, Game or episode");
        var intent=RulerMarriageIntent.fromJson(command.arguments());
        StrictJson.require(intent.choiceId().equals(request.choiceId())&&current.frame().identity().player().longValueExact()==intent.actorId(),
                "unresolved public marriage original belongs to another current player or pair");
        return Optional.of(original);
    }
    private static final class ActualCurrent implements Current {
        private final Context context;
        private ActualCurrent(Context context){this.context=Objects.requireNonNull(context);}
        @Override public MarriageArrangePublicCodec.Reply arrange(MarriageArrangePublicCodec.Request request)throws InterruptedException {
            var deadline=context.clock().instant().plus(context.actionTimeout());var reconciled=new AtomicBoolean();
            var cleanupFacade=new AtomicReference<InteractionCapabilities>();
            try{return context.withCurrent(root->root.executePublicDecision(deadline,(frame,driver,same)->{
                var installed=context.installed(root);var runtime=installed.context();runtime.writer().requireSession(same);
                var family=installed.remainingDomains().family().nativeReads();family.requireOwner(root);
                var actual=installed.interactions();family.requireInteractions(actual.capabilities(),actual.definitions());
                request.revision().requireCurrent(frame.identity().frame().revision());
                var archive=runtime.archive().withSession(same);
                var original=originalUnresolved(request,ContinuityActionJournal.receipts(same.head().state(),archive),frame.identity(),frame.source(),frame.sessionId());
                // Preparation and the true fresh-read phase use this same facade. Its fresh query
                // may repopulate the retained DATA; Root clears it before releasing this call lock.
                cleanupFacade.set(actual.capabilities());
                if(original.isPresent()) {
                    var receipt=original.orElseThrow();reconciled.set(true);
                    return new RootApplicationSession.ReconcilePublicAction<MarriageArrangePublicCodec.Reply>(receipt.command().actionId(),archive.receiptReferenceOf(receipt));
                }
                var controls=actual.projection().project(frame,deadline);
                // Direct public intent has no ordinary planner history/goal or extra policy. The sole
                // native producer adds the genuine actor/candidate claims from its retained exact query.
                var claims=new Claims(Set.of(),Set.of(),Set.of(),Set.of());
                var command=prepareOriginal(actual.capabilities(),controls,"public-marriage-"+UUID.randomUUID(),claims,request.choiceId());
                return new RootApplicationSession.SubmitPublicAction<MarriageArrangePublicCodec.Reply>(command);
            },(receipt,archive,same)->new MarriageArrangePublicCodec.Reply(receipt,reconciled.get()),()->{
                var actual=cleanupFacade.get();if(actual!=null)actual.forgetMarriageChoices();
            }));
            }catch(IOException missing){throw new UncheckedIOException("actual public ARRANGE unavailable",missing);}
        }
    }
}
