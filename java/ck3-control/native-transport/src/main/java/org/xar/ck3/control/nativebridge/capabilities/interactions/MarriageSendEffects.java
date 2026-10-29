package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames;
import org.xar.ck3.control.application.effects.family.FamilySendWriterExclusion;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.*;

/** Observes a new native outgoing request using original preparation, complete storage and the sole Game writer. */
public final class MarriageSendEffects {
    public static final String PREPARATION_SCHEMA="xar.java.family-marriage-send-preparation/v1";
    private final FamilyMarriageSendReads queries;
    private final PlanningReadPort reads;
    private final NativeEffectSnapshots snapshots;
    private final NativeEffectEvidence.FrameLoader frames;
    public MarriageSendEffects(FamilyMarriageSendReads actualQueries,PlanningReadPort actualReads,
            NativeEffectSnapshots actualSnapshots,NativeEffectEvidence.FrameLoader actualFrames) {
        queries=Objects.requireNonNull(actualQueries);reads=Objects.requireNonNull(actualReads);
        snapshots=Objects.requireNonNull(actualSnapshots);frames=Objects.requireNonNull(actualFrames);
    }
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source,Sender sender) {
        return FamilyMarriageSendExpectation.expected(before,source,sender.subject(),sender.candidate());
    }
    public static boolean accepts(ActionCommand command) {
        if(!command.expected().observerSchema().equals(FamilyMarriageSendExpectation.SCHEMA))return false;
        try {Sender sender=FamilyMarriageSendReads.sender(command);
            return command.expected().equals(expected(command.before(),command.source(),sender));
        }catch(IllegalArgumentException failure){return false;}
    }
    /** Source-qualified producer keeps these refs in its one NativeRequest manifest, without changing native fields. */
    public static List<ExactRef> preservePreparation(ActionCommand command,String requestId,NativeRequest nativeRequest,
            PlanningReadReceipt actualBefore,ActionPorts.OutcomeArchive archive) {
        need(accepts(command),"exact shared marriage send postcondition required");
        need(nativeRequest.step().equals(command.operation().value()),"preparation changed the original native operation");
        NativeRecordedEvidenceVerifier.requireRead(actualBefore,archive);
        var arguments=FamilyMarriageSendReads.arguments(actualBefore.request().arguments());
        requireArguments(command,requestId,arguments,Scope.ACTION_PREPARATION);
        need(actualBefore.request().before().equals(command.before())&&!actualBefore.requestId().equals(requestId),"before preparation crossed original frame or submit identity");
        ExactRef read=archive.preserveRead(actualBefore);need(read.equals(archive.readReferenceOf(actualBefore)),"actual before read identity changed");
        var n=StrictJson.object().put("schema",PREPARATION_SCHEMA).put("command_body_sha256",ActionCodec.bodySha256(command))
                .put("request_id",requestId).put("prepared_fields_sha256",ActionCodec.sha256(nativeRequest.additionalFields().bytes()));
        n.set("before_read",read.toJson());ExactRef basis=archive.preserveMaterial(raw(n));
        return List.of(basis,read);
    }
    public record Preparation(ExactRef basis,PlanningReadReceipt read,Observation observation,Prepared materialized,List<ExactRef> materials) {
        public Preparation {Objects.requireNonNull(basis);Objects.requireNonNull(read);Objects.requireNonNull(observation);Objects.requireNonNull(materialized);materials=List.copyOf(materials);}
    }
    private record OriginalPreparationManifest(ExactRef basis,String bodySha256,String requestId,String fieldsSha256,ExactRef beforeRead) { }
    /** Actual fresh/pending consumers use the retained original manifest's request ID, never a reconstructed nonce. */
    public Preparation loadPreparation(ActionCommand command,NativeRequest originalPrepared,Complete before,ActionPorts.OutcomeArchive archive) {
        return loadPreparation(command,originalManifest(originalPrepared,archive).requestId(),originalPrepared,before,archive);
    }
    /** Reads only preserved originals. The installed query replay owns the preparation's original qualification. */
    public Preparation loadPreparation(ActionCommand command,String requestId,NativeRequest originalPrepared,Complete before,ActionPorts.OutcomeArchive archive) {
        need(accepts(command)&&before.identity().equals(command.before())&&before.source().equals(command.source())
                &&before.sessionId().equals(command.sessionId())&&originalPrepared.step().equals(command.operation().value()),"original marriage preparation crossed action/source/session");
        var original=originalManifest(originalPrepared,archive);
        need(original.bodySha256().equals(ActionCodec.bodySha256(command))&&original.requestId().equals(requestId)
                &&original.fieldsSha256().equals(ActionCodec.sha256(originalPrepared.additionalFields().bytes())),
                "original marriage manifest changed immutable command/request/native fields");
        ExactRef basis=original.basis(),readRef=original.beforeRead();
        need(originalPrepared.preparationEvidence().contains(readRef),"actual before query absent from the original preparation closure");
        PlanningReadReceipt read=archive.loadRead(readRef);need(archive.readReferenceOf(read).equals(readRef),"actual before query locator changed");
        NativeRecordedEvidenceVerifier.requireRead(read,archive);verifyReadFrame(read,before,archive);
        var args=FamilyMarriageSendReads.arguments(read.request().arguments());requireArguments(command,requestId,args,Scope.ACTION_PREPARATION);
        need(!read.requestId().equals(requestId),"action ACK reused as independent before query");
        Observation decoded=queries.preparationContract().replay(read);
        need(decoded.prepared().orElseThrow() instanceof Prepared,"actual original native marriage context unavailable");
        Prepared prepared=(Prepared)decoded.prepared().orElseThrow();Sender sender=FamilyMarriageSendReads.sender(command);
        need(prepared.canSend()&&decoded.outgoing().complete(),"original complete native legality/context/storage required");
        need((sender.route()==Route.RULER||prepared.roles().actor()==sender.actor())&&(sender.route()==Route.RULER||
                prepared.roles().secondaryActor()==sender.subject()&&prepared.roles().secondaryRecipient()==sender.candidate())
                &&(sender.recipient().isEmpty()||prepared.roles().recipient()==sender.recipient().getAsLong()),"native materialized five roles differ from the exact intended pair");
        boolean intended=sender.route()==Route.RULER?prepared.matrilineal():FamilyMarriageIntent.fromJson(command.arguments()).matrilineal();
        need(matrilinealMatches(sender,intended,prepared),"actual selected/effective native matrilineality differs from its original route contract");
        return new Preparation(basis,read,decoded,prepared,List.of(basis));
    }
    /** Native setter flags, selected option and effective lineality are distinct source fields. */
    static boolean matrilinealMatches(Sender sender,boolean intendedSelection,Prepared actual) {
        Objects.requireNonNull(sender);Objects.requireNonNull(actual);
        if(sender.route()==Route.RULER)return true;
        if(sender.route()==Route.FULFILL_BETROTHAL)
            return actual.effectiveMatrilineal().filter(effective->effective.booleanValue()==intendedSelection).isPresent();
        boolean actualSelection=actual.matrilineal();
        boolean selectedMatches=intendedSelection==actualSelection&&(!sender.requestMatrilineal()||actualSelection)
                &&(!sender.requireMatrilinealOff()||!actualSelection);
        if(sender.route()==Route.CHILD_MATRILINEAL||sender.route()==Route.CHILD_DEFAULT)
            return selectedMatches&&actual.effectiveMatrilineal().filter(effective->effective.booleanValue()==intendedSelection).isPresent();
        return selectedMatches;
    }
    private static OriginalPreparationManifest originalManifest(NativeRequest originalPrepared,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(originalPrepared);Objects.requireNonNull(archive);
        ExactRef basis=null;ObjectNode n=null;
        for(ExactRef ref:originalPrepared.preparationEvidence()) {
            RawJson body=archive.loadMaterial(ref);exact(ref,body.bytes());JsonNode parsed=DriverJson.toNode(DriverJson.object(body.bytes(),DriverJson.MAX_NATIVE_BYTES));
            if(parsed.isObject()&&parsed.has("schema")&&parsed.get("schema").isTextual()&&PREPARATION_SCHEMA.equals(parsed.get("schema").textValue())) {
                need(basis==null,"ambiguous marriage outgoing preparation manifests");basis=ref;n=StrictJson.object(parsed,Set.of("schema","command_body_sha256","request_id","prepared_fields_sha256","before_read"));
            }
        }
        need(basis!=null&&n!=null,"original preparation has no complete outgoing baseline");
        ExactRef readRef=ExactRef.fromJson(n.get("before_read"));
        need(readRef.bytes()>0&&originalPrepared.preparationEvidence().contains(readRef),"actual before query absent from complete original preparation");
        return new OriginalPreparationManifest(basis,StrictJson.text(n.get("command_body_sha256")),StrictJson.text(n.get("request_id")),
                StrictJson.text(n.get("prepared_fields_sha256")),readRef);
    }
    /** UNKNOWN remains unresolved until the coordinator enters its original canonical pending observation scope. */
    public NativeEffectRegistry.Projected observe(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive) {
        if(!accepts(command)||!ActionReconciliationScope.activeFor(command))
            return NativeEffectRegistry.Projected.pending("original marriage request requires its actual canonical reconciliation scope",List.of(attempt.guard().nativeEvidence()));
        if(!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.custody().isEmpty())
            return NativeEffectRegistry.Projected.pending("family-send v1 retains UNKNOWN until actual response custody is available",List.of(attempt.guard().nativeEvidence()));
        try {
            var pair=snapshots.readFamilySend(command,attempt);
            Preparation prepared=loadPreparation(command,attempt.requestId(),attempt.preparedRequest(),pair.before(),archive);
            if(!outbound(command,attempt,dispatch))return pending(pair,"original marriage submit packet unavailable");
            var request=PlanningReadRequest.newReconciliation(ActionReconciliationScope.requireIdentity(command,attempt),queries.observationContract().operation(),
                    FamilyMarriageSendReads.observationArguments(command,attempt,archive.readReferenceOf(prepared.read()),prepared.materialized().roles().actor()),ActionObservationWindow.deadline(command));
            var result=reads.read(same,queries.observationContract(),request);
            if(!(result instanceof PlanningReadResult.Known<Observation> known))return pending(pair,"independent complete marriage outgoing storage unavailable");
            verifyReadFrame(known.receipt(),pair.after(),archive);
            NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),known.receipt(),queries.observationContract().operation());
            return project(command,attempt,dispatch,pair,prepared,known.receipt(),same.head(),archive);
        }catch(IOException failure){throw new UncheckedIOException("actual original marriage reconciliation is unavailable",failure);}
    }
    /** Original-byte replay entry; all preparation, packet, guard and source contracts are still rederived. */
    public NativeEffectRegistry.Projected projectOriginals(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            OriginalFrames pair,PlanningReadReceipt actualAfter,WriterContracts.Head head,ActionPorts.OutcomeArchive archive) {
        Preparation prepared=loadPreparation(command,attempt.requestId(),attempt.preparedRequest(),pair.before(),archive);
        verifyReadFrame(actualAfter,pair.after(),archive);
        NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),actualAfter,queries.observationContract().operation());
        return project(command,attempt,dispatch,pair,prepared,actualAfter,head,archive);
    }
    private NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            OriginalFrames pair,Preparation prepared,PlanningReadReceipt afterRead,WriterContracts.Head head,ActionPorts.OutcomeArchive archive) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.custody().isEmpty())
            return pending(pair,"family-send v1 cannot synthesize original ACK custody for UNKNOWN");
        if(!outbound(command,attempt,dispatch))return pending(pair,"original marriage dispatch is unbound");
        requireChronology(prepared.read(),afterRead,attempt,dispatch);
        var args=FamilyMarriageSendReads.arguments(afterRead.request().arguments());requireArguments(command,attempt.requestId(),args,Scope.POST_SUBMISSION);
        need(args.beforeRead().orElseThrow().equals(archive.readReferenceOf(prepared.read())),"after storage query borrowed a different before baseline");
        Observation after=queries.observationContract().replay(afterRead);
        OptionalLong pending=match(prepared.materialized(),prepared.observation().outgoing(),after.outgoing());
        if(pending.isEmpty()||!FamilySendWriterExclusion.exclusive(head,command,attempt,prepared.read(),afterRead,pair,archive))
            return pending(pair,"outgoing difference is incomplete, pre-existing, ambiguous or crossed another Game submission");
        Sender sender=FamilyMarriageSendReads.sender(command);
        var observation=new FamilySendObservation(FamilySendObservation.Profile.MARRIAGE,command.actionId(),ActionCodec.bodySha256(command),
                attempt.requestId(),archive.referenceOf(dispatch),archive.requestReferenceOf(attempt.preparedRequest()),
                NativeEffectEvidence.basis(pair.before()),NativeEffectEvidence.basis(pair.after()),
                pair.before().identity(),pair.after().identity(),command.source(),command.sessionId(),prepared.read(),afterRead,
                attempt.preparedRequest().preparationEvidence(),pending.getAsLong(),prepared.materialized().definitionHash(),
                FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE,sender.subject(),sender.candidate(),pending.getAsLong()));
        observation.validate(command,attempt,dispatch,archive);
        return new NativeEffectRegistry.Projected(new ActionPorts.FamilySendObserved(observation),Optional.empty());
    }
    /** Pure material comparison. Neither unique after state nor final relation alone establishes a send. */
    public static OptionalLong match(Prepared prepared,FamilyOutgoingCodec.Snapshot before,FamilyOutgoingCodec.Snapshot after) {
        if(!prepared.canSend()||!before.complete()||!after.complete()
                ||before.profile()!=FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE||after.profile()!=FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE
                ||before.definitionHash().orElse(-1)!=prepared.definitionHash()||after.definitionHash().orElse(-1)!=prepared.definitionHash()
                ||before.senderCharacterId().orElse(-1)!=prepared.roles().actor()||after.senderCharacterId().orElse(-1)!=prepared.roles().actor())return OptionalLong.empty();
        if(before.frame().build()!=InteractionModels.Build.CROZIER4||after.frame().build()!=InteractionModels.Build.CROZIER4
                ||!before.frame().actor().equals(after.frame().actor())||!before.frame().date().equals(after.frame().date())
                ||after.frame().revision().compareTo(before.frame().revision())<0
                ||after.frame().querySequence().compareTo(before.frame().querySequence())<=0)return OptionalLong.empty();
        if(before.candidates().stream().anyMatch(c->sameMaterial(prepared,c)))return OptionalLong.empty();
        List<FamilyOutgoingCodec.Candidate> matches=after.candidates().stream().filter(c->sameMaterial(prepared,c)).toList();
        if(matches.size()!=1)return OptionalLong.empty();var candidate=matches.getFirst();
        if(!candidate.knownActiveRoute()||before.occupiedPendingIds().contains(candidate.pendingFullId()))return OptionalLong.empty();
        return OptionalLong.of(candidate.pendingFullId());
    }
    private static boolean sameMaterial(Prepared p,FamilyOutgoingCodec.Candidate c) {
        return c.definitionHash()==p.definitionHash()&&c.roles().equals(p.roles())&&c.options().equals(p.options());
    }
    private static boolean outbound(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        if(!dispatch.requestId().equals(attempt.requestId()))return false;byte[] packet;
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            if(!ack.nativeOk()||ack.outbound().isEmpty())return false;
            packet=ack.outbound().orElseThrow().originalPacket();
        }else if(dispatch instanceof NativeActionPort.Unknown unknown)packet=unknown.originalRequestPacket();else return false;
        if(packet.length==0)return false;
        try {
            var actual=NativeWire.decodeExecuteRequest(packet);
            need(actual.requestId().equals(attempt.requestId())&&actual.step().equals(command.operation().value())
                    &&actual.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                    &&actual.expectedSnapshotRevision().isEmpty()
                    &&StrictJson.parse(actual.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),
                    "original marriage submit packet differs from its immutable prepared native request");
            return true;
        }catch(IOException failure){throw new UncheckedIOException("original marriage native outbound packet is malformed",failure);}
    }
    private static void requireChronology(PlanningReadReceipt before,PlanningReadReceipt after,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        var first=before.original().custody().orElseThrow();var last=after.original().custody().orElseThrow();first.verify(before);last.verify(after);
        need(first.session().equals(last.session())&&first.custodyEpoch().equals(last.custodyEpoch())
                &&last.writeEntered().order().compareTo(first.responseReceived().order())>0
                &&!first.responseReceived().observedAt().isAfter(attempt.submittedAt())
                &&!last.writeEntered().observedAt().isBefore(attempt.submittedAt()),"marriage storage queries do not bracket the original native dispatch");
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            NativeRequestChronology.requireBeforeSubmission(before,attempt,ack);NativeRequestChronology.requireSampledAfter(after,attempt,ack);
        }else need(dispatch instanceof NativeActionPort.Unknown,"no original submitted marriage dispatch");
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,Supplier<ContinuityStorePort.Session> actualCurrent) {
        return new NativeRecordedEvidenceVerifier.Binding(operation,source,(head,receipt,archive)->{
            need(accepts(receipt.command())&&receipt.command().operation().equals(operation),"archived marriage observer has another exact operation or shared contract");
            ContinuityStorePort.Session same=Objects.requireNonNull(actualCurrent.get());need(sameHead(same).digest().equals(head.digest()),"marriage replay must use the actual same writer head");
            need(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed,
                    "marriage sender archive requires its dedicated typed send settlement");
            var settled=(ActionState.Settled)receipt.state();
            var observed=((ActionState.FamilySendConfirmed)settled.settlement()).observation();
            need(observed.profile()==FamilySendObservation.Profile.MARRIAGE,"marriage sender archive borrowed another domain profile");
            observed.validate(receipt.command(),settled.attempt(),settled.dispatch(),archive);
            var originals=observed.loadFrames(archive,frames);
            var replayed=projectOriginals(receipt.command(),settled.attempt(),settled.dispatch(),originals,observed.afterStorage(),head,archive);
            need(replayed.result() instanceof ActionPorts.FamilySendObserved send && send.observation().equals(observed)
                    && replayed.compatibleResult().isEmpty(),"archived marriage send differs from full original domain replay");
        });
    }
    private void verifyReadFrame(PlanningReadReceipt read,Complete actual,ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        need(FamilyMarriageSendReads.identity(read.request()).equals(actual.identity())&&read.request().source().equals(actual.source())
                &&read.request().sessionId().equals(actual.sessionId()),"original outgoing query changed actual full native/Driver frame");
        for(var guard:List.of(read.before(),read.after())) {
            Complete rebuilt;String binding;
            if(read.request().origin() instanceof CommandOrigin.Reconciliation) {
                var identity=read.request().origin().requireReconciliation();
                need(guard.binding().origin() instanceof CommandOrigin.Reconciliation&&guard.binding().origin().requireReconciliation().sameGuardFrame(identity),"outgoing reconciliation read guard changed original pending");
                rebuilt=frames.load(new NativeEffectEvidence.FrameBasis(identity.nativeEvidence(),identity.evidence().observationManifest()),archive);binding=identity.bindingSha256();
            }else {rebuilt=RootGuardEvidence.loadFrame(guard.binding(),archive,frames);binding=actual.fullBindingSha256();}
            need(NativeEffectEvidence.basis(rebuilt).equals(NativeEffectEvidence.basis(actual))
                    &&rebuilt.fullBindingSha256().equals(actual.fullBindingSha256())&&guard.originalBindingSha256().equals(binding),"outgoing query has incomplete original frame closure");
        }
    }
    private static void requireArguments(ActionCommand command,String requestId,Arguments a,Scope scope) {
        need(a.scope()==scope&&a.actionId().equals(command.actionId())&&a.bodySha256().equals(ActionCodec.bodySha256(command))
                &&a.attemptRequestId().equals(requestId)&&a.senderIntent().equals(command.arguments()),"outgoing query borrowed another immutable sender intent/request");
    }
    private static NativeEffectRegistry.Projected pending(OriginalFrames pair,String reason){return NativeEffectRegistry.Projected.pending(reason,List.of(pair.after().originalEvidence()));}
    private static WriterContracts.Head sameHead(ContinuityStorePort.Session same) {try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static void text(JsonNode n,String key,String value){need(value.equals(StrictJson.text(n.get(key))),"original marriage preparation field differs: "+key);}
    private static void exact(ExactRef reference,byte[] raw){need(reference.bytes()==raw.length&&reference.sha256().equals(ActionCodec.sha256(raw)),"actual original marriage material changed");}
    private static void need(boolean condition,String message){StrictJson.require(condition,message);}
}

