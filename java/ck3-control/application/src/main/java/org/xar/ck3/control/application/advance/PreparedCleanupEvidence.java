package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** DATA codecs for a separately authorized, prepared fifth cleanup child. None of
 * these records or methods is an Attempt, Submitting state, Guard, issuer, installed
 * source witness or Native permit. Canonical membership, accepted actual A/backend
 * qualification and the one-write late physical capability belong to the actual
 * source/coordinator/SDK. No method submits, refreshes an old command or grants credit. */
public final class PreparedCleanupEvidence {
    public static final String CURSOR_PREFIX="prepared-cleanup-successor/v1: ";
    public static final String PREPARED_SCHEMA="xar.life-prepared-cleanup/v1";
    public static final String LATE_SCHEMA="xar.life-prepared-cleanup-late-binding/v1";
    public static final String CAPTURED_SCHEMA="xar.life-prepared-cleanup-post-ack/v1";
    public static final String FAILURE_SCHEMA="xar.life-prepared-cleanup-failure/v1";
    private static final int MAXIMUM=64*1024;
    private static final Duration OPERATION_WINDOW=Duration.ofMinutes(10),READ_WINDOW=Duration.ofMinutes(2);
    private static final Set<String> PREPARED_FIELDS=Set.of("schema","original_parent","original_children","a_terminal",
            "a_proof","authorization","command","command_body_sha256","native_request_id","native_prepared","preparation_nonce","issued_at_utc","deadline_utc");
    private PreparedCleanupEvidence() { }

    public record Prepared(ExactRef reference,ActionReceipt parentReceipt,ExactRef parentReference,
            List<ActionReceipt> children,List<ExactRef> childReferences,ExactRef aTerminalReference,
            ExactRef aProofReference,ExactRef authorizationReference,PostExitCleanupNoEffectProof.Originals aProof,
            ActionCommand command,ExactRef commandReference,String nativeRequestId,NativeRequest nativePrepared,
            ExactRef nativePreparedReference,String preparationNonce,Instant issuedAt,Instant deadline) {
        public Prepared { Objects.requireNonNull(reference);Objects.requireNonNull(parentReceipt);Objects.requireNonNull(parentReference);
            children=List.copyOf(children);childReferences=List.copyOf(childReferences);Objects.requireNonNull(aTerminalReference);
            Objects.requireNonNull(aProofReference);Objects.requireNonNull(authorizationReference);Objects.requireNonNull(aProof);
            Objects.requireNonNull(command);Objects.requireNonNull(commandReference);StrictJson.text(nativeRequestId);
            Objects.requireNonNull(nativePrepared);Objects.requireNonNull(nativePreparedReference);requireCanonicalNonce(preparationNonce);Objects.requireNonNull(issuedAt);Objects.requireNonNull(deadline); }
    }
    /** Volatile original sample. Construction issues no read guard/source authority and does not archive or query. */
    public record StatusSample(NativeActionPort.AckReceived acknowledgement,Instant deadline) {
        public StatusSample { Objects.requireNonNull(acknowledgement);Objects.requireNonNull(deadline);
            require(acknowledgement.nativeOk(),"prepared cleanup Status sample requires a successful original READ ACK");
            var custody=acknowledgement.custody().orElseThrow();custody.verify(acknowledgement);
            require(custody.writeEntered().observedAt().isBefore(deadline)&&!custody.responseReceived().observedAt().isAfter(deadline)
                    &&!deadline.isAfter(custody.writeEntered().observedAt().plus(READ_WINDOW)),"prepared cleanup Status escaped its original at-most-two-minute READ window");
            ClockStatusRead.decode(acknowledgement); }
        public org.xar.ck3.control.reconciliation.LateOutcome.Status status(){return ClockStatusRead.decode(acknowledgement);}
    }
    /** Same-call volatile late binding. There is deliberately no durable append or archive call in its constructor. */
    public record LateBinding(Prepared prepared,StatusSample status,NativeActionPort.AckReceived freshSnapshotAck,
            NativeObservationPort.ObservedFrame writeFrame,NativeRequestChronology.Event snapshotReceived,
            Instant boundAt,Instant writeDeadline) {
        public LateBinding { Objects.requireNonNull(prepared);Objects.requireNonNull(status);Objects.requireNonNull(freshSnapshotAck);
            Objects.requireNonNull(writeFrame);Objects.requireNonNull(snapshotReceived);Objects.requireNonNull(boundAt);Objects.requireNonNull(writeDeadline); }
    }
    /** Capture all originals before any slow durable outcome work. An incomplete capture is never successful. */
    public record PostAckCaptured(LateBinding binding,NativeActionPort.AckReceived cancellationAcknowledgement,
            StatusSample idle1,StatusSample idle2,NativeActionPort.AckReceived freshSnapshotAck,
            NativeObservationPort.ObservedFrame afterFrame,NativeRequestChronology.Event snapshotReceived,Instant captureDeadline) {
        public PostAckCaptured { Objects.requireNonNull(binding);Objects.requireNonNull(cancellationAcknowledgement);Objects.requireNonNull(idle1);
            Objects.requireNonNull(idle2);Objects.requireNonNull(freshSnapshotAck);Objects.requireNonNull(afterFrame);
            Objects.requireNonNull(snapshotReceived);Objects.requireNonNull(captureDeadline); }
    }
    /** Preserves the SDK's actual typed result; never converts arbitrary failure to NoDispatch. */
    public record FailureData(Prepared prepared,Optional<LateBinding> binding,NativeActionPort.DispatchOutcome original,
            List<NativeActionPort.DispatchOutcome> observationOriginals,Instant capturedAt,List<ExactRef> supplementalOriginals) {
        public FailureData { Objects.requireNonNull(prepared);binding=Objects.requireNonNull(binding);Objects.requireNonNull(original);
            observationOriginals=List.copyOf(observationOriginals);require(observationOriginals.size()<=5,"bounded original cleanup observation failure chain required");
            Objects.requireNonNull(capturedAt);supplementalOriginals=List.copyOf(supplementalOriginals); }
    }

