package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** One observation-only profile of the actual ordinary native producer for a canonical original guardian send. */
public final class GuardianReconciliationQueries {
    public static final String CONTRACT_ID="interactions:ordinary-query:reconciliation/v1";
    public interface CanonicalAdmission {
        void verifyCurrent(PlanningReadRequest request);
        void verifyOriginal(PlanningReadReceipt receipt);
    }
    public record Issued<R>(ReadContract<R> contract,PlanningReadRequest request) {
        public Issued {
            Objects.requireNonNull(contract);Objects.requireNonNull(request);
            need(contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    &&request.origin() instanceof CommandOrigin.Reconciliation&&contract.operation().equals(request.operation()),
                    "reconciliation descriptor changed its explicit read mode/operation");
        }
    }
    private final RootInteractionContextProjection projection;
    private final ReadContract<OrdinaryContext> ordinary;
    private final ReadContract<OrdinaryContext> contract;
    /** The profile witness is this exact selected Java factory; sourceRef remains the actual ordinary native producer. */
    public GuardianReconciliationQueries(ReadContract<OrdinaryContext> actualOrdinaryQuery,Build actualQualifiedBuild,
            ExactRef actualProfileSource,CanonicalAdmission actualAdmission) {
        ordinary=Objects.requireNonNull(actualOrdinaryQuery);Objects.requireNonNull(actualProfileSource);
        Objects.requireNonNull(actualAdmission);need(actualQualifiedBuild==Build.CROZIER4,"guardian storage requires actual source-qualified current4");
        need(ordinary.contractId().equals("interactions:ordinary-query")
                &&ordinary.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&ordinary.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP)
                &&ordinary.requiredCapability().equals(Optional.of(OrdinaryInteractionCodec.QUERY_CAPABILITY))
                &&ordinary.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&ordinary.permissionKey().equals(OrdinaryInteractionCodec.QUERY_CAPABILITY)
                &&ordinary.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,
                "the identical installed original ordinary native query is required");
        projection=new RootInteractionContextProjection(actualQualifiedBuild);
        java.util.function.Function<PlanningReadReceipt,OrdinaryContext> decode=receipt->withProfile(actualProfileSource,()->{
            requireOriginalPacket(receipt);actualAdmission.verifyOriginal(receipt);
            var context=InteractionArguments.context(receipt.request());
            var intent=typedArguments(receipt.request());
            return OrdinaryInteractionCodec.query(receipt.original().originalResultToken().orElseThrow(),context,intent);
        });
        contract=new ReadContract<>(CONTRACT_ID,ordinary.operation(),ordinary.requiredCapability(),ordinary.permissionKey(),
                ordinary.permissionMode(),ordinary.wireProfile(),ReadContract.GuardMode.RECONCILIATION_OBSERVATION,ordinary.sourceRef(),
                (request,id)->withProfile(actualProfileSource,()->{
                    OrdinaryRequest intent=typedArguments(request);actualAdmission.verifyCurrent(request);
                    return new NativeRequest(ordinary.operation().value(),ordinary.requiredCapability(),
                            OrdinaryInteractionCodec.request(InteractionArguments.context(request),intent,false));
                }),decode,decode);
    }
    public ReadContract<OrdinaryContext> contract(){return contract;}
    public void requireOrdinary(ReadContract<OrdinaryContext> actual){need(ordinary==actual,"guardian profile borrowed another ordinary query object");}
    public void requireFrame(PlanningReadRequest request,Complete actual) {
        need(actual.identity().equals(request.reconciliationBefore())&&actual.source().equals(request.source())
                &&actual.sessionId().equals(request.sessionId())
                &&projection.project(actual,request.deadline()).equals(InteractionArguments.context(request)),
                "guardian query controls are not the actual complete Root native/Driver projection");
    }
    /** Pure closed binding reused by Root readiness; it does not qualify a current or archived writer state. */
    public static void requireOriginalRequest(PlanningReadRequest request,ActionCommand original,ActionState.Attempt attempt) {
        Objects.requireNonNull(request);Objects.requireNonNull(original);Objects.requireNonNull(attempt);
        need(GuardianOutgoingEffects.accepts(original),"only the exact canonical education send can issue this query");
        var identity=request.origin().requireReconciliation();var pending=identity.pending();
        need(pending.actionId().equals(original.actionId())&&pending.bodySha256().equals(ActionCodec.bodySha256(original))
                &&pending.requestId().equals(attempt.requestId())&&pending.originalBefore().equals(original.before())
                &&request.source().equals(original.source())&&request.sessionId().equals(original.sessionId())
                &&original.source().equals(identity.source())&&original.sessionId().equals(identity.sessionId())
                &&attempt.guard().connectionGeneration().equals(identity.connectionGeneration()),
                "guardian query changed its canonical original action/body/request/source/session/connection");
        var actual=InteractionArguments.context(request);var intent=typedArguments(request);
        need(intent.equals(GuardianOutgoingEffects.nativeIntent(OrdinaryInitiationIntent.fromJson(original.arguments())))
                &&actual.before().equals(identity.factual())&&actual.connectionGeneration().equals(identity.connectionGeneration()),
                "guardian query changed the original education pair/options or factual native frame");
        var before=original.before().frame();var current=identity.factual().frame();
        need(current.episodeRunId().equals(before.episodeRunId())&&current.identity().player().equals(before.identity().player())
                &&current.identity().dateRaw().equals(before.identity().dateRaw())
                &&current.identity().nativeRevision().compareTo(before.identity().nativeRevision())>=0
                &&current.revision().compareTo(before.revision())>=0,"guardian storage query crossed player/episode/day or regressed the original frame");
    }
    private static OrdinaryRequest typedArguments(PlanningReadRequest request) {
        need(request.origin() instanceof CommandOrigin.Reconciliation&&request.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP),
                "guardian query requires its own explicit canonical reconciliation operation");
        var body=InteractionArguments.parseApp(request.arguments());
        closed(body,"group_context","interaction_key","recipient_id","education");
        var context=InteractionArguments.context(request);var intent=InteractionArguments.ordinary(body);
        need(context.build()==Build.CROZIER4&&context.controls().paused()&&context.controls().mapReady()&&context.controls().alive()
                &&intent.interaction().value().equals("educate_child_interaction")&&intent.education().isPresent(),
                "guardian query cannot borrow another ordinary interaction or unavailable played frame");
        var education=intent.education().orElseThrow();
        need(education.child().isPresent()&&education.guardian().isPresent()&&education.options().isPresent(),
                "guardian query requires the complete original materialized child/guardian/options");
        return intent;
    }
    public Issued<OrdinaryContext> issue(ReconciliationIdentity identity,ActionCommand original,ActionState.Attempt attempt,
            Complete actual,Instant deadline) {
        Objects.requireNonNull(identity);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        need(actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())&&actual.sessionId().equals(identity.sessionId())
                &&actual.connectionGeneration().equals(identity.connectionGeneration())&&actual.originalEvidence().equals(identity.nativeEvidence())
                &&NativeEffectEvidence.basis(actual).driverFacts().equals(identity.evidence().observationManifest()),
                "guardian descriptor does not use the actual Root reconciliation full frame");
        var context=projection.project(actual,deadline);var args=InteractionArguments.body(context);
        InteractionArguments.ordinary(args,GuardianOutgoingEffects.nativeIntent(OrdinaryInitiationIntent.fromJson(original.arguments())));
        var request=PlanningReadRequest.newReconciliation(identity,contract.operation(),InteractionArguments.app(args),deadline);
        requireOriginalRequest(request,original,attempt);return new Issued<>(contract,request);
    }
    private static void requireOriginalPacket(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);need(receipt.contractId().equals(CONTRACT_ID)&&receipt.original().nativeOk(),
                "guardian storage requires its exact registered successful independent read");
        var request=receipt.request();var identity=request.origin().requireReconciliation();var context=InteractionArguments.context(request);
        var intent=typedArguments(request);
        for(var guard:List.of(receipt.before(),receipt.after())) {
            var binding=guard.binding();
            need(guard.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    &&binding.origin() instanceof CommandOrigin.Reconciliation&&identity.sameGuardFrame(binding.origin().requireReconciliation())
                    &&binding.operation().equals(request.operation())&&binding.source().equals(request.source())&&binding.sessionId().equals(request.sessionId())
                    &&binding.connectionGeneration().equals(identity.connectionGeneration())&&binding.nativeEvidence().equals(identity.nativeEvidence())
                    &&binding.capabilityEvidence().equals(identity.capabilityEvidence())&&binding.supportingEvidence().size()==1
                    &&guard.originalBindingSha256().equals(identity.bindingSha256()),"guardian original read lost its canonical factual frame/custody binding");
        }
        receipt.original().custody().orElseThrow(()->new IllegalArgumentException("guardian query has no original held-wire custody")).verify(receipt);
        try {
            var incoming=NativeWire.decode(receipt.original().originalPacket());
            need(incoming instanceof NativeWire.CommandResult,"guardian query response has another packet kind");
            var result=(NativeWire.CommandResult)incoming;
            need(result.nativeOk()&&result.requestId().equals(receipt.requestId())
                    &&java.util.Arrays.equals(result.payload().value(),receipt.original().originalFrame().bytes())
                    &&result.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(receipt.original().originalResultToken()),
                    "guardian query response envelope/token changed");
            var outgoing=NativeWire.decodeExecuteRequest(receipt.original().outbound().orElseThrow().originalPacket());
            need(outgoing.requestId().equals(receipt.requestId())&&!receipt.requestId().equals(identity.pending().requestId())
                    &&outgoing.step().equals(OrdinaryInteractionCodec.QUERY_STEP)
                    &&outgoing.expectedRevision().equals(Optional.of(context.revision()))&&outgoing.expectedSnapshotRevision().isEmpty()
                    &&parse(new RawJson(outgoing.normalizedAdditionalFields().value())).equals(parse(OrdinaryInteractionCodec.request(context,intent,false))),
                    "guardian independent query changed original native fields or borrowed the submit request");
        }catch(IOException failure){throw new UncheckedIOException("guardian original query packet unreadable",failure);}
    }
    private static <T>T withProfile(ExactRef source,Supplier<T> work) {
        try {
            var witness=SharedSourceFiles.observe(Path.of(source.path()));
            need(witness.source().bytes()==source.bytes()&&witness.source().sha256().equals(source.sha256()),"actual guardian profile source changed");
            try{return Objects.requireNonNull(work.get());}finally{SharedSourceFiles.assertUnchanged(witness);}
        }catch(IOException failure){throw new UncheckedIOException("actual guardian profile source unavailable",failure);}
    }
}

