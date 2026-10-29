package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Original fresh legality, canonical pending and independently published native focus receipt; never a second submitter. */
public final class ChildEducationFocusEffects {
    public static final String PREPARATION_SCHEMA="xar.java.child-focus-original-preparation/v1";
    private static final OperationKey OPERATION=new OperationKey(ChildEducationFocusIntent.STEP);
    private final ReadContract<Obj> query;
    private final ReadContract<Obj> receipt;
    private final PlanningReadPort reads;
    private final NativeEffectSnapshots snapshots;
    private final NativeEffectEvidence.FrameLoader frames;
    public ChildEducationFocusEffects(ReadContract<Obj> actualQuery,ReadContract<Obj> actualReconciliationReceipt,
            PlanningReadPort actualReads,NativeEffectSnapshots actualSnapshots,NativeEffectEvidence.FrameLoader actualFrames) {
        query=Objects.requireNonNull(actualQuery);receipt=Objects.requireNonNull(actualReconciliationReceipt);
        reads=Objects.requireNonNull(actualReads);snapshots=Objects.requireNonNull(actualSnapshots);frames=Objects.requireNonNull(actualFrames);
        need(query.operation().value().equals(ChildEducationFocus.QUERY_STEP)&&query.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&query.contractId().equals(ChildEducationFocusQueries.QUERY_CONTRACT)
                &&receipt.operation().value().equals(ChildEducationFocus.RECEIPT_STEP)&&receipt.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&receipt.contractId().equals(ChildEducationFocusQueries.RECONCILIATION_RECEIPT_CONTRACT)&&query.sourceRef().equals(receipt.sourceRef()),
                "actual distinct ordinary-query and canonical-receipt products required");
        for(var actual:List.of(query,receipt))need(actual.hasPureReplay()&&actual.requiredCapability().isEmpty()
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&actual.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&actual.permissionKey().equals(ChildEducationFocus.PERMISSION),"focus read must retain its exact original private native producer profile");
    }
    public static boolean accepts(ActionCommand command) {
        if(!command.operation().equals(OPERATION))return false;
        try{return command.origin() instanceof CommandOrigin.Gameplay&&ChildEducationFocusIntent.fromJson(command.arguments())
                .expected(command.before(),command.source()).equals(command.expected());}
        catch(IllegalArgumentException invalid){return false;}
    }
    public static Selection selection(ChildEducationFocusIntent intent) {
        Objects.requireNonNull(intent);
        return new Selection(intent.childFullId(),Key.valueOf(intent.target().name()));
    }
    public record Preparation(PlanningReadReceipt read,Query query,Context context,List<ExactRef> materials) {
        public Preparation {Objects.requireNonNull(read);Objects.requireNonNull(query);Objects.requireNonNull(context);materials=List.copyOf(materials);}
    }
    /** The real Root preparer calls this only after its current source/lease and actual fresh query have been checked. */
    public NativeRequest prepare(ActionCommand command,String requestId,Complete originalBefore,PlanningReadReceipt fresh,
            ActionPorts.OutcomeArchive archive) {
        need(accepts(command),"canonical focus action and exact expectation required");StrictJson.text(requestId);
        need(originalBefore.identity().equals(command.before())&&originalBefore.source().equals(command.source())
                &&originalBefore.sessionId().equals(command.sessionId()),"focus fresh preparation changed actual command/source/session frame");
        verifyReadFrame(fresh,originalBefore,archive);Query legal=decodeQuery(command,fresh);
        need(legal.status()==QueryStatus.AVAILABLE&&legal.nativeLegal().equals(Optional.of(true)),"actual fresh native focus legality required");
        Context context=ChildEducationFocusQueries.context(fresh.request());
        // Reuse only the original query's common native frame/selection field encoder.
        // The returned step and installed private mutation permission remain the exact SUBMIT route.
        NativeRequest fields=ChildEducationFocusQueries.nativeRequest(new OperationKey(ChildEducationFocus.QUERY_STEP),context,legal.selection(),Optional.empty());
        var nativeFields=StrictJson.parse(fields.additionalFields().bytes()).deepCopy();
        need(nativeFields.isObject(),"actual focus request fields must be an object");
        ((com.fasterxml.jackson.databind.node.ObjectNode)nativeFields).put("action_request_id",requestId);
        RawJson raw=new RawJson(StrictJson.canonical(nativeFields));
        ExactRef before=archive.preserveRead(fresh);need(before.equals(archive.readReferenceOf(fresh)),"focus fresh read identity changed");
        var body=StrictJson.object().put("schema",PREPARATION_SCHEMA).put("command_body_sha256",ActionCodec.bodySha256(command))
                .put("request_id",requestId).put("prepared_fields_sha256",ActionCodec.sha256(raw.bytes()));body.set("before_read",before.toJson());
        RawJson manifest=new RawJson(StrictJson.canonical(body));ExactRef basis=archive.preserveMaterial(manifest);
        need(manifest.equals(archive.loadMaterial(basis)),"focus original manifest archive changed");
        return new NativeRequest(OPERATION.value(),Optional.empty(),raw,List.of(basis,before));
    }
    public Preparation loadPreparation(ActionCommand command,ActionState.Attempt attempt,Complete before,ActionPorts.OutcomeArchive archive) {
        return loadPreparation(command,attempt.requestId(),attempt.preparedRequest(),before,archive);
    }
    private Preparation loadPreparation(ActionCommand command,String requestId,NativeRequest prepared,Complete before,ActionPorts.OutcomeArchive archive) {
        need(accepts(command)&&before.identity().equals(command.before())&&before.source().equals(command.source())
                &&before.sessionId().equals(command.sessionId())&&prepared.step().equals(OPERATION.value())&&prepared.requiredCapability().isEmpty(),
                "focus original preparation changed command/frame/source/session/native route");
        var refs=prepared.preparationEvidence();need(refs.size()==2,"complete focus preparation requires exact manifest and original query");
        RawJson original=archive.loadMaterial(refs.getFirst());exact(refs.getFirst(),original.bytes());
        JsonNode n=StrictJson.object(StrictJson.parse(original.bytes()),java.util.Set.of("schema","command_body_sha256","request_id","prepared_fields_sha256","before_read"));
        need(PREPARATION_SCHEMA.equals(StrictJson.text(n.get("schema")))&&ActionCodec.bodySha256(command).equals(StrictJson.text(n.get("command_body_sha256")))
                &&requestId.equals(StrictJson.text(n.get("request_id")))&&ActionCodec.sha256(prepared.additionalFields().bytes()).equals(StrictJson.text(n.get("prepared_fields_sha256")))
                &&refs.getLast().equals(ExactRef.fromJson(n.get("before_read"))),"focus original manifest or native request changed");
        PlanningReadReceipt read=archive.loadRead(refs.getLast());need(archive.readReferenceOf(read).equals(refs.getLast()),"focus original query locator changed");
        verifyReadFrame(read,before,archive);Query decoded=decodeQuery(command,read);
        need(decoded.status()==QueryStatus.AVAILABLE&&decoded.nativeLegal().equals(Optional.of(true)),"original focus legality was not available and true");
        Context context=ChildEducationFocusQueries.context(read.request());
        NativeRequest fields=ChildEducationFocusQueries.nativeRequest(new OperationKey(ChildEducationFocus.QUERY_STEP),context,decoded.selection(),Optional.empty());
        var expected=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(fields.additionalFields().bytes());expected.put("action_request_id",requestId);
        need(StrictJson.parse(prepared.additionalFields().bytes()).equals(expected),"focus prepared fields differ from original fresh native frame/selection/request ID");
        return new Preparation(read,decoded,context,List.of(refs.getFirst()));
    }
    private Query decodeQuery(ActionCommand command,PlanningReadReceipt read) {
        query.replay(read);var intent=ChildEducationFocusIntent.fromJson(command.arguments());
        var arguments=ChildEducationFocusQueries.queryArguments(read.request().arguments());
        need(arguments.selection().equals(selection(intent))&&read.request().before().equals(command.before())
                &&arguments.expectedRevision().equals(command.before().frame().revision()),"focus query changed immutable child/key/public frame");
        return ChildEducationFocus.decodeQuery(read.original().originalResultToken().orElseThrow(),ChildEducationFocusQueries.context(read.request()).frame(),selection(intent));
    }
    /** Canonical DATA wrapper only. Its authority is the actual Attempt, original wire and Root ancestry, never a Driver history row. */
    public Optional<Pending> pending(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            Preparation preparation,ActionPorts.OutcomeArchive archive) {
        requireOriginalDispatch(command,attempt,dispatch,archive);
        var context=preparation.context();var intent=ChildEducationFocusIntent.fromJson(command.arguments());
        return pendingData(context,selection(intent),attempt.requestId(),submittedData(dispatch,context,selection(intent),attempt.requestId()));
    }
    /** Decode the original response as DATA only, after pending() has verified its actual immutable custody. */
    static Optional<Submitted> submittedData(NativeActionPort.DispatchOutcome dispatch,Context context,Selection selected,String requestId) {
        need(dispatch.requestId().equals(requestId),"focus response changed its original request ID");
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            // A bridge completion/reclaim error may follow a real queued command.
            // Keep the canonical original unknown; only an explicit typed rejection
            // is negative, and only a real subsequent native receipt can grant focus.
            if(ack.nativeOk()&&ack.originalResultToken().isPresent())
                return Optional.of(ChildEducationFocus.decodeSubmitted(ack.originalResultToken().orElseThrow(),context.frame(),selected,requestId));
        }else need(dispatch instanceof NativeActionPort.Unknown,"focus pending requires the actual submitted ACK or UNKNOWN attempt");
        return Optional.empty();
    }
    /** Pure shared wire producer, never admission. The actual caller must first qualify canonical original dispatch custody. */
    static Optional<Pending> pendingData(Context context,Selection selection,String requestId,Optional<Submitted> originalSubmitted) {
        Objects.requireNonNull(context);Objects.requireNonNull(selection);StrictJson.text(requestId);Objects.requireNonNull(originalSubmitted);
        var n=StrictJson.object().put("schema",ChildEducationFocus.SCHEMA).put("kind","submit")
                .put("action_request_id",requestId).put("request_id",requestId).put("child_full_id",selection.child())
                .put("requested_focus_key",selection.target().wire()).put("source_public_revision",context.publicRevision());
        n.set("pre_frame",ChildEducationFocus.encodeFrame(context.frame()));n.set("source_context",ChildEducationFocus.encodeContext(context));
        if(originalSubmitted.isPresent()) {
            Submitted original=originalSubmitted.orElseThrow();
            need(original.equals(ChildEducationFocus.decodeSubmitted(original.original(),context.frame(),selection,requestId)),"typed focus submission differs from its actual source payload");
            var submitted=original.submission();
            if(submitted.status()==SubmitStatus.REJECTED_BEFORE_SUBMIT)return Optional.empty();
            n.put("status",submitted.status().name().toLowerCase(java.util.Locale.ROOT)).put("accepted",submitted.accepted());
            if(submitted.reason().isPresent())n.put("unavailable_reason",submitted.reason().orElseThrow());else n.putNull("unavailable_reason");
            if(submitted.accepted())n.put("native_command_submitted",true);else n.putNull("native_command_submitted");
        } else {
            n.put("status","action_state_unknown").putNull("accepted").putNull("native_command_submitted").putNull("unavailable_reason");
        }
        return Optional.of(ChildEducationFocus.decodePending(new RawJson(StrictJson.canonical(n))));
    }
    public NativeEffectRegistry.Projected observe(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive) {
        if(!accepts(command)||!ActionReconciliationScope.activeFor(command))return unresolved(attempt,"focus requires its actual canonical pending observation scope");
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);Preparation prepared=loadPreparation(command,attempt,before,archive);
        requireOriginalDispatch(command,attempt,dispatch,archive);
        var rejected=rejected(command,attempt,dispatch,prepared,archive);if(rejected.isPresent())return rejected.orElseThrow();
        Optional<Pending> pending=pending(command,attempt,dispatch,prepared,archive);
        if(pending.isEmpty())return unresolved(attempt,"focus original response did not establish a pending native attempt");
        var pair=snapshots.read(command,attempt);
        try {
            var args=ChildEducationFocusQueries.receiptArguments(new ChildEducationFocusQueries.ReceiptArguments(pair.after().identity().frame().revision(),pending.orElseThrow()));
            var request=PlanningReadRequest.newReconciliation(ActionReconciliationScope.requireIdentity(command,attempt),receipt.operation(),args,ActionObservationWindow.deadline(command));
            var result=reads.read(same,receipt,request);
            if(!(result instanceof PlanningReadResult.Known<Obj> known))return unresolved(attempt,"actual independent focus receipt unavailable");
            var projected=project(command,attempt,dispatch,pair,prepared,pending.orElseThrow(),known.receipt(),archive);
            if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
            ExactRef evidence=NativeEffectEvidence.preserve(command,attempt,pair,List.of(prepared.read(),known.receipt()),
                    projected.compatibleResult().orElseThrow(),prepared.materials(),archive);
            return NativeEffectSnapshots.withEvidence(projected,List.of(evidence,prepared.materials().getFirst()));
        }catch(IOException failure){throw new UncheckedIOException("actual canonical focus observation scope unavailable",failure);}
    }
    private NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair,Preparation prepared,Pending pending,PlanningReadReceipt after,ActionPorts.OutcomeArchive archive) {
        verifyReadFrame(prepared.read(),pair.before(),archive);
        verifyReadFrame(after,pair.after(),archive);NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),after,receipt.operation());
        receipt.replay(after);var args=ChildEducationFocusQueries.receiptArguments(after.request().arguments());
        need(args.pending().equals(pending)&&args.expectedRevision().equals(pair.after().identity().frame().revision()),"focus receipt changed the actual canonical pending/public after frame");
        requireChronology(prepared.read(),after,attempt,dispatch);
        Context context=ChildEducationFocusQueries.context(after.request());
        Receipt decoded=ChildEducationFocus.decodeReceipt(after.original().originalResultToken().orElseThrow(),context.frame(),pending);
        if(!decoded.observedApplied())return unresolved(attempt,"original native focus receipt remains pending/unavailable; current focus alone is not authority");
        var intent=ChildEducationFocusIntent.fromJson(command.arguments());
        Obj result=ChildEducationFocusQueries.project(decoded,context,after.requestId(),Optional.of(pending));
        return NativeEffectSnapshots.observed(command,attempt,pair.after(),ChildEducationFocusIntent.OBSERVER_SCHEMA,intent.values(),
                new ObservationProvenance.Query(after.requestId()),new RawJson(DriverJson.encode(result)),List.of());
    }
    private Optional<NativeEffectRegistry.Projected> rejected(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,Preparation prepared,ActionPorts.OutcomeArchive archive) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())return Optional.empty();
        var value=ChildEducationFocus.decodeSubmitted(ack.originalResultToken().orElseThrow(),prepared.context().frame(),selection(ChildEducationFocusIntent.fromJson(command.arguments())),attempt.requestId()).submission();
        if(value.status()!=SubmitStatus.REJECTED_BEFORE_SUBMIT)return Optional.empty();
        need(!value.accepted(),"a rejected focus submit cannot claim queue acceptance");
        ExactRef original=archive.preserveMaterial(ack.originalResultToken().orElseThrow());
        need(archive.loadMaterial(original).equals(ack.originalResultToken().orElseThrow()),"original native focus rejection changed");
        return Optional.of(new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(
                new ActionState.Rejected(attempt.requestId(),value.reason().filter(s->!s.isBlank()).orElse("native focus rejected before submit"),original)),Optional.empty()));
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualSource,Supplier<ContinuityStorePort.Session> actualSession) {
        return new NativeRecordedEvidenceVerifier.Binding(OPERATION,actualSource,(head,canonical,archive)->{
            need(accepts(canonical.command())&&canonical.state() instanceof ActionState.Settled,"focus replay requires the exact settled original action");
            var same=Objects.requireNonNull(actualSession.get());try{need(same.head().digest().equals(head.digest()),"focus replay must borrow the actual same writer head");}
            catch(IOException failure){throw new UncheckedIOException(failure);}
            var settled=(ActionState.Settled)canonical.state();Complete before=RootGuardEvidence.loadFrame(settled.attempt().guard(),archive,frames);
            var prep=loadPreparation(canonical.command(),settled.attempt(),before,archive);requireOriginalDispatch(canonical.command(),settled.attempt(),settled.dispatch(),archive);
            if(settled.settlement() instanceof ActionState.Rejected rejected) {
                need(settled.dispatch() instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&ack.originalResultToken().isPresent(),"focus rejection lacks its actual native payload");
                var ack=(NativeActionPort.AckReceived)settled.dispatch();
                var original=ack.originalResultToken().orElseThrow();
                var decoded=ChildEducationFocus.decodeSubmitted(original,prep.context().frame(),selection(ChildEducationFocusIntent.fromJson(canonical.command().arguments())),settled.attempt().requestId()).submission();
                need(decoded.status()==SubmitStatus.REJECTED_BEFORE_SUBMIT&&!decoded.accepted()
                        &&rejected.requestId().equals(settled.attempt().requestId())&&archive.loadMaterial(rejected.originalEvidence()).equals(original)
                        &&rejected.reason().equals(decoded.reason().filter(s->!s.isBlank()).orElse("native focus rejected before submit")),"focus rejection differs from original native payload");
                exact(rejected.originalEvidence(),original.bytes());return;
            }
            need(settled.settlement() instanceof ActionState.Applied,"focus send-only/control DATA cannot grant a focus mutation");
            var original=NativeEffectEvidence.load(canonical,archive,frames);
            need(original.independentReads().size()==2&&original.independentReads().getFirst().equals(prep.read())
                    &&original.supportingMaterials().equals(prep.materials()),"focus original read/material closure changed");
            var actualPending=pending(canonical.command(),settled.attempt(),settled.dispatch(),prep,archive).orElseThrow();
            var replayed=project(canonical.command(),settled.attempt(),settled.dispatch(),original.frames(),prep,actualPending,original.independentReads().getLast(),archive);
            replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
        });
    }
    private void verifyReadFrame(PlanningReadReceipt read,Complete actual,ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read,archive);boolean reconciliation=read.request().origin() instanceof CommandOrigin.Reconciliation;
        var identity=reconciliation?read.request().reconciliationBefore():read.request().before();
        need(identity.equals(actual.identity())&&read.request().source().equals(actual.source())&&read.request().sessionId().equals(actual.sessionId()),"focus read changed full original frame/source/session");
        for(var guard:List.of(read.before(),read.after())) {
            Complete rebuilt;String binding;
            if(reconciliation){var original=read.request().origin().requireReconciliation();need(guard.binding().origin() instanceof CommandOrigin.Reconciliation
                    &&guard.binding().origin().requireReconciliation().sameGuardFrame(original),"focus receipt changed canonical pending guard");
                rebuilt=frames.load(new NativeEffectEvidence.FrameBasis(original.nativeEvidence(),original.evidence().observationManifest()),archive);binding=original.bindingSha256();
            }else{rebuilt=RootGuardEvidence.loadFrame(guard.binding(),archive,frames);binding=actual.fullBindingSha256();}
            need(NativeEffectEvidence.basis(rebuilt).equals(NativeEffectEvidence.basis(actual))&&rebuilt.fullBindingSha256().equals(actual.fullBindingSha256())
                    &&guard.originalBindingSha256().equals(binding),"focus read lost exact original native/Driver guard closure");
        }
    }
    private static void requireChronology(PlanningReadReceipt before,PlanningReadReceipt after,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        var first=before.original().custody().orElseThrow();var last=after.original().custody().orElseThrow();first.verify(before);last.verify(after);
        need(first.session().equals(last.session())&&first.custodyEpoch().equals(last.custodyEpoch())
                &&first.responseReceived().order().compareTo(last.writeEntered().order())<0
                &&!first.responseReceived().observedAt().isAfter(attempt.submittedAt())&&!last.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "focus independent reads crossed the original submission/custody interval");
        if(dispatch instanceof NativeActionPort.AckReceived ack){
            // This native route can return an error after queueing. Ordering comes
            // from retained endpoint custody, independently of ACK business success.
            var submitted=ack.custody().orElseThrow();submitted.verify(ack,attempt.guard());
            need(submitted.session().equals(first.session())&&submitted.custodyEpoch().equals(first.custodyEpoch())
                    &&!first.requestId().equals(attempt.requestId())&&!last.requestId().equals(attempt.requestId())
                    &&!submitted.writeEntered().observedAt().isBefore(attempt.submittedAt())
                    &&first.responseReceived().order().compareTo(submitted.writeEntered().order())<0
                    &&!first.responseReceived().observedAt().isAfter(submitted.writeEntered().observedAt())
                    &&last.writeEntered().order().compareTo(submitted.responseReceived().order())>0
                    &&!last.writeEntered().observedAt().isBefore(submitted.responseReceived().observedAt()),
                    "focus source and receipt did not bracket the actual original endpoint write/response");
        }
        else need(dispatch instanceof NativeActionPort.Unknown,"focus observation has no original native submission");
    }
    private static void requireOriginalDispatch(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive) {
        need(dispatch.requestId().equals(attempt.requestId())&&archive.load(archive.referenceOf(dispatch)).equals(dispatch),"focus original dispatch changed");
        byte[] packet;
        if(dispatch instanceof NativeActionPort.AckReceived ack){need(ack.outbound().isPresent()&&ack.custody().isPresent(),"actual focus ACK requires retained outbound/response custody");
            ack.custody().orElseThrow().verify(ack,attempt.guard());packet=ack.outbound().orElseThrow().originalPacket();
            try{var decoded=NativeWire.decode(ack.originalPacket());need(decoded instanceof NativeWire.CommandResult,"focus ACK original packet type differs");
                var result=(NativeWire.CommandResult)decoded;need(result.requestId().equals(attempt.requestId())&&result.nativeOk()==ack.nativeOk()
                        &&java.util.Arrays.equals(result.payload().value(),ack.originalFrame().bytes())
                        &&result.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(ack.originalResultToken()),"focus actual ACK envelope/token changed");
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }else{need(dispatch instanceof NativeActionPort.Unknown,"focus requires original ACK or UNKNOWN");packet=((NativeActionPort.Unknown)dispatch).originalRequestPacket();}
        need(packet.length>0,"focus original submitted request packet is absent; no invented pending or retry");
        try{var actual=NativeWire.decodeExecuteRequest(packet);need(actual.requestId().equals(attempt.requestId())&&actual.step().equals(OPERATION.value())
                &&actual.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))&&actual.expectedSnapshotRevision().isEmpty()
                &&StrictJson.parse(actual.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),
                "focus original wire differs from its one immutable prepared native request");}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static NativeEffectRegistry.Projected unresolved(ActionState.Attempt attempt,String reason){return NativeEffectRegistry.Projected.pending(reason,List.of(attempt.guard().nativeEvidence()));}
    private static void exact(ExactRef reference,byte[] bytes){need(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"original focus material bytes changed");}
    private static void need(boolean condition,String message){StrictJson.require(condition,message);}
}
