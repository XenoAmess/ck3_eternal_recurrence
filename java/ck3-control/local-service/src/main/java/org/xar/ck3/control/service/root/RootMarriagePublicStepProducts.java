package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageChoicesProjection;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionOriginalFailure;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.MarriageChoices;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Context;
import org.xar.ck3.control.service.mcp.MarriageArrangePublicCodec;
import org.xar.ck3.control.service.mcp.MarriageChoicesPublicCodec;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Original generic marriage steps. The existing Family owner prepares; the actual Root alone submits. */
public final class RootMarriagePublicStepProducts {
    public static final String QUERY = "query-arrange-marriage-choices";
    private static final String PREFIX = "arrange-marriage-";
    private static final Pattern CHOICE = Pattern.compile("[0-9]+-[0-9]+");
    private static final BigInteger MAX_SAFE = BigInteger.valueOf(9_007_199_254_740_991L);
    private static final BigInteger MAX_U64 = new BigInteger("18446744073709551615");
    private RootMarriagePublicStepProducts() { }

    /** Pure original parser only. A matching string supplies no native availability or permission. */
    public static Optional<String> choiceId(OperationKey step) {
        String value=Objects.requireNonNull(step).value();
        if(!value.startsWith(PREFIX))return Optional.empty();
        String choice=value.substring(PREFIX.length());
        return CHOICE.matcher(choice).matches()?Optional.of(choice):Optional.empty();
    }
    public static boolean query(OperationKey step) {return QUERY.equals(Objects.requireNonNull(step).value());}
    public static boolean marriage(OperationKey step) {return query(step)||choiceId(step).isPresent();}

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);var context=actual.context();var family=actual.remainingDomains().family().nativeReads();
        family.requireContext(context);
        family.requireInteractions(actual.interactions().capabilities(),actual.interactions().definitions());
        var sources=new LinkedHashSet<ExactRef>();
        for(Class<?> type:List.of(RootMarriagePublicStepProducts.class,RootFamilySendRecordingMaterial.class,
                RootMarriageArrangePublicProducts.class,RootFamilyNativeReadProducts.class,RootFamilyRuntimeFactory.class,
                RootApplicationSession.class,RootFrontendRuntime.class,RootPublicStepFailureOriginals.class,PublicServiceFailure.class,MarriageArrangePublicCodec.class,MarriageChoicesPublicCodec.class,
                PublicPlanningCodec.class))sources.add(actual.publicStepSource(Module.LOCAL_SERVICE,type));
        for(Class<?> type:List.of(InteractionCapabilities.class,InteractionOriginalFailure.class,FamilyMarriageChoicesProjection.class))
            sources.add(actual.publicStepSource(Module.NATIVE_TRANSPORT,type));
        for(Class<?> type:List.of(RulerMarriageIntent.class,ContinuityActionJournal.class,NativeRecordedEvidenceVerifier.class))
            sources.add(actual.publicStepSource(Module.APPLICATION,type));
        ExactRef nativeDriver=actual.definitions().frontend().originalNativeDriver();
        sources.add(nativeDriver);
        List<ExactRef> closure=List.copyOf(sources);
        RootPublicStepExecution.OwnerGuard owner=identical->{
            StrictJson.require(identical==context&&actual.context()==context,"marriage public steps crossed the installed physical Root");
            if(!(identical.actions() instanceof RootApplicationSession dispatcher))throw new IOException("actual marriage Root dispatcher unavailable");
            family.requireContext(identical);family.requireOwner(dispatcher);
            family.requireInteractions(actual.interactions().capabilities(),actual.interactions().definitions());
        };
        var read=new RootPublicStepExecution.Read("original-marriage-choices",RootMarriagePublicStepProducts::query,owner,
                (original,frame,known,same,caller,archive)->{
                    caller.requireCurrent(original);
                    var result=family.publicRulerChoices(same,frame,original.deadline());
                    if(!(result instanceof PlanningReadResult.Known<MarriageChoices> complete))
                        throw new IOException("actual native marriage choices are unavailable");
                    NativeRecordedEvidenceVerifier.requireRead(complete.receipt(),archive);
                    StrictJson.require(archive.readReferenceOf(complete.receipt()).equals(complete.originalReceipt()),
                            "original marriage query reference is not this retained native read");
                    return queryResult(complete);
                },closure);
        var action=new RootPublicStepExecution.OwnedAction("original-arrange-marriage",step->choiceId(step).isPresent(),owner,
                (root,catalog,caller,deadline)->{
                    StrictJson.require(catalog==actual&&root==context.actions(),"marriage action crossed its actual installed dispatcher");
                    var request=request(caller);var cleanup=new AtomicReference<InteractionCapabilities>();
                    var prepared=new AtomicReference<ActionCommand>();
                    return root.executePublicDecision(deadline,(frame,driver,same)->{
                        owner.requireContext(context);request.revision().requireCurrent(frame.identity().frame().revision());
                        var archive=context.archive().withSession(same);
                        var interactions=actual.interactions();cleanup.set(interactions.capabilities());
                        try(var originalDriver=RootPublicStepFailureOriginals.beginDriver(frame,driver,same,caller)) {
                            try {
                                var controls=interactions.projection().project(frame,deadline);
                                var decision=decide(request,ContinuityActionJournal.receipts(same.head().state(),archive),controls,
                                        interactions.capabilities(),archive::receiptReferenceOf);
                                if(decision instanceof RootApplicationSession.SubmitPublicAction<RawJson> submit) {
                                    RootPublicStepFailureOriginals.trackPreparedAction(submit.command());
                                    prepared.set(submit.command());
                                }
                                return decision;
                            }catch(PublicServiceFailure failure) {
                                throw RootPublicStepFailureOriginals.recordDriverFailure(frame,driver,same,caller,failure,Optional.empty(),Optional.empty());
                            }
                        }
                    },(receipt,archive,same)->{
                        RootFamilySendRecordingMaterial.Publication publication;
                        try {
                            requireCompletedResult(receipt,archive.receiptReferenceOf(receipt));
                            var installed=actual.bindings().actualArchivedVerifier(receipt.command().operation())
                                    .orElseThrow(()->new IOException("actual installed marriage archived verifier unavailable"));
                            publication=RootFamilySendRecordingMaterial.captureOrdinary(context,actual,same,receipt,archive,installed,nativeDriver,closure,true);
                        }catch(PublicServiceFailure failure) {
                            // Retained UNKNOWN has no new strong command and keeps its original canonical history.
                            if(prepared.get()==null)throw failure;
                            throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,failure,Optional.empty(),Optional.empty());
                        }
                        // Public numeric formatting is Service work after a successful Driver result; it cannot add a failed Driver row.
                        return publicResult(publication.result());
                    },()->{var facade=cleanup.get();if(facade!=null)facade.forgetMarriageChoices();});
                },closure);
        return List.of(read,action);
    }

    /** Pure command/retained-identity choice used by the actual held Root callback; it never executes a command. */
    static RootApplicationSession.PublicActionDecision<RawJson> decide(MarriageArrangePublicCodec.Request request,
            List<ActionReceipt> originals,Context controls,InteractionCapabilities same,Function<ActionReceipt,ExactRef> originalReference) {
        var pending=RootMarriageArrangePublicProducts.originalUnresolved(request,originals,controls.before(),controls.source(),controls.sessionId());
        if(pending.isPresent()) {
            var retained=pending.orElseThrow();
            return new RootApplicationSession.ReconcilePublicAction<>(retained.command().actionId(),originalReference.apply(retained));
        }
        var command=RootMarriageArrangePublicProducts.prepareOriginal(same,controls,"public-step-marriage-"+UUID.randomUUID(),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.choiceId());
        StrictJson.require(command.operation().value().equals(request.step()),"actual marriage owner changed the original public step");
        return new RootApplicationSession.SubmitPublicAction<>(command);
    }

    /** Missing complete original result keeps the original canonical receipt; it is never a retry instruction. */
    public static final class ResultUnavailable extends IOException {
        private final ActionReceipt receipt;private final ExactRef originalReceipt;
        private ResultUnavailable(ActionReceipt receipt,ExactRef originalReceipt) {
            super("original marriage result unavailable for retained "+receipt.outcome()+"; reconcile original action, never resubmit");
            this.receipt=Objects.requireNonNull(receipt);this.originalReceipt=Objects.requireNonNull(originalReceipt);
        }
        public ActionReceipt receipt(){return receipt;}
        public ExactRef originalReceipt(){return originalReceipt;}
    }

    static void requireCompletedResult(ActionReceipt receipt,ExactRef original)throws ResultUnavailable {
        if(!RootFamilySendRecordingMaterial.supports(receipt))throw new ResultUnavailable(receipt,original);
    }

    static MarriageArrangePublicCodec.Request request(PublicPlanningCodec.ExecuteRequest caller) {
        String choice=choiceId(caller.step()).orElseThrow(()->new IllegalArgumentException("original arrange-marriage step required"));
        MarriageChoicesPublicCodec.ExpectedRevision revision;
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)
            revision=new MarriageChoicesPublicCodec.ProvidedRevision(value.value());
        else if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionNull)
            revision=new MarriageChoicesPublicCodec.NullRevision();
        else revision=new MarriageChoicesPublicCodec.MissingRevision();
        return new MarriageArrangePublicCodec.Request(choice,new MarriageChoicesPublicCodec.Request(revision));
    }

    /** Full original primitive result spread, with the original normalized choices and backend marker. */
    static RawJson queryResult(PlanningReadResult.Known<MarriageChoices> actual) {
        FamilyMarriageChoicesProjection.project(actual);
        ObjectNode result=object(actual.receipt().original().originalResultToken().orElseThrow()).deepCopy();
        var choices=result.putArray("arrange_marriage_choices");
        for(var choice:actual.value().choices())choices.addObject().put("choice_id",choice.choiceId())
                .put("played_character_id",choice.player()).put("candidate_character_id",choice.candidate()).put("source","native");
        result.put("backend_id","native-headless");return publicResult(raw(result));
    }

    /** Field-role conversion only. Unknown wide numbers fail; the original numeric archive is never rewritten. */
    static RawJson publicResult(RawJson original) {
        ObjectNode result=object(original).deepCopy();
        for(String key:List.of("query_sequence","revision","native_revision","queried_revision","queried_native_revision")) {
            JsonNode value=result.get(key);if(value==null)continue;
            StrictJson.require(value.isIntegralNumber()&&value.bigIntegerValue().signum()>=0&&value.bigIntegerValue().compareTo(MAX_U64)<=0,
                    "original marriage public uint64 field changed type or range: "+key);
            result.put(key,value.bigIntegerValue().toString());
        }
        safeNumbers(result);return raw(result);
    }
    private static void safeNumbers(JsonNode value) {
        if(value.isIntegralNumber())StrictJson.require(value.bigIntegerValue().abs().compareTo(MAX_SAFE)<=0,
                "unknown wide marriage result integer has no declared public role");
        else if(value.isFloatingPointNumber())StrictJson.require(Double.isFinite(value.doubleValue()),"nonfinite original marriage result number");
        if(value.isContainerNode())for(JsonNode child:value)safeNumbers(child);
    }
    private static ObjectNode object(RawJson raw) {
        JsonNode value=StrictJson.parse(raw.bytes());StrictJson.require(value instanceof ObjectNode,"complete original marriage result object required");
        return (ObjectNode)value;
    }
    private static RawJson raw(ObjectNode value){return new RawJson(DriverJson.encodeNode(value));}
}