    /** Durable preparation DATA only. Actual Root must already have verified canonical A and backend/source qualification. */
    public static ExactRef preservePrepared(ActionReceipt parent,List<ActionReceipt> children,ActionCommand child5,
            NativeRequest nativePrepared,String preparationNonce,Instant issuedAt,Instant deadline,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        children=List.copyOf(children);require(children.size()==4&&children.getLast().state() instanceof ActionState.CleanupNoEffectConfirmed,
                "prepared cleanup requires four actual originals ending in A NoEffect terminal");
        var terminal=children.getLast();var terminalState=(ActionState.CleanupNoEffectConfirmed)terminal.state();
        var proof=PostExitCleanupNoEffectProof.load(terminalState.proofReference(),archive,frames);
        var row=StrictJson.object();row.put("schema",PREPARED_SCHEMA);row.set("original_parent",archive.receiptReferenceOf(parent).toJson());
        var references=row.putArray("original_children");for(var child:children)references.add(archive.receiptReferenceOf(child).toJson());
        row.set("a_terminal",archive.receiptReferenceOf(terminal).toJson());row.set("a_proof",terminalState.proofReference().toJson());
        row.set("authorization",proof.authorizationReference().toJson());row.set("command",archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(child5))).toJson());
        row.put("command_body_sha256",ActionCodec.bodySha256(child5));row.put("native_request_id",RequestIds.forCommand(child5));
        row.set("native_prepared",archive.preserveRequest(nativePrepared).toJson());requireCanonicalNonce(preparationNonce);row.put("preparation_nonce",preparationNonce);row.put("issued_at_utc",issuedAt.toString());row.put("deadline_utc",deadline.toString());
        var reference=archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));var decoded=loadPrepared(reference,archive,frames);
        require(decoded.parentReceipt().equals(parent)&&decoded.children().equals(children)&&decoded.command().equals(child5)
                &&decoded.nativePrepared().equals(nativePrepared),"prepared cleanup canonical original roundtrip differs");return reference;
    }
    public static Prepared loadPrepared(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        return loadPreparedChecked(reference,archive,Objects.requireNonNull(frames));
    }
    public static Prepared loadPreparedOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        return loadPreparedChecked(reference,archive,null);
    }
    private static Prepared loadPreparedChecked(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Obj row=material(reference,archive);
        if(new Text(PreparedCleanupSuccessorEvidence.PREPARED_SCHEMA).equals(row.get("schema")))
            return frames==null?PreparedCleanupSuccessorEvidence.loadPreparedOriginals(reference,archive)
                    :PreparedCleanupSuccessorEvidence.loadPrepared(reference,archive,frames);
        require(row.members().keySet().equals(PREPARED_FIELDS)&&new Text(PREPARED_SCHEMA).equals(row.get("schema")),
                "prepared cleanup schema or fields differ");
        var parentReference=exact(row.get("original_parent"));var parent=receipt(parentReference,archive);
        var references=new ArrayList<ExactRef>();var children=new ArrayList<ActionReceipt>();
        for(var item:array(row.get("original_children"),"original_children")){var ref=exact(item);references.add(ref);children.add(receipt(ref,archive));}
        require(children.size()==4&&references.stream().distinct().count()==4&&references.stream().noneMatch(parentReference::equals),
                "prepared cleanup needs complete distinct original four-child references");
        var terminalReference=exact(row.get("a_terminal"));var terminal=children.getLast();
        require(terminalReference.equals(references.getLast())&&terminal.state() instanceof ActionState.CleanupNoEffectConfirmed,
                "prepared cleanup A terminal is not its exact fourth original");
        var terminalState=(ActionState.CleanupNoEffectConfirmed)terminal.state();var proofReference=exact(row.get("a_proof"));
        require(terminalState.proofReference().equals(proofReference),"prepared cleanup A terminal changed its proof");
        PostExitCleanupNoEffectProof.verifyArchivedState(terminal,proofReference,terminalState.originalAttempt(),terminalState.originalDispatch(),archive);
        var proof=frames==null?PostExitCleanupNoEffectProof.loadOriginals(proofReference,archive):PostExitCleanupNoEffectProof.load(proofReference,archive,frames);
        var authorization=exact(row.get("authorization"));
        require(parent.equals(proof.parentReceipt())&&parentReference.equals(proof.parentReference())&&authorization.equals(proof.authorizationReference())
                &&children.subList(0,3).equals(proof.children().subList(0,3))&&terminal.command().equals(proof.child4().command())
                &&terminal.bodySha256().equals(proof.child4().bodySha256()),"prepared cleanup changed original parent/four-prefix/auth");
        var commandReference=exact(row.get("command"));byte[] commandBytes=archive.loadMaterial(commandReference).bytes();exactBytes(commandReference,commandBytes);
        var command=ActionCodec.decodeCommand(commandBytes);require(java.util.Arrays.equals(commandBytes,ActionCodec.encodeCommand(command)),
                "prepared cleanup command is not its complete canonical original");
        var requestReference=exact(row.get("native_prepared"));var nativePrepared=archive.loadRequest(requestReference);
        require(archive.requestReferenceOf(nativePrepared).equals(requestReference),"prepared cleanup native preparation reference differs");
        Instant issuedAt=instant(row.get("issued_at_utc"),"issued_at_utc"),deadline=instant(row.get("deadline_utc"),"deadline_utc");
        var requestId=text(row.get("native_request_id"),"native_request_id");var preparationNonce=text(row.get("preparation_nonce"),"preparation_nonce");requireCanonicalNonce(preparationNonce);
        require(requestId.equals(RequestIds.forCommand(command))&&new Text(ActionCodec.bodySha256(command)).equals(row.get("command_body_sha256")),
                "prepared cleanup command digest or deterministic native request ID differs");
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(OPERATION_WINDOW))&&command.deadline().equals(deadline)
                &&!issuedAt.isBefore(proof.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt()),
                "prepared cleanup does not have its own finite post-A operation window");
        var generation=proof.original().originalArm().generation().decimal();var operation=new OperationKey(ClockStatusRead.CANCEL_PREFIX+generation);
        var arguments=new Obj(java.util.Map.of());var expected=new ActionCommand(ActionIds.child(parent.command().actionId(),5,operation),command.before(),
                parent.command().source(),parent.command().sessionId(),operation,arguments,
                AdvancePrimitives.expected(command.before(),parent.command().source(),operation,arguments),parent.command().claims(),deadline);
        require(command.equals(expected)&&!command.actionId().equals(terminal.command().actionId())&&!requestId.equals(RequestIds.forCommand(terminal.command()))
                &&nativePrepared.equals(AdvancePrimitives.prepareRequest(command)),"prepared cleanup is not the distinct exact fifth generation-bound CANCEL");
        var identity=command.before();var previous=terminal.command().before();
        require(identity.game().equals(previous.game())&&identity.machineId().equals(previous.machineId())
                &&identity.frame().episodeRunId().equals(previous.frame().episodeRunId())
                &&identity.frame().identity().player().equals(previous.frame().identity().player())
                &&identity.frame().identity().dateRaw().equals(previous.frame().identity().dateRaw()),"prepared cleanup changed the original owner/episode/partial date");
        return new Prepared(reference,parent,parentReference,children,references,terminalReference,proofReference,authorization,proof,command,commandReference,
                requestId,nativePrepared,requestReference,preparationNonce,issuedAt,deadline);
    }
    private static ActionReceipt receipt(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var value=archive.loadReceipt(reference);require(archive.receiptReferenceOf(value).equals(reference),"prepared cleanup receipt original differs");return value;
    }
    private static Obj material(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        require(reference.bytes()>0&&reference.bytes()<=MAXIMUM,"prepared cleanup bounded material reference required");
        byte[] bytes=archive.loadMaterial(reference).bytes();exactBytes(reference,bytes);return DriverJson.object(bytes,MAXIMUM);
    }
    private static void exactBytes(ExactRef reference,byte[] bytes){require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"prepared cleanup original bytes changed");}
    private static ExactRef exact(Value value){return ExactRef.fromJson(toNode(object(value,"exact reference")));}
    private static Instant instant(Value value,String key){return Instant.parse(StrictJson.utc(text(value,key)));}

    /** Pure live-time predicates, with no archive/canonical/foreign callback between the late capture and write.
     * Actual SDK must additionally retain its private Prepared identity and call its original Native wire validators. */
    public static LateBinding bindLate(Prepared prepared,StatusSample status,NativeActionPort.AckReceived freshSnapshotAck,
            NativeObservationPort.ObservedFrame writeFrame,NativeRequestChronology.Event received,
            Instant boundAt,Instant writeDeadline,Instant actualNow) {
        var result=new LateBinding(prepared,status,freshSnapshotAck,writeFrame,received,boundAt,writeDeadline);
        requireLateBinding(result,actualNow);return result;
    }
    public static void requireLateBinding(LateBinding binding,Instant actualNow) {
        Objects.requireNonNull(actualNow);var prepared=binding.prepared();var read=binding.status();
        var statusCustody=read.acknowledgement().custody().orElseThrow();statusCustody.verify(read.acknowledgement());
        requireSubject(prepared,statusCustody.session());requireRawFrame(prepared,binding.writeFrame());
        requireFreshAfter(read.acknowledgement(),binding.freshSnapshotAck(),binding.writeFrame(),binding.snapshotReceived());
        var original=prepared.aProof().original();var current=read.status();var date=prepared.command().before().frame().identity().dateRaw();
        var delta=date.subtract(original.plan().startingDateRaw());AdvanceClock.requireSameSlot(original.originalArm(),current);
        require(delta.signum()>0&&delta.mod(AdvancePlan.DAY).signum()==0&&date.compareTo(original.plan().targetDateRaw())<0
                &&current.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED&&!current.abnormal()&&!current.terminalObserved()
                &&current.completedDailyTicks()==delta.divide(AdvancePlan.DAY).longValueExact()&&current.lastObservedDateRaw()==date.longValueExact()
                &&current.triggerDateRaw()==0&&current.intermediatePauseCount()==0&&current.triggerFlags()==0&&current.triggerReasons().isEmpty()
                &&current.signedDateDeltaFromTargetRaw()==0&&current.overshootDays()==-1&&!current.pauseWrapperCalled()&&!current.pauseObserved(),
                "late cleanup Status did not retain the original nonterminal ARMED partial slot");
        var expiry=min(prepared.deadline(),min(statusCustody.responseReceived().observedAt().plus(READ_WINDOW),binding.writeFrame().observedAt().plus(READ_WINDOW)));
        require(binding.writeDeadline().equals(expiry)&&!binding.boundAt().isBefore(binding.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt())
                &&!actualNow.isBefore(binding.boundAt())&&actualNow.isBefore(expiry)&&!read.deadline().isAfter(prepared.deadline())
                &&!statusCustody.writeEntered().observedAt().isBefore(prepared.issuedAt()),
                "late cleanup binding expired or widened its exact original operation/physical freshness window");
        var ids=originalIds(prepared);require(!ids.contains(read.acknowledgement().requestId())&&!ids.contains(binding.freshSnapshotAck().requestId())
                &&!read.acknowledgement().requestId().equals(binding.freshSnapshotAck().requestId()),"late cleanup READ reused an original command/native identity");
    }
    /** Event-time validation after all volatile originals have been captured; no clock.now is substituted. */
    public static void requirePostAckCaptured(PostAckCaptured captured) {
        var binding=captured.binding();requireLateBinding(binding,binding.boundAt());var prepared=binding.prepared();
        var ack=captured.cancellationAcknowledgement();var control=ack.custody().orElseThrow();control.verify(ack);
        require(ack.nativeOk()&&ack.requestId().equals(prepared.nativeRequestId()),"prepared cleanup has no original successful exact-child ACK");
        Obj result=DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),MAXIMUM);
        require(result.members().keySet().equals(Set.of("step","accepted","status"))
                &&new Text(prepared.command().operation().value()).equals(result.get("step"))
                &&new Bool(true).equals(result.get("accepted"))&&new Text("canceled").equals(result.get("status")),
                "prepared cleanup ACK is not the original accepted canceled result");
        var late=binding.freshSnapshotAck().custody().orElseThrow();
        require(control.session().equals(late.session())&&control.custodyEpoch().equals(late.custodyEpoch())
                &&control.writeEntered().order().compareTo(late.responseReceived().order())>0
                &&!control.writeEntered().observedAt().isBefore(binding.boundAt())&&control.writeEntered().observedAt().isBefore(binding.writeDeadline()),
                "prepared cleanup actual write crossed its late held connection or write deadline");
        var idle1=captured.idle1();var idle2=captured.idle2();var first=idle1.acknowledgement().custody().orElseThrow();
        var second=idle2.acknowledgement().custody().orElseThrow();requireAfter(control,first);requireAfter(first,second);
        requireFreshAfter(idle2.acknowledgement(),captured.freshSnapshotAck(),captured.afterFrame(),captured.snapshotReceived());
        requireRawFrame(prepared,captured.afterFrame());
        var original=prepared.aProof().original();var date=prepared.command().before().frame().identity().dateRaw();
        AdvanceClock.validateCancellation(original.originalArm(),idle1.status(),original.plan(),date);
        AdvanceClock.validateCancellation(original.originalArm(),idle2.status(),original.plan(),date);
        require(idle1.status().equals(idle2.status())&&idle1.status().completedDailyTicks()==binding.status().status().completedDailyTicks()
                &&idle1.status().lastObservedDateRaw()==binding.status().status().lastObservedDateRaw(),"prepared cleanup independent IDLE proofs changed the original partial slot");
        var until=captured.captureDeadline();require(until.isAfter(control.responseReceived().observedAt())
                &&!until.isAfter(control.responseReceived().observedAt().plus(READ_WINDOW))
                &&!idle1.deadline().isAfter(until)&&!idle2.deadline().isAfter(until)
                &&!captured.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt().isAfter(until)
                &&captured.afterFrame().nativeRevision().compareTo(binding.writeFrame().nativeRevision())>=0,
                "prepared cleanup volatile after-ACK capture escaped its own finite at-most-two-minute window");
        var ids=originalIds(prepared);var observed=List.of(binding.status().acknowledgement().requestId(),binding.freshSnapshotAck().requestId(),
                idle1.acknowledgement().requestId(),idle2.acknowledgement().requestId(),captured.freshSnapshotAck().requestId());
        require(observed.stream().distinct().count()==observed.size()&&observed.stream().noneMatch(ids::contains),
                "prepared cleanup reused an original or supposedly independent observation ID");
    }

    private static void requireSubject(Prepared prepared,NativeObservationPort.TransportSession session) {
        var command=prepared.command();require(session.machineId().equals(command.before().machineId())&&session.game().equals(command.before().game())
                &&session.sessionId().equals(command.sessionId()),"prepared cleanup crossed its original machine/Game birth/session");
    }
    private static void requireRawFrame(Prepared prepared,NativeObservationPort.ObservedFrame frame) {
        requireSubject(prepared,frame.session());Obj state=DriverJson.object(frame.state().bytes(),RawJson.MAXIMUM_BYTES);
        var player=object(state.get("played_character"),"played_character");var before=prepared.command().before().frame().identity();
        require(new Bool(true).equals(state.get("paused"))&&new Bool(true).equals(state.get("map_ready"))&&new Bool(true).equals(player.get("alive"))
                &&integer(state.get("date_raw"),"date_raw").equals(before.dateRaw())&&integer(player.get("character_id"),"character_id").equals(before.player())
                &&frame.nativeRevision().compareTo(before.nativeRevision())>=0,"prepared cleanup raw full frame changed the alive paused original actor/partial date");
    }
    private static void requireAfter(NativeRequestChronology before,NativeRequestChronology after) {
        require(before.session().equals(after.session())&&before.custodyEpoch().equals(after.custodyEpoch())&&!before.requestId().equals(after.requestId())
                &&after.writeEntered().order().compareTo(before.responseReceived().order())>0
                &&!after.writeEntered().observedAt().isBefore(before.responseReceived().observedAt()),"prepared cleanup independent observations crossed their held connection/order");
    }
    /** Application DATA checks only. Actual source/SDK additionally applies NativeFreshSnapshotPort.verifyAfterOriginal
     * to these identical original packets; this layer deliberately creates no Native Received or copied wire parser. */
    private static void requireFreshAfter(NativeActionPort.AckReceived before,NativeActionPort.AckReceived fresh,
            NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received) {
        var previous=before.custody().orElseThrow();previous.verify(before);var custody=fresh.custody().orElseThrow();custody.verify(fresh);requireAfter(previous,custody);
        require(fresh.nativeOk()&&custody.session().equals(frame.session())&&received.order().compareTo(custody.writeCompleted().order())>0
                &&received.order().compareTo(custody.responseReceived().order())<0&&!received.observedAt().isBefore(custody.writeCompleted().observedAt())
                &&!received.observedAt().isAfter(custody.responseReceived().observedAt())&&received.observedAt().equals(frame.observedAt()),
                "prepared cleanup full snapshot was not received between its own independent READ write and ACK");
        Obj result=DriverJson.object(fresh.originalResultToken().orElseThrow().bytes(),MAXIMUM);
        require(result.members().keySet().equals(Set.of("schema","request_id","snapshot_id","revision"))
                &&new Text("xar.native.fresh-full-state-read/v1").equals(result.get("schema"))&&new Text(fresh.requestId()).equals(result.get("request_id"))
                &&new Text(frame.snapshotId()).equals(result.get("snapshot_id"))&&frame.nativeRevision().equals(integer(result.get("revision"),"revision")),
                "prepared cleanup full-state READ result does not bind its actual frame");
    }
    private static java.util.Set<String> originalIds(Prepared prepared) {
        var result=new java.util.HashSet<String>();result.add(RequestIds.forCommand(prepared.parentReceipt().command()));result.add(prepared.nativeRequestId());
        for(var child:prepared.children()){result.add(RequestIds.forCommand(child.command()));ActionTransitions.attempt(child.state()).ifPresent(a->result.add(a.requestId()));}
        result.add(prepared.aProof().freshStatus().receipt().requestId());result.add(prepared.aProof().freshSnapshotAck().requestId());return result;
    }
    private static Instant min(Instant left,Instant right){return left.isBefore(right)?left:right;}
    private static void requireCanonicalNonce(String value) {
        StrictJson.text(value);require(java.util.UUID.fromString(value).toString().equals(value),"prepared cleanup canonical immutable UUID nonce required");
    }

    /** Archive only after dispatch/capture; never call this between last late observation and endpoint.writePacket. */
    public static ExactRef preserveLateBinding(LateBinding binding,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        requireLateBinding(binding,binding.boundAt());var ref=save(lateNode(binding,archive),archive);
        require(sameLate(loadLateBinding(ref,archive,frames),binding),"late cleanup canonical DATA roundtrip differs");return ref;
    }
    public static LateBinding loadLateBinding(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        return loadLateBindingChecked(reference,archive,Objects.requireNonNull(frames));
    }
    public static LateBinding loadLateBindingOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        return loadLateBindingChecked(reference,archive,null);
    }
    private static LateBinding loadLateBindingChecked(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var result=decodeLate(material(reference,archive),archive,frames);requireLateBinding(result,result.boundAt());return result;
    }
    private static ObjectNode lateNode(LateBinding binding,ActionPorts.OutcomeArchive archive) {
        var row=StrictJson.object();row.put("schema",LATE_SCHEMA);row.set("prepared",binding.prepared().reference().toJson());
        row.set("status",statusNode(binding.status(),archive));row.set("fresh_snapshot_ack",archive.preserve(binding.freshSnapshotAck()).toJson());
        row.set("write_frame",frameNode(binding.writeFrame(),archive));row.set("snapshot_received",eventNode(binding.snapshotReceived()));
        row.put("bound_at_utc",binding.boundAt().toString());row.put("write_deadline_utc",binding.writeDeadline().toString());return row;
    }
    private static LateBinding decodeLate(Obj row,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        require(row.members().keySet().equals(Set.of("schema","prepared","status","fresh_snapshot_ack","write_frame","snapshot_received","bound_at_utc","write_deadline_utc"))
                &&new Text(LATE_SCHEMA).equals(row.get("schema")),"late cleanup schema or fields differ");
        var prepared=loadPreparedChecked(exact(row.get("prepared")),archive,frames);var status=decodeStatus(row.get("status"),archive);
        var ack=ack(exact(row.get("fresh_snapshot_ack")),archive);var frame=decodeFrame(row.get("write_frame"),ack,archive);
        return new LateBinding(prepared,status,ack,frame,decodeEvent(row.get("snapshot_received")),instant(row.get("bound_at_utc"),"bound_at_utc"),instant(row.get("write_deadline_utc"),"write_deadline_utc"));
    }
    /** The caller must first possess every volatile post-ACK original. No observation or IO callback is issued here. */
    public static ExactRef preservePostAckCaptured(PostAckCaptured captured,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        requirePostAckCaptured(captured);var row=StrictJson.object();row.put("schema",CAPTURED_SCHEMA);
        row.set("late_binding",preserveLateBinding(captured.binding(),archive,frames).toJson());row.set("cancellation_ack",archive.preserve(captured.cancellationAcknowledgement()).toJson());
        row.set("idle1",statusNode(captured.idle1(),archive));row.set("idle2",statusNode(captured.idle2(),archive));
        row.set("fresh_snapshot_ack",archive.preserve(captured.freshSnapshotAck()).toJson());row.set("after_frame",frameNode(captured.afterFrame(),archive));
        row.set("snapshot_received",eventNode(captured.snapshotReceived()));row.put("capture_deadline_utc",captured.captureDeadline().toString());
        var reference=save(row,archive);loadPostAckCaptured(reference,archive,frames);return reference;
    }
    public static PostAckCaptured loadPostAckCaptured(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        return loadPostAckCapturedChecked(reference,archive,Objects.requireNonNull(frames));
    }
    public static PostAckCaptured loadPostAckCapturedOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        return loadPostAckCapturedChecked(reference,archive,null);
    }
    private static PostAckCaptured loadPostAckCapturedChecked(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Obj row=material(reference,archive);require(row.members().keySet().equals(Set.of("schema","late_binding","cancellation_ack","idle1","idle2","fresh_snapshot_ack","after_frame","snapshot_received","capture_deadline_utc"))
                &&new Text(CAPTURED_SCHEMA).equals(row.get("schema")),"captured cleanup schema or fields differ");
        var binding=loadLateBindingChecked(exact(row.get("late_binding")),archive,frames);var ack=ack(exact(row.get("fresh_snapshot_ack")),archive);
        var result=new PostAckCaptured(binding,ack(exact(row.get("cancellation_ack")),archive),decodeStatus(row.get("idle1"),archive),decodeStatus(row.get("idle2"),archive),ack,
                decodeFrame(row.get("after_frame"),ack,archive),decodeEvent(row.get("snapshot_received")),instant(row.get("capture_deadline_utc"),"capture_deadline_utc"));
        requirePostAckCaptured(result);return result;
    }

    public static ExactRef preserveFailure(FailureData failure,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        requireFailure(failure);var decodedPrepared=loadPrepared(failure.prepared().reference(),archive,frames);
        require(samePrepared(decodedPrepared,failure.prepared()),"cleanup failure changed its durable preparation");
        var row=StrictJson.object();row.put("schema",FAILURE_SCHEMA);row.set("prepared",failure.prepared().reference().toJson());
        row.set("late_binding",failure.binding().isPresent()?lateNode(failure.binding().orElseThrow(),archive):com.fasterxml.jackson.databind.node.NullNode.getInstance());
        row.set("original",archive.preserve(failure.original()).toJson());var originals=row.putArray("observation_originals");
        for(var outcome:failure.observationOriginals())originals.add(archive.preserve(outcome).toJson());
        var supplemental=row.putArray("supplemental_originals");for(var ref:failure.supplementalOriginals())supplemental.add(ref.toJson());
        row.put("captured_at_utc",failure.capturedAt().toString());var reference=save(row,archive);loadFailure(reference,archive,frames);return reference;
    }
    /** Failure DATA can preserve an expired/failed late binding, never return it as a positive LateBinding role. */
    public static FailureData loadFailure(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Obj row=material(reference,archive);require(row.members().keySet().equals(Set.of("schema","prepared","late_binding","original","observation_originals","supplemental_originals","captured_at_utc"))
                &&new Text(FAILURE_SCHEMA).equals(row.get("schema")),"cleanup failure schema or fields differ");
        var prepared=loadPrepared(exact(row.get("prepared")),archive,frames);Optional<LateBinding> binding=row.get("late_binding") instanceof Nil?Optional.empty():Optional.of(decodeLate(object(row.get("late_binding"),"late_binding"),archive,frames));
        var original=outcome(exact(row.get("original")),archive);var observations=new ArrayList<NativeActionPort.DispatchOutcome>();
        for(var item:array(row.get("observation_originals"),"observation_originals"))observations.add(outcome(exact(item),archive));
        var supplemental=new ArrayList<ExactRef>();for(var item:array(row.get("supplemental_originals"),"supplemental_originals")){var ref=exact(item);require(ref.bytes()>0&&ref.bytes()<=RawJson.MAXIMUM_BYTES+4L,"bounded raw cleanup failure original required");exactBytes(ref,archive.readOriginalPacket(ref));supplemental.add(ref);}
        var result=new FailureData(prepared,binding,original,observations,instant(row.get("captured_at_utc"),"captured_at_utc"),supplemental);requireFailure(result);return result;
    }
    public static void requireFailure(FailureData failure) {
        require(failure.original().requestId().equals(failure.prepared().nativeRequestId())
                &&!failure.capturedAt().isBefore(failure.prepared().issuedAt())&&failure.supplementalOriginals().size()<=32
                &&failure.supplementalOriginals().stream().distinct().count()==failure.supplementalOriginals().size(),
                "cleanup failure belongs to another prepared child or has unbounded original metadata");
        failure.binding().ifPresent(binding->require(samePrepared(binding.prepared(),failure.prepared()),"cleanup failure borrowed another preparation binding"));
    }
    private static ObjectNode statusNode(StatusSample sample,ActionPorts.OutcomeArchive archive) {
        var row=StrictJson.object();row.set("acknowledgement",archive.preserve(sample.acknowledgement()).toJson());row.put("deadline_utc",sample.deadline().toString());return row;
    }
    private static StatusSample decodeStatus(Value value,ActionPorts.OutcomeArchive archive) {
        Obj row=object(value,"status");require(row.members().keySet().equals(Set.of("acknowledgement","deadline_utc")),"cleanup Status sample fields differ");
        return new StatusSample(ack(exact(row.get("acknowledgement")),archive),instant(row.get("deadline_utc"),"deadline_utc"));
    }
    private static ObjectNode frameNode(NativeObservationPort.ObservedFrame frame,ActionPorts.OutcomeArchive archive) {
        var row=StrictJson.object();row.set("native_frame",archive.preserveNativeFrame(frame).toJson());row.set("state_material",archive.preserveMaterial(frame.state()).toJson());
        row.put("snapshot_id",frame.snapshotId());row.put("native_revision",frame.nativeRevision().toString());row.put("observed_at_utc",frame.observedAt().toString());return row;
    }
    private static NativeObservationPort.ObservedFrame decodeFrame(Value value,NativeActionPort.AckReceived actualRead,ActionPorts.OutcomeArchive archive) {
        Obj row=object(value,"frame");require(row.members().keySet().equals(Set.of("native_frame","state_material","snapshot_id","native_revision","observed_at_utc")),"cleanup full-state frame fields differ");
        var nativeRef=exact(row.get("native_frame"));byte[] bytes=archive.loadNativeFrame(nativeRef);exactBytes(nativeRef,bytes);
        var stateRef=exact(row.get("state_material"));var state=archive.loadFullMaterial(stateRef);exactBytes(stateRef,state.bytes());
        return new NativeObservationPort.ObservedFrame(actualRead.custody().orElseThrow().session(),text(row.get("snapshot_id"),"snapshot_id"),
                positive(row.get("native_revision"),"native_revision"),state,bytes,instant(row.get("observed_at_utc"),"observed_at_utc"));
    }

    private static ObjectNode eventNode(NativeRequestChronology.Event value) {
        var row=StrictJson.object();row.put("order",value.order().toString());row.put("observed_at_utc",value.observedAt().toString());return row;
    }
    private static NativeRequestChronology.Event decodeEvent(Value value) {
        Obj row=object(value,"event");require(row.members().keySet().equals(Set.of("order","observed_at_utc")),"cleanup endpoint event fields differ");
        return new NativeRequestChronology.Event(positive(row.get("order"),"order"),instant(row.get("observed_at_utc"),"observed_at_utc"));
    }
    private static BigInteger positive(Value value,String key) {
        String text=text(value,key);require(text.matches("[1-9][0-9]*"),"cleanup canonical positive decimal required: "+key);
        var result=new BigInteger(text);require(result.compareTo(StrictJson.UINT64_MAX)<=0,"cleanup uint64 exceeded: "+key);return result;
    }
    private static NativeActionPort.DispatchOutcome outcome(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var result=archive.load(reference);require(archive.referenceOf(result).equals(reference),"cleanup original dispatch reference differs");return result;
    }
    private static NativeActionPort.AckReceived ack(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var result=outcome(reference,archive);require(result instanceof NativeActionPort.AckReceived,"cleanup actual original ACK is absent");return (NativeActionPort.AckReceived)result;
    }
    private static ExactRef save(ObjectNode value,ActionPorts.OutcomeArchive archive) {
        byte[] bytes=StrictJson.canonical(value);require(bytes.length<=MAXIMUM,"cleanup versioned material exceeds its unchanged cap");
        return archive.preserveMaterial(new RawJson(bytes));
    }
    private static boolean samePrepared(Prepared left,Prepared right) {
        return left.reference().equals(right.reference())&&left.parentReceipt().equals(right.parentReceipt())&&left.parentReference().equals(right.parentReference())
                &&left.children().equals(right.children())&&left.childReferences().equals(right.childReferences())
                &&left.aTerminalReference().equals(right.aTerminalReference())&&left.aProofReference().equals(right.aProofReference())
                &&left.authorizationReference().equals(right.authorizationReference())&&left.aProof().proofReference().equals(left.aProofReference())
                &&right.aProof().proofReference().equals(right.aProofReference())&&left.command().equals(right.command())
                &&left.commandReference().equals(right.commandReference())&&left.nativeRequestId().equals(right.nativeRequestId())
                &&left.nativePrepared().equals(right.nativePrepared())&&left.nativePreparedReference().equals(right.nativePreparedReference())
                &&left.preparationNonce().equals(right.preparationNonce())&&left.issuedAt().equals(right.issuedAt())&&left.deadline().equals(right.deadline());
    }
    static boolean sameLate(LateBinding left,LateBinding right) {
        return samePrepared(left.prepared(),right.prepared())&&left.status().equals(right.status())&&left.freshSnapshotAck().equals(right.freshSnapshotAck())
                &&sameFrame(left.writeFrame(),right.writeFrame())&&left.snapshotReceived().equals(right.snapshotReceived())
                &&left.boundAt().equals(right.boundAt())&&left.writeDeadline().equals(right.writeDeadline());
    }
    private static boolean sameFrame(NativeObservationPort.ObservedFrame left,NativeObservationPort.ObservedFrame right) {
        return left.session().equals(right.session())&&left.snapshotId().equals(right.snapshotId())&&left.nativeRevision().equals(right.nativeRevision())
                &&java.util.Arrays.equals(left.state().bytes(),right.state().bytes())&&java.util.Arrays.equals(left.originalPacket(),right.originalPacket())
                &&left.observedAt().equals(right.observedAt());
    }
}
